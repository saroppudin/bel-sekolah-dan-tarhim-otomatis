import subprocess
import threading
import time
import logging

logger = logging.getLogger("audio_player")
_play_lock = threading.Lock()


class AudioPlayer:
    """Wrapper mpv: mutex supaya tidak ada 2 suara tabrakan di 1 sink,
    plus retry sekali kalau proses mpv crash sebelum durasi selesai."""

    def play_file(self, path: str, timeout: int = 600, retry: bool = True) -> bool:
        with _play_lock:
            ok = self._run_mpv(["mpv", "--no-video", "--really-quiet", path], timeout)
            if not ok and retry:
                logger.warning(f"Playback gagal, retry sekali: {path}")
                ok = self._run_mpv(["mpv", "--no-video", "--really-quiet", path], timeout)
            return ok

    def test_tone(self, freq: int = 1000, duration: int = 2) -> bool:
        """Test output cepat tanpa file, generate sine wave langsung."""
        with _play_lock:
            cmd = [
                "mpv", "--no-video", "--really-quiet",
                f"av://lavfi:sine=frequency={freq}:duration={duration}"
            ]
            return self._run_mpv(cmd, timeout=duration + 5)

    def _run_mpv(self, cmd, timeout) -> bool:
        try:
            start = time.time()
            proc = subprocess.run(cmd, timeout=timeout)
            elapsed = time.time() - start
            if proc.returncode != 0 and elapsed < 1:
                # mpv exit cepat & error = kemungkinan crash / file rusak / sink tidak ada
                return False
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error(f"mpv timeout: {cmd}")
            return False
        except FileNotFoundError:
            logger.error("mpv tidak ditemukan, pastikan sudah terinstall")
            return False


audio_player = AudioPlayer()
