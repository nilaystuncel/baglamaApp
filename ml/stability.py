import numpy as np


def pitch_stability(f0: np.ndarray) -> float:
    valid = f0[~np.isnan(f0)]
    if len(valid) < 2:
        return 0.0

    # Ardışık perde değişimlerinin standart sapması — düşük = daha stabil
    diffs = np.abs(np.diff(valid))
    std_dev = float(np.std(diffs))

    # Hz cinsinden sapmayı 0-100 skoruna çevir
    score = max(0.0, 100.0 - (std_dev * 4))
    return round(min(score, 100.0), 1)


def performance_score(tempo_acc: float, note_acc: float, stability: float) -> float:
    score = tempo_acc * 0.3 + note_acc * 0.5 + stability * 0.2
    return round(score, 1)
