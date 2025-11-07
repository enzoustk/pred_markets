"""
Análise de CLV (Customer Lifetime Value).
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from data.analysis import DataAnalyst


def calculate_clv_analysis(df: pd.DataFrame, user_address: str) -> Dict:
    """
    Calcula análise de CLV para as apostas.
    
    Args:
        df: DataFrame com as apostas
        user_address: Endereço do usuário
    
    Returns:
        dict: Dicionário com estatísticas de CLV
    """
    if df.empty or not user_address:
        return {
            'clv_positive_percent': 0.0,
            'clv_zero_percent': 0.0,
            'clv_negative_percent': 0.0,
            'avg_clv_percent': 0.0,
            'median_clv_percent': 0.0,
            'avg_clv_odds': 0.0,
            'median_clv_odds': 0.0
        }
    
    # Chamar calculate_clv do DataAnalyst
    # pull_data=True significa que vamos buscar os dados das trades
    df_with_clv = DataAnalyst.calculate_clv(
        pull_data=True,
        user_address=user_address,
        df=df.copy()
    )
    
    # Verificar se temos colunas de CLV
    if 'price_clv' not in df_with_clv.columns or 'odds_clv' not in df_with_clv.columns:
        return {
            'clv_positive_percent': 0.0,
            'clv_zero_percent': 0.0,
            'clv_negative_percent': 0.0,
            'avg_clv_percent': 0.0,
            'median_clv_percent': 0.0,
            'avg_clv_odds': 0.0,
            'median_clv_odds': 0.0
        }
    
    # Filtrar apenas linhas com CLV calculado (não NaN)
    df_clv_valid = df_with_clv[df_with_clv['price_clv'].notna() & df_with_clv['odds_clv'].notna()].copy()
    
    if df_clv_valid.empty:
        return {
            'clv_positive_percent': 0.0,
            'clv_zero_percent': 0.0,
            'clv_negative_percent': 0.0,
            'avg_clv_percent': 0.0,
            'median_clv_percent': 0.0,
            'avg_clv_odds': 0.0,
            'median_clv_odds': 0.0
        }
    
    # Calcular CLV percentual (price_clv / avg_price * 100)
    # Precisamos do avg_price, que pode estar no resultado do calculate_clv ou precisamos calcular
    # Por enquanto, vamos usar price_clv diretamente e calcular percentual baseado em odds_clv
    
    # Calcular estatísticas de odds_clv
    odds_clv = df_clv_valid['odds_clv'].values
    price_clv = df_clv_valid['price_clv'].values
    
    # CLV positivo, zero e negativo baseado em price_clv
    clv_positive = (price_clv > 0).sum()
    clv_zero = (price_clv == 0).sum()
    clv_negative = (price_clv < 0).sum()
    total_valid = len(df_clv_valid)
    
    # Percentuais
    clv_positive_percent = (clv_positive / total_valid * 100) if total_valid > 0 else 0.0
    clv_zero_percent = (clv_zero / total_valid * 100) if total_valid > 0 else 0.0
    clv_negative_percent = (clv_negative / total_valid * 100) if total_valid > 0 else 0.0
    
    # Calcular médias e medianas
    # Para percentual, vamos calcular baseado na diferença de odds
    # odds_clv é a razão entre as odds, então (odds_clv - 1) * 100 dá o percentual
    odds_clv_percent = (odds_clv - 1) * 100
    
    avg_clv_percent = float(np.mean(odds_clv_percent)) if len(odds_clv_percent) > 0 else 0.0
    median_clv_percent = float(np.median(odds_clv_percent)) if len(odds_clv_percent) > 0 else 0.0
    
    avg_clv_odds = float(np.mean(odds_clv)) if len(odds_clv) > 0 else 0.0
    median_clv_odds = float(np.median(odds_clv)) if len(odds_clv) > 0 else 0.0
    
    return {
        'clv_positive_percent': clv_positive_percent,
        'clv_zero_percent': clv_zero_percent,
        'clv_negative_percent': clv_negative_percent,
        'avg_clv_percent': avg_clv_percent,
        'median_clv_percent': median_clv_percent,
        'avg_clv_odds': avg_clv_odds,
        'median_clv_odds': median_clv_odds
    }


def get_clv_stats(df: pd.DataFrame, user_address: str) -> Dict:
    """
    Retorna estatísticas de CLV formatadas.
    
    Args:
        df: DataFrame com as apostas
        user_address: Endereço do usuário
    
    Returns:
        dict: Estatísticas formatadas
    """
    stats = calculate_clv_analysis(df, user_address)
    
    return {
        'clv_positive_percent': stats['clv_positive_percent'],
        'clv_zero_percent': stats['clv_zero_percent'],
        'clv_negative_percent': stats['clv_negative_percent'],
        'avg_clv_percent': stats['avg_clv_percent'],
        'median_clv_percent': stats['median_clv_percent'],
        'avg_clv_odds': stats['avg_clv_odds'],
        'median_clv_odds': stats['median_clv_odds']
    }

