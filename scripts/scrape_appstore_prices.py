#!/usr/bin/env python3
"""
StravaRank - Automated App Store In-App Purchases Price Scraper
Scrapes official Strava subscription prices directly from Apple App Store regional pages.
"""

import json
import os
import re
import sys
import time
import urllib.request

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "data.json")

# Country ID to App Store country code mapping
COUNTRY_MAP = {
    "US": "us", "JP": "jp", "TR": "tr", "GB": "gb", "MX": "mx",
    "BR": "br", "ID": "id", "IN": "in", "PH": "ph", "ZA": "za",
    "VN": "vn", "TH": "th", "PL": "pl", "TW": "tw", "KR": "kr",
    "FR": "fr", "AU": "au", "SG": "sg", "CA": "ca", "NZ": "nz",
    "DE": "de", "NO": "no", "SE": "se", "CH": "ch", "CO": "co",
    "EG": "eg", "NG": "ng"
}

def clean_price(price_str):
    """Parse raw localized price string into float number"""
    # e.g., '₺799,99' -> 799.99, '¥7,800' -> 7800.0, '$79.99' -> 79.99
    s = price_str.replace(" ", "").replace("\xa0", "")
    # Remove currency symbols and non-digits/periods/commas
    clean = re.sub(r"[^\d.,]", "", s)
    if not clean:
        return 0.0

    # European style 1.299,00 or 799,99
    if "," in clean and "." in clean:
        if clean.rfind(",") > clean.rfind("."):
            # 1.599,99
            clean = clean.replace(".", "").replace(",", ".")
        else:
            # 1,599.99
            clean = clean.replace(",", "")
    elif "," in clean:
        # Check if comma is decimal separator (e.g. 799,99) or thousands separator (7,800)
        parts = clean.split(",")
        if len(parts[-1]) == 2:
            clean = clean.replace(",", ".")
        else:
            clean = clean.replace(",", "")

    try:
        return float(clean)
    except:
        return 0.0

def scrape_storefront(country_code):
    url = f"https://apps.apple.com/{country_code}/app/id426826309"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="ignore")
                pairs = re.findall(r'<div class="text-pair[^"]*">\s*<span>([^<]+)</span>\s*<span>([^<]+)</span>', html)
                return pairs
    except Exception as e:
        return []

def run_scraper(dry_run=False):
    print("🚀 Starting Apple App Store Official Price Scraper...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    countries = data.get("countries", [])
    changed_records = []

    for c in countries:
        cid = c["id"]
        store_code = COUNTRY_MAP.get(cid)
        if not store_code:
            continue

        print(f"  Fetching {c['country']} ({cid} / {store_code})...", end="", flush=True)
        pairs = scrape_storefront(store_code)
        if not pairs:
            print(" ⚠ Storefront unavailable")
            time.sleep(0.5)
            continue

        annual_candidates = []
        monthly_candidates = []
        family_candidates = []

        for name, price_str in pairs:
            price_val = clean_price(price_str)
            if price_val <= 0:
                continue
            name_lower = name.lower()
            if "family" in name_lower:
                family_candidates.append(price_val)
            elif "month" in name_lower or "1 month" in name_lower:
                monthly_candidates.append(price_val)
            elif "year" in name_lower or "annual" in name_lower or "1 year" in name_lower:
                annual_candidates.append(price_val)
            elif "subscription" in name_lower:
                # Strava subscription tiers: usually smaller one is monthly, bigger one is annual
                annual_candidates.append(price_val)

        # Distinguish annual vs monthly
        detected_annual = None
        detected_monthly = None
        detected_family = family_candidates[0] if family_candidates else None

        if annual_candidates:
            annual_candidates.sort()
            # If multiple subscription prices, smaller is monthly, larger is annual
            if len(annual_candidates) >= 2 and not monthly_candidates:
                detected_monthly = annual_candidates[0]
                detected_annual = annual_candidates[-1]
            else:
                detected_annual = annual_candidates[-1]

        if monthly_candidates:
            detected_monthly = min(monthly_candidates)

        print(f" ✓ Annual: {detected_annual} | Monthly: {detected_monthly}")

        # Check for changes
        old_annual = c.get("annual")
        if detected_annual and detected_annual != old_annual:
            changed_records.append({
                "country": c["country"],
                "code": cid,
                "old_annual": old_annual,
                "new_annual": detected_annual
            })
            if not dry_run:
                c["annual"] = detected_annual
                if detected_monthly:
                    c["monthly"] = detected_monthly
                if detected_family:
                    c["family_annual"] = detected_family

        time.sleep(0.6)

    print(f"\n📊 Scrape complete! {len(changed_records)} price changes detected.")
    for ch in changed_records:
        print(f"  * {ch['country']} ({ch['code']}): {ch['old_annual']} -> {ch['new_annual']}")

    if changed_records and not dry_run:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("💾 Updated data.json with new official prices.")

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_scraper(dry_run=is_dry)
