import os
import sys
import pytest

# Ensure root package is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from YUKIYTAPI.main import app

client = TestClient(app)

def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "YUKI YT API"
    assert data["brand"] == "SUDEEPBOTS"
    assert "endpoints" in data

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "total_song_downloads" in data
    assert "active_tokens" in data

def test_download_token_generate():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    response = client.get(f"/download?url={url}&type=audio")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["video_id"] == "dQw4w9WgXcQ"
    assert "download_token" in data
    assert "SudeepBots" in data["download_token"]

def test_stream_unauthorized():
    response = client.get("/stream/dQw4w9WgXcQ?type=audio")
    assert response.status_code == 401
