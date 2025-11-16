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


def user_stats(df: pd.DataFrame) -> None:
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


def cum_profit(df: pd.DataFrame) -> None:
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

    
def daily_profit(df: pd.DataFrame) -> None:
    daily_profit_data = dh.create_daily_summary(df)
    st.subheader('PnL by Date')
    st.dataframe(
        data=daily_profit_data,
        hide_index=True,
        width='stretch'
        )


def closed_positions(df: pd.DataFrame) -> None:
    
    # --- 1. PREPARAR O DF PRINCIPAL ---
    
    st.subheader('Closed Positions:')
    
    # Garante que estamos trabalhando com uma cópia
    df = df.copy()
    
    # Ordena o DataFrame principal por data, do mais recente para o mais antigo
    # Isso é feito ANTES da paginação
    df = df.sort_values(by='endDate', ascending=False)
    
    
    # --- 2. CONFIGURAR PAGINAÇÃO ---
    
    PAGE_SIZE = 20 # Quantos itens por página
    
    # Inicializa o número da página no session_state se não existir
    if 'cp_current_page' not in st.session_state:
        st.session_state.cp_current_page = 1
        
    # Calcula o número total de páginas
    total_rows = len(df)
    total_pages = (total_rows // PAGE_SIZE) + (1 if total_rows % PAGE_SIZE > 0 else 0)
    
    # Garante que a página atual seja válida (importante ao aplicar filtros)
    # Se o filtro diminuiu o total de páginas, reseta para a página 1
    if st.session_state.cp_current_page > total_pages:
        st.session_state.cp_current_page = 1
        
    # Funções para os botões (callbacks)
    def go_to_prev_page():
        st.session_state.cp_current_page = max(1, st.session_state.cp_current_page - 1)
        
    def go_to_next_page():
        st.session_state.cp_current_page = min(total_pages, st.session_state.cp_current_page + 1)

    # Exibe o status da página
    st.write(f"Page: **{st.session_state.cp_current_page}** of **{total_pages}** (Total Trades: {total_rows})")
    
    
    # --- 3. PREPARAR O CSV PARA DOWNLOAD (COM O DF COMPLETO) ---
    
    # Seleciona e renomeia as colunas para o CSV ficar igual à tabela
    csv_df = df[[
        'endDate', 'title', 'outcome',
        'totalBought', 'avgPrice', 'curPrice',
        'realizedPnl', 'slug', 'tags'
    ]].copy()
    
    csv_df = csv_df.rename(columns={
        'endDate': 'End Date',
        'avgPrice': 'Average Price',
        'totalBought': 'Total Bought',
        'realizedPnl': 'Realized Profit',
        'curPrice': 'Current Price',
        'title': 'Event',
        'outcome': 'Bet',
        'slug': 'Slug',
        'tags': 'Tags'
    })
    
    # Converte o DataFrame COMPLETO para um string CSV (em bytes)
    csv_data = csv_df.to_csv(index=False).encode('utf-8')

    
    # --- 4. EXIBIR A PÁGINA ATUAL ---
    
    # Fatiar (Slice) o DataFrame ANTES de formatar
    start_index = (st.session_state.cp_current_page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    
    # Pega a fatia de dados brutos
    df_slice = df.iloc[start_index:end_index]
    
    # Formatar APENAS a fatia (para performance)
    formated_df_slice = dh.filter_and_format_closed(df=df_slice) 
    
    # Exibir o DataFrame fatiado
    st.dataframe(
        data=formated_df_slice,
        hide_index=True,
        column_order=[
            col for col in formated_df_slice.columns
            if col not in ["Slug", "Tags"]
        ],
        width='stretch' # Usa o parâmetro novo (substitui use_container_width)
    )
    
    
    # --- 5. EXIBIR BOTÕES DE NAVEGAÇÃO E DOWNLOAD ---
    
    # Layout dos botões: [Prev] [Next] [Espaço] [Download]
    cols = st.columns([1, 1, 3, 2]) 
    
    with cols[0]:
        st.button(
            "Previous",
            on_click=go_to_prev_page,
            disabled=st.session_state.cp_current_page <= 1,
            key='cp_prev', # Chave única
            use_container_width=True # Botão preenche a coluna
        )
    with cols[1]:
        st.button(
            "Next",
            on_click=go_to_next_page,
            disabled=st.session_state.cp_current_page >= total_pages,
            key='cp_next', # Chave única
            use_container_width=True
        )
    
    # cols[2] é um espaço vazio
    
    with cols[3]:
        st.download_button(
            label="Download all as CSV",
            data=csv_data, # Os dados em bytes do CSV COMPLETO
            file_name=f'closed_positions_{st.session_state.get("selected_wallet", "all")}.csv',
            mime='text/csv',
            use_container_width=True # Botão preenche a coluna
        )


def tag_df(df: pd.DataFrame) -> None:
    st.subheader('PnL by Market')
    st.dataframe(
        data=df,
        hide_index=True,
        column_order=[
            col for col in df.columns
            if col not in ["Staked"]],
        width='stretch'
    )


def time_filter_buttons(df):

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

 
def tag_buttons(tags: list) -> list:

    return st.pills(
        'Select Tags',
        label_visibility="collapsed",
        options=tags,
        selection_mode='multi'
        )

    
def get_filtered_df(
    df: pd.DataFrame,
    tags: list = [],
    start_date=None,
    end_date=None
) -> dict:

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


def copy_trade_simulator(df: pd.DataFrame) -> None:
    cols = st.columns([1,2])
    with cols[0]:
        params = copy_trade_sim_params()
    with cols[1]:
        st.subheader('Simulation Details')
        st.button('Simulate Performance')


def copy_trade_sim_params():
    """
    Exibe um formulário para o usuário configurar
    os parâmetros de copytrade.
    """
    
    st.subheader("Copytrade Strategy Settings")

    # 1. Inicia o formulário
    # Todos os st.widgets dentro do 'with' só serão enviados
    # quando o st.form_submit_button for clicado.
    
    with st.form(key="copytrade_form"):
        
        # --- CAMPO 1: Selected Stake ---
        selected_stake = st.number_input(
            label="Selected Stake ($)",
            min_value=1.00,
            value=100.00,  # Valor inicial padrão
            step=100.00,
            format="%.2f",  # Garante 2 casas decimais
            help="Select the USD size of all trades."
        )
        
        st.divider()

        # --- CAMPO 2: Strategy Options (com descrições) ---
        strategy_options = ["Fully Flat", "Flat Above", "2x Flat"]
        strategy_captions = [
            "Assuming all bets would be made with the selected stake",
            "Assuming all bets that were made with a lower amount than the selected stake would only go through with the original amount bet.",
            "Assuming Only bets twice the selected stake would go through."
        ]
        
        selected_strategy = st.radio(
            label="Select Strategy",
            options=strategy_options,
            captions=strategy_captions, # <-- Usa 'captions' para as descrições
            index=0 # 'Fully Flat' é a opção padrão
        )

        st.divider()

        # --- CAMPO 3: Trigger Value ---
        trigger_value = st.number_input(
            label="Trigger Value ($)",
            min_value=1.00,
            value=5.00, # Valor inicial padrão
            step=1.00,
            format="%.2f",
            help="Min amount in $ to Trigger the CopyTrade." # Descrição no tooltip
        )
        
        st.divider()
        
        # --- CAMPO 4: Position Building (com descrições) ---
        position_options = ["Follow Trader", "In batches"]
        position_captions = [
            "Take and make orders with the same amount as trader until fills the selected stake",
            "Once above the threshold, Make x amount of orders, spliting the total stake."
        ]
        
        selected_positioning = st.radio(
            label="Position Building",
            options=position_options,
            captions=position_captions, # <-- Usa 'captions' para as descrições
            index=0 # 'Follow Trader' é a opção padrão
        )

        # --- Botão de Submissão ---
        submitted = st.form_submit_button("Save Settings")

    # 2. Lógica para rodar DEPOIS que o formulário for enviado
    if submitted:
        st.success("Strategy settings saved!")
        
        # Exemplo: Salvar no session_state para usar depois
        st.session_state.trade_settings = {
            "stake": selected_stake,
            "strategy": selected_strategy,
            "trigger": trigger_value,
            "positioning": selected_positioning
        }

def open_positions(df: pd.DataFrame) -> None:
    
    # --- 1. PREPARAR O DF PRINCIPAL ---
    
    st.subheader('Open Positions:')
    
    # Garante que estamos trabalhando com uma cópia
    df = df.copy()
    
    # Ordena o DataFrame principal por data de vencimento
    df = df.sort_values(by='endDate', ascending=False)
    
    
    # --- 2. CONFIGURAR PAGINAÇÃO ---
    
    PAGE_SIZE = 20
    
    if 'op_current_page' not in st.session_state:
        st.session_state.op_current_page = 1
        
    total_rows = len(df)
    total_pages = (total_rows // PAGE_SIZE) + (1 if total_rows % PAGE_SIZE > 0 else 0)
    
    if st.session_state.op_current_page > total_pages:
        st.session_state.op_current_page = 1
        
    def op_go_to_prev_page():
        st.session_state.op_current_page = max(1, st.session_state.op_current_page - 1)
        
    def op_go_to_next_page():
        st.session_state.op_current_page = min(total_pages, st.session_state.op_current_page + 1)

    st.write(f"Page: **{st.session_state.op_current_page}** of **{total_pages}** (Total Positions: {total_rows})")
    
    
    # --- 3. PREPARAR O CSV PARA DOWNLOAD (DF COMPLETO) ---
    
    csv_columns = [
        'endDate', 'title', 'outcome',
        'totalBought', 'avgPrice', 'curPrice', 'currentValue',
        'cashPnl', 'slug', 'tags'
    ]
    
    csv_columns_exist = [col for col in csv_columns if col in df.columns]
    csv_df = df[csv_columns_exist].copy()
    
    csv_df = csv_df.rename(columns={
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
    
    csv_data = csv_df.to_csv(index=False).encode('utf-8')

    
    # --- 4. EXIBIR A PÁGINA ATUAL ---
    
    start_index = (st.session_state.op_current_page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    df_slice = df.iloc[start_index:end_index]
    
    # Agora chamamos a função de formatação que retorna um Styler
    formated_df_slice = dh.filter_and_format_active(df=df_slice) 
    
    # Exibir o DataFrame fatiado
    st.dataframe(
        data=formated_df_slice, # Passa o objeto Styler
        hide_index=True,
        
        # Para esconder colunas de um Styler, você precisa ler
        # as colunas do '.data' (o DataFrame dentro do Styler)
        column_order=[
            col for col in formated_df_slice.data.columns
            if col not in ["Slug", "Tags"] # Esconde as colunas
        ],
        
        width='stretch' 
    )
    
    
    # --- 5. EXIBIR BOTÕES DE NAVEGAÇÃO E DOWNLOAD ---
    
    cols = st.columns([1, 1, 3, 2]) 
    
    with cols[0]:
        st.button(
            "Previous",
            on_click=op_go_to_prev_page,
            disabled=st.session_state.op_current_page <= 1,
            key='op_prev', 
            use_container_width=True
        )
    with cols[1]:
        st.button(
            "Next",
            on_click=op_go_to_next_page,
            disabled=st.session_state.op_current_page >= total_pages,
            key='op_next', 
            use_container_width=True # <-- O 'S' foi removido daqui
        )
    
    with cols[3]:
        st.download_button(
            label="Download all as CSV",
            data=csv_data,
            file_name=f'open_positions_{st.session_state.get("selected_wallet", "all")}.csv',
            mime='text/csv',
            use_container_width=True
        )