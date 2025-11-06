"""
Funções auxiliares para o dashboard.
"""
import pandas as pd
import numpy as np


def safe_divide(numerator, denominator):
    """
    Função auxiliar para evitar divisão por zero (vetorizada).
    Lida com números únicos ou colunas do pandas.
    """
    # Converte para Series do pandas para lidar com tudo de forma uniforme
    num = pd.Series(numerator).fillna(0.0)
    den = pd.Series(denominator)
    
    # Substitui 0 e NaN no denominador por np.nan para evitar erros
    den_safe = den.replace(0, np.nan).fillna(np.nan)
    
    # Executa a divisão
    result = num / den_safe
    
    # Preenche os resultados NaN/Inf (de 0/0 ou x/0) com 0.0
    result = result.fillna(0.0).replace([np.inf, -np.inf], 0.0)
    
    # Retorna um único número se a entrada foi um número
    if isinstance(numerator, (int, float)) and isinstance(denominator, (int, float)):
        return result.iloc[0]
    
    # Retorna a Série
    return result


