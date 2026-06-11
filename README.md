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

- `data/raw_data.csv`：历史原始数据与评分，按日期、平台和链接去重
- `reports/YYYY-MM-DD.md`：每日中文爆款日报

日报包含今日美国女鞋趋势、TikTok 热度趋势、Amazon 验证款、Temu 低价跟款机会、Top 20 爆款机会榜、今日建议跟款方向和风险提醒。TikTok 当日无有效数据时，日报会明确提示页面反爬、地区限制、选择器失效或需要登录等可能原因。

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
