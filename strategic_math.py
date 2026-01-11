import math
import env

def calculate_kelly_bet(ai_probability, market_price_cents, bankroll, daily_limit_remaining, kelly_fraction=0.25):
    """
    Calculates the optimal bet size based on edge, constrained by bankroll and daily limits.
    
    Args:
        ai_probability (float): 0.0 to 1.0 (e.g., 0.75)
        market_price_cents (int): 1 to 99 (e.g., 60)
        bankroll (float): Total available funds in dollars
        daily_limit_remaining (float): How much of the $10 limit is left
        kelly_fraction (float): Safety multiplier (0.25 is standard to avoid ruin)
    """
    
    market_prob = market_price_cents / 100.0
    
    # 1. Check if we actually have an edge
    if ai_probability <= (market_prob + 0.05): # Minimum 5% edge required to trade
        return 0, 0
        
    # 2. Kelly Criterion for Binary Options
    # Formula: f = (p - q/b) simplified to (p - price) / (1 - price)
    kelly_percentage = (ai_probability - market_prob) / (1 - market_prob)
    
    # 3. Apply Fractional Kelly (Safety)
    safe_kelly = kelly_percentage * kelly_fraction
    
    # 4. Calculate raw bet amount
    raw_bet_amount = bankroll * safe_kelly
    
    # 5. Apply Constraints
    # Constraint A: Cannot bet more than daily limit remaining
    bet_amount = min(raw_bet_amount, daily_limit_remaining)
    
    # Constraint B: Minimum bet is usually roughly $1-$2 to make it worth it
    if bet_amount < 1.00:
        return 0, 0

    # 6. Calculate Contract Count
    # Price is in cents, so we convert dollars to cents
    contract_price_dollars = market_price_cents / 100.0
    count = math.floor(bet_amount / contract_price_dollars)
    
    return count, round(count * contract_price_dollars, 2)

def get_advisor_recommendations(research_results, total_daily_budget=env.MAX_BET_AMOUNT_CENTS):
    """
    Distributes a fixed budget across researched markets based on 'Edge'.
    
    research_results: A list of dicts containing {ticker, question, ai_prob, market_prob}
    total_daily_budget: Your parameter (default $10)
    """
    
    # 1. Calculate the 'Edge' for each market (Difference between AI and Market)
    active_opportunities = []
    total_edge_points = 0
    
    for res in research_results:
        # Only look at BUY recommendations
        if res['analysis']['verdict'] != "PASS":
            ai_prob = res['analysis']['my_estimated_probability']
            market_prob = res['market']['yes_price'] / 100.0
            
            # Absolute edge (e.g., AI says 70%, Market says 50%, Edge = 0.20)
            edge = max(0, abs(ai_prob - market_prob))
            
            if edge > 0.05: # Minimum 5% edge to even consider it
                res['edge_score'] = edge
                active_opportunities.append(res)
                total_edge_points += edge

    if not active_opportunities:
        return "🚫 No strong edges found today. Keep your $10."

    # 2. Distribute the $10 budget proportionally to the edge
    print(f"🎯 ADVISOR REPORT: Distributing ${total_daily_budget} across {len(active_opportunities)} markets\n")
    
    recommendations = []
    for op in active_opportunities:
        # Weight = (This Edge / Sum of all Edges)
        weight = op['edge_score'] / total_edge_points
        suggested_spend = total_daily_budget * weight
        
        recommendations.append({
            "ticker": op['market']['ticker'],
            "question": op['market']['question'],
            "suggested_bet": f"${suggested_spend:.2f}",
            "reason": op['analysis']['reasoning'],
            "confidence": op['analysis']['confidence']
        })
        
    return recommendations