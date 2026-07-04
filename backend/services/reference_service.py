import json
from pathlib import Path

from config import ROOT_DIR

REFERENCES_PATH = ROOT_DIR / "data" / "references" / "songs.json"


class ReferenceService:
    def __init__(self) -> None:
        self._references: list[dict] = []
        self._load()

    def _load(self) -> None:
        with open(REFERENCES_PATH, encoding="utf-8") as f:
            self._references = json.load(f)

    def list_songs(self) -> list[dict]:
        self._load()
        return [
            {
                "id": song["id"],
                "title": song["title"],
                "artist": song["artist"],
                "expected_bpm": song["expected_bpm"],
                "description": song["description"],
            }
            for song in self._references
        ]

    def get_by_id(self, reference_id: str) -> dict | None:
        self._load()
        for song in self._references:
            if song["id"] == reference_id:
                return song
        return None


reference_service = ReferenceService()
