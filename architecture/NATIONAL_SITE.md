# National section

Tracking: #183. Owner direction, November 15 to 16, 2026: build the national resource top-down, with Ohio as the template and every state working toward it. The intended address is the-reefer.com, which is held as a domain only until the owner connects it.

## What is built

`build_national.py` writes `national/`: a home page and one page for each of the 50 states and DC. The pages are generated and are never hand-edited.

Each state page has the same two parts.

1. **The law.** The shared questions in `data/state-permissions.json`, each answer with its citation, review date and evidence level. An unanswered question reads "Not yet reviewed" and says that this does not mean prohibited.
2. **Directory and local help.** The seven pathways of the [state directory contract](STATE_DIRECTORY_CONTRACT.md). A state with a pack shows the level it earns in `data/state-scorecard.json` under the [completion standard](STATE_COMPLETION_STANDARD.md), plus what the next level needs. A state without a pack shows "Not started" for all seven.

The home page lists every jurisdiction, the national items that cover every state, and the scorecard for the states that have a guide.

The pages add no claim of their own. `tests/test_national.py` checks that every answer shown comes from the data, that levels come only from the scorecard, and that the committed pages match the build.

## How a state moves toward Ohio

1. Answer the shared law questions from the state's own sources (work like #174 and #180). The state page fills in on the next build.
2. Add the state to `data/state-standard.json` with a dated regulator count, then add its pack as a pilot (work like #182 for Washington). The scorecard picks it up and the seven pathways start showing earned levels.
3. Raise each pathway to Ohio's level. The pilot label drops when every pathway matches Ohio's or better.

## Publishing

Pages use relative links, so the folder can be served from any address. Until `NATIONAL_ORIGIN` is set at build time, pages carry no canonical address and ask search engines not to index them. Connecting the-reefer.com is an owner decision and a separate issue: GitHub Pages allows one custom domain per repository, and this repository's is currently `weed.vethomeguard.org`.

## Open questions for the owner

- Site name. The pages use "The Reefer" as a working name taken from the domain.
- Where the pilot states' pathway links should point. Pennsylvania and New York link to the shared `state.html` in this repository.
- Whether Ohio pages should link to the national home. This change leaves the Ohio site untouched.
