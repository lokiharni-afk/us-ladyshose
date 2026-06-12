from scraper import TIKTOK_SEARCHES, parse_amazon_html, parse_temu_html, parse_tiktok_html, select_top20_amazon


def test_select_top20_amazon_filters_before_limiting():
    rows = [
        {"source": "tiktok_us", "hot_score": 100 - rank, "product_url": f"https://tiktok/{rank}"}
        for rank in range(20)
    ]
    rows.extend(
        [
            {"source": "amazon_us", "hot_score": 70 - rank, "product_url": f"https://amazon/{rank}"}
            for rank in range(25)
        ]
    )

    selected = select_top20_amazon(rows)

    assert len(selected) == 20
    assert all(row["source"] == "amazon_us" for row in selected)


def test_parse_amazon_html_extracts_product():
    html = '<div data-asin="A1"><h2><a href="/dp/A1"><span>Soft Slides</span></a></h2><span class="a-price"><span class="a-offscreen">$19.99</span></span><span class="a-icon-alt">4.7 out of 5 stars</span><span class="a-size-base">1,234</span><img src="img.jpg"></div>'
    rows = parse_amazon_html(html, "2026-06-11", "search", "women slides", 50)
    assert rows[0]["title"] == "Soft Slides"
    assert rows[0]["price"] == "$19.99"
    assert rows[0]["rank"] == 1


def test_parse_tiktok_html_allows_missing_views():
    html = '<div data-e2e="search-video-item"><a href="/@shoe/video/1"><div data-e2e="search-card-desc">Cloud slides</div></a><strong data-e2e="like-count">12K</strong><strong data-e2e="comment-count">300</strong></div>'
    rows = parse_tiktok_html(html, "2026-06-11", "cloud slides", 20)
    assert rows[0]["source"] == "tiktok_us"
    assert rows[0]["data_type"] == "trend_video"
    assert rows[0]["list_type"] == "keyword_search"
    assert rows[0]["likes"] == "12K"
    assert rows[0]["views"] is None


def test_tiktok_uses_requested_us_women_shoes_keywords():
    assert TIKTOK_SEARCHES == [
        "women sandals",
        "cloud slides",
        "platform sandals",
        "orthopedic sandals",
        "recovery slides",
        "flip flops women",
        "summer slippers women",
        "beach sandals women",
    ]


def test_parse_temu_html_records_competition_count():
    html = '<div data-testid="product-card"><a href="/goods.html?id=1"><img alt="Platform Slides" src="x.jpg"></a><span data-testid="price">$7.99</span></div>'
    rows = parse_temu_html(html, "2026-06-11", "platform slides", 50)
    assert rows[0]["competition_count"] == 1
    assert rows[0]["source"] == "temu_us"


def test_select_top20_amazon_only_returns_amazon_products_in_overall_top20():
    rows = [
        {"source": "amazon_us", "hot_score": 90, "product_url": "https://amazon.com/dp/B000000001"},
        {"source": "tiktok_us", "hot_score": 95, "product_url": "https://tiktok.com/video/1"},
        {"source": "amazon_us", "hot_score": 80, "product_url": ""},
    ]

    selected = select_top20_amazon(rows)

    assert len(selected) == 1
    assert selected[0]["hot_score"] == 90
