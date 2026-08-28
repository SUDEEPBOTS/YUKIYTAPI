"""
Drop-in compatibility module for Telegram Music Bots (Yukki, AnonX, Fallen, etc.).
Allows bot owners to replace 1000+ lines of custom Youtube.py with 1 clean import:

    from yukiytapi.compat import YouTubeAPI
    YouTube = YouTubeAPI()
"""

import os
import re
import asyncio
from typing import Union, List, Tuple, Dict, Any, Optional

from .client import YukiAPI, extract_video_id
from .models import Track

class YouTubeAPI:
    def __init__(self, base_url: str = "https://music.yukiapi.site"):
        self.base = "https://www.youtube.com/watch?v="
        self.client = YukiAPI(base_url=base_url)

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        vid = extract_video_id(link)
        return bool(vid and re.match(r'^[a-zA-Z0-9_-]{11}$', vid))

    async def url(self, message_1: Any, message_2: Any = None) -> Optional[str]:
        messages = [message_1, message_2]
        text = ""
        offset = None
        length = None
        for message in messages:
            if not message:
                continue
            if getattr(message, "entities", None):
                for entity in message.entities:
                    if entity.type == "url":
                        text = getattr(message, "text", "") or getattr(message, "caption", "")
                        offset, length = entity.offset, entity.length
                        break
            elif getattr(message, "caption_entities", None):
                for entity in message.caption_entities:
                    if entity.type == "text_link":
                        return entity.url
        if offset is not None:
            return text[offset : offset + length]
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None) -> Tuple[str, str, int, str, str]:
        if videoid:
            link = self.base + link
        track = await self.client.details(link)
        return (track.title, track.duration_min, track.duration_sec, track.thumbnail, track.vidid)

    async def track(self, link: str, videoid: Union[bool, str] = None) -> Tuple[str, str, int, str, str]:
        return await self.details(link, videoid)

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        track = await self.client.details(link)
        return track.title

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        track = await self.client.details(link)
        return track.duration_min

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        track = await self.client.details(link)
        return track.thumbnail

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        tracks = await self.client.search(query, limit=limit)
        return [t.to_dict() for t in tracks]

    async def formats(self, link: str, videoid: Union[bool, str] = None) -> Tuple[List[Dict[str, str]], str]:
        if videoid:
            link = self.base + link
        vid = extract_video_id(link) or link
        formats_list = [
            {"format": "Audio (High Quality)", "ext": "mp3", "format_id": "audio"},
            {"format": "Video (720p HD)", "ext": "mp4", "format_id": "video"}
        ]
        return formats_list, link

    async def playlist(self, link: str, limit: int = 50, user_id: Any = None) -> List[str]:
        tracks = await self.client.playlist(link, limit=limit)
        return [t.id for t in tracks]

    async def download(
        self,
        link: str,
        mystic: Any = None,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> Tuple[str, bool]:
        is_video = bool(video or songvideo or (format_id == "video"))
        req_type = "video" if is_video else "audio"

        if videoid:
            link = self.base + link

        file_path = await self.client.download(link, type=req_type)
        return file_path, True

    async def video(self, link: str, videoid: Union[bool, str] = None) -> Tuple[int, Optional[str]]:
        if videoid:
            link = self.base + link
        try:
            stream_url = await self.client.get_stream(link, type="video")
            return 1, stream_url
        except Exception:
            return 0, None

    async def is_live(self, link: str, videoid: Union[bool, str] = None) -> bool:
        return False

# Alias
YouTube = YouTubeAPI
