#!/usr/bin/env python3
"""
StravaRank - Automated App Store In-App Purchases Price Scraper
Scrapes official Strava subscription prices directly from Apple App Store regional pages.
"""

import json
import html as html_lib
import os
import re
import sys
import time
import urllib.request

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "data.json")
APP_ID = "426826309"
APP_SLUG = "strava-run-bike-walk"
PRICE_PATTERN = r"(?:[^\d\r\n]{1,8}\s*)?\d[\d.,\s]*(?:ribu|rb|천|만|万)?"

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
    lower = s.lower()
    multiplier = 1
    if "ribu" in lower or re.search(r"(?:^|\d)rb$", lower):
        multiplier = 1_000
    elif "천" in s:
        multiplier = 1_000
    elif "만" in s or "万" in s:
        multiplier = 10_000

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
    elif "." in clean:
        # Some storefronts use a dot as a thousands separator (e.g. Rp 449.000).
        parts = clean.split(".")
        if len(parts[-1]) == 3 and all(parts):
            clean = clean.replace(".", "")

    try:
        return float(clean) * multiplier
    except:
        return 0.0

def extract_price_pairs(page_text):
    """Extract product name and price pairs from current and legacy App Store markup."""
    text = html_lib.unescape(page_text)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = text.replace("\xa0", " ")

    pairs = []

    # Legacy App Store markup.
    legacy_pairs = re.findall(
        r'<div class="text-pair[^"]*">\s*<span>([^<]+)</span>\s*'
        r"<span>([^<]+)</span>",
        page_text,
    )
    pairs.extend(legacy_pairs)

    # Current App Store pages render entries such as "Subscription₺799,99".
    product_pattern = re.compile(
        rf"^[ \t*•-]*(?P<name>Strava(?:\s*\+\s*Runna)?\s+Subscription|"
        rf"Family Plan Subscription|Subscription|1\s+(?:Month|Year))"
        rf"\s*(?P<price>{PRICE_PATTERN})",
        re.IGNORECASE | re.MULTILINE,
    )
    for match in product_pattern.finditer(text):
        name = re.sub(r"\s+", " ", match.group("name")).strip()
        price = re.sub(r"\s+", " ", match.group("price")).strip()
        pairs.append((name, price))

    deduped = []
    seen = set()
    for name, price in pairs:
        key = (name.strip(), price.strip())
        if key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped

def fetch_page(url, headers=None):
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.geturl(), resp.read().decode("utf-8", errors="ignore")

def scrape_storefront(country_code):
    direct_url = f"https://apps.apple.com/{country_code}/app/{APP_SLUG}/id{APP_ID}?l=en-US"
    try:
        final_url, page = fetch_page(direct_url)
        pairs = extract_price_pairs(page)
        if pairs and f"/{country_code}/" in final_url.lower():
            return pairs
    except Exception:
        pass

    # Apple can redirect requests to the account's storefront. Jina renders the
    # requested regional page as text so the weekly check still works from CN.
    try:
        rendered_url = (
            f"https://r.jina.ai/http://apps.apple.com/{country_code}/app/"
            f"{APP_SLUG}/id{APP_ID}?l=en-US"
        )
        _, rendered = fetch_page(rendered_url, headers={"Accept": "text/plain"})
        return extract_price_pairs(rendered)
    except Exception:
        return []

def run_scraper(dry_run=False, country_filter=None):
    print("🚀 Starting Apple App Store Official Price Scraper...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    countries = data.get("countries", [])
    changed_records = []

    for c in countries:
        cid = c["id"]
        if country_filter and cid.upper() != country_filter.upper():
            continue
        store_code = COUNTRY_MAP.get(cid)
        if not store_code:
            continue

        print(f"  Fetching {c['country']} ({cid} / {store_code})...", end="", flush=True)
        pairs = scrape_storefront(store_code)
        if not pairs:
            print(" ⚠ Storefront unavailable")
            time.sleep(0.5)
            continue

        subscription_candidates = []
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
            elif "runna" in name_lower:
                continue
            elif "month" in name_lower or "1 month" in name_lower:
                monthly_candidates.append(price_val)
            elif "year" in name_lower or "annual" in name_lower or "1 year" in name_lower:
                annual_candidates.append(price_val)
            elif "subscription" in name_lower:
                subscription_candidates.append(price_val)

        detected_annual = None
        detected_monthly = None
        detected_family = family_candidates[0] if family_candidates else None

        subscription_candidates = sorted(set(subscription_candidates))
        if subscription_candidates:
            detected_monthly = subscription_candidates[0]
            detected_annual = subscription_candidates[-1]

        if annual_candidates and not subscription_candidates:
            detected_annual = max(annual_candidates)

        if monthly_candidates and not subscription_candidates:
            detected_monthly = min(monthly_candidates)

        print(f" ✓ Annual: {detected_annual} | Monthly: {detected_monthly}")

        changes = {}
        for field, new_value in (
            ("annual", detected_annual),
            ("monthly", detected_monthly),
            ("family_annual", detected_family),
        ):
            if new_value and new_value != c.get(field):
                changes[field] = (c.get(field), new_value)

        if changes:
            changed_records.append({
                "country": c["country"],
                "code": cid,
                "changes": changes,
            })
            if not dry_run:
                for field, (_, new_value) in changes.items():
                    c[field] = new_value

        time.sleep(0.6)

    print(f"\n📊 Scrape complete! {len(changed_records)} price changes detected.")
    for ch in changed_records:
        fields = ", ".join(
            f"{field}: {old} -> {new}"
            for field, (old, new) in ch["changes"].items()
        )
        print(f"  * {ch['country']} ({ch['code']}): {fields}")

    if changed_records and not dry_run:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("💾 Updated data.json with new official prices.")

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    filter_arg = next((arg for arg in sys.argv[1:] if arg.startswith("--country=")), None)
    country_filter = filter_arg.split("=", 1)[1] if filter_arg else None
    run_scraper(dry_run=is_dry, country_filter=country_filter)
