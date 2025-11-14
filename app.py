import os
import pandas as pd
import streamlit as st
from dashboard import ui
from data.analysis import DataAnalyst
from dashboard import data_helpers as dh

# Importar o dataframe que vamos usar para testes
# TODO: Lógica para usar o dataframe puxado via main.py


def generate_dashboard():
    # Configurações da página
    st.set_page_config(layout="wide")

    # ============================================
    # CARREGAR DADOS NECESSÁRIOS PARA A PÁGINA
    # ============================================

    df = pd.read_csv('marketed.csv')

    profit, staked, roi = DataAnalyst.calculate_stats(df)
    stats = DataAnalyst.calculate_advanced_stats(df)
    daily_profit = dh.create_daily_summary(df)
    tag_df = dh.create_tag_df(df=df)
    cum_profit = dh.cum_pnl(df=df)


    # ============================================
    # COMEÇAR A GERAR DADOS
    # ============================================


    # Logo da Striker
    st.image('images/striker_logo/logo-reduzido_negativo.svg', width=150)
    
    # Título da Página
    ui.center_text("PolyMarket in-depth Analysis for trader", size=50, bold=True)

    st.divider() 
    header_columns = st.columns(7)
    with header_columns[0]: ui.center_text(f'Profit:', size=24); ui.center_text(ui.float_to_dol(profit), bold=True)
    with header_columns[1]: ui.center_text("ROI", size=24); ui.center_text(ui.float_to_pct(roi), bold=True)
    with header_columns[2]: ui.center_text("Staked", size=24); ui.center_text(ui.float_to_dol(staked), bold=True)
    with header_columns[3]: ui.center_text("Flat Profit", size=24); ui.center_text(ui.float_to_dol(stats['flat_profit']), bold=True)
    with header_columns[4]: ui.center_text("Avg Stake", size=24); ui.center_text(ui.float_to_dol(stats['avg_stake']), bold=True)
    with header_columns[5]: ui.center_text("Median Stake", size=24); ui.center_text(ui.float_to_dol(stats['median_stake']), bold=True)
    with header_columns[6]: ui.center_text("Max Drawdown", size=24); ui.center_text('Loading...')
    
    # Gráfico de Lucro acumulado
    st.divider()
    st.subheader('Cumulative Profit')
    
    
    st.area_chart(
        cum_profit,
        x='Date',
        y='Cumulative Profit'
    )
    
    
    # Divir página em Colunas
    col1, col2 = st.columns([5,2])

    # Exibir os trades do User:
    with col1:
        st.divider()
        st.subheader('Tag Analisys')
        st.dataframe(
            data=tag_df,
            hide_index=True,
            column_order=[
                col for col in tag_df.columns
                if col not in ["Staked"]]
            )
            
        
        # ---------------------------------------
        st.subheader('Closed Positions:')
        formated_df = dh.filter_and_format(df=df)
        st.dataframe(
            data=formated_df,
            hide_index=True,
            column_order=[
                col for col in formated_df.columns
                if col not in ["Slug", "Tags"]
                ]
            )

    with col2:
        # TODO: Botões de Filtro por data
        st.divider()
        st.subheader('Daily Profit')
        st.dataframe(
            data=daily_profit,
            hide_index=True,
            height=880)
    
generate_dashboard()