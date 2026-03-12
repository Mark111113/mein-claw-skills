#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://127.0.0.1:${WECHAT_EXPORTER_PORT:-3017}/}"
REPO_DIR="${WECHAT_EXPORTER_DIR:-/root/.openclaw/workspace/projects/wechat-article-exporter}"
LOG_FILE="$REPO_DIR/open_exporter_vnc.log"
mkdir -p "$REPO_DIR"

if command -v chromium >/dev/null 2>&1; then
  DISPLAY=:0 nohup chromium --new-window --no-sandbox --disable-dev-shm-usage \
    --no-first-run --no-default-browser-check "$URL" >"$LOG_FILE" 2>&1 &
  echo "[wechat-latest-collector] opened Chromium on :0 -> $URL"
  exit 0
fi

if command -v firefox >/dev/null 2>&1; then
  DISPLAY=:0 nohup firefox "$URL" >"$LOG_FILE" 2>&1 &
  echo "[wechat-latest-collector] opened Firefox on :0 -> $URL"
  exit 0
fi

echo "[wechat-latest-collector] no desktop browser found" >&2
exit 1
