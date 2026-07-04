from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReferenceSong(BaseModel):
    id: str
    title: str
    artist: str
    expected_bpm: float
    description: str


class NoteError(BaseModel):
    index: int
    expected_note: str
    played_note: str
    deviation_cents: float


class AnalysisMetrics(BaseModel):
    tempo_accuracy: float
    note_accuracy: float
    stability: float
    performance_score: float
    detected_bpm: float
    expected_bpm: float
    duration_sec: float


class AnalysisResult(BaseModel):
    recording_id: str
    reference_id: str
    reference_title: str
    metrics: AnalysisMetrics
    errors: list[NoteError]
    feedback: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecordingResponse(BaseModel):
    id: str
    filename: str
    reference_id: str
    reference_title: str
    created_at: datetime
    analysis: AnalysisResult | None = None


class HistoryItem(BaseModel):
    id: str
    reference_title: str
    performance_score: float
    tempo_accuracy: float
    note_accuracy: float
    stability: float
    created_at: datetime


class UploadResponse(BaseModel):
    recording_id: str
    filename: str
    reference_id: str
    reference_title: str
    analysis: AnalysisResult


class FeedbackResponse(BaseModel):
    recording_id: str
    feedback: str
    metrics: AnalysisMetrics
    errors: list[NoteError]


class HealthResponse(BaseModel):
    status: str
    database: str
    references: int
