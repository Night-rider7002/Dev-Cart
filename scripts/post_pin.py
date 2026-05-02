#!/usr/bin/env python3
"""
post_pin.py
Orchestrates the Pinterest posting process:
1. Reads Pending products with live Landing Pages from Sheet.
2. Scrapes product details & generates a Pinterest-optimized image.
3. Uploads image to Pinterest and creates a Pin linking to the landing page.
4. Updates Sheet status to 'Published'.
"""

import os, json, requests, time, sys
from google.oauth2.service_account import Credentials
import gspread

# Import logic from sibling scripts
# We'll wrap these in functions or just copy the core logic for reliability in GHA
from scrape_product import scrape_with_requests, scrape_with_playwright
from generate_pin_image import download_image, fit_and_crop, add_gradient_overlay, render_text, add_brand_badge, PIN_W, PIN_H

# ── Config ────────────────────────────────────────────────────────────
SHEET_ID           = os.environ["SHEET_ID"]
PINTEREST_TOKEN    = os.environ["PINTEREST_TOKEN"]
PINTEREST_BOARD_ID = os.environ["PINTEREST_BOARD_ID"]
GCP_CREDS_JSON     = os.environ["GCP_CREDS_JSON"]

def get_sheet():
    creds = Credentials.from_service_account_info(
        json.loads(GCP_CREDS_JSON),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds).open_by_key(SHEET_ID).sheet1

def upload_pin_to_pinterest(image_path, title, description, link):
    """
    Pinterest V5 API flow: 
    1. For simplicity with GitHub Actions, we use 'image_url' source if possible.
    2. However, since we generate a local image, we either need to host it 
       or use the Base64/Multipart upload if the API supports it.
    
    Update: Pinterest V5 'pins' endpoint supports 'image_url' for media_source.
    But since our image is local, we'd normally need to upload to 'media' first.
    To keep it simple for this script, we will use the 'image_url' from Amazon 
    directly if image generation is skipped, OR we assume the user wants 
    the high-quality generated one.
    """
    
    # Header for API
    headers = {
        "Authorization": f"Bearer {PINTEREST_TOKEN}",
        "Content-Type": "application/json"
    }

    # For this implementation, we use the original image_url for the pin 
    # to avoid needing a public host for the generated .jpg in the CI environment.
    # In a full setup, you'd push the .jpg to GitHub Pages first then link it.
    
    payload = {
        "board_id": PINTEREST_BOARD_ID,
        "title": title[:100],
        "description": description[:500] + " #ad",
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": image_path  # We'll pass the original URL for now
        }
    }

    resp = requests.post("https://api.pinterest.com/v5/pins", headers=headers, json=payload)
    if resp.status_code not in [200, 201]:
        print(f"Pinterest Error: {resp.text}")
        return None
    return resp.json().get("id")

def main():
    sheet = get_sheet()
    rows = sheet.get_all_records()
    
    count = 0
    max_batch = 3 # stay safe with rate limits
    
    for i, row in enumerate(rows):
        if count >= max_batch: break
        
        # Check if product is ready to be pinned
        status = row.get("Status", "Pending")
        page_url = row.get("Page_URL")
        category = row.get("Category", "Gadgets")
        url = row.get("URL")
        
        if status == "Pending" and page_url:
            print(f"Processing: {url}")
            
            try:
                # 1. Scrape
                data = {}
                try:
                    data = scrape_with_requests(url)
                except Exception as e:
                    print(f"  Requests scrape failed, trying Playwright: {e}")
                    data = scrape_with_playwright(url)
                
                if not data.get("product_name"):
                    print(f"  Skipping: Scraping failed for {url}")
                    continue
                
                title = data["product_name"]
                img_url = data["image_url"]
                
                # 3. Post to Pinterest
                pin_id = upload_pin_to_pinterest(
                    image_path=img_url, 
                    title=f"Best {category}: {title[:50]}",
                    description=f"Check out this essential {category} for engineering students! Found on Hostel Engineer Picks.",
                    link=page_url
                )
                
                if pin_id:
                    print(f"Pin Created: {pin_id}")
                    # Update Sheet: Status (Col D), Pin_ID (Col E), Published_At (Col F)
                    row_idx = i + 2
                    sheet.update_cell(row_idx, 4, "Published")
                    sheet.update_cell(row_idx, 5, pin_id)
                    sheet.update_cell(row_idx, 6, time.strftime("%Y-%m-%d %H:%M:%S"))
                    count += 1
                
                time.sleep(5) # Delay between pins
                
            except Exception as e:
                print(f"Error processing {url}: {e}")

if __name__ == "__main__":
    main()
