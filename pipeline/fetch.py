"""Download each active registry source into .pipeline-cache/raw/ (never committed).

Methods (registry "fetch.method"):
  socrata     Socrata open-data API: GET url with $limit/$offset paging -> JSON rows
  arcgis      ArcGIS FeatureServer/MapServer layer: paged /query, attributes + WGS84 point
  csv | xlsx | json | pdf | html   one file at fetch.url
  page-link   read fetch.url (a regulator landing page), take the first link whose address
              matches fetch.link_pattern, then download it as fetch.then (csv/xlsx/pdf/json)

A failed download is recorded in the fetch log with its reason and is never retried around:
no alternate hosts, mirrors, caches or archives. A 403, a login wall or a bot check is
"blocked" and the source stays queued until a person looks at it.

Run: python -m pipeline.fetch [--only ID_OR_STATE ...]
"""
import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from pipeline.common import FETCH_LOG, RAW, load_json, registry, save_json

USER_AGENT = 'TheReeferDirectoryPipeline/1.0 (+https://the-reefer.com/about.html; public regulator lists)'
BOT_MARKERS = ('captcha', 'cf-challenge', 'challenge-platform', 'are you a robot', 'verify you are human',
               'access denied', 'request rejected', 'incapsula', 'akamai bot')


class Blocked(Exception):
    pass


def get(url, params=None, timeout=90, tries=3):
    if params:
        url = url + ('&' if '?' in url else '?') + urllib.parse.urlencode(params, safe='$=*,:')
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': '*/*'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                ctype = resp.headers.get('Content-Type', '')
            if 'html' in ctype.lower() and any(m in body[:20000].decode('utf-8', 'ignore').lower() for m in BOT_MARKERS):
                raise Blocked(f'bot check or access page at {url}')
            return body, ctype
        except urllib.error.HTTPError as err:
            if err.code in (401, 403, 407, 429, 451):
                raise Blocked(f'HTTP {err.code} at {url}') from err
            last = err
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            last = err
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(f'{url}: {last}')


def fetch_socrata(spec):
    rows, offset, limit = [], 0, int(spec.get('page_size', 5000))
    params = dict(spec.get('params', {}))
    while True:
        body, _ = get(spec['url'], {**params, '$limit': limit, '$offset': offset})
        page = json.loads(body)
        rows.extend(page)
        if len(page) < limit:
            return json.dumps(rows).encode(), 'json'
        offset += limit


def fetch_arcgis(spec):
    rows, offset, limit = [], 0, int(spec.get('page_size', 1000))
    base = spec['url'].rstrip('/') + '/query'
    while True:
        params = {'where': spec.get('where', '1=1'), 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                  'f': 'json', 'resultOffset': offset, 'resultRecordCount': limit}
        body, _ = get(base, params)
        page = json.loads(body)
        if 'error' in page:
            raise RuntimeError(f'ArcGIS error: {page["error"]}')
        for feat in page.get('features', []):
            attrs = dict(feat.get('attributes') or {})
            geom = feat.get('geometry') or {}
            if 'x' in geom and 'y' in geom:
                attrs['_lon'], attrs['_lat'] = geom['x'], geom['y']
            rows.append(attrs)
        if not page.get('exceededTransferLimit') and len(page.get('features', [])) < limit:
            return json.dumps(rows).encode(), 'json'
        offset += limit


def resolve_link(spec):
    body, _ = get(spec['url'])
    html = body.decode('utf-8', 'ignore')
    pattern = re.compile(spec['link_pattern'], re.I)
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, re.I):
        href = href.replace('&amp;', '&')
        if pattern.search(href):
            return urllib.parse.urljoin(spec['url'], href)
    raise RuntimeError(f'no link matching {spec["link_pattern"]!r} on {spec["url"]}')


def fetch_one(source):
    spec = source['fetch']
    method = spec['method']
    resolved = spec.get('url')
    if method == 'socrata':
        body, ext = fetch_socrata(spec)
    elif method == 'arcgis':
        body, ext = fetch_arcgis(spec)
    elif method == 'page-link':
        resolved = resolve_link(spec)
        body, _ = get(resolved)
        ext = spec['then']
    elif method in ('csv', 'xlsx', 'json', 'pdf', 'html'):
        body, _ = get(spec['url'], spec.get('params'))
        ext = method
    else:
        raise ValueError(f'unknown fetch method {method}')
    if ext == 'xlsx' and not body.startswith(b'PK'):
        raise RuntimeError('expected an Excel file but got something else (the page may have changed)')
    if ext == 'pdf' and not body.startswith(b'%PDF'):
        raise RuntimeError('expected a PDF but got something else (the page may have changed)')
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f'{source["id"]}.{ext}'
    path.write_bytes(body)
    return {'file': path.name, 'resolved_url': resolved, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}


def selected(sources, only):
    if not only:
        return [s for s in sources if s.get('status') == 'active']
    wanted = {o.upper() for o in only}
    return [s for s in sources if s['id'].upper() in wanted or s['jurisdiction'].upper() in wanted]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', nargs='*', help='source ids or jurisdiction codes (default: every active source)')
    args = ap.parse_args(argv)
    log = load_json(FETCH_LOG, {})
    for source in selected(registry()['sources'], args.only):
        if source['fetch']['method'] == 'manual':
            continue
        stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
        try:
            info = fetch_one(source)
            log[source['id']] = {'ok': True, 'fetched_at': stamp, **info}
            print(f'ok       {source["id"]}: {info["bytes"]:,} bytes')
        except Blocked as err:
            log[source['id']] = {'ok': False, 'blocked': True, 'fetched_at': stamp, 'error': str(err)}
            print(f'BLOCKED  {source["id"]}: {err}')
        except Exception as err:  # noqa: BLE001 - every failure is logged, none is fatal
            log[source['id']] = {'ok': False, 'blocked': False, 'fetched_at': stamp, 'error': f'{type(err).__name__}: {err}'}
            print(f'FAILED   {source["id"]}: {err}')
    save_json(FETCH_LOG, log)


if __name__ == '__main__':
    main()
