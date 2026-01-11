import requests
import datetime
import time
from collections import defaultdict

def fetch_current_kalshi_markets(max_per_category=30):
    """
    Fetches active Kalshi markets but ensures diversity by capping
    each category (Politics, Econ, Sports, etc.) to a specific limit.
    """
    base_url = "https://api.elections.kalshi.com/trade-api/v2/events"

    # We use the 'events' endpoint because it contains the 'category' field
    # 'with_nested_markets=true' gives us the actual tickers inside that event immediately
    params = {
        "limit": 30,  # Get 100 events per page
        "status": "open",
        "with_nested_markets": "true"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) KalshiScout/1.0",
        "Accept": "application/json"
    }

    # Storage for our sorted markets
    # Structure: { "Politics": [market1, market2...], "Economics": [...] }
    categorized_markets = defaultdict(list)

    print("🔍 Scouting Kalshi for diverse opportunities...")

    cursor = None
    has_more_pages = True
    page_count = 0

    while has_more_pages:
        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {response.text}")
                break

            data = response.json()
            events = data.get("events", [])
            cursor = data.get("cursor")

            if not events:
                break

            print(f"  > Processing page {page_count + 1} ({len(events)} events found)...")

            for event in events:
                category = event.get("category", "Uncategorized")
                markets = event.get("markets", [])

                # If we already have enough markets for this category, skip this event
                if len(categorized_markets[category]) >= max_per_category:
                    continue

                # Add markets from this event to our bucket
                for market in markets:
                    # Basic filter: Ensure market is actually open
                    if market.get("status") == "active" or market.get("status") == "open":
                        # Enforce the limit again just in case an event has 50 markets
                        if len(categorized_markets[category]) < max_per_category:

                            # Clean up the object to only what we need
                            clean_market = {
                                "ticker": market.get("ticker"),
                                "question": market.get("title") or event.get("title"),
                                "category": category,
                                "end_date": market.get("expiration_time"),
                                "yes_price": market.get("yes_bid", 0),
                                "volume": market.get("volume", 0),
                                "event_id": event.get("event_ticker")
                            }
                            categorized_markets[category].append(clean_market)

            # Check if we are "full" on all major categories to stop early
            # (Optional optimization: if we have 30 of Pol, Econ, and Tech, we can stop)

            if not cursor:
                has_more_pages = False

            page_count += 1
            time.sleep(0.2) # Be nice to the API

        except Exception as e:
            print(f"⚠️ Error fetching page: {e}")
            has_more_pages = False

    # --- Display Results ---
    print("\n" + "="*50)
    print(f"🎯 SCOUT REPORT: Top {max_per_category} Markets Per Category")
    print("="*50)

    total_markets = 0

    for category, markets in categorized_markets.items():
        if not markets:
            continue

        print(f"\n📂 {category.upper()} ({len(markets)} markets)")
        print("-" * 30)

        # Sort by volume (optional) to show most active ones first
        sorted_markets = sorted(markets, key=lambda x: x['volume'], reverse=True)

        for i, m in enumerate(sorted_markets[:5], 1):  # Just print top 5 for readability
            # Parse date safely
            expiry = m['end_date'].split('T')[0] if m['end_date'] else "N/A"
            print(f"  {i}. {m['question']}")
            print(f"     [Ticker: {m['ticker']}] | Expires: {expiry} | Price: {m['yes_price']}¢")

        if len(markets) > 5:
            print(f"     ... and {len(markets) - 5} more.")

        total_markets += len(markets)

    print("\n" + "="*50)
    print(f"✅ Total Markets Scouted: {total_markets}")

    return categorized_markets