import time
import pandas as pd
import streamlit as st
from api.fetch import fetch_total_trades
from api.fetch_pnl_subgraph import fetch_pnl_data


def select_user():
    st.subheader("Select User")

    # campo de input do chat
    user_address = st.chat_input("Type user address")

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
            
def get_trades(user_address: str) -> pd.DataFrame:
    with st.spinner("Fetching trades..."):
        return fetch_pnl_data(
            user_address=user_address,
            include_positions=True,
            closed_only=True
        )
    