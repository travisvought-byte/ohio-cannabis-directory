"""Validate and normalize independently sourced state market observations.

The dataset is intentionally empty until regulator figures are verified.
No pairwise comparisons or inferred zero values are stored.
"""
from datetime import date

METRICS = {
    "retail_sales_usd": "USD",
    "operational_retail_locations": "count",
    "licensed_retailers": "count",
    "average_flower_price_usd_per_gram": "USD/g",
    "cannabis_tax_receipts_usd": "USD",
}
SCOPES = {"medical", "adult_use", "combined"}
PERIODS = {"day", "month", "quarter", "year"}


def validate_market(data, observations):
    states = set(data["states"])
    sources = {s["id"]: s for s in data["sources"]}
    keys = set()
    for n, row in enumerate(observations):
        where = f"market[{n}]"
        assert row["state"] in states, f"{where}: unknown state"
        assert row["metric"] in METRICS, f"{where}: unsupported metric"
        assert row["unit"] == METRICS[row["metric"]], f"{where}: incorrect unit"
        assert row["scope"] in SCOPES, f"{where}: invalid market scope"
        assert row["period"] in PERIODS, f"{where}: invalid period"
        start, end = date.fromisoformat(row["period_start"]), date.fromisoformat(row["period_end"])
        assert start <= end, f"{where}: invalid period dates"
        assert end <= date.fromisoformat(data["as_of"]), f"{where}: future observation"
        assert isinstance(row["value"], (int, float)) and not isinstance(row["value"], bool), f"{where}: numeric value required"
        assert row["value"] >= 0, f"{where}: negative value"
        assert row["source_ids"], f"{where}: sources required"
        assert all(sid in sources for sid in row["source_ids"]), f"{where}: unknown source"
        assert any(sources[sid]["kind"] in {"government", "regulator"} for sid in row["source_ids"]), f"{where}: regulator source required"
        assert isinstance(row.get("definition"), str) and row["definition"].strip(), f"{where}: definition required"
        key = (row["state"], row["metric"], row["scope"], row["period_start"], row["period_end"])
        assert key not in keys, f"{where}: duplicate observation"
        keys.add(key)
    return len(observations)


def comparable(observations, metric, scope, start, end):
    """Only match exactly identical reporting periods and market scope."""
    return {row["state"]: row["value"] for row in observations
            if row["metric"] == metric and row["scope"] == scope
            and row["period_start"] == start and row["period_end"] == end}
