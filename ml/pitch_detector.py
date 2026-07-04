import librosa
import numpy as np


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def hz_to_note(freq: float) -> str | None:
    if freq <= 0 or np.isnan(freq):
        return None
    midi = int(round(librosa.hz_to_midi(freq)))
    octave = (midi // 12) - 1
    name = NOTE_NAMES[midi % 12]
    return f"{name}{octave}"


def note_to_hz(note: str) -> float:
    return float(librosa.note_to_hz(note))


def cents_deviation(freq: float, target_note: str) -> float:
    if freq <= 0 or np.isnan(freq):
        return 999.0
    target_hz = note_to_hz(target_note)
    return float(abs(1200 * np.log2(freq / target_hz)))


TUNING_FMIN = {
    "kisa_sap_re_sol_la": "C3",
    "uzun_sap": "A1",
}
TUNING_FMAX = {
    "kisa_sap_re_sol_la": "C6",
    "uzun_sap": "A5",
}


def extract_pitch_contour(
    y: np.ndarray,
    sr: int,
    hop_length: int = 512,
    tuning: str = "kisa_sap_re_sol_la",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fmin = librosa.note_to_hz(TUNING_FMIN.get(tuning, "D2"))
    fmax = librosa.note_to_hz(TUNING_FMAX.get(tuning, "C6"))
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=fmin,
        fmax=fmax,
        sr=sr,
        hop_length=hop_length,
    )
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
    return times, f0, voiced_flag


def get_pitch_at_time(
    times: np.ndarray,
    f0: np.ndarray,
    target_time: float,
    window: float = 0.15,
) -> float | None:
    mask = (times >= target_time) & (times <= target_time + window)
    segment = f0[mask]
    valid = segment[~np.isnan(segment)]
    if len(valid) == 0:
        return None
    return float(np.median(valid))
