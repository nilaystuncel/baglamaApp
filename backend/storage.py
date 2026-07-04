import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config import ROOT_DIR

DATA_DIR = ROOT_DIR / "data" / "store"
RECORDINGS_FILE = DATA_DIR / "recordings.json"


class FileStorage:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not RECORDINGS_FILE.exists():
            RECORDINGS_FILE.write_text("[]", encoding="utf-8")

    def _read(self) -> list[dict]:
        return json.loads(RECORDINGS_FILE.read_text(encoding="utf-8"))

    def _write(self, data: list[dict]) -> None:
        RECORDINGS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    async def insert_recording(self, doc: dict) -> None:
        data = self._read()
        data.insert(0, doc)
        self._write(data)

    async def insert_analysis(self, doc: dict) -> None:
        pass  # analysis recording içinde tutuluyor

    async def insert_feedback(self, doc: dict) -> None:
        pass

    async def find_recording(self, recording_id: str) -> dict | None:
        for doc in self._read():
            if doc.get("_id") == recording_id:
                return doc
        return None

    async def list_recordings(self, limit: int = 20) -> list[dict]:
        return self._read()[:limit]


class MongoStorage:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def insert_recording(self, doc: dict) -> None:
        await self.db.recordings.insert_one(doc)

    async def insert_analysis(self, doc: dict) -> None:
        await self.db.analysis_results.insert_one(doc)

    async def insert_feedback(self, doc: dict) -> None:
        await self.db.feedback.insert_one(doc)

    async def find_recording(self, recording_id: str) -> dict | None:
        return await self.db.recordings.find_one({"_id": recording_id})

    async def list_recordings(self, limit: int = 20) -> list[dict]:
        cursor = self.db.recordings.find().sort("created_at", -1).limit(limit)
        return [doc async for doc in cursor]


storage: FileStorage | MongoStorage | None = None
use_mongodb: bool = False


async def init_storage(db: Any | None) -> str:
    global storage, use_mongodb

    if db is not None:
        try:
            await db.command("ping")
            storage = MongoStorage(db)
            use_mongodb = True
            return "mongodb"
        except Exception:
            pass

    storage = FileStorage()
    use_mongodb = False
    return "file"


def get_storage() -> FileStorage | MongoStorage:
    if storage is None:
        raise RuntimeError("Depolama başlatılmadı.")
    return storage
