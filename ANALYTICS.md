# Analytics questions

Travis will check delivery in the GoatCounter dashboard separately. Production `action:` arrivals have not been confirmed in this update. Local instrumentation checks do not establish dashboard delivery.

| Question | Action to review | Meaning |
| --- | --- | --- |
| How many people finish the self-check? | `assessment-completed` | All 33 questions answered; counted once per page session, not unique people. |
| How many download the visit companion? | `download-visit-plan` (current), `download-visit-companion` (earlier guide) | PDF-button clicks, not verified completed downloads. |
| Which calculators get used? | `supply-calculator-used` | First valid supply calculation per page session; label calculator removed. |
| Which homepage cards get clicked? | `home-` task-card actions | Clicks on the four homepage routes. |

In https://vhg-guide.goatcounter.com/, filter paths beginning `action:` and compare the same reporting periods. Blockers and disabled JavaScript can reduce coverage.

Exclude answers, notes, search text, calculator values and coordinates. Query strings are stripped. Outbound visits report domains only. The site remains usable without analytics. Implementation and other events are documented in [architecture/ANALYTICS.md](architecture/ANALYTICS.md).

## the-reefer.com

The national site (the-reefer.com) reports to the same GoatCounter dashboard through `assets/analytics.js`. Its paths begin `/the-reefer.com/` and its actions begin `action:the-reefer.com/`, so they never mix with ohioweed.org. Named home-page actions: `task:<card>` (the "What brings you here?" cards), `map-state` (map tile clicks), `state-picker` (the Pick your state box) and `family:<domain>` (links to the other sites). A sponsored spot's link reports `sponsor:<id>`, the spot's id in `data/national-sponsors.json`; that count is the only sponsor figure the site keeps, and nothing about the visitor goes to the sponsor. The privacy page (`privacy.html`, built by `build_national.py`) describes this counting; change it whenever `assets/analytics.js` changes what it records. Wix holds only the domain and does not see visits; GitHub Pages provides no visitor counts.

The pirate game (`pillage/`, Pillage the Reefer) reports four milestones through `window.directoryTrack`, as `action:the-reefer.com/index.html:pillage-…` (the counter names a page by its file name, and the game's page is `pillage/index.html`; the `pillage-` prefix keeps these apart from the home page): `pillage-new-game` (a voyage started), `pillage-first-pillage` (first merchant ship boarded), `pillage-map-piece` (a treasure map piece dug up) and `pillage-emerald-bale` (the game's main goal reached). Progress itself stays in the visitor's browser (`localStorage`) and is never sent.
