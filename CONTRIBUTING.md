Contributing

The preferred public intake route is the repository issue chooser:

https://github.com/travisvought-byte/ohio-cannabis-directory/issues/new/choose

Choose the form that best matches the change:

• Add an organization — a missing organization operating in or serving the Ohio cannabis market.
• Correct a record — contact information, category, capabilities, source, service area, or another factual correction.
• Report a status change — closure, rename, acquisition, merger, sale, or successor organization.
• Add a B2B relationship — a documented organization-to-organization relationship that belongs in the relationship layer.

Each form asks for evidence because every published row and relationship in this directory is intended to remain traceable to a named source.

GitHub issue forms require a GitHub account.

Field and conference intake

intake.html is a separate field/offline capture tool. It stores captured records in the browser on that device until they are exported as CSV. It does not automatically submit records to GitHub or change the published directory.

That separation is intentional: a submission is a research lead, not an automatic publication.

Pull requests

If you are comfortable working with CSV, you may also open a pull request.

• Organization records live at ohio-cannabis-directory.csv in the repository root.
• Relationship records live at b2b-relationships.csv in the repository root.
• Include the supporting source in the same proposed change.
• Do not hand-edit the embedded directory data inside index.html.

The current build scripts still regenerate the HTML from the maintainer’s master workbook. Accepted CSV changes therefore need to be reconciled into that source and the HTML regenerated before a release is complete.

What gets accepted

An entry belongs here if it is an organization operating in or serving the Ohio cannabis market, and its existence and relevance can be confirmed against a named source.

First-party submissions are welcome and are held to the same standard as any other. If you are submitting your own organization, say so. That is treated as evidence and recorded as part of the provenance.

What does not get accepted

• Entries with no verifiable source
• Personal contact detail that a person would not reasonably expect to be published
• Paid placement or paid ranking

There is no mechanism to pay for inclusion, position, verification, or emphasis. Keeping the public dataset independent is part of what makes it useful.

How verification works

Verification Tier separates source-verified rows from rows carrying a named open issue. Where something is unresolved, Needs Research identifies the specific unresolved fact rather than expressing general doubt.

Submissions enter as unverified research leads and are promoted only after the evidence is reviewed.

Records are not silently deleted. Organizations that close, merge, rename, or are superseded may move out of scope while remaining searchable for provenance and historical resolution.
