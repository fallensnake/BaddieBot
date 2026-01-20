import streamlit as st
import pandas as pd
import time
import main  # Import your existing bot logic
'''streamlit run dashboard.py'''
# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AdvAIsor",
    page_icon=":smiling_imp:",
    layout="wide"
)

# --- HEADER ---
st.title("🤖  Market Advisor")
st.markdown("### *Artificial Intelligence Prediction Market Analyst*")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    budget = st.number_input("Daily Budget ($)", value=100)
    
    st.divider()
    
    st.subheader("🚀 Select Strategy")
    
    # Create two columns for side-by-side buttons
    col1, col2 = st.columns(2)

    # BUTTON 1: STANDARD (Specific Categories)
    if col1.button("Standard", type="primary", use_container_width=True):
        st.info("Targeting: Politics, Econ, Sports")
        with st.spinner("🤖 Scouting specific categories..."):
            try:
                # Mode="standard" triggers the category-based fetch
                results = main.run_advisor_bot(mode="standard")
                st.session_state['results'] = results
                st.session_state['last_run'] = time.strftime("%Y-%m-%d %H:%M:%S")
                st.success("Standard Scan Complete!")
            except Exception as e:
                st.error(f"Error: {e}")

    # BUTTON 2: DAILY (Expires < 24h)
    if col2.button("Daily ⚡", type="secondary", use_container_width=True):
        st.info("Targeting: All markets expiring < 24h")
        with st.spinner("⚡ Scouting daily movers..."):
            try:
                # Mode="daily" triggers the expiration-based fetch
                results = main.run_advisor_bot(mode="daily")
                st.session_state['results'] = results
                st.session_state['last_run'] = time.strftime("%Y-%m-%d %H:%M:%S")
                st.success("Daily Scan Complete!")
            except Exception as e:
                st.error(f"Error: {e}")
# --- MAIN DISPLAY area ---
if 'results' in st.session_state:
    data = st.session_state['results']
    
    # 1. Summary Metrics
    col1, col2, col3 = st.columns(3)
    final_orders = data.get('final_orders', [])
    
    total_spend = sum(item['suggested_bet'] for item in final_orders)
    
    col1.metric("💰 Total Capital Allocated", f"${total_spend/100:.2f}")
    col2.metric("📊 Opportunities Found", len(final_orders))
    col3.metric("🕒 Last Update", st.session_state['last_run'])

    st.divider()

    # 2. Detailed Strategy Table
    st.subheader("🎯 Recommended Bets")
    
    if final_orders:
        # Convert list of dicts to a clean DataFrame for display
        df = pd.DataFrame(final_orders)
        
        # Clean up columns for the user
        # We assume your keys are: 'ticker', 'title', 'side', 'suggested_bet', 'confidence', 'reason'
        display_df = df.copy()
        
        # Format the Bet Size to $
        if 'suggested_bet' in display_df.columns:
            display_df['Bet Size'] = display_df['suggested_bet'].apply(lambda x: f"${x/100:.2f}")
        
        # Rename columns for clarity
        display_df = display_df.rename(columns={
            'ticker': 'Ticker',
            'title': 'Event',
            'side': 'Side',
            'confidence': 'Conf (1-10)',
            'reason': 'AI Reasoning'
        })
        
        # Select and Reorder columns to show only what matters
        cols_to_show = ['Event', 'Side', 'Bet Size', 'Conf (1-10)', 'AI Reasoning']
        # Filter to only existing columns (prevents crash if a key is missing)
        final_cols = [c for c in cols_to_show if c in display_df.columns]
        
        # Display professional interactive table
        st.dataframe(
            display_df[final_cols], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "AI Reasoning": st.column_config.TextColumn("AI Reasoning", width="large"),
            }
        )
    else:
        st.warning("No bets met the criteria today.")

    # 3. Raw Logs (Hidden inside an expander)
    with st.expander("🔍 View Raw Scout Data & Debug Logs"):
        st.json(data)

else:
    # Default State
    st.info("👋 Ready to start. Click 'RUN ANALYSIS' in the sidebar.")