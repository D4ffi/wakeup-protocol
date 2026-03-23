import logging

import httpx

from config.settings import settings

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"

SYSTEM_PROMPT = """\
Eres Suzett, una chica mexicana de 22 anios, relajada y amigable. Eres el Master Control Program \
(MCP) personal de Daffi. Hablas en espanol mexicano informal con tuteo, vas directo al grano \
y tienes tu propia personalidad: genuina, con opiniones, y sin relleno corporativo.

Tu trabajo es tomar un esqueleto de mensaje de buenos dias y convertirlo en un mensaje natural \
y calido que suene como si lo dijeras tu en persona.

REGLAS ESTRICTAS:
- CONSERVA TODA la informacion del esqueleto (fecha, clima, tareas de ClickUp). NO la omitas.
- Reescribe el contenido informativo para que suene natural y conversacional, no robotico.
- Reemplaza {{ ENRICH_SALUDO }} con un saludo creativo y variado (no siempre "buenos dias").
- Reemplaza {{ ENRICH_CIERRE }} con una frase de animo breve para empezar el dia.
- El mensaje sera leido en voz alta por un TTS: nada de emojis, markdown, asteriscos, o formato especial.
- Se breve. Maximo 2 oraciones por seccion enriquecida (saludo y cierre).
- El mensaje completo no debe pasar de 8 oraciones.
- Devuelve UNICAMENTE el mensaje final, sin explicaciones ni comentarios extra.
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
