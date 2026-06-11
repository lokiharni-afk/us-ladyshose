from analyzer import analyze_rows, parse_number


def test_parse_number_handles_social_suffixes_and_commas():
    assert parse_number("1.2K") == 1200
    assert parse_number("3.4M views") == 3_400_000
    assert parse_number("12,345 ratings") == 12345
    assert parse_number("") is None


def test_amazon_movers_and_shakers_scores_higher_than_regular_search():
    base = {
        "date": "2026-06-11",
        "source": "amazon_us",
        "data_type": "product",
        "title": "Soft platform summer slides",
        "rank": 3,
        "rating": 4.7,
        "review_count": 1200,
        "price": 19.99,
    }
    rows = analyze_rows(
        [
            {**base, "list_type": "search"},
            {**base, "list_type": "movers_and_shakers"},
        ]
    )
    assert rows[1]["hot_score"] > rows[0]["hot_score"]
    assert "Movers & Shakers" in rows[1]["reason"]


def test_tiktok_recent_engagement_and_temu_low_competition_are_scored():
    rows = analyze_rows(
        [
            {
                "date": "2026-06-11",
                "source": "tiktok",
                "data_type": "video",
                "title": "Cloud slides for summer",
                "likes": "25K",
                "comments": "1.2K",
                "views": "500K",
                "published_at": "2026-06-10",
            },
            {
                "date": "2026-06-11",
                "source": "temu_us",
                "data_type": "product",
                "title": "Comfort cloud slides",
                "rank": 2,
                "price": "$7.99",
                "competition_count": 35,
            },
        ]
    )
    assert rows[0]["hot_score"] >= 50
    assert "互动" in rows[0]["reason"]
    assert "低价" in rows[1]["reason"]
    assert "竞争较少" in rows[1]["reason"]
