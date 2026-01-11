import time
import sys
import env
import current_markets as scout       #  (fetching markets) scripts
import research_strat as researcher # Your Perplexity script
import strategic_math as advisor        # Your budget math script

# --- IMPORT YOUR MODULES ---
# Make sure these filenames match exactly what you saved!

# --- CONFIGURATION ---
DAILY_BUDGET = env.MAX_BET_AMOUNT_CENTS   # How much you want to allocate today
MAX_RESEARCH_ITEMS = 3 # Limit AI calls to save money/time
MIN_VOLUME = 500       # Only look at markets with >$500 volume (Liquidity Check)

def run_advisor_bot():
    print("\n" + "="*60)
    print(f"🤖 BADDIE BOT ADVISOR: Starting Daily Routine (${DAILY_BUDGET})")
    print("="*60 + "\n")

    # STEP 1: SCOUTING
    # ------------------------------------------------------
    print("📡 SCOUT: Scanning Kalshi for active markets...")
    try:
        # Assuming your scout script has a function like get_markets() or returns a list
        # If your scout script just prints, you might need to modify it slightly to 'return' the list
        all_markets = scout.fetch_diverse_kalshi_markets() 
    except Exception as e:
        print(f"❌ Scout failed: {e}")
        return

    # Flatten the dictionary if your scout returns {category: [markets]}
    flat_market_list = []
    if isinstance(all_markets, dict):
        for cat, markets in all_markets.items():
            flat_market_list.extend(markets)
    else:
        flat_market_list = all_markets

    print(f"✅ SCOUT: Found {len(flat_market_list)} total markets.")

    # STEP 2: FILTERING (The "Liquidity Trap" Check)
    # ------------------------------------------------------
    print(f"\n🔍 FILTER: Selecting top {MAX_RESEARCH_ITEMS} liquid candidates...")
    
    # Sort by volume (highest first) to find 'real' markets
    # We use .get('volume', 0) to avoid crashing if volume is missing
    candidates = [m for m in flat_market_list if m.get('volume', 0) > MIN_VOLUME]
    candidates = sorted(candidates, key=lambda x: x.get('volume', 0), reverse=True)
    
    # Take the top N candidates
    top_picks = candidates[:MAX_RESEARCH_ITEMS]
    
    if not top_picks:
        print("⚠️ FILTER: No markets met the liquidity threshold. Try lowering MIN_VOLUME.")
        return

    for i, m in enumerate(top_picks):
        print(f"   {i+1}. {m['ticker']} (${m.get('volume',0):,} vol): {m['question'][:60]}...")

    # STEP 3: RESEARCHING
    # ------------------------------------------------------
    print(f"\n🧠 RESEARCHER: Analyzing {len(top_picks)} markets with AI...")
    
    research_results = researcher.research_batch(top_picks)
    
    if not research_results:
        print("🚫 RESEARCHER: AI found no viable edges or failed to analyze.")
        return

    # STEP 4: ADVISING
    # ------------------------------------------------------
    print("\n" + "-"*60)
    recommendations = advisor.get_advisor_recommendations(research_results, total_daily_budget=DAILY_BUDGET)
    
    # Handle the case where advisor returns a string (error/no trade) vs a list
    if isinstance(recommendations, str):
        print(f"📢 ADVICE: {recommendations}")
    else:
        print(f"🚀 FINAL STRATEGY REPORT ({time.strftime('%Y-%m-%d')})")
        print("-" * 60)
        print(f"{'TICKER':<15} | {'BET SIZE':<10} | {'CONFIDENCE':<10} | {'REASON'}")
        print("-" * 60)
        
        for rec in recommendations:
            print(f"{rec['ticker']:<15} | {rec['suggested_bet']:<10} | {rec['confidence']:<10} | {rec['reason'][:50]}...")
            print(f"{' ':<41} {rec['reason'][50:100]}...") # Wrap text slightly
            print("-" * 60)
            
    print("\n✅ MISSION COMPLETE.")

if __name__ == "__main__":
    run_advisor_bot()