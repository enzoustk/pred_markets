import pandas as pd
from data.analysys import *
from api.fetch import user_data
from data.handle import process_sports_trades

def main(user_address):
    """
    Para um user:
    Puxa todos os dados dele,
    Separa as Apostas em Esportes;
    Análise profunda nas apostas.
    """
    user_full_data = user_data(user_address=user_address)    
    user_sports_data = process_sports_trades(user_full_data)
    user_sports_data.to_csv('sports_data.csv',index=False)
    DataAnalyst.calculate_stats(user_sports_data)
    print(DataAnalyst.daily_balance(user_sports_data))
    print(DataAnalyst.monthly_balance(user_sports_data))
    # DataAnalyst.analyze_by_tag(user_sports_data)
    
    
    ### Agora, a partir disso, podemos começar o processamento dos dados do Trader.
    
    
user = '0x2c335066fe58fe9237c3d3dc7b275c2a034a0563'
main(user_address=user)
