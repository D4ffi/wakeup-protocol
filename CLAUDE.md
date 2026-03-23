# Wakey-Wakey

Servicio complementario para un agente personal (OpenClaw + Gemini API) que genera mensajes de "buenos dias" personalizados con TTS y los reproduce en Google Home.

## Arquitectura

Pipeline secuencial ejecutado por cron:

1. **Collectors** recopilan datos (clima, tareas ClickUp, fecha/hora)
2. **Template** Jinja2 arma un esqueleto del mensaje con los datos
3. **Enricher** envia el esqueleto a OpenClaw (primary) o Gemini API (fallback) para darle dinamismo y naturalidad
4. **TTS** convierte el texto final a audio .mp3 (ElevenLabs primary, edge-tts fallback)
5. **Delivery** sirve el audio en URL publica y hace cast a Google Home via pychromecast

## Stack

- Python 3.12
- FastAPI (servidor de audio + endpoints de control)
- Jinja2 (templates de mensajes)
- httpx (HTTP client async)
- pydantic-settings (configuracion via .env)
- pychromecast (cast directo a Google Home)
- edge-tts / ElevenLabs (TTS)
- Docker + docker-compose

## Infraestructura

- **wakey-wakey corre en VPS** (configurar `VPS_HOST` en `.env`)
  - Genera audio y lo sirve en URL publica
  - Comparte red Docker con OpenClaw (`openclaw-tca0_default`)
  - URL interna del enricher: `http://openclaw:40291`
- **OpenClaw corre en la misma VPS**
  - Contenedor en red Docker compartida
  - Gateway HTTP accesible internamente
- **Cliente local** (PC/dispositivo en casa) descarga el audio y:
  - Cast a Google Home via pychromecast (primario)
  - Reproduce por bocinas del PC (fallback)

## Estructura

```
config/settings.py              - Configuracion central (pydantic-settings, carga .env)
config/templates/*.j2           - Templates Jinja2 de mensajes
src/main.py                     - Entry point, orquesta el pipeline
src/server.py                   - FastAPI server (sirve audios + /health + /generate)
src/collectors/weather.py       - OpenWeatherMap API
src/collectors/tasks.py         - ClickUp API
src/collectors/datetime_info.py - Fecha, hora, dia de la semana
src/enricher/openclaw.py        - OpenClaw agent API (enricher principal)
src/enricher/gemini.py          - Gemini API (enricher fallback)
src/tts/base.py                 - Interfaz base TTSEngine
src/tts/elevenlabs.py           - ElevenLabs TTS
src/tts/edge.py                 - edge-tts (fallback gratuito)
src/delivery/chromecast.py      - Cast a Google Home via pychromecast (protocolo directo)
client/                         - Cliente local (futuro) para delivery a Google Home / bocinas
```

## Comandos

```bash
# Desarrollo local
pip install -r requirements.txt
python -m src.main              # Ejecutar pipeline una vez
python -m src.server            # Levantar servidor de audio

# Docker
docker-compose up -d            # Levantar todo (server + cron)
docker-compose logs -f          # Ver logs

# Test manual
curl http://localhost:8123/health
curl -X POST http://localhost:8123/generate
```

## Variables de entorno

Ver `.env.example` para la lista completa. Las criticas son:
- `OPENWEATHER_API_KEY` + `OPENWEATHER_CITY`
- `CLICKUP_API_TOKEN`
- `OPENCLAW_URL` + `OPENCLAW_TOKEN` (enricher principal, URL interna Docker)
- `GEMINI_API_KEY` (enricher fallback)
- `TTS_ENGINE` (elevenlabs | edge)
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` (si TTS_ENGINE=elevenlabs)
- `CHROMECAST_DEVICE` (nombre exacto del Google Home)
- `AUDIO_BASE_URL` (URL publica de la VPS donde se sirve el audio)

## Convenciones

- Async everywhere (httpx, edge-tts, FastAPI son todos async)
- Collectors retornan dicts planos que se pasan al template
- Fallbacks silenciosos: si un collector falla, se omite esa seccion del mensaje
- Logs con `logging` stdlib, nivel configurable via `LOG_LEVEL`
- Fallback chain: OpenClaw -> Gemini -> texto plano (para enricher), ElevenLabs -> edge-tts (para TTS)
