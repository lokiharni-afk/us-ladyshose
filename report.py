"""Generate the daily Chinese Markdown report."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from analyzer import TREND_WORDS
from score import hot_level, opportunity_level

FOLLOW_DIRECTIONS = [
    ("recovery", "Recovery Slides 恢复拖鞋"),
    ("cloud", "Cloud Slides 云朵拖鞋"),
    ("orthopedic", "Orthopedic Sandals 足弓支撑凉鞋"),
    ("platform", "Platform Sandals 厚底凉鞋"),
    ("beach", "Beach Flip Flops 沙滩人字拖"),
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


def _follow_directions(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "今日有效数据不足，暂无法形成跟款方向。"
    scored = []
    for keyword, label in FOLLOW_DIRECTIONS:
        matches = [row for row in rows if keyword in str(row.get("title") or "").lower()]
        signal = sum(float(row.get("hot_score") or 0) for row in matches)
        scored.append((len(matches), signal, label))
    ranked = sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)
    return "\n".join(f"{index}. {label}" for index, (_, _, label) in enumerate(ranked[:5], 1))


def _level_summary(rows: list[dict[str, Any]]) -> str:
    counts = Counter(hot_level(row.get("hot_score")) for row in rows)
    return f"- S级爆款：{counts['S级爆款']} 条\n- A级爆款：{counts['A级爆款']} 条"


def build_report(run_date: str, rows: list[dict[str, Any]], warnings: list[str] | None = None) -> str:
    warnings = warnings or []
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

## 风险提醒

{warning_text}
- 排名、互动量和价格可能因地区、登录状态及页面实验而变化。
- 本报告用于选品初筛，不代表销量、利润或知识产权安全结论。
"""
