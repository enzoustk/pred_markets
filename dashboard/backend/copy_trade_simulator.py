import pandas as pd
import streamlit as st
from helpers import safe_divide
from dashboard.ui import elements
import plotly.graph_objects as go
from api.fetch_clv import fetch_clv
from dashboard.backend import data_helpers as dh

def run(
    df: pd.DataFrame,
    tags: list
    ) -> None:
    cols = st.columns([1, 2])
    
    with cols[0]:
        params = get_params(tags)
        st.divider()
        
        simulate = st.button('Simulate Performance', type="primary")
        
    with cols[1]:

        if simulate:
            st.subheader('Simulation Details')
            with st.spinner("Running Simulation..."):
                
                # 2. Gera o novo DF Simulado
                sim_df = get_df(
                    df=df,
                    params=params 
                )
                
                if not sim_df.empty:

                    final_result_df = run_flat_sim_calculation(
                        df=sim_df,
                        copy_stake=params['stake'],
                        trigger=params['trigger'],
                        strategy=params['strategy'],
                        sell_strategy=params['sell_strategy']
                    )
                    
                    st.session_state['simulation_result'] = final_result_df
                    
                    st.success("Simulation Ended")
                    
                else:
                    st.warning("No trade found for the given filters.")
                    # Limpa resultados anteriores se a nova busca for vazia
                    st.session_state['simulation_result'] = None

        if st.session_state.get('simulation_result') is not None:
            display_sim_results(st.session_state['simulation_result'])


def get_params(
    tags: list
    ) -> dict:
    """
    Exibe os widgets de configuração e retorna um dicionário com os valores atuais.
    Não utiliza st.form para garantir que os dados lidos pelo botão 'Simulate'
    sejam sempre os que estão visíveis na tela (WYSIWYG).
    """
    
    st.subheader("Copytrade Strategy Settings")

    # 1- Stake 
    stake = st.number_input(
        label="Selected Stake ($)",
        min_value=1.00,
        step=100.00,
        format="%.2f",
        value=100.00
    )
    
    st.divider()
    
    # 2- Tags
    selected_tags = st.pills(
        label='Select Markets',
        options=tags,
        selection_mode='multi',
        default=[]
    )
    
    st.divider()

    # 3- Strategy
    strategy_options = ["Flat Staking", "Capped", "2x Flat"]
    strategy_captions = [
        "Assuming all bets would be made with the selected stake",
        "Bets lower than stake are copied as is. Higher bets are capped to the selected Stake.",
        "Only bets twice the selected stake would go through."
    ]
    
    selected_strategy = st.radio(
        label="Select Strategy Assumptions",
        options=strategy_options,
        captions=strategy_captions,
        index=0
    )

    st.divider()

    # 4- Trigger
    trigger_value = st.number_input(
        label="Trigger Value ($)",
        min_value=0.00,
        step=1.00,
        format="%.2f",
        value=5.00,
        help="Min amount in $ traded by the original user to Trigger the CopyTrade."
    )
    
    st.divider()
    
    sell_options = ["Proportional", "One Sell Dumps All", "Never Sell"]
    sell_captions = [
        "Standard: If trader sells 10%, you sell 10%.",
        "Panic Mode: If trader sells any amount, you close the entire position.",
        "Diamond Hands: Ignore all sell signals. Hold until settlement."
    ]
    
    selected_sell_strat = st.radio(
        label="Select Sell Strategy",
        options=sell_options,
        captions=sell_captions,
        index=0
    )
        
    return {
        "user": st.session_state.get('selected_wallet', ''),
        "stake": stake,
        "strategy": selected_strategy,  
        "trigger": trigger_value,
        "selected_tags": selected_tags,
        "sell_strategy": selected_sell_strat,
    }


def get_df(
    df: pd.DataFrame,
    params: dict
    ) -> pd.DataFrame:
    """
    Orquestra a filtragem e busca de dados da API (Fetch CLV).
    Recebe 'params' explicitamente para garantir consistência.
    """
    
    filtered_data_dict = filter_df(df, params)
    
    trades_df = fetch_clv(
        df=filtered_data_dict['raw'],
        user_address=params.get('user')
    )
    
    if trades_df.empty:
        return pd.DataFrame()

    won_map = df.drop_duplicates('asset').set_index('asset')['curPrice']
    trades_df['won'] = trades_df['asset'].map(won_map)

    return trades_df
    
    
def filter_df(
    df: pd.DataFrame,
    params: dict
    ) -> dict:
    """
    Wrapper para chamar o elements.get_filtered_df com os parâmetros corretos.
    """
    return elements.get_filtered_df(
        df=df,
        tags=params['selected_tags'],
        stake=params['stake'],
    )


def run_flat_sim_calculation(
    df: pd.DataFrame,
    copy_stake: float,
    trigger: float,
    strategy: str,
    sell_strategy: str,
    ) -> pd.DataFrame:
    
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        df = df.sort_values(by='timestamp', ascending=True)

    grouped = df.groupby('asset')
    copy_trade_list = [] 
    
    for _, asset_df in grouped:
        
        # --- INICIALIZAÇÃO ---
        trader_shares = 0.0
        trader_usdc = 0.0 
        trader_realized_profit = 0.0 
        
        trader_gross_bought_usd = 0.0 
        trader_gross_shares_bought = 0.0 
        
        trader_gross_sold_usd = 0.0 
        trader_gross_shares_sold = 0.0 
        
        trader_buy_txs = 0
        trader_sell_txs = 0

        # Copy
        copy_shares = 0.0
        copy_usdc = 0.0   
        copy_realized_profit = 0.0
        
        copy_gross_bought_usd = 0.0
        copy_gross_shares_bought = 0.0
        
        copy_gross_sold_usd = 0.0
        copy_gross_shares_sold = 0.0
        
        copy_buy_txs = 0
        copy_sell_txs = 0
        
        # --- LOOP ---
        for _, row in asset_df.iterrows():
            side = row['side'].upper()
            price = float(row['price'])
            shares = float(row['size'])
            usdcSize = shares * price 
            
            # === COMPRA ===
            if side == 'BUY':
                trader_buy_txs += 1
                trader_shares += shares
                trader_usdc += usdcSize 
                
                trader_gross_bought_usd += usdcSize
                trader_gross_shares_bought += shares
            
                if not trader_usdc > trigger:
                    continue
                
                # Lógica de Stake (Copy)
                target_exposure = 0.0
                if strategy == 'Flat Staking':
                    target_exposure = copy_stake
                
                elif strategy == 'Capped':
                    target_exposure = min(trader_usdc, copy_stake)
                
                elif strategy == '2x Flat':
                    target_exposure = copy_stake if trader_usdc >= (copy_stake * 2) else 0.0
                
                amount_to_buy = target_exposure - copy_usdc
                
                if amount_to_buy <= 0.01: continue 
                
                remaining_budget = copy_stake - copy_usdc
                
                real_buy_amount = min(amount_to_buy, remaining_budget)
                
                if real_buy_amount <= 0.001: continue

                copy_buy_txs += 1
                copy_usdc += real_buy_amount
                
                shares_bought_copy = (real_buy_amount / price)
                copy_shares += shares_bought_copy
                
                copy_gross_bought_usd += real_buy_amount
                copy_gross_shares_bought += shares_bought_copy
            
            # === VENDA ===
            elif side == 'SELL':
                trader_sell_txs += 1
                
                trader_gross_sold_usd += usdcSize 
                trader_gross_shares_sold += shares
                
                trader_shares_before = trader_shares
                trader_usdc_before = trader_usdc
                
                trader_sell_ratio = (shares / trader_shares_before) if trader_shares_before > 0 else 0.0
                if trader_sell_ratio > 1.0: trader_sell_ratio = 1.0
                
                trader_shares -= shares
                cost_basis_removed = trader_usdc_before * trader_sell_ratio
                trader_usdc -= cost_basis_removed
                trader_realized_profit += (usdcSize - cost_basis_removed)

                if copy_shares <= 0:
                    continue
                
                copy_sell_ratio = 0.0
                
                if sell_strategy == 'Proportional':
                    copy_sell_ratio = trader_sell_ratio
                elif sell_strategy == 'One Sell Dumps All':
                    copy_sell_ratio = 1.0 if shares > 0 else 0.0
                elif sell_strategy == 'Never Sell':
                    copy_sell_ratio = 0.0
                
                if copy_sell_ratio <= 0:
                    continue

                copy_sell_txs += 1
                copy_shares_before = copy_shares
                copy_usdc_before = copy_usdc 
                
                copy_shares_to_sell = copy_shares_before * copy_sell_ratio
                copy_sell_value = copy_shares_to_sell * price
                
                copy_gross_sold_usd += copy_sell_value
                copy_gross_shares_sold += copy_shares_to_sell
                
                copy_cost_basis_removed = copy_usdc_before * copy_sell_ratio
                
                copy_shares -= copy_shares_to_sell
                copy_usdc -= copy_cost_basis_removed
                copy_realized_profit += (copy_sell_value - copy_cost_basis_removed)
                
        # === FECHAMENTO & CÁLCULO DE MÉDIAS ===
        try:
            raw_won = asset_df['won'].iloc[0]
            won = 1 if float(raw_won) >= 0.9 else 0
        except:
            won = 0 
        
        final_value_trader = trader_shares if won else 0.0
        final_value_copy = copy_shares if won else 0.0
        
        trader_live_profit = final_value_trader - trader_usdc
        copy_live_profit = final_value_copy - copy_usdc
        
        trader_total_profit = trader_realized_profit + trader_live_profit
        copy_total_profit = copy_realized_profit + copy_live_profit
        
        # Avgs
        t_avg_buy  = safe_divide(trader_gross_bought_usd, trader_gross_shares_bought, 0.0)
        t_avg_sell = safe_divide(trader_gross_sold_usd, trader_gross_shares_sold, 0.0)
        t_avg_held = safe_divide(trader_usdc, trader_shares, 0.0)

        c_avg_buy  = safe_divide(copy_gross_bought_usd, copy_gross_shares_bought, 0.0)
        c_avg_sell = safe_divide(copy_gross_sold_usd, copy_gross_shares_sold, 0.0)
        c_avg_held = safe_divide(copy_usdc, copy_shares, 0.0)


        t_roi = safe_divide(trader_total_profit * 100, trader_gross_bought_usd, 0.0)
        c_roi = safe_divide(copy_total_profit * 100, copy_gross_bought_usd, 0.0)
        
        first_row = asset_df.iloc[0]

        position = {
            'timestamp': first_row['timestamp'],
            'trade': first_row.get('title', 'Unknown'),
            'bet': first_row.get('outcome', 'Unknown'),
            'won': won,
            
            # --- COPY DATA ---
            'copy_total_bought': copy_gross_bought_usd,
            'copy_total_sold': copy_gross_sold_usd,     
            'copy_held_live': copy_usdc, 
            'copy_avg_buy': c_avg_buy,
            'copy_avg_sell': c_avg_sell,
            'copy_avg_held': c_avg_held,
            'copy_buy_txs': copy_buy_txs,
            'copy_sell_txs': copy_sell_txs,
            'copy_pnl_realized': copy_realized_profit,
            'copy_pnl_live': copy_live_profit,
            'copy_pnl_total': copy_total_profit,
            'copy_roi': c_roi,
            
            # --- TRADER DATA ---
            'trader_total_bought': trader_gross_bought_usd, 
            'trader_total_sold': trader_gross_sold_usd,     
            'trader_held_live': trader_usdc,  
            'trader_avg_buy': t_avg_buy,
            'trader_avg_sell': t_avg_sell,
            'trader_avg_held': t_avg_held,
            'trader_buy_txs': trader_buy_txs,
            'trader_sell_txs': trader_sell_txs,
            'trader_pnl_realized': trader_realized_profit,
            'trader_pnl_live': trader_live_profit,
            'trader_pnl_total': trader_total_profit,
            'trader_roi': t_roi,
        }

        copy_trade_list.append(position)
    
    result_df = pd.DataFrame(copy_trade_list)
    if not result_df.empty:
        result_df = result_df.sort_values(by='timestamp', ascending=True)

    return result_df


def display_sim_results(data: pd.DataFrame):
    """
    Função Coordenadora:
    1. Valida dados.
    2. Exibe KPIs globais (Métricas).
    3. Chama a renderização do Gráfico.
    4. Chama a renderização das Tabelas.
    """
    if data is None or data.empty:
        st.warning("Sim data is Empty.")
        return

    # Trabalhamos com uma cópia para segurança
    sim_df = data.copy()

    st.subheader("Results")

    # --- 1. KPIs GLOBAIS ---
    # Mantivemos o cálculo aqui pois são métricas rápidas de cabeçalho
    total_trader_pnl = sim_df['trader_pnl_total'].sum()
    total_copy_pnl = sim_df['copy_pnl_total'].sum()
    total_copy_volume = sim_df['copy_total_bought'].sum() if 'copy_total_bought' in sim_df.columns else 0.0
    global_roi = (total_copy_pnl / total_copy_volume * 100) if total_copy_volume > 0 else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Copy PnL", f"${total_copy_pnl:,.2f}", f"${total_copy_pnl - total_trader_pnl:,.2f} vs Trader")
    col2.metric("Global ROI", f"{global_roi:.2f}%", delta_color="normal" if global_roi > 0 else "inverse")
    col3.metric("Total Trades", f"{len(sim_df)}")
    col4.metric("Staked", f"${total_copy_volume:,.2f}")

    st.divider()

    # --- 2. CHAMADA DO GRÁFICO ---
    display_equity_chart(sim_df)

    # --- 3. CHAMADA DAS TABELAS ---
    display_sim_tables(sim_df)


def display_equity_chart(df: pd.DataFrame):
    """
    Responsável apenas por calcular as curvas acumuladas e renderizar o Plotly.
    """
    st.write("### Equity Curve")
    st.caption("Hint: Click on the Graph Caption to Hide or Display the Line")
    
    try:
        # Prepara dados para o gráfico (Cálculo Local)
        chart_df = df.copy() # Cópia leve para não afetar o DF original com colunas temp
        chart_df['acum_trader'] = chart_df['trader_pnl_total'].cumsum()
        chart_df['acum_copy'] = chart_df['copy_pnl_total'].cumsum()
        chart_df = chart_df.reset_index(drop=True)
        chart_df['trade_number'] = chart_df.index + 1

        fig = go.Figure()
        
        # Trader Line
        fig.add_trace(go.Scatter(
            x=chart_df['trade_number'], 
            y=chart_df['acum_trader'], 
            mode='lines', 
            name='Trader', 
            line=dict(color='white', width=1), 
            hovertemplate='$%{y:,.2f}'
        ))
        
        # Copy Strategy Line
        fig.add_trace(go.Scatter(
            x=chart_df['trade_number'], 
            y=chart_df['acum_copy'], 
            mode='lines', 
            name='Copy Strategy', 
            line=dict(color="#60E224", width=3), 
            marker=dict(size=4), 
            hovertemplate='$%{y:,.2f}'
        ))
        
        fig.update_layout(
            title="", 
            xaxis_title="Total Trades", 
            yaxis_title="Profit", 
            template="plotly_dark", 
            hovermode="x unified", 
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')
        
    except Exception as e:
        st.error(f"Error rendering chart: {e}")

def display_sim_tables(df: pd.DataFrame):
    """
    Exibe as tabelas de simulação (Copy vs Trader) usando paginação.
    """
    st.write("### All Trades")
    
    # 1. Preparação dos Dados
    # Separa os dados em dois DFs distintos
    df_copy, df_trader = split_and_format_df(df)
    
    # 2. Configuração Visual (Column Config)
    # Define como cada coluna deve aparecer (R$, %, datas, etc.)
    common_column_config = {
        "timestamp": st.column_config.DatetimeColumn(
            "First Trade",
            format="D MMM YYYY, HH:mm",
            width="medium"
        ),
        "trade": st.column_config.TextColumn("Market", width="large"),
        "bet": st.column_config.TextColumn("Bet", width="small"),
        "won": st.column_config.CheckboxColumn("Win?", width="small"),
        
        "avg_buy": st.column_config.NumberColumn("Avg Buy", format="%.3f"),
        "avg_sell": st.column_config.NumberColumn("Avg Sell", format="%.3f"),
        "avg_held": st.column_config.NumberColumn("Avg Live", format="%.3f"),

        "buy_txs": st.column_config.NumberColumn("# Buys"),
        "total_bought": st.column_config.NumberColumn("Total Bought", format="$%.2f"),
        "sell_txs": st.column_config.NumberColumn("# Sells"),
        "total_sold": st.column_config.NumberColumn("Total Sold", format="$%.2f"),
        "held_live": st.column_config.NumberColumn("Held Live", format="$%.2f"),
        
        "pnl_realized": st.column_config.NumberColumn("PnL Pre-Live", format="$%.2f"),
        "pnl_live": st.column_config.NumberColumn("PnL Live", format="$%.2f"),
        "pnl_total": st.column_config.NumberColumn("PnL Total", format="$%.2f"),
        "roi": st.column_config.NumberColumn("ROI", format="%.2f%%"),
    }
    
    # 3. Ordem das Colunas
    order = [
        'timestamp', 'trade', 'bet', 'won', 'roi', 'pnl_total', 
        'total_bought', 'avg_buy', 'avg_sell', 'pnl_realized', 'pnl_live'
    ]

    # 4. Renderização das Abas com Paginação
    tab1, tab2 = st.tabs(["CopyTrade Details", "Trader Details"])
    
    # --- ABA COPY ---
    with tab1:
        dh.render_paginated_table(
            df=df_copy,
            unique_key="sim_copy_table",  # ID Único essencial para não conflitar com a outra aba
            page_size=10,                 # 10 linhas por página fica bom em dashboards
            csv_file_name="copy_strategy_results.csv",
            # Argumentos do st.dataframe:
            column_config=common_column_config,
            column_order=order,
            hide_index=True
        )
        
    # --- ABA TRADER ---
    with tab2:
        dh.render_paginated_table(
            df=df_trader,
            unique_key="sim_trader_table", # ID Único diferente da aba 1
            page_size=10,
            csv_file_name="trader_original_results.csv",
            # Argumentos do st.dataframe:
            column_config=common_column_config,
            column_order=order,
            hide_index=True
        )


def split_and_format_df(
    combined_df: pd.DataFrame
    ):
    """
    Separa o DF combinado em dois (Copy e Trader).
    """
    # Colunas de Metadados (comuns aos dois)
    # Adicionei 'timestamp' aqui
    meta_cols = ['timestamp', 'trade', 'bet', 'won'] 
    
    # --- 1. COPY ---
    c_cols = [c for c in combined_df.columns if c.startswith('copy_')]
    copy_df = combined_df[meta_cols + c_cols].copy()
    copy_df.columns = [c.replace('copy_', '') if c.startswith('copy_') else c for c in copy_df.columns]
    
    # --- 2. TRADER ---
    t_cols = [c for c in combined_df.columns if c.startswith('trader_')]
    trader_df = combined_df[meta_cols + t_cols].copy()
    trader_df.columns = [c.replace('trader_', '') if c.startswith('trader_') else c for c in trader_df.columns]
    
    return copy_df, trader_df