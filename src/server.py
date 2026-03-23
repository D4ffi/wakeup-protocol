import logging
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings

log = logging.getLogger(__name__)

AUDIO_DIR = Path(__file__).parent.parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Wakey-Wakey", version="1.0.0")

# Servir archivos de audio estaticos
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(background_tasks: BackgroundTasks):
    """Trigger manual para generar el mensaje de buenos dias."""
    from src.main import run_pipeline

    background_tasks.add_task(run_pipeline)
    return JSONResponse(
        {"status": "generating", "message": "Pipeline iniciado en background"},
        status_code=202,
    )


@app.get("/latest")
async def latest():
    """Retorna el audio mas reciente."""
    files = sorted(AUDIO_DIR.glob("*.mp3"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return JSONResponse({"error": "No hay audios generados"}, status_code=404)
    return FileResponse(files[0], media_type="audio/mpeg")


def start_server():
    import uvicorn

    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=settings.audio_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    start_server()
