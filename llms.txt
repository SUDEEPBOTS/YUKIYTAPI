# YukiAPI Python SDK — Comprehensive Technical Documentation & AI Specification

> **Package Name:** `yukiapi` (Mirror: `yukiytapi`)  
> **Current Version:** `1.0.0`  
> **Base API URL:** `https://music.yukiapi.site` (Fallback: `https://yukiapi.site/music`)  
> **License:** MIT  
> **Maintainer:** SUDEEPBOTS / HellFireDevs  

---

## 1. Overview & Architecture

`yukiapi` is an asynchronous and synchronous Python SDK designed for Telegram Music Bots (Yukki, AnonX, Fallen, Rose, VCPlayer), Discord Bots, and media processing pipelines. It interacts with the **Yuki YouTube Streaming & Search Engine** to deliver sub-second search results, atomic audio/video disk downloads, and direct streaming URLs for voice chat engines (e.g., `pytgcalls`, `PyTgCalls`).

```
┌────────────────────────────────────────────────────────┐
│                   Client Application                   │
│   (Pyrogram / Telethon / discord.py / PyTgCalls Bot)   │
└───────────────────────────┬────────────────────────────┘
                            │
              pip install yukiapi (Client SDK)
                            │
       ┌────────────────────┴────────────────────┐
       ▼                                         ▼
[Modern SDK Interface]                [Drop-in Compat Layer]
yuki = YukiAPI()                      from yukiapi.compat import YouTubeAPI
await yuki.search(...)                YouTube = YouTubeAPI()
await yuki.download(...)              await YouTube.download(...)
       │                                         │
       └────────────────────┬────────────────────┘
                            │ HTTPS / JSON-RPC
                            ▼
┌────────────────────────────────────────────────────────┐
│            YukiAPI Server (Port 8000 + Nginx)          │
│                                                        │
│  ├── 3-Way Search Race:                                │
│  │   ├── Arm A: youtube-search-python (VideosSearch)   │
│  │   ├── Arm B: yt-music-api (Vercel Node)             │
│  │   └── Arm C: yt-dlp (ytsearch flat extraction)      │
│  │                                                     │
│  ├── In-Memory LRU RAM Cache (1ms repeat searches)     │
│  ├── Pre-Cached Vault Storage (Instant FileResponse)   │
│  └── Nginx Zero-Buffering Pipeline (proxy_buffering off│
└────────────────────────────────────────────────────────┘
```

---

## 2. Installation

```bash
pip install yukiapi
```

Or via mirror package:

```bash
pip install yukiytapi
```

---

## 3. Core Class Reference

### 3.1 `yukiapi.YukiAPI` (or `yukiapi.YukiClient`)

The primary client class. Supports both async context management and standalone instantiation.

#### Constructor

```python
YukiAPI(
    base_url: str = "https://music.yukiapi.site",
    fallback_url: str = "https://yukiapi.site/music",
    timeout: int = 60,
    session: Optional[aiohttp.ClientSession] = None
)
```

#### Async Methods

| Method | Signature | Return Type | Description |
| :--- | :--- | :--- | :--- |
| `search` | `async search(query: str, limit: int = 5)` | `List[Track]` | Executes 3-Way Async Race to search YouTube tracks. |
| `details` | `async details(query_or_url: str)` | `Track` | Resolves full track metadata. Supports tuple unpacking. |
| `track` | `async track(query_or_url: str)` | `Track` | Alias for `details()`. |
| `download` | `async download(query_or_url: str, type: str = "audio", output_dir: str = "downloads", filename: Optional[str] = None)` | `str` | Downloads track to local disk atomically (`.tmp` -> final). Returns absolute path. |
| `get_stream` | `async get_stream(query_or_url: str, type: str = "audio")` | `str` | Generates tokenized direct streaming URL for PyTgCalls / FFmpeg. |
| `stream_url` | `async stream_url(query_or_url: str, type: str = "audio")` | `str` | Alias for `get_stream()`. |
| `get_token` | `async get_token(query_or_url: str, type: str = "audio")` | `Tuple[str, str]` | Fetches `(download_token, video_id)` from backend. |
| `playlist` | `async playlist(url: str, limit: int = 50)` | `List[Track]` | Extracts tracks from YouTube playlist URL. |
| `close` | `async close()` | `None` | Closes underlying `aiohttp.ClientSession`. |

#### Sync Methods

| Method | Signature | Return Type | Description |
| :--- | :--- | :--- | :--- |
| `search_sync` | `search_sync(query: str, limit: int = 5)` | `List[Track]` | Synchronous wrapper for `search()`. |
| `details_sync` | `details_sync(query_or_url: str)` | `Track` | Synchronous wrapper for `details()`. |
| `download_sync` | `download_sync(query_or_url: str, type: str = "audio", output_dir: str = "downloads", filename: Optional[str] = None)` | `str` | Synchronous wrapper for `download()`. |
| `get_stream_sync` | `get_stream_sync(query_or_url: str, type: str = "audio")` | `str` | Synchronous wrapper for `get_stream()`. |

---

### 3.2 Data Model: `yukiapi.Track`

Structured track object returned by `search()`, `details()`, and `playlist()`.

```python
@dataclass
class Track:
    id: str            # 11-char YouTube Video ID (e.g. 'BddP6PYo2gs')
    vidid: str         # Alias for id
    title: str         # Full Track Title
    duration: str      # Duration string (e.g. '4:28' or '1:02:15')
    duration_min: str  # Duration formatted in MM:SS
    duration_sec: int  # Duration in total integer seconds (e.g. 268)
    link: str          # Canonical YouTube URL (https://www.youtube.com/watch?v=...)
    thumbnail: str     # High quality thumbnail URL
    channel: str       # Channel / Artist name
    views: str         # Formatted view count (e.g. '618M views')
```

#### Special Features of `Track`:

1. **Tuple Unpacking Support:**
   ```python
   title, dur_min, dur_sec, thumb, vidid = await yuki.details("Kesariya")
   ```
2. **Dictionary Key Access Support:**
   ```python
   track["title"]      # Works identically to track.title
   track["id"]         # Works identically to track.id
   track.to_dict()     # Returns standard Python dictionary
   ```

---

## 4. Drop-in Telegram Music Bot Compatibility (`yukiapi.compat`)

### `yukiapi.compat.YouTubeAPI` (or `YouTube`)

Designed to replace complex 1300+ line `platforms/Youtube.py` files in **YukkiMusic**, **AnonXMusic**, **FallenMusic**, and forks in 1 single line.

#### Migration Instruction:
In the bot repository, open `platforms/Youtube.py` and replace entire file content with:

```python
from yukiapi.compat import YouTubeAPI

YouTube = YouTubeAPI()
```

#### Implemented Methods in `YouTubeAPI`:

```python
async def exists(link: str, videoid: Union[bool, str] = None) -> bool
async def url(message_1: Message, message_2: Message = None) -> Optional[str]
async def details(link: str, videoid: Union[bool, str] = None) -> Tuple[str, str, int, str, str]
async def track(link: str, videoid: Union[bool, str] = None) -> Tuple[str, str, int, str, str]
async def title(link: str, videoid: Union[bool, str] = None) -> str
async def duration(link: str, videoid: Union[bool, str] = None) -> str
async def thumbnail(link: str, videoid: Union[bool, str] = None) -> str
async def search(query: str, limit: int = 5) -> List[Dict[str, Any]]
async def formats(link: str, videoid: Union[bool, str] = None) -> Tuple[List[Dict[str, str]], str]
async def playlist(link: str, limit: int = 50, user_id: Any = None) -> List[str]
async def download(link: str, mystic: Any = None, video: bool = False, videoid: bool = False, songaudio: bool = False, songvideo: bool = False, format_id: str = None, title: str = None) -> Tuple[str, bool]
async def video(link: str, videoid: Union[bool, str] = None) -> Tuple[int, Optional[str]]
async def is_live(link: str, videoid: Union[bool, str] = None) -> bool
```

---

## 5. End-to-End Implementation Examples

### Example 1: Full PyTgCalls Voice Chat Bot Integration

```python
import asyncio
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioQuality, MediaStream
from yukiapi import YukiAPI

app = Client("music_bot", api_id=12345, api_hash="abcdef", bot_token="TOKEN")
call = PyTgCalls(app)
yuki = YukiAPI()

async def play_song(chat_id: int, query: str):
    # 1. Resolve song details
    track = await yuki.details(query)
    print(f"Now loading: {track.title} [{track.duration}]")

    # 2. Download file to local disk (Atomic write, zero network stutter)
    file_path = await yuki.download(track.id, type="audio", output_dir="downloads")

    # 3. Stream to Telegram Voice Chat
    await call.play(
        chat_id,
        MediaStream(
            file_path,
            audio_parameters=AudioQuality.HIGH,
        )
    )
```

---

### Example 2: CLI Usage

```bash
# Search songs
yuki-dl --search "Arijit Singh" --limit 5

# Download high-quality audio
yuki-dl "Kesariya"

# Download 720p HD Video
yuki-dl "Kesariya" --video

# Output direct tokenized stream URL
yuki-dl --url "Kesariya"
```

---

## 6. HTTP REST API Endpoints Specification

| Endpoint | Method | Parameters | Sample Response |
| :--- | :--- | :--- | :--- |
| `/search` | `GET` | `q` (string, required), `limit` (int, default: 5) | `{"status":"success","query":"...","count":5,"results":[...]}` |
| `/details` | `GET` | `url` (string, video ID, link, or query) | `{"status":"success","id":"...","title":"...","duration_min":"...","thumbnail":"..."}` |
| `/download` | `GET` | `url` (string, required), `type` (`audio` or `video`) | `{"status":"success","video_id":"...","download_token":"..."}` |
| `/stream/{video_id}` | `GET` | `token` (query string or `X-Download-Token` header), `type` | Binary Media Stream (`audio/mp4` / `video/mp4`) with `Accept-Ranges: bytes` |
| `/playlist` | `GET` | `url` (string, required), `limit` (int, default: 50) | `{"status":"success","count":...,"tracks":[...]}` |

---

## 7. Error Handling

```python
from yukiapi import YukiAPI
from yukiapi.errors import TrackNotFoundError, TokenError, DownloadError, YukiAPIError

async with YukiAPI() as yuki:
    try:
        track = await yuki.details("non_existent_song_xyz_123")
    except TrackNotFoundError:
        print("Track could not be resolved.")
    except TokenError:
        print("Auth token expired or denied.")
    except DownloadError as e:
        print(f"Download pipeline failed: {e}")
    except YukiAPIError as e:
        print(f"General YukiAPI error: {e}")
```
