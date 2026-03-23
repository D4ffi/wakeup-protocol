import asyncio
import logging
import time

import pychromecast

from config.settings import settings

log = logging.getLogger(__name__)

# Cache del dispositivo para no re-descubrir en cada ejecucion
_cached_cast = None


def _discover_device() -> pychromecast.Chromecast:
    """Descubre el Google Home por nombre en la red local."""
    global _cached_cast

    if _cached_cast is not None:
        try:
            _cached_cast.socket_client.receiver_controller.update_status()
            return _cached_cast
        except Exception:
            log.debug("Cache de chromecast invalido, re-descubriendo")
            _cached_cast = None

    device_name = settings.chromecast_device
    log.info("Buscando dispositivo '%s' en la red...", device_name)

    chromecasts, browser = pychromecast.get_listed_chromecasts(
        friendly_names=[device_name],
    )

    if not chromecasts:
        browser.stop_discovery()
        raise RuntimeError(
            f"No se encontro el dispositivo '{device_name}'. "
            "Verifica que este encendido y en la misma red."
        )

    cast = chromecasts[0]
    cast.wait()
    browser.stop_discovery()

    log.info(
        "Conectado a '%s' (%s)", cast.cast_info.friendly_name, cast.cast_info.host
    )
    _cached_cast = cast
    return cast


def _play_url(cast: pychromecast.Chromecast, audio_url: str) -> None:
    """Reproduce una URL de audio en el dispositivo."""
    mc = cast.media_controller
    mc.play_media(audio_url, "audio/mpeg")
    mc.block_until_active(timeout=10)

    log.info("Reproduciendo audio en '%s'", cast.cast_info.friendly_name)

    # Esperar a que termine de reproducir (polling simple)
    while mc.status.player_is_playing or mc.status.player_is_idle is False:
        time.sleep(1)


async def cast_audio(audio_url: str) -> None:
    """Hace cast del audio al Google Home via Chromecast protocol."""
    device_name = settings.chromecast_device
    if not device_name:
        log.warning("CHROMECAST_DEVICE no configurado, omitiendo cast")
        return

    loop = asyncio.get_event_loop()

    # pychromecast es sync, lo corremos en un thread para no bloquear
    cast = await loop.run_in_executor(None, _discover_device)
    await loop.run_in_executor(None, _play_url, cast, audio_url)

    log.info("Cast completado a '%s'", device_name)
