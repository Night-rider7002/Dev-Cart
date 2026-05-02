#!/usr/bin/env python3
"""
get_asins.py
Bulk scrapes Amazon search results for ASINs based on keywords.
Useful for seeding the project without PA-API.
"""

import requests, time
from bs4 import BeautifulSoup

ASSOCIATE_TAG = "yourname-21"

KEYWORDS = [
    "study lamp for students",
    "laptop stand portable",
    "scientific calculator",
    "usb hub laptop",
    "noise cancelling earphones",
    "portable fan small",
    "power bank fast charging",
    "desk organizer",
    "extension cord board",
    "water bottle insulated"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

def main():
    all_links = []
    print(f"Scraping ASINs for {len(KEYWORDS)} keywords...")

    for keyword in KEYWORDS:
        search_url = f"https://www.amazon.in/s?k={keyword.replace(' ', '+')}"
        print(f"  Searching: {keyword}")
        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")

            for a in soup.select("a.a-link-normal[href*='/dp/']"):
                href = a.get("href", "")
                if "/dp/" not in href: continue
                asin = href.split("/dp/")[1].split("/")[0].split("?")[0]
                if len(asin) == 10 and asin not in [x["asin"] for x in all_links]:
                    all_links.append({
                        "asin": asin,
                        "url": f"https://www.amazon.in/dp/{asin}",
                        "affiliate_link": f"https://www.amazon.in/dp/{asin}?tag={ASSOCIATE_TAG}",
                        "category": keyword.title(),
                        "status": "Pending"
                    })
            time.sleep(2)
        except Exception as e:
            print(f"    Error: {e}")

    print(f"\nFound {len(all_links)} products.")
    # In a real run, you'd save this to CSV or append to Sheet
    with open("discovered_asins.txt", "w") as f:
        for item in all_links:
            f.write(f"{item['url']}\t{item['category']}\n")
    print("Saved to discovered_asins.txt")

if __name__ == "__main__":
    main()
