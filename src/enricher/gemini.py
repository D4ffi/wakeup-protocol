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

El mensaje DEBE incluir TODAS estas secciones en este orden:
1. SALUDO: Reemplaza {{ ENRICH_SALUDO }} con un saludo creativo (no siempre "buenos dias"). Maximo 2 oraciones.
2. FECHA: Menciona el dia y fecha que aparece en el esqueleto.
3. CLIMA: SIEMPRE incluye la temperatura, condicion y sensacion termica del esqueleto. Hazlo sonar natural.
4. TAREAS: Si hay tareas de ClickUp, mencionalas TODAS con nombre. Si no hay, di que es dia tranquilo.
5. CIERRE: Reemplaza {{ ENRICH_CIERRE }} con una frase de animo breve. Maximo 2 oraciones.

REGLAS:
- NUNCA omitas el clima ni las tareas. Es informacion que Daffi necesita para su dia.
- El mensaje sera leido en voz alta por un TTS: nada de emojis, markdown, asteriscos, guiones, o formato especial.
- El mensaje completo no debe pasar de 10 oraciones.
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
                            "Enriquece este esqueleto de mensaje de buenos dias. "
                            "IMPORTANTE: Incluye TODA la informacion (fecha, clima con temperatura, tareas). "
                            "Solo reescribelo para que suene natural, no elimines datos.\n\n"
                            f"ESQUELETO:\n{skeleton}"
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
