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
from deduplicate import deduplicate_rows
from review_analyzer import analyze_reviews
from review_scraper import collect_amazon_reviews
from report import build_report
from scraper import collect_all, select_top20_amazon
from trend_analyzer import analyze_trends_from_history

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_PATH = DATA_DIR / "raw_data.csv"
HISTORY_DIR = DATA_DIR / "history"
REPORTS_DIR = ROOT / "reports"
REVIEWS_PATH = DATA_DIR / "reviews.csv"

COLUMNS = [
    "date", "source", "data_type", "list_type", "keyword", "rank", "title",
    "price", "rating", "review_count", "likes", "comments", "views",
    "published_at", "competition_count", "product_url", "image_url",
    "hot_score", "reason",
]
REVIEW_COLUMNS = [
    "product_title", "review_text", "review_rating", "review_date",
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


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    for column in COLUMNS:
        if column not in frame:
            frame[column] = None
    frame[COLUMNS].to_csv(path, index=False, encoding="utf-8-sig")


def write_daily_snapshot(data_dir: Path, run_date: str, rows: list[dict[str, Any]]) -> tuple[Path, Path]:
    latest_path = data_dir / "raw_data.csv"
    snapshot_path = data_dir / "history" / f"{run_date}.csv"
    _write_csv(latest_path, rows)
    _write_csv(snapshot_path, rows)
    return latest_path, snapshot_path


def write_reviews(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    for column in REVIEW_COLUMNS:
        if column not in frame:
            frame[column] = None
    frame[REVIEW_COLUMNS].to_csv(path, index=False, encoding="utf-8-sig")
    return path


def _attach_review_signals(
    rows: list[dict[str, Any]],
    insight_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched = []
    for original in rows:
        row = dict(original)
        insight = insight_map.get(str(row.get("title") or ""))
        if insight:
            row["review_positive_count"] = insight.get("positive_signal_count", 0)
            row["review_negative_count"] = insight.get("negative_signal_count", 0)
        enriched.append(row)
    return enriched


async def run() -> None:
    run_date = os.getenv("RUN_DATE") or datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    rows, warnings = await collect_all(run_date)
    analyzed = analyze_rows(rows)
    initial_deduplicated, _ = deduplicate_rows(analyzed)
    review_products = select_top20_amazon(initial_deduplicated)
    reviews, review_warnings = await collect_amazon_reviews(
        review_products,
        headless=os.getenv("HEADLESS", "true").lower() != "false",
    )
    warnings.extend(review_warnings)
    review_insight_map = analyze_reviews(reviews)
    rescored = analyze_rows(_attach_review_signals(analyzed, review_insight_map))
    deduplicated, dedup_stats = deduplicate_rows(rescored)
    latest_path, snapshot_path = write_daily_snapshot(DATA_DIR, run_date, deduplicated)
    reviews_path = write_reviews(REVIEWS_PATH, reviews)
    trend_rows, trend_metadata = analyze_trends_from_history(HISTORY_DIR, run_date)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"{run_date}.md").write_text(
        build_report(
            run_date,
            deduplicated,
            warnings,
            dedup_stats,
            trend_rows,
            trend_metadata,
            list(review_insight_map.values()),
        ),
        encoding="utf-8",
    )
    amazon_count = sum(row.get("source") == "amazon_us" for row in deduplicated)
    tiktok_count = sum(row.get("source") == "tiktok_us" for row in deduplicated)
    print(f"Collected Amazon: {amazon_count}, TikTok: {tiktok_count}, total after deduplication: {len(deduplicated)}")
    print(f"Deduplicated {dedup_stats['removed_count']} of {dedup_stats['original_count']} records")
    print(f"Collected {len(reviews)} reviews for {len(review_products)} Amazon Top20 products")
    print(f"Wrote {latest_path}, {snapshot_path}, {reviews_path}, and reports/{run_date}.md")


if __name__ == "__main__":
    asyncio.run(run())
