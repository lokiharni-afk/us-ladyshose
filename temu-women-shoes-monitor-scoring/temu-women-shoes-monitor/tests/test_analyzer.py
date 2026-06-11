from analyzer import analyze_rows, parse_number
from score import opportunity_level


def test_parse_number_handles_social_suffixes_commas_and_empty_values():
    assert parse_number("1.2K") == 1200
    assert parse_number("3.4M views") == 3_400_000
    assert parse_number("12,345 ratings") == 12345
    assert parse_number("") is None
    assert parse_number(None) is None


def test_amazon_score_uses_required_100_point_model_and_chinese_reason():
    row = analyze_rows(
        [{
            "source": "amazon_us",
            "title": "Recovery comfort arch support soft platform sandals",
            "rank": 8,
            "review_count": "5,200",
            "price": "$19.99",
            "rating": "4.7",
        }]
    )[0]

    assert row["hot_score"] == 100
    assert "排名靠前" in row["reason"]
    assert "评论数高" in row["reason"]
    assert "价格处于8-25美元黄金区间" in row["reason"]
    assert "recovery" in row["reason"]
    assert "comfort" in row["reason"]
    assert "arch support" in row["reason"]


def test_tiktok_score_uses_required_100_point_model_and_handles_empty_fields():
    strong = analyze_rows(
        [{
            "source": "tiktok_us",
            "title": "Cloud slides and recovery slides for summer",
            "views": "1.2M",
            "likes": "55K",
            "comments": "1.5K",
        }]
    )[0]
    empty = analyze_rows([{"source": "tiktok_us", "title": None}])[0]

    assert strong["hot_score"] == 91
    assert "播放量达到100万以上" in strong["reason"]
    assert "点赞数达到5万以上" in strong["reason"]
    assert "cloud slides" in strong["reason"]
    assert empty["hot_score"] == 0
    assert empty["reason"] == "数据不足，暂未发现明确爆款信号。"


def test_opportunity_levels_follow_score_thresholds():
    assert opportunity_level(85) == "立即跟款"
    assert opportunity_level(70) == "重点观察"
    assert opportunity_level(55) == "普通观察"
    assert opportunity_level(54.99) == "暂不跟款"
