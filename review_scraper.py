"""Collect up to 10 displayed reviews from each Top20 Amazon product page."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bs4 import BeautifulSoup, Tag
from playwright.async_api import BrowserContext, async_playwright

LOGGER = logging.getLogger(__name__)
MAX_REVIEWS_PER_PRODUCT = 10
REVIEW_STAGE_TIMEOUT_SECONDS = 180


def _text(node: Tag, selector: str) -> str | None:
    found = node.select_one(selector)
    return found.get_text(" ", strip=True) if found else None


def parse_amazon_reviews(
    html: str,
    product_title: str,
    limit: int = MAX_REVIEWS_PER_PRODUCT,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for card in soup.select("[data-hook='review']"):
        rating_text = _text(card, "[data-hook='review-star-rating'], [data-hook='cmps-review-star-rating']")
        review_text = _text(card, "[data-hook='review-body']")
        if not review_text:
            continue
        rows.append({
            "product_title": product_title,
            "review_text": review_text,
            "review_rating": rating_text.split(" ")[0] if rating_text else None,
            "review_date": _text(card, "[data-hook='review-date']"),
        })
        if len(rows) >= limit:
            break
    return rows


async def _collect_product_page(
    context: BrowserContext,
    product: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> tuple[list[dict[str, Any]], str | None]:
    title = str(product.get("title") or "Amazon 商品")
    url = str(product.get("product_url") or "")
    if not url:
        return [], f"{title}：缺少商品链接"
    async with semaphore:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            content = await page.content()
            lower = content.lower()
            if any(marker in lower for marker in ("captcha", "verify you are human", "unusual traffic")):
                raise RuntimeError("页面出现验证码或访问验证")
            return parse_amazon_reviews(content, title), None
        except Exception as exc:
            message = f"{title}评价采集失败：{exc}"
            LOGGER.warning(message)
            return [], message
        finally:
            await page.close()


async def collect_amazon_reviews(
    products: list[dict[str, Any]],
    headless: bool = True,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not products:
        return [], []

    async def collect() -> tuple[list[dict[str, Any]], list[str]]:
        reviews: list[dict[str, Any]] = []
        warnings: list[str] = []
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            context = await browser.new_context(locale="en-US", timezone_id="America/New_York")
            semaphore = asyncio.Semaphore(5)
            results = await asyncio.gather(
                *(_collect_product_page(context, product, semaphore) for product in products),
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, Exception):
                    warnings.append(f"评价采集失败：{result}")
                else:
                    rows, warning = result
                    reviews.extend(rows)
                    if warning:
                        warnings.append(warning)
            await context.close()
            await browser.close()
        return reviews, warnings

    try:
        return await asyncio.wait_for(collect(), timeout=REVIEW_STAGE_TIMEOUT_SECONDS)
    except Exception as exc:
        message = f"今日评价采集失败：{exc}"
        LOGGER.warning(message)
        return [], [message]
