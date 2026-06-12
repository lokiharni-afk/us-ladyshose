import pandas as pd

from trend_analyzer import analyze_keyword_trends, analyze_trends_from_history


def test_keyword_trends_calculate_daily_averages_and_statuses():
    rows = []
    daily_recovery = [2, 2, 2, 2, 2, 2, 8]
    for day, count in enumerate(daily_recovery, 1):
        rows.extend({"date": f"2026-06-{day:02d}", "title": "Recovery slides"} for _ in range(count))
        rows.append({"date": f"2026-06-{day:02d}", "title": "Cloud slides"})

    trends, metadata = analyze_keyword_trends(rows, "2026-06-07")
    recovery = next(row for row in trends if row["keyword"] == "recovery")
    cloud = next(row for row in trends if row["keyword"] == "cloud")

    assert recovery["today_count"] == 8
    assert recovery["average_3d"] == 4.0
    assert recovery["average_7d"] == 2.86
    assert recovery["average_30d"] == 2.86
    assert recovery["trend_status"] == "快速上升"
    assert recovery["action"] == "优先跟踪，可作为明日重点选品方向。"
    assert cloud["trend_status"] == "稳定"
    assert metadata["history_days"] == 7
    assert metadata["insufficient_history"] is False


def test_keyword_trends_handle_less_than_seven_days():
    trends, metadata = analyze_keyword_trends(
        [
            {"date": "2026-06-11", "title": "Platform comfort sandals"},
            {"date": "2026-06-12", "title": "Platform sandals"},
        ],
        "2026-06-12",
    )

    platform = next(row for row in trends if row["keyword"] == "platform")
    assert platform["today_count"] == 1
    assert metadata["history_days"] == 2
    assert metadata["insufficient_history"] is True


def test_trends_read_all_daily_snapshots_from_history_directory(tmp_path):
    history = tmp_path / "history"
    history.mkdir()
    for day in range(1, 4):
        pd.DataFrame([
            {"date": f"2026-06-{day:02d}", "title": "Cloud slides"},
        ]).to_csv(history / f"2026-06-{day:02d}.csv", index=False)

    trends, metadata = analyze_trends_from_history(history, "2026-06-03")
    cloud = next(row for row in trends if row["keyword"] == "cloud")

    assert cloud["average_30d"] == 1.0
    assert metadata["history_days"] == 3


def test_empty_snapshot_still_counts_as_history_day(tmp_path):
    history = tmp_path / "history"
    history.mkdir()
    pd.DataFrame([{"date": "2026-06-11", "title": "Cloud slides"}]).to_csv(
        history / "2026-06-11.csv", index=False
    )
    pd.DataFrame(columns=["date", "title"]).to_csv(history / "2026-06-12.csv", index=False)

    trends, metadata = analyze_trends_from_history(history, "2026-06-12")
    cloud = next(row for row in trends if row["keyword"] == "cloud")

    assert metadata["history_days"] == 2
    assert cloud["today_count"] == 0
    assert cloud["average_7d"] == 0.5
