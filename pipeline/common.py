"""Shared paths, the normalized row shape and text helpers for the source pipeline."""
import json
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / 'pipeline/registry.json'
CACHE = ROOT / '.pipeline-cache'          # raw downloads; never committed
RAW = CACHE / 'raw'
FETCH_LOG = ROOT / 'data/sources/pipeline/_fetch-log.json'  # committed: status only, no row data
SNAPSHOTS = ROOT / 'data/sources/pipeline'  # normalized, business-only snapshots; committed
OUTPUT = ROOT / 'data/state-retail-locations.json'
COVERAGE_JSON = ROOT / 'data/pipeline-coverage.json'
COVERAGE_MD = ROOT / 'architecture/PIPELINE_COVERAGE.md'

# The only fields a normalized row may carry. Anything a source publishes beyond these
# (owner and contact names, equity categories, internal notes) is dropped on purpose.
FIELDS = ('name', 'licensee', 'address', 'street', 'city', 'state', 'zip', 'county', 'phone', 'website',
          'license_number', 'license_type', 'status', 'lat', 'lon', 'opened')

EVIDENCE_LEVELS = {
    'regulator-list': "Listed by the state or national regulator's own published list on the date retrieved.",
    'regulator-open-data': "Listed in the regulator's own open-data export on the date retrieved.",
    'official-portal': "Listed on the government's official open-data portal, attributed to the regulator.",
    'business-own-page': "Stated on the business's own website; not a license verification.",
    'trade-show': 'Exhibited or sponsored at a cannabis trade show (owner rule: counts as cannabis-adjacent).',
    'local-semi-legitimate': 'A local source with limited standing (for example a souvenir-seed booth or appointment-only wholesaler), listed with this label.',
}


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


def registry():
    return load_json(REGISTRY)


def today():
    return date.today().isoformat()


def plus_days(iso, days):
    return (date.fromisoformat(iso) + timedelta(days=days)).isoformat()


def clean(value):
    """Collapse whitespace; treat blanks, NaN and placeholder dashes as missing."""
    if value is None:
        return None
    if isinstance(value, dict):  # Socrata url objects: {"url": ...}
        value = value.get('url') or value.get('description')
        if value is None:
            return None
    if isinstance(value, float):
        if value != value:  # NaN
            return None
        if value.is_integer():
            value = int(value)
    text = ' '.join(str(value).split())
    if text.lower() in ('', 'nan', 'none', 'null', 'n/a', 'na', '-', '--'):
        return None
    return text


def title_if_shouting(text):
    """Regulators often publish in capitals. Keep mixed case as published; soften all-caps."""
    if not text or not text.isupper() or len(text) < 4:
        return text
    small = {'and', 'of', 'the', 'at', 'in', 'on', 'for', 'llc', 'inc', 'ltd', 'co', 'dba'}
    words = []
    for i, w in enumerate(text.lower().split(' ')):
        if w in ('llc', 'inc', 'ltd', 'lp', 'llp', 'pllc'):
            words.append(w.upper() if w != 'inc' else 'Inc')
        elif re.fullmatch(r'(n|s|e|w|ne|nw|se|sw)', w):
            words.append(w.upper())
        elif re.fullmatch(r'\d+(st|nd|rd|th)', w):
            words.append(w)
        elif i and w in small:
            words.append(w)
        else:
            words.append(w[:1].upper() + w[1:])
    return ' '.join(words)


def norm_key(text):
    """A loose comparison key: lower case, letters and digits only, common words folded."""
    if not text:
        return ''
    t = text.lower()
    t = re.sub(r'\b(street)\b', 'st', t)
    t = re.sub(r'\b(avenue)\b', 'ave', t)
    t = re.sub(r'\b(road)\b', 'rd', t)
    t = re.sub(r'\b(boulevard)\b', 'blvd', t)
    t = re.sub(r'\b(drive)\b', 'dr', t)
    t = re.sub(r'\b(highway)\b', 'hwy', t)
    t = re.sub(r'\b(suite|ste|unit|#)\b.*$', '', t)
    t = re.sub(r'\b(llc|inc|ltd|co|corp|company|dba|the)\b', '', t)
    return re.sub(r'[^a-z0-9]', '', t)


def phone(text):
    text = clean(text)
    if not text:
        return None
    digits = re.sub(r'\D', '', text)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
    return text


def website(text):
    text = clean(text)
    if not text or ' ' in text or '.' not in text or '@' in text:
        return None
    if not re.match(r'https?://', text, re.I):
        text = 'https://' + text.lstrip('/')
    return text


def zip5(text):
    text = clean(text)
    if not text:
        return None
    m = re.match(r'(\d{5})', text.zfill(5) if text.isdigit() and len(text) < 5 else text)
    return m.group(1) if m else text
