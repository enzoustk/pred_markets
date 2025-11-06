"""
Funções utilitárias para preparação e transformação de dados.
"""
import pandas as pd
import numpy as np
import importlib.util
import os

# Importar safe_divide do arquivo utils.py na raiz (evitar import circular)
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_utils_file_path = os.path.join(_parent_dir, 'utils.py')

if os.path.exists(_utils_file_path):
    spec = importlib.util.spec_from_file_location("dashboard_utils_root", _utils_file_path)
    _utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_utils_module)
    safe_divide = _utils_module.safe_divide
else:
    raise ImportError(f"Não foi possível importar safe_divide. Verifique se {_utils_file_path} existe.")


def prepare_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara colunas calculadas padrão do DataFrame.
    
    Args:
        df: DataFrame com dados de apostas
        
    Returns:
        DataFrame com colunas calculadas adicionadas
    """
    df = df.copy()  # Evitar SettingWithCopyWarning
    
    # Calcular total_profit se não existir
    # CORREÇÃO: Usar apenas realizedPnl para evitar duplicação
    if 'total_profit' not in df.columns:
        df['total_profit'] = df['realizedPnl'].fillna(0)
    
    # Calcular staked se não existir
    if 'staked' not in df.columns:
        df['staked'] = df['totalBought'] * df['avgPrice']
    
    # Calcular volume_calc se não existir
    if 'volume_calc' not in df.columns:
        df['volume_calc'] = df['totalBought'] * df['avgPrice']
    
    # Calcular roi_individual se não existir
    if 'roi_individual' not in df.columns:
        df['roi_individual'] = safe_divide(df['total_profit'], df['staked'])
    
    return df


def calculate_flat_profit_by_period(
    df_daily: pd.DataFrame,
    df_main: pd.DataFrame,
    period: str = 'D'
) -> pd.DataFrame:
    """
    Calcula flat profit por período (diário, mensal ou anual).
    
    Args:
        df_daily: DataFrame com dados diários (date, profit, etc.)
        df_main: DataFrame principal com dados de apostas
        period: Período para agrupar ('D' para diário, 'M' para mensal, 'Y' para anual)
        
    Returns:
        DataFrame com coluna 'flat_profit' adicionada
    """
    df_daily_copy = df_daily.copy()
    df_main_copy = prepare_df_columns(df_main.copy())
    
    if 'endDate' not in df_main_copy.columns:
        df_daily_copy['flat_profit'] = 0
        return df_daily_copy
    
    # Agrupar por período e calcular flat_profit
    df_main_copy['date_period'] = pd.to_datetime(
        df_main_copy['endDate'], format='ISO8601', utc=True
    ).dt.tz_localize(None).dt.to_period(period)
    
    flat_profit_by_period = df_main_copy.groupby('date_period')['roi_individual'].sum()
    
    # Converter para dicionário usando string do período como chave
    flat_profit_dict = {str(k): v for k, v in flat_profit_by_period.items()}
    
    # Normalizar datas do df_daily para fazer match correto
    # Converter para string e extrair apenas a parte da data (YYYY-MM-DD)
    def normalize_date(date_val):
        if pd.isna(date_val):
            return None
        # Se já for string, extrair apenas a parte da data
        if isinstance(date_val, str):
            # Extrair apenas a parte da data (antes do espaço ou T)
            date_str = date_val.split()[0].split('T')[0]
            return date_str
        # Se for Timestamp ou datetime, converter para string
        elif hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%d')
        else:
            return str(date_val).split()[0].split('T')[0]
    
    df_daily_copy['date_normalized'] = df_daily_copy['date'].apply(normalize_date)
    df_daily_copy['flat_profit'] = df_daily_copy['date_normalized'].map(flat_profit_dict).fillna(0)
    
    # Remover coluna temporária
    df_daily_copy = df_daily_copy.drop(columns=['date_normalized'])
    
    # Garantir que a coluna date permanece como string
    df_daily_copy['date'] = df_daily_copy['date'].astype(str)
    
    return df_daily_copy


def calculate_deciles(
    df: pd.DataFrame,
    column: str = 'staked',
    include_flat_profit: bool = True
) -> pd.DataFrame:
    """
    Calcula decis para uma coluna específica.
    
    Args:
        df: DataFrame com dados
        column: Nome da coluna para calcular decis (padrão: 'staked')
        include_flat_profit: Se True, calcula flat profit para cada decil
        
    Returns:
        DataFrame com colunas calculadas por decil
    """
    df = prepare_df_columns(df.copy())
    
    stakes = df[column]
    total_count = len(stakes)
    
    if total_count == 0:
        return pd.DataFrame()
    
    percentiles = np.arange(0, 101, 10)
    decile_values = np.percentile(stakes, percentiles)
    
    decile_data = []
    
    for i in range(len(decile_values) - 1):
        # Criar máscara para o decil
        if i == len(decile_values) - 2:
            decil_mask = (stakes >= decile_values[i]) & (stakes <= decile_values[i+1])
        else:
            decil_mask = (stakes >= decile_values[i]) & (stakes < decile_values[i+1])
        
        count = decil_mask.sum()
        if count == 0:
            continue
        
        decil_df = df[decil_mask]
        
        profit_total = float(decil_df['total_profit'].sum())
        volume_total = float(decil_df['volume_calc'].sum())
        roi = float(safe_divide(profit_total, volume_total))
        
        flat_profit = 0.0
        if include_flat_profit:
            flat_profit = float(decil_df['roi_individual'].sum())
        
        decile_data.append({
            'decil': f"{i*10}-{(i+1)*10}%",
            'range_min': float(decile_values[i]),
            'range_max': float(decile_values[i+1]),
            'bets': int(count),
            'volume': volume_total,
            'profit': profit_total,
            'roi': roi,
            'flat_profit': flat_profit
        })
    
    return pd.DataFrame(decile_data)

