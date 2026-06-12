from main import merge_history, write_daily_snapshot


def test_merge_history_deduplicates_same_daily_platform_url():
    old = [{"date": "2026-06-11", "source": "amazon_us", "product_url": "https://a/1", "title": "Old"}]
    new = [{"date": "2026-06-11", "source": "amazon_us", "product_url": "https://a/1", "title": "New"}]
    merged = merge_history(old, new)
    assert len(merged) == 1
    assert merged[0]["title"] == "New"


def test_write_daily_snapshot_writes_latest_and_dated_history(tmp_path):
    rows = [{"date": "2026-06-12", "source": "amazon_us", "title": "Cloud Slides"}]

    latest, snapshot = write_daily_snapshot(tmp_path, "2026-06-12", rows)

    assert latest == tmp_path / "raw_data.csv"
    assert snapshot == tmp_path / "history" / "2026-06-12.csv"
    assert latest.exists()
    assert snapshot.exists()
