import time
import requests
import pandas as pd
    
def assertion_active(
    active_df: pd.DataFrame,
    closed_df: pd.DataFrame,
    ) -> pd.DataFrame:

    # Cria cópias para não modificar os originais
    active_df = active_df.copy()
    closed_df = closed_df.copy()

    # Identifica posições realmente ativas (redeemable == False)
    real_active_mask = active_df['redeemable'] == False
    
    # Adiciona coluna 'ativo' para active_df
    active_df['active'] = real_active_mask
    
    # Adiciona coluna 'ativo' para closed_df (todas False)
    closed_df['active'] = False
    
    # Combina os dois DataFrames
    return pd.concat([active_df, closed_df], ignore_index=True)
    
def process_sports_trades(full_df: pd.DataFrame):
    """
    Filtra todas as linhas que tenham a tag 'Games' OU 'Sports'
    
    Args:
        full_df: DataFrame completo com coluna 'tags'
    
    Returns:
        DataFrame filtrado contendo apenas mercados com tag 'Games' ou 'Sports'
    """

    
    # Verificar se a coluna 'tags' existe
    if 'tags' not in full_df.columns:
        print("Erro: Coluna 'tags' não encontrada no DataFrame")
        return pd.DataFrame()
    
    # Filtrar linhas que tenham a tag 'Games' OU 'Sports'
    sports_games_mask = full_df['tags'].apply(
        lambda tags: ('Games' in tags or 'Sports' in tags) if isinstance(tags, list) else False
    )
    sports_games_df = full_df[sports_games_mask].copy()
    
    print(f"Filtrados {len(sports_games_df)} mercados com tag 'Games' ou 'Sports' de {len(full_df)} total")
    
    return sports_games_df