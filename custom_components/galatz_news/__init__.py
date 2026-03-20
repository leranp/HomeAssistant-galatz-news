import datetime
import logging
import re

import requests

DOMAIN = "galatz_news"
_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    def play_galatz_news_service(call):
        """Handle the service call."""
        media_player_entity_id = call.data.get("entity_id")

        now = datetime.datetime.now()
        date_hour = now.strftime("%y%m%d-%H")

        url = (
            f"https://api.bynetcdn.com/Redirector/glz/{date_hour}_News/PD"
            f"?awCollectionId=1111&ExternalId={date_hour}_News"
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Rigor/1.0.0; http://rigor.com)"
        }

        try:
            r = requests.head(url, headers=headers, timeout=10, allow_redirects=False)
            redirect_url = r.headers.get("Location", "")
        except requests.RequestException:
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

        hass.services.call(
            "media_player",
            "play_media",
            {
                "entity_id": media_player_entity_id,
                "media_content_id": mp3_url,
                "media_content_type": "music",
            },
        )

    def play_kan_news_service(call):
        """Handle the service call."""
        media_player_entity_id = call.data.get("entity_id")

        stream_url = _get_kan_news_url()
        if not stream_url:
            _LOGGER.error("Could not retrieve KAN news stream URL")
            return

        _LOGGER.debug("Playing KAN news: %s", stream_url)

        hass.services.call(
            "media_player",
            "play_media",
            {
                "entity_id": media_player_entity_id,
                "media_content_id": stream_url,
                "media_content_type": "music",
            },
        )

    hass.services.register(DOMAIN, "play_galatz_news", play_galatz_news_service)
    hass.services.register(DOMAIN, "play_kan_news", play_kan_news_service)

    return True


def _get_kan_news_url():
    """
    Fetch the latest hourly news stream URL from KAN radio.

    KAN's website is protected by Cloudflare, which blocks plain HTTP requests.
    cloudscraper bypasses this protection and retrieves the full server-rendered
    HTML, which contains the stream URL in a `data-player-src` attribute.

    Returns the HLS stream URL (m3u8), or None on failure.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8",
    }
    try:
        response = requests.get(
            "https://www.kan.org.il/radio/hourlynews.aspx",
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        _LOGGER.error("Failed to fetch KAN news page: %s", e)
        return None

    _LOGGER.debug(
        "KAN page: status=%s length=%s", response.status_code, len(response.text)
    )

    match = re.search(r'data-player-src="([^"]+)"', response.text)
    if not match:
        _LOGGER.error(
            "Could not find data-player-src in KAN page "
            "(status=%s, length=%s, snippet=%.200s)",
            response.status_code,
            len(response.text),
            response.text,
        )
        return None

    stream_url = match.group(1).replace("&amp;", "&")

    # פרוטוקול יחסי (//...) — הוסף https:
    if stream_url.startswith("//"):
        stream_url = "https:" + stream_url

    return stream_url
