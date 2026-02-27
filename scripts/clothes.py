"""
Scraper for umico.az clothes (category_id=3003).
Fetches all pages concurrently and writes to data/clothes.csv.

Usage:
    python scripts/clothes.py
"""

import asyncio
import csv
import os
import time
from pathlib import Path

import aiohttp

# ── Config ──────────────────────────────────────────────────────────────────
BASE_URL = "https://mp-catalog.umico.az/api/v1/products"
CATEGORY_ID = 3003
PER_PAGE = 24
SORT = "global_popular_score"
CONCURRENCY = 20          # simultaneous requests
RETRY_LIMIT = 3
RETRY_DELAY = 2           # seconds between retries
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "clothes.csv"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "az",
    "content-language": "az",
    "http_accept_language": "az",
    "http_content_language": "az",
    "origin": "https://birmarket.az",
    "referer": "https://birmarket.az/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
}

CSV_FIELDS = [
    "id",
    "name",
    "brand",
    "category_id",
    "category_name",
    "status",
    "retail_price",
    "old_price",
    "discount_pct",
    "seller_name",
    "seller_rating",
    "rating_value",
    "review_count",
    "in_stock",
    "installment_enabled",
    "max_installment_months",
    "image_url",
    "product_url",
]

PRODUCT_BASE_URL = "https://birmarket.az/products"


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_product(p: dict) -> dict:
    offer = p.get("default_offer") or {}
    seller = offer.get("seller") or {}
    seller_name_obj = seller.get("marketing_name") or {}
    ratings = p.get("ratings") or {}
    category = p.get("category") or {}
    main_img = p.get("main_img") or {}

    retail_price = offer.get("retail_price")
    old_price = offer.get("old_price")
    if retail_price and old_price and old_price > retail_price:
        discount_pct = round((1 - retail_price / old_price) * 100, 1)
    else:
        discount_pct = 0.0

    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "brand": p.get("brand") or "",
        "category_id": p.get("category_id"),
        "category_name": category.get("name", ""),
        "status": p.get("status"),
        "retail_price": retail_price,
        "old_price": old_price,
        "discount_pct": discount_pct,
        "seller_name": seller_name_obj.get("name", ""),
        "seller_rating": seller.get("rating"),
        "rating_value": ratings.get("rating_value"),
        "review_count": ratings.get("session_count"),
        "in_stock": offer.get("avail_check", False),
        "installment_enabled": offer.get("installment_enabled", False),
        "max_installment_months": offer.get("max_installment_months"),
        "image_url": main_img.get("medium", ""),
        "product_url": f"{PRODUCT_BASE_URL}/{p.get('slugged_name', '')}",
    }


async def fetch_page(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    page: int,
) -> list[dict]:
    params = {
        "page": page,
        "category_id": CATEGORY_ID,
        "per_page": PER_PAGE,
        "sort": SORT,
    }
    for attempt in range(1, RETRY_LIMIT + 1):
        async with semaphore:
            try:
                async with session.get(
                    BASE_URL, params=params, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        return [parse_product(p) for p in data.get("products", [])]
                    print(f"  [page {page}] HTTP {resp.status}, attempt {attempt}/{RETRY_LIMIT}")
            except Exception as e:
                print(f"  [page {page}] Error: {e}, attempt {attempt}/{RETRY_LIMIT}")

        if attempt < RETRY_LIMIT:
            await asyncio.sleep(RETRY_DELAY)

    print(f"  [page {page}] Giving up after {RETRY_LIMIT} attempts.")
    return []


async def get_total_pages(session: aiohttp.ClientSession) -> int:
    params = {
        "page": 1,
        "category_id": CATEGORY_ID,
        "per_page": PER_PAGE,
        "sort": SORT,
    }
    async with session.get(
        BASE_URL, params=params, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)
    ) as resp:
        data = await resp.json(content_type=None)
    total = data["meta"]["total"]
    pages = (total + PER_PAGE - 1) // PER_PAGE
    print(f"Total products: {total:,}  |  Pages: {pages:,}")
    return pages


async def main() -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    start = time.perf_counter()

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        total_pages = await get_total_pages(session)

        tasks = [
            fetch_page(session, semaphore, page)
            for page in range(1, total_pages + 1)
        ]

        rows: list[dict] = []
        done = 0
        for coro in asyncio.as_completed(tasks):
            page_rows = await coro
            rows.extend(page_rows)
            done += 1
            if done % 100 == 0 or done == total_pages:
                elapsed = time.perf_counter() - start
                print(f"  Progress: {done}/{total_pages} pages | {len(rows):,} products | {elapsed:.1f}s")

    print(f"\nWriting {len(rows):,} rows to {OUTPUT_CSV} …")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.perf_counter() - start
    print(f"Done in {elapsed:.1f}s  ->  {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
