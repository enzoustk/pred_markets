import pandas as pd

def assertion_active(
    active_df: pd.DataFrame,
    closed_df: pd.DataFrame,
    ) -> pd.DataFrame:
    """
    Confere se as posições listadas como ativa de fato são ativas
    Retorna um DataFrame combinado com coluna 'ativo' sendo True apenas para posições realmente ativas
    """
    # Cria cópias para não modificar os originais
    active_df = active_df.copy()
    closed_df = closed_df.copy()
    
    # Identifica posições realmente ativas (redeemable == False)
    real_active_mask = active_df['redeemable'] == False
    
    # Adiciona coluna 'ativo' para active_df
    active_df['ativo'] = real_active_mask
    
    # Adiciona coluna 'ativo' para closed_df (todas False)
    closed_df['ativo'] = False
    
    # Combina os dois DataFrames
    combined_df = pd.concat([active_df, closed_df], ignore_index=True)
    combined_df.to_csv('combined_df.csv', index=False)
    return combined_df