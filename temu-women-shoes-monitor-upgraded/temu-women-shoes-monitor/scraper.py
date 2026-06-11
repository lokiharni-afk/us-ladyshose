"""Resilient Playwright collectors for Amazon US, TikTok, and Temu US."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Callable
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup, Tag
from playwright.async_api import BrowserContext, Page, async_playwright

AMAZON_TASKS = [
    ("best_sellers", "Best Sellers Women Sandals", "https://www.amazon.com/Best-Sellers-Womens-Sandals/zgbs/fashion/679425011"),
    ("movers_and_shakers", "Movers & Shakers Women Shoes", "https://www.amazon.com/gp/movers-and-shakers/fashion/679337011"),
    ("new_releases", "New Releases Women Sandals", "https://www.amazon.com/gp/new-releases/fashion/679425011"),
]
AMAZON_SEARCHES = ["women summer slippers", "women slides", "platform sandals women"]
TIKTOK_SEARCHES = [
    "women sandals",
    "cloud slides",
    "platform sandals",
    "orthopedic sandals",
    "recovery slides",
    "flip flops women",
    "summer slippers women",
    "beach sandals women",
]
TEMU_SEARCHES = ["women summer slippers", "women slides", "platform sandals women", "cloud slides", "women sandals"]

LOGGER = logging.getLogger(__name__)


def _text(node: Tag | None, selectors: list[str]) -> str | None:
    if not node:
        return None
    for selector in selectors:
        found = node.select_one(selector)
        if found and found.get_text(" ", strip=True):
            return found.get_text(" ", strip=True)
    return None


def _attr(node: Tag | None, selectors: list[str], attribute: str) -> str | None:
    if not node:
        return None
    for selector in selectors:
        found = node.select_one(selector)
        if found and found.get(attribute):
            return str(found.get(attribute))
    return None


def parse_amazon_html(html: str, run_date: str, list_type: str, keyword: str, limit: int = 50) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[data-asin]:not([data-asin=''])")
    rows = []
    for card in cards:
        title = _text(card, ["h2 span", "a.a-link-normal span", ".p13n-sc-truncate-desktop-type2"])
        href = _attr(card, ["h2 a", "a.a-link-normal"], "href")
        if not title or not href:
            continue
        rating_text = _text(card, [".a-icon-alt"])
        rows.append({
            "date": run_date, "source": "amazon_us", "data_type": "product",
            "list_type": list_type, "keyword": keyword, "rank": len(rows) + 1,
            "title": title, "price": _text(card, [".a-price .a-offscreen", ".p13n-sc-price"]),
            "rating": rating_text.split(" ")[0] if rating_text else None,
            "review_count": _text(card, [".a-size-base", ".a-link-normal .a-size-small"]),
            "product_url": urljoin("https://www.amazon.com", href),
            "image_url": _attr(card, ["img"], "src"),
        })
        if len(rows) >= limit:
            break
    return rows


def parse_tiktok_html(html: str, run_date: str, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[data-e2e='search-video-item'], [data-e2e='search_top-item']")
    rows = []
    for card in cards:
        href = _attr(card, ["a[href*='/video/']"], "href")
        title = _text(card, ["[data-e2e='search-card-desc']", "[data-e2e='search-card-video-caption']", "a"])
        if not title or not href:
            continue
        rows.append({
            "date": run_date, "source": "tiktok_us", "data_type": "trend_video", "list_type": "keyword_search",
            "keyword": keyword, "rank": len(rows) + 1, "title": title,
            "price": None, "rating": None, "review_count": None,
            "likes": _text(card, ["[data-e2e='like-count']"]),
            "comments": _text(card, ["[data-e2e='comment-count']"]),
            "views": _text(card, ["[data-e2e='video-views']", "[data-e2e='search-card-video-views']"]),
            "published_at": _text(card, ["time"]),
            "competition_count": None,
            "product_url": urljoin("https://www.tiktok.com", href),
            "image_url": _attr(card, ["img"], "src"),
        })
        if len(rows) >= limit:
            break
    return rows


def parse_temu_html(html: str, run_date: str, keyword: str, limit: int = 50) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[data-testid='product-card'], [data-product-id], div[class*='goods-container']")
    competition_count = len(cards)
    rows = []
    for card in cards:
        href = _attr(card, ["a[href*='goods']", "a[href]"], "href")
        title = _attr(card, ["img[alt]"], "alt") or _text(card, ["[data-testid='product-title']", "h2", "h3"])
        if not title or not href:
            continue
        rows.append({
            "date": run_date, "source": "temu_us", "data_type": "product", "list_type": "search",
            "keyword": keyword, "rank": len(rows) + 1, "title": title,
            "price": _text(card, ["[data-testid='price']", "[class*='price']"]),
            "competition_count": competition_count,
            "product_url": urljoin("https://www.temu.com", href),
            "image_url": _attr(card, ["img"], "src"),
        })
        if len(rows) >= limit:
            break
    return rows


async def _load_and_parse(
    context: BrowserContext,
    url: str,
    parser: Callable[..., list[dict[str, Any]]],
    parser_args: tuple[Any, ...],
    semaphore: asyncio.Semaphore,
) -> list[dict[str, Any]]:
    async with semaphore:
        page: Page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            for _ in range(8):
                await page.mouse.wheel(0, 2500)
                await page.wait_for_timeout(750)
            content = (await page.content()).lower()
            if any(marker in content for marker in ("captcha", "verify you are human", "unusual traffic")):
                raise RuntimeError("页面出现验证码或访问验证")
            return parser(await page.content(), *parser_args)
        finally:
            await page.close()


async def collect_all(run_date: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows, warnings = [], []
    headless = os.getenv("HEADLESS", "true").lower() != "false"
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            permissions=["geolocation"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        )
        semaphore = asyncio.Semaphore(3)
        amazon_tasks: list[tuple[str, Any]] = []
        tiktok_tasks: list[tuple[str, Any]] = []
        temu_tasks: list[tuple[str, Any]] = []
        for list_type, label, url in AMAZON_TASKS:
            amazon_tasks.append((f"Amazon {label}", _load_and_parse(context, url, parse_amazon_html, (run_date, list_type, label, 50), semaphore)))
        for keyword in AMAZON_SEARCHES:
            url = f"https://www.amazon.com/s?k={quote_plus(keyword)}"
            amazon_tasks.append((f"Amazon {keyword}", _load_and_parse(context, url, parse_amazon_html, (run_date, "search", keyword, 50), semaphore)))
        for keyword in TIKTOK_SEARCHES:
            url = f"https://www.tiktok.com/search?q={quote_plus(keyword)}"
            tiktok_tasks.append((f"TikTok {keyword}", _load_and_parse(context, url, parse_tiktok_html, (run_date, keyword, 20), semaphore)))
        for keyword in TEMU_SEARCHES:
            url = f"https://www.temu.com/search_result.html?search_key={quote_plus(keyword)}"
            temu_tasks.append((f"Temu {keyword}", _load_and_parse(context, url, parse_temu_html, (run_date, keyword, 50), semaphore)))

        for tasks in (amazon_tasks, tiktok_tasks, temu_tasks):
            results = await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)
            for (label, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    message = f"{label}：采集失败，{result}"
                    LOGGER.warning(message)
                    warnings.append(message)
                elif not result:
                    message = f"{label}：页面未解析到有效记录，可能是页面结构变化、访问受限或需要登录"
                    LOGGER.warning(message)
                    warnings.append(message)
                else:
                    rows.extend(result)
        await context.close()
        await browser.close()
    return rows, warnings
