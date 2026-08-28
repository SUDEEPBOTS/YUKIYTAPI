"""
YukiYTAPI Python SDK
~~~~~~~~~~~~~~~~~~~

The official, ultra-fast Python SDK and API client for the Yuki YouTube Media Streaming & Search Engine.
Designed for Telegram Music Bots (Yukki, AnonX, Fallen), Discord Bots, and Media Applications.

:copyright: (c) 2026 SUDEEPBOTS / HellFireDevs
:license: MIT
"""

from .client import YukiAPI, YukiClient, extract_video_id
from .models import Track
from .errors import YukiAPIError, TrackNotFoundError, TokenError, DownloadError
from .compat import YouTubeAPI, YouTube

__version__ = "1.0.0"
__author__ = "SUDEEPBOTS"
__all__ = [
    "YukiAPI",
    "YukiClient",
    "Track",
    "YukiAPIError",
    "TrackNotFoundError",
    "TokenError",
    "DownloadError",
    "YouTubeAPI",
    "YouTube",
    "extract_video_id",
]
