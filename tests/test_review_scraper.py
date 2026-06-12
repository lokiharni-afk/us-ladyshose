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
        "Recovery Slides",
        10,
    )

    assert rows[0]["product_title"] == "Recovery Slides"
    assert rows[0]["review_rating"] == "5.0"
    assert rows[0]["review_text"] == "Comfortable and soft."
    assert rows[0]["review_date"] == "Reviewed in the United States on June 1, 2026"
