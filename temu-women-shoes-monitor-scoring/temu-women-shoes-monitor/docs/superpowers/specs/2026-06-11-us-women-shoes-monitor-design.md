# 美国女鞋多平台爆款监控设计

## 目标

每天独立采集 Amazon US、TikTok 和 Temu US 的美国女鞋数据，按平台特点计算爆款评分，并生成中文日报。Amazon US 和 TikTok 是优先监控渠道，Temu US 仅用于低价和竞争验证。

## 数据源

### Amazon US

- 榜单：Best Sellers Women Sandals、Movers & Shakers Women Shoes、New Releases Women Sandals
- 搜索词：women summer slippers、women slides、platform sandals women
- 字段：标题、价格、评分、评论数、排名、链接、图片、榜单类型

### TikTok

- 搜索词：summer slippers、platform slides、women sandals、cloud slides
- 字段：视频标题、点赞数、评论数、播放量、发布时间、链接
- 播放量不可获取时留空

### Temu US

- 搜索词：women summer slippers、women slides、platform sandals women、cloud slides、women sandals
- 字段：标题、价格、排名、链接、图片、关键词

## 架构

- `scraper.py` 使用 Playwright 按平台独立抓取，单个任务失败不阻断其他任务。不绕过验证码或访问限制。
- `analyzer.py` 统一清洗数据并按平台规则计算 `hot_score` 和中文 `reason`，不进行跨平台关联。
- `report.py` 基于当日数据和抓取状态生成中文 Markdown 日报。
- `main.py` 协调抓取、分析、CSV 追加去重和日报生成。
- `.github/workflows/daily.yml` 每天北京时间 09:00 运行并提交结果。

## 评分

- Amazon：排名靠前加分；Movers & Shakers 高额加分；高评分和高评论数加分；趋势标题词加分。
- TikTok：点赞、评论、播放量和发布时间新鲜度加分；趋势标题词加分。
- Temu：排名靠前、价格较低、搜索结果数量较少和趋势标题词加分。
- 各平台单独评分，Top 20 直接从当日全部独立记录中按分数排序。

## 输出与失败处理

- `data/raw_data.csv` 保存统一字段，不适用字段留空；按稳定记录键去重。
- `reports/YYYY-MM-DD.md` 包含今日美国女鞋趋势、TikTok 热度款、Amazon 验证款、Temu 低价跟款机会、Top 20 建议跟款商品和风险提醒。
- 抓取受阻时记录任务错误，保留历史 CSV，并在日报风险提醒中明确说明。

## 测试

- 单元测试覆盖数值解析、各平台评分、CSV 合并去重和日报章节。
- 抓取器使用静态 HTML 解析测试，避免测试依赖线上页面。

