# Dev Cart — Affiliate Engine Project Context

## What This Project Does
Automated Amazon affiliate marketing engine that:
1. Discovers products from Amazon via scraping
2. Generates Pinterest pins (image + title + description) using Gemini AI
3. Publishes pins to Pinterest via API
4. Hosts affiliate landing pages on GitHub Pages
5. Tracks everything in Google Sheet

## Tech Stack
- Python scripts running on GitHub Actions (free)
- Gemini 1.5 Flash API for content generation (free)
- PIL/Pillow for pin image generation (1000x1500px)
- Pinterest API v5 for posting pins
- GitHub Pages for landing pages
- Google Sheets as database

## File Structure
affiliate-engine/
├── .github/workflows/affiliate_engine.yml
├── pages/                    # HTML landing pages
├── scripts/
│   ├── discover_products.py  # finds Amazon products, generates affiliate links
│   ├── build_landing_page.py # creates HTML pages, pushes to GitHub
│   ├── post_pin.py           # generates image + posts to Pinterest
│   ├── scrape_product.py     # scrapes Amazon product name + image URL
│   └── generate_pin_image.py # PIL image compositor (1000x1500)
├── index.html                # homepage
└── privacy.html              # required for Pinterest app

## Environment Variables / Secrets Needed
SHEET_ID              = Google Sheet ID
AMAZON_ASSOCIATE_TAG  = Amazon tag (format: name-21)
GEMINI_KEY            = Gemini API key
GCP_CREDS_JSON        = Google service account JSON
PINTEREST_TOKEN       = Pinterest OAuth access token
PINTEREST_BOARD_ID    = Pinterest board ID
PAT_TOKEN             = GitHub Personal Access Token
GITHUB_REPO           = username/reponame

## Current Status
- Google Sheet: set up with columns URL, Category, Affiliate_Link, 
  Status, Pin_ID, Published_At, Page_URL
- GCP Service Account: created, JSON key downloaded
- Gemini API key: obtained
- GitHub repo: created at https://night-rider7002.github.io/Dev-cart/
- Pinterest app: REJECTED — needs reapplication after building 
  account activity
- Amazon Associates: approved, have associate tag
- Pinterest token: pending app approval

## Known Issues to Fix
- Pinterest API rejected — using manual upload as interim solution
- Amazon PA-API not yet available (needs 3 qualifying sales first)
- Currently scraping Amazon search pages directly for product URLs

## Pin Strategy
- 15 pins per day
- Post between 8-11 PM IST
- 80/20 rule: 80% value content, 20% affiliate pins
- Sandbox period first 60 days: start with 3-5 pins/day
- All pins link to GitHub Pages landing page, NOT direct affiliate link
- Every description ends with: #ad (legal requirement)

## Target Audience
Engineering students and developers in India
Living in hostels or rented accommodation
Budget conscious, tech savvy
Keywords: hostel essentials, dev setup, student gadgets india