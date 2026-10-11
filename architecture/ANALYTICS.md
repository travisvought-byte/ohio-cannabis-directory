# Directory usage measurement

Open https://travisvought.goatcounter.com/ and look for paths beginning `action:`.

- `navigate:<page>`: section clicks from each source page.
- `download:<filename>`: PDF and data link clicks; a click is not proof of a completed download.
- `outbound:<domain>`: visits to provider/source websites, grouped by domain.
- `email-contact`, `phone-contact`: contact link clicks; not proof of a message or call.
- `search-used`, `search-no-results`: debounced search activity; no search terms are recorded.
- `filter-changed`, `category-filter`, `distance-sort`: navigation actions where supported.
- `assessment-export`, `assessment-print`, `buyer-guide-print`: worksheet actions.

Review weekly: which pages receive visitors, which routes get clicks, where searches fail, and whether visitors open or print resources. Compare like periods; events are not a conversion funnel or exact unique-person counts. No historical click data can be reconstructed.

Buyer and assessment inputs are excluded. Query strings are stripped from pageview paths. Outbound links report domains only; email and phone values are excluded. No coordinates are sent. GoatCounter itself handles ordinary request metadata under its existing privacy policy.

Local verification uses a mock count function; production delivery depends on GoatCounter availability and visitor blockers. The site remains usable when analytics is unavailable.
