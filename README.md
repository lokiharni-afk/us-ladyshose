# 美国女鞋多平台爆款监控

每天独立监控 Amazon US、TikTok 和 Temu US 的美国女鞋数据，生成中文爆款日报。Amazon 与 TikTok 是主要信号源，Temu 用于低价和竞争验证。项目不使用 Google Sheets，也不进行跨平台商品关联。

## 监控范围

### Amazon US

- Best Sellers Women Sandals
- Movers & Shakers Women Shoes
- New Releases Women Sandals
- 搜索：`women summer slippers`、`women slides`、`platform sandals women`

### TikTok

- 搜索：`summer slippers`、`platform slides`、`women sandals`、`cloud slides`
- 尝试采集视频标题、点赞数、评论数、播放量、发布时间和链接
- 播放量或发布时间无法获取时保留为空

### Temu US

- 搜索：`women summer slippers`、`women slides`、`platform sandals women`、`cloud slides`、`women sandals`
- 采集标题、价格、排名、链接、图片和页面内竞争数量

每个任务最多保留前 50 条有效记录。三个平台单独采集和评分，不进行跨平台关联。

## 输出

- `data/raw_data.csv`：历史原始数据与评分，按日期、平台和链接去重
- `reports/YYYY-MM-DD.md`：每日中文爆款日报

日报包含今日美国女鞋趋势、TikTok 热度款、Amazon 验证款、Temu 低价跟款机会、Top 20 建议跟款商品和风险提醒。

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

- Amazon：排名靠前、进入 Movers & Shakers、Best Sellers 或 New Releases、高评分、高评论数和趋势标题词加分。
- TikTok：点赞、评论、播放量、发布时间新鲜度和趋势标题词加分。
- Temu：排名靠前、低价、页面内同类竞争较少和趋势标题词加分。
- 趋势词包括 `platform`、`cloud`、`comfort`、`soft`、`summer`、`beach`、`wedge`、`slides`。

## GitHub Actions

工作流位于 `.github/workflows/daily.yml`，每天 UTC 01:00，即北京时间 09:00 自动运行，也支持手动触发。工作流会运行测试、安装 Chromium、执行采集，并自动提交和推送更新后的 CSV 与日报。

仓库需要允许 GitHub Actions 写入内容：

1. 打开仓库 `Settings`。
2. 进入 `Actions` > `General`。
3. 在 `Workflow permissions` 中选择 `Read and write permissions`。

## 访问限制与维护

Amazon、TikTok 和 Temu 都可能按地区、登录状态或访问频率展示验证码，且页面结构会变化。本项目不会绕过验证码。某个任务失败时，其他任务仍继续运行，失败原因会写入日报风险提醒。

选择器失效时，可更新 `scraper.py` 中对应的解析函数。首次部署后应手动运行一次 GitHub Actions，并检查三个平台的实际有效记录数。

