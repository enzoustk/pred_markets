import time
import pandas as pd
import streamlit as st
from api.fetch import fetch_total_trades
from api.fetch_subgraph import fetch_pnl_data
from dashboard.ui.formatting import center_text


def select_user(
    ) -> str:
    # Retora um user válido    
    st.subheader("Select User")

    # campo de input do chat
    user_address = st.chat_input("Type user address")
    center_text('Hint: 0x507e52ef684ca2dd91f90a9d26d149dd3288beae', size=12)
    
    # se o usuário enviou algo
    if user_address:
        wallet_trades = fetch_total_trades(user_address)

        if wallet_trades == -1:
            st.error("Invalid Wallet.")
        else:
            st.success(
                f"Carteira **{user_address}** válida.\n"
                f"Total de Traded Markets: **{wallet_trades}**"
            )
            # guardar no session_state se quiser
            st.session_state["selected_wallet"] = user_address
            return user_address

       
def get_trades(
    user_address: str
    ) -> pd.DataFrame:
    # Wrapper para puxar todas as Posições do User
    with st.spinner("Fetching trades..."):
        return fetch_pnl_data(user_address)


def merge_dfs(
    closed_df: pd.DataFrame,
    active_df: pd.DataFrame
    ):
    # Recebe os dois dataframes e cria um só para sintetizar as estatísticas
    # Deixá-lo cru por enquanto, fica de TODO para resolvê-lo.
    merge_df = pd.concat([active_df, closed_df])
    merge_df['total_profit'] = merge_df['realizedPnl'].fillna(0) + merge_df['cashPnl'].fillna(0)
    return merge_df