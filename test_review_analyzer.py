from review_analyzer import analyze_reviews


def test_review_analyzer_extracts_selection_insights():
    reviews = [
        {
            "product_title": "Recovery Slides",
            "product_url": "https://amazon.com/dp/A1",
            "review_type": "positive",
            "review_text": "Very comfortable, soft and lightweight. Good for walking and true to size.",
        },
        {
            "product_title": "Recovery Slides",
            "product_url": "https://amazon.com/dp/A1",
            "review_type": "critical",
            "review_text": "Size too small, hard sole and strong smell. Not durable.",
        },
    ]

    insights = analyze_reviews(reviews)
    item = insights["https://amazon.com/dp/A1"]

    assert "舒适" in item["positive_summary"]
    assert "尺码偏小" in item["negative_summary"]
    assert "偏小" in item["sizing_insight"]
    assert "鞋底硬" in item["quality_risk"]
    assert "walking" in item["usage_scenario"]
    assert item["positive_signal_count"] >= 3
    assert item["negative_signal_count"] >= 3

