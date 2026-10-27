"""State-first projections from canonical source-linked comparison records.

No pairwise records are stored: every topic is indexed once per state.
"""
import html


def profiles(data):
    result = {code: {"name": name, "topics": {}} for code, name in data["states"].items()}
    for topic in data["topics"]:
        for entry in topic["entries"]:
            code = entry["state"]
            if code not in result:
                raise ValueError(f"Unknown state: {code}")
            if topic["id"] in result[code]["topics"]:
                raise ValueError(f"Duplicate state/topic: {code}/{topic['id']}")
            result[code]["topics"][topic["id"]] = {
                "label": topic["label"],
                "question": topic["question"],
                "summary": entry["summary"],
                "citation": entry["citation"],
                "reviewed_on": entry["reviewed_on"],
                "effective_on": entry.get("effective_on"),
                "source_ids": list(entry["source_ids"]),
            }
    return result


def render_coverage(data):
    """Source-derived coverage only, not a cannabis-policy quality score."""
    state_profiles = profiles(data)
    count = len(data["topics"])
    esc = lambda value: html.escape(str(value), quote=True)
    parts = ['<div class="card" aria-label="Reviewed coverage by state"><h3>Research coverage</h3>',
             '<p class="muted">Source-linked policy topics reviewed per state. Coverage is not a policy score.</p>',
             '<div class="coverage-grid">']
    for code, profile in state_profiles.items():
        reviewed = len(profile["topics"])
        percent = round(100 * reviewed / count) if count else 0
        parts.append(
            f'<div class="coverage-item" data-state="{esc(code)}">'
            f'<strong>{esc(profile["name"])}</strong><span>{reviewed} of {count} topics</span>'
            f'<div class="coverage-track" role="progressbar" aria-label="{esc(profile["name"])} reviewed topics" '
            f'aria-valuenow="{reviewed}" aria-valuemin="0" aria-valuemax="{count}">'
            f'<div class="coverage-fill" style="width:{percent}%"></div></div></div>'
        )
    parts.append('</div></div>')
    return ''.join(parts)
