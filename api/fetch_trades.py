### Junta todos os Módulos e Puxa os dados para uma dada wallet
import logging
from format_data import normalize, export
from fetch.all import fetch_all_data

def run(wallet: str):
    logging.info("=== INÍCIO: Coleta completa para %s ===", wallet)
    trades, actions = fetch_all_data(wallet)
    trades = normalize(trades)
    actions = normalize(actions)
    export(trades, "trades_data.csv")
    export(actions, "actions_data.csv")
    logging.info("✅ Processo finalizado com sucesso.")

run(wallet="0x2c335066fe58fe9237c3d3dc7b275c2a034a0563")

