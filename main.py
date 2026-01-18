import time
import sys
import env

# --- IMPORT MODULES ---
try:
    import current_markets as scout       
    import research_strat as researcher   
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Missing a script file. Details: {e}")
    sys.exit(1)

# --- CONFIGURATION ---
DAILY_BUDGET = env.MAX_BET_AMOUNT_CENTS  
MIN_VOLUME = 500         
MAX_RESEARCH_PER_CAT = 15  # Scaled back slightly for speed/stability

def run_advisor_bot():
    start_time = time.time()
    
    # 1. INITIALIZE CONTEXT
    bot_context = {
        'raw_picks': [] 
    }

    print("\n" + "="*60)
    print(f"🤖 BADDIE BOT ADVISOR: Omni-Market Mode (${DAILY_BUDGET/100:.2f})")
    print("="*60 + "\n")

    # ======================================================
    # STEP 1: SCOUT (Data Collection)
    # ======================================================
    print("📡 SCOUT: Scanning Kalshi markets across all categories...")
    
    try:
        # Fetches categories like Politics, Economics, Sports, etc.
        raw_market_data = scout.fetch_current_kalshi_markets(["Sports", "Politics", "Economics"], max_per_category=30)
    except Exception as e:
        print(f"❌ CRITICAL SCOUT FAILURE: {e}")
        return

    # ======================================================
    # STEP 2 & 3: FILTER & RESEARCH (Iterative Processing)
    # ======================================================
    print(f"\n🧠 RESEARCHER: Analyzing categories and finding edges...")

    # We loop through the dictionary keys (categories) and values (lists of events)
    for category, events in raw_market_data.items():
        print(f"\n📂 Processing Category: {category.upper()}")
        
        # --- A. LIQUIDITY TRAP FILTER ---
        # Keep only events with volume > MIN_VOLUME
        target_events = raw_market_data.get(category, [])

        if not target_events:
            print(f"   ⚠️ Skipping: No liquid events found in {category}.")
            continue
            
        print(f"   ↳ Sending {len(target_events)} liquid events to AI Researcher...")

        # --- B. AI RESEARCH ---
        try:
            # FIX: We pass the 'liquid_events' list directly to the researcher.
            # We also pass 'category' so the AI knows the context.
            cat_picks = researcher.research_event_group(category, target_events)
            
            if cat_picks:
                print(f"   ✅ Success: AI identified {len(cat_picks)} opportunities.")
                bot_context['raw_picks'].extend(cat_picks)
            else:
                print(f"   🚫 Pass: AI found no edge in this category.")
                
        except Exception as e:
            print(f"   ❌ Error researching {category}: {e}")
            continue

    # ======================================================
    # STEP 4: REPORTING
    # ======================================================
    print("\n🚀 FINAL STRATEGY REPORT")
    print("-" * 65)
    # We display the raw picks directly since we skipped the math/advisor step for now
    print("-" * 65)

    if not bot_context['raw_picks']:
        print("🤷‍♂️ AI Result: No high-value edges found today.")
    else:
        for rec in bot_context['raw_picks']:
            # Handle potential key name variations safely
            name = rec.get('option_name') or rec.get('pick_name', 'Unknown')
            price = rec.get('market_price') or rec.get('market_implied_prob', 0)
            real_prob = rec.get('estimated_real_prob', 0)
            conf = rec.get('confidence_score') or rec.get('confidence', 0)
            reason = rec.get('reasoning') or rec.get('analysis', 'No reason given.')

            print(f"OPTION: {name} ({rec.get('ticker', 'N/A')})")
            print(f"   💰 Price: {price}¢  vs  🧠 Real Prob: {real_prob}%")
            print(f"   🔥 Confidence: {conf}/10")
            print(f"   📝 Reason: {reason}\n")

    print("-" * 65)
    print(f"⏱️  Total Run Time: {time.time() - start_time:.2f}s")
    print("✅ MISSION COMPLETE.")

if __name__ == "__main__":
    run_advisor_bot()
''' 
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
'''
'''
        # --- A. LIQUIDITY TRAP FILTER ---
        # Keep only events with volume > MIN_VOLUME
        target_events = raw_market_data.get(category, [])
        
        # Sort by volume and trim to save AI tokens
        liquid_events = sorted(liquid_events, key=lambda x: x.get('volume', 0), reverse=True)[:MAX_RESEARCH_PER_CAT]
'''