# 美国女鞋多平台爆款监控

每天独立监控 Amazon US、TikTok 和 Temu US 的美国女鞋数据，生成中文爆款日报。Amazon 与 TikTok 是主要信号源，Temu 用于低价和竞争验证。项目不使用 Google Sheets，也不进行跨平台商品关联。

## 监控范围

### Amazon US

- Best Sellers Women Sandals
- Movers & Shakers Women Shoes
- New Releases Women Sandals
- 搜索：`women summer slippers`、`women slides`、`platform sandals women`

### TikTok

- 搜索：`women sandals`、`cloud slides`、`platform sandals`、`orthopedic sandals`、`recovery slides`、`flip flops women`、`summer slippers women`、`beach sandals women`
- 尝试采集视频标题、点赞数、评论数、播放量、发布时间和链接
- 播放量或发布时间无法获取时保留为空
- 每个关键词尽量采集前 20 条结果
- TikTok 记录固定使用 `source=tiktok_us`、`data_type=trend_video`、`list_type=keyword_search`

### Temu US

- 搜索：`women summer slippers`、`women slides`、`platform sandals women`、`cloud slides`、`women sandals`
- 采集标题、价格、排名、链接、图片和页面内竞争数量

Amazon 和 Temu 每个任务最多保留前 50 条有效记录，TikTok 每个关键词最多保留前 20 条。三个平台单独采集和评分，不进行跨平台关联。

## 输出

- `data/raw_data.csv`：当天最新采集、评分和去重结果
- `data/history/YYYY-MM-DD.csv`：每日历史快照，用于趋势分析
- `data/reviews.csv`：Top20 中 Amazon 商品的买家评价
- `reports/YYYY-MM-DD.md`：每日中文爆款日报

日报包含今日美国女鞋趋势、TikTok 热度趋势、Amazon 验证款、Temu 低价跟款机会、Top 20 爆款机会榜、今日建议跟款方向、Temu 跟款机会判断和风险提醒。TikTok 当日无有效数据时，日报会明确提示页面反爬、地区限制、选择器失效或需要登录等可能原因。

### 日报选品建议

- 今日建议跟款方向基于 Top 20 爆款记录，至少输出 Recovery Slides、Orthopedic Sandals、Cloud Slides、Platform Sandals 和 Beach Sandals 五个方向。
- 每个方向展示英文关键词、推荐原因、建议售价区间和风险等级。
- Temu 跟款机会判断会识别 Crocs、OOFOS、Skechers、Clarks、REEF 和 Amazon Essentials 等品牌词；命中品牌词时标记为“不建议”。
- 非品牌 Amazon 商品按价格给出 Temu 建议：高于 30 美元建议 9.99-19.99 美元，15-30 美元建议 7.99-14.99 美元，低于 15 美元标记为谨慎跟款。
- Temu跟款清单基于 Top20 中的 Amazon 商品，输出搜索关键词、Amazon 价格、建议 Temu 售价、竞争等级、跟款优先级和原因。
- 清单中包含 recovery、orthopedic、arch support 或 cloud 的商品优先级为高；包含 OOFOS、Crocs、Clarks 或 Skechers 等品牌词时优先级降为低。
- Temu 清单建议售价：Amazon 高于 30 美元对应 9.99-19.99 美元，15-30 美元对应 7.99-14.99 美元，低于 15 美元对应 6.99-12.99 美元。
- 竞争等级按 Top20 中相同 Temu 搜索关键词的出现数量判断：5 条以上为高、2-4 条为中、1 条为低。

### 同款去重

`deduplicate.py` 会在生成日报和保存历史数据前执行同款去重。标题相似度超过 85%、品牌相同且价格差不超过 20% 时判定为同款，只保留爆款分最高的记录。

日报会展示本次去重数量、原始记录数和去重后记录数。Top20 爆款机会榜会再次执行去重保护，禁止出现重复商品。价格缺失时不会判定为同款，避免误删 TikTok 趋势内容；不同日期的记录会保留，用于历史趋势分析。

### 关键词趋势雷达

`trend_analyzer.py` 每次运行后读取 `data/history/*.csv` 的全部每日快照，按日期统计 recovery、orthopedic、arch support、cloud、platform、comfort、soft、beach、summer、slides、wedge、flip flops 和 sandals 的标题出现次数。

日报展示当前历史样本天数、今日出现次数、近 3 日均值、近 7 日均值、近 30 日均值、趋势状态和操作建议。今日次数超过近 7 日均值 1.5 倍为快速上升，超过 1.1 倍为小幅上升，达到 0.8 倍为稳定，否则为下降。历史数据不足 7 天时仍正常运行，并提示趋势结果仅供参考。

### 每日数据快照

每次运行会将当天去重后的最新数据同时写入：

- `data/raw_data.csv`
- `data/history/YYYY-MM-DD.csv`

`raw_data.csv` 始终表示最新一天的数据；日期快照用于形成真实的 3 天、7 天和 30 天趋势。GitHub Actions 会自动提交最新数据、每日快照和日报。

### 买家评价洞察

`review_scraper.py` 只对首次评分去重后的 Top20 爆款机会榜中的 Amazon 商品采集评价。每个商品只访问一次商品详情页，最多采集 10 条展示评价，并保存到 `data/reviews.csv`。字段包括商品标题、评价内容、评价评分和评价日期。

评价采集最多并发访问 5 个商品页面，单页超时 15 秒，整个评价阶段最长 3 分钟。页面反爬、需要验证或无法访问时返回空评价列表，不中断 Amazon、TikTok、Temu 主采集。GitHub Actions 任务设置为最长 10 分钟。

`review_analyzer.py` 从评价中提取并在日报展示：

- 买家最喜欢：comfortable、arch support、lightweight 等正面词。
- 买家吐槽：runs small、narrow fit、poor quality 等负面词。
- 高频评价关键词。
- Temu机会关键词：cloud、recovery、orthopedic、arch support。

Amazon 评分会根据评价信号联动调整：正面信号较强加 5-10 分，负面风险较高扣 5-15 分，最终分数仍限制在 0-100。日报新增“买家评价洞察”；无可用评价时会明确提示“今日评价采集失败或无可用评价”。

## 本地运行

需要 Python 3.11。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
pytest -v
python main.py
```

可选环境变量：

- `HEADLESS=false`：使用可见浏览器，便于本地排查
- `RUN_DATE=2026-06-11`：覆盖日报日期，格式为 `YYYY-MM-DD`

## 爆款评分

`score.py` 提供独立、可测试的 100 分爆款评分模型。每次运行都会重新计算 CSV 中全部记录的 `hot_score` 和中文 `reason`，不改变现有 CSV 字段结构。

### Amazon 评分

- 排名重点加权：前 10 名 45 分、前 30 名 35 分、前 50 名 20 分、其后 10 分。
- 评论数重点加权：5000 条以上 25 分、1000 条以上 20 分，其他档位保持不变。
- 价格最高 15 分：8-25 美元获得最高分。
- 标题关键词最高 20 分：cloud、platform、recovery、orthopedic 各 8 分，comfort、arch support 各 6 分，其他趋势词保持原权重。
- 组合趋势额外加分：`platform + comfort` 加 10 分、`cloud + slides` 加 10 分、`orthopedic + arch support` 加 15 分。
- 商品评分最高 10 分：4.6 以上获得最高分。
- 最终爆款分仍封顶 100 分。

### TikTok 评分

- 播放量最高 35 分，100 万以上获得最高分。
- 点赞数最高 25 分，5 万以上获得最高分。
- 评论数最高 15 分，1000 条以上获得最高分。
- 标题关键词最高 25 分，重点关注 cloud slides、platform sandals、recovery slides、orthopedic sandals、summer sandals、beach sandals 和 women sandals。

### 机会等级

- 85 分及以上：立即跟款
- 70-84 分：重点观察
- 55-69 分：普通观察
- 55 分以下：暂不跟款

### 爆款等级

- 90 分及以上：S级爆款
- 80-89 分：A级爆款
- 70-79 分：B级爆款
- 60-69 分：C级观察
- 60 分以下：忽略

日报会统计当天 S级爆款和 A级爆款数量，并在 Top 20 爆款机会榜中同时展示爆款等级和机会等级。

Temu 继续作为低价和竞争验证渠道，保留原有验证型评分。

## GitHub Actions

工作流位于 `.github/workflows/daily.yml`，每天 UTC 01:00，即北京时间 09:00 自动运行，也支持手动触发。工作流会运行测试、安装 Chromium、执行采集，并自动提交和推送更新后的 CSV 与日报。

仓库需要允许 GitHub Actions 写入内容：

1. 打开仓库 `Settings`。
2. 进入 `Actions` > `General`。
3. 在 `Workflow permissions` 中选择 `Read and write permissions`。

## 访问限制与维护

Amazon、TikTok 和 Temu 都可能按地区、登录状态或访问频率展示验证码，且页面结构会变化。本项目不会绕过验证码。某个任务失败时，其他任务仍继续运行，失败原因会写入日报风险提醒。

选择器失效时，可更新 `scraper.py` 中对应的解析函数。首次部署后应手动运行一次 GitHub Actions，并检查三个平台的实际有效记录数。
