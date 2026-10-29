"""Build the PA organization directory from canonical business services and evidence.

One card per permanent organization, even when it has several service routes.
No legacy Ohio contact or service-area field is treated as a newly reviewed PA fact.
"""
import csv
import html
import io
from collections import defaultdict
from directory_data import ROOT, load_directory, script_json
from directory_brand import brand_page
from public_data import externalize

OUT = ROOT / 'pennsylvania-directory.html'


def category(service):
    text = (service['name'] + ' ' + service.get('description', '')).lower()
    rules = [
        ('Testing laboratories', ('approved testing laboratory',)),
        ('Education & research', ('certificate', 'graduate programs', 'research', 'hemp home')),
        ('Industry organizations', ('coalition', 'council', 'guild', 'steering committee')),
        ('Legal & licensing', ('law', 'legal', 'intellectual property', 'employment counsel')),
        ('Accounting & finance', ('accounting', 'cpa', 'tax and advisory')),
        ('Banking & payments', ('bank', 'credit union', 'canpay', 'payment')),
        ('Insurance', ('insurance', 'amwins')),
        ('Security', ('security', 'dem360')),
        ('Packaging & labels', ('packaging', 'labels', 'labeling')),
        ('Extraction & processing equipment', ('extraction equipment',)),
        ('Software & technology', ('dutchie', 'software', 'integration')),
        ('Hemp materials', ('hempatrics', 'fiber', 'hurd')),
    ]
    if service['id'].startswith('svc-pa-operator-'):
        return 'Operators & brands'
    for label, words in rules:
        if any(word in text for word in words):
            return label
    return 'Consulting & other services'


def build_model(data):
    organizations = {o['id']: o for o in data['organizations']}
    evidence = {e['id']: e for e in data['evidence']}
    grouped = defaultdict(list)
    facts = defaultdict(list)
    for e in data['evidence']:
        if e['claim'].startswith(('company-', 'public-business-')) and e['status'] == 'source-reviewed':
            facts[e['subject_id']].append(e)
    for service in data['services']:
        org = organizations[service['organization_id']]
        if ('PA' in service.get('listed_in', []) and 'business' in service['pathway_ids']
                and org.get('scope') == 'public' and org['kind'] != 'government'):
            grouped[org['id']].append(service)
    cards = []
    for oid, services in grouped.items():
        org = organizations[oid]
        org_facts = facts[oid]
        cats = sorted({e['value'] for e in org_facts if e['claim'] == 'company-category'} or {category(s) for s in services})
        roles = sorted({e['value'] for e in org_facts if e['claim'] == 'company-role'})
        if not roles:
            roles = ['Operator' if 'Operators & brands' in cats else
                     'Supplier' if any(c in cats for c in ('Packaging & labels', 'Extraction & processing equipment', 'Hemp materials', 'Cultivation supplies', 'Gases & consumables')) else
                     'Industry organization' if 'Industry organizations' in cats else
                     'Education & research' if 'Education & research' in cats else 'Service provider']
        routes = []
        sources = {}
        for s in services:
            detail = s['attributes'].get('provider_details', {})
            routes.append(dict(id=s['id'], name=s['name'], description=s.get('description', ''),
                               pa_connection=detail.get('coverage_note', ''), url=s['next_step']['url']))
            for eid in s['evidence_ids']:
                e = evidence[eid]
                key = (e['source_url'], e.get('reviewed_on', ''), e['limitations'])
                sources[key] = {k:e.get(k, '') for k in ('source_url', 'source_kind', 'reviewed_on', 'status', 'limitations')}
        for e in org_facts:
            key = (e['source_url'], e['reviewed_on'], e['limitations'])
            sources[key] = {k:e.get(k, '') for k in ('source_url', 'source_kind', 'reviewed_on', 'status', 'limitations')}
        public_facts = [{k:e[k] for k in ('claim', 'value', 'source_url', 'reviewed_on', 'limitations')}
                        for e in org_facts if e['claim'] not in ('company-role', 'company-category')]
        cards.append(dict(id=oid, name=org['name'].removeprefix('! '), categories=cats, roles=roles,
                          routes=routes, facts=public_facts, sources=list(sources.values())))
    return sorted(cards, key=lambda c:(c['name'].casefold(), c['id']))


def build_page(data, persist=False):
    cards = build_model(data)
    fallback = '<h2>Company index</h2><ul>' + ''.join(
        '<li><a href="'+html.escape(c['routes'][0]['url'], quote=True)+'">'+html.escape(c['name'])+'</a> · '+html.escape('; '.join(c['categories']))+'</li>' for c in cards) + '</ul>'
    page = (ROOT / 'templates/pa-companies.html').read_text().replace('__COUNT__', str(len(cards))).replace('__FALLBACK__', fallback)
    payload = script_json(cards)
    page = page.replace('__DATA__', payload)
    if persist:
        stream = io.StringIO(newline='')
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['Organization ID', 'Organization', 'Role', 'Directory category', 'What they provide', 'PA connection', 'Public business facts', 'Business inquiry', 'Source URLs'])
        for c in cards:
            writer.writerow([c['id'], c['name'], '; '.join(c['roles']), '; '.join(c['categories']),
                             ' | '.join(r['description'] for r in c['routes']),
                             ' | '.join(f['value'] for f in c['facts'] if f['claim']=='company-pa-connection') or ' | '.join(r['pa_connection'] for r in c['routes']),
                             ' | '.join(f['value'] for f in c['facts'] if f['claim']!='company-pa-connection'),
                             c['routes'][0]['url'], ' | '.join(dict.fromkeys(s['source_url'] for s in c['sources']))])
        (ROOT / 'pennsylvania-companies.csv').write_text(stream.getvalue(), encoding='utf-8-sig', newline='')
    return brand_page(externalize(page, payload, cards, 'data/public-pa-companies.json', persist=persist))


def main():
    data = load_directory()
    OUT.write_text(build_page(data, persist=True))
    print(f'Built Pennsylvania company directory: {len(build_model(data))} organization identities')


if __name__ == '__main__':
    main()
