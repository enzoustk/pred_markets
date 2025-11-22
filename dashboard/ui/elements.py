import pandas as pd
import streamlit as st
import plotly.express as px
from helpers import get_exploded_df
from dashboard.ui.formatting import *
from data.analysis import DataAnalyst
from datetime import datetime, timedelta
from dashboard.backend import data_helpers as dh
from dateutil.relativedelta import relativedelta


def top_bar():
        img_cols = st.columns([2.8,3.5])
        with img_cols[1]:
            st.image('images/striker_logo/logo-reduzido_branco.png', width=150)
        center_text('Powered by Striker', size=12)


def user_stats(
    df: pd.DataFrame
    ) -> None:
    profit, staked, roi = DataAnalyst.calculate_stats(df)
    stats = DataAnalyst.calculate_advanced_stats(df)
    
    # --- Linha 1: 4 Métricas Principais ---
    cols1 = st.columns(4)
    cols1[0].metric(label="Profit", value=float_to_dol(profit))
    cols1[1].metric(label="ROI", value=float_to_pct(roi))
    cols1[2].metric(label="Staked", value=float_to_dol(staked))
    cols1[3].metric(label="Flat Profit", value=float_to_units(stats['flat_profit']))

    # --- Linha 2: 3 Métricas Avançadas ---
    cols2 = st.columns(4)
    cols2[0].metric(label="Total Trades", value=len(df))
    cols2[1].metric(label="Avg Stake", value=float_to_dol(stats['avg_stake']))
    cols2[2].metric(label="Median Stake", value=float_to_dol(stats['median_stake']))
    cols2[3].metric(label="Max Drawdown", value='Loading...')


def cum_profit(
    df: pd.DataFrame
    ) -> None:
    cum_profit = dh.cum_pnl(df=df, date_column='endDate')
    
    st.subheader('Cumulative Profit')
    
    fig = px.area(
        cum_profit,
        x='Date',
        y='Cumulative Profit',
    )

    # --- 1. ATUALIZAÇÕES GERAIS (LAYOUT) ---
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Data',
        yaxis_title='Lucro Acumulado ($)',
        yaxis_tickprefix='$',
        
        # --- AQUI: Remove as linhas de grade ---
        xaxis_showgrid=False,
        yaxis_showgrid=False
    )
    
    # --- 2. ATUALIZAÇÕES DA TRACE (LINHA/ÁREA) ---
    fig.update_traces(
        # Suas cores de marca
        line=dict(color='#00ADEF', width=2),   
        fillcolor='rgba(28, 55, 117, 0.2)', # Seu fundo com 20% de opacidade
        
        # --- AQUI: Simplifica o hover (tooltip) ---
        # %{x|%Y-%m-%d} -> Formata a data
        # %{y:$,.2f} -> Formata o valor como $1,234.56
        # <extra></extra> -> Remove o nome da "trace"
        hovertemplate="<b>Data:</b> %{x|%Y-%m-%d}<br><b>Lucro:</b> %{y:$,.2f}<extra></extra>"
    )

    st.plotly_chart(fig, width='stretch')

    
def daily_profit(
    df: pd.DataFrame
    ) -> None:
    daily_profit_data = dh.create_daily_summary(df)
    st.subheader('PnL by Date')
    st.dataframe(
        data=daily_profit_data,
        hide_index=True,
        width='stretch'
        )


def closed_positions(
    df: pd.DataFrame
    ) -> None:
    
    st.subheader('Closed Positions:')
    
    # 1. Preparação dos Dados (Sorting)
    df = df.copy()
    if 'endDate' in df.columns:
        df = df.sort_values(by='endDate', ascending=False)
        
    # 2. Preparação do CSV (Opcional, se quiser nomes bonitos no Excel)
    csv_export_df = df[[
        'endDate', 'title', 'outcome', 'totalBought', 
        'avgPrice', 'curPrice', 'realizedPnl', 'slug', 'tags'
    ]].rename(columns={
        'endDate': 'End Date',
        'avgPrice': 'Average Price',
        'totalBought': 'Total Bought',
        'realizedPnl': 'Realized Profit',
        'curPrice': 'Current Price',
        'title': 'Event',
        'outcome': 'Bet'
    })


    df_config = {
        "hide_index": True,
        'column_config': {
            'Slug': None,
            'Tags': None
        }
    }

    # 4. Chama o Renderizador Paginado
    dh.render_paginated_table(
        df=df,
        unique_key="closed_positions_table", # ID Único Importante
        page_size=20,
        format_func=dh.filter_and_format_closed, # Passa a função, NÃO chama ela ()
        csv_df=csv_export_df,
        csv_file_name=f'closed_positions_{st.session_state.get("selected_wallet", "all")}.csv',
        **df_config # Passa hide_index, etc.
    )


def tag_df(
    df: pd.DataFrame
    ) -> None:
    st.subheader('PnL by Market')
    st.dataframe(
        data=df,
        hide_index=True,
        column_order=[
            col for col in df.columns
            if col not in ["Staked"]],
        width='stretch'
    )


def time_filter_buttons(
    df: pd.DataFrame
    ) -> tuple:

    # Available filter options
    options = [
        "Current Week",
        "Current Month",
        "Previous Month",
        "Last 3 Months",
        "Last 6 Months",
        "Current Year",
        "Last Year",
        "Total",
        "Custom"
    ]

    today = datetime.today()

    # Default values to avoid UnboundLocalError
    start = None
    end = None

    selected = st.pills(
        label="Select Time Range",
        label_visibility="collapsed",
        options=options,
        default="Current Year",
    )

    # ------------------------------------------------------------------
    # Period-based filters
    # ------------------------------------------------------------------

    if selected == "Current Week":
        start = today - timedelta(days=today.weekday())  # Monday of current week
        end = today

    elif selected == "Current Month":
        start = today.replace(day=1)
        end = today

    elif selected == "Previous Month":
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        start = last_day_prev_month.replace(day=1)
        end = last_day_prev_month

    elif selected == "Last 3 Months":
        start = today - relativedelta(months=3)
        end = today

    elif selected == "Last 6 Months":
        start = today - relativedelta(months=6)
        end = today

    elif selected == "Current Year":
        start = today.replace(month=1, day=1)
        end = today

    elif selected == "Last Year":
        start = datetime(today.year - 1, 1, 1)
        end = datetime(today.year - 1, 12, 31)

    elif selected == "Total":
        # no date filtering
        start = None
        end = None

    elif selected == "Custom":
        start, end = st.date_input(
            "Select a custom date range",
            value=(df["endDate"].min(), df["endDate"].max()),
        )

    return selected, start, end

 
def tag_buttons(
    tags: list
    ) -> list:

    return st.pills(
        'Select Tags',
        label_visibility="collapsed",
        options=tags,
        selection_mode='multi'
        )

    
def get_filtered_df(
    df: pd.DataFrame,
    tags: list = [],
    stake: float | None = None,
    start_date=None,
    end_date=None
    ) -> dict:
    
    df = df.copy()

    # Normaliza datas
    df["endDate"] = pd.to_datetime(df['endDate'], format='ISO8601', utc=True).dt.tz_localize(None)

    df["endDate"] = pd.to_datetime(df["endDate"], utc=False, errors="coerce")

    # ---------------------------------------------------------------------
    # 💡 Só aplica filtro se start_date e end_date forem datetime válidos
    # ---------------------------------------------------------------------
    if isinstance(start_date, (datetime, pd.Timestamp)) and \
       isinstance(end_date, (datetime, pd.Timestamp)):
        
        df = df[(df["endDate"] >= start_date) &
                (df["endDate"] <= end_date)]

    if stake is not None:
                # Cria a coluna temporária calculada
        df["calculated_stake"] = df["totalBought"] * df["avgPrice"]

        # Filtra onde o valor calculado é maior que a stake passada
        df = df[df["calculated_stake"] > stake]
    
    # exploded pós-filtro
    exploded_df = get_exploded_df(df=df)

    # ---------------------------------------------------------------------
    # TAG FILTER
    # ---------------------------------------------------------------------
    if tags:
        raw_df = exploded_df[exploded_df["tag"].isin(tags)]
        main_df = dh.filter_and_format_closed(raw_df)
        tag_trades_df = dh.filter_and_format_closed(raw_df)
    else:
        raw_df = df
        main_df = dh.filter_and_format_closed(df)
        tag_trades_df = dh.filter_and_format_closed(exploded_df)

    return {
        "raw": raw_df,
        "main": main_df,
        "exploded": tag_trades_df
    }


def stake(
    ) -> float:
    # 1. Inicializa o valor "Confirmado" se ele ainda não existir
    if "confirmed_stake" not in st.session_state:
        st.session_state.confirmed_stake = 100.00  # Valor inicial padrão

    # --- Funções de Callback (O que acontece ao clicar) ---
    def aplicar_valor():
        # Pega o valor que está escrito no input (acessado pela key) e salva no confirmado
        st.session_state.confirmed_stake = st.session_state.widget_stake

    def resetar_valor():
        # Reseta tanto o valor visual do input quanto o valor confirmado para 0
        st.session_state.widget_stake = 0.00
        st.session_state.confirmed_stake = 0.00

    # --- Interface Visual ---
    
    # O Input (vinculado ao session_state via 'key')
    st.number_input(
        label="Select Stake to Filter ($)",
        min_value=0.00,      # Mudei para 0.00 para permitir o reset zerado
        value=0.0,        # Valor inicial visual
        step=100.00,
        format="%.2f",
        help="Select the min USD size of all trades.",
        key="widget_stake"   # IMPORTANTE: Essa chave conecta o input ao session_state
    )

    # Colunas para os botões ficarem lado a lado
    col1, col2 = st.columns(2)

    with col1:
        # Botão que atualiza o valor real
        st.button("Apply", on_click=aplicar_valor, width='stretch')
    
    with col2:
        # Botão que zera tudo
        st.button("Reset", on_click=resetar_valor, width='stretch')

    # Mostra para o usuário qual valor está VALENDO no momento (opcional, mas útil)
    st.caption(f"Current Filter: **${st.session_state.confirmed_stake:.2f}**")

    # --- Retorno ---
    # Retorna o valor CONFIRMADO, e não o que está sendo digitado no momento
    return st.session_state.confirmed_stake

def open_positions(df: pd.DataFrame) -> None:
    
    st.subheader('Open Positions:')
    
    # --- 1. PREPARAR O DF PRINCIPAL ---
    # Garante cópia e ordena por data de vencimento (decrescente)
    df = df.copy()
    if 'endDate' in df.columns:
        df = df.sort_values(by='endDate', ascending=False)
    
    # --- 2. PREPARAR O CSV PARA DOWNLOAD ---
    # Define as colunas que queremos no Excel/CSV final
    csv_columns = [
        'endDate', 'title', 'outcome',
        'totalBought', 'avgPrice', 'curPrice', 'currentValue',
        'cashPnl', 'slug', 'tags'
    ]
    
    # Filtra colunas existentes e renomeia para ficar bonito no download
    existing_cols = [col for col in csv_columns if col in df.columns]
    csv_export_df = df[existing_cols].copy().rename(columns={
        'endDate': 'End Date',
        'avgPrice': 'Average Price',
        'totalBought': 'Total Bought',
        'cashPnl': 'Unrealized PnL',
        'currentValue': 'Current Value',
        'curPrice': 'Current Price',
        'title': 'Event',
        'outcome': 'Bet',
        'slug': 'Slug',
        'tags': 'Tags'
    })

    # --- 3. CONFIGURAÇÃO VISUAL DA TABELA ---
    # Aqui definimos o que esconder ou formatar na visualização da tela.
    # Como sua função `dh.filter_and_format_active` provavelmente retorna um Styler
    # com as colunas já renomeadas para "Slug" e "Tags", usamos essas chaves.
    df_config = {
        "hide_index": True,
        "column_config": {
            "Slug": None,  # Oculta a coluna Slug
            "Tags": None,  # Oculta a coluna Tags
            # Você pode adicionar outras configurações aqui se o Styler não cobrir tudo
        }
    }

    # --- 4. RENDERIZAÇÃO PAGINADA ---
    dh.render_paginated_table(
        df=df,
        unique_key="open_positions_table", # ID único para não conflitar com Closed Positions
        page_size=20,
        format_func=dh.filter_and_format_active, # A função que aplica cores/estilos
        csv_df=csv_export_df,
        csv_file_name=f'open_positions_{st.session_state.get("selected_wallet", "all")}.csv',
        **df_config # Repassa as configs de colunas
    )