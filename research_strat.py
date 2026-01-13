import json
import re
import httpx
from openai import OpenAI
import env 

# Initialize Perplexity Client
client = OpenAI(
    api_key=env.PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai",
    http_client=httpx.Client(timeout=60.0) # Increased timeout for deep thinking
)

def research_event_group(category, market_list):
    """
    Analyzes a list of specific market options using Perplexity/Sonar.
    
    Args:
        category (str): The category name (e.g., 'Politics')
        market_list (list): A list of market dictionaries from the Scout module.
                            Expected keys: 'option_name', 'ticker', 'yes_ask', 'event_title'
    
    Returns:
        list: A list of the top 5 recommendation dictionaries.
    """
    if not market_list:
        return []

    print(f"   > 🧠 Analyzing {len(market_list)} betting options in '{category}'...")

    # 1. Format the data for the AI context
    # We strip unnecessary data to save tokens and keep the AI focused.
    context_text = ""
    for m in market_list:
        # Calculate implied probability from the 'ask' price (cost to buy)
        price = m.get('yes_ask', 0)
        
        # Skip invalid prices (0 or >99)
        if price < 1 or price > 99: 
            continue
            
        context_text += (
            f"- Event: {m['event_title']} | Option: {m['option_name']} | "
            f"Ticker: {m['ticker']} | Price (Implied %): {price}%\n"
        )

    # 2. Construct the Analysis Prompt
    system_prompt = f"""
    You are a professional prediction market analyst (Kalshi/Polymarket expert).
    
    YOUR TASK:
    Analyze the provided list of betting options for the category '{category}'.
    Identify exactly the TOP 5 "Value Bets" where the market is WRONG.
    
    METHODOLOGY:
    1. "Implied Probability" is simply the Price (e.g., 30c = 30%).
    2. "Real World Probability" is your estimation based on current news, polls, and data.
    3. Look for the "Edge": Where Real Prob > Implied Prob.
    
    SCORING:
    - Confidence Score: 1 (Low) to 10 (High).
    - Explanation: Max 3 concise sentences explaining the discrepancy.
    
    OUTPUT FORMAT (JSON ONLY):
    Return a valid JSON object containing a list named "picks".
    {{
        "picks": [
            {{
                "ticker": "TICKER_HERE",
                "option_name": "Name of option",
                "market_price": 30,
                "estimated_real_prob": 55,
                "confidence_score": 8,
                "reasoning": "Polls show candidate leading by 5 points, but market prices them as an underdog. Momentum is shifting favorable."
            }}
        ]
    }}
    """
    
    user_prompt = (
        f"Here are the active markets for {category}:\n\n"
        f"{context_text}\n\n"
        f"Based on real-world data, return the Top 5 best value plays in JSON format."
    )

    try:
        # Call Perplexity Sonar-Pro (or Medium) for reasoning
        response = client.chat.completions.create(
            model="sonar-pro", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1 # Low temp for factual consistency
        )
        
        # 3. Clean & Parse Response
        raw_content = response.choices[0].message.content
        
        # Remove any <think> blocks if the model outputs them
        clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL)
        
        # Extract JSON using regex (handles if model adds extra text)
        json_match = re.search(r'(\{.*\})', clean_content, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group(1))
            picks = data.get('picks', [])
            
            # Post-processing: Add the category back to the pick for the Advisor to see
            for p in picks:
                p['category'] = category
                
            return picks
            
        else:
            print("   ⚠️ Error: Could not find JSON in AI response.")
            return []

    except Exception as e:
        print(f"   ❌ AI Analysis Failed: {e}")
        return []