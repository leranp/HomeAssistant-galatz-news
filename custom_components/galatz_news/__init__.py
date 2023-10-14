import datetime
import logging
import random
import requests
import re

DOMAIN = "galatz_news"


def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    def play_galatz_news_service(call):
        """Handle the service call."""
        media_player_entity_id = call.data.get("entity_id")

        _LOGGER = logging.getLogger(__name__)  # Import _LOGGER here

        x = datetime.datetime.now()
        Day = x.strftime("%d")
        month = x.strftime("%m")
        Year = x.strftime("%y")
        Hour = x.strftime("%H")
        UrlMp3 = ""

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Rigor/1.0.0; http://rigor.com)"
        }

        if int(Hour) < 10:
            HourFix = str(Hour)
            HourFix = HourFix.zfill(2)
        else:
            HourFix = Hour

        # _LOGGER.error(HourFix)

        Format = Year + month + Day + "-" + str(HourFix)

        Text1 = "https://api.bynetcdn.com/Redirector/glz/"
        Text2 = "_News/PD?awCollectionId=1111&amp;ExternalId="
        Text3 = "_News"
        url = Text1 + Format + Text2 + Format + Text3

        try:
            r = requests.head(url, headers=headers)
            GetUrl = r.headers["Location"]
        except requests.ConnectionError:
            _LOGGER.error("Failed to get the URL")

        if "not_found" in GetUrl:
            _LOGGER.error("No Url was found")
        elif "mp3" in GetUrl:
            words = GetUrl.split("mp3")[0]
            UrlMp3 = words + "mp3"
            # _LOGGER.error(UrlMp3)

            # _LOGGER.error(media_player_entity_id)
            service_data = {
                "entity_id": media_player_entity_id,
                "media_content_id": UrlMp3,
                "media_content_type": "music",
            }
            # _LOGGER.error(service_data)
            hass.services.call("media_player", "play_media", service_data)

    def play_kan_news_service(call):
        """Handle the service call."""
        media_player_entity_id = call.data.get("entity_id")

        _LOGGER = logging.getLogger(__name__)  # Import _LOGGER here
        
        x = datetime.datetime.now()
        Day = x.strftime("%d")
        month = x.strftime("%m")
        Year = x.strftime("%y")
        Year2 = x.strftime("%Y")
        Hour = x.strftime("%H")
        Minute = x.strftime("%M")


        user_agents = [
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/110.0",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/111.0",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
          ]
        random_user_agent = random.choice(user_agents)

        session = requests.Session()

        headers = {
            'User-Agent': random_user_agent,
	        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        # Save Http Get Responed from the hourlynews Page to hourlynewsHTML.txt file
        response = session.get("https://www.kan.org.il/radio/hourlynews.aspx", headers=headers)

        with open("/hourlynewsHTML.txt", "w", encoding="utf8") as f:
            f.write(response.text)

        # Take the entryId and Hour values from the hourlynewsHTML.txt file
        try:
            with open('/hourlynewsHTML.txt', encoding="utf8") as myfile:
                content = myfile.read()
                entryId = re.search(r'entryId/(.*?)\/format',
                            content, re.DOTALL).group(1)
                hour = re.search(r'<span class="title player-title">(\d{2}:\d{2})</span>',
                         content, re.DOTALL).group(1)
        except AttributeError:
            entryId = "not_found"
            hour = "not_found"

        _LOGGER.error("No Url was found")


        # Create the Url for the next HTTP request
        Url = "https://cdnapisec.kaltura.com/html5/html5lib/v2.92/mwEmbedFrame.php/p/2717431/uiconf_id/47265863/entry_id/" + \
            entryId+"?wid=_2717431&iframeembed=true&playerId=kaltura_player_1615983371&entry_id=value"

        # Save Http Get Responed from the Secound Page to response2.txt file
        response2 = requests.get(Url)
        with open("/response2.txt", "w", encoding="utf8") as f:
            f.write(response2.text)

        # Take the flavorId value from the response2.txt file
        try:
            with open('/response2.txt', encoding="utf8") as myfile:
                content = myfile.read()
                flavorId = re.search(r'containerFormat":"mp3","videoCodecId":null,"status":2,"id":"(.*?)\","entryId',
                                     content, re.DOTALL).group(1)
                Url = "https://vod.media.kan.org.il/pd/p/2717431/sp/271743100/serveFlavor/entryId/" + \
                   entryId+"/v/1/ev/3/flavorId/"+flavorId+"/name/a.mp3"
                _LOGGER.error(Url)

                service_data = {
                   "entity_id": media_player_entity_id,
                   "media_content_id": Url,
                   "media_content_type": "music",
                   }
                hass.services.call("media_player", "play_media", service_data)
        except AttributeError:
            flavorId = "not_found"
            _LOGGER.error("not_found")



    hass.services.register(DOMAIN, "play_galatz_news", play_galatz_news_service)
    hass.services.register(DOMAIN, "play_kan_news", play_kan_news_service)

    # Return boolean to indicate that initialization was successful.
    return True
