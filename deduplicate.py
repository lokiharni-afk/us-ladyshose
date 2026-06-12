"""Remove likely duplicate products while keeping the highest-scoring record."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Iterable

from score import extract_brand, parse_number


def normalize_title(title: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(title or "").lower()))


def title_similarity(first: Any, second: Any) -> float:
    return SequenceMatcher(None, normalize_title(first), normalize_title(second)).ratio()


def _price_difference_within_20_percent(first: Any, second: Any) -> bool:
    first_price = parse_number(first)
    second_price = parse_number(second)
    if first_price is None or second_price is None:
        return False
    maximum = max(abs(float(first_price)), abs(float(second_price)))
    if maximum == 0:
        return True
    return abs(float(first_price) - float(second_price)) / maximum <= 0.20


def is_duplicate(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_date = str(first.get("date") or "")
    second_date = str(second.get("date") or "")
    if first_date and second_date and first_date != second_date:
        return False
    first_brand = extract_brand(first.get("title"))
    second_brand = extract_brand(second.get("title"))
    return (
        bool(first_brand)
        and first_brand == second_brand
        and title_similarity(first.get("title"), second.get("title")) > 0.85
        and _price_difference_within_20_percent(first.get("price"), second.get("price"))
    )


def deduplicate_rows(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    original = [dict(row) for row in rows]
    ranked = sorted(original, key=lambda row: float(parse_number(row.get("hot_score")) or 0), reverse=True)
    kept: list[dict[str, Any]] = []
    for row in ranked:
        if not any(is_duplicate(row, existing) for existing in kept):
            kept.append(row)
    stats = {
        "original_count": len(original),
        "deduplicated_count": len(kept),
        "removed_count": len(original) - len(kept),
    }
    return kept, stats
