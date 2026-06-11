from report import build_report


def test_report_contains_opportunity_table_and_recommendation_sections():
    rows = [
        {
            "source": "tiktok_us", "title": "Cloud slides summer trend", "price": None,
            "hot_score": 88, "reason": "播放量高；标题包含 cloud slides",
            "product_url": "https://tiktok.example/1",
        },
        {
            "source": "amazon_us", "title": "Orthopedic sandals with arch support", "price": "$29.99",
            "hot_score": 82, "reason": "排名靠前；标题包含 orthopedic",
            "product_url": "https://amazon.example/1",
        },
    ]

    text = build_report("2026-06-11", rows, [])

    assert "## Top 20 爆款机会榜" in text
    assert "## 今日建议跟款方向" in text
    assert "| 排名 | 来源 | 标题 | 价格 | 爆款分 | 机会等级 | 爆款原因 | 链接 |" in text
    assert "立即跟款" in text
    assert "重点观察" in text
    assert "Cloud Slides 云朵拖鞋" in text
    assert "Orthopedic Sandals 足弓支撑凉鞋" in text


def test_report_explains_when_tiktok_has_no_data():
    text = build_report("2026-06-11", [], [])
    assert "TikTok 今日未采集到有效数据，可能原因：页面反爬、地区限制、选择器失效或需要登录。" in text
