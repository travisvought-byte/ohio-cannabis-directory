"""Accessible source-linked market trend visualization from state-first observations."""
from collections import defaultdict
from html import escape


def render_market_trends(observations, state_names, source_links):
    groups = defaultdict(list)
    for row in observations:
        groups[(row["state"], row["metric"], row["scope"], row["unit"])].append(row)
    parts = []
    for (state, metric, scope, unit), rows in sorted(groups.items()):
        if len(rows) < 2:
            continue
        rows = sorted(rows, key=lambda r: (r["period_end"], r["period_start"]))
        # Only draw a trend for the same point-in-time reporting type.
        periods = {r["period"] for r in rows}
        if len(periods) != 1:
            continue
        maximum = max(r["value"] for r in rows)
        parts.append(
            '<article class="card market-trend" data-state="' + escape(state, quote=True) + '">'
            '<h3>' + escape(state_names[state]) + ': ' + escape(metric.replace("_", " ")) + '</h3>'
            '<p class="muted">' + escape(scope.replace("_", " ")) + ' · ' + escape(unit) +
            ' · Same metric and reporting type over time; not a causal analysis.</p>'
        )
        for row in rows:
            width = (100 * row["value"] / maximum) if maximum else 0
            links = ' '.join(source_links(sid) for sid in row["source_ids"])
            parts.append(
                '<div class="market-trend-row"><span>' + escape(row["period_end"]) + '</span>'
                '<div class="market-trend-track"><div class="market-trend-fill" style="width:' +
                f'{width:.2f}%' + '"></div></div>'
                '<strong>' + f'{row["value"]:,.0f}' + '</strong></div>'
                '<p class="muted">' + escape(row["definition"]) + ' ' + links + '</p>'
            )
        parts.append('</article>')
    if not parts:
        return '<p class="muted">More source-verified observations are needed for trends.</p>'
    return ''.join(parts)
