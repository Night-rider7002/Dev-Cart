#!/usr/bin/env python3
"""
discover_products.py
Fetches products from Amazon PA-API + Bestseller pages.
Deduplicates against existing Sheet data.
Appends new rows with Status=Pending.
"""

import os, json, requests, time, hashlib
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
import gspread

# ── Config ────────────────────────────────────────────────────────────
SHEET_ID       = os.environ["SHEET_ID"]
ASSOCIATE_TAG  = os.environ["AMAZON_ASSOCIATE_TAG"]
GEMINI_KEY     = os.environ["GEMINI_KEY"]
GCP_CREDS_JSON = os.environ["GCP_CREDS_JSON"]  # service account JSON as string

KEYWORDS = [
    "hostel room essentials india",
    "engineering student gadgets under 500",
    "study lamp led students",
    "laptop stand portable",
    "scientific calculator college",
    "portable fan hostel",
    "noise cancelling earphones study",
    "usb hub laptop students",
    "mini whiteboard desk",
    "cable organizer desk students",
    "extension board hostel",
    "power bank fast charging",
    "water bottle insulated college",
    "desk organizer study table",
    "blue light glasses students"
]

BESTSELLER_URLS = [
    "https://www.amazon.in/gp/bestsellers/electronics/",
    "https://www.amazon.in/gp/bestsellers/computers/",
    "https://www.amazon.in/gp/new-releases/office-products/",
    "https://www.amazon.in/gp/movers-and-shakers/electronics/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

# ── Google Sheets connection ──────────────────────────────────────────
def get_sheet():
    creds_dict = json.loads(GCP_CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def get_existing_asins(sheet) -> set:
    urls = sheet.col_values(1)  # Column A = URL
    asins = set()
    for url in urls:
        if "/dp/" in url:
            asin = url.split("/dp/")[1].split("/")[0].split("?")[0]
            asins.add(asin)
    return asins

# ── Scrape bestseller pages ───────────────────────────────────────────
def scrape_bestsellers(category_url: str) -> list[dict]:
    products = []
    try:
        resp = requests.get(category_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.select("a.a-link-normal[href*='/dp/']"):
            href = a.get("href", "")
            if "/dp/" not in href:
                continue
            asin = href.split("/dp/")[1].split("/")[0]
            if len(asin) != 10:
                continue
            # Get category from URL
            parts = category_url.rstrip("/").split("/")
            category = parts[-1].replace("-", " ").title()
            affiliate_url = f"https://www.amazon.in/dp/{asin}?tag={ASSOCIATE_TAG}"
            products.append({
                "url": f"https://www.amazon.in/dp/{asin}",
                "affiliate_link": affiliate_url,
                "category": category,
                "asin": asin
            })
        time.sleep(3)  # rate limit courtesy delay
    except Exception as e:
        print(f"Bestseller scrape failed for {category_url}: {e}")
    return products

# ── Categorize with Gemini ────────────────────────────────────────────
def categorize_product(product_name: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": (
            f"Product: {product_name}\n"
            "Return ONLY one category from this list that best fits the product:\n"
            "Study & Desk Setup, Tech Gadgets, Room Essentials, Health & Fitness, "
            "Kitchen & Food, Books & Stationery, Clothing & Accessories\n"
            "Return just the category name, nothing else."
        )}]}]
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        res_json = resp.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print(f"Gemini Categorization Error: {json.dumps(res_json)}")
            return "General"
    except Exception as e:
        print(f"Categorization failed for {product_name}: {e}")
        return "General"

# ── Main ──────────────────────────────────────────────────────────────
def main():
    sheet = get_sheet()
    existing_asins = get_existing_asins(sheet)
    print(f"Existing ASINs in sheet: {len(existing_asins)}")

    new_rows = []
    seen_asins = set()

    # Source 1: Bestseller pages
    for url in BESTSELLER_URLS:
        products = scrape_bestsellers(url)
        for p in products:
            if p["asin"] not in existing_asins and p["asin"] not in seen_asins:
                seen_asins.add(p["asin"])
                new_rows.append([
                    p["url"],
                    p["category"],
                    p["affiliate_link"],
                    "Pending",
                    "",  # Pin_ID
                    "",  # Published_At
                    "",  # Page_URL
                ])

    print(f"New products found: {len(new_rows)}")

    # Batch append to sheet (avoid hitting Sheets API rate limit)
    if new_rows:
        sheet.append_rows(new_rows, value_input_option="RAW")
        print(f"Appended {len(new_rows)} rows to sheet.")

if __name__ == "__main__":
    main()
