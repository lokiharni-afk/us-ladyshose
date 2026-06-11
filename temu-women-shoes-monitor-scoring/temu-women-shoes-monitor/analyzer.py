"""Apply the scoring model to collected rows."""

from __future__ import annotations

from typing import Any, Iterable

from score import parse_number, score_row

TREND_WORDS = ("platform", "cloud", "recovery", "orthopedic", "comfort", "arch support", "soft", "summer", "beach", "wedge", "slides")


def analyze_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    analyzed = []
    for original in rows:
        row = dict(original)
        row["hot_score"], row["reason"] = score_row(row)
        analyzed.append(row)
    return analyzed
