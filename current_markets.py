import time
import requests
from collections import defaultdict

def fetch_current_kalshi_markets(target_categories, max_per_category=30):
    """
    Fetches active Kalshi markets and filters them by the requested categories.
    
    Args:
        target_categories (list): List of category strings (e.g., ["Politics", "Economics"])
        max_per_category (int): Max number of betting options to collect per category.
        
    Returns:
        dict: { "Politics": [market_obj, ...], "Economics": [...] }
    """
    # API CONFIGURATION
    base_url = "https://api.elections.kalshi.com/trade-api/v2/events"
    
    params = {
        "limit": 100,             # Max allowed by Kalshi per page
        "status": "open",         # Only active markets
        "with_nested_markets": "true" # CRITICAL: Gets all options (Yes/No tickers) inside the event
    }

    headers = {
        "User-Agent": "KalshiScout/2.0",
        "Accept": "application/json"
    }

    # Normalize categories for case-insensitive matching
    target_cats_lower = [c.lower() for c in target_categories]
    
    # Storage
    categorized_markets = defaultdict(list)
    
    print(f"🔍 SCOUT: Searching for {', '.join(target_categories)}...")

    cursor = None
    has_more_pages = True
    page_count = 0

    while has_more_pages:
        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(base_url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                break

            data = response.json()
            events = data.get("events", [])
            cursor = data.get("cursor")

            if not events:
                break

            page_count += 1
            print(f"  > Page {page_count}: Scanning {len(events)} events...")

            for event in events:
                # 1. Check Category
                event_cat = event.get("category", "Uncategorized")
                
                # Skip if this category is not in our target list
                if event_cat.lower() not in target_cats_lower:
                    continue
                
                # Skip if we are already full for this category
                if len(categorized_markets[event_cat]) >= max_per_category:
                    continue

                # 2. Extract Markets (Betting Options)
                # Sort markets by volume first so we get the most liquid options
                raw_markets = event.get("markets", [])
                sorted_markets = sorted(raw_markets, key=lambda x: x.get("volume", 0), reverse=True)

                for market in sorted_markets:
                    # Double check limit inside the market loop
                    if len(categorized_markets[event_cat]) >= max_per_category:
                        break
                    
                    # 3. Build Clean Market Object
                    # Note: 'yes_bid' is the price you can sell at instantly
                    #       'yes_ask' is the price you can buy at instantly
                    clean_market = {
                        "ticker": market.get("ticker"),
                        "event_title": event.get("title"),
                        "option_name": market.get("title") or market.get("subtitle"), # Specific option name (e.g., "Trump", "Harris")
                        "category": event_cat,
                        "expiration": market.get("expiration_time"),
                        "yes_ask": market.get("yes_ask", 0), # Price to BUY Yes
                        "no_ask": market.get("no_ask", 0),   # Price to BUY No
                        "volume": market.get("volume", 0),
                        "liquidity": market.get("liquidity", 0),
                        "event_id": event.get("event_ticker")
                    }
                    
                    categorized_markets[event_cat].append(clean_market)

            # --- OPTIMIZATION: STOP EARLY ---
            # Check if all requested categories are full
            all_full = True
            for cat in target_categories:
                # We check case-insensitive match against the keys we actually found
                found_count = 0
                for key in categorized_markets.keys():
                    if key.lower() == cat.lower():
                        found_count = len(categorized_markets[key])
                
                if found_count < max_per_category:
                    all_full = False
                    break
            
            if all_full:
                print("✨ limit reached for all requested categories. Stopping early.")
                has_more_pages = False
            elif not cursor:
                has_more_pages = False
            else:
                time.sleep(0.1) # Rate limit safety

        except Exception as e:
            print(f"⚠️ Exception on page {page_count}: {e}")
            has_more_pages = False

    # --- REPORTING ---
    print("\n" + "="*60)
    print(f"📊 FINAL SCOUT REPORT")
    print("="*60)
    
    total_found = 0
    for cat, mkts in categorized_markets.items():
        count = len(mkts)
        total_found += count
        if count > 0:
            print(f"📂 {cat}: {count} options found")
            # Show top 1 example
            top = mkts[0]
            print(f"   ↳ Example: {top['event_title']} -> [{top['option_name']}]")
            print(f"     (Buy Yes: {top['yes_ask']}¢ | Vol: {top['volume']})")

    print(f"\n✅ Collection Complete. Total Markets: {total_found}")
    return categorized_markets

# --- TEST RUN ---
if __name__ == "__main__":
    # Example Usage
    my_cats = ["Sports","Politics", "Economics"]
    results = fetch_current_kalshi_markets(target_categories=my_cats, max_per_category=30)