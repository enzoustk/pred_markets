import pandas as pd
import streamlit as st
from dashboard.backend import data_helpers as dh
from dashboard.backend import user_data
from dashboard.ui import elements, formatting
from dashboard.backend import clv


def user_analysis() -> None:
    # Título
    formatting.center_text("PolyMarket in-depth Analysis for trader", size=50, bold=True)

    # Puxar os dados do User
    user_data.select_user() 


    if st.session_state.get("selected_wallet") is None:
        st.info("Por favor, selecione uma carteira para começar.")
        st.stop()

    current_address = st.session_state.get("selected_wallet")


    if (
        st.session_state.get("df") is None
        or st.session_state.get("fetched_wallet") != current_address
    ):
        
        st.session_state["df"] = user_data.get_trades(user_address=current_address)
        st.session_state["fetched_wallet"] = current_address

        if 'clv_data' in st.session_state:
            del st.session_state['clv_data']

    
    if st.session_state["df"].empty:
        st.warning(f"A carteira {current_address} não possui trades registrados.")
        st.stop()
    
    
    st.divider()
    
    
    # Dados de Tags
    tag_df, tags = dh.create_tag_df(df=st.session_state["df"], return_tags=True)
    st.header('Select Filters to Apply:')
    selected_tags = elements.tag_buttons(tags)
    
    _, start_td, end_td = elements.time_filter_buttons(
        df=st.session_state["df"])
    
    
    dataframes = elements.get_filtered_df(
        df=st.session_state["df"],
        tags=selected_tags,
        start_date=start_td,
        end_date=end_td
        )

    # Main Stats

   

    elements.user_stats(df=dataframes['raw'])
    
    st.divider()

    elements.cum_profit(df=dataframes['raw']) 
    
    st.divider()       
    clv.render_clv_section(
        df=dataframes['raw'],
        user_address=current_address
    )
       
    # Exibir os trades do User:
    tabs = st.tabs(
        [
            'Markets Analisys',
            'Open Positions',
            'Closed Positions',
            'CopyTrade Simulator'
            ])
    
    with tabs[0]:
        cols = st.columns([3,1])
        with cols[0]:
            elements.tag_df(df=tag_df)
    
        with cols[1]:
            elements.daily_profit(df=dataframes['raw'])       
            
    with tabs[2]:
        elements.closed_positions(df=dataframes['raw'])
    
    with tabs[3]:
        elements.copy_trade_simulator(df=dataframes['raw'])
