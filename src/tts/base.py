from abc import ABC, abstractmethod
from pathlib import Path


class TTSEngine(ABC):
    @abstractmethod
    async def synthesize(self, text: str, output_path: Path) -> Path:
        """Convierte texto a audio y guarda en output_path. Retorna el path del archivo."""
        ...
