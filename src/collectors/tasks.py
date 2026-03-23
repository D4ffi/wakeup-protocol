import logging
from datetime import datetime, timezone

import httpx

from config.settings import settings

log = logging.getLogger(__name__)

CLICKUP_API = "https://api.clickup.com/api/v2"


async def collect() -> dict | None:
    if not settings.clickup_api_token:
        log.warning("CLICKUP_API_TOKEN no configurado, omitiendo tareas")
        return None

    headers = {"Authorization": settings.clickup_api_token}

    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        # Obtener equipos para sacar las tareas del usuario
        teams_resp = await client.get(f"{CLICKUP_API}/team")
        teams_resp.raise_for_status()
        teams = teams_resp.json()["teams"]

        if not teams:
            return {"tareas": [], "total": 0}

        team_id = teams[0]["id"]

        # Tareas asignadas al usuario, filtradas por fecha de hoy
        now = datetime.now(timezone.utc)
        start_of_day = int(now.replace(hour=0, minute=0, second=0).timestamp() * 1000)
        end_of_day = int(now.replace(hour=23, minute=59, second=59).timestamp() * 1000)

        params = {
            "due_date_gt": str(start_of_day),
            "due_date_lt": str(end_of_day),
            "subtasks": "true",
            "include_closed": "false",
        }

        tasks_resp = await client.get(
            f"{CLICKUP_API}/team/{team_id}/task", params=params
        )
        tasks_resp.raise_for_status()
        raw_tasks = tasks_resp.json()["tasks"]

    tareas = [
        {
            "nombre": t["name"],
            "estado": t["status"]["status"],
            "prioridad": (t.get("priority") or {}).get("priority", "sin prioridad"),
            "lista": t.get("list", {}).get("name", ""),
        }
        for t in raw_tasks
    ]

    return {"tareas": tareas, "total": len(tareas)}
