#!/bin/bash
echo "🛑 Stopping yuki_api tmux session..."
tmux kill-session -t yuki_api 2>/dev/null

echo "🛑 Killing processes on port 8080..."
fuser -k 8080/tcp 2>/dev/null

echo "🗑️ Removing yvenv (Virtual Environment)..."
rm -rf yvenv

echo "🗑️ Removing compiled caches..."
rm -rf YUKIYTAPI/__pycache__ YUKIYTAPI/database/__pycache__

echo "✅ Uninstall/Cleanup complete! You can now safely delete the folder if you want."
