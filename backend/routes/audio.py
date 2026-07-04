import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from config import settings
from services.analysis_service import analysis_service
from services.reference_service import reference_service

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.audio_loader import load_audio
from ml.pitch_detector import extract_pitch_contour, hz_to_note
from ml.note_matcher import extract_note_sequence

router = APIRouter(prefix="/api", tags=["audio"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm"}


@router.post("/debug-pitch")
async def debug_pitch(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    safe_name = f"{uuid.uuid4()}{suffix}"
    save_path = settings.upload_path / safe_name
    content = await file.read()
    save_path.write_bytes(content)

    y, sr = load_audio(save_path)
    times, f0, _ = extract_pitch_contour(y, sr)
    notes = extract_note_sequence(f0)
    valid_f0 = [round(float(x), 1) for x in f0 if x is not None and not __import__('numpy').isnan(x)]

    return {
        "detected_notes": notes,
        "note_count": len(notes),
        "sample_frequencies_hz": valid_f0[:30],
    }


@router.get("/references")
async def list_references():
    return reference_service.list_songs()


@router.get("/references/{reference_id}/notes")
async def get_reference_notes(reference_id: str):
    song = reference_service.get_by_id(reference_id)
    if not song:
        raise HTTPException(status_code=404, detail="Türkü bulunamadı.")
    return {
        "id": song["id"],
        "title": song["title"],
        "notes": [{"note": n["note"], "solfege": n.get("solfege", "")} for n in song.get("notes", [])]
    }


@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    reference_id: str = Form(...),
):
    if not reference_service.get_by_id(reference_id):
        raise HTTPException(status_code=400, detail="Geçersiz referans türkü.")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya formatı. İzin verilenler: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    safe_name = f"{uuid.uuid4()}{suffix}"
    save_path = settings.upload_path / safe_name

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Boş dosya yüklenemez.")

    save_path.write_bytes(content)

    try:
        result = await analysis_service.process_upload(
            file_path=save_path,
            filename=file.filename or safe_name,
            reference_id=reference_id,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {exc}") from exc


@router.get("/analysis/{recording_id}")
async def get_analysis(recording_id: str):
    analysis = await analysis_service.get_analysis(recording_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    return analysis


@router.get("/feedback/{recording_id}")
async def get_feedback(recording_id: str):
    feedback = await analysis_service.get_feedback(recording_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Geri bildirim bulunamadı.")
    return feedback


@router.get("/history")
async def get_history(limit: int = 20):
    return await analysis_service.get_history(limit=limit)
