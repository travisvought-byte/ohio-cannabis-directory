# Review policy

Decided by the directory owner on October 21, 2026 ([issue #22](https://github.com/travisvought-byte/ohio-cannabis-directory/issues/22)). Implemented in `build_review_queue.py`; the current backlog is in [REVIEW_QUEUE.md](REVIEW_QUEUE.md).

## Two review cycles

| Cycle | Applies to | Interval | What it covers |
| --- | --- | --- | --- |
| **Full review** | Ohio operators (cultivators, processors, dispensaries), testing labs, and every listing whose service area is Ohio statewide or an Ohio region | 90 days | Operating status, license where applicable, services, contacts, Ohio coverage and source dates, from primary sources |
| **Routine verification** | National and multistate vendors (service area begins "Nationwide" or "Multistate") | 180 days | Website resolves, cannabis service page is live, a contact route works, and Ohio service coverage is still stated |

A routine verification sets `Last Reviewed`, but the review file must record it as a routine verification (`"scope": "routine-verification"` on the completed item) so it is never mistaken for a full review.

## Immediate review

Any reported closure, license action, ownership change or material correction is reviewed immediately, regardless of schedule. Record each report in `data/review-triggers.json` with its source and date. Open triggers are queued as **P0**. Set `resolved_on` and `resolution` once the review is complete; keep the entry for history.

Reports usually arrive through the status-change and correct-record issue forms, email, or the regulator's announcements. A report is a lead: the review confirms it against primary sources before any record changes.

## Priorities

- **P0:** open review triggers.
- **P1:** named open issues, operators, labs and community resources that are due or undated, and listings without a website.
- **P2:** remaining due or undated business providers.

A blocked or failed retrieval is recorded as an attempt and does not reset the review date.

## Forecast

The queue also lists how many listings come due in the next 60 days, by week and cycle, so review batches can be planned before they become overdue.
