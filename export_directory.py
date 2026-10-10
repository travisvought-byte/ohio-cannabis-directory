"""Regenerate compatibility downloads from canonical structured data."""
import csv,json
from directory_data import ROOT,load_records,load_relationship_records,load_seed_records

def export_csv(name,rows,bom=False):
 with (ROOT/name).open('w',encoding='utf-8-sig' if bom else 'utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
def main():
 export_csv('ohio-cannabis-directory.csv',load_records(),True)
 export_csv('b2b-relationships.csv',load_relationship_records())
 (ROOT/'seed-suppliers.json').write_text(json.dumps(load_seed_records(),ensure_ascii=False,indent=2)+'\n')
 print('Exported compatibility CSVs and seed download from data/directory.json')
if __name__=='__main__':main()
