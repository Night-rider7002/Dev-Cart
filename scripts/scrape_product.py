#!/usr/bin/env python3
"""
scrape_product.py
Usage: python3 scrape_product.py "<amazon_url>"
Output: JSON to stdout — { "product_name": str, "image_url": str, "error": str|null }

Strategy:
  1. Try requests + BeautifulSoup (zero-browser, lowest RAM).
  2. If blocked (bot detection), fall back to Playwright Chromium (headless).

Docker requirements:
  pip install requests beautifulsoup4 lxml playwright
  playwright install chromium --with-deps
"""

import sys
import json
import re

def scrape_with_requests(url: str) -> dict:
    import requests
    from bs4 import BeautifulSoup

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1",
    }

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    if "api-services-support@amazon.com" in resp.text:
        raise ValueError("Bot-detected by Amazon. Switching to Playwright.")

    soup = BeautifulSoup(resp.text, "lxml")

    # Product title — multiple selector fallbacks
    name = None
    for sel in ["#productTitle", "#title", "h1.a-size-large"]:
        tag = soup.select_one(sel)
        if tag:
            name = tag.get_text(strip=True)
            break

    # Main image — Amazon stores it in a JS blob; parse raw HTML
    image_url = None
    img_tag = soup.select_one("#landingImage, #imgBlkFront, #main-image")
    if img_tag:
        image_url = img_tag.get("data-old-hires") or img_tag.get("src")

    # Fallback: extract from inline JSON (colorImages / imageGalleryData)
    if not image_url:
        match = re.search(r'"hiRes":"(https://m\.media-amazon\.com/images/[^"]+)"', resp.text)
        if match:
            image_url = match.group(1)

    if not name or not image_url:
        raise ValueError(f"Parsed name={name!r}, image={image_url!r}. Incomplete.")

    return {"product_name": name, "image_url": image_url, "error": None}


def scrape_with_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",   # critical for Docker /dev/shm limits
                "--disable-gpu",
                "--single-process",
            ],
        )
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        name = page.locator("#productTitle").first.inner_text().strip()

        # Trigger image load
        image_url = page.evaluate("""() => {
            const img = document.querySelector('#landingImage, #imgBlkFront');
            return img ? (img.getAttribute('data-old-hires') || img.src) : null;
        }""")

        browser.close()

    if not name or not image_url:
        raise ValueError("Playwright extraction incomplete.")

    return {"product_name": name, "image_url": image_url, "error": None}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No URL provided.", "product_name": None, "image_url": None}))
        sys.exit(1)

    target_url = sys.argv[1]
    result = {}

    try:
        result = scrape_with_requests(target_url)
    except Exception as e1:
        try:
            result = scrape_with_playwright(target_url)
        except Exception as e2:
            result = {
                "product_name": None,
                "image_url": None,
                "error": f"requests: {e1} | playwright: {e2}",
            }

    print(json.dumps(result))
