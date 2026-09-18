#!/usr/bin/env python3
"""Build the OCHBS 2026 intake page.

Captures new organizations and first-party verifications at the conference,
offline, and exports CSV in the master workbook's exact column order so rows
drop straight into the Directory tab.

Embeds a name index of the existing 511 records so the page can warn when an
organization is already in the directory. In that case the right action is to
verify the existing row, not create a duplicate.
"""
import json
import pandas as pd

SRC = "/mnt/user-data/uploads/Ohio_Cannabis_Ecosystem_Directory_v67_Master.xlsx"
OUT = "/mnt/user-data/outputs/ochbs-2026-intake.html"
OUT_OF_SCOPE = "Out of scope — flagged for removal or separate list"


def norm(s):
    """Loose key for duplicate matching: lowercase, alphanumeric only,
    with common company suffixes stripped."""
    s = str(s).lower()
    for junk in (" llc", " inc", " ltd", " co", " corp", " lp", " llp", " plc"):
        s = s.replace(junk, " ")
    return "".join(ch for ch in s if ch.isalnum())


def main():
    df = pd.read_excel(SRC, sheet_name="Directory", header=3).dropna(how="all")

    index = []
    for _, r in df.iterrows():
        name = str(r["Organization / Business Name"]).strip()
        index.append({
            "n": name,
            "k": norm(name),
            "c": str(r["Category"]).strip(),
            "s": 0 if str(r["Category"]).strip() == OUT_OF_SCOPE else 1,
        })

    cats = sorted({i["c"] for i in index if i["s"]})
    cat_opts = "\n".join(f'<option>{c}</option>' for c in cats)

    page = (TEMPLATE
            .replace("__INDEX__", json.dumps(index, ensure_ascii=False, separators=(",", ":")))
            .replace("__CAT_OPTS__", cat_opts)
            .replace("__N__", str(len(index))))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {OUT} — {len(index)} names indexed, {len(cats)} categories")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OCHBS 2026 Intake</title>
<style>
  :root{
    --paper:#EDEFE8; --paper-deep:#E3E6DC; --ink:#16231B; --ink-soft:#4A5A50;
    --rule:#C2CAB9; --field:#5F7434; --field-deep:#43521F; --flag:#8A4B2A;
    --serif:Georgia,"Iowan Old Style","Palatino Linotype",serif;
    --sans:"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.5}
  .wrap{max-width:34rem;margin:0 auto;padding:0 1.1rem}
  header{border-bottom:1px solid var(--rule);padding:1.5rem 0 1.1rem}
  h1{font-family:var(--serif);font-weight:400;font-size:1.6rem;margin:0 0 .3rem}
  .sub{margin:0;color:var(--ink-soft);font-size:.88rem}

  form{padding:1.2rem 0 0}
  label{display:block;font-size:.82rem;color:var(--ink-soft);margin:.9rem 0 .2rem}
  label .req{color:var(--flag)}
  input,select,textarea{
    width:100%;font-family:var(--sans);font-size:16px;color:var(--ink);
    background:#F6F7F2;border:1px solid var(--rule);border-radius:2px;
    padding:.55rem .6rem;appearance:none;
  }
  textarea{min-height:4.5rem;resize:vertical;line-height:1.45}
  input:focus,select:focus,textarea:focus{outline:2px solid var(--field-deep);outline-offset:1px;border-color:var(--field)}
  select{background-image:url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='7'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%234A5A50' stroke-width='1.4' fill='none'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right .6rem center;padding-right:1.9rem}
  .pair{display:flex;gap:.6rem}
  .pair>div{flex:1;min-width:0}

  .dupe{
    margin-top:.45rem;padding:.55rem .65rem;border-left:3px solid var(--flag);
    background:#F2EAE4;font-size:.85rem;color:#5C3520;display:none;
  }
  .dupe strong{font-weight:600}
  .dupe.on{display:block}

  .save{
    width:100%;margin:1.4rem 0 .4rem;font-family:var(--sans);font-size:1rem;
    background:var(--field);color:#F3F5EE;border:0;border-radius:2px;
    padding:.8rem;cursor:pointer;
  }
  .save:hover{background:var(--field-deep)}
  .save:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
  .save.verify{background:var(--flag)}

  .note{font-size:.8rem;color:var(--ink-soft);margin:.3rem 0 0}

  .stack{border-top:1px solid var(--rule);margin-top:2rem;padding:1.2rem 0 3rem}
  .stack h2{font-family:var(--serif);font-weight:400;font-size:1.1rem;margin:0 0 .2rem}
  .count{font-size:.85rem;color:var(--ink-soft);margin:0 0 .9rem}
  .entry{border-bottom:1px solid var(--rule);padding:.7rem 0;font-size:.9rem;display:flex;gap:.6rem;align-items:baseline}
  .entry .who{flex:1;min-width:0}
  .entry .who b{font-weight:600;display:block}
  .entry .who span{color:var(--ink-soft);font-size:.82rem}
  .entry .tag{font-size:.72rem;color:var(--flag);white-space:nowrap}
  .entry button{background:none;border:0;color:var(--ink-soft);cursor:pointer;font-size:1.1rem;padding:0 .2rem}
  .entry button:hover{color:var(--flag)}

  .actions{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1.1rem}
  .btn{font-size:.85rem;background:var(--paper-deep);border:1px solid var(--rule);color:var(--ink);padding:.5rem .8rem;border-radius:2px;cursor:pointer}
  .btn:hover{border-color:var(--field)}
  .warn{margin-top:1rem;padding:.6rem .7rem;border-left:3px solid var(--flag);background:#F2EAE4;font-size:.84rem;color:#5C3520;display:none}
  .warn.on{display:block}
  @media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>

<header class="wrap">
  <h1>OCHBS 2026 intake</h1>
  <p class="sub">Capture it standing up. Everything stays on this device until you export.</p>
</header>

<div class="wrap">
  <div class="warn" id="nostore">This browser is blocking local storage, so entries will be lost if the page reloads. Export after every few records.</div>

  <form id="f" autocomplete="off">
    <label for="org">Organization <span class="req">*</span></label>
    <input id="org" required>
    <div class="dupe" id="dupe"></div>

    <div class="pair">
      <div>
        <label for="cat">Category</label>
        <select id="cat">
          <option value="">Decide later</option>
          __CAT_OPTS__
        </select>
      </div>
      <div>
        <label for="type">Type</label>
        <select id="type">
          <option>Business</option>
          <option>Nonprofit</option>
          <option>Individual</option>
        </select>
      </div>
    </div>

    <label for="person">Contact person and title</label>
    <input id="person" placeholder="Name &mdash; role">

    <div class="pair">
      <div>
        <label for="email">Email</label>
        <input id="email" type="email" inputmode="email">
      </div>
      <div>
        <label for="phone">Phone</label>
        <input id="phone" type="tel" inputmode="tel">
      </div>
    </div>

    <label for="web">Website</label>
    <input id="web" inputmode="url" placeholder="company.com">

    <label for="keys">What they actually do</label>
    <input id="keys" placeholder="Packaging; child-resistant; labeling">

    <label for="area">Service area</label>
    <input id="area" placeholder="Ohio statewide">

    <label for="notes">Notes and what they told you</label>
    <textarea id="notes" placeholder="Said in person that they now serve Ohio dispensaries directly&hellip;"></textarea>

    <label for="gap">Unresolved fact to check later</label>
    <input id="gap" placeholder="Whether the Columbus location is still open">

    <button class="save" id="save" type="submit">Save record</button>
    <p class="note">Saved as first-party evidence, stamped with today's date. Verify before promoting into the master.</p>
  </form>
</div>

<section class="wrap stack">
  <h2>Captured</h2>
  <p class="count" id="count">Nothing yet.</p>
  <div id="list"></div>
  <div class="actions">
    <button class="btn" id="csv">Export CSV for the master</button>
    <button class="btn" id="wipe">Clear all</button>
  </div>
</section>

<script>
const INDEX = __INDEX__;
const KEY = 'ochbs2026-intake';
const $ = id => document.getElementById(id);
const F = ['org','cat','type','person','email','phone','web','keys','area','notes','gap'];

let rows = [];
let storeOK = true;
try {
  const raw = localStorage.getItem(KEY);
  if (raw) rows = JSON.parse(raw);
} catch(e) { storeOK = false; $('nostore').classList.add('on'); }

function persist(){
  if (!storeOK) return;
  try { localStorage.setItem(KEY, JSON.stringify(rows)); }
  catch(e){ storeOK = false; $('nostore').classList.add('on'); }
}

const norm = s => String(s).toLowerCase()
  .replace(/ (llc|inc|ltd|co|corp|lp|llp|plc)\b/g,' ')
  .replace(/[^a-z0-9]/g,'');

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

let matched = null;

$('org').addEventListener('input', () => {
  const k = norm($('org').value);
  matched = null;
  if (k.length > 3){
    matched = INDEX.find(i => i.k === k)
      || INDEX.find(i => i.k.length > 4 && (i.k.includes(k) || k.includes(i.k)));
  }
  const box = $('dupe'), btn = $('save');
  if (matched){
    box.className = 'dupe on';
    box.innerHTML = matched.s
      ? `Already in the directory as <strong>${esc(matched.n)}</strong> under ${esc(matched.c)}. Capture this as a first-party verification instead of a new row.`
      : `<strong>${esc(matched.n)}</strong> is currently marked out of scope. If they are operating, this is a first-party correction worth recording.`;
    btn.textContent = 'Save as verification';
    btn.classList.add('verify');
    if (!$('cat').value && matched.s) $('cat').value = matched.c;
  } else {
    box.className = 'dupe';
    btn.textContent = 'Save record';
    btn.classList.remove('verify');
  }
});

$('f').addEventListener('submit', e => {
  e.preventDefault();
  const r = {};
  F.forEach(f => r[f] = $(f).value.trim());
  if (!r.org) return;
  r.dupe = matched ? matched.n : '';
  r.when = new Date().toISOString().slice(0,10);
  rows.unshift(r);
  persist();
  $('f').reset();
  $('dupe').className = 'dupe';
  $('save').textContent = 'Save record';
  $('save').classList.remove('verify');
  matched = null;
  draw();
  $('org').focus();
  window.scrollTo({top:0, behavior:'instant'});
});

function draw(){
  $('count').textContent = rows.length
    ? `${rows.length} record${rows.length===1?'':'s'} on this device.`
    : 'Nothing yet.';
  $('list').innerHTML = rows.map((r,i) => `<div class="entry">
    <div class="who"><b>${esc(r.org)}</b><span>${esc(r.person || r.cat || r.keys || '—')}</span></div>
    ${r.dupe ? '<div class="tag">verification</div>' : ''}
    <button type="button" data-i="${i}" aria-label="Remove ${esc(r.org)}">&times;</button>
  </div>`).join('');
}

$('list').addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b) return;
  rows.splice(+b.dataset.i, 1);
  persist();
  draw();
});

$('wipe').addEventListener('click', () => {
  if (!rows.length) return;
  if (!confirm(`Delete all ${rows.length} records? Export first if you have not.`)) return;
  rows = [];
  persist();
  draw();
});

$('csv').addEventListener('click', () => {
  if (!rows.length) return;
  // master column order, so rows paste straight into the Directory tab
  const head = ['Category','Organization / Business Name','Type','Contact Person','Email',
    'Phone','Website','Source(s)','Service Area','Notes','Needs Research','Seed Source',
    'Verification Tier','Capabilities / Keywords'];
  const q = v => '"' + String(v == null ? '' : v).replace(/"/g,'""') + '"';
  const body = rows.map(r => [
    r.cat, r.org, r.type, r.person, r.email, r.phone, r.web,
    'First-party, OCHBS 2026',
    r.area, r.notes, r.gap,
    'OCHBS 2026 intake, ' + r.when + (r.dupe ? ' — verification of existing row: ' + r.dupe : ''),
    r.dupe ? 'First-party verification — review against existing row'
           : 'First-party — unverified against second source',
    r.keys
  ].map(q).join(','));
  const csv = [head.map(q).join(',')].concat(body).join('\r\n');
  const url = URL.createObjectURL(new Blob(['\ufeff'+csv], {type:'text/csv;charset=utf-8'}));
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ochbs-2026-intake.csv';
  a.click();
  URL.revokeObjectURL(url);
});

draw();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
