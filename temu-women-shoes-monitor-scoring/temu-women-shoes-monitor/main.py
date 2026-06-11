"""Run collectors, analyze rows, persist history, and write the daily report."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from analyzer import analyze_rows
from report import build_report
from scraper import collect_all

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "raw_data.csv"
REPORTS_DIR = ROOT / "reports"

COLUMNS = [
    "date", "source", "data_type", "list_type", "keyword", "rank", "title",
    "price", "rating", "review_count", "likes", "comments", "views",
    "published_at", "competition_count", "product_url", "image_url",
    "hot_score", "reason",
]


def merge_history(old_rows: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in old_rows + new_rows:
        url = str(row.get("product_url") or row.get("video_url") or "")
        fallback = f"{row.get('list_type', '')}:{row.get('keyword', '')}:{row.get('rank', '')}:{row.get('title', '')}"
        key = (str(row.get("date", "")), str(row.get("source", "")), url or fallback)
        merged[key] = row
    return list(merged.values())


def _read_history() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        return []
    return pd.read_csv(DATA_PATH).where(pd.notna, None).to_dict("records")


def _write_history(rows: list[dict[str, Any]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    for column in COLUMNS:
        if column not in frame:
            frame[column] = None
    frame[COLUMNS].to_csv(DATA_PATH, index=False, encoding="utf-8-sig")


async def run() -> None:
    run_date = os.getenv("RUN_DATE") or datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    rows, warnings = await collect_all(run_date)
    analyzed = analyze_rows(rows)
    history = analyze_rows(merge_history(_read_history(), rows))
    _write_history(history)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"{run_date}.md").write_text(build_report(run_date, analyzed, warnings), encoding="utf-8")
    amazon_count = sum(row.get("source") == "amazon_us" for row in analyzed)
    tiktok_count = sum(row.get("source") == "tiktok_us" for row in analyzed)
    print(f"Collected Amazon: {amazon_count}, TikTok: {tiktok_count}, total: {len(analyzed)}")
    print(f"Wrote {DATA_PATH} and reports/{run_date}.md")


if __name__ == "__main__":
    asyncio.run(run())
