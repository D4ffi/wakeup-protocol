import logging
from pathlib import Path

import edge_tts

from config.settings import settings
from src.tts.base import TTSEngine

log = logging.getLogger(__name__)


class EdgeTTS(TTSEngine):
    async def synthesize(self, text: str, output_path: Path) -> Path:
        communicate = edge_tts.Communicate(text, settings.edge_tts_voice)
        await communicate.save(str(output_path))
        log.info("Audio generado con edge-tts: %s", output_path)
        return output_path
