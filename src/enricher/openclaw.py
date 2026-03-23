import logging

import httpx

from config.settings import settings

log = logging.getLogger(__name__)

ENRICH_PROMPT = (
    "Enriquece este mensaje de buenos dias. "
    "Reemplaza ENRICH_SALUDO y ENRICH_CIERRE con texto natural. "
    "El mensaje sera leido en voz alta por un TTS, asi que evita emojis, markdown, o formato especial. "
    "Devuelve SOLO el mensaje completo final, sin explicaciones.\n\n"
)


async def enrich(skeleton: str) -> str:
    """Envia el esqueleto del mensaje al agente de OpenClaw para enriquecerlo."""
    url = f"{settings.openclaw_url}/v1/responses"

    headers = {
        "Authorization": f"Bearer {settings.openclaw_token}",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": settings.openclaw_agent_id,
    }

    payload = {
        "model": "openclaw",
        "input": f"{ENRICH_PROMPT}{skeleton}",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # La respuesta de OpenResponses viene en data.output[]
    # Buscamos el primer item de tipo "message" con role "assistant"
    for item in data.get("output", []):
        if item.get("type") == "message" and item.get("role") == "assistant":
            parts = item.get("content", [])
            texts = [p["text"] for p in parts if p.get("type") == "output_text"]
            if texts:
                return "\n".join(texts).strip()

    # Fallback: si la estructura es diferente, intentar text directo
    if "output_text" in data:
        return data["output_text"].strip()

    raise ValueError("No se pudo extraer respuesta del agente OpenClaw")
