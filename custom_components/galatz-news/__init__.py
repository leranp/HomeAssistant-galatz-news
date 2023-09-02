import datetime
import requests
import logging
import urllib
import os

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
        UrlMp3 = ''

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Rigor/1.0.0; http://rigor.com)'
        }

        if int(Hour) < 10 :
            HourFix = str(Hour)
            HourFix = HourFix.zfill(2)
        else:
            HourFix = Hour
            
        _LOGGER.error(HourFix)
        
        Format = Year + month + Day + "-" + str(HourFix)

        Text1 = "https://api.bynetcdn.com/Redirector/glz/"
        Text2 = "_News/PD?awCollectionId=1111&amp;ExternalId="
        Text3 = "_News"

        url =  Text1 + Format + Text2 + Format + Text3

        try:
            r = requests.head(url, headers=headers)
            GetUrl = r.headers['Location']
        except requests.ConnectionError:
            _LOGGER.error("Failed to get the URL")
            
        if "not_found" in GetUrl:
                no_url = "No Url"
                _LOGGER.error("No Url was found")
        elif "mp3" in GetUrl:
                words = GetUrl.split("mp3")[0]
                UrlMp3 = words + "mp3"
                _LOGGER.error(UrlMp3)
                
                _LOGGER.error(media_player_entity_id)
                service_data = {"entity_id":media_player_entity_id,"media_content_id":UrlMp3,"media_content_type":"music"}
                _LOGGER.error(service_data)
                hass.services.call('media_player', 'play_media', service_data)

    hass.services.register(DOMAIN, "play_galatz_news", play_galatz_news_service)

    # Return boolean to indicate that initialization was successful.
    return True
