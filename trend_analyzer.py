"""Analyze keyword frequency trends from daily history snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

MONITORED_KEYWORDS = (
    "recovery",
    "orthopedic",
    "arch support",
    "cloud",
    "platform",
    "comfort",
    "soft",
    "beach",
    "summer",
    "slides",
    "wedge",
    "flip flops",
    "sandals",
)

ACTION_BY_STATUS = {
    "快速上升": "优先跟踪，可作为明日重点选品方向。",
    "小幅上升": "继续观察，适合寻找低价差异化款。",
    "稳定": "可作为常规上架方向。",
    "下降": "暂缓跟款。",
}


def _trend_status(today_count: int, average_7d: float) -> str:
    if average_7d == 0:
        return "快速上升" if today_count > 0 else "稳定"
    if today_count > average_7d * 1.5:
        return "快速上升"
    if today_count > average_7d * 1.1:
        return "小幅上升"
    if today_count >= average_7d * 0.8:
        return "稳定"
    return "下降"


def analyze_keyword_trends(
    rows: Iterable[dict[str, Any]],
    run_date: str,
    snapshot_dates: Iterable[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    daily_counts: dict[str, Counter[str]] = defaultdict(Counter)
    dates = {str(day) for day in (snapshot_dates or []) if str(day) <= run_date}
    for row in rows:
        row_date = str(row.get("date") or "")
        if not row_date or row_date > run_date:
            continue
        dates.add(row_date)
        title = str(row.get("title") or "").lower()
        for keyword in MONITORED_KEYWORDS:
            if keyword in title:
                daily_counts[row_date][keyword] += 1

    ordered_dates = sorted(dates)
    recent_3 = ordered_dates[-3:]
    recent_7 = ordered_dates[-7:]
    recent_30 = ordered_dates[-30:]
    trend_rows = []
    for keyword in MONITORED_KEYWORDS:
        today_count = daily_counts[run_date][keyword]
        average_3d = round(sum(daily_counts[day][keyword] for day in recent_3) / len(recent_3), 2) if recent_3 else 0.0
        average_7d = round(sum(daily_counts[day][keyword] for day in recent_7) / len(recent_7), 2) if recent_7 else 0.0
        average_30d = round(sum(daily_counts[day][keyword] for day in recent_30) / len(recent_30), 2) if recent_30 else 0.0
        status = _trend_status(today_count, average_7d)
        trend_rows.append({
            "keyword": keyword,
            "today_count": today_count,
            "average_3d": average_3d,
            "average_7d": average_7d,
            "average_30d": average_30d,
            "trend_status": status,
            "action": ACTION_BY_STATUS[status],
        })

    metadata = {
        "history_days": len(ordered_dates),
        "insufficient_history": len(ordered_dates) < 7,
    }
    return trend_rows, metadata


def analyze_trends_from_history(
    history_dir: str | Path,
    run_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    snapshot_dates: list[str] = []
    directory = Path(history_dir)
    if directory.exists():
        for csv_path in sorted(directory.glob("*.csv")):
            if csv_path.stem > run_date or csv_path.stat().st_size == 0:
                continue
            snapshot_dates.append(csv_path.stem)
            frame = pd.read_csv(csv_path).where(pd.notna, None)
            rows.extend(frame.to_dict("records"))
    return analyze_keyword_trends(rows, run_date, snapshot_dates)
