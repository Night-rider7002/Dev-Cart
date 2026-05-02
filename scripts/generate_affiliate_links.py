#!/usr/bin/env python3
"""
generate_affiliate_links.py
Converts a list of Amazon URLs into affiliate links.
Outputs a CSV ready for import into the master Google Sheet.
"""

import csv

ASSOCIATE_TAG = "yourname-21"  # Replace with actual tag

# Add your products here
products = [
    {"url": "https://www.amazon.in/dp/B08L5TNJHG", "category": "Tech Gadgets"},
    {"url": "https://www.amazon.in/dp/B07PXGQC1Q", "category": "Study & Desk Setup"},
    {"url": "https://www.amazon.in/dp/B09G9HD6PD", "category": "Room Essentials"},
]

def make_affiliate_link(amazon_url, tag):
    if "/dp/" in amazon_url:
        asin = amazon_url.split("/dp/")[1].split("/")[0].split("?")[0]
    else:
        asin = amazon_url.strip()
    return f"https://www.amazon.in/dp/{asin}?tag={tag}"

def main():
    rows = []
    print("Generating affiliate links...")
    for p in products:
        affiliate = make_affiliate_link(p["url"], ASSOCIATE_TAG)
        print(f"✅ {affiliate}")
        rows.append({
            "URL": p["url"],
            "Category": p["category"],
            "Affiliate_Link": affiliate,
            "Status": "Pending",
            "Pin_ID": "",
            "Published_At": "",
            "Page_URL": ""
        })

    if rows:
        with open("affiliate_links.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nDone. {len(rows)} affiliate links saved to affiliate_links.csv")

if __name__ == "__main__":
    main()
