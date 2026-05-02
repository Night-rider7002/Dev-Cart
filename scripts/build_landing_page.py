#!/usr/bin/env python3
"""
build_landing_page.py
Groups products by category.
Generates SEO-optimized HTML landing pages via Gemini.
Pushes to GitHub Pages via GitHub API.
Updates Sheet with Page_URL.
"""

import os, json, requests, base64, time
from google.oauth2.service_account import Credentials
import gspread

SHEET_ID       = os.environ["SHEET_ID"]
GEMINI_KEY     = os.environ["GEMINI_KEY"]
GITHUB_TOKEN   = os.environ["PAT_TOKEN"]
GITHUB_REPO    = os.environ["GITHUB_REPO"]  # format: "username/reponame"
ASSOCIATE_TAG  = os.environ["AMAZON_ASSOCIATE_TAG"]
GCP_CREDS_JSON = os.environ["GCP_CREDS_JSON"]

def get_sheet():
    creds = Credentials.from_service_account_info(
        json.loads(GCP_CREDS_JSON),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds).open_by_key(SHEET_ID).sheet1

def generate_page_html(category: str, products: list[dict]) -> str:
    """Call Gemini to write the page copy, then inject into HTML template."""
    product_list = "\n".join([
        f"- {p.get('product_name', p['url'])} (₹{p.get('price', 'Check Price')})"
        for p in products[:10]
    ])

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"""
You are writing SEO content for an affiliate landing page targeting engineering students in Indian hostels.
Category: {category}
Products: {product_list}

Return ONLY a JSON object with these fields:
{{
  "page_title": "SEO title under 60 chars",
  "meta_description": "SEO meta description under 155 chars",
  "hero_heading": "H1 heading under 70 chars",
  "hero_subtext": "2 sentence intro paragraph",
  "product_intros": ["one sentence intro for each product in same order as input list"]
}}
"""
    resp = requests.post(gemini_url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    }, timeout=15)

    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    raw = raw.replace("```json", "").replace("```", "").strip()
    copy = json.loads(raw)

    # Build product cards HTML
    product_cards = ""
    intros = copy.get("product_intros", [""] * len(products))
    for i, p in enumerate(products[:10]):
        asin = p['url'].split("/dp/")[1].split("/")[0] if "/dp/" in p['url'] else ""
        intro = intros[i] if i < len(intros) else ""
        product_cards += f"""
        <div class="product-card">
            <img src="{p.get('image_url', '')}" alt="{p.get('product_name', 'Product')}">
            <div class="card-body">
                <h3>{p.get('product_name', 'Product')}</h3>
                <p class="intro">{intro}</p>
                <p class="price">₹{p.get('price', 'Check Price')}</p>
                <a href="{p['affiliate_link']}" class="cta-btn" target="_blank" rel="nofollow sponsored">
                    Check Price on Amazon →
                </a>
            </div>
        </div>"""

    # Full page HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{copy['page_title']}</title>
    <meta name="description" content="{copy['meta_description']}">
    <meta property="og:title" content="{copy['page_title']}">
    <meta property="og:description" content="{copy['meta_description']}">
    <link rel="canonical" href="https://{GITHUB_REPO.split('/')[0]}.github.io/{GITHUB_REPO.split('/')[1]}/pages/{category.lower().replace(" ", "-").replace("/", "-")}.html">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: #f8f9fa; color: #212529; }}
        header {{ background: #e63946; color: white; padding: 2rem; text-align: center; }}
        header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        header p {{ opacity: 0.9; font-size: 1.1rem; }}
        .disclosure {{ background: #fff3cd; border: 1px solid #ffc107; padding: 0.75rem 1rem; text-align: center; font-size: 0.85rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        .product-card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: transform 0.2s; }}
        .product-card:hover {{ transform: translateY(-4px); }}
        .product-card img {{ width: 100%; height: 220px; object-fit: contain; background: #f8f9fa; padding: 1rem; }}
        .card-body {{ padding: 1.2rem; }}
        .card-body h3 {{ font-size: 0.95rem; margin-bottom: 0.5rem; line-height: 1.4; }}
        .intro {{ font-size: 0.85rem; color: #6c757d; margin-bottom: 0.75rem; }}
        .price {{ font-size: 1.1rem; font-weight: 700; color: #e63946; margin-bottom: 1rem; }}
        .cta-btn {{ display: block; background: #ff9900; color: white; text-align: center; padding: 0.7rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9rem; }}
        .cta-btn:hover {{ background: #e68900; }}
        footer {{ text-align: center; padding: 2rem; color: #6c757d; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <header>
        <h1>{copy['hero_heading']}</h1>
        <p>{copy['hero_subtext']}</p>
    </header>
    <div class="disclosure">
        ⚠️ <strong>Affiliate Disclosure:</strong> This page contains affiliate links. 
        We may earn a small commission if you purchase, at no extra cost to you. #ad
    </div>
    <div class="grid">
        {product_cards}
    </div>
    <footer>
        <p>© 2025 Hostel Engineer Picks | Amazon affiliate links disclosed above</p>
    </footer>
</body>
</html>"""
    return html

def push_to_github(filename: str, html: str) -> str:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/pages/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    existing = requests.get(url, headers=headers)
    sha = existing.json().get("sha") if existing.status_code == 200 else None

    payload = {
        "message": f"auto: update {filename}",
        "content": base64.b64encode(html.encode()).decode(),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload)
    username = GITHUB_REPO.split("/")[0]
    reponame = GITHUB_REPO.split("/")[1]
    page_url = f"https://{username}.github.io/{reponame}/pages/{filename}"
    return page_url

def main():
    sheet = get_sheet()
    rows = sheet.get_all_records()

    # Group pending products by category
    categories = {}
    for i, row in enumerate(rows):
        if row.get("Status") == "Pending" and not row.get("Page_URL"):
            cat = row.get("Category", "General")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({"row_index": i + 2, **row})

    for category, products in categories.items():
        print(f"Building page for: {category} ({len(products)} products)")
        html = generate_page_html(category, products)
        filename = category.lower().replace(" ", "-").replace("/", "-") + ".html"
        page_url = push_to_github(filename, html)
        print(f"Published: {page_url}")

        # Write Page_URL back to sheet for each product in this category
        for p in products:
            sheet.update_cell(p["row_index"], 7, page_url)  # Column G = Page_URL

        time.sleep(2)  # avoid Gemini rate limit

if __name__ == "__main__":
    main()
