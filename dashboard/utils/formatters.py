"""
Funções de formatação reutilizáveis para valores do dashboard.
"""
import pandas as pd
from typing import Union


def format_currency(value: Union[float, int, None], decimals: int = 2) -> str:
    """
    Formata um valor como moeda.
    
    Args:
        value: Valor numérico para formatar
        decimals: Número de casas decimais (padrão: 2)
    
    Returns:
        String formatada como moeda (ex: "$1,234.56")
    """
    if value is None or pd.isna(value):
        return f"$0.{'0' * decimals}"
    
    try:
        return f"${float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return f"$0.{'0' * decimals}"


def format_percentage(value: Union[float, int, None], decimals: int = 2, multiply: bool = True) -> str:
    """
    Formata um valor como porcentagem.
    
    Args:
        value: Valor numérico para formatar
        decimals: Número de casas decimais (padrão: 2)
        multiply: Se True, multiplica por 100 antes de formatar (padrão: True)
    
    Returns:
        String formatada como porcentagem (ex: "12.34%")
    """
    if value is None or pd.isna(value):
        return f"0.{'0' * decimals}%"
    
    try:
        val = float(value)
        if multiply:
            val = val * 100
        return f"{val:.{decimals}f}%"
    except (ValueError, TypeError):
        return f"0.{'0' * decimals}%"


def format_integer(value: Union[float, int, None]) -> str:
    """
    Formata um valor como inteiro com separadores de milhar.
    
    Args:
        value: Valor numérico para formatar
    
    Returns:
        String formatada (ex: "1,234")
    """
    if value is None or pd.isna(value):
        return "0"
    
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "0"


def format_date(value: Union[str, pd.Timestamp, None], format_str: str = "%Y-%m-%d") -> str:
    """
    Formata uma data.
    
    Args:
        value: Valor de data (string, Timestamp, etc.)
        format_str: Formato de saída (padrão: "%Y-%m-%d")
    
    Returns:
        String formatada da data
    """
    if value is None or pd.isna(value):
        return "N/A"
    
    try:
        if isinstance(value, str):
            # Tentar converter string para datetime
            dt = pd.to_datetime(value)
        elif isinstance(value, pd.Timestamp):
            dt = value
        else:
            # Tentar converter timestamp numérico
            dt = pd.to_datetime(value, unit='ms' if value > 1e10 else 's')
        
        return dt.strftime(format_str)
    except (ValueError, TypeError):
        return str(value)


def get_profit_loss_class(value: Union[float, int, None]) -> str:
    """
    Retorna a classe CSS apropriada baseada no valor (profit/loss/neutral).
    
    Args:
        value: Valor numérico
    
    Returns:
        String com classe CSS ('profit', 'loss', ou 'neutral')
    """
    if value is None or pd.isna(value):
        return 'neutral'
    
    try:
        val = float(value)
        if val > 0:
            return 'profit'
        elif val < 0:
            return 'loss'
        else:
            return 'neutral'
    except (ValueError, TypeError):
        return 'neutral'

