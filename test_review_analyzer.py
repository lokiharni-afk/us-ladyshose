from review_analyzer import analyze_reviews


def test_review_analyzer_extracts_selection_insights():
    reviews = [
        {
            "product_title": "Recovery Slides",
            "review_text": "Very comfortable, soft and lightweight. Good for walking, arch support and true to size.",
        },
        {
            "product_title": "Recovery Slides",
            "review_text": "Runs small, narrow fit, hard sole and strong smell. Not durable. Recovery cloud style.",
        },
    ]

    insights = analyze_reviews(reviews)
    item = insights["Recovery Slides"]

    assert "舒适" in item["positive_summary"]
    assert "鞋型偏窄" in item["negative_summary"]
    assert "窄脚" in item["sizing_insight"]
    assert "鞋底硬" in item["quality_risk"]
    assert "walking" in item["usage_scenario"]
    assert item["positive_signal_count"] >= 3
    assert item["negative_signal_count"] >= 3
    assert "arch support" in item["frequent_review_keywords"]
    assert "recovery" in item["temu_opportunity_keywords"]
