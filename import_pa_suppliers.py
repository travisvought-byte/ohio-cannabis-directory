"""Import the reviewed PA supplier manifest; retain shared organization records unchanged."""
import copy
import hashlib
import json
from directory_data import ROOT

MANIFEST = ROOT / 'data/sources/pa-suppliers-2026-10-29.json'
PREFIX = 'ev-pa-supplier-'


def build(data, manifest):
    result = copy.deepcopy(data)
    profiles = manifest['profiles']
    if len({p['staging_id'] for p in profiles}) != len(profiles):
        raise ValueError('Duplicate staging ID')
    decisions = {d['staging_id']: d for d in manifest['decisions']}
    orgs = {o['id']: o for o in result['organizations']}
    service_ids = {'svc-pa-supplier-' + p['staging_id'].removeprefix('pa-') for p in profiles}
    subjects = service_ids | {p['organization_id'] for p in profiles}
    result['services'] = [s for s in result['services'] if s['id'] not in service_ids]
    result['evidence'] = [e for e in result['evidence']
                          if not (e['id'].startswith(PREFIX) and e['subject_id'] in subjects)]
    for profile in profiles:
        decision = decisions[profile['staging_id']]
        if decision['decision'] != 'propose-publication' or decision['record_type'] != 'current-provider':
            raise ValueError('Only reviewed current provider profiles may enter this import')
        for source in profile['sources']:
            if (source['status'] != 'source-reviewed' or not source['url'].startswith('https://')
                    or not source['reviewed_on'] or source['reviewed_on'] > manifest['reviewed_on']):
                raise ValueError('Publication requires a successfully reviewed HTTPS source')
        oid = profile['organization_id']
        if oid not in orgs:
            org = dict(id=oid, name=profile['name'], kind='service-provider', legacy_ids=[],
                       contacts=[], website=profile['website'], scope='public')
            result['organizations'].append(org)
            orgs[oid] = org
        elif orgs[oid].get('scope') != 'public':
            raise ValueError('Existing nonpublic identity needs a separate publication decision')
        sid = 'svc-pa-supplier-' + profile['staging_id'].removeprefix('pa-')
        evidence_ids = []

        def claim(subject, name, value, source):
            digest = hashlib.sha256('|'.join((subject, name, value, source['url'])).encode()).hexdigest()[:16]
            eid = PREFIX + digest
            result['evidence'].append(dict(id=eid, subject_id=subject, claim=name, value=value,
                source_url=source['url'], source_kind=source['source_kind'], status='source-reviewed',
                reviewed_on=source['reviewed_on'], recorded_on=manifest['reviewed_on'],
                recheck_on=manifest['recheck_on'], limitations=source['limitations']))
            if subject == sid:
                evidence_ids.append(eid)

        first = profile['sources'][0]
        # Classification is an editorial summary of the cited offering, not a credential.
        claim(oid, 'company-category', profile['category'], first)
        claim(oid, 'company-role', profile['role'], first)
        claim(sid, 'service-description', profile['description'], first)
        pa_source = next(s for s in profile['sources'] if s['url'] == profile['pa_source'])
        claim(oid, 'company-pa-connection', profile['pa_connection'], pa_source)
        claim(sid, 'company-pa-connection', profile['pa_connection'], pa_source)
        inquiry = next(s for s in profile['sources'] if s['url'] == profile['inquiry_url'])
        note = 'Use the provider inquiry page to confirm project fit, Pennsylvania availability and current terms.'
        claim(sid, 'provider-contact', note, inquiry)
        result['services'].append(dict(id=sid, organization_id=oid,
            name=profile['name'] + ' — ' + profile['category'], description=profile['description'],
            location_ids=[], pathway_ids=['business'], coverage=[], audiences=['business'],
            eligibility='Business inquiry. Confirm current availability, qualifications and product or project suitability directly.',
            next_step={'label': 'Business inquiry', 'url': profile['inquiry_url']}, availability='unknown',
            attributes={'provider_details': dict(serves='Businesses seeking ' + profile['category'].lower() + '.',
                coverage_note=profile['pa_connection'], contact_note=note, source_url=inquiry['url'],
                reviewed_on=inquiry['reviewed_on'])}, fulfillment=[], evidence_ids=evidence_ids,
            origin='organization-profile', listed_in=['PA']))
    return result


if __name__ == '__main__':
    manifest = json.loads(MANIFEST.read_text())
    path = ROOT / 'data/directory.json'
    result = build(json.loads(path.read_text()), manifest)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(f"Imported {len(manifest['profiles'])} reviewed PA supplier/service routes.")
