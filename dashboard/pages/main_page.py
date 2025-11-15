import pandas as pd
import streamlit as st
from dashboard import data_helpers as dh
from dashboard.ui import elements


def main_page(df: pd.DataFrame) -> None:    
    # Título
    elements.header()

    # Dados de Tags
    tag_df, tags = dh.create_tag_df(df=df, return_tags=True)
    selected_tags = elements.tag_buttons(tags)
    
    _, start_td, end_td = elements.time_filter_buttons(
        df=df)
    
    
    dataframes = elements.get_filtered_df(
        df=df,
        tags=selected_tags,
        start_date=start_td,
        end_date=end_td
        )

        # Main Stats
    st.divider()
    elements.user_stats(df=dataframes['raw'])
    st.divider()
    
    maincols = st.columns(2)
    with maincols[0]:
        elements.cum_profit(df=dataframes['raw']) 
    
    with maincols[1]:
        st.write('CLV Analysis')
    # Divir página em Colunas desalinhadas
    col1, col2 = st.columns([5,2])
    
    with col1:
        st.divider()
        elements.tag_df(df=tag_df)
    
    with col2:
        # Saldo por Dia...
        st.divider()
        elements.daily_profit(df=dataframes['raw'])

    # Exibir os trades do User:
    st.divider()
    elements.closed_positions(df=dataframes['raw'])