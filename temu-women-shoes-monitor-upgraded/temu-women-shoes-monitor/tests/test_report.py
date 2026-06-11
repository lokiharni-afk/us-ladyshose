from report import build_report


def test_report_contains_all_required_sections_and_platform_rows():
    rows = [
        {"source": "tiktok_us", "title": "Cloud slides video", "hot_score": 88, "reason": "互动热度高", "product_url": "https://tiktok.example/1"},
        {"source": "amazon_us", "title": "Platform sandals", "hot_score": 82, "reason": "排名靠前", "product_url": "https://amazon.example/1"},
        {"source": "temu_us", "title": "Soft slides", "hot_score": 70, "reason": "低价验证机会", "product_url": "https://temu.example/1"},
    ]
    text = build_report("2026-06-11", rows, ["TikTok: 播放量部分缺失"])
    for heading in [
        "今日美国女鞋趋势",
        "TikTok 热度趋势",
        "Amazon 验证款",
        "Temu 低价跟款机会",
        "Top 20 建议跟款商品",
        "风险提醒",
    ]:
        assert heading in text
    assert "Cloud slides video" in text


def test_report_explains_when_tiktok_has_no_data():
    text = build_report("2026-06-11", [], [])
    assert "TikTok 今日未采集到有效数据，可能原因：页面反爬、地区限制、选择器失效或需要登录。" in text
