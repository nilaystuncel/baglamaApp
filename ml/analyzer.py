from pathlib import Path

import librosa
import numpy as np

from .audio_loader import load_audio
from .feedback import generate_feedback
from .note_matcher import NoteMatchResult, match_notes
from .pitch_detector import extract_pitch_contour
from .stability import performance_score, pitch_stability
from .tempo_detector import detect_tempo, tempo_accuracy


class AudioAnalyzer:
    def analyze(
        self,
        audio_path: str | Path,
        reference: dict,
    ) -> dict:
        y, sr = load_audio(audio_path, sr=22050)
        duration = float(librosa.get_duration(y=y, sr=sr))

        detected_bpm = detect_tempo(y, sr)
        expected_bpm = float(reference["expected_bpm"])
        tempo_acc = tempo_accuracy(detected_bpm, expected_bpm)

        tuning = reference.get("tuning", "kisa_sap_re_sol_la")
        times, f0, _ = extract_pitch_contour(y, sr, tuning=tuning)
        stability = pitch_stability(f0)

        note_results, note_acc = match_notes(times, f0, reference.get("notes", []))
        score = performance_score(tempo_acc, note_acc, stability)

        feedback = generate_feedback(
            tempo_accuracy=tempo_acc,
            note_accuracy=note_acc,
            stability=stability,
            performance_score=score,
            detected_bpm=detected_bpm,
            expected_bpm=expected_bpm,
            errors=note_results,
            reference_title=reference["title"],
        )

        return {
            "metrics": {
                "tempo_accuracy": tempo_acc,
                "note_accuracy": note_acc,
                "stability": stability,
                "performance_score": score,
                "detected_bpm": round(detected_bpm, 1),
                "expected_bpm": expected_bpm,
                "duration_sec": round(duration, 2),
            },
            "errors": [
                {
                    "index": r.index,
                    "expected_note": r.expected_note,
                    "played_note": r.played_note or "algılanamadı",
                    "deviation_cents": r.deviation_cents,
                }
                for r in note_results
                if not r.is_correct
            ],
            "feedback": feedback,
        }
