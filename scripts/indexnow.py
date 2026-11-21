#!/usr/bin/env python3
"""Tell Bing (and the other IndexNow search engines) which pages just changed.

IndexNow needs no account: the site publishes a key file at its root, and we
POST the changed addresses with that key. Only addresses listed in the
published sitemap.xml are sent, so forwarding stubs and private pages never go.

Usage:
  indexnow.py --host example.org --key KEY --root PUBLISHED_DIR --changed FILE ...
  indexnow.py --host example.org --key KEY --root PUBLISHED_DIR --compare OLD_DIR
  indexnow.py --host example.org --key KEY --root PUBLISHED_DIR --all
Add --wait to hold until the key file is live (first deploy), --dry-run to only print.
"""
import argparse
import filecmp
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = 'https://api.indexnow.org/IndexNow'
LIMIT = 10000


def sitemap_urls(root: Path):
    path = root / 'sitemap.xml'
    if not path.exists():
        return []
    return re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', path.read_text(encoding='utf-8'))


def page_path(rel: str) -> str:
    rel = rel.replace(os.sep, '/').lstrip('./')
    if rel == 'index.html':
        return '/'
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel


def changed_between(old: Path, new: Path):
    out = []
    for path in new.rglob('*.html'):
        rel = path.relative_to(new)
        before = old / rel
        if not before.exists() or not filecmp.cmp(before, path, shallow=False):
            out.append(str(rel))
    return out


def wait_for_key(host: str, key: str, minutes: int = 15):
    url = f'https://{host}/{key}.txt'
    deadline = time.time() + minutes * 60
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'Cache-Control': 'no-cache'}), timeout=20) as r:
                if r.read().decode('utf-8', 'replace').strip() == key:
                    print(f'key file is live at {url}')
                    return True
        except (urllib.error.URLError, OSError):
            pass
        if time.time() > deadline:
            print(f'::warning::key file {url} is not live yet; skipping this round')
            return False
        time.sleep(20)


def submit(host: str, key: str, urls):
    body = json.dumps({'host': host, 'key': key, 'keyLocation': f'https://{host}/{key}.txt',
                       'urlList': urls}).encode('utf-8')
    req = urllib.request.Request(ENDPOINT, data=body, method='POST',
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', required=True)
    ap.add_argument('--key', required=True)
    ap.add_argument('--root', type=Path, default=Path('.'))
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--changed', nargs='*')
    group.add_argument('--compare', type=Path)
    group.add_argument('--all', action='store_true')
    ap.add_argument('--wait', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    listed = sitemap_urls(args.root)
    base = f'https://{args.host}'
    if args.all:
        urls = listed
    else:
        rels = changed_between(args.compare, args.root) if args.compare else [
            c for c in (args.changed or []) if c.endswith('.html') and (args.root / c).exists()]
        wanted = {base + page_path(r) for r in rels}
        urls = [u for u in listed if u in wanted]
    urls = list(dict.fromkeys(urls))[:LIMIT]
    if not urls:
        print('no listed pages changed; nothing to send')
        return 0
    print(f'{len(urls)} page(s) to send:')
    for u in urls[:50]:
        print('  ' + u)
    if len(urls) > 50:
        print(f'  ... and {len(urls) - 50} more')
    if args.dry_run:
        return 0
    if args.wait and not wait_for_key(args.host, args.key):
        return 0
    status = submit(args.host, args.key, urls)
    meaning = {200: 'accepted', 202: 'received, key check pending', 400: 'bad request',
               403: 'key not valid for this site', 422: 'addresses do not match the site',
               429: 'too many requests'}.get(status, 'unexpected answer')
    print(f'IndexNow answered {status}: {meaning}')
    if status in (200, 202):
        return 0
    if status == 429:
        print('::warning::IndexNow asked us to slow down; these pages will go next time')
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
