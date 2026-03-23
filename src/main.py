import asyncio
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader

from config.settings import settings
from src.collectors import datetime_info, weather, tasks
from src.enricher.openclaw import enrich as openclaw_enrich
from src.enricher.gemini import enrich as gemini_enrich, _fallback
# Delivery se maneja via cliente local (cast a Google Home / bocinas PC)

log = logging.getLogger(__name__)

AUDIO_DIR = Path(__file__).parent.parent / "audio"
TEMPLATE_DIR = Path(__file__).parent.parent / "config" / "templates"


def _get_tts_engine():
    if settings.tts_engine == "elevenlabs":
        from src.tts.elevenlabs import ElevenLabsTTS
        return ElevenLabsTTS()
    from src.tts.edge import EdgeTTS
    return EdgeTTS()


async def run_pipeline():
    """Ejecuta el pipeline completo: collect -> template -> enrich -> tts -> deliver."""
    logging.basicConfig(level=settings.log_level)
    log.info("Iniciando pipeline de buenos dias")

    # 1. Recopilar datos en paralelo
    dt_data, weather_data, tasks_data = await asyncio.gather(
        datetime_info.collect(),
        _safe_collect(weather.collect, "clima"),
        _safe_collect(tasks.collect, "tareas"),
    )

    # 2. Renderizar template con datos
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("buenos_dias.j2")

    skeleton = template.render(
        dt=dt_data,
        clima=weather_data,
        clickup=tasks_data,
        ENRICH_SALUDO="{{ ENRICH_SALUDO }}",
        ENRICH_CIERRE="{{ ENRICH_CIERRE }}",
    )

    log.info("Esqueleto generado:\n%s", skeleton)

    # 3. Enriquecer: OpenClaw -> Gemini fallback -> texto plano
    message = None

    if settings.openclaw_url and settings.openclaw_token:
        try:
            message = await openclaw_enrich(skeleton)
            log.info("Mensaje enriquecido con OpenClaw")
        except Exception:
            log.exception("Error con OpenClaw, intentando fallback Gemini")

    if message is None and settings.gemini_api_key:
        try:
            message = await gemini_enrich(skeleton)
            log.info("Mensaje enriquecido con Gemini (fallback)")
        except Exception:
            log.exception("Error con Gemini, usando esqueleto plano")

    if message is None:
        message = _fallback(skeleton)

    log.info("Mensaje final:\n%s", message)

    # 4. TTS
    AUDIO_DIR.mkdir(exist_ok=True)
    tz = ZoneInfo(settings.timezone)
    timestamp = datetime.now(tz).strftime("%Y%m%d_%H%M%S")
    audio_path = AUDIO_DIR / f"buenos_dias_{timestamp}.mp3"

    tts = _get_tts_engine()
    try:
        await tts.synthesize(message, audio_path)
    except Exception:
        log.exception("Error con %s, intentando fallback edge-tts", settings.tts_engine)
        if settings.tts_engine != "edge":
            from src.tts.edge import EdgeTTS
            await EdgeTTS().synthesize(message, audio_path)
        else:
            raise

    # 5. Audio listo — el cliente local se encarga del delivery
    audio_url = f"{settings.audio_base_url}/audio/{audio_path.name}"
    log.info("Pipeline completado. Audio disponible en: %s", audio_url)
    return audio_url


async def _safe_collect(coro_fn, name: str):
    """Ejecuta un collector con manejo de errores silencioso."""
    try:
        return await coro_fn()
    except Exception:
        log.exception("Error recopilando %s", name)
        return None


if __name__ == "__main__":
    asyncio.run(run_pipeline())
