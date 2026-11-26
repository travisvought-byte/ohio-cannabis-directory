# National cannabis CRM research leads (batch 2026-11-25)

Status: **research leads, not published.** Nothing here is read by any build script or page.

What this is: per-state lead files (`<ST>.json`, plus `US.json` for nationwide or unlocated records) from the
national cannabis industry mapping pass. Sources merged: the MJBizCon 2026 planner (495 exhibitors, 207 announced
speakers), MJBizCon exhibitor enrichment, event rosters, and state-by-state research of regulators, operators,
associations, advocates, labs, media, events and public officials.

Rules applied:
- Every record cites at least one source URL. Records without one were left out.
- Records already in `data/directory.json` are not repeated here.
- `confidence: "verified"` means a primary-domain source shows the fact; `"lead"` means it still needs a primary-source
  check (most research this pass came from search results, not opened pages).
- People are limited to published professional roles (executives, agency heads, announced speakers, public officials).
  No private contact details are included.

Before anything moves into `directory.json`: open the primary source, record evidence with a review date, and follow
the evidence standard and inclusion rules in `AGENTS.md`. See `index.json` for per-state counts.
