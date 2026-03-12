#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_REPO_DIR = SKILL_DIR.parent
DEFAULT_EXPORTER_DIR = Path(os.environ.get('WECHAT_EXPORTER_DIR', '/root/.openclaw/workspace/projects/wechat-article-exporter'))
DEFAULT_BASE_URL = os.environ.get('WECHAT_EXPORTER_BASE_URL', f"http://127.0.0.1:{os.environ.get('WECHAT_EXPORTER_PORT', '3017')}")
DEFAULT_TEMP_DIR = Path(os.environ.get('WECHAT_LATEST_TEMP_DIR', '/root/.openclaw/workspace/temp'))
DEFAULT_AUTH_KEY_FILE = DEFAULT_EXPORTER_DIR / 'state' / 'auth_key.txt'
DEFAULT_COLLECTOR = Path(os.environ.get('WECHAT_COLLECTOR_PATH', str(SKILLS_REPO_DIR / 'wechat-collector' / 'scripts' / 'wechat_collector.py')))
LEGACY_AUTH_KEY_FILES = [
    Path('/root/.openclaw/workspace/projects/wechat-latest-collector/state/auth_key.txt'),
    Path('/root/.openclaw/workspace/temp/wechat_exporter_auth_key.txt'),
]


def req_json(session, url, **kwargs):
    r = session.get(url, timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()


def validate_auth_key(session, base_url):
    data = req_json(session, f'{base_url}/api/public/v1/authkey')
    return isinstance(data, dict) and data.get('code') == 0


def resolve_biz_from_url(session, base_url, article_url):
    data = req_json(session, f'{base_url}/api/public/v1/accountbyurl', params={'url': article_url})
    candidates = [data]
    for key in ('data', 'account', 'accounts', 'list'):
        v = data.get(key) if isinstance(data, dict) else None
        if isinstance(v, list):
            candidates.extend(v)
        elif isinstance(v, dict):
            candidates.append(v)
    for item in candidates:
        if not isinstance(item, dict):
            continue
        for key in ('fakeid', 'biz', '__biz'):
            val = item.get(key)
            if val:
                return val, data
    raise RuntimeError(f'Could not resolve biz/fakeid from article URL response: {json.dumps(data, ensure_ascii=False)[:800]}')


def fetch_latest(session, base_url, biz, limit):
    data = req_json(session, f'{base_url}/api/public/v1/article', params={'fakeid': biz, 'begin': 0, 'size': limit})
    base_resp = data.get('base_resp', {}) if isinstance(data, dict) else {}
    if base_resp.get('ret') not in (0, '0', None):
        raise RuntimeError(f'Article API failed: {json.dumps(base_resp, ensure_ascii=False)}')
    return data


def load_auth_key(auth_key, auth_key_file, state_dir):
    if auth_key:
        return auth_key.strip()
    if auth_key_file.exists():
        key = auth_key_file.read_text(encoding='utf-8').strip()
        if key:
            return key
    if auth_key_file == DEFAULT_AUTH_KEY_FILE:
        for legacy in LEGACY_AUTH_KEY_FILES:
            if legacy.exists():
                key = legacy.read_text(encoding='utf-8').strip()
                if key:
                    state_dir.mkdir(parents=True, exist_ok=True)
                    auth_key_file.write_text(key + '\n', encoding='utf-8')
                    return key
    raise SystemExit(
        'No auth key available. Please open the exporter in VNC, log in, go to API page, click 查询 API 密钥, '
        f'and save it to {auth_key_file} or pass --auth-key explicitly.'
    )


def main():
    ap = argparse.ArgumentParser(description='Fetch latest N WeChat official account articles and optionally collect full text.')
    ap.add_argument('--auth-key', help='auth-key from local wechat-article-exporter API page')
    ap.add_argument('--auth-key-file', type=Path, default=DEFAULT_AUTH_KEY_FILE, help='path to cached auth-key file')
    ap.add_argument('--biz', help='WeChat account __biz/fakeid')
    ap.add_argument('--article-url', help='A known article URL from the target account; used to resolve biz/fakeid')
    ap.add_argument('--limit', type=int, default=5)
    ap.add_argument('--base-url', default=DEFAULT_BASE_URL)
    ap.add_argument('--collect', action='store_true', help='also run wechat_collector.py on the discovered URLs')
    ap.add_argument('--collector-path', type=Path, default=DEFAULT_COLLECTOR, help='path to wechat_collector.py')
    ap.add_argument('--temp-dir', type=Path, default=DEFAULT_TEMP_DIR, help='directory for metadata/url temp files')
    ap.add_argument('--output-prefix', default='wechat_latest')
    args = ap.parse_args()

    if not args.biz and not args.article_url:
        raise SystemExit('Need either --biz or --article-url')

    args.temp_dir.mkdir(parents=True, exist_ok=True)
    args.auth_key_file.parent.mkdir(parents=True, exist_ok=True)

    auth_key = load_auth_key(args.auth_key, args.auth_key_file, args.auth_key_file.parent)

    s = requests.Session()
    s.headers.update({'Cookie': f'auth-key={auth_key}', 'X-Auth-Key': auth_key})

    if not validate_auth_key(s, args.base_url):
        raise SystemExit(
            'Auth key is invalid or expired. Please reopen the exporter in VNC, log in again if needed, '
            'go to API page, click 查询 API 密钥, then update the cached auth-key file and rerun.'
        )

    biz = args.biz
    resolution = None
    if not biz and args.article_url:
        biz, resolution = resolve_biz_from_url(s, args.base_url, args.article_url)

    data = fetch_latest(s, args.base_url, biz, args.limit)
    articles = data.get('articles', [])

    ts = time.strftime('%Y%m%d_%H%M%S')
    safe_biz = ''.join(ch for ch in biz if ch.isalnum() or ch in ('-', '_', '='))
    prefix = args.temp_dir / f'{args.output_prefix}_{safe_biz}_{ts}'
    json_path = prefix.with_suffix('.json')
    urls_path = prefix.with_suffix('.urls.txt')

    output = {
        'biz': biz,
        'resolved_from_article_url': args.article_url,
        'resolution_response': resolution,
        'base_resp': data.get('base_resp'),
        'articles': [
            {
                'title': a.get('title'),
                'link': a.get('link'),
                'author_name': a.get('author_name'),
                'update_time': a.get('update_time'),
                'create_time': a.get('create_time'),
                'aid': a.get('aid'),
            }
            for a in articles
        ],
    }

    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    urls = [a.get('link') for a in articles if a.get('link')]
    urls_path.write_text('\n'.join(urls) + ('\n' if urls else ''), encoding='utf-8')

    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(f'\nSaved article metadata to: {json_path}')
    print(f'Saved URL list to: {urls_path}')
    print(f'Using auth-key file: {args.auth_key_file}')
    print(f'Using collector path: {args.collector_path}')

    if args.collect:
        if not args.collector_path.exists():
            raise RuntimeError(f'Collector not found: {args.collector_path}')
        cmd = ['python3', str(args.collector_path), *urls]
        print('\nRunning collector:', ' '.join(cmd))
        subprocess.run(cmd, check=False)


if __name__ == '__main__':
    main()
