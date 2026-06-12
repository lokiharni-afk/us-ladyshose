"""Generate the daily Chinese Markdown report."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from analyzer import TREND_WORDS
from deduplicate import deduplicate_rows
from score import hot_level, opportunity_level, parse_number

FOLLOW_DIRECTIONS = [
    ("Recovery Slides 恢复拖鞋", ("recovery",), "recovery slides"),
    ("Orthopedic Sandals 足弓支撑凉鞋", ("orthopedic", "arch support"), "orthopedic sandals"),
    ("Cloud Slides 云朵拖鞋", ("cloud", "cloud slides"), "cloud slides"),
    ("Platform Sandals 厚底凉鞋", ("platform",), "platform sandals"),
    ("Beach Sandals 沙滩凉鞋", ("beach", "flip flops"), "beach sandals"),
]

BRAND_WORDS = ("Crocs", "OOFOS", "Skechers", "Clarks", "REEF", "Amazon Essentials")
TEMU_PRIORITY_WORDS = ("recovery", "orthopedic", "arch support", "cloud")
TEMU_SEARCH_PATTERNS = [
    (("orthopedic", "arch support"), "orthopedic arch support sandals"),
    (("recovery",), "recovery slides"),
    (("cloud",), "cloud slides"),
    (("platform",), "platform sandals"),
    (("beach",), "beach sandals"),
    (("flip flops",), "women flip flops"),
]


def _table(rows: list[dict[str, Any]], limit: int = 10) -> str:
    if not rows:
        return "暂无可用数据。\n"
    lines = ["| 排名 | 平台 | 标题 | 爆款分 | 理由 |", "|---:|---|---|---:|---|"]
    for index, row in enumerate(sorted(rows, key=lambda x: float(x.get("hot_score") or 0), reverse=True)[:limit], 1):
        title = str(row.get("title") or "无标题").replace("|", " ")
        url = row.get("product_url") or row.get("video_url") or ""
        title_cell = f"[{title}]({url})" if url else title
        reason = str(row.get("reason") or "").replace("|", " ")
        lines.append(f"| {index} | {row.get('source', '')} | {title_cell} | {row.get('hot_score', 0)} | {reason} |")
    return "\n".join(lines) + "\n"


def _trends(rows: Iterable[dict[str, Any]]) -> str:
    counts: Counter[str] = Counter()
    for row in rows:
        title = str(row.get("title", "")).lower()
        counts.update(word for word in TREND_WORDS if word in title)
    if not counts:
        return "今日有效数据不足，暂无法判断稳定趋势。"
    return "高频趋势词：" + "、".join(f"**{word}**（{count}）" for word, count in counts.most_common(6)) + "。"


def _opportunity_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "暂无可用数据。\n"
    lines = [
        "| 排名 | 来源 | 标题 | 价格 | 爆款分 | 爆款等级 | 机会等级 | 爆款原因 | 链接 |",
        "|---:|---|---|---:|---:|---|---|---|---|",
    ]
    ranked = sorted(rows, key=lambda row: float(row.get("hot_score") or 0), reverse=True)[:20]
    for index, row in enumerate(ranked, 1):
        title = str(row.get("title") or "无标题").replace("|", " ")
        price = str(row.get("price") or "-").replace("|", " ")
        score = row.get("hot_score") or 0
        reason = str(row.get("reason") or "").replace("|", " ")
        url = str(row.get("product_url") or row.get("video_url") or "")
        link = f"[查看]({url})" if url else "-"
        lines.append(
            f"| {index} | {row.get('source', '')} | {title} | {price} | {score} | "
            f"{hot_level(score)} | {opportunity_level(score)} | {reason} | {link} |"
        )
    return "\n".join(lines) + "\n"


def _top_rows(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: float(row.get("hot_score") or 0), reverse=True)[:limit]


def _temu_price_range(price: Any) -> str:
    value = parse_number(price)
    if value is None:
        return "价格缺失，需人工判断"
    if value > 30:
        return "9.99-19.99美元"
    if value >= 15:
        return "7.99-14.99美元"
    return "谨慎跟款"


def _direction_price_range(matches: list[dict[str, Any]]) -> str:
    prices = [
        float(value)
        for row in matches
        if row.get("source") == "amazon_us"
        if (value := parse_number(row.get("price"))) is not None
    ]
    if not prices:
        return "9.99-19.99美元（待价格验证）"
    return _temu_price_range(sum(prices) / len(prices))


def _direction_risk(matches: list[dict[str, Any]]) -> str:
    titles = " ".join(str(row.get("title") or "").lower() for row in matches)
    if any(brand.lower() in titles for brand in BRAND_WORDS):
        return "高"
    if not matches:
        return "高"
    top_score = max(float(row.get("hot_score") or 0) for row in matches)
    return "低" if top_score >= 85 else "中" if top_score >= 70 else "高"


def _follow_directions(rows: list[dict[str, Any]]) -> str:
    top_rows = _top_rows(rows)
    directions = []
    for name, keywords, english_keyword in FOLLOW_DIRECTIONS:
        matches = [
            row for row in top_rows
            if any(keyword in str(row.get("title") or "").lower() for keyword in keywords)
        ]
        top_score = max((float(row.get("hot_score") or 0) for row in matches), default=0)
        sources = len({str(row.get("source") or "") for row in matches})
        if matches:
            reason = f"Top20中出现{len(matches)}条，最高爆款分{top_score:g}，覆盖{sources}个平台"
        else:
            reason = "当前Top20信号较弱，作为美国女鞋常青方向持续观察"
        directions.append((
            len(matches),
            sum(float(row.get("hot_score") or 0) for row in matches),
            name,
            english_keyword,
            reason,
            _direction_price_range(matches),
            _direction_risk(matches),
        ))
    directions.sort(key=lambda item: (item[0], item[1]), reverse=True)
    lines = [
        "| 方向名称 | 英文关键词 | 推荐原因 | 建议售价区间 | 风险等级 |",
        "|---|---|---|---|---|",
    ]
    for _, _, name, keyword, reason, price_range, risk in directions:
        lines.append(f"| {name} | `{keyword}` | {reason} | {price_range} | {risk} |")
    return "\n".join(lines) + "\n"


def _temu_opportunity_table(rows: list[dict[str, Any]]) -> str:
    amazon_rows = [row for row in _top_rows(rows) if row.get("source") == "amazon_us"]
    if not amazon_rows:
        return "Top20 中暂无 Amazon 商品，今日无法判断 Temu 跟款机会。\n"
    lines = [
        "| Amazon 商品 | Amazon价格 | 品牌词 | Temu机会 | 推荐Temu售价 |",
        "|---|---:|---|---|---|",
    ]
    for row in amazon_rows:
        title = str(row.get("title") or "无标题").replace("|", " ")
        title_lower = title.lower()
        brand = next((brand for brand in BRAND_WORDS if brand.lower() in title_lower), None)
        price = str(row.get("price") or "-").replace("|", " ")
        opportunity = "不建议" if brand else "高"
        recommended_price = "不适用" if brand else _temu_price_range(row.get("price"))
        lines.append(f"| {title} | {price} | {brand or '-'} | {opportunity} | {recommended_price} |")
    return "\n".join(lines) + "\n"


def _temu_follow_price_range(price: Any) -> str:
    value = parse_number(price)
    if value is None:
        return "价格缺失，需人工判断"
    if value > 30:
        return "9.99-19.99美元"
    if value >= 15:
        return "7.99-14.99美元"
    return "6.99-12.99美元"


def _temu_search_keyword(title: Any) -> str:
    text = str(title or "").lower()
    for required_words, keyword in TEMU_SEARCH_PATTERNS:
        if all(word in text for word in required_words):
            return keyword
    words = [word for word in text.split() if word.isalpha()][:4]
    return " ".join(words) or "women sandals"


def _temu_follow_list(rows: list[dict[str, Any]]) -> str:
    amazon_rows = [row for row in _top_rows(rows) if row.get("source") == "amazon_us"]
    if not amazon_rows:
        return "Top20 中暂无 Amazon 商品，今日无法生成 Temu 跟款清单。\n"

    keywords = [_temu_search_keyword(row.get("title")) for row in amazon_rows]
    competition_counts = Counter(keywords)
    lines = [
        "| 关键词 | Amazon价格 | 建议Temu售价 | 竞争等级 | 跟款优先级 | 原因 |",
        "|---|---:|---|---|---|---|",
    ]
    for row, keyword in zip(amazon_rows, keywords):
        title = str(row.get("title") or "")
        title_lower = title.lower()
        brand = next((brand for brand in BRAND_WORDS if brand.lower() in title_lower), None)
        priority_matches = [word for word in TEMU_PRIORITY_WORDS if word in title_lower]
        count = competition_counts[keyword]
        competition = "高" if count >= 5 else "中" if count >= 2 else "低"
        if brand:
            priority = "低"
            reason = f"包含品牌词 {brand}，跟款优先级低"
        elif priority_matches:
            priority = "高"
            reason = f"标题包含高机会词 {'、'.join(priority_matches)}"
        else:
            priority = "中"
            reason = "未命中品牌词或高机会词，建议常规观察"
        price = str(row.get("price") or "-").replace("|", " ")
        lines.append(
            f"| {keyword} | {price} | {_temu_follow_price_range(row.get('price'))} | "
            f"{competition} | {priority} | {reason} |"
        )
    return "\n".join(lines) + "\n"


def _level_summary(rows: list[dict[str, Any]]) -> str:
    counts = Counter(hot_level(row.get("hot_score")) for row in rows)
    return f"- S级爆款：{counts['S级爆款']} 条\n- A级爆款：{counts['A级爆款']} 条"


def _deduplication_summary(stats: dict[str, int]) -> str:
    return (
        f"- 本次去重数量：{stats['removed_count']}\n"
        f"- 原始记录：{stats['original_count']}\n"
        f"- 去重后记录：{stats['deduplicated_count']}"
    )


def _keyword_trend_radar(
    trend_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> str:
    warning = "历史数据不足7天，趋势判断仅供参考。\n\n" if metadata.get("insufficient_history") else ""
    if not trend_rows:
        return warning + "暂无关键词历史趋势数据。\n"
    lines = [
        "| 关键词 | 今日出现次数 | 近3日均值 | 近7日均值 | 趋势状态 | 操作建议 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in trend_rows:
        lines.append(
            f"| {row.get('keyword', '')} | {row.get('today_count', 0)} | "
            f"{row.get('average_3d', 0)} | {row.get('average_7d', 0)} | "
            f"{row.get('trend_status', '')} | {row.get('action', '')} |"
        )
    return warning + "\n".join(lines) + "\n"


def build_report(
    run_date: str,
    rows: list[dict[str, Any]],
    warnings: list[str] | None = None,
    dedup_stats: dict[str, int] | None = None,
    trend_rows: list[dict[str, Any]] | None = None,
    trend_metadata: dict[str, Any] | None = None,
) -> str:
    warnings = warnings or []
    trend_rows = trend_rows or []
    trend_metadata = trend_metadata or {"history_days": 0, "insufficient_history": True}
    rows, report_stats = deduplicate_rows(rows)
    dedup_stats = dedup_stats or report_stats
    amazon = [row for row in rows if row.get("source") == "amazon_us"]
    tiktok = [row for row in rows if row.get("source") == "tiktok_us"]
    temu = [row for row in rows if row.get("source") == "temu_us"]
    tiktok_section = _table(tiktok, 20) if tiktok else "TikTok 今日未采集到有效数据，可能原因：页面反爬、地区限制、选择器失效或需要登录。\n"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 未发现抓取任务级异常；平台数据仍需人工复核。"
    return f"""# 美国女鞋爆款日报 - {run_date}

## 今日美国女鞋趋势

{_trends(rows)}

## 爆款等级统计

{_level_summary(rows)}

## 去重统计

{_deduplication_summary(dedup_stats)}

## 关键词趋势雷达

{_keyword_trend_radar(trend_rows, trend_metadata)}

## TikTok 热度趋势

{tiktok_section}
## Amazon 验证款

{_table(amazon)}
## Temu 低价跟款机会

{_table(temu)}
## Top 20 爆款机会榜

各平台记录独立评分，不进行跨平台商品关联。

{_opportunity_table(rows)}
## 今日建议跟款方向

{_follow_directions(rows)}

## Temu 跟款机会判断

{_temu_opportunity_table(rows)}

## Temu跟款清单

{_temu_follow_list(rows)}

## 风险提醒

{warning_text}
- 排名、互动量和价格可能因地区、登录状态及页面实验而变化。
- 本报告用于选品初筛，不代表销量、利润或知识产权安全结论。
"""
