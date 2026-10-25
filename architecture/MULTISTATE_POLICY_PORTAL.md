# Multi-state policy portal: first resident-state expansion

Owner direction: comparative research should help residents propose changes in their own state's cannabis policy. Tracking: #38, following #23/#27.

## Working first edition

`compare.html` adds an Ohio/Michigan home-state selector, policy topic, comparison state, cited legal summaries and a resident-controlled proposal. It reuses the law entries in `data/state-comparison.json`; no existing review date or legal claim is changed by this UI work. Oregon remains a reference where an entry exists. A topic with no reviewed model cannot produce a new proposal.

The existing market lesson and forecasts remain explicitly an Ohio assessment of Michigan's experience. Selecting Michigan does not convert Ohio forecasts into Michigan forecasts. The page does not rank the states or claim that a legal difference proves a better outcome.

`policy_portal.py` renders the proposal section as part of `build_compare.py`, including its script and law data. This keeps `release_tools.py` and `tests/check_data.py` on the same deterministic build path. Personal fields are not stored or sent. Copy, text download and letter-only printing use the current draft. Changing jurisdictions/topics after editing preserves the draft and blocks exports until the resident explicitly rebuilds. No-JavaScript readers retain cited law cards, proposal instructions and official contact routes.

Michigan's Senate lookup and its link to the official House website were inspected on October 21, 2026:
- https://www.senate.michigan.gov/senators/find-your-senator/
- https://www.senate.michigan.gov/ (links to https://www.house.mi.gov/)

Direct House/legislature retrieval attempts returned timeout/502/403. These attempts are not a completed House-site review. The portal labels the House link as its official website, not a verified address lookup. No legislator roster or recipient identity is inferred.

## Next research batches

Prioritize a complete, useful Ohio/Michigan comparison before adding many thin states. Each batch needs official law/regulator sources, effective dates where established, reviewed dates, exceptions and clear medical/adult-use distinctions.

1. Record clearing: automatic versus application routes, covered offenses, exclusions, implementation and actual access. Include official court/application routes.
2. Taxes and revenue: distinguish retail/wholesale, medical/adult-use and local taxes; use actual distributions and outcomes, not only statutory promises.
3. Home growing and medical/patient protections, including employment, housing and veterans' access. Separate enacted protections from proposed bills.
4. Independent entry: microbusiness access, fees, ownership limits, local permission and financing barriers. Add dated operational results.
5. Follow the updated #42 directory priorities: Pennsylvania, Washington state and New York, then Michigan and Kentucky. Reuse the limited Michigan policy portal without claiming a complete Michigan ecosystem guide. Illinois can remain a comparison reference. New resident-state policy coverage still requires topic-specific evidence.

## What “worked elsewhere” must establish

A model law and an outcome study are separate evidence objects. Before displaying a success claim, record:

- Policy goal and measurable result; baseline, observation period and source definition.
- Enacted/effective/operational dates, medical/adult-use population and market maturity.
- Plausible alternative explanations, study limitations and whether the evidence supports association or causation.
- Relevant differences in local opt-outs, taxes, licensing/capacity, enforcement, neighboring markets and patient access.
- Benefits and costs for consumers, patients, independent entrants, existing businesses and public programs.
- Applicability to the resident's state: supported similarities, differences and unresolved questions.

Until those fields are researched, label a jurisdiction a policy example, not a success model. No automated “best state” score. Research failures remain gaps rather than fresh verification.

## Deliberate remaining work

Outcome matching and additional topics are not completed by the initial portal UI. Integrating state-specific lessons into a common schema needs a separate reviewable change so Ohio-specific data is not silently relabeled. Use official state lawmaker lookup links initially; API roster integration can follow without hand-maintaining multi-state contact lists.
