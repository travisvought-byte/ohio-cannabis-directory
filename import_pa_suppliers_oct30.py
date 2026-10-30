"""Apply the October 30 public-source PA supplier expansion without network access."""
import json
from directory_data import ROOT
from import_pa_suppliers import build as import_suppliers

MANIFEST = ROOT / 'data/sources/pa-suppliers-2026-10-30.json'


def build(data, manifest):
    result = import_suppliers(data, manifest)
    result['as_of'] = max(result['as_of'], manifest['reviewed_on'])
    pa = next(s for s in result['states'] if s['code'] == 'PA')
    pa['reviewed_on'] = max(pa['reviewed_on'], manifest['reviewed_on'])
    return result


if __name__ == '__main__':
    path = ROOT / 'data/directory.json'
    result = build(json.loads(path.read_text()), json.loads(MANIFEST.read_text()))
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('Imported six PA supplier/commercial-service profiles reviewed October 30, 2026.')
