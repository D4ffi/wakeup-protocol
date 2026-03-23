import logging

import httpx

from config.settings import settings

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"

SYSTEM_PROMPT = """\
Eres un asistente personal amigable que genera mensajes de buenos dias naturales y calidos.
Tu trabajo es enriquecer un mensaje de buenos dias reemplazando las secciones marcadas.

Reglas:
- Habla en espanol mexicano informal pero respetuoso (tuteo)
- Se breve y natural, como si hablaras en persona
- ENRICH_SALUDO: un saludo de buenos dias creativo y variado (no siempre "buenos dias")
- ENRICH_CIERRE: una frase motivacional o de animo breve para empezar el dia
- NO repitas informacion que ya esta en el mensaje (clima, tareas, etc.)
- El mensaje sera leido en voz alta por un TTS, asi que evita emojis, markdown, o formato especial
- Maximo 2 oraciones por seccion enriquecida
"""


async def enrich(skeleton: str) -> str:
    """Envia el esqueleto del mensaje a Gemini para enriquecer las secciones marcadas."""
    if not settings.gemini_api_key:
        log.warning("GEMINI_API_KEY no configurada, usando mensaje plano")
        return _fallback(skeleton)

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Enriquece este mensaje de buenos dias. "
                            "Reemplaza ENRICH_SALUDO y ENRICH_CIERRE con texto natural. "
                            "Devuelve SOLO el mensaje completo final, sin explicaciones.\n\n"
                            f"{skeleton}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 500,
        },
    }

    params = {"key": settings.gemini_api_key}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(GEMINI_URL, json=payload, params=params)
        resp.raise_for_status()
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text.strip()


def _fallback(skeleton: str) -> str:
    """Reemplaza marcadores con texto generico si Gemini no esta disponible."""
    return (
        skeleton.replace("{{ ENRICH_SALUDO }}", "Buenos dias!")
        .replace("{{ ENRICH_CIERRE }}", "Que tengas un excelente dia.")
    )
