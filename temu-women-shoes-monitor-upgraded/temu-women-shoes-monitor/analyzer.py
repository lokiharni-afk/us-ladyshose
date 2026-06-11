"""Normalize collected rows and calculate platform-specific hot scores."""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Iterable

TREND_WORDS = ("platform", "cloud", "comfort", "soft", "summer", "beach", "wedge", "slides")


def parse_number(value: Any) -> float | int | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().upper().replace(",", "")
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*([KMB]?)", text)
    if not match:
        return None
    number = float(match.group(1))
    number *= {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[match.group(2)]
    return int(number) if number.is_integer() else number


def _trend_matches(title: str) -> list[str]:
    lower = title.lower()
    return [word for word in TREND_WORDS if word in lower]


def _rank_points(rank: Any, maximum: float = 35) -> float:
    parsed = parse_number(rank)
    if not parsed or parsed <= 0:
        return 0
    return max(0, maximum * (1 - (min(float(parsed), 100) - 1) / 100))


def _freshness_points(published_at: Any, run_date: str) -> float:
    if not published_at:
        return 0
    try:
        published = datetime.fromisoformat(str(published_at).replace("Z", "+00:00")).date()
        current = date.fromisoformat(run_date)
    except ValueError:
        return 0
    days = max(0, (current - published).days)
    return 15 if days <= 2 else 10 if days <= 7 else 5 if days <= 30 else 0


def _score_amazon(row: dict[str, Any]) -> tuple[float, list[str]]:
    score, reasons = _rank_points(row.get("rank")), []
    if score:
        reasons.append("Amazon 排名靠前")
    list_type = str(row.get("list_type", "")).lower()
    if list_type == "movers_and_shakers":
        score += 35
        reasons.append("入选 Movers & Shakers")
    elif list_type == "best_sellers":
        score += 20
        reasons.append("入选 Best Sellers")
    elif list_type == "new_releases":
        score += 15
        reasons.append("入选 New Releases")
    reviews = parse_number(row.get("review_count")) or 0
    if reviews:
        score += min(20, math.log10(float(reviews) + 1) * 5)
        reasons.append("评论基础较强")
    rating = parse_number(row.get("rating")) or 0
    if rating >= 4.5:
        score += 10
        reasons.append("评分高于 4.5")
    return score, reasons


def _score_tiktok(row: dict[str, Any]) -> tuple[float, list[str]]:
    likes = float(parse_number(row.get("likes")) or 0)
    comments = float(parse_number(row.get("comments")) or 0)
    views = float(parse_number(row.get("views")) or 0)
    score = min(30, math.log10(likes + 1) * 6)
    score += min(20, math.log10(comments + 1) * 5)
    score += min(25, math.log10(views + 1) * 4)
    freshness = _freshness_points(row.get("published_at"), str(row.get("date", "")))
    score += freshness
    reasons = []
    if likes or comments or views:
        reasons.append("TikTok 互动热度高")
    if freshness:
        reasons.append("近期发布")
    return score, reasons


def _score_temu(row: dict[str, Any]) -> tuple[float, list[str]]:
    score, reasons = _rank_points(row.get("rank"), 30), []
    if score:
        reasons.append("Temu 排名靠前")
    price = parse_number(row.get("price"))
    if price is not None and float(price) < 10:
        score += 25
        reasons.append("低价验证机会")
    elif price is not None and float(price) <= 20:
        score += 15
        reasons.append("价格有竞争力")
    competition = parse_number(row.get("competition_count"))
    if competition is not None and competition <= 50:
        score += 20
        reasons.append("同类竞争较少")
    return score, reasons


def analyze_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    analyzed = []
    for original in rows:
        row = dict(original)
        source = str(row.get("source", "")).lower()
        if source == "amazon_us":
            score, reasons = _score_amazon(row)
        elif source == "tiktok_us":
            score, reasons = _score_tiktok(row)
        elif source == "temu_us":
            score, reasons = _score_temu(row)
        else:
            score, reasons = 0.0, []
        matches = _trend_matches(str(row.get("title", "")))
        if matches:
            score += min(20, len(matches) * 4)
            reasons.append("趋势词：" + "、".join(matches))
        row["hot_score"] = round(score, 2)
        row["reason"] = "；".join(reasons) if reasons else "暂未发现明显爆款信号"
        analyzed.append(row)
    return analyzed
