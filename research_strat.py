import json
import re
import httpx
from openai import OpenAI
import env 

client = OpenAI(
    api_key=env.PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai",
    http_client=httpx.Client(timeout=.0)
)

def research_event_group(category, event_list):
    """
    Analyzes complete events.
    Input: List of Events, each containing multiple Options.
    """
    print(f"   > 🧠 Analyzing {len(event_list)} complex events in '{category}'...")

    # 1. Format the data for the AI
    # Structure:
    # EVENT: Who will win? 
    # - Option A (20c)
    # - Option B (50c)
    context_text = ""
    for e in event_list:
        context_text += f"\nEVENT: {e['title']} (Vol: {e['total_volume']})\n"
        for opt in e['options']:
            context_text += f"   - Option: {opt['name']} | Ticker: {opt['ticker']} | Price: {opt['price']}¢\n"

    # 2. The "Arbitrage" Prompt
    system_prompt = f"""
    You are a prediction market expert. You are looking at multi-outcome events (like elections or awards on Kalshi).
    
    YOUR JOB:
    1. Look at each EVENT and its list of OPTIONS (Outcomes).
    2. Compare the Implied Probability (Price) vs Real World Probability.
    3. Pick the SINGLE best value bet per event.
    
    RULES:
    - If the favorite is overpriced (e.g., 90c but risky), look for the underdog.
    - If an option is priced at 1c or 99c, ignore it (liquidity trap).
    - If no option looks good, ignore the event.
    
    OUTPUT JSON:
    {{
        "picks": [
            {{
                "event": "Event Title",
                "pick_name": "Name of the option you are buying",
                "ticker": "The Ticker for that option",
                "analysis": "Why this specific option is mispriced vs the others",
                "confidence": "HIGH"
            }}
        ]
    }}
    """
    
    user_prompt = f"Here are the {category} events:\n{context_text}\n\nFind the best value plays."

    try:
        response = client.chat.completions.create(
            model="sonar-pro", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        
        # Clean & Parse
        raw = response.choices[0].message.content
        clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL)
        json_match = re.search(r'(\{.*\})', clean, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(1)).get('picks', [])
        return []

    except Exception as e:
        print(f"     ❌ Analysis Error: {e}")
        return []