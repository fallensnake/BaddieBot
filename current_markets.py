import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import requests

def fetch_current_kalshi_markets(target_categories, max_per_category=30):
    """
    Fetches active Kalshi markets and filters them by category AND price (10c-90c).
    """
    # ... [API CONFIGURATION remains the same] ...
    base_url = "https://api.elections.kalshi.com/trade-api/v2/events"
    params = { "limit": 100, "status": "open", "with_nested_markets": "true" }
    headers = { "User-Agent": "KalshiScout/2.0", "Accept": "application/json" }

    target_cats_lower = [c.lower() for c in target_categories]
    categorized_markets = defaultdict(list)
    
    print(f"🔍 SCOUT: Searching for {', '.join(target_categories)} (Price: 10¢-90¢)...")

    cursor = None
    has_more_pages = True
    page_count = 0

    while has_more_pages:
        if cursor: params["cursor"] = cursor

        try:
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code != 200: break

            data = response.json()
            events = data.get("events", [])
            cursor = data.get("cursor")

            if not events: break
            page_count += 1

            for event in events:
                event_cat = event.get("category", "Uncategorized")
                if event_cat.lower() not in target_cats_lower: continue
                if len(categorized_markets[event_cat]) >= max_per_category: continue

                raw_markets = event.get("markets", [])
                sorted_markets = sorted(raw_markets, key=lambda x: x.get("volume", 0), reverse=True)

                for market in sorted_markets:
                    if len(categorized_markets[event_cat]) >= max_per_category: break
                    
                    yes_price = market.get("yes_ask", 0)

                    # --- 🛡️ PRICE TRAP FILTER ---
                    # Skip if price is too low (<10c) or too high (>90c)
                    if yes_price < 10 or yes_price > 90:
                        continue
                    # -----------------------------

                    clean_market = {
                        "ticker": market.get("ticker"),
                        "event_title": event.get("title"),
                        "option_name": market.get("title") or market.get("subtitle"),
                        "category": event_cat,
                        "expiration": market.get("expiration_time"),
                        "yes_ask": yes_price,
                        "volume": market.get("volume", 0),
                        "liquidity": market.get("liquidity", 0),
                        "event_id": event.get("event_ticker")
                    }
                    
                    categorized_markets[event_cat].append(clean_market)

            # Check if full
            all_full = True
            for cat in target_categories:
                # Count explicitly to be safe
                count = sum(1 for k in categorized_markets if k.lower() == cat.lower())
                if count < max_per_category:
                    all_full = False
                    break
            
            if all_full: has_more_pages = False
            elif not cursor: has_more_pages = False
            else: time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Exception: {e}")
            has_more_pages = False

    return categorized_markets

def get_daily_markets(max_markets=30):
    """
    Fetches active Kalshi markets expiring < 24h.
    Filters out extreme odds (<10% or >90%).
    """
    # ... [API CONFIGURATION & TIME CALCS remain the same] ...
    base_url = "https://api.elections.kalshi.com/trade-api/v2/events"
    params = { "limit": 100, "status": "open", "with_nested_markets": "true" }
    headers = { "User-Agent": "KalshiScout/2.0", "Accept": "application/json" }

    now = datetime.now(timezone.utc)
    cutoff_time = now + timedelta(hours=24)
    
    print(f"⏰ SCOUT: Searching for daily markets (Price: 10¢-90¢)...")

    daily_candidates = []
    cursor = None
    has_more_pages = True
    page_count = 0

    while has_more_pages:
        if cursor: params["cursor"] = cursor

        try:
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code != 200: break

            data = response.json()
            events = data.get("events", [])
            cursor = data.get("cursor")

            if not events: break
            page_count += 1

            for event in events:
                raw_markets = event.get("markets", [])
                
                for market in raw_markets:
                    expiration_str = market.get("expiration_time")
                    if not expiration_str: continue

                    try:
                        exp_dt = datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
                    except ValueError: continue
                    
                    # 1. Time Filter (< 24h)
                    if now < exp_dt <= cutoff_time:
                        
                        yes_price = market.get("yes_ask", 0)

                        # --- 🛡️ PRICE TRAP FILTER ---
                        # Skip strictly < 10 or > 90
                        if yes_price < 10 or yes_price > 90:
                            continue
                        # -----------------------------

                        clean_market = {
                            "ticker": market.get("ticker"),
                            "event_title": event.get("title"),
                            "option_name": market.get("title") or market.get("subtitle"),
                            "category": event.get("category"),
                            "expiration": exp_dt, 
                            "expiration_str": expiration_str, 
                            "yes_ask": yes_price,
                            "volume": market.get("volume", 0),
                            "liquidity": market.get("liquidity", 0)
                        }
                        
                        daily_candidates.append(clean_market)

            if not cursor: has_more_pages = False
            else: time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Exception: {e}")
            has_more_pages = False

    # Sort by soonest expiration
    daily_candidates.sort(key=lambda x: x['expiration'])
    
    final_markets = daily_candidates[:max_markets]

    print(f"✅ Found {len(daily_candidates)} valid markets. Returning top {len(final_markets)}.")
    return final_markets
# --- TEST RUN ---
if __name__ == "__main__":
    # Example Usage
    my_cats = ["Sports","Politics", "Economics",'Climate']
    results = fetch_current_kalshi_markets(my_cats, 30)
    print(results)