from .note_matcher import NoteMatchResult


def generate_feedback(
    tempo_accuracy: float,
    note_accuracy: float,
    stability: float,
    performance_score: float,
    detected_bpm: float,
    expected_bpm: float,
    errors: list[NoteMatchResult],
    reference_title: str,
) -> str:
    parts: list[str] = []

    parts.append(f'"{reference_title}" performansınız analiz edildi.')
    parts.append(f"Genel performans skoru: {performance_score}/100.")

    if tempo_accuracy >= 85:
        parts.append(
            f"Tempo oldukça iyi. Hedef {expected_bpm} BPM, siz {detected_bpm:.0f} BPM çaldınız (%{tempo_accuracy} uyum)."
        )
    elif tempo_accuracy >= 60:
        parts.append(
            f"Tempoda küçük sapmalar var. Hedef {expected_bpm} BPM, siz {detected_bpm:.0f} BPM çaldınız (%{tempo_accuracy} uyum)."
        )
    else:
        parts.append(
            f"Tempo hedeften uzak. Hedef {expected_bpm} BPM, siz {detected_bpm:.0f} BPM çaldınız. Metronom ile çalışmanız önerilir."
        )

    if note_accuracy >= 85:
        parts.append(f"Nota uyumu güçlü (%{note_accuracy}).")
    elif note_accuracy >= 60:
        parts.append(f"Nota uyumu orta seviyede (%{note_accuracy}). Bazı geçişlerde dikkat gerekli.")
    else:
        parts.append(f"Nota uyumu düşük (%{note_accuracy}). Referans melodiyi dinleyerek tekrar deneyin.")

    if stability >= 85:
        parts.append(f"Ses stabilitesi iyi (%{stability}).")
    else:
        parts.append(f"Ses stabilitesinde titreme var (%{stability}). Notaları daha uzun ve net basmayı deneyin.")

    wrong = [e for e in errors if not e.is_correct]
    if wrong:
        parts.append("Tespit edilen hatalar:")
        for err in wrong[:5]:
            played = err.played_note or "algılanamadı"
            parts.append(
                f"  • {err.index + 1}. nota: beklenen {err.expected_note}, çalınan {played}"
            )
        if len(wrong) > 5:
            parts.append(f"  • ... ve {len(wrong) - 5} hata daha.")
    else:
        parts.append("Belirgin nota hatası tespit edilmedi.")

    return "\n".join(parts)
