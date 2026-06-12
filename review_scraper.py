"""Collect Amazon reviews for Top20 Amazon products without blocking the daily run."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag
from playwright.async_api import BrowserContext, async_playwright

LOGGER = logging.getLogger(__name__)
REVIEW_TYPES = (("positive", "positive", 5), ("critical", "critical", 5), ("recent", "recent", 10))


def _text(node: Tag, selector: str) -> str | None:
    found = node.select_one(selector)
    return found.get_text(" ", strip=True) if found else None


def parse_amazon_reviews(
    html: str,
    run_date: str,
    review_type: str,
    product_title: str,
    product_url: str,
    limit: int,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for card in soup.select("[data-hook='review']"):
        rating_text = _text(card, "[data-hook='review-star-rating'], [data-hook='cmps-review-star-rating']")
        helpful_text = _text(card, "[data-hook='helpful-vote-statement']") or ""
        helpful_match = re.search(r"([\d,]+)", helpful_text)
        rows.append({
            "date": run_date,
            "source": "amazon_us",
            "product_title": product_title,
            "product_url": product_url,
            "review_type": review_type,
            "review_rating": rating_text.split(" ")[0] if rating_text else None,
            "review_title": _text(card, "[data-hook='review-title']"),
            "review_text": _text(card, "[data-hook='review-body']"),
            "review_date": _text(card, "[data-hook='review-date']"),
            "verified_purchase": card.select_one("[data-hook='avp-badge']") is not None,
            "helpful_count": int(helpful_match.group(1).replace(",", "")) if helpful_match else 0,
        })
        if len(rows) >= limit:
            break
    return rows


def _asin(product_url: str) -> str | None:
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", urlparse(product_url).path, re.IGNORECASE)
    return match.group(1).upper() if match else None


async def _collect_page(
    context: BrowserContext,
    run_date: str,
    product: dict[str, Any],
    review_type: str,
    filter_value: str,
    limit: int,
    semaphore: asyncio.Semaphore,
) -> tuple[list[dict[str, Any]], str | None]:
    asin = _asin(str(product.get("product_url") or ""))
    if not asin:
        return [], f"{product.get('title', 'Amazon 商品')}：无法识别 ASIN"
    if review_type == "recent":
        url = f"https://www.amazon.com/product-reviews/{asin}/?sortBy=recent"
    else:
        url = f"https://www.amazon.com/product-reviews/{asin}/?filterByStar={filter_value}"
    async with semaphore:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            content = await page.content()
            lower = content.lower()
            if any(marker in lower for marker in ("captcha", "verify you are human", "unusual traffic")):
                raise RuntimeError("页面出现验证码或访问验证")
            return parse_amazon_reviews(
                content, run_date, review_type, str(product.get("title") or ""),
                str(product.get("product_url") or ""), limit,
            ), None
        except Exception as exc:
            message = f"{product.get('title', 'Amazon 商品')} {review_type}评价采集失败：{exc}"
            LOGGER.warning(message)
            return [], message
        finally:
            await page.close()


async def collect_amazon_reviews(
    products: list[dict[str, Any]],
    run_date: str,
    headless: bool = True,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not products:
        return [], []
    reviews: list[dict[str, Any]] = []
    warnings: list[str] = []
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            context = await browser.new_context(locale="en-US", timezone_id="America/New_York")
            semaphore = asyncio.Semaphore(2)
            tasks = [
                _collect_page(context, run_date, product, review_type, filter_value, limit, semaphore)
                for product in products
                for review_type, filter_value, limit in REVIEW_TYPES
            ]
            for rows, warning in await asyncio.gather(*tasks):
                reviews.extend(rows)
                if warning:
                    warnings.append(warning)
            await context.close()
            await browser.close()
    except Exception as exc:
        message = f"今日评价采集失败：{exc}"
        LOGGER.warning(message)
        return [], [message]
    return reviews, warnings
