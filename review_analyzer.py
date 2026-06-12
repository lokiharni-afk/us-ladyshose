"""Extract product-selection insights from Amazon review text."""

from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Any, Iterable

POSITIVE_TERMS = {
    "comfortable": "舒适",
    "comfort": "舒适",
    "soft": "软底",
    "lightweight": "轻便",
    "arch support": "足弓支撑",
    "good quality": "质量好",
    "cute": "可爱",
    "stylish": "时尚",
    "true to size": "尺码标准",
    "non slip": "防滑",
    "good for walking": "适合长时间走路",
    "walking": "适合走路",
    "plantar fasciitis": "适合足底筋膜炎恢复",
}
NEGATIVE_TERMS = {
    "runs small": "尺码偏小",
    "narrow fit": "鞋型偏窄",
    "size too small": "尺码偏小",
    "too small": "尺码偏小",
    "size too large": "尺码偏大",
    "too large": "尺码偏大",
    "uncomfortable": "不舒适",
    "poor quality": "做工差",
    "smell": "有异味",
    "slippery": "不防滑",
    "narrow": "鞋型偏窄",
    "hard sole": "鞋底硬",
    "broke": "易断",
    "not durable": "不耐穿",
}
SIZING_TERMS = {
    "runs small": "偏小",
    "narrow fit": "窄脚",
    "size too small": "偏小",
    "too small": "偏小",
    "size too large": "偏大",
    "too large": "偏大",
    "narrow": "窄脚",
    "wide": "宽脚",
    "true to size": "true to size",
}
QUALITY_TERMS = {
    "broke": "易断",
    "smell": "异味",
    "hard sole": "鞋底硬",
    "not durable": "不耐穿",
    "poor quality": "做工差",
}
USAGE_TERMS = (
    "walking", "beach", "pool", "shower", "vacation", "travel",
    "home", "work", "plantar fasciitis", "recovery",
)
TEMU_OPPORTUNITY_TERMS = ("cloud", "recovery", "orthopedic", "arch support")


def _matched_counts(text: str, terms: dict[str, str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for phrase, label in terms.items():
        matches = re.findall(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text)
        if matches:
            counts[label] += len(matches)
    return counts


def _summary(counts: Counter[str], fallback: str) -> str:
    return "、".join(label for label, _ in counts.most_common(5)) or fallback


def analyze_reviews(reviews: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for review in reviews:
        grouped[str(review.get("product_title") or "unknown")].append(dict(review))

    insights: dict[str, dict[str, Any]] = {}
    for key, product_reviews in grouped.items():
        positive_counts: Counter[str] = Counter()
        negative_counts: Counter[str] = Counter()
        sizing_counts: Counter[str] = Counter()
        quality_counts: Counter[str] = Counter()
        usage_counts: Counter[str] = Counter()
        keyword_counts: Counter[str] = Counter()
        temu_counts: Counter[str] = Counter()
        positive_keyword_counts: Counter[str] = Counter()
        negative_keyword_counts: Counter[str] = Counter()
        for review in product_reviews:
            text = str(review.get("review_text") or "").lower()
            positive_counts.update(_matched_counts(text, POSITIVE_TERMS))
            negative_counts.update(_matched_counts(text, NEGATIVE_TERMS))
            sizing_counts.update(_matched_counts(text, SIZING_TERMS))
            quality_counts.update(_matched_counts(text, QUALITY_TERMS))
            usage_counts.update(term for term in USAGE_TERMS if term in text)
            keyword_counts.update(
                phrase for phrase in (*POSITIVE_TERMS, *NEGATIVE_TERMS, *USAGE_TERMS)
                if phrase in text
            )
            positive_keyword_counts.update(phrase for phrase in POSITIVE_TERMS if phrase in text)
            negative_keyword_counts.update(phrase for phrase in NEGATIVE_TERMS if phrase in text)
            temu_counts.update(term for term in TEMU_OPPORTUNITY_TERMS if term in text)

        positives = _summary(positive_counts, "暂无明确正面高频词")
        negatives = _summary(negative_counts, "暂无明显集中差评")
        sizing = _summary(sizing_counts, "暂无明确尺码反馈")
        quality = _summary(quality_counts, "暂无明显材质或质量风险")
        usage = _summary(usage_counts, "暂无明确使用场景")
        insights[key] = {
            "product_title": product_reviews[0].get("product_title") or "无标题",
            "positive_summary": positives,
            "negative_summary": negatives,
            "sizing_insight": sizing,
            "quality_risk": quality,
            "usage_scenario": usage,
            "product_improvement_suggestion": f"保留{positives}卖点，并重点改善{negatives}。",
            "temu_listing_suggestion": (
                f"标题突出{positives}；主图展示核心舒适卖点；详情页解释{quality}；"
                f"尺码表提醒{sizing}；避免{negatives}相关差评。"
            ),
            "positive_signal_count": sum(positive_counts.values()),
            "negative_signal_count": sum(negative_counts.values()),
            "review_count": len(product_reviews),
            "positive_keywords": [item for item, _ in positive_keyword_counts.most_common(8)],
            "negative_keywords": [item for item, _ in negative_keyword_counts.most_common(8)],
            "frequent_review_keywords": [item for item, _ in keyword_counts.most_common(10)],
            "temu_opportunity_keywords": [item for item, _ in temu_counts.most_common(8)],
        }
    return insights
