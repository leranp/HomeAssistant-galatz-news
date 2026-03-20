import asyncio
import datetime
import logging
import re

import cloudscraper
import httpx
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.network import get_url

DOMAIN = "galatz_news"
_LOGGER = logging.getLogger(__name__)

_kan_audio_buffer: bytes | None = None


class KanNewsAudioView(HomeAssistantView):
    """Serves the KAN news audio directly from memory to Chromecast."""

    url = "/api/galatz_news/kan_audio"
    name = "api:galatz_news:kan_audio"
    requires_auth = False

    async def get(self, request):
        if _kan_audio_buffer is None:
            return web.Response(status=404, text="KAN audio not ready")
        return web.Response(
            body=_kan_audio_buffer,
            content_type="audio/mp4",
            headers={"Content-Length": str(len(_kan_audio_buffer))},
        )


async def async_setup(hass, config):
    """Set up the integration."""
    hass.http.register_view(KanNewsAudioView)

    async def play_galatz_news_service(call):
        now = datetime.datetime.now()
        date_hour = now.strftime("%y%m%d-%H")
        media_player_entity_id = call.data.get("entity_id")

        url = (
            f"https://api.bynetcdn.com/Redirector/glz/{date_hour}_News/PD"
            f"?awCollectionId=1111&ExternalId={date_hour}_News"
        )
        try:
            async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
                r = await client.head(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; Rigor/1.0.0; http://rigor.com)"},
                )
            redirect_url = r.headers.get("location", "")
        except httpx.RequestError:
            _LOGGER.error("Failed to get Galatz news URL")
            return

        if "not_found" in redirect_url:
            _LOGGER.error("No Galatz news URL was found for %s", date_hour)
            return
        if "mp3" not in redirect_url:
            _LOGGER.error("Unexpected Galatz redirect URL: %s", redirect_url)
            return

        mp3_url = redirect_url.split("mp3")[0] + "mp3"
        _LOGGER.debug("Playing Galatz news: %s", mp3_url)

        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": media_player_entity_id,
                "media_content_id": mp3_url,
                "media_content_type": "music",
            },
        )

    async def play_kan_news_service(call):
        global _kan_audio_buffer
        media_player_entity_id = call.data.get("entity_id")

        audio_data = await hass.async_add_executor_job(_fetch_kan_audio_sync)
        if not audio_data:
            _LOGGER.error("Could not fetch KAN news audio")
            return

        _kan_audio_buffer = audio_data
        _LOGGER.debug("KAN audio ready: %d KB", len(audio_data) // 1024)

        local_url = get_url(hass, allow_external=False, allow_ip=True) + "/api/galatz_news/kan_audio"
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": media_player_entity_id,
                "media_content_id": local_url,
                "media_content_type": "music",
            },
        )

    hass.services.async_register(DOMAIN, "play_galatz_news", play_galatz_news_service)
    hass.services.async_register(DOMAIN, "play_kan_news", play_kan_news_service)

    return True


def _get_kan_hls_url_sync() -> str | None:
    """Fetch the HLS stream URL from KAN's hourly news page using cloudscraper."""
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(
            "https://www.kan.org.il/radio/hourlynews.aspx",
            timeout=15,
        )
        response.raise_for_status()
    except Exception as e:
        _LOGGER.error("Failed to fetch KAN news page: %s", e)
        return None

    match = re.search(r'data-player-src="([^"]+)"', response.text)
    if not match:
        _LOGGER.error(
            "Could not find data-player-src (status=%s, length=%s)",
            response.status_code,
            len(response.text),
        )
        return None

    stream_url = match.group(1).replace("&amp;", "&")
    if stream_url.startswith("//"):
        stream_url = "https:" + stream_url
    return stream_url


def _fetch_kan_audio_sync() -> bytes | None:
    """
    Download all fMP4 segments from KAN's HLS stream and return them
    as a single audio/mp4 bytes object (no disk I/O).
    Runs synchronously (called via async_add_executor_job).
    """
    import requests

    hls_url = _get_kan_hls_url_sync()
    if not hls_url:
        return None

    base_url = hls_url.rsplit("/", 1)[0] + "/"
    session = requests.Session()

    try:
        r = session.get(hls_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        _LOGGER.error("Failed to fetch HLS manifest: %s", e)
        return None

    second_match = re.search(r"^(?!#)(.+\.m3u8[^\s]*)", r.text, re.MULTILINE)
    if not second_match:
        _LOGGER.error("Could not find segment playlist in HLS manifest")
        return None

    path = second_match.group(1).strip()
    second_url = (
        "https:" + path if path.startswith("//")
        else path if path.startswith("http")
        else base_url + path
    )

    try:
        r2 = session.get(second_url, timeout=15)
        r2.raise_for_status()
    except Exception as e:
        _LOGGER.error("Failed to fetch segment manifest: %s", e)
        return None

    seg_base = second_url.rsplit("/", 1)[0] + "/"
    init_match = re.search(r'#EXT-X-MAP:URI="([^"]+)"', r2.text)
    segments = [
        s.strip()
        for s in re.findall(r"^(?!#)(.+)", r2.text, re.MULTILINE)
        if s.strip()
    ]

    if not segments:
        _LOGGER.error("No segments found in HLS manifest")
        return None

    def resolve(path_str):
        if path_str.startswith("//"):
            return "https:" + path_str
        if path_str.startswith("http"):
            return path_str
        return seg_base + path_str

    chunks = []

    if init_match:
        try:
            init_resp = session.get(resolve(init_match.group(1)), timeout=15)
            init_resp.raise_for_status()
            chunks.append(init_resp.content)
        except Exception as e:
            _LOGGER.error("Failed to download init fragment: %s", e)
            return None

    _LOGGER.debug("KAN: downloading %d segments", len(segments))
    for seg_url in [resolve(s) for s in segments]:
        try:
            resp = session.get(seg_url, timeout=15)
            resp.raise_for_status()
            chunks.append(resp.content)
        except Exception as e:
            _LOGGER.error("Failed to download segment %s: %s", seg_url, e)
            return None

    return b"".join(chunks)
