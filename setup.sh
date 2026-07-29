#!/usr/bin/env bash
set -uo pipefail

REPO_URL="https://github.com/SUDEEPBOTS/YUKIYTAPI.git"
REPO_DIR="YUKIYTAPI"
APP_NAME="yuki-yt-api"
APP_MODULE="YUKIYTAPI.main:app"
PORT=8080
TMUX_SESSION="yuki_api"
VENV_DIR="yvenv"
LOG_FILE="yuki_api.log"
TEST_VIDEO_ID="dQw4w9WgXcQ"
MIN_PY_MAJOR=3
MIN_PY_MINOR=9

log() { echo "[*] $1"; }
err() { echo -e "\033[1;31m[!] $1\033[0m" >&2; }

loading_bar() {
    local pid=$1
    local delay=0.5
    printf "[*] Processing: "
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        printf "."
        sleep $delay
    done
    printf " Done!\n"
}

sudo_if_needed() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    else
        sudo "$@"
    fi
}

check_python_version() {
    if ! command -v python3 &>/dev/null; then return 1; fi
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -lt "$MIN_PY_MAJOR" ] || { [ "$PY_MAJOR" -eq "$MIN_PY_MAJOR" ] && [ "$PY_MINOR" -lt "$MIN_PY_MINOR" ]; }; then
        return 1
    fi
    return 0
}

check_python() {
    if check_python_version; then
        return 0
    fi
    
    # Try to install a compatible python version
    if command -v apt-get &>/dev/null; then
        sudo_if_needed apt-get update -qq
        for ver in 12 11 10 9; do
            if sudo_if_needed apt-get install -y "python3.${ver}" "python3.${ver}-venv" -qq >/dev/null 2>&1; then
                # Ensure python3 command points to the newly installed version if possible
                if command -v "python3.${ver}" &>/dev/null; then
                    sudo_if_needed update-alternatives --install /usr/bin/python3 python3 "/usr/bin/python3.${ver}" 1 >/dev/null 2>&1 || true
                fi
                if check_python_version; then
                    return 0
                fi
            fi
        done
    fi

    # If all auto-installs fail
    err "Compatible Python (>= ${MIN_PY_MAJOR}.${MIN_PY_MINOR}) not found and auto-install failed."
    err "Please install Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ manually."
    exit 1
}

ensure_pkg() {
    # $1 = command to check, $2 = apt package name
    local cmd="$1" pkg="$2"
    if command -v "$cmd" &>/dev/null; then
        return
    fi
    if ! command -v apt-get &>/dev/null; then
        err "${cmd} missing and apt-get not available. Install ${pkg} manually."
        exit 1
    fi
    sudo_if_needed apt-get update -qq
    sudo_if_needed apt-get install -y "$pkg" -qq
    if ! command -v "$cmd" &>/dev/null; then
        err "Could not install ${pkg} automatically. Run manually: sudo apt install ${pkg}"
        exit 1
    fi
}

clone_or_update_repo() {
    if [ -d "$REPO_DIR/.git" ]; then
        (cd "$REPO_DIR" && git pull --ff-only > /dev/null 2>&1) || err "git pull failed, continuing with existing copy"
    else
        if [ -d "$REPO_DIR" ]; then
            err "${REPO_DIR} exists but is not a git repo, removing and re-cloning..."
            rm -rf "$REPO_DIR"
        fi
        git clone "$REPO_URL" "$REPO_DIR" > /dev/null 2>&1
    fi
    cd "$REPO_DIR" || { err "Could not cd into ${REPO_DIR}"; exit 1; }
}

ensure_venv_support() {
    if python3 -c "import ensurepip" &>/dev/null; then
        return
    fi
    if ! command -v apt-get &>/dev/null; then
        err "ensurepip missing and apt-get not available. Install venv support manually for Python ${PY_VER}."
        exit 1
    fi
    sudo_if_needed apt-get update -qq
    if ! sudo_if_needed apt-get install -y "python${PY_VER}-venv" -qq; then
        sudo_if_needed apt-get install -y python3-venv -qq
    fi
    if ! python3 -c "import ensurepip" &>/dev/null; then
        err "Could not install venv support automatically. Run manually: sudo apt install python${PY_VER}-venv"
        exit 1
    fi
}

setup_venv() {
    if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
        rm -rf "$VENV_DIR"
    fi
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        if [ ! -f "$VENV_DIR/bin/activate" ]; then
            err "venv creation failed. Cleaning up broken ${VENV_DIR} directory..."
            rm -rf "$VENV_DIR"
            exit 1
        fi
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
}

check_deno() {
    if ! command -v deno &>/dev/null; then
        curl -fsSL https://deno.land/install.sh | sh -s -- -y
        export PATH="$HOME/.deno/bin:$PATH"
        if ! command -v deno &>/dev/null; then
            err "deno install failed. Add \$HOME/.deno/bin to PATH manually and re-run."
            exit 1
        fi
    fi
}

install_requirements() {
    if [ -f "requirements.txt" ]; then
        log "Installing Python requirements..."
        ( pip install --upgrade pip > /dev/null 2>&1 && pip install setuptools > /dev/null 2>&1 && pip install -r requirements.txt > /dev/null 2>&1 ) &
        loading_bar $!
    else
        err "requirements.txt not found in ${REPO_DIR}, skipping"
    fi

    log "Compiling High-Security Cython Native Binaries..."
    ( python3 setup.py build_ext --inplace > /dev/null 2>&1 ) &
    loading_bar $!
    
    log "Wiping Raw C Source Files for extra security..."
    rm -f YUKIYTAPI/main.c YUKIYTAPI/database/stats.c
}

port_in_use() {
    local port=$1
    if command -v ss &>/dev/null; then
        ss -tuln | grep -q ":${port} "
    elif command -v lsof &>/dev/null; then
        lsof -i ":${port}" &>/dev/null
    else
        (echo > "/dev/tcp/127.0.0.1/${port}") &>/dev/null
    fi
}

get_port_pid() {
    local port=$1
    if command -v lsof &>/dev/null; then
        lsof -ti ":${port}"
    else
        fuser "${port}/tcp" 2>/dev/null
    fi
}

check_port_and_zombies() {
    if port_in_use "$PORT"; then
        PID=$(get_port_pid "$PORT")
        CMD=$(ps -p "$PID" -o cmd= 2>/dev/null || true)
        if echo "$CMD" | grep -q "$APP_MODULE"; then
            log "Port ${PORT} busy with an old/zombie instance of ${APP_NAME} (PID ${PID}). Killing it..."
            kill -9 "$PID" 2>/dev/null
            sleep 1
        else
            err "Port ${PORT} is busy with an unrelated process (PID ${PID}): ${CMD}"
            err "Free the port manually or change PORT in this script."
            exit 1
        fi
    fi

    PIDS=$(pgrep -f "$APP_MODULE" || true)
    if [ -n "$PIDS" ]; then
        log "Found duplicate process(es), killing: $PIDS"
        kill -9 $PIDS 2>/dev/null
        sleep 1
    fi
    tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true
}

start_tmux() {
    log "Starting ${APP_NAME} in tmux session '${TMUX_SESSION}'..."
    tmux new-session -d -s "$TMUX_SESSION" \
        "cd $(pwd) && source ${VENV_DIR}/bin/activate && export PYTHONPATH=$(pwd) && uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT} 2>&1 | tee ${LOG_FILE}"
    sleep 5
    if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        err "tmux session died immediately. Check ${LOG_FILE} in ${REPO_DIR}."
        exit 1
    fi
}

verify_running() {
    for i in $(seq 1 10); do
        CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/")
        if [ "$CODE" == "200" ]; then
            return 0
        fi
        sleep 2
    done
    err "Server did not respond after 20s. Recent log:"
    tmux capture-pane -t "$TMUX_SESSION" -p | tail -30
    exit 1
}

test_download() {
    RESP=$(curl -s "http://127.0.0.1:${PORT}/download?url=${TEST_VIDEO_ID}&type=audio")
    TOKEN=$(echo "$RESP" | grep -o '"download_token":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$TOKEN" ]; then
        err "Failed to get download token. Response: $RESP"
        exit 1
    fi
    HTTP_CODE=$(curl -s -o /tmp/test_song.m4a -w "%{http_code}" "http://127.0.0.1:${PORT}/stream/${TEST_VIDEO_ID}?token=${TOKEN}&type=audio")
    if [ "$HTTP_CODE" == "200" ] && [ -s /tmp/test_song.m4a ]; then
        SIZE=$(du -h /tmp/test_song.m4a | cut -f1)
        log "SUCCESS - test song downloaded (${SIZE}). API is fully working."
        rm -f /tmp/test_song.m4a
    else
        err "Stream test failed (HTTP ${HTTP_CODE})"
        exit 1
    fi
}

main() {
    log "Checking system dependencies..."
    check_python
    ensure_pkg git git
    ensure_pkg tmux tmux
    ensure_pkg ffmpeg ffmpeg
    ensure_pkg unzip unzip
    clone_or_update_repo
    ensure_venv_support
    setup_venv
    check_deno
    install_requirements
    check_port_and_zombies
    start_tmux
    verify_running
    test_download
    log "All done. Attach anytime with: tmux attach -t ${TMUX_SESSION}"
    
    local public_ip
    public_ip=$(curl -s --max-time 3 ifconfig.me || echo "YOUR_SERVER_IP")
    echo ""
    log "=================================================="
    log "🚀 YUKI API IS LIVE!"
    log "🌐 Public URL: http://${public_ip}:${PORT}"
    log "💻 Local URL:  http://127.0.0.1:${PORT}"
    log "📂 Directory:  $(pwd)"
    log "=================================================="
    echo ""
}

main
