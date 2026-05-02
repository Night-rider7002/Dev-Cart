#!/usr/bin/env python3
"""
pinterest_auth.py
Run this LOCALLY to get your PINTEREST_TOKEN.
"""
import requests
import urllib.parse

# 1. Get these from https://developers.pinterest.com/apps/
CLIENT_ID     = input("Enter Pinterest App ID: ").strip()
CLIENT_SECRET = input("Enter Pinterest App Secret: ").strip()
REDIRECT_URI  = "https://localhost"

def main():
    # Phase 1: Get Auth URL
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "pins:read,pins:write,boards:read,boards:write"
    }
    auth_url = f"https://www.pinterest.com/oauth/?{urllib.parse.urlencode(params)}"
    
    print("\n1. Open this URL in your browser to authorize:")
    print(auth_url)
    print("\n2. After authorizing, you will be redirected to a 'localhost' page.")
    print("3. Copy the 'code' parameter from that URL (the part after ?code=)")
    
    code_url = input("\nPaste the FULL redirect URL here: ").strip()
    
    # Extract code
    code = code_url
    if "code=" in code_url:
        code = code_url.split("code=")[1].split("&")[0]

    # Phase 2: Exchange Code for Token
    print("\nExchanging code for token...")
    resp = requests.post(
        "https://api.pinterest.com/v5/oauth/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print("\n✅ SUCCESS!")
        print(f"PINTEREST_TOKEN: {data.get('access_token')}")
        print("\nSave this as a secret in your GitHub Repo.")
    else:
        print("\n❌ FAILED")
        print(resp.text)

if __name__ == "__main__":
    main()
