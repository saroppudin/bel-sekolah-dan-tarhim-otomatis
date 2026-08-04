from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///data/bel.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class AudioFile(Base):
    __tablename__ = "audio_files"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    keterangan = Column(String, default="")
    durasi_detik = Column(Integer, default=0)


class JadwalUmum(Base):
    """Protected: lagu_pagi, indonesia_raya, bel_sholat_dzuhur, bel_masuk.
    Tidak pernah ikut ter-bulk-delete saat kosongkan jadwal harian/ujian."""
    __tablename__ = "jadwal_umum"
    id = Column(Integer, primary_key=True)
    jam = Column(Integer, nullable=False)
    menit = Column(Integer, nullable=False)
    hari = Column(Integer, nullable=False)  # 1=Senin .. 6=Sabtu
    kunci_jadwal = Column(String, nullable=False)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"))
    aktif = Column(Boolean, default=True)
    audio_file = relationship("AudioFile")


class JadwalHarian(Base):
    """Khusus bel_kbm, bebas ditambah/edit/hapus/kosongkan."""
    __tablename__ = "jadwal_harian"
    id = Column(Integer, primary_key=True)
    jam = Column(Integer, nullable=False)
    menit = Column(Integer, nullable=False)
    hari = Column(Integer, nullable=False)
    kunci_jadwal = Column(String, default="bel_kbm")
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"))
    aktif = Column(Boolean, default=True)
    audio_file = relationship("AudioFile")


class JadwalUjian(Base):
    """Khusus bel_ujian, bebas ditambah/edit/hapus/kosongkan."""
    __tablename__ = "jadwal_ujian"
    id = Column(Integer, primary_key=True)
    jam = Column(Integer, nullable=False)
    menit = Column(Integer, nullable=False)
    hari = Column(Integer, nullable=False)
    kunci_jadwal = Column(String, default="bel_ujian")
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"))
    aktif = Column(Boolean, default=True)
    audio_file = relationship("AudioFile")


class ModeKunciStatus(Base):
    __tablename__ = "mode_kunci_status"
    id = Column(Integer, primary_key=True)
    mode = Column(String, nullable=False)          # kbm / ujian / libur
    kunci_jadwal = Column(String, nullable=False)
    aktif = Column(Boolean, default=True)


class ModeOperasional(Base):
    __tablename__ = "mode_operasional"
    id = Column(Integer, primary_key=True)
    mode_aktif = Column(String, default="kbm")
    diubah_pada = Column(DateTime, default=datetime.utcnow)


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    lintang = Column(String, default="")
    bujur = Column(String, default="")
    metode_hisab = Column(String, default="kemenag")
    output_mode = Column(String, default="line_out")   # line_out / bluetooth
    bt_mac_address = Column(String, default="")
    tarhim_subuh_file_id = Column(Integer, ForeignKey("audio_files.id"), nullable=True)
    tarhim_maghrib_01_id = Column(Integer, ForeignKey("audio_files.id"), nullable=True)
    tarhim_maghrib_02_id = Column(Integer, ForeignKey("audio_files.id"), nullable=True)
    tarhim_maghrib_03_id = Column(Integer, ForeignKey("audio_files.id"), nullable=True)
    tarhim_cycle_start_date = Column(Date, default=datetime(2026, 1, 5).date())  # Senin acuan
    jeda_senin_aktif = Column(Boolean, default=True)
    jeda_senin_durasi_menit = Column(Integer, default=45)
    jeda_senin_pemicu_kunci = Column(String, default="bel_masuk")


class PrayerTimesCache(Base):
    __tablename__ = "prayer_times_cache"
    id = Column(Integer, primary_key=True)
    tanggal = Column(Date, unique=True, nullable=False)
    subuh = Column(String)
    dzuhur = Column(String)
    ashar = Column(String)
    maghrib = Column(String)
    isya = Column(String)
    sumber = Column(String, default="online")  # online / lokal


class RotationState(Base):
    """Menyimpan giliran siapa yang main duluan saat 2 kunci bentrok di jam sama."""
    __tablename__ = "rotation_state"
    id = Column(Integer, primary_key=True)
    pasangan_kunci = Column(String, unique=True, nullable=False)  # mis "bel_sholat_dzuhur|bel_kbm"
    giliran_terakhir = Column(String, default="")
    tanggal_terakhir = Column(Date, nullable=True)


class PauseState(Base):
    __tablename__ = "pause_state"
    id = Column(Integer, primary_key=True)
    aktif = Column(Boolean, default=False)
    sampai = Column(DateTime, nullable=True)          # durasi pilihan admin (kalau ada)
    safety_valve_at = Column(DateTime, nullable=True) # auto-resume jam 14:00 WIB berikutnya
    alasan = Column(String, default="")

class PlaybackLog(Base):
    __tablename__ = "playback_log"
    id = Column(Integer, primary_key=True)
    waktu = Column(DateTime, default=datetime.utcnow)
    kunci_jadwal = Column(String)
    audio_path = Column(String)
    status = Column(String)   # sukses / gagal / dilewati_pause / dilewati_jeda_senin
    keterangan = Column(String, default="")


def init_db():
    Base.metadata.create_all(engine)
