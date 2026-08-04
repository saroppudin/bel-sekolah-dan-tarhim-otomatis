import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

from datetime import time as dtime

JAM_SAFETY_VALVE = dtime(14, 0)  # 14:00 WIB


def _hitung_safety_valve(now: datetime) -> datetime:
    """Safety valve berikutnya: hari ini jam 14:00 kalau belum lewat,
    kalau sudah lewat -> besok jam 14:00."""
    target = now.replace(hour=14, minute=0, second=0, microsecond=0)
    if now.time() >= JAM_SAFETY_VALVE:
        target += timedelta(days=1)
    return target


def aktifkan_pause_manual(db, durasi_menit: int | None, alasan: str = ""):
    """durasi_menit=None -> pause 'sampai di-resume manual', tapi tetap
    dijaga safety-valve jam 14:00 supaya tidak lupa selamanya."""
    now = datetime.now()
    p = db.query(PauseState).first() or PauseState()
    p.aktif = True
    p.sampai = (now + timedelta(minutes=durasi_menit)) if durasi_menit else None
    p.safety_valve_at = _hitung_safety_valve(now)
    p.alasan = alasan
    db.add(p)
    db.commit()


def _is_paused(db) -> bool:
    p = db.query(PauseState).first()
    if not p or not p.aktif:
        return False

    now = datetime.now()

    # Durasi pilihan admin habis
    if p.sampai and now >= p.sampai:
        p.aktif = False
        db.commit()
        return False

    # Safety-valve jam 14:00 tercapai (jaring pengaman kalau admin lupa)
    if p.safety_valve_at and now >= p.safety_valve_at:
        p.aktif = False
        db.commit()
        logger.warning("Pause manual auto-resume oleh safety-valve jam 14:00 WIB")
        return False

    return True


def resume_manual(db):
    """Dipanggil tombol 'Resume' di dashboard."""
    p = db.query(PauseState).first()
    if p:
        p.aktif = False
        db.commit()

from .models import (
    SessionLocal, JadwalUmum, JadwalHarian, JadwalUjian, ModeKunciStatus,
    ModeOperasional, Settings, PauseState, RotationState, PlaybackLog
)
from .audio_player import audio_player

logger = logging.getLogger("scheduler")

jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///data/bel.db")}
scheduler = BackgroundScheduler(jobstores=jobstores, timezone="Asia/Jakarta")


def _mode_aktif(db) -> str:
    row = db.query(ModeOperasional).first()
    return row.mode_aktif if row else "kbm"


def _kunci_status(db, mode: str, kunci: str) -> bool:
    row = db.query(ModeKunciStatus).filter_by(mode=mode, kunci_jadwal=kunci).first()
    return row.aktif if row else False


def _is_paused(db) -> bool:
    p = db.query(PauseState).first()
    if not p or not p.aktif:
        return False
    if p.sampai and datetime.now() >= p.sampai:
        p.aktif = False
        db.commit()
        return False
    return True


def _in_jeda_senin(db, now: datetime) -> bool:
    """Cek apakah 'now' jatuh di window jeda 45 menit setelah bel_masuk hari Senin."""
    s = db.query(Settings).first()
    if not s or not s.jeda_senin_aktif or now.weekday() != 0:  # 0 = Senin
        return False
    pemicu = (
        db.query(JadwalUmum)
        .filter_by(hari=1, kunci_jadwal=s.jeda_senin_pemicu_kunci, aktif=True)
        .first()
    )
    if not pemicu:
        return False
    mulai = now.replace(hour=pemicu.jam, minute=pemicu.menit, second=0, microsecond=0)
    selesai = mulai + timedelta(minutes=s.jeda_senin_durasi_menit)
    return mulai <= now <= selesai


def _cek_giliran(db, kunci: str, jam: int, menit: int, hari: int) -> bool:
    """Cari apakah ada kunci lain di jam:menit:hari yang sama -> tentukan giliran.
    Return True jika kunci ini yang 'jalan duluan' hari ini."""
    semua_sumber = []
    for Model in (JadwalUmum, JadwalHarian, JadwalUjian):
        semua_sumber += db.query(Model).filter_by(
            jam=jam, menit=menit, hari=hari, aktif=True
        ).all()

    bentrok = [e for e in semua_sumber if e.kunci_jadwal != kunci]
    if not bentrok:
        return True  # tidak ada konflik, langsung main

    lawan = sorted(bentrok, key=lambda e: e.kunci_jadwal)[0].kunci_jadwal
    pasangan = "|".join(sorted([kunci, lawan]))
    state = db.query(RotationState).filter_by(pasangan_kunci=pasangan).first()
    today = date.today()

    if not state:
        state = RotationState(pasangan_kunci=pasangan, giliran_terakhir=kunci, tanggal_terakhir=today)
        db.add(state)
        db.commit()
        return True  # pertama kali, kunci ini duluan

    if state.tanggal_terakhir == today:
        # sudah ditentukan giliran hari ini
        return state.giliran_terakhir == kunci

    # hari baru -> gantian
    giliran_baru = kunci if state.giliran_terakhir != kunci else lawan
    state.giliran_terakhir = giliran_baru
    state.tanggal_terakhir = today
    db.commit()
    # kalau giliran_baru != kunci ini, berarti kunci ini menunggu sebentar sebelum main
    if giliran_baru != kunci:
        import time
        time.sleep(1.5)  # kasih kesempatan lawan mengunci audio_player duluan
    return True  # tetap True: keduanya tetap main, cuma urutannya diatur


def _log(db, kunci, path, status, ket=""):
    db.add(PlaybackLog(kunci_jadwal=kunci, audio_path=path, status=status, keterangan=ket))
    db.commit()


def execute_bel(table: str, entry_id: int):
    """Dipanggil oleh cron trigger tiap minggu untuk 1 baris jadwal tertentu.
    Semua pengecekan mode/pause/jeda/giliran dilakukan real-time di sini,
    bukan saat build jadwal -> otomatis tahan restart & tahan perubahan mode mendadak."""
    db = SessionLocal()
    try:
        Model = {"umum": JadwalUmum, "harian": JadwalHarian, "ujian": JadwalUjian}[table]
        entry = db.query(Model).filter_by(id=entry_id, aktif=True).first()
        if not entry:
            return

        mode = _mode_aktif(db)
        if not _kunci_status(db, mode, entry.kunci_jadwal):
            return  # kunci ini nonaktif di mode sekarang

        now = datetime.now()

        if _is_paused(db):
            _log(db, entry.kunci_jadwal, "", "dilewati_pause")
            return

        if _in_jeda_senin(db, now) and entry.kunci_jadwal != "tarhim":
            _log(db, entry.kunci_jadwal, "", "dilewati_jeda_senin")
            return

        _cek_giliran(db, entry.kunci_jadwal, entry.jam, entry.menit, entry.hari)

        if not entry.audio_file:
            _log(db, entry.kunci_jadwal, "", "gagal", "file audio tidak diset")
            return

        ok = audio_player.play_file(entry.audio_file.path)
        _log(db, entry.kunci_jadwal, entry.audio_file.path, "sukses" if ok else "gagal")
    finally:
        db.close()


def register_recurring_jobs():
    """Daftarkan cron job untuk semua entri jadwal_umum/harian/ujian.
    Karena pakai CronTrigger + jobstore persistent, ini SEKALI daftar saja
    dan otomatis tahan restart -- tidak perlu di-rebuild tiap hari."""
    db = SessionLocal()
    try:
        for table, Model in (("umum", JadwalUmum), ("harian", JadwalHarian), ("ujian", JadwalUjian)):
            for entry in db.query(Model).filter_by(aktif=True).all():
                job_id = f"{table}_{entry.id}"
                scheduler.add_job(
                    execute_bel,
                    trigger=CronTrigger(day_of_week=entry.hari - 1, hour=entry.jam, minute=entry.menit),
                    args=[table, entry.id],
                    id=job_id,
                    replace_existing=True,
                )
    finally:
        db.close()
