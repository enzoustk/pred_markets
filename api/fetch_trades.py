### Junta todos os Módulos e Puxa os dados para uma dada wallet
import logging
from format_data import normalize
from fetch.all import fetch_all_data

def run(wallet: str):
    logging.info("=== INÍCIO: Coleta completa para %s ===", wallet)
    trades, actions = fetch_all_data(wallet)
    trades = normalize(trades)
    actions = normalize(actions)
    logging.info("✅ Processo finalizado com sucesso.")


