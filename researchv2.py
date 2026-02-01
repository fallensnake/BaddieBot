import json
import re
import httpx
from openai import OpenAI
import env 

# Initialize Perplexity Client
client = OpenAI(
    api_key=env.PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai",
    http_client=httpx.Client(timeout=300.0)
)

def research_event_group(category, market_list):
    """
    Analyzes markets with a focus on HIGH PROBABILITY 'Free Money' plays.
    """
    if not market_list:
        return []

    print(f"   > 🧠 Analyzing {len(market_list)} options in '{category}' for safe yields...")

    # 1. Format Data
    context_text = ""
    for m in market_list:
        price = m.get('yes_ask', 0)
        # We allow higher prices now (up to 92c) because "free money" 
        # often hides in the 80c-90c range.
        if price < 5 or price > 96: 
            continue
            
        context_text += (
            f"- Event: {m['event_title']} | Option: {m['option_name']} | "
            f"Ticker: {m['ticker']} | Price (Implied %): {price}%\n"
        )

    # 2. THE "FREE MONEY" PROMPT
    system_prompt = f"""
    You are a risk-averse arbitrage trader for prediction markets.
    
    YOUR GOAL:
    Find "Free Money" opportunities. Do NOT look for risky underdogs or contrarian bets.
    Look for outcomes that are ALMOST CERTAIN to happen, but the market is still pricing them with doubt.
    
    METHODOLOGY (SAFE YIELD HUNTING):
    1. Ignore "Long Shots" (prices under 20c) unless breaking news confirms them 100%.
    2. Focus on "Mispriced Favorites": 
       - Example: An event is priced at 75c (75%) but reality says it's 95% certain.
       - This is a safe 1.3x return.
    3. Your "Real World Probability" should reflect FACTS, not speculation.
    
    SCORING:
    - Confidence Score (1-10): Rate strictly on SAFETY. 
       - 10 = The event has effectively already happened (Free Money).
       - 1 = It's a coin toss (Avoid).
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "picks": [
            {{
                "ticker": "TICKER",
                "option_name": "Option Name",
                "market_price": 75,
                "estimated_real_prob": 90,
                "confidence_score": 9,
                "reasoning": "Polls and news confirm this is a lock. Market is lagging. Easy 20% yield."
            }}
        ]
    }}
    """
    
    user_prompt = (
        f"Here are the active markets for {category}:\n\n"
        f"{context_text}\n\n"
        f"Identify the Top 10 safest, high-probability plays."
    )

    try:
        response = client.chat.completions.create(
            model="sonar-pro", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1 
        )
        
        raw_content = response.choices[0].message.content
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL)
        json_match = re.search(r'(\{.*\})', clean_content, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group(1))
            picks = data.get('picks', [])
            
            for p in picks:
                p['category'] = category
                # Force high confidence only for this strategy
                if p.get('confidence_score', 0) < 6:
                    continue
            
            return picks
            
        return []

    except Exception as e:
        print(f"   ❌ AI Analysis Failed: {e}")
        return []

if __name__ == "__main__":
    print("🧪 STARTING ISOLATED RESEARCH TEST")
    print("="*60)

    # 1. MOCK DATA
    # This simulates what 'scout.py' would return for the "Politics" category.
    # We include some obvious "value" plays to see if the AI catches them.
    test_category = "Politics"
    
    test_markets = [
        {
            "ticker": "KX-TRUMP-24",
            "event_title": "Who will win the 2024 Presidential Election?",
            "option_name": "Donald Trump",
            "yes_ask": 52,  # Implied 52%
        },
        {
            "ticker": "KX-BIDEN-24",
            "event_title": "Who will win the 2024 Presidential Election?",
            "option_name": "Joe Biden",
            "yes_ask": 45,  # Implied 45%
        },
        {
            "ticker": "KX-GAVIN-24",
            "event_title": "Who will win the 2024 Presidential Election?",
            "option_name": "Gavin Newsom",
            "yes_ask": 2,   # Implied 2%
        },
        {
            "ticker": "KX-FED-CUT",
            "event_title": "Will the Fed cut rates in March?",
            "option_name": "Yes",
            "yes_ask": 15,  # Implied 15% - maybe AI thinks this is higher?
        },
        {
            "ticker": "KX-GOV-SHUT",
            "event_title": "Will there be a government shutdown in Jan?",
            "option_name": "Yes",
            "yes_ask": 80,  # Implied 80%
        }
    ]

    # 2. RUN THE FUNCTION
    try:
        print(f"📉 Feeding {len(test_markets)} mock markets to AI...")
        results = research_event_group(test_category, test_markets)
        
        # 3. PRINT RESULTS
        print("\n✅ TEST RESULTS:")
        print(json.dumps(results, indent=2))
        
        if not results:
            print("\n⚠️ RESULT EMPTY: Check your API Key or Prompt formatting.")
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")