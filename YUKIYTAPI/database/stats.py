# Copyright (c) 2026 SUDEEPBOTS. All Rights Reserved.
# Distributed under the MIT License.

import os
import json

DB_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(DB_DIR))
STATS_FILE = os.path.join(DB_DIR, "stats.json")
CACHE_DIR = os.path.join(BASE_DIR, "YUKIYTAPI", "saved")

def init_db():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f:
            json.dump({"total_downloads": 0}, f)

def add_download():
    try:
        with open(STATS_FILE, "r") as f:
            data = json.load(f)
        data["total_downloads"] = data.get("total_downloads", 0) + 1
        with open(STATS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def get_stats():
    total_size = 0
    if os.path.exists(CACHE_DIR):
        for dirpath, _, filenames in os.walk(CACHE_DIR):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp) and os.path.exists(fp):
                    total_size += os.path.getsize(fp)
    
    cache_size_mb = round(total_size / (1024 * 1024), 2)
    
    try:
        with open(STATS_FILE, "r") as f:
            data = json.load(f)
            total_dl = data.get("total_downloads", 0)
    except Exception:
        total_dl = 0
        
    return total_dl, cache_size_mb
