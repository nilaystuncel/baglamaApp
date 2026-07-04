import librosa
import numpy as np


def detect_tempo(y: np.ndarray, sr: int) -> float:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
    return float(tempo[0]) if len(tempo) else 0.0


def tempo_accuracy(detected_bpm: float, expected_bpm: float) -> float:
    if expected_bpm <= 0 or detected_bpm <= 0:
        return 0.0
    ratio = min(detected_bpm, expected_bpm) / max(detected_bpm, expected_bpm)
    return round(ratio * 100, 1)


def beat_times(y: np.ndarray, sr: int) -> np.ndarray:
    tempo = detect_tempo(y, sr)
    if tempo <= 0:
        return np.array([])
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr, bpm=tempo)
    return librosa.frames_to_time(beat_frames, sr=sr)
