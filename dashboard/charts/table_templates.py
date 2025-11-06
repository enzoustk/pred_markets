"""
Templates reutilizáveis para criação de tabelas Plotly.
"""
import plotly.graph_objects as go
from typing import List, Optional, Dict, Callable, Any
from dashboard.constants import *
from dashboard.utils.formatters import format_currency, format_percentage, get_profit_loss_class


def create_plotly_table(
    headers: List[str],
    columns: List[List[Any]],
    column_formatters: Optional[List[Callable]] = None,
    column_colors: Optional[List[List[str]]] = None,
    column_alignments: Optional[List[str]] = None,
    profit_loss_columns: Optional[List[int]] = None,
    raw_values: Optional[List[List[float]]] = None,
    header_font_size: int = 13,
    cell_font_size: int = 15,
    header_height: int = 40,
    cell_height: int = 45,
    fill_color: str = COLOR_CONTENT_BG
) -> go.Table:
    """
    Cria uma tabela Plotly genérica com configurações padrão.
    
    Args:
        headers: Lista de nomes das colunas
        columns: Lista de listas, onde cada lista é uma coluna de dados
        column_formatters: Lista opcional de funções para formatar cada coluna
        column_colors: Lista opcional de cores para cada coluna (sobrescreve profit_loss)
        column_alignments: Lista opcional de alinhamentos ('left', 'right', 'center')
        profit_loss_columns: Índices das colunas que devem ter cores profit/loss baseadas em valores
        raw_values: Valores numéricos brutos para calcular cores profit/loss (se não fornecidos, usa columns)
        header_font_size: Tamanho da fonte do cabeçalho
        cell_font_size: Tamanho da fonte das células
        header_height: Altura do cabeçalho
        cell_height: Altura das células
        fill_color: Cor de fundo da tabela
        
    Returns:
        go.Table: Objeto de tabela Plotly configurado
    """
    # Valores padrão
    if column_alignments is None:
        column_alignments = ['left'] * len(headers)
    
    # Formatar colunas se necessário
    formatted_columns = []
    if column_formatters:
        for col, formatter in zip(columns, column_formatters):
            if formatter:
                formatted_columns.append([formatter(v) if v is not None else '' for v in col])
            else:
                formatted_columns.append([str(v) if v is not None else '' for v in col])
    else:
        formatted_columns = [[str(v) if v is not None else '' for v in col] for col in columns]
    
    # Determinar cores das colunas
    font_colors = []
    if column_colors:
        # Se cores específicas foram fornecidas, usar elas
        font_colors = column_colors
    elif profit_loss_columns is not None:
        # Calcular cores baseadas em profit/loss
        values_to_check = raw_values if raw_values else columns
        font_colors = []
        for col_idx, col_data in enumerate(formatted_columns):
            if col_idx in profit_loss_columns:
                # Verificar valores correspondentes
                check_values = values_to_check[col_idx] if col_idx < len(values_to_check) else col_data
                colors = [
                    COLOR_PROFIT if (isinstance(v, (int, float)) and v >= 0) else COLOR_LOSS
                    for v in check_values
                ]
                font_colors.append(colors)
            else:
                # Cor padrão para colunas não-profit/loss
                font_colors.append([COLOR_WHITE] * len(col_data))
    else:
        # Todas as colunas com cor padrão
        font_colors = [[COLOR_WHITE] * len(col) for col in formatted_columns]
    
    # Criar tabela
    return go.Table(
        header=dict(
            values=headers,
            fill_color=fill_color,
            font=dict(size=header_font_size, color=COLOR_WHITE, family=FONT_FAMILY, weight=500),
            align=column_alignments,
            line_color=COLOR_SEPARATOR,
            height=header_height
        ),
        cells=dict(
            values=formatted_columns,
            fill_color=fill_color,
            align=column_alignments,
            font=dict(size=cell_font_size, color=COLOR_WHITE, family=FONT_FAMILY, weight=400),
            font_color=font_colors,
            height=cell_height,
            line_color=COLOR_SEPARATOR
        )
    )


def create_kpi_table_plotly(
    stats: dict,
    metrics: Optional[List[str]] = None,
    metric_keys: Optional[List[str]] = None,
    formatters: Optional[List[Callable]] = None
) -> go.Table:
    """
    Cria tabela de KPIs (Métricas Principais) usando template genérico.
    
    Args:
        stats: Dicionário com estatísticas
        metrics: Nomes das métricas (padrão: ['Profit Total', 'Flat Profit', ...])
        metric_keys: Chaves no dicionário stats (padrão: ['total_profit', 'flat_profit', ...])
        formatters: Funções de formatação para cada métrica
        
    Returns:
        go.Table: Tabela de KPIs
    """
    if metrics is None:
        metrics = [
            'Profit Total', 'Flat Profit', 'ROI Total',
            'Volume Total', 'Stake Médio', 'Stake Mediano'
        ]
    
    if metric_keys is None:
        metric_keys = [
            'total_profit', 'flat_profit', 'total_roi',
            'total_volume', 'mean_stake', 'median_stake'
        ]
    
    if formatters is None:
        formatters = [
            format_currency,  # Profit Total
            format_currency,  # Flat Profit
            format_percentage,  # ROI Total
            format_currency,  # Volume Total
            format_currency,  # Stake Médio
            format_currency   # Stake Mediano
        ]
    
    # Extrair valores
    values = [stats.get(key, 0) for key in metric_keys]
    
    # Formatar valores
    formatted_values = [
        formatter(val) if formatter else str(val)
        for val, formatter in zip(values, formatters)
    ]
    
    # Criar cores para a coluna de valores: profit/loss baseado em métrica e valor
    value_colors = []
    for val, metric in zip(values, metrics):
        if "profit" in metric.lower() or "roi" in metric.lower():
            value_colors.append(COLOR_PROFIT if val >= 0 else COLOR_LOSS)
        else:
            value_colors.append(COLOR_WHITE)
    
    # Criar cores por coluna
    column_colors = [
        [COLOR_WHITE] * len(metrics),  # Coluna de métricas (sempre branco)
        value_colors  # Coluna de valores (cores profit/loss)
    ]
    
    return create_plotly_table(
        headers=['Métrica', 'Valor'],
        columns=[metrics, formatted_values],
        column_colors=column_colors,
        column_alignments=['left', 'right'],
        fill_color=COLOR_CONTENT_BG
    )


def create_profit_loss_table_plotly(
    headers: List[str],
    columns: List[List[Any]],
    profit_indices: List[int],
    roi_indices: Optional[List[int]] = None,
    formatters: Optional[List[Callable]] = None
) -> go.Table:
    """
    Cria tabela com colunas de profit/loss destacadas.
    
    Args:
        headers: Nomes das colunas
        columns: Dados das colunas
        profit_indices: Índices das colunas que representam profit (cores verdes/vermelhas)
        roi_indices: Índices opcionais das colunas ROI (cores verdes/vermelhas)
        formatters: Funções de formatação para cada coluna
        
    Returns:
        go.Table: Tabela configurada
    """
    # Combinar índices de profit e ROI
    profit_loss_cols = list(set(profit_indices + (roi_indices or [])))
    
    # Determinar cores para cada coluna
    column_colors = []
    for col_idx, col_data in enumerate(columns):
        if col_idx in profit_loss_cols:
            colors = [
                COLOR_PROFIT if (isinstance(v, (int, float)) and v >= 0) else COLOR_LOSS
                for v in col_data
            ]
            column_colors.append(colors)
        else:
            column_colors.append([COLOR_WHITE] * len(col_data))
    
    # Formatar colunas se necessário
    formatted_columns = columns
    if formatters:
        formatted_columns = []
        for col, formatter in zip(columns, formatters):
            if formatter:
                formatted_columns.append([formatter(v) if v is not None else '' for v in col])
            else:
                formatted_columns.append([str(v) if v is not None else '' for v in col])
    
    # Determinar alinhamentos (padrão: primeira coluna left, resto right)
    alignments = ['left'] + ['right'] * (len(headers) - 1)
    
    return create_plotly_table(
        headers=headers,
        columns=formatted_columns,
        column_colors=column_colors,
        column_alignments=alignments,
        fill_color=COLOR_CONTENT_BG
    )

