import time
import sys
import env

# --- IMPORT MODULES ---
# We wrap imports in try/except to ensure the bot fails gracefully if a file is missing
try:
    import current_markets as scout       # Fetcher
    import research_strat as researcher   # Analyst
    import strategic_math as advisor      # Math/Bet Sizing
    # import portfolio_manager as pm      # <--- FUTURE FEATURE: Uncomment when ready
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Missing a script file. Details: {e}")
    sys.exit(1)

# --- CONFIGURATION ---
DAILY_BUDGET = env.MAX_BET_AMOUNT_CENTS  
MIN_VOLUME = 500         # Liquidity Trap Threshold ($500)
MAX_RESEARCH_PER_CAT = 5 # Don't overwhelm the AI; pick top 5 liquid events per cat

# List of categories to target. 
# If your scout module fetches everything automatically, you can ignore this list 
# or use it to filter the results.
TARGET_CATEGORIES = [
    "Politics", "Economics", "Sports", "Technology", "Culture", "Global"
]

def run_advisor_bot():
    start_time = time.time()
    
    # 1. INITIALIZE CONTEXT
    # This dictionary will hold all data as it moves through the pipeline.
    # This makes adding "Portfolio Analysis" later very easy.
    bot_context = {
        'budget': DAILY_BUDGET,
        'current_portfolio': [], # <--- FUTURE: pm.get_current_positions()
        'candidates': {},        # Events passing liquidity check
        'raw_picks': [],         # Picks from Researcher before math
        'final_orders': []       # Final recommendations
    }

    print("\n" + "="*60)
    print(f"🤖 BADDIE BOT ADVISOR: Omni-Market Mode (${DAILY_BUDGET/100:.2f})")
    print("="*60 + "\n")

    # ======================================================
    # STEP 1: SCOUT (Data Collection)
    # ======================================================
    print("📡 SCOUT: Scanning Kalshi markets across all categories...")
    
    try:
        # Fetch everything. Expecting return format: {'Politics': [Events], 'Economics': [Events]}
        raw_market_data = scout.fetch_event_batches(categories=TARGET_CATEGORIES)
    except Exception as e:
        print(f"❌ CRITICAL SCOUT FAILURE: {e}")
        return

    total_found = sum(len(v) for v in raw_market_data.values())
    print(f"   ↳ Found {total_found} raw events across {len(raw_market_data)} categories.")

    # ======================================================
    # STEP 2 & 3: FILTER & RESEARCH (Iterative Processing)
    # ======================================================
    # We iterate through each category to find the best specific markets in that niche.
    
    print(f"\n🧠 RESEARCHER: Analyzing liquidity and finding edges...")

    for category, events in raw_market_data.items():
        print(f"\n   📂 Processing Category: {category.upper()}")
        
        # --- A. LIQUIDITY TRAP FILTER ---
        # Filter events in this specific category by volume
        liquid_events = [e for e in events if e.get('total_volume', 0) > MIN_VOLUME]
        
        # Sort by volume (highest first) and take top N to save AI tokens
        #liquid_events = sorted(liquid_events, key=lambda x: x.get('total_volume', 0), reverse=True)[:MAX_RESEARCH_PER_CAT]

        if not liquid_events:
            print(f"      ⚠️ Skipping: No liquid events found in {category}.")
            continue

        print(f"      ↳ Sending {len(liquid_events)} events to AI Researcher...")

        # --- B. AI RESEARCH ---
        try:
            # We pass the category and the specific list of events to the researcher
            # Expecting researcher to return a list of specific outcomes/tickers
            cat_picks = researcher.research_event_group(category, liquid_events)
            
            if cat_picks:
                print(f"      ✅ Success: AI identified {len(cat_picks)} opportunities.")
                # Add to our master list in context
                bot_context['raw_picks'].extend(cat_picks)
            else:
                print(f"      🚫 Pass: AI found no edge.")
                
        except Exception as e:
            print(f"      ❌ Error researching {category}: {e}")
            continue

    # ======================================================
    # STEP 4: ADVISOR (Optimization & Sizing)
    # ======================================================
    print("\n" + "-"*60)
    total_picks = len(bot_context['raw_picks'])
    
    if total_picks == 0:
        print("😴 ADVISOR: No picks generated today. Saving budget.")
        return

    print(f"📐 ADVISOR: Optimizing {total_picks} potential bets against budget...")

    # --- FUTURE FEATURE: PORTFOLIO CHECK ---
    # Here is where you would calculate risk based on current exposure.
    # existing_risk = pm.calculate_exposure(bot_context['current_portfolio'])
    
    try:
        # The advisor takes the raw picks and determines bet sizing (Kelly Criterion / EV)
        # We pass the whole context or just the picks
        recommendations = advisor.get_advisor_recommendations(
            picks=bot_context['raw_picks'], 
            total_budget=bot_context['budget']
        )
        bot_context['final_orders'] = recommendations
        
    except Exception as e:
        print(f"❌ ADVISOR ERROR: {e}")
        return

    # ======================================================
    # STEP 5: REPORTING / EXECUTION
    # ======================================================
    print("\n🚀 FINAL STRATEGY REPORT")
    print("-" * 65)
    print(f"{'MARKET / OPTION':<30} | {'SIDE':<5} | {'BET SIZE':<10} | {'REASON'}")
    print("-" * 65)

    for rec in bot_context['final_orders']:
        # Extract data safely with defaults
        ticker = rec.get('ticker') or rec.get('title', 'Unknown')
        side = rec.get('side', 'YES') # Yes/No
        size = rec.get('suggested_bet', 0)
        reason = rec.get('reason', 'N/A')

        # Formatting for table
        display_name = (ticker[:27] + '..') if len(ticker) > 29 else ticker
        
        print(f"{display_name:<30} | {side:<5} | ${size/100:<9.2f} | {reason[:20]}...")

    # Summary
    total_spent = sum(r.get('suggested_bet', 0) for r in bot_context['final_orders'])
    print("-" * 65)
    print(f"💰 TOTAL ALLOCATION: ${total_spent/100:.2f} / ${DAILY_BUDGET/100:.2f}")
    print(f"⏱️  Run Time: {time.time() - start_time:.2f}s")
    print("✅ MISSION COMPLETE.")


if __name__ == "__main__":
    run_advisor_bot()