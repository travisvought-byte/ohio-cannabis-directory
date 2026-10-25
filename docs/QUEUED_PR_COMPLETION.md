# Completion of queued pull requests

Issue #54 integrates the six queued changes against the current main branch, including the published Pennsylvania referral pilot. Each original PR head is retained as an ancestor, allowing one reviewed integration merge to complete the queue without six separate merge sequences.

| PR | Result |
|---|---|
| #30 | Weekly read-only audit; added a current-date diagnostic mode while keeping committed builds reproducible, plus retained report artifacts. |
| #32 | Strict path classifier and bypass tests; tool regression job now also checks the actual issue-queue builder, risk reporter and research references. |
| #35 | Twice-weekly bounded issue manifest; now reads every API page, recognizes issue URLs and qualified references, and does not imply that candidates are unclaimed. |
| #37 | Read-only PR risk report; added complete-count, immutable-tree mode and blob-identity checks, including symlink/executable and unavailable-metadata regressions. |
| #39 | Ohio/Michigan policy proposals using existing dated law evidence, local editable drafts, jurisdiction-safe exports and official contacts. Existing PA pages and Ohio-specific assessments are preserved. |
| #44 | Research-only PA batch: 28 candidates, 29 sources and eight sample locations. DOH and PSP now reuse the permanent agency IDs introduced by the public referral pilot, bringing proposed existing-identity matches to eleven. No operator ownership/permit claims are newly reconciled or published. |

The original issues' automation scope is reporting and preparation. Autonomous coding-agent execution and automatic approval/merge are not part of these completed tools.

## Closed V4.20 PR #3

The eight organization additions from the old PR are already present in the current canonical directory:

| Organization | Permanent ID |
|---|---|
| Mood Leaf | org-105e0713e773 |
| SIPE Promotional Products | org-3af4221fa5d1 |
| Precise TB Solutions | org-baee0f174df2 |
| Courier Pro Logistics | org-fb49bcaddd77 |
| Tom & Berry Premium Reserve | org-271d2e550b0d |
| SCM Promotions | org-646560c1ff20 |
| Ohio Women’s Cannabis Chamber of Commerce | org-d124f071dca0 |
| GLEAF / Gleaf Group | org-ac6c53cdc50a |

The current changelog includes v4.20, shared builders retain GoatCounter through `assets/analytics.js`, and citation/archive metadata has advanced to v4.37. The old PR's release counts, metadata and upload instructions are superseded. No organization addition from it is missing, and restoring its old generated pages or duplicate version fields would regress the current site. It can remain closed without a new merge.

## Validation

The integration PR records final Python, JavaScript, browser, workflow-tool and research-reference results and the tested tree hash. No canonical public directory record, release version or evidence-review date changes in this integration.

The policy UI preserves the existing law summaries and October 21 evidence dates. An October 24 direct re-fetch of Michigan's statute page returned HTTP 403, so it was recorded as an unsuccessful recheck, not a fresh review. Ohio's cited March 20 statute page was readable and consistent with the existing entry. No law evidence date was reset by this UI integration.
