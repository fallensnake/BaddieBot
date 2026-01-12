import time
import sys
import env

# --- IMPORT MODULES ---
try:
    import current_markets as scout       # Your updated fetcher (fetch_event_batches)
    import research_strat as researcher   # Your updated researcher (research_event_group)
    import strategic_math as advisor      # Your math module
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Missing a script file. Details: {e}")
    sys.exit()

# --- CONFIGURATION ---
DAILY_BUDGET = env.MAX_BET_AMOUNT_CENTS  # Convert cents to dollars if needed
MAX_RESEARCH_ITEMS = 3   # How many EVENTS to research (e.g., 3 elections)
MIN_VOLUME = 500         # Filter events with <$500 total volume

def run_advisor_bot():
    print("\n" + "="*60)
    print(f"🤖 BADDIE BOT ADVISOR: Multi-Option Event Mode (${DAILY_BUDGET:.2f})")
    print("="*60 + "\n")

    # STEP 1: SCOUTING
    # ------------------------------------------------------
    print("📡 SCOUT: Scanning Kalshi for active multi-outcome events...")
    try:
        # Use the NEW function that gets events + options
        # Returns dict: {'Politics': [EventObj, ...], 'Economics': [...]}
        categorized_events = scout.fetch_event_batches(max_per_category=10) 
    except Exception as e:
        print(f"❌ Scout failed: {e}")
        return

    # Flatten the dictionary into a single list of events for sorting
    all_events = []
    for category, event_list in categorized_events.items():
        for event in event_list:
            event['category'] = category # Tag it so we know where it came from
            all_events.append(event)

    print(f"✅ SCOUT: Found {len(all_events)} total complex events.")

    # STEP 2: FILTERING (The "Liquidity Trap" Check)
    # ------------------------------------------------------
    print(f"\n🔍 FILTER: Selecting top {MAX_RESEARCH_ITEMS} liquid events...")
    
    # Filter by TOTAL event volume (sum of all options)
    candidates = [e for e in all_events if e.get('total_volume', 0) > MIN_VOLUME]
    
    # Sort by volume (highest first)
    candidates = sorted(candidates, key=lambda x: x.get('total_volume', 0), reverse=True)
    
    
    if not candidates:
        print("⚠️ FILTER: No events met the liquidity threshold.")
        return

    # Display what we found (showing options)
    for i, e in enumerate(candidates):
        print(f"\n   {i+1}. [EVENT] {e['title']} (${e['total_volume']:,} vol)")
        # Show top 3 options as a preview
        for opt in e['options'][:3]:
            print(f"      - {opt['name']}: {opt['price']}¢")
        if len(e['options']) > 3:
            print(f"      ... and {len(e['options'])-3} more options.")

    # STEP 3: RESEARCHING
    # ------------------------------------------------------
    print(f"\n🧠 RESEARCHER: Analyzing {len(candidates)} events with AI...")
    
    # We need to loop through them because your researcher function 
    # likely takes a category and a list. Since we flattened them, 
    # let's just re-group them or pass them one by one if preferred.
    # For efficiency, we'll process them in one batch if possible, 
    # or iterate. Here, I'll assume we iterate to be safe.
    
    research_results = []
    
    # Group by category again to use your batch function efficiently
    # (Or you can just modify research_strat to take a list of mixed events)
    from collections import defaultdict
    events_by_cat = defaultdict(list)
    for e in candidates:
        events_by_cat[e['category']].append(e)
        
    for category, events in events_by_cat.items():
        # Using the new 'research_event_group' function
        picks = researcher.research_event_group(category, events)
        if picks:
            research_results.extend(picks)
            
    if not research_results:
        print("🚫 RESEARCHER: AI found no viable edges or decided to PASS.")
        return

    # STEP 4: ADVISING
    # ------------------------------------------------------
    print("\n" + "-"*60)
    
    # We need to adapt the research results to what the advisor expects.
    # The new researcher returns a specific structure. 
    # If advisor expects {ticker, yes_price, analysis}, ensure we map it.
    
    # Assuming 'advisor_math' takes the list of picks and distributes budget
    recommendations = advisor.get_advisor_recommendations(
        research_results, # Pass the list of picks
        total_daily_budget=DAILY_BUDGET
    )
    
    # Handle the output
    if isinstance(recommendations, str):
        print(f"📢 ADVICE: {recommendations}")
    else:
        print(f"🚀 FINAL STRATEGY REPORT ({time.strftime('%Y-%m-%d')})")
        print("-" * 60)
        print(f"{'PICK':<20} | {'BET SIZE':<10} | {'CONFIDENCE':<10} | {'REASON'}")
        print("-" * 60)
        
        for rec in recommendations:
            # Adjust keys based on what your advisor returns
            ticker = rec.get('ticker') or rec.get('pick_name', 'Unknown')
            # Truncate name if too long
            display_name = (ticker[:18] + '..') if len(ticker) > 20 else ticker
            
            print(f"{display_name:<20} | {rec['suggested_bet']:<10} | {rec.get('confidence', 'High'):<10} | {rec.get('reason', '')[:45]}...")
            print("-" * 60)
            
    print("\n✅ MISSION COMPLETE.")

if __name__ == "__main__":
    run_advisor_bot()