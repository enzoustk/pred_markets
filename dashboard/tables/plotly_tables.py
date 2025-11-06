"""
Tabelas Plotly para o dashboard.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dashboard.constants import *
from dashboard.utils import safe_divide
from dashboard.utils.formatters import format_currency, format_percentage
from dashboard.utils.data_preparation import prepare_df_columns, calculate_deciles
from dashboard.charts.table_templates import (
    create_kpi_table_plotly,
    create_profit_loss_table_plotly,
    create_plotly_table
)

def _criar_tabela_kpi(stats: dict) -> go.Table:
    """Cria o bloco de Métricas Principais (estilo tabela minimalista)."""
    return create_kpi_table_plotly(stats)

def _criar_tabela_top_tags(df_tags: pd.DataFrame) -> go.Table:
    """Cria tabela com Top 5 Tags e links (Estilo Apple)."""
    if df_tags.empty:
        return create_plotly_table(
            headers=['Tag', 'Profit', 'ROI'],
            columns=[[], [], []],
            column_alignments=['left', 'right', 'right']
        )

    df_top_tags = df_tags.nlargest(5, 'roi')
    
    # O go.Table não renderiza HTML. Passamos apenas o texto puro da tag.
    tags = df_top_tags['tag'].tolist()
    profits = df_top_tags['profit'].tolist()
    rois = df_top_tags['roi'].tolist()
    
    # Formatar valores
    profits_formatted = [format_currency(p) for p in profits]
    rois_formatted = [format_percentage(r) for r in rois]
    
    # Criar cores: primeira coluna (tags) em COLOR_ACCENT, profit e ROI com cores profit/loss
    column_colors = [
        [COLOR_ACCENT] * len(tags),  # Tags em azul (simula link)
        [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in profits],  # Profit
        [COLOR_PROFIT if r >= 0 else COLOR_LOSS for r in rois]  # ROI
    ]

    return create_plotly_table(
        headers=['Tag', 'Profit', 'ROI'],
        columns=[tags, profits_formatted, rois_formatted],
        column_colors=column_colors,
        column_alignments=['left', 'right', 'right']
    )

def _criar_tabela_diaria(df_daily: pd.DataFrame) -> go.Table:
    """Cria a tabela de Resumo Diário (Estilo Apple)."""
    df_daily_filtered = df_daily[df_daily['profit'] != 0].sort_values('date', ascending=False).head(10)
    
    if df_daily_filtered.empty:
        return create_plotly_table(
            headers=['Data', 'Saldo', 'ROI'],
            columns=[[], [], []],
            column_alignments=['left', 'right', 'right']
        )
        
    dates = df_daily_filtered['date'].astype(str).tolist()
    profits = df_daily_filtered['profit'].values.tolist()
    rois = df_daily_filtered['roi'].values.tolist()
    
    # Formatar valores
    profits_formatted = [format_currency(p) for p in profits]
    rois_formatted = [format_percentage(r) for r in rois]
    
    # Criar cores: profit e ROI com cores profit/loss
    column_colors = [
        [COLOR_WHITE] * len(dates),  # Datas em branco
        [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in profits],  # Profit
        [COLOR_PROFIT if r >= 0 else COLOR_LOSS for r in rois]  # ROI
    ]

    return create_plotly_table(
        headers=['Data', 'Saldo', 'ROI'],
        columns=[dates, profits_formatted, rois_formatted],
        column_colors=column_colors,
        column_alignments=['left', 'right', 'right']
    )

def _criar_tabela_decis(df: pd.DataFrame) -> go.Table:
    """Cria a tabela de Distribuição de Stake (Estilo Apple)."""
    # Usar função reutilizável para calcular decis
    deciles_df = calculate_deciles(df, column='staked', include_flat_profit=True)
    
    if deciles_df.empty:
        return create_plotly_table(
            headers=['Decil', 'Range', 'Bets', 'Volume', 'Profit', 'ROI', 'Flat Profit'],
            columns=[[], [], [], [], [], [], []],
            column_alignments=['left', 'right', 'right', 'right', 'right', 'right', 'right']
        )

    # Preparar dados para a tabela
    decile_labels = deciles_df['decil'].tolist()
    table_ranges = [f"${row['range_min']:,.2f} - ${row['range_max']:,.2f}" for _, row in deciles_df.iterrows()]
    table_bets = [f"{int(b):,}" for b in deciles_df['bets']]
    table_volumes = [format_currency(v) for v in deciles_df['volume']]
    table_profits = [format_currency(p) for p in deciles_df['profit']]
    table_rois = [format_percentage(r) for r in deciles_df['roi']]
    table_flat_profits = [format_currency(fp) for fp in deciles_df['flat_profit']]
    
    # Criar cores: profit, ROI e flat profit com cores profit/loss
    column_colors = [
        [COLOR_WHITE] * len(decile_labels),  # Decil
        [COLOR_WHITE] * len(decile_labels),  # Range
        [COLOR_WHITE] * len(decile_labels),  # Bets
        [COLOR_WHITE] * len(decile_labels),  # Volume
        [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in deciles_df['profit']],  # Profit
        [COLOR_PROFIT if r >= 0 else COLOR_LOSS for r in deciles_df['roi']],  # ROI
        [COLOR_PROFIT if fp >= 0 else COLOR_LOSS for fp in deciles_df['flat_profit']]  # Flat Profit
    ]

    return create_plotly_table(
        headers=['Decil', 'Range', 'Bets', 'Volume', 'Profit', 'ROI', 'Flat Profit'],
        columns=[decile_labels, table_ranges, table_bets, table_volumes, table_profits, table_rois, table_flat_profits],
        column_colors=column_colors,
        column_alignments=['left', 'right', 'right', 'right', 'right', 'right', 'right']
    )


