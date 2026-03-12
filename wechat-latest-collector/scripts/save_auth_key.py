#!/usr/bin/env python3
import argparse
from pathlib import Path
import os

DEFAULT_EXPORTER_DIR = Path(os.environ.get('WECHAT_EXPORTER_DIR', '/root/.openclaw/workspace/projects/wechat-article-exporter'))
DEFAULT_PATH = DEFAULT_EXPORTER_DIR / 'state' / 'auth_key.txt'

ap = argparse.ArgumentParser(description='Save exporter auth-key for later reuse')
ap.add_argument('auth_key', help='auth-key copied from exporter API page')
ap.add_argument('--path', type=Path, default=DEFAULT_PATH)
args = ap.parse_args()

args.path.parent.mkdir(parents=True, exist_ok=True)
args.path.write_text(args.auth_key.strip() + '\n', encoding='utf-8')
print(args.path)
