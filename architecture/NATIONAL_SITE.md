# National section

Tracking: #183. Owner direction, November 15 to 16, 2026: build the national resource top-down, with Ohio as the template and every state working toward it. The intended address is the-reefer.com, which is held as a domain only until the owner connects it.

## What is built

Owner direction, November 16, 2026: the site is a cannabis information and resource portal. `build_national.py` writes `national/` (generated, never hand-edited):

- **Home** (`index.html`): a state picker, the law questions to compare, national help grouped by need, and every state.
- **Compare the law** (`law-<question>.html`, one per shared question): every state and DC side by side with a status filter. Rows link to the state page for the full answer and its source.
- **Help by need** (`help.html`): the national items from `data/state-permissions.json`, grouped by need.
- **About** (`about.html`): how answers are checked, the evidence labels, ground rules, build progress and corrections.
- **One page per state and DC.**

Each state page has the same two parts.

1. **The law.** The shared questions in `data/state-permissions.json`, each answer with its citation, review date and evidence level. An unanswered question reads "Not yet reviewed" and says that this does not mean prohibited.
2. **Directory and local help.** The seven pathways of the [state directory contract](STATE_DIRECTORY_CONTRACT.md). A state with a pack shows the level it earns in `data/state-scorecard.json` under the [completion standard](STATE_COMPLETION_STANDARD.md), plus what the next level needs. A state without a pack shows "Not started" for all seven.

The pages add no claim of their own. `tests/test_national.py` checks that every answer shown comes from the data, that levels come only from the scorecard, and that the committed pages match the build.

## How a state moves toward Ohio

1. Answer the shared law questions from the state's own sources (work like #174 and #180). The state page fills in on the next build.
2. Add the state to `data/state-standard.json` with a dated regulator count, then add its pack as a pilot (work like #182 for Washington). The scorecard picks it up and the seven pathways start showing earned levels.
3. Raise each pathway to Ohio's level. The pilot label drops when every pathway matches Ohio's or better.

## Publishing

Owner direction, November 16, 2026: this repository's GitHub Pages site is the-reefer.com. The domain is registered at Wix; its DNS points the bare domain at GitHub Pages (A records 185.199.108.153, 185.199.109.153, 185.199.110.153 and 185.199.111.153) and `www` at `travisvought-byte.github.io`.

`scripts/build_pages_site.py` assembles the published site on every push to `main`:

- the national pages go to the site root with the-reefer.com as their canonical address (the committed copies in `national/` carry no canonical and stay out of search indexes);
- each Ohio page forwards to its own page at ohioweed.org, so the Ohio guide has one canonical copy;
- the shared state page and the Pennsylvania pages are published as built;
- the retired address `weed.vethomeguard.org` is replaced by the-reefer.com in the published copy only. Committed files still name the old address; moving them is a separate change.

`tests/test_pages_site.py` checks the assembled site.

## Open questions for the owner

- Site name. The pages use "The Reefer" as a working name taken from the domain.
- Where the pilot states' pathway links should point. Pennsylvania and New York link to the shared `state.html` in this repository.
- Whether Ohio pages should link to the national home. The Ohio site is untouched.
- Whether the Ohio pages should also be served in full at the-reefer.com instead of forwarding to ohioweed.org.
