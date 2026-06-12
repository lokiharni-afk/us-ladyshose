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
    assert "S级爆款：0 条" in text
    assert "A级爆款：2 条" in text
    assert "| 排名 | 来源 | 标题 | 价格 | 爆款分 | 爆款等级 | 机会等级 | 爆款原因 | 链接 |" in text
    assert "A级爆款" in text
    assert "立即跟款" in text
    assert "重点观察" in text
    assert "Cloud Slides 云朵拖鞋" in text
    assert "Orthopedic Sandals 足弓支撑凉鞋" in text
    assert "| 方向名称 | 英文关键词 | 推荐原因 | 建议售价区间 | 风险等级 |" in text
    assert "Recovery Slides" in text
    assert "Platform Sandals" in text
    assert "Beach Sandals" in text


def test_report_builds_temu_opportunity_from_brand_and_amazon_price():
    rows = [
        {
            "source": "amazon_us",
            "title": "Crocs Cloud Slides",
            "price": "$39.99",
            "hot_score": 95,
            "reason": "排名靠前",
            "product_url": "https://amazon.example/branded",
        },
        {
            "source": "amazon_us",
            "title": "Generic Orthopedic Sandals",
            "price": "$22.99",
            "hot_score": 90,
            "reason": "排名靠前",
            "product_url": "https://amazon.example/generic",
        },
        {
            "source": "amazon_us",
            "title": "Generic Beach Sandals",
            "price": "$12.99",
            "hot_score": 85,
            "reason": "排名靠前",
            "product_url": "https://amazon.example/cheap",
        },
        {
            "source": "amazon_us",
            "title": "Generic Recovery Slides",
            "price": "$45.00",
            "hot_score": 80,
            "reason": "排名靠前",
            "product_url": "https://amazon.example/premium",
        },
    ]

    text = build_report("2026-06-12", rows, [])

    assert "## Temu 跟款机会判断" in text
    assert "| Amazon 商品 | Amazon价格 | 品牌词 | Temu机会 | 推荐Temu售价 |" in text
    assert "Crocs Cloud Slides" in text
    assert "Crocs | 不建议" in text
    assert "Generic Orthopedic Sandals" in text
    assert "高 | 7.99-14.99美元" in text
    assert "Generic Beach Sandals" in text
    assert "高 | 谨慎跟款" in text
    assert "Generic Recovery Slides" in text
    assert "高 | 9.99-19.99美元" in text


def test_report_builds_temu_follow_list_from_top20():
    rows = [
        {
            "source": "amazon_us", "title": "Generic Recovery Slides", "price": "$35.00",
            "hot_score": 95, "reason": "排名靠前",
        },
        {
            "source": "amazon_us", "title": "OOFOS Recovery Slides", "price": "$60.00",
            "hot_score": 92, "reason": "排名靠前",
        },
        {
            "source": "amazon_us", "title": "Generic Orthopedic Arch Support Sandals", "price": "$25.00",
            "hot_score": 90, "reason": "排名靠前",
        },
        {
            "source": "amazon_us", "title": "Generic Beach Sandals", "price": "$12.00",
            "hot_score": 85, "reason": "排名靠前",
        },
    ]

    text = build_report("2026-06-12", rows, [])

    assert "## Temu跟款清单" in text
    assert "| 关键词 | Amazon价格 | 建议Temu售价 | 竞争等级 | 跟款优先级 | 原因 |" in text
    assert "recovery slides | $35.00 | 9.99-19.99美元 | 中 | 高" in text
    assert "OOFOS Recovery Slides" not in text.split("## Temu跟款清单", 1)[1].split("## 风险提醒", 1)[0]
    assert "品牌词 OOFOS，跟款优先级低" in text
    assert "orthopedic arch support sandals | $25.00 | 7.99-14.99美元 | 低 | 高" in text
    assert "beach sandals | $12.00 | 6.99-12.99美元 | 低 | 中" in text


def test_report_explains_when_tiktok_has_no_data():
    text = build_report("2026-06-11", [], [])
    assert "TikTok 今日未采集到有效数据，可能原因：页面反爬、地区限制、选择器失效或需要登录。" in text


def test_report_deduplicates_top20_and_shows_deduplication_stats():
    rows = [
        {
            "source": "amazon_us", "title": "CloudStep Women's Recovery Cloud Slides",
            "price": "$19.99", "hot_score": 82, "reason": "旧记录",
        },
        {
            "source": "amazon_us", "title": "CloudStep Womens Recovery Cloud Slides",
            "price": "$21.99", "hot_score": 91, "reason": "最高分记录",
        },
    ]

    text = build_report("2026-06-12", rows, [])
    top20 = text.split("## Top 20 爆款机会榜", 1)[1].split("## 今日建议跟款方向", 1)[0]

    assert "本次去重数量：1" in text
    assert "原始记录：2" in text
    assert "去重后记录：1" in text
    assert "最高分记录" in top20
    assert "旧记录" not in top20


def test_report_contains_keyword_trend_radar_and_history_warning():
    trends = [
        {
            "keyword": "recovery",
            "today_count": 8,
            "average_3d": 4.0,
            "average_7d": 2.86,
            "average_30d": 2.0,
            "trend_status": "快速上升",
            "action": "优先跟踪，可作为明日重点选品方向。",
        }
    ]

    text = build_report(
        "2026-06-12",
        [],
        [],
        trend_rows=trends,
        trend_metadata={"history_days": 3, "insufficient_history": True},
    )

    assert "## 关键词趋势雷达" in text
    assert "当前历史数据：3天" in text
    assert "| 关键词 | 今日出现次数 | 近3日均值 | 近7日均值 | 近30日均值 | 趋势状态 | 操作建议 |" in text
    assert "recovery | 8 | 4.0 | 2.86 | 2.0 | 快速上升 | 优先跟踪，可作为明日重点选品方向。" in text
    assert "趋势结果仅供参考。" in text


def test_report_contains_buyer_review_insights_and_empty_fallback():
    insights = [{
        "product_title": "Recovery Slides",
        "positive_summary": "舒适、软底、轻便",
        "negative_summary": "尺码偏小、鞋底硬",
        "sizing_insight": "偏小",
        "quality_risk": "鞋底硬",
        "usage_scenario": "walking、recovery",
        "product_improvement_suggestion": "优化尺码与鞋底柔软度",
        "temu_listing_suggestion": "标题突出舒适和软底；尺码表提醒偏小",
    }]

    text = build_report("2026-06-12", [], [], review_insights=insights)
    empty = build_report("2026-06-12", [], [], review_insights=[])

    assert "## 买家评价洞察" in text
    assert "### 买家最喜欢的点" in text
    assert "### 买家最常抱怨的问题" in text
    assert "### Temu 上架优化建议" in text
    assert "舒适" in text
    assert "尺码偏小" in text
    assert "今日评价采集失败或无可用评价" in empty
