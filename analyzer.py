"""Apply the scoring model to collected rows."""

from __future__ import annotations

from typing import Any, Iterable

from score import format_price_cny, parse_number, score_row
from trend_analyzer import MONITORED_KEYWORDS

TREND_WORDS = MONITORED_KEYWORDS


def analyze_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    analyzed = []
    for original in rows:
        row = dict(original)
        if row.get("price"):
            row["price"] = format_price_cny(row["price"])
        row["hot_score"], row["reason"] = score_row(row)
        analyzed.append(row)
    return analyzed
