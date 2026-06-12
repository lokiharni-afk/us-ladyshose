from review_scraper import parse_amazon_reviews


def test_parse_amazon_reviews_extracts_required_fields():
    html = """
    <div data-hook="review">
      <i data-hook="review-star-rating"><span>5.0 out of 5 stars</span></i>
      <a data-hook="review-title"><span>Great slides</span></a>
      <span data-hook="review-body"><span>Comfortable and soft.</span></span>
      <span data-hook="review-date">Reviewed in the United States on June 1, 2026</span>
      <span data-hook="avp-badge">Verified Purchase</span>
      <span data-hook="helpful-vote-statement">12 people found this helpful</span>
    </div>
    """
    rows = parse_amazon_reviews(
        html,
        "2026-06-12",
        "positive",
        "Recovery Slides",
        "https://www.amazon.com/dp/A1",
        5,
    )

    assert rows[0]["source"] == "amazon_us"
    assert rows[0]["review_type"] == "positive"
    assert rows[0]["review_rating"] == "5.0"
    assert rows[0]["verified_purchase"] is True
    assert rows[0]["helpful_count"] == 12

