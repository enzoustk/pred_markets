import numpy as np
import pandas as pd
import streamlit as st
from dashboard.ui import formatting
from data.analysis import DataAnalyst
from dashboard.backend import data_helpers as dh

def filter_clv_df(
    df:pd.DataFrame,
) -> pd.DataFrame:
    
    
    new_df = df[[
        'endDate', 'title', 'outcome',
        'totalBought', 'avgPrice', 'curPrice',
        'realizedPnl', 'slug', 'tags', 
        'match_start_price', 'price_clv', 'odds_clv'
    ]].copy()

    new_df = new_df.sort_values(by='endDate',ascending=False)
    
    new_df = new_df.rename(columns={
        'endDate': 'End Date',
        'avgPrice': 'Average Price',
        'match_start_price': 'Closing Price',
        'price_clv': 'Probability CLV (%)',
        'odds_clv': 'CLV as Odds',
        'totalBought': 'Total Bought',
        'realizedPnl': 'Realized Profit',
        'curPrice': 'Current Price',
        'title': 'Event',
        'outcome': 'Bet',
        'slug': 'Slug',
        'tags': 'Tags',
        
    })
    
     # 3. Criar versões formatadas
    df_fmt = pd.DataFrame()

    # Data formatada
    df_fmt["End Date"] = pd.to_datetime(new_df["End Date"]) \
        .dt.strftime("%d/%m/%Y")

    df_fmt["Event"] = new_df["Event"]
    df_fmt["Bet"] = new_df["Bet"]
    df_fmt["Slug"] = new_df["Slug"]

    # --- INÍCIO DA CORREÇÃO ---
    # Apenas copie os valores numéricos. O Styler vai formatá-los.
    df_fmt["Total Bought"] = new_df["Total Bought"]
    df_fmt["Probability CLV (%)"] = new_df["Probability CLV (%)"]
    df_fmt["CLV as Odds"] = new_df["CLV as Odds"]
    df_fmt["Average Price"] = new_df["Average Price"]
    df_fmt["Current Price"] = new_df["Current Price"]
    
    # Correto: Manter como número para formatação e coloração
    df_fmt["Realized Profit"] = new_df["Realized Profit"]
    # --- FIM DA CORREÇÃO ---

    # Tags
    df_fmt["Tags"] = new_df["Tags"].apply(formatting.format_tags)
    
    
    # 4. APLICAR FORMATAÇÃO E CORES
    # (O código do styler abaixo NÃO precisa mudar, ele já está correto)
    # 4. APLICAR FORMATAÇÃO E CORES
    styler = (
        df_fmt.style
        .format({
            "Probability CLV (%)": lambda x: f"{x*100:.2f}%",  # Formata o CLV como porcentagem
            "Total Bought": "{:.2f}",
            "CLV as Odds": "{:.2f}",
            "Average Price": "{:.2f}",
            "Current Price": "{:.2f}",
            "Realized Profit": formatting.float_to_dol,
        })
        
        # APLICA A MESMA FUNÇÃO DE COR NAS TRÊS COLUNAS
        .map(
            formatting.color_positive_negative, 
            subset=["Realized Profit", "Probability CLV (%)", "CLV as Odds"]
        )
    )

    return styler


def fetch_clv(
    df: pd.DataFrame,
    user_address: str,
    ):
    
    # Recebendo o dataframe já filtrado dataframes['raw']
    with st.spinner("Fetching CLV data..."):
        clv_df = DataAnalyst.calculate_clv(
            user_address=user_address,
            df=df)
    
       
    display_clv(df=clv_df)

  
def render_clv_section(
    df: pd.DataFrame,
    user_address: str,
):
    """
    Controla toda a lógica de exibição do CLV:
    1. Mostra o botão.
    2. Se clicado, calcula e SALVA os dados no st.session_state.
    3. Em CADA re-execução, LÊ os dados e chama display_clv.
    """
    st.header('Closing Line Value Stats')
    # 1. O Botão (Calcula e Salva)
    if st.button('Fetch CLV for Filtered User Trades'):
        with st.spinner("Fetching CLV data..."):
            # Chama a função de cálculo
            clv_df = DataAnalyst.calculate_clv(
                user_address=user_address,
                df=df
            )
            # Salva os DADOS BRUTOS (DataFrame) no estado
            st.session_state['clv_data'] = clv_df

    # 2. A Exibição (Lê e Desenha)
    # Isso roda em TODA re-execução, garantindo que o CLV
    # não suma ao clicar em outros filtros.
    if 'clv_data' in st.session_state:
        
        clv_data = st.session_state.get('clv_data')
        
        # Garante que os dados existem antes de tentar exibir
        if clv_data is not None and not clv_data.empty:
            # Chama a função de exibição
            display_clv(df=clv_data)
        elif clv_data is None:
            # Limpa o estado se a função de cálculo falhou (retornou None)
            st.error("Erro ao calcular CLV. A função não retornou dados.")
            del st.session_state['clv_data']


def display_clv(df: pd.DataFrame):
    """
    Recebe um DataFrame de CLV já calculado e exibe
    o expander, o dataframe formatado e as estatísticas.
    """
    
    # 1. Formata (chama sua função de Styler)
    styler = filter_clv_df(df) 
    
    # 2. Exibe o Expander
    # (expanded=True faz ele já vir aberto)
    
    

    print_clv_data(df=df)
    

    with st.expander("All CLV Data", expanded=True):
    
        # 3. Exibe o DataFrame
        st.dataframe(
            data=styler, # Passa o Styler
            column_order=[
                col for col in styler.columns
                if col not in ['Slug', 'Total Bought', 'Tags', 'CLV as Odds']
                ],
            hide_index=True
        )
    


def print_clv_data(df: pd.DataFrame) -> None:
    # 1. Cálculos (seu código original)
    total_rows = len(df)
    
    clv_percents = np.sign(df['price_clv']).value_counts(normalize=True)
    pos_clv = clv_percents.get(1.0, 0)
    neg_clv = clv_percents.get(-1.0, 0)
    neutral_clv = clv_percents.get(0.0, 0)

    pnl_percents = np.sign(df['realizedPnl']).value_counts(normalize=True)
    pos_trades = pnl_percents.get(1.0, 0)
    neg_trades = pnl_percents.get(-1.0, 0)
    neutral_trades = pnl_percents.get(0.0, 0)
    
    # 2. Exibição com st.metric
    
    # --- Linha 1: Métricas de PnL (Lucro/Perda) ---
    st.subheader("Trade Performance")
    
    # Cria 4 colunas para os "cartões"
    cols = st.columns(3)
    cols[0].metric(label="Total Trades", value=total_rows)
    cols[1].metric(label="Winning Trades", value=f"{pos_trades * 100:.2f}%")
    cols[2].metric(label="Losing Trades", value=f"{neg_trades * 100:.2f}%")



    # --- Linha 2: Métricas de CLV (Valor de Fechamento) ---
    st.subheader("Closing Line Value (CLV)")
    
    # Cria 3 colunas para os "cartões"
    cols = st.columns(3)
    cols[0].metric(label="Markets", value=df['tags'].explode().nunique())
    cols[1].metric(label="CLV+ (Beat Market)", value=f"{pos_clv * 100:.2f}%")
    cols[2].metric(label="CLV- (Lost to Market)", value=f"{neg_clv * 100:.2f}%")

    
    
    
    
    