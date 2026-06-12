from deduplicate import deduplicate_rows, is_duplicate


def test_same_product_requires_similar_title_same_brand_and_close_price():
    first = {
        "title": "CloudStep Women's Recovery Cloud Slides",
        "price": "$19.99",
        "hot_score": 82,
    }
    duplicate = {
        "title": "CloudStep Womens Recovery Cloud Slides",
        "price": "$21.99",
        "hot_score": 91,
    }
    different_brand = {
        "title": "OtherBrand Womens Recovery Cloud Slides",
        "price": "$21.99",
        "hot_score": 95,
    }
    expensive = {
        "title": "CloudStep Womens Recovery Cloud Slides",
        "price": "$30.00",
        "hot_score": 95,
    }

    assert is_duplicate(first, duplicate)
    assert not is_duplicate(first, different_brand)
    assert not is_duplicate(first, expensive)


def test_deduplicate_keeps_highest_score_and_returns_stats():
    rows = [
        {"title": "CloudStep Women's Recovery Cloud Slides", "price": "$19.99", "hot_score": 82},
        {"title": "CloudStep Womens Recovery Cloud Slides", "price": "$21.99", "hot_score": 91},
        {"title": "OtherBrand Platform Sandals", "price": "$25.00", "hot_score": 75},
    ]

    result, stats = deduplicate_rows(rows)

    assert len(result) == 2
    assert result[0]["hot_score"] == 91
    assert stats == {"original_count": 3, "deduplicated_count": 2, "removed_count": 1}


def test_deduplicate_preserves_same_product_history_from_different_dates():
    first = {
        "date": "2026-06-11",
        "title": "CloudStep Women's Recovery Cloud Slides",
        "price": "$19.99",
        "hot_score": 82,
    }
    next_day = {
        "date": "2026-06-12",
        "title": "CloudStep Womens Recovery Cloud Slides",
        "price": "$21.99",
        "hot_score": 91,
    }

    result, stats = deduplicate_rows([first, next_day])

    assert len(result) == 2
    assert stats["removed_count"] == 0
