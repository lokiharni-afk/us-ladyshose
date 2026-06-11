"""Deterministic hot-score models for collected marketplace and trend rows."""

from __future__ import annotations

import math
import re
from typing import Any

AMAZON_KEYWORDS = {
    "cloud": 8,
    "platform": 8,
    "recovery": 8,
    "orthopedic": 8,
    "comfort": 6,
    "arch support": 6,
    "soft": 3,
    "beach": 3,
    "summer": 3,
    "wedge": 3,
}

TIKTOK_KEYWORDS = {
    "cloud slides": 8,
    "platform sandals": 8,
    "recovery slides": 8,
    "orthopedic sandals": 8,
    "summer sandals": 5,
    "beach sandals": 5,
    "women sandals": 3,
}


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


def opportunity_level(score: Any) -> str:
    value = float(parse_number(score) or 0)
    if value >= 85:
        return "立即跟款"
    if value >= 70:
        return "重点观察"
    if value >= 55:
        return "普通观察"
    return "暂不跟款"


def hot_level(score: Any) -> str:
    value = float(parse_number(score) or 0)
    if value >= 90:
        return "S级爆款"
    if value >= 80:
        return "A级爆款"
    if value >= 70:
        return "B级爆款"
    if value >= 60:
        return "C级观察"
    return "忽略"


def _keyword_score(title: Any, weights: dict[str, int], maximum: int) -> tuple[int, list[str]]:
    text = str(title or "").lower()
    matches = [keyword for keyword in weights if keyword in text]
    return min(maximum, sum(weights[keyword] for keyword in matches)), matches


def score_amazon(row: dict[str, Any]) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []

    rank = parse_number(row.get("rank"))
    if rank is not None:
        if rank <= 10:
            score += 45
            reasons.append("排名靠前")
        elif rank <= 30:
            score += 35
            reasons.append("排名进入前30")
        elif rank <= 50:
            score += 20
            reasons.append("排名进入前50")
        else:
            score += 10
            reasons.append("已有榜单排名")

    reviews = parse_number(row.get("review_count"))
    if reviews is not None:
        if reviews >= 5000:
            score += 25
            reasons.append("评论数高")
        elif reviews >= 1000:
            score += 20
            reasons.append("评论数达到1000以上")
        elif reviews >= 300:
            score += 10
            reasons.append("评论数达到300以上")
        elif reviews >= 50:
            score += 5
            reasons.append("评论数达到50以上")

    price = parse_number(row.get("price"))
    if price is not None:
        if 8 <= price <= 25:
            score += 15
            reasons.append("价格处于8-25美元黄金区间")
        elif 25 < price <= 40:
            score += 10
            reasons.append("价格处于25-40美元区间")
        elif price < 8:
            score += 5
            reasons.append("价格低于8美元")
        else:
            score += 3
            reasons.append("价格高于40美元")

    keyword_points, matches = _keyword_score(row.get("title"), AMAZON_KEYWORDS, 20)
    score += keyword_points
    if matches:
        reasons.append(f"标题包含 {'、'.join(matches)}，符合美国女鞋舒适化趋势")

    title = str(row.get("title") or "").lower()
    combinations = [
        (("platform", "comfort"), 10, "platform + comfort组合趋势加分"),
        (("cloud", "slides"), 10, "cloud + slides组合趋势加分"),
        (("orthopedic", "arch support"), 15, "orthopedic + arch support组合趋势加分"),
    ]
    for required_words, bonus, reason in combinations:
        if all(word in title for word in required_words):
            score += bonus
            reasons.append(reason)

    rating = parse_number(row.get("rating"))
    if rating is not None:
        if rating >= 4.6:
            score += 10
            reasons.append("评分达到4.6以上")
        elif rating >= 4.3:
            score += 7
            reasons.append("评分达到4.3以上")
        elif rating >= 4.0:
            score += 4
            reasons.append("评分达到4.0以上")

    return min(100, score), _reason(reasons)


def score_tiktok(row: dict[str, Any]) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []

    views = parse_number(row.get("views"))
    if views is not None:
        if views >= 1_000_000:
            score += 35
            reasons.append("播放量达到100万以上")
        elif views >= 300_000:
            score += 25
            reasons.append("播放量达到30万以上")
        elif views >= 100_000:
            score += 18
            reasons.append("播放量达到10万以上")
        elif views >= 10_000:
            score += 8
            reasons.append("播放量达到1万以上")

    likes = parse_number(row.get("likes"))
    if likes is not None:
        if likes >= 50_000:
            score += 25
            reasons.append("点赞数达到5万以上")
        elif likes >= 10_000:
            score += 18
            reasons.append("点赞数达到1万以上")
        elif likes >= 3_000:
            score += 10
            reasons.append("点赞数达到3000以上")
        elif likes >= 500:
            score += 5
            reasons.append("点赞数达到500以上")

    comments = parse_number(row.get("comments"))
    if comments is not None:
        if comments >= 1000:
            score += 15
            reasons.append("评论数达到1000以上")
        elif comments >= 300:
            score += 10
            reasons.append("评论数达到300以上")
        elif comments >= 50:
            score += 5
            reasons.append("评论数达到50以上")

    keyword_points, matches = _keyword_score(row.get("title"), TIKTOK_KEYWORDS, 25)
    score += keyword_points
    if matches:
        reasons.append(f"标题包含 {'、'.join(matches)}，符合TikTok女鞋趋势")

    return min(100, score), _reason(reasons)


def score_temu(row: dict[str, Any]) -> tuple[int, str]:
    """Keep Temu's existing role as a lightweight price/competition validator."""
    score = 0
    reasons: list[str] = []
    rank = parse_number(row.get("rank"))
    if rank is not None and rank <= 50:
        score += 30 if rank <= 10 else 20
        reasons.append("Temu 排名靠前")
    price = parse_number(row.get("price"))
    if price is not None and price < 10:
        score += 25
        reasons.append("低价验证机会")
    elif price is not None and price <= 20:
        score += 15
        reasons.append("价格有竞争力")
    competition = parse_number(row.get("competition_count"))
    if competition is not None and competition <= 50:
        score += 20
        reasons.append("同类竞争较少")
    return min(100, score), _reason(reasons)


def score_row(row: dict[str, Any]) -> tuple[int, str]:
    source = str(row.get("source") or "").lower()
    if source == "amazon_us":
        return score_amazon(row)
    if source == "tiktok_us":
        return score_tiktok(row)
    if source == "temu_us":
        return score_temu(row)
    return 0, _reason([])


def _reason(reasons: list[str]) -> str:
    return "；".join(reasons) + "。" if reasons else "数据不足，暂未发现明确爆款信号。"
