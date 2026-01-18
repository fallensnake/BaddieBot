import json
import sys

# --- IMPORT YOUR MODULES ---
try:
    # Ensure these match your actual filenames
    import current_markets as scout       
    import research_strat as researcher   
except ImportError as e:
    print(f"❌ Critical Error: {e}")
    print("Make sure 'current_markets.py' and 'research_strat.py' are in this folder.")
    sys.exit(1)

def run_real_politics_test():
    print("\n" + "="*60)
    print("🤖 BADDIE BOT: Live Politics Test Mode")
    print("="*60 + "\n")

    # 1. DEFINE TEST PARAMETERS
    # We only want 'Politics' and we only want the top 15 most liquid options to save time/tokens.
    TARGET_CATS = ["Politics"]
    LIMIT = 15

    # 2. SCOUT (Fetch Real Data)
    print(f"📡 SCOUT: Fetching live '{TARGET_CATS[0]}' markets from Kalshi...")
    
    try:
        # This calls your actual API function
        market_data = scout.fetch_current_kalshi_markets(TARGET_CATS, max_per_category=LIMIT)
    except Exception as e:
        print(f"❌ SCOUT FAILED: {e}")
        return

    # Extract just the politics list from the dictionary
    politics_markets = market_data.get("Politics", [])

    if not politics_markets:
        print("⚠️ SCOUT ALERT: No active Politics markets found. Check API or Time of Day.")
        return

    print(f"   ↳ Success: Found {len(politics_markets)} active betting options.\n")

    # 3. RESEARCHER (AI Analysis)
    print(f"🧠 RESEARCHER: Sending data to Perplexity for analysis...")

    try:
        # Pass the real list to the AI
        # It should return a list of dictionary 'picks'
        recommendations = researcher.research_event_group("Politics", politics_markets)
        
    except Exception as e:
        print(f"❌ RESEARCHER FAILED: {e}")
        return

    # 4. DISPLAY RESULTS
    print("\n" + "-"*60)
    print("🚀 FINAL RESULTS (Live Data)")
    print("-" * 60)

    if not recommendations:
        print("🤷‍♂️ AI Result: No high-value edges found (or AI refused to bet).")
    else:
        for i, rec in enumerate(recommendations, 1):
            # Handle potential key name variations safely
            name = rec.get('option_name') or rec.get('pick_name', 'Unknown')
            price = rec.get('market_price') or rec.get('market_implied_prob', 0)
            real_prob = rec.get('estimated_real_prob', 0)
            conf = rec.get('confidence_score') or rec.get('confidence', 0)
            reason = rec.get('reasoning') or rec.get('analysis', 'No reason given.')

            print(f"{i}. OPTION: {name} ({rec.get('ticker', 'N/A')})")
            print(f"   💰 Price: {price}¢  vs  🧠 Real Prob: {real_prob}%")
            print(f"   🔥 Confidence: {conf}/10")
            print(f"   📝 Reason: {reason}\n")

    print("✅ TEST COMPLETE.")

if __name__ == "__main__":
    run_real_politics_test()