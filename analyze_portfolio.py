import json
import time
import base64
import requests
import datetime
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# --- IMPORTS ---
import env

try:
    import research_strat as researcher
except ImportError:
    researcher = None
    print("⚠️ Warning: 'research_markets.py' not found. AI updates will be disabled.")

# --- CONFIGURATION & AUTH ---

def get_private_key():
    """
    Loads the private key from the file path defined in env.py.
    """
    key_path = getattr(env, 'KALSHI_PRIVATE_KEY_PATH', 'BaddieBot.txt')
    
    if not os.path.exists(key_path):
        # Fallback: Try to use the raw key string if provided in env
        if hasattr(env, 'KALSHI_PRIVATE_KEY'):
            return serialization.load_pem_private_key(
                env.KALSHI_PRIVATE_KEY.encode(),
                password=None
            )
        raise FileNotFoundError(f"❌ Could not find key file at: {key_path}")

    with open(key_path, "rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

def sign_request(method, path):
    """Generates the RSA signature using the local private key."""
    timestamp = str(int(time.time() * 1000))
    msg_string = timestamp + method + path

    private_key = get_private_key()
    signature = private_key.sign(
        msg_string.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return timestamp, base64.b64encode(signature).decode('utf-8')

def make_authenticated_request(method, endpoint, params=None):
    """Sends signed requests using credentials."""
    base_url = "https://api.elections.kalshi.com" 
    path = '/trade-api/v2' + endpoint
    
    try:
        timestamp, signature = sign_request(method, path)
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return None

    headers = {
        "KALSHI-ACCESS-KEY": env.KALSHI_KEY_ID,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    url = f"{base_url}{path}"
    
    try:
        response = requests.request(method, url, headers=headers, params=params)
        if response.status_code == 401:
            print("❌ Error 401: Unauthorized. Check your API Key ID and Private Key.")
            return None
        return response.json()
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return None

# --- PORTFOLIO LOGIC ---

def get_portfolio_summary():
    """Fetches balance and active positions, returning them for analysis."""
    print("💼 Accessing Portfolio...")

    # 1. Get Balance
    balance_data = make_authenticated_request("GET", "/portfolio/balance")
    if balance_data:
        balance_cents = balance_data.get('balance', 0)
        cash = balance_cents / 100.0
        print(f"\n💰 Available Cash: ${cash:,.2f}")

    # 2. Get Active Positions
    positions_data = make_authenticated_request("GET", "/portfolio/positions")
    if not positions_data:
        return []

    positions = positions_data.get('market_positions', [])
    active_holdings = [] # We will store detailed data here

    if not positions:
        print("📭 No active positions found.")
        return []

    print(f"\n📊 Current Holdings ({len(positions)} markets):")
    print("-" * 85)
    print(f"{'Market Ticker':<30} | {'Side':<4} | {'Count':<6} | {'Current Price':<15}")
    print("-" * 85)

    for p in positions:
        ticker = p.get('ticker')
        raw_count = p.get('position', 0)
        
        if raw_count == 0: continue # Skip closed positions

        side = "YES" if raw_count > 0 else "NO"
        count = abs(raw_count)

        # 3. Fetch Market Details (Price & Question)
        market_url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"
        try:
            m_res = requests.get(market_url)
            m_data = m_res.json().get('market', {})
            
            # Price logic
            current_price = m_data.get('yes_bid', 0)
            price_display = f"{current_price}¢"
            
            # Store for AI Analysis
            active_holdings.append({
                "ticker": ticker,
                "question": m_data.get('title', ticker), # Get the readable question
                "side": side,
                "count": count,
                "current_price": current_price,
                "expiration": m_data.get('expiration_time', 'Unknown')
            })

            print(f"{ticker:<30} | {side:<4} | {count:<6} | {price_display:<15}")

        except Exception:
            print(f"{ticker:<30} | {side:<4} | {count:<6} | (Data unavailable)")

    print("-" * 85)
    return active_holdings

def analyze_holdings_news(holdings):
    """Uses the Researcher module to give updates on your specific positions."""
    if not researcher:
        return
    
    if not holdings:
        return

    print(f"\n🗞️  AI PORTFOLIO WATCH: Analyzing top positions...")
    
    # Sort by 'count' to prioritize your biggest bags, take top 3
    top_holdings = sorted(holdings, key=lambda x: x['count'], reverse=True)[:3]

    for item in top_holdings:
        question = item['question']
        print(f"\n🔍 Scanning news for: '{question}'...")
        
        # We reuse your existing research function
        analysis = researcher.get_ai_analysis(
            question, 
            item['current_price'], 
            item['expiration']
        )

        if analysis:
            # Check for danger (If you hold YES but AI says BUY_NO)
            sentiment_check = "✅ Holding seems safe."
            if item['side'] == "YES" and analysis['verdict'] == "BUY_NO":
                sentiment_check = "⚠️ WARNING: News trend is NEGATIVE for your position."
            elif item['side'] == "NO" and analysis['verdict'] == "BUY_YES":
                sentiment_check = "⚠️ WARNING: News trend is POSITIVE against your short."

            print(f"   > Update: {analysis.get('reasoning', 'No news found.')}")
            print(f"   > Verdict: {sentiment_check}")
        else:
            print("   > (AI could not retrieve news for this item)")

    print("\n✅ Portfolio Review Complete.")

if __name__ == "__main__":
    # 1. Get the data
    my_holdings = get_portfolio_summary()
    
    # 2. Run the analysis
    if my_holdings:
        analyze_holdings_news(my_holdings)