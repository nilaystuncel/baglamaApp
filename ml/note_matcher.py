from dataclasses import dataclass

import numpy as np

from .pitch_detector import hz_to_note


@dataclass
class NoteMatchResult:
    index: int
    expected_note: str
    played_note: str | None
    played_hz: float | None
    deviation_cents: float
    is_correct: bool


def extract_note_sequence(f0: np.ndarray, min_duration_frames: int = 3) -> list[str]:
    notes = []
    prev_note = None
    count = 0

    for freq in f0:
        if freq is None or np.isnan(freq) or freq <= 0:
            if count >= min_duration_frames and prev_note is not None:
                notes.append(prev_note)
            prev_note = None
            count = 0
            continue

        note = hz_to_note(freq)
        if note == prev_note:
            count += 1
        else:
            if count >= min_duration_frames and prev_note is not None:
                notes.append(prev_note)
            prev_note = note
            count = 1

    if count >= min_duration_frames and prev_note is not None:
        notes.append(prev_note)

    return notes


def note_to_midi(note: str) -> int | None:
    try:
        import librosa
        return int(librosa.note_to_midi(note))
    except Exception:
        return None


def cents_deviation_from_note(played: str | None, expected: str) -> float:
    if played is None:
        return 999.0
    pm = note_to_midi(played)
    em = note_to_midi(expected)
    if pm is None or em is None:
        return 999.0
    return float(abs(pm - em) * 100)


def align_sequences(
    ref: list[str],
    played: list[str],
    tolerance_cents: float = 150.0,
) -> tuple[list[NoteMatchResult], int]:
    n = len(ref)
    m = len(played)
    GAP = 200.0

    dp = np.full((n + 1, m + 1), np.inf)
    dp[0][0] = 0.0
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + GAP
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + GAP

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = cents_deviation_from_note(played[j - 1], ref[i - 1])
            dp[i][j] = min(
                dp[i - 1][j - 1] + cost,
                dp[i - 1][j] + GAP,
                dp[i][j - 1] + GAP,
            )

    alignments = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + cents_deviation_from_note(played[j - 1], ref[i - 1]):
            alignments.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + GAP:
            alignments.append((i - 1, None))
            i -= 1
        else:
            j -= 1

    alignments.reverse()
    results = []
    correct_count = 0

    for ref_idx, played_idx in alignments:
        expected = ref[ref_idx]
        played_note = played[played_idx] if played_idx is not None else None
        deviation = cents_deviation_from_note(played_note, expected)
        is_correct = deviation <= tolerance_cents
        if is_correct:
            correct_count += 1
        results.append(NoteMatchResult(
            index=ref_idx,
            expected_note=expected,
            played_note=played_note,
            played_hz=None,
            deviation_cents=round(deviation, 1),
            is_correct=is_correct,
        ))

    return results, correct_count


def match_notes(
    times: np.ndarray,
    f0: np.ndarray,
    reference_notes: list[dict],
    tolerance_cents: float = 150.0,
) -> tuple[list[NoteMatchResult], float]:
    played_sequence = extract_note_sequence(f0)
    ref_notes = [r["note"] for r in reference_notes]

    if not ref_notes:
        return [], 0.0

    if not played_sequence:
        results = [
            NoteMatchResult(i, ref_notes[i], None, None, 999.0, False)
            for i in range(len(ref_notes))
        ]
        return results, 0.0

    results, correct_count = align_sequences(ref_notes, played_sequence, tolerance_cents)
    accuracy = (correct_count / len(ref_notes) * 100) if ref_notes else 0.0
    return results, round(accuracy, 1)
