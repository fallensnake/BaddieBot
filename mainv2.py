import time
import sys
import env
import current_markets as scout       
import research_strat as researcher

# --- CONFIGURATION ---
DAILY_BUDGET = env.MAX_BET_AMOUNT_CENTS  
MIN_VOLUME = 500         
MAX_RESEARCH_PER_CAT = 15  # Scaled back slightly for speed/stability

def run_advisor_bot(mode="standard", categories=None):
    """
    Main Runner.
    
    Args:
        mode (str): "standard" (Category Search) or "daily" (Expiring <24h).
        categories (list): Optional list of categories to filter by. 
                           Default: ["Sports", "Politics", "Economics"]
    """
    start_time = time.time()
    
    # 1. SET DEFAULTS
    if categories is None:
        categories = ["Sports", "Politics", "Economics"]

    # Normalize user input to lowercase for consistent matching
    target_cats_lower = [c.lower() for c in categories]

    # 2. INITIALIZE CONTEXT
    bot_context = {
        'budget': DAILY_BUDGET,
        'raw_picks': [], 
        'final_orders': []
    }

    print("\n" + "="*60)
    print(f"🤖 BADDIE BOT ADVISOR: {mode.upper()} MODE (${DAILY_BUDGET/100:.2f})")
    print(f"🎯 Targets: {', '.join(categories)}")
    print("="*60 + "\n")

    # ======================================================
    # STEP 1: SCOUT (Flexible Data Collection)
    # ======================================================
    print("📡 SCOUT: Scanning Kalshi markets...")
    
    raw_data = None

    try:
        if mode == "daily":
            # Daily mode fetches EVERYTHING expiring soon first
            all_daily = scout.get_daily_markets(max_markets=100)
            
            # We must manually filter by category here because get_daily_markets collects all
            raw_data = [
                m for m in all_daily 
                if m.get('category', '').lower() in target_cats_lower
            ]
            print(f"   ↳ Filtered {len(all_daily)} daily markets down to {len(raw_data)} in target categories.")
            
        else:
            # Standard mode lets the Scout handle the category filtering efficiently
            raw_data = scout.fetch_current_kalshi_markets(
                categories, 
                max_per_category=30
            )
            
    except Exception as e:
        print(f"❌ CRITICAL SCOUT FAILURE: {e}")
        return bot_context

    # ======================================================
    # STEP 1.5: NORMALIZE DATA
    # ======================================================
    market_data = {}

    if isinstance(raw_data, list):
        # Flat List (Daily Mode) -> Wrap in a generic key
        if raw_data:
            print(f"   ↳ Normalizing {len(raw_data)} items...")
            market_data['Daily_Movers'] = raw_data
        else:
            print("   ⚠️ No markets found matching criteria.")
            
    elif isinstance(raw_data, dict):
        # Dictionary (Standard Mode) -> Use as is
        market_data = raw_data
        
    else:
        print("❌ Error: Scout returned unknown data format.")
        return bot_context

    total_events = sum(len(v) for v in market_data.values())
    print(f"   ↳ Ready to process {total_events} events.")

    # ======================================================
    # STEP 2 & 3: RESEARCHER
    # ======================================================
    print(f"\n🧠 RESEARCHER: Analyzing opportunities...")

    for category, events in market_data.items():
        if not events:
            continue

        print(f"\n📂 Processing Group: {category.upper()}")
        print(f"   ↳ Sending {len(events)} events to AI Researcher...")

        # --- AI RESEARCH ---
        try:
            cat_picks = researcher.research_event_group(category, events)
            
            if cat_picks:
                print(f"   ✅ Success: AI identified {len(cat_picks)} opportunities.")
                bot_context['raw_picks'].extend(cat_picks)
            else:
                print(f"   🚫 Pass: AI found no edge.")
                
        except Exception as e:
            print(f"   ❌ Error researching {category}: {e}")
            continue

    # ======================================================
    # STEP 4: ADVISOR
    # ======================================================
    if bot_context['raw_picks']:
        print(f"\n⚡ ADVISOR: Formatting {len(bot_context['raw_picks'])} picks...")
        
        formatted_orders = []
        for pick in bot_context['raw_picks']:
            # Calculate Edge
            real_prob = pick.get('estimated_real_prob', 0)
            market_price = pick.get('market_price', 0)
            edge = real_prob - market_price
            
            formatted_orders.append({
                'ticker': pick.get('ticker'),
                'title': pick.get('option_name'), 
                'side': "YES",
                'suggested_bet': edge, 
                'confidence': pick.get('confidence_score', 0),
                'reason': f"Implied: {market_price}% vs Real: {real_prob}% | {pick.get('reasoning')}"
            })
            
        # Sort by Confidence Score (Descending)
        formatted_orders.sort(key=lambda x: x['confidence'], reverse=True)
        bot_context['final_orders'] = formatted_orders
        
    else:
        print("\n😴 ADVISOR: No picks found to display.")

    print("-" * 65)
    print(f"⏱️  Run Time: {time.time() - start_time:.2f}s")
    
    return bot_context

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # Example: Run standard mode but ONLY for Politics
    run_advisor_bot('standard', categories=["Politics"])
    
    # Example: Run daily mode for EVERYTHING (default)
    # run_advisor_bot('daily')