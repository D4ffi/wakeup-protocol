from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Clima
    openweather_api_key: str = ""
    openweather_city: str = "Monterrey,MX"

    # ClickUp
    clickup_api_token: str = ""

    # OpenClaw (enricher principal)
    openclaw_url: str = ""  # ej: http://openclaw:40291
    openclaw_token: str = ""
    openclaw_agent_id: str = "main"

    # Gemini (enricher fallback)
    gemini_api_key: str = ""

    # TTS
    tts_engine: str = "elevenlabs"  # elevenlabs | edge
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    edge_tts_voice: str = "es-MX-DaliaNeural"

    # Chromecast (Google Home)
    chromecast_device: str = ""  # Nombre del dispositivo (ej: "Google Home Sala")

    # Server
    audio_base_url: str = "http://localhost:8123"
    audio_port: int = 8123

    # Schedule
    wakeup_hour: int = 7
    wakeup_minute: int = 0
    timezone: str = "America/Monterrey"

    # General
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
