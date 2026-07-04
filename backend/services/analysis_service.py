import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from config import ROOT_DIR
from storage import get_storage

sys.path.insert(0, str(ROOT_DIR))
from ml.analyzer import AudioAnalyzer

from services.reference_service import reference_service


class AnalysisService:
    def __init__(self) -> None:
        self.analyzer = AudioAnalyzer()

    async def process_upload(
        self,
        file_path: Path,
        filename: str,
        reference_id: str,
    ) -> dict:
        reference = reference_service.get_by_id(reference_id)
        if not reference:
            raise ValueError(f"Referans türkü bulunamadı: {reference_id}")

        result = self.analyzer.analyze(file_path, reference)
        recording_id = str(uuid4())
        now = datetime.utcnow()

        analysis_doc = {
            "recording_id": recording_id,
            "reference_id": reference_id,
            "reference_title": reference["title"],
            "metrics": result["metrics"],
            "errors": result["errors"],
            "feedback": result["feedback"],
            "created_at": now,
        }

        recording_doc = {
            "_id": recording_id,
            "filename": filename,
            "file_path": str(file_path),
            "reference_id": reference_id,
            "reference_title": reference["title"],
            "created_at": now,
            "analysis": analysis_doc,
        }

        store = get_storage()
        await store.insert_recording(recording_doc)
        await store.insert_analysis({**analysis_doc, "_id": str(uuid4())})
        await store.insert_feedback(
            {
                "_id": str(uuid4()),
                "recording_id": recording_id,
                "feedback": result["feedback"],
                "created_at": now,
            }
        )

        return {
            "recording_id": recording_id,
            "filename": filename,
            "reference_id": reference_id,
            "reference_title": reference["title"],
            "analysis": analysis_doc,
        }

    async def get_analysis(self, recording_id: str) -> dict | None:
        doc = await get_storage().find_recording(recording_id)
        if not doc:
            return None
        return doc.get("analysis")

    async def get_feedback(self, recording_id: str) -> dict | None:
        analysis = await self.get_analysis(recording_id)
        if not analysis:
            return None
        return {
            "recording_id": recording_id,
            "feedback": analysis["feedback"],
            "metrics": analysis["metrics"],
            "errors": analysis["errors"],
        }

    async def get_history(self, limit: int = 20) -> list[dict]:
        docs = await get_storage().list_recordings(limit=limit)
        items = []
        for doc in docs:
            analysis = doc.get("analysis", {})
            metrics = analysis.get("metrics", {})
            items.append(
                {
                    "id": doc["_id"],
                    "reference_title": doc.get("reference_title", ""),
                    "performance_score": metrics.get("performance_score", 0),
                    "tempo_accuracy": metrics.get("tempo_accuracy", 0),
                    "note_accuracy": metrics.get("note_accuracy", 0),
                    "stability": metrics.get("stability", 0),
                    "created_at": doc.get("created_at"),
                }
            )
        return items


analysis_service = AnalysisService()
