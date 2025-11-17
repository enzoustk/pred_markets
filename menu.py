import sys
import pandas as pd
from api.fetch_clv import *
from helpers import get_exploded_df
from data.analysis import DataAnalyst
from api.fetch import fetch_total_trades
from helpers import sep


def choose_wallet() -> str:
    """
    Página em que o user escolhe a carteira
    Só sai daqui quando escolhe uma carteira válida
    """
    while True:
        # Coletar o endereço
       
        print('Digite o endereço do user:')
        print('(Ou aperte 0 para sair)')
                    
        user_address = input('> ')
        
        try:
            if int(user_address) == 0:
                print('Saindo...')
                sys.exit()
        except ValueError:
            pass
               
        # Sair do loop se for uma carteira válida
        wallet_trades = fetch_total_trades(user_address)
                
        
        if wallet_trades == -1: 
            print('\n','Carteira inválida! Tente novamente','\n', sep = 20 * ('-'))
            continue
        
        if wallet_trades != -1:
            print(
                sep(),
                f'Carteira {user_address} válida.',
                f'Total de Traded Markets: {wallet_trades}',
                sep(),
                sep='\n'
                )
            return user_address
                           

def clv_menu(
    df: pd.DataFrame,
    user_address: str,
    current_clvs: pd.DataFrame = pd.DataFrame(),
    ):
    """
    Organiza uma requisição para a API da Polymarket
    """
    
    
    print('Solitação de Análise CLV Iniciada.')
    
    while True:
        try:
            min_bets = int(input('Defina o mínimo de apostas por tag: '))
            if min_bets <=0:
                print('Escolha um número maior ou igual a 0')
            break
        
        except ValueError:
            print('Escolha um valor válido para o mínimo de tags')
        
    # Imprime os dados para o user escolher
    tag_df = DataAnalyst.tag_analysis(df=df, min_bets=min_bets)
    DataAnalyst.print_tag_report(tag_df=tag_df)
    
    # Hora de deixar o user filtar
    print('Tag escolhida:')
    
    while True:
        chosen_tag = input('> ')
        if chosen_tag in tag_df['tag'].tolist():
            break
        print(f"Tag '{chosen_tag}' não encontrada. Tente novamente.")
        

    # Filtrar o DF pela tag escolhida:
    exploded_df = get_exploded_df(df)
    # Com a tag, vamos puxar os dados:
    
    clv_df = DataAnalyst.calculate_clv(
        user_address=user_address,
        df=exploded_df[exploded_df['tag'] == chosen_tag]
        )
    
    print(f'CLV para a tag {chosen_tag} calculado.')
    
    if current_clvs.empty: 
        current_clvs = clv_df
    else:
        current_clvs = pd.concat([current_clvs, clv_df])
        
    return current_clvs
    
    