# Seed directory release review — November 2026

## Source checks
- Grow Your BLYZZZ: https://growyourblyzzz.com/ — 65+ souvenir strains, Traders World Building 11, Lebanon; site explicitly disclaims seed viability.
- Super Dank Seed Bank: https://superdankseed.com/ — seller advertises breeder brands and nationwide shipping; pickup details require confirmation.
- Dutch Wilson Genetics: https://dutchwilsonseeds.com/ — Ohio breeder, regular/feminized, Ohio Dumpster crosses.
- Great Lakes Genetics: https://www.greatlakesgenetics.com/ — catalog identifies Kavman Kannabliss, World Breeders, 12/12 Seed Co., Calyx Bros., Preservation Seeds, Cat Dad's Collection, Subcool Seeds, Backyard Boogie, Satori Seeds, Off-Grid Seeds, Unicorn Genetics, Golden Coast Genetics, Maha Kala Seeds. Breeder listing does not establish Ohio origin.
- Lake Erie Cannabis: https://www.lakeeriecannabis.com/seeds — seed order-request workflow and 147 strain profiles; verify location.
- Ohio's Best Seed Bank: https://ohiosbestseedbank.com/ — mailing address only, no onsite sales; outside-Ohio third-party fulfillment.
- Mosca Seeds: https://moscaseeds.com/cannabis-seeds-near-me/ — lists Gardening Indoor in North Lima (locator typo: GARDENING INOOR). Current stock unconfirmed.
- Exotic Gardens: https://billsbudblog.com/2025/10/08/exotic-gardens/ — third-party 2025 account describes seeds and genetics in Canton; verify current stock.

## Release blockers
1. ~~build_seeds.py hardcodes one Ohio grow-supply lead; inaccurate for 16 records.~~ Resolved: the count is computed from records whose role starts with "Grow supplies".
2. Generator claims no Ohio seller has pickup, despite sellers advertising physical locations or appointment pickup; differentiate claimed pickup and verified stock. Partly resolved: the sentence now follows an optional `pickup_verified` field. Set it only when the seller's own page confirms pickup; stock still needs direct confirmation.
3. ~~Exact-match area filter requires controlled location values.~~ Resolved: build_seeds.py rejects any area outside Ohio / Michigan / National and builds the filter options from the data.
4. Seed sex and flowering behavior must remain separate filters.
5. Distinguish official seller catalog, breeder locator, third-party account, and unverified lead.
6. Agricultural seed-labeler registration is not proof of cannabis retail authorization.
7. Rebuild generated seeds.html, validate output, and merge only after review.
