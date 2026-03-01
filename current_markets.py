import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import requests

def get_sport_markets(max_markets=30):
    """
    Specialized fetcher ONLY for Sports.
    Handles league mapping (NBA, NFL) and enforces game diversity (max 4 per game).
    """
    base_url = "https://api.elections.kalshi.com/trade-api/v2/events"
    params = { "limit": 100, "status": "open", "with_nested_markets": "true" }
    headers = { "User-Agent": "KalshiScout/2.0", "Accept": "application/json" }

    now = datetime.now(timezone.utc)
    cutoff_time = now + timedelta(days=21) # Sports Postponement Buffer
    
    sports_leagues = ["sports", "nba", "nfl", "mlb"]
    sports_markets = []
    
    cursor = None
    has_more_pages = True

    while has_more_pages:
        if cursor: params["cursor"] = cursor

        try:
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code != 200: break

            data = response.json()
            events = data.get("events", [])
            cursor = data.get("cursor")

            if not events: break

            for event in events:
                event_cat = event.get("category", "Uncategorized").lower()
                if event_cat not in sports_leagues: 
                    continue
                
                raw_markets = event.get("markets", [])

                for market in raw_markets:
                    time_check_str = market.get("close_time") or market.get("expiration_time")
                    if not time_check_str: continue

                    try:
                        check_dt = datetime.fromisoformat(time_check_str.replace('Z', '+00:00'))
                    except ValueError: continue
                    
                    if check_dt <= now or check_dt > cutoff_time:
                        continue

                    yes_price = market.get("yes_ask", 0)
                    if yes_price < 10 or yes_price > 90:
                        continue

                    clean_market = {
                        "ticker": market.get("ticker"),
                        "event_title": event.get("title"),
                        "option_name": market.get("title") or market.get("subtitle"),
                        "category": "Sports", # Force everything into one clean category
                        "yes_ask": yes_price,
                        "volume": market.get("volume", 0),
                        "liquidity": market.get("liquidity", 0),
                        "event_id": event.get("event_ticker")
                    }
                    sports_markets.append(clean_market)

            if not cursor: has_more_pages = False
            else: time.sleep(0.1)

        except Exception as e:
            has_more_pages = False

    # --- SPORTS DIVERSITY FILTER ---
    sports_markets.sort(key=lambda x: x['volume'], reverse=True)
    
    diverse_list = []
    seen_games = defaultdict(int)
    
    for m in sports_markets:
        # Group by Base Ticker (e.g. KXNBA-260226-LALGSW)
        ticker_parts = m['ticker'].split('-')
        game_key = "-".join(ticker_parts[:3]) if len(ticker_parts) >= 3 else m['event_title']
        
        if seen_games[game_key] < 4:
            diverse_list.append(m)
            seen_games[game_key] += 1
            
        if len(diverse_list) >= max_markets:
            break
            
    # Return as a dict so it matches the format of fetch_current_kalshi_markets
    return {"Sports": diverse_list} if diverse_list else {}

def fetch_current_kalshi_markets(target_categories, max_per_category=30):
    """
    Acts as the Main Manager for fetching markets.
    If 'Sports' is requested, it delegates that to get_sport_markets().
    Fetches the rest using the standard 30-day volume sort.
    """
    # 1. Check if Sports was requested and separate it
    target_cats_lower = [c.lower() for c in target_categories]
    
    wants_sports = False
    if "sports" in target_cats_lower:
        wants_sports = True
        target_cats_lower.remove("sports") # Remove it so the standard loop ignores it
        
    categorized_markets = defaultdict(list)
    
    # 2. Fetch standard categories (Politics, Econ, etc.) if any are left
    if target_cats_lower:
        base_url = "https://api.elections.kalshi.com/trade-api/v2/events"
        params = { "limit": 100, "status": "open", "with_nested_markets": "true" }
        headers = { "User-Agent": "KalshiScout/2.0", "Accept": "application/json" }

        now = datetime.now(timezone.utc)
        cutoff_time = now + timedelta(days=30)
        
        print(f"🔍 SCOUT: Searching standard markets: {', '.join([c.title() for c in target_cats_lower])}...")

        cursor = None
        has_more_pages = True

        while has_more_pages:
            if cursor: params["cursor"] = cursor

            try:
                response = requests.get(base_url, params=params, headers=headers)
                if response.status_code != 200: break

                data = response.json()
                events = data.get("events", [])
                cursor = data.get("cursor")

                if not events: break

                for event in events:
                    event_cat = event.get("category", "Uncategorized")
                    
                    if event_cat.lower() not in target_cats_lower: 
                        continue
                    
                    raw_markets = event.get("markets", [])

                    for market in raw_markets:
                        time_check_str = market.get("close_time") or market.get("expiration_time")
                        if not time_check_str: continue

                        try:
                            check_dt = datetime.fromisoformat(time_check_str.replace('Z', '+00:00'))
                        except ValueError: continue
                        
                        if check_dt <= now or check_dt > cutoff_time:
                            continue

                        yes_price = market.get("yes_ask", 0)
                        if yes_price < 10 or yes_price > 90:
                            continue

                        clean_market = {
                            "ticker": market.get("ticker"),
                            "event_title": event.get("title"),
                            "option_name": market.get("title") or market.get("subtitle"),
                            "category": event_cat,
                            "yes_ask": yes_price,
                            "volume": market.get("volume", 0),
                            "liquidity": market.get("liquidity", 0),
                            "event_id": event.get("event_ticker")
                        }
                        categorized_markets[event_cat].append(clean_market)

                if not cursor: has_more_pages = False
                else: time.sleep(0.1)

            except Exception as e:
                print(f"⚠️ Exception: {e}")
                has_more_pages = False

        # Sort non-sports categories purely by volume
        for cat in categorized_markets:
            categorized_markets[cat].sort(key=lambda x: x['volume'], reverse=True)
            categorized_markets[cat] = categorized_markets[cat][:max_per_category]

    # 3. Fetch Sports (if requested) using the specialized function
    if wants_sports:
        sports_data = get_sport_markets(max_markets=max_per_category)
        
        # Merge the sports data into the main dictionary
        if "Sports" in sports_data:
            categorized_markets["Sports"] = sports_data["Sports"]

    return categorized_markets

# ... [Ensure get_sport_markets is defined directly beneath this in the same file] ...

def get_daily_markets(target_categories):
    """
    Fetches active Kalshi markets closing/expiring within 24 hours.
    Returns a flat list sorted by closing time.
    """
    base_url = "https://api.elections.kalshi.com/trade-api/v2/events"
    params = { "limit": 100, "status": "open", "with_nested_markets": "true" }
    headers = { "User-Agent": "KalshiScout/2.0", "Accept": "application/json" }

    now = datetime.now(timezone.utc)
    cutoff_time = now + timedelta(hours=24)
    target_cats_lower = [c.lower() for c in target_categories]
    
    print(f"⏰ SCOUT: Searching markets (Trading Closes < 24h)...")

    daily_candidates = []
    cursor = None
    has_more_pages = True

    while has_more_pages:
        if cursor: params["cursor"] = cursor
        try:
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code != 200: break

            data = response.json()
            events = data.get("events", [])
            cursor = data.get("cursor")

            if not events: break

            for event in events:
                event_cat = event.get("category", "Uncategorized").lower()
                if not any(t in event_cat for t in target_cats_lower): continue

                for market in event.get("markets", []):
                    # Time Logic
                    close_str = market.get("close_time")
                    exp_str = market.get("expiration_time")
                    
                    relevant_dt = None
                    if close_str:
                        try: relevant_dt = datetime.fromisoformat(close_str.replace('Z', '+00:00'))
                        except ValueError: pass
                    if not relevant_dt and exp_str:
                        try: relevant_dt = datetime.fromisoformat(exp_str.replace('Z', '+00:00'))
                        except ValueError: pass

                    if not relevant_dt: continue

                    # Must close within next 24h
                    if not (now < relevant_dt <= cutoff_time): continue

                    yes_price = market.get("yes_ask", 0)
                    if yes_price < 10 or yes_price > 90: continue

                    clean_market = {
                        "ticker": market.get("ticker"),
                        "event_title": event.get("title"),
                        "option_name": market.get("title") or market.get("subtitle"),
                        "category": event.get("category"),
                        "relevant_dt": relevant_dt,
                        "yes_ask": yes_price,
                        "volume": market.get("volume", 0)
                    }
                    daily_candidates.append(clean_market)

            if not cursor: has_more_pages = False
            else: time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Exception: {e}")
            has_more_pages = False

    # Sort by time (Soonest -> Latest)
    daily_candidates.sort(key=lambda x: x['relevant_dt'])
    
    print(f"✅ Found {len(daily_candidates)} valid markets.")
    return daily_candidates
if __name__ == "__main__":
    # Example Usage
    my_cats = ['Sports']
    results = fetch_current_kalshi_markets(my_cats, max_per_category=50)
    print(results)