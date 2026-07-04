import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from config import settings
from database import close_db, connect_db
from routes.audio import router as audio_router
from services.reference_service import reference_service
from storage import init_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await connect_db()
    mode = await init_storage(db)
    app.state.storage_mode = mode
    yield
    await close_db()


app = FastAPI(
    title="Bağlama Performans Analiz API",
    description="Bağlama çalışını analiz eden ses işleme sistemi",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audio_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "database": app.state.storage_mode,
        "references": len(reference_service.list_songs()),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
