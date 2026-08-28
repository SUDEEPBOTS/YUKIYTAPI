import os
import re
import asyncio
import aiohttp
import urllib.parse
from typing import Optional, List, Tuple, Union, Dict, Any

from .models import Track
from .errors import YukiAPIError, TrackNotFoundError, TokenError, DownloadError

DEFAULT_BASE_URL = "https://music.yukiapi.site"
FALLBACK_BASE_URL = "https://yukiapi.site/music"

def extract_video_id(url: str) -> str:
    """Extract 11-char YouTube video ID from any standard or shortened link."""
    if not url:
        return ""
    url = str(url).strip()
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    patterns = [
        r'(?:v=)([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'/shorts/([a-zA-Z0-9_-]{11})',
        r'/embed/([a-zA-Z0-9_-]{11})',
        r'/live/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return url

class YukiAPI:
    """
    Official High-Speed Asynchronous & Synchronous Client for YukiYTAPI Music Engine.
    
    Usage:
        async with YukiAPI() as yuki:
            results = await yuki.search("Kesariya", limit=5)
            track = await yuki.details("Kesariya")
            file_path = await yuki.download("Kesariya", type="audio")
            stream_url = await yuki.get_stream("Kesariya", type="audio")
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        fallback_url: str = FALLBACK_BASE_URL,
        timeout: int = 60,
        session: Optional[aiohttp.ClientSession] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.fallback_url = fallback_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout, connect=10)
        self._session = session
        self._owns_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(enable_cleanup_closed=True)
            self._session = aiohttp.ClientSession(connector=connector, timeout=self.timeout)
            self._owns_session = True
        return self._session

    async def __aenter__(self):
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    def __del__(self):
        try:
            if self._owns_session and self._session and not self._session.closed:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self._session.close())
                except Exception:
                    pass
        except Exception:
            pass

    async def _request(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None) -> Any:
        session = await self._get_session()
        urls_to_try = [f"{self.base_url}{path}", f"{self.fallback_url}{path}"]
        last_error = None

        for url in urls_to_try:
            try:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 404:
                        raise TrackNotFoundError(f"Resource not found at {path}")
                    elif resp.status == 401:
                        raise TokenError("Access token expired or unauthorized")
                    else:
                        text = await resp.text()
                        last_error = YukiAPIError(f"HTTP {resp.status}: {text[:200]}")
            except (TrackNotFoundError, TokenError):
                raise
            except Exception as e:
                last_error = e
                continue

        raise YukiAPIError(f"Request failed on all YukiAPI endpoints: {last_error}")

    async def search(self, query: str, limit: int = 5) -> List[Track]:
        """
        Searches YouTube for tracks using the 3-Way Async Race engine.
        Returns a list of Track objects.
        """
        if not query or not str(query).strip():
            return []
        data = await self._request("/search", params={"q": str(query).strip(), "limit": limit})
        results = data.get("results", [])
        return [Track.from_dict(item) for item in results]

    async def details(self, query_or_url: str) -> Track:
        """
        Gets full track metadata (title, duration_min, duration_sec, thumbnail, vidid).
        Supports tuple unpacking:
            title, dur_min, dur_sec, thumb, vidid = await yuki.details("Kesariya")
        """
        if not query_or_url or not str(query_or_url).strip():
            raise TrackNotFoundError("Empty query provided")
        data = await self._request("/details", params={"url": str(query_or_url).strip()})
        return Track.from_dict(data)

    async def track(self, query_or_url: str) -> Track:
        """Alias for details()"""
        return await self.details(query_or_url)

    async def get_token(self, query_or_url: str, type: str = "audio") -> Tuple[str, str]:
        """
        Generates a high-speed download/streaming token for a track.
        Returns (token, video_id).
        """
        vid_id = extract_video_id(query_or_url)
        if not vid_id or not re.match(r'^[a-zA-Z0-9_-]{11}$', vid_id):
            # Resolve via search first
            t = await self.details(query_or_url)
            vid_id = t.id

        data = await self._request("/download", params={"url": vid_id, "type": type})
        token = data.get("download_token")
        if not token:
            raise TokenError("Could not retrieve download token from YukiAPI")
        return token, vid_id

    async def get_stream(self, query_or_url: str, type: str = "audio") -> str:
        """
        Returns a direct streaming URL with authentication token for PyTgCalls / GroupCall playback.
        """
        token, vid_id = await self.get_token(query_or_url, type=type)
        return f"{self.base_url}/stream/{vid_id}?type={type}&token={token}"

    async def stream_url(self, query_or_url: str, type: str = "audio") -> str:
        """Alias for get_stream()"""
        return await self.get_stream(query_or_url, type=type)

    async def playlist(self, url: str, limit: int = 50) -> List[Track]:
        """
        Extracts playlist tracks from a YouTube playlist URL.
        """
        data = await self._request("/playlist", params={"url": url, "limit": limit})
        tracks = data.get("tracks", [])
        return [Track.from_dict(item) for item in tracks]

    async def download(
        self,
        query_or_url: str,
        type: str = "audio",
        output_dir: str = "downloads",
        filename: Optional[str] = None
    ) -> str:
        """
        Downloads the track from YukiAPI high-speed stream to local disk atomically.
        Returns the absolute local file path.
        """
        token, vid_id = await self.get_token(query_or_url, type=type)
        ext = "mp4" if type == "video" else "mp3"
        os.makedirs(output_dir, exist_ok=True)
        out_name = filename or f"{vid_id}.{ext}"
        final_path = os.path.abspath(os.path.join(output_dir, out_name))

        if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
            return final_path

        session = await self._get_session()
        stream_url = f"{self.base_url}/stream/{vid_id}"
        tmp_path = final_path + f".{os.getpid()}.tmp"

        headers = {"X-Download-Token": token}
        params = {"type": type, "token": token}

        try:
            async with session.get(stream_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    raise DownloadError(f"Stream returned status {resp.status}")
                with open(tmp_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(32768):
                        f.write(chunk)
            os.replace(tmp_path, final_path)
            return final_path
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise DownloadError(f"Download failed: {str(e)}")

    # ── Synchronous Wrappers for non-async environments ──

    def search_sync(self, query: str, limit: int = 5) -> List[Track]:
        return asyncio.run(self.search(query, limit=limit))

    def details_sync(self, query_or_url: str) -> Track:
        return asyncio.run(self.details(query_or_url))

    def get_stream_sync(self, query_or_url: str, type: str = "audio") -> str:
        return asyncio.run(self.get_stream(query_or_url, type=type))

    def download_sync(self, query_or_url: str, type: str = "audio", output_dir: str = "downloads", filename: Optional[str] = None) -> str:
        return asyncio.run(self.download(query_or_url, type=type, output_dir=output_dir, filename=filename))

# Alias
YukiClient = YukiAPI
