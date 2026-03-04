#!/bin/bash
# 视频批量下载启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "$1" ]; then
  echo "用法: $0 <采集目录>"
  echo "示例: $0 /mnt/fn/Download3/clawdbotfile/xiaohongshu/20260224_0913_红嘴鸥"
  exit 1
fi

python3 video_batch_downloader.py "$1"
