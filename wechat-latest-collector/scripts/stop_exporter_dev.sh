#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${WECHAT_EXPORTER_DIR:-/root/.openclaw/workspace/projects/wechat-article-exporter}"
PID_FILE="$REPO_DIR/.server.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "[wechat-latest-collector] no pid file"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
  echo "[wechat-latest-collector] stopping process-group pid=$PID"
  kill -TERM -- "-$PID" 2>/dev/null || kill "$PID" 2>/dev/null || true
  sleep 2
  kill -KILL -- "-$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
else
  echo "[wechat-latest-collector] pid not running"
fi

rm -f "$PID_FILE"
