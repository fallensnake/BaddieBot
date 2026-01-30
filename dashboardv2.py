import streamlit as st
import pandas as pd
import time
import mainv2  # Import your existing bot logic
'''streamlit run dashboardv2.py'''
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
    
    st.subheader("🎯 Target Categories")
    
    # 1. MULTI-SELECT WIDGET
    # Returns a list of strings, e.g. ['Politics', 'Economics']
    available_cats = [
        "Politics", "Economics", "Sports",'Mentions', 
        "Science", "Technology", "Crypto", "Culture", 'Climate'
    ]
    selected_cats = st.multiselect(
        "Select Markets to Scout:",
        options=available_cats,
        default=["Politics", "Economics", "Sports"] # Default selection
    )
    
    st.divider()
    st.subheader("🚀 Select Strategy")
    
    # Create two columns for side-by-side buttons
    col1, col2 = st.columns(2)

    # BUTTON 1: STANDARD (User-Selected Categories)
    if col1.button("Standard", type="primary", use_container_width=True):
        
        # Validation: Make sure they picked at least one category
        if not selected_cats:
            st.error("⚠️ Please select at least one category above!")
        else:
            st.info(f"Targeting: {', '.join(selected_cats)}")
            
            with st.spinner(f"🤖 Scouting {len(selected_cats)} categories..."):
                try:
                    # PASS THE USER SELECTION TO YOUR BOT HERE
                    results = mainv2.run_advisor_bot(
                        mode="standard", 
                        categories=selected_cats
                    )
                    
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
                # Daily mode ignores the specific category list and looks for speed
                results = mainv2.run_advisor_bot(mode="daily")
                
                st.session_state['results'] = results
                st.session_state['last_run'] = time.strftime("%Y-%m-%d %H:%M:%S")
                st.success("Daily Scan Complete!")
                
            except Exception as e:
                st.error(f"Error: {e}")

# --- MAIN DISPLAY AREA ---
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
    st.info("👋 Ready to start. Select categories in the sidebar and click 'Standard'.")