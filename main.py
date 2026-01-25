import time
import sys
import env
import current_markets as scout       
import research_strat as researcher
# --- CONFIGURATION ---
DAILY_BUDGET = env.MAX_BET_AMOUNT_CENTS  
MIN_VOLUME = 500         
MAX_RESEARCH_PER_CAT = 15  # Scaled back slightly for speed/stability

def run_advisor_bot(mode="standard"):
    """
    Main Runner.
    mode="standard" -> Fetches specific categories (Politics, Econ).
    mode="daily"    -> Fetches everything expiring in <24h.
    """
    start_time = time.time()
    
    # 1. INITIALIZE CONTEXT
    bot_context = {
        'budget': DAILY_BUDGET,
        'raw_picks': [], 
        'final_orders': []
    }

    print("\n" + "="*60)
    print(f"🤖 BADDIE BOT ADVISOR: {mode.upper()} MODE (${DAILY_BUDGET/100:.2f})")
    print("="*60 + "\n")

    # ======================================================
    # STEP 1: SCOUT (Flexible Data Collection)
    # ======================================================
    print("📡 SCOUT: Scanning Kalshi markets...")
    

    if mode == "daily":
        # Might return a LIST of markets or a Dict
        raw_data = scout.get_daily_markets(max_markets=100)
    else:
        # Returns a DICT {'Politics': [...], 'Economics': [...]}
        raw_data = scout.fetch_current_kalshi_markets(
            ["Sports", "Politics", "Economics"], 
            max_per_category=30
        )
    # ======================================================
    # STEP 1.5: NORMALIZE DATA (The Robust Fix)
    # ======================================================
    # We ensure 'market_data' is ALWAYS a Dictionary: {'Category': [List of Events]}
    
    market_data = {}

    if isinstance(raw_data, list):
        # If we got a flat list (e.g. from daily fetch), wrap it in a generic key
        print(f"   ↳ Detected Flat List ({len(raw_data)} items). Normalizing...")
        market_data['Daily_Movers'] = raw_data
        
    elif isinstance(raw_data, dict):
        # If it's already a dict, just use it
        market_data = raw_data
        
    else:
        print("❌ Error: Scout returned unknown data format.")
        return bot_context

    total_events = sum(len(v) for v in market_data.values())
    print(f"   ↳ Ready to process {total_events} events across {len(market_data)} groups.")

    # ======================================================
    # STEP 2 & 3: FILTER & RESEARCH (Iterative Processing)
    # ======================================================
    print(f"\n🧠 RESEARCHER: Analyzing opportunities...")

    # Now this loop works perfectly for BOTH modes because we normalized it!
    for category, events in market_data.items():
        print(f"\n📂 Processing Group: {category.upper()}")

        target_events = market_data.get(category, [])

        if not target_events:
            print(f"   ⚠️ Skipping: No liquid events found in {category}.")
            continue
            
        print(f"   ↳ Sending {len(target_events)} events to AI Researcher...")

        # --- B. AI RESEARCH ---
        # We pass the cleaned list + category context to the AI
        cat_picks = researcher.research_event_group(category, target_events)
            
        if cat_picks:
            print(f"   ✅ Success: AI identified {len(cat_picks)} opportunities.")
            bot_context['raw_picks'].extend(cat_picks)
        else:
            print(f"   🚫 Pass: AI found no edge.")

    # ======================================================
    # STEP 4: ADVISOR (Format & Return)
    # ======================================================
    if bot_context['raw_picks']:
        print(f"\n⚡ ADVISOR: Formatting {len(bot_context['raw_picks'])} picks for Dashboard...")
        
        formatted_orders = []
        for pick in bot_context['raw_picks']:
            # Calculate Edge
            real_prob = pick.get('estimated_real_prob', 0)
            market_price = pick.get('market_price', 0)
            edge = real_prob - market_price
            
            # Format
            formatted_orders.append({
                'ticker': pick.get('ticker'),
                'title': pick.get('option_name'), 
                'side': "YES",
                'suggested_bet': edge, 
                'confidence': pick.get('confidence_score', 0),
                'reason': f"Implied: {market_price}% vs Real: {real_prob}% | {pick.get('reasoning')}"
            })
            
        bot_context['final_orders'] = formatted_orders
    else:
        print("\n😴 ADVISOR: No picks found to display.")

    print("-" * 65)
    print(f"⏱️  Run Time: {time.time() - start_time:.2f}s")
    
    return bot_context

if __name__ == "__main__":
    run_advisor_bot('daily')
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