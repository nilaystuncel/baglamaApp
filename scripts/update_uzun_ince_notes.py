import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SONGS_PATH = ROOT / "data" / "references" / "songs.json"

# Kolay nota: perde adi = pitch (do=C, re=D, mi=E, fa=F, sol=G, la=A, si=Bb)
SOLFEGE = {
    "do": "C4",
    "re": "D4",
    "mi": "E4",
    "fa": "F4",
    "fa#": "F#4",
    "sol": "G4",
    "la": "A4",
    "si": "A#4",
}


def phrase(notes: list[str], durations: list[float], start: float):
    out = []
    t = start
    for name, duration in zip(notes, durations):
        out.append(
            {
                "time": round(t, 2),
                "note": SOLFEGE[name],
                "duration": duration,
                "solfege": name,
            }
        )
        t += duration
    return out, t


def build_melody() -> tuple[list[dict], float]:
    notes: list[dict] = []
    t = 0.0

    p1 = ["do", "re", "re", "do", "si", "la", "do", "si", "la", "la", "la"]
    d1 = [0.5, 0.75, 0.75, 0.5, 0.5, 0.5, 0.5, 0.75, 0.5, 0.5, 1.0]

    p2 = ["mi", "re", "mi", "do", "re", "do", "si", "la", "do", "si", "la", "la", "la"]
    d2 = [0.5, 0.5, 0.5, 0.5, 0.75, 0.5, 0.5, 0.5, 0.5, 0.75, 0.5, 0.5, 1.0]

    for _ in range(2):
        chunk, t = phrase(p1, d1, t)
        notes.extend(chunk)
        chunk, t = phrase(p2, d2, t)
        notes.extend(chunk)

    p4 = ["fa#", "sol", "sol", "sol", "sol", "fa#", "mi", "sol", "fa#"]
    d4 = [0.5, 0.5, 0.5, 0.75, 0.5, 0.75, 0.5, 0.75, 1.0]
    chunk, t = phrase(p4, d4, t)
    notes.extend(chunk)

    p5 = ["sol", "mi", "re", "mi", "mi", "mi", "re", "do", "mi", "re"]
    d5 = [0.5, 0.75, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.75]
    chunk, t = phrase(p5, d5, t)
    notes.extend(chunk)

    p6 = ["re", "do", "si", "la", "re", "si", "do", "do", "si", "la", "do", "si"]
    d6 = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.75, 0.5, 0.5, 0.5, 0.5, 0.75]
    chunk, t = phrase(p6, d6, t)
    notes.extend(chunk)

    p7 = ["si", "la", "sol", "si", "la", "la"]
    d7 = [0.5, 0.75, 0.5, 0.5, 0.5, 2.5]
    chunk, t = phrase(p7, d7, t)
    notes.extend(chunk)

    return notes, t


def main() -> None:
    notes, total = build_melody()
    songs = json.loads(SONGS_PATH.read_text(encoding="utf-8"))

    for song in songs:
        if song["id"] != "uzun-ince-bir-yoldayim":
            continue
        song.update(
            {
                "expected_bpm": 72,
                "description": "Hüseyni makamı, La karar. Kolay nota perde adları (do=C, re=D, si=Bb). ~52 sn.",
                "makam": "huseyni",
                "tuning": "la_karar",
                "note_mapping": "perde_adi",
                "solfege_map": {
                    "do": "C",
                    "re": "D",
                    "mi": "E",
                    "fa": "F",
                    "fa#": "F#",
                    "sol": "G",
                    "la": "A",
                    "si": "Bb",
                },
                "total_duration_sec": round(total, 1),
                "notes": notes,
            }
        )
        break

    SONGS_PATH.write_text(json.dumps(songs, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Ilk cumle:")
    for n in notes[:11]:
        print(f"  {n['solfege']:4} -> {n['note']}")
    print(f"Toplam: {len(notes)} nota, {round(total, 1)} sn")


if __name__ == "__main__":
    main()
