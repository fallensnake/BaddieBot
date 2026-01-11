import json
import time
import base64
import requests
import datetime
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# Import your local env.py file
import env

# --- CONFIGURATION & AUTH ---

def get_private_key():
    """
    Loads the private key from the file path defined in env.py.
    """
    key_path = env.KALSHI_PRIVATE_KEY_PATH
    
    # Check if file exists
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"❌ Could not find the key file at: {key_path}")

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
    # Production URL (Change to 'demo-api.kalshi.com' if using demo keys)
    base_url = "https://api.elections.kalshi.com" 
    path = '/trade-api/v2' + endpoint
    
    try:
        timestamp, signature = sign_request(method, path)
    except FileNotFoundError as e:
        print(e)
        return None
    except Exception as e:
        print(f"❌ Error signing request: {e}")
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
        response.raise_for_status() # Raise error for 4xx/5xx responses
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"⚠️ HTTP Error: {e}")
        print(f"Response Body: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return None

# --- PORTFOLIO LOGIC ---

def get_portfolio_summary():
    """Fetches balance and active positions."""
    print("💼 Accessing Portfolio...")

    # 1. Get Balance
    balance_data = make_authenticated_request("GET", "/portfolio/balance")
    if not balance_data:
        return

    balance_cents = balance_data.get('balance', 0)
    cash = balance_cents / 100.0
    print(f"\n💰 Available Cash: ${cash:,.2f}")

    # 2. Get Active Positions
    positions_data = make_authenticated_request("GET", "/portfolio/positions")
    
    if not positions_data:
        print("Could not fetch positions data.")
        return

    positions = positions_data.get('market_positions', [])
    if not positions:
        print("📭 No active positions found.")
        return

    print(f"\n📊 Current Holdings ({len(positions)} markets):")
    print("-" * 85)
    # Adjusted spacing for better local terminal readability
    print(f"{'Market Ticker':<25} | {'Side':<4} | {'Count':<6} | {'Current (Bid/Ask)':<20}")
    print("-" * 85)

    for p in positions:
        ticker = p.get('ticker')
        raw_count = p.get('position', 0)
        
        # Skip if count is 0 (closed position still showing in history)
        if raw_count == 0:
            continue

        side = "YES" if raw_count > 0 else "NO"
        count = abs(raw_count)

        # 3. Get Current Market Price
        market_url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"
        try:
            m_res = requests.get(market_url)
            if m_res.status_code == 200:
                m_data = m_res.json().get('market', {})
                # Display the relevant price based on your holding
                if side == "YES":
                    price_display = f"{m_data.get('yes_bid', 0)}¢ (Bid)"
                else:
                    # If holding NO, you sell into the NO bid (which is 100 - yes_ask)
                    # Or broadly, the value is inverse of YES. 
                    # For simplicity in display, we show the YES price context
                    price_display = f"YES is {m_data.get('yes_bid', 0)}¢"
            else:
                price_display = "(Price unavail)"

            print(f"{ticker:<25} | {side:<4} | {count:<6} | {price_display:<20}")

        except Exception as e:
            print(f"{ticker:<25} | {side:<4} | {count:<6} | (Error fetching price)")

    print("-" * 85)