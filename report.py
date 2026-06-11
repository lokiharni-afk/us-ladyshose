"""Generate the daily Chinese Markdown report."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from analyzer import TREND_WORDS


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


def build_report(run_date: str, rows: list[dict[str, Any]], warnings: list[str] | None = None) -> str:
    warnings = warnings or []
    amazon = [row for row in rows if row.get("source") == "amazon_us"]
    tiktok = [row for row in rows if row.get("source") == "tiktok"]
    temu = [row for row in rows if row.get("source") == "temu_us"]
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 未发现抓取任务级异常；平台数据仍需人工复核。"
    return f"""# 美国女鞋爆款日报 - {run_date}

## 今日美国女鞋趋势

{_trends(rows)}

## TikTok 热度款

{_table(tiktok)}
## Amazon 验证款

{_table(amazon)}
## Temu 低价跟款机会

{_table(temu)}
## Top 20 建议跟款商品

各平台记录独立评分，不进行跨平台商品关联。

{_table(rows, 20)}
## 风险提醒

{warning_text}
- 排名、互动量和价格可能因地区、登录状态及页面实验而变化。
- 本报告用于选品初筛，不代表销量、利润或知识产权安全结论。
"""

