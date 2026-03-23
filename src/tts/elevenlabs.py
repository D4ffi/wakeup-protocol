import logging
from pathlib import Path

import httpx

from config.settings import settings
from src.tts.base import TTSEngine

log = logging.getLogger(__name__)

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"


class ElevenLabsTTS(TTSEngine):
    async def synthesize(self, text: str, output_path: Path) -> Path:
        url = f"{ELEVENLABS_URL}/{settings.elevenlabs_voice_id}"

        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.3,
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)

        log.info("Audio generado con ElevenLabs: %s", output_path)
        return output_path
