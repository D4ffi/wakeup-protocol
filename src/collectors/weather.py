import logging

import httpx

from config.settings import settings

log = logging.getLogger(__name__)

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


async def collect() -> dict | None:
    if not settings.openweather_api_key:
        log.warning("OPENWEATHER_API_KEY no configurada, omitiendo clima")
        return None

    params = {
        "q": settings.openweather_city,
        "appid": settings.openweather_api_key,
        "units": "metric",
        "lang": "es",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(OWM_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    weather = data["weather"][0]
    main = data["main"]

    return {
        "temperatura": round(main["temp"]),
        "sensacion": round(main["feels_like"]),
        "humedad": main["humidity"],
        "condicion": weather["description"],
        "ciudad": settings.openweather_city.split(",")[0],
    }
