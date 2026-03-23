from datetime import datetime
from zoneinfo import ZoneInfo

from config.settings import settings

DIAS = [
    "lunes", "martes", "miercoles", "jueves",
    "viernes", "sabado", "domingo",
]

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


async def collect() -> dict:
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)

    return {
        "hora": now.strftime("%H:%M"),
        "dia_semana": DIAS[now.weekday()],
        "dia": now.day,
        "mes": MESES[now.month - 1],
        "anio": now.year,
        "fecha_legible": f"{DIAS[now.weekday()]} {now.day} de {MESES[now.month - 1]}",
        "es_fin_de_semana": now.weekday() >= 5,
    }
