import os
import json
import re
import sys
from openai import OpenAI

# Import your local env file
import env

# --- CONFIGURATION ---

client = OpenAI(
    api_key=env.PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

def get_ai_analysis(market_question, current_price, end_date):
    """
    Asks Perplexity to research a specific market and estimate probability.
    """

    # 1. Craft the "Analyst Persona" Prompt
    system_prompt = """
    You are a ruthless prediction market analyst. Your goal is to estimate the
    TRUE probability of an event occurring based on the latest news.

    You will be given a market question and its current trading price (implied probability).
    Your output must be a strict JSON object with NO markdown formatting.

    JSON Format:
    {
        "my_estimated_probability": 0.0 to 1.0,
        "reasoning": "A short, dense summary of why (5 sentences).",
        "verdict": "BUY_YES", "BUY_NO", or "PASS",
        "confidence": "HIGH" or "LOW"
    }

    Rules for Verdict:
    - BUY_YES if your prob > (current_price + 0.10)
    - BUY_NO if your prob < (current_price - 0.10)
    - PASS if the edge is too small or news is unclear.
    """

    user_prompt = f"""
    Event: "{market_question}"
    Current Market Price for YES: {current_price} cents (Implied Prob: {current_price/100})
    Expiration Date: {end_date}

    Search the web for the latest news on this topic.
    Compare the market's implied probability vs. reality.
    """

    try:
        # 2. Call Perplexity (sonar-reasoning-pro is best for deep research)
        response = client.chat.completions.create(
            model="sonar-reasoning-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1, # Keep it factual
        )

        # 3. Parse the JSON
        content = response.choices[0].message.content

        # Use Regex to find the first '{' and the last '}'
        # This ignores any "Here is your JSON:" chatter from the AI
        json_match = re.search(r'\{.*\}', content, re.DOTALL)

        if json_match:
            clean_content = json_match.group(0)
            analysis = json.loads(clean_content)
            return analysis
        else:
            print(f"❌ No JSON found in response for: {market_question}")
            return None

    except json.JSONDecodeError as e:
        print(f"⚠️ JSON failed to parse for '{market_question}': {e}")
        return None
    except Exception as e:
        print(f"⚠️ Research failed: {e}")
        return None

def research_batch(markets_list):
    """
    Takes a list of raw markets (from the Scout) and filters for GOLD.
    """
    print(f"\n🔬 Starting Deep Research on {len(markets_list)} markets...")
    print("-" * 60)

    opportunities = []

    for market in markets_list:
        question = market['question']
        price = market['yes_price']

        # Skip if price is too extreme (e.g., 99c or 1c) to avoid liquidity traps
        if price < 5 or price > 95:
            continue

        print(f"Searching: {question[:50]}...")

        # Note: 'end_date' key must exist in your market dictionary
        analysis = get_ai_analysis(question, price, market.get('end_date', 'Unknown'))

        if analysis and analysis.get('verdict') != 'PASS':
            # We found an edge!
            opportunity = {
                "market": market,
                "analysis": analysis,
                "edge": abs(analysis['my_estimated_probability'] - (price/100))
            }
            opportunities.append(opportunity)

            # Real-time feedback
            print(f"  >>> FOUND EDGE: {analysis['verdict']} (Conf: {analysis['confidence']})")
            print(f"      Reason: {analysis['reasoning']}")

    return opportunities
