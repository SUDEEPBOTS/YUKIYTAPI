"""
========================================================================
  YUKI YT API - ADVANCED YOUTUBE MEDIA STREAMING ENGINE
========================================================================
  Copyright (c) 2026 SUDEEPBOTS. All Rights Reserved.
  Distributed under the MIT License.
========================================================================
"""

import os
import sys
import time
import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from YUKIYTAPI.database.stats import init_db, add_download, get_stats

app = FastAPI(
    title="Yuki YouTube Streaming API",
    description="High-speed YouTube media streaming and audio extraction microservice by SUDEEPBOTS",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web console and clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "YUKIYTAPI", "saved")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

os.makedirs(CACHE_DIR, exist_ok=True)
init_db()

TOKENS = {}
START_TIME = time.time()


# ─────────────────────────────────────────
# BACKGROUND TASK: Move temp file to permanent cache
# ─────────────────────────────────────────
def _move_to_cache(tmp_path: str, cache_path: str) -> None:
    try:
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            os.replace(tmp_path, cache_path)
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


# ─────────────────────────────────────────
# ROOT ENDPOINT
# ─────────────────────────────────────────
@app.get("/", tags=["General"])
async def home(request: Request):
    uptime = round(time.time() - START_TIME, 2)
    return JSONResponse({
        "status": "online",
        "service": "YUKI YT API",
        "author": "SUDEEPBOTS",
        "brand": "SUDEEPBOTS",
        "uptime": f"{uptime}s",
        "endpoints": {
            "web_studio": "/web",
            "swagger_docs": "/docs",
            "health_check": "/health",
            "telemetry": "/stats",
            "token_generate": "/download?url={youtube_url}&type={audio/video}",
            "media_stream": "/stream/{video_id}?type={audio/video}&token={token}"
        },
        "message": "Welcome to Yuki YouTube Streaming API by SUDEEPBOTS"
    })


# ─────────────────────────────────────────
# HEALTH PROBE
# ─────────────────────────────────────────
@app.get("/health", tags=["Monitoring"])
async def health():
    return JSONResponse({
        "status": "healthy",
        "uptime": round(time.time() - START_TIME, 2),
        "engine": "FastAPI + yt-dlp",
        "cache_ready": os.path.exists(CACHE_DIR)
    })


# ─────────────────────────────────────────
# WEB STUDIO CONSOLE
# ─────────────────────────────────────────
@app.get("/web", response_class=HTMLResponse, tags=["Studio"])
async def web_studio():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Yuki YT API Web Studio</h1><p>UI file index.html is loading...</p>")


# ─────────────────────────────────────────
# METRICS & STATS
# ─────────────────────────────────────────
@app.get("/stats", tags=["Monitoring"])
async def api_stats(request: Request):
    total_dl, cache_mb = get_stats()
    return JSONResponse({
        "status": "success",
        "total_song_downloads": total_dl,
        "total_cache_size_mb": cache_mb,
        "active_tokens": len(TOKENS),
        "uptime_seconds": round(time.time() - START_TIME, 2)
    })


# ─────────────────────────────────────────
# STEP 1: TOKEN GENERATE
# ─────────────────────────────────────────
@app.get("/download", tags=["Streaming"])
async def generate_token(request: Request, url: str, type: str = "audio"):
    if not url:
        raise HTTPException(status_code=400, detail="Missing required 'url' parameter")

    # Extract Video ID or clean URL
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0].split("&")[0]
    elif "watch?v=" in url:
        video_id = url.split("v=")[-1].split("&")[0]
    else:
        video_id = url.split("?")[0].split("&")[0]

    yuki_token = f"YUKIMusic{uuid.uuid4().hex[:16]}SudeepBots"
    TOKENS[yuki_token] = {
        "video_id": video_id,
        "type": type.lower(),
        "expires": time.time() + 120,  # 2 minutes expiry
    }

    return JSONResponse({
        "status": "success",
        "video_id": video_id,
        "download_token": yuki_token,
        "stream_url": f"/stream/{video_id}?type={type}&token={yuki_token}",
        "usage": "Use token parameter or X-Download-Token header in /stream endpoint"
    })


# ─────────────────────────────────────────
# STEP 2: STREAM MEDIA (download → serve → cache)
# ─────────────────────────────────────────
@app.get("/stream/{video_id}", tags=["Streaming"])
async def stream_music(
    request: Request,
    video_id: str,
    background_tasks: BackgroundTasks,
    type: str = "audio",
    token: str = None,
    x_download_token: str = Header(None),
):
    # Auth validation
    actual_token = token or x_download_token
    if not actual_token or actual_token not in TOKENS:
        raise HTTPException(status_code=401, detail="Invalid or Missing Download Token. Obtain one from /download")

    token_data = TOKENS[actual_token]
    if time.time() > token_data["expires"] or token_data["video_id"] != video_id:
        TOKENS.pop(actual_token, None)
        raise HTTPException(status_code=401, detail="Token Expired or Invalid Video ID")

    # Consume single-use token
    del TOKENS[actual_token]

    # Check cache hit
    ext = "m4a" if type == "audio" else "mp4"
    cache_path = os.path.join(CACHE_DIR, f"{video_id}.{ext}")

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        add_download()
        return FileResponse(
            cache_path,
            media_type="audio/mp4" if type == "audio" else "video/mp4",
            filename=f"{video_id}.{ext}"
        )

    # Cache miss → yt-dlp download to temp
    tmp_path = os.path.join(CACHE_DIR, f"{video_id}.tmp.{ext}")
    outtmpl = os.path.join(CACHE_DIR, f"{video_id}.tmp.%(ext)s")

    cmd = ["yt-dlp"]

    # Safely attach cookies if file exists and has content
    if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        cmd.extend(["--cookies", COOKIES_FILE])

    # Add challenge bypass runtime & formats
    cmd.extend([
        "--js-runtimes", "node",
        "--remote-components", "ejs:github",
    ])

    if type == "audio":
        cmd.extend([
            "-f", "bestaudio[ext=m4a]/bestaudio[ext=opus]/bestaudio/best",
            "-o", outtmpl,
            "--quiet",
            video_id,
        ])
    else:
        cmd.extend([
            "-f", "(bestvideo[ext=mp4]+bestaudio[ext=m4a])/best[ext=mp4]/best",
            "-o", outtmpl,
            "--quiet",
            video_id,
        ])

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            err_msg = stderr.decode()[:300] if stderr else "Unknown yt-dlp error"
            raise HTTPException(
                status_code=500,
                detail=f"yt-dlp extraction failed: {err_msg}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming engine error: {str(e)}")

    # Locate generated output file
    actual_tmp = None
    if os.path.exists(CACHE_DIR):
        for fname in os.listdir(CACHE_DIR):
            if fname.startswith(f"{video_id}.tmp.") and not fname.endswith(".tmp"):
                actual_tmp = os.path.join(CACHE_DIR, fname)
                break

    if not actual_tmp or not os.path.exists(actual_tmp):
        raise HTTPException(status_code=500, detail="Extraction finished but audio payload could not be located")

    actual_ext = actual_tmp.rsplit(".", 1)[-1]
    final_cache = os.path.join(CACHE_DIR, f"{video_id}.{actual_ext}")

    add_download()

    # Move to cache asynchronously after streaming to user
    background_tasks.add_task(_move_to_cache, actual_tmp, final_cache)

    return FileResponse(
        actual_tmp,
        media_type="audio/mp4" if type == "audio" else "video/mp4",
        filename=f"{video_id}.{actual_ext}"
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("YUKIYTAPI.main:app", host=host, port=port, reload=False)
