# Analytics questions

Travis will check delivery in the GoatCounter dashboard separately. Production `action:` arrivals have not been confirmed in this update. Local instrumentation checks do not establish dashboard delivery.

| Question | Action to review | Meaning |
| --- | --- | --- |
| How many people finish the self-check? | `assessment-completed` | All 33 questions answered; counted once per page session, not unique people. |
| How many download the visit companion? | `download-visit-plan` (current), `download-visit-companion` (earlier guide) | PDF-button clicks, not verified completed downloads. |
| Which calculators get used? | `supply-calculator-used` | First valid supply calculation per page session; label calculator removed. |
| Which homepage cards get clicked? | `home-` task-card actions | Clicks on the four homepage routes. |

In https://travisvought.goatcounter.com/, filter paths beginning `action:` and compare the same reporting periods. Blockers and disabled JavaScript can reduce coverage.

Exclude answers, notes, search text, calculator values and coordinates. Query strings are stripped. Outbound visits report domains only. The site remains usable without analytics. Implementation and other events are documented in [architecture/ANALYTICS.md](architecture/ANALYTICS.md).
