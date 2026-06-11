from main import merge_history


def test_merge_history_deduplicates_same_daily_platform_url():
    old = [{"date": "2026-06-11", "source": "amazon_us", "product_url": "https://a/1", "title": "Old"}]
    new = [{"date": "2026-06-11", "source": "amazon_us", "product_url": "https://a/1", "title": "New"}]
    merged = merge_history(old, new)
    assert len(merged) == 1
    assert merged[0]["title"] == "New"
