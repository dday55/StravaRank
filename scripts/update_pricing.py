#!/usr/bin/env python3
"""
StravaRank Automated Pricing & Exchange Rate Updater
- Pulls live daily foreign exchange rates from global financial APIs
- Updates data.json timestamps and currency rates
- Calculates latest USD and CNY conversions
- Zero external dependencies (uses standard python3 library)
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "data.json")

# Primary and Fallback Exchange Rate APIs (Free, Keyless, Daily updated)
API_PRIMARY = "https://open.er-api.com/v6/latest/USD"
API_FALLBACK = "https://api.frankfurter.app/latest?from=USD"

def fetch_live_rates():
    """Fetch live rates with automatic fallback"""
    headers = {"User-Agent": "StravaRank-Updater/1.0"}
    
    # 1. Try Primary API
    try:
        print(f"[1/3] Fetching live rates from primary API: {API_PRIMARY}...")
        req = urllib.request.Request(API_PRIMARY, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                rates = data.get("rates", {})
                if "CNY" in rates and "EUR" in rates:
                    print(f"  ✓ Successfully fetched {len(rates)} currencies.")
                    return rates
    except Exception as e:
        print(f"  ⚠ Primary API failed: {e}. Trying fallback...")

    # 2. Try Fallback API (European Central Bank)
    try:
        print(f"[1/3] Fetching live rates from fallback API: {API_FALLBACK}...")
        req = urllib.request.Request(API_FALLBACK, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                rates = data.get("rates", {})
                rates["USD"] = 1.0
                if "CNY" in rates:
                    print(f"  ✓ Successfully fetched {len(rates)} currencies from ECB.")
                    return rates
    except Exception as e:
        print(f"  ✗ Fallback API also failed: {e}")

    return None

def update_dataset():
    if not os.path.exists(DATA_PATH):
        print(f"Error: dataset file not found at {DATA_PATH}")
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # 1. Fetch live rates
    live_rates = fetch_live_rates()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if live_rates:
        print("[2/3] Updating exchange rates in data.json...")
        current_rates = dataset.get("rates", {})
        updated_count = 0
        for currency, old_val in current_rates.items():
            if currency in live_rates:
                new_val = round(float(live_rates[currency]), 4)
                if new_val != old_val:
                    updated_count += 1
                current_rates[currency] = new_val

        dataset["rates"] = current_rates
        dataset["updated_at"] = today_str
        print(f"  ✓ Updated {updated_count} exchange rate values. Timestamp: {today_str}")
    else:
        print("  ⚠ Could not fetch live rates. Preserving current rates.")

    # 2. Sort countries by updated annual price in CNY
    print("[3/3] Re-evaluating country rankings...")
    cny_rate = dataset["rates"].get("CNY", 7.23)
    baseline_usd = dataset.get("baseline", {}).get("annual_usd", 79.99)
    baseline_cny = baseline_usd * cny_rate

    countries = dataset.get("countries", [])
    for c in countries:
        curr = c["currency"]
        rate = dataset["rates"].get(curr, 1.0)
        c["price_usd_calc"] = round(c["annual"] / rate, 2)
        c["price_cny_calc"] = round(c["price_usd_calc"] * cny_rate, 1)
        c["savings_pct_calc"] = round(((c["price_usd_calc"] - baseline_usd) / baseline_usd) * 100, 1)

    # Sort countries from lowest price to highest
    countries.sort(key=lambda x: x["price_usd_calc"])
    for rank_idx, c in enumerate(countries, 1):
        c["rank"] = rank_idx

    dataset["countries"] = countries

    # 3. Write back atomically
    tmp_path = DATA_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, DATA_PATH)

    print(f"\n✨ Successfully updated data.json! (Total: {len(countries)} countries indexed)")
    print(f"   - CNY Exchange Rate: 1 USD = {cny_rate} CNY")
    print(f"   - Cheapest Country: {countries[0]['country']} ({countries[0]['symbol']}{countries[0]['annual']} ≈ ¥{countries[0]['price_cny_calc']} CNY)")
    turkey = next((country for country in countries if country["id"] == "TR"), None)
    if turkey:
        print(f"   - Turkey Price: ₺{turkey['annual']} TRY ≈ ¥{turkey['price_cny_calc']} CNY")

if __name__ == "__main__":
    update_dataset()
