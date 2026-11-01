"""Convert a downloaded OCM 'Current OCM Licenses' export into the saved New York retail snapshot.

Usage: python scripts/snapshot_ny_ocm_licenses.py <Current_OCM_Licenses_YYYYMMDD.xlsx|csv> <retrieved_on YYYY-MM-DD>

The raw export is not committed: it contains a primary-contact personal name column and many
non-retail and applicant rows. This script keeps only rows whose Business Purpose includes retail
sales and that carry a date opened to the public, drops the personal-name and equity-category
columns, and records whole-file counts so the import denominator can be audited.
"""
import json,re,sys
from collections import Counter
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT_DIR=ROOT/'data/sources'
DROPPED=['Primary Contact Name','SEE Category']
KEEP={'License Number':'license_number','License Type':'license_type','License Status':'license_status','Operational Status':'operational_status',
      'Issued Date':'issued_on','Effective Date':'effective_on','Expiration Date':'expires_on','Entity Name':'entity_name','DBA':'dba','Location ID':'location_id',
      'Address Line 1':'address_1','Address Line 2':'address_2','City':'city','State':'state','Zip Code':'zip','County':'county','Region':'region',
      'Business Website':'website','Business Purpose':'business_purpose','Retail Activities Sales with Delivery':'delivery','Retail Activities Drive Thru':'drive_thru',
      'Retail Date Opened to Public':'opened_to_public_on','Hours of Operation':'hours'}
DATES={'issued_on','effective_on','expires_on','opened_to_public_on'}
def clean(key,value):
 if pd.isna(value):return None
 if key in DATES:return pd.Timestamp(value).date().isoformat()
 if key in ('delivery','drive_thru'):return bool(int(value))
 if key=='zip':return str(value).split('.')[0].zfill(5)
 return ' '.join(str(value).split())
def main(path,retrieved_on):
 df=pd.read_excel(path,dtype={'Zip Code':str}) if path.endswith('.xlsx') else pd.read_csv(path,dtype={'Zip Code':str})
 missing=set(KEEP)-set(df.columns)
 if missing:raise SystemExit('Export is missing columns: '+', '.join(sorted(missing)))
 retail=df['Business Purpose'].fillna('').str.contains('Retail Sales')&df['Retail Date Opened to Public'].notna()
 rows=[{v:clean(v,r[k]) for k,v in KEEP.items()} for _,r in df[retail].iterrows()]
 rows.sort(key=lambda r:(r['license_number'],r['location_id'] or ''))
 snapshot={
  'source_label':'NY Open Data: Current OCM Licenses (Office of Cannabis Management)',
  'source_url':'https://data.ny.gov/d/jskf-tt3q',
  'download_url':'https://data.ny.gov/api/views/jskf-tt3q/rows.csv?accessType=DOWNLOAD',
  'retrieved_on':retrieved_on,
  'export_file':re.sub(r'^[0-9a-f]{8}-','',Path(path).name),
  'export_rows':len(df),
  'export_counts':{'license_type':dict(Counter(df['License Type'].fillna('(blank)'))),'operational_status':dict(Counter(df['Operational Status'].fillna('(blank)')))},
  'kept_rule':'Business Purpose includes "Retail Sales" and Retail Date Opened to Public is present. Registered Organization medical rows carry no opening date in this export and are not kept.',
  'dropped_columns':DROPPED,
  'limitations':'Office of Cannabis Management open-data export. A license row and its operational status are a dated snapshot, not a live license verification. Hours, website and delivery flags are as reported to the regulator; confirm with the store. The export publishes no phone numbers or coordinates.',
  'rows':rows}
 out=OUT_DIR/f'new-york-ocm-retail-{retrieved_on}.json'
 out.write_text(json.dumps(snapshot,indent=1,ensure_ascii=False)+'\n')
 print(f'Saved {len(rows)} retail rows of {len(df)} to {out.relative_to(ROOT)}')
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit(__doc__)
 main(sys.argv[1],sys.argv[2])
