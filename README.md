# HomeAssistant integration for playing the latest hourly news from Galatz and KAN Radio stations

[![](https://img.shields.io/github/release/leranp/galatz-news/all.svg?style=for-the-badge)](https://github.com/leranp/HomeAssistant-galatz-news/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/badge/MAINTAINER-%40leranp-red?style=for-the-badge)](https://github.com/leranp)
[![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge)](https://community.home-assistant.io)

![Galatz Logo](https://upload.wikimedia.org/wikipedia/commons/3/30/GaltzLogo.svg)


## Installation

Installation via [HACS](https://hacs.xyz/) (recommended) or by copying `custom_components/galatz_news` into your Home Assistant configuration directory.

## Configuration

After installation, add the integration via **Settings → Devices & Services → Add Integration** and search for **Galatz & KAN News**. No manual configuration required.

## Services

### `galatz_news.play_galatz_news`
Plays the latest hourly news from **Galatz** (IDF Radio) on the selected media player.

The audio is streamed directly as MP3 from the Galatz CDN.

```yaml
service: galatz_news.play_galatz_news
data:
  entity_id: media_player.your_speaker
```

---

### `galatz_news.play_kan_news`
Plays the latest hourly news from **KAN** (Israeli Public Broadcasting) on the selected media player.

The audio is fetched from KAN's HLS stream, buffered in memory, and served locally — making it compatible with Chromecast and other media players that cannot play HLS directly.

```yaml
service: galatz_news.play_kan_news
data:
  entity_id: media_player.your_speaker
```

## Notes

- Both services are compatible with Chromecast devices (Google Home, Nest, etc.)
- The KAN service may take a few seconds to buffer the audio before playback begins
- This integration only works from within Israel due to geo-restrictions on KAN's website

## Disclaimer

This integration is not affiliated with or endorsed by Galatz or KAN. I am not responsible for any loss or damage caused by this integration.
