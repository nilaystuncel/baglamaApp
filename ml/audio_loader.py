from pathlib import Path

import librosa
import numpy as np


def load_audio(audio_path: str | Path, sr: int = 22050) -> tuple[np.ndarray, int]:
    path = Path(audio_path)
    suffix = path.suffix.lower()

    try:
        y, loaded_sr = librosa.load(str(path), sr=sr, mono=True)
        return y, loaded_sr
    except Exception as exc:
        if suffix in {".webm", ".mp3", ".m4a", ".ogg"}:
            raise RuntimeError(
                f"{suffix} formatı okunamadı. Canlı kayıt için WAV dönüşümü gerekir "
                f"veya sisteme ffmpeg kurulmalı."
            ) from exc
        raise RuntimeError(f"Ses dosyası okunamadı: {exc}") from exc
