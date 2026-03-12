#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${WECHAT_EXPORTER_DIR:-/root/.openclaw/workspace/projects/wechat-article-exporter}"
PORT="${PORT:-${WECHAT_EXPORTER_PORT:-3017}}"
HOST="${HOST:-${WECHAT_EXPORTER_HOST:-0.0.0.0}}"
PID_FILE="$REPO_DIR/.server.pid"
LOG_FILE="$REPO_DIR/server.log"

mkdir -p "$(dirname "$REPO_DIR")"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "[wechat-latest-collector] cloning wechat-article-exporter..."
  git clone --depth=1 https://github.com/wechat-article/wechat-article-exporter.git "$REPO_DIR"
fi

cd "$REPO_DIR"

if [ ! -d node_modules ]; then
  echo "[wechat-latest-collector] installing dependencies..."
  corepack enable >/dev/null 2>&1 || true
  corepack prepare yarn@1.22.22 --activate >/dev/null 2>&1 || true
  yarn install --frozen-lockfile
fi

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[wechat-latest-collector] exporter already running on pid=$OLD_PID"
    exit 0
  fi
fi

rm -f "$LOG_FILE"

echo "[wechat-latest-collector] starting exporter on http://127.0.0.1:${PORT}/"
setsid bash -lc "cd '$REPO_DIR' && exec script -qefc 'env PORT=$PORT HOST=$HOST yarn dev' '$LOG_FILE'" >/dev/null 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

for _ in $(seq 1 120); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "[wechat-latest-collector] exporter process exited early" >&2
    echo "log: $LOG_FILE" >&2
    tail -n 80 "$LOG_FILE" >&2 || true
    exit 1
  fi
  if python3 - <<PY
import socket
s=socket.socket()
s.settimeout(0.5)
try:
    s.connect(('127.0.0.1', int('${PORT}')))
    print('ok')
    raise SystemExit(0)
except Exception:
    raise SystemExit(1)
finally:
    s.close()
PY
  then
    echo "[wechat-latest-collector] exporter ready (pid=$PID)"
    exit 0
  fi
  sleep 1
done

echo "[wechat-latest-collector] exporter did not become ready in time" >&2
echo "log: $LOG_FILE" >&2
tail -n 80 "$LOG_FILE" >&2 || true
exit 1
