"""
Página principal do dashboard.
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from dashboard.constants import *
from dashboard.ui.styles import get_all_styles
from dashboard.ui.js_templates import get_chart_update_animation_css
from dashboard.templates.loader import load_html, load_css, load_js, create_page_html
from dashboard.charts.plotly_helpers import (
    hex_to_rgba,
    prepare_chart_data_by_period,
    create_area_chart
)
from dashboard.tables.html_tables import (
    _criar_tabela_kpi_html,
    _criar_tabela_diaria_html,
    _criar_tabela_decis_html,
    _criar_tabela_drawdown_html,
    _calcular_drawdown,
    _criar_tabela_metricas_principais_html
)
from dashboard.tables.plotly_tables import (
    _criar_tabela_kpi,
    _criar_tabela_top_tags,
    _criar_tabela_diaria,
    _criar_tabela_decis
)

def criar_pagina_principal(stats: dict, df_daily: pd.DataFrame, df_tags: pd.DataFrame, df_main: pd.DataFrame, df_monthly: pd.DataFrame = None, df_yearly: pd.DataFrame = None):
    """
    Cria a página principal com tabelas HTML nativas e retorna HTML completo.
    """
    # Calcular drawdown
    drawdown_data = _calcular_drawdown(df_daily, df_main)
    drawdown_table_html = _criar_tabela_drawdown_html(df_daily, df_main, include_controls=True)
    
    # Preparar dados para gráfico usando função reutilizável
    chart_data_by_period = prepare_chart_data_by_period(df_daily)
    initial_data = chart_data_by_period['all']
    
    # Determinar cor baseada no lucro acumulado final
    daily_filtered = df_daily[df_daily['profit'] != 0].sort_values('date').copy()
    if not daily_filtered.empty:
        daily_filtered['cumulative_profit'] = daily_filtered['profit'].cumsum()
        final_profit = daily_filtered['cumulative_profit'].iloc[-1]
    else:
        final_profit = 0
    area_color = COLOR_PROFIT if final_profit >= 0 else COLOR_LOSS
    
    # Criar gráfico de área usando função reutilizável
    fig_cumulative = create_area_chart(
        x_data=initial_data['x'],
        y_data=initial_data['y'],
        title='Cumulative Profit Over Time',
        area_color=area_color
    )
    
    cumulative_chart_html = fig_cumulative.to_html(full_html=False, include_plotlyjs='cdn', div_id='cumulative-chart')
    
    # Preparar todos os dados originais para cálculo de intervalo personalizado
    all_dates = daily_filtered['date'].astype(str).tolist() if not daily_filtered.empty else []
    all_profits = daily_filtered['profit'].tolist() if not daily_filtered.empty else []
    all_cumulative = daily_filtered['cumulative_profit'].tolist() if not daily_filtered.empty else []
    
    # Converter dados para JSON para JavaScript
    chart_data_json = json.dumps(chart_data_by_period)
    all_data_json = json.dumps({
        'dates': all_dates,
        'profits': all_profits,
        'cumulative': all_cumulative
    })
    
    # CSS global para todas as tabelas do dashboard (usando módulo reutilizável)
    table_css = get_all_styles()
    
    # Carregar templates separados
    from dashboard.templates.loader import load_template
    chart_animation_css = get_chart_update_animation_css().replace('.chart-container', '#cumulative-chart-container')
    cumulative_chart_js = load_template('main_page', 'js')
    
    # Preparar conteúdo HTML da página
    content = load_html('main_page', 
        cumulative_chart_html=cumulative_chart_html,
        chart_animation_css=chart_animation_css,
        chart_data_json=chart_data_json,
        all_data_json=all_data_json,
        cumulative_chart_js=cumulative_chart_js,
        metrics_main_html=_criar_tabela_metricas_principais_html(stats, drawdown_data),
        metrics_table_html=_criar_tabela_kpi_html(stats, drawdown_data, drawdown_table_html),
        stake_distribution_table_html=_criar_tabela_decis_html(df_main),
        daily_summary_table_html=_criar_tabela_diaria_html(df_daily, df_main, df_monthly, df_yearly)
    )
    
    # Criar página HTML completa usando templates
    # Nota: JS é carregado inline no HTML template, não via load_js
    html = create_page_html(
        title='Performance Overview',
        content=content,
        css_files=['main_page'],
        js_files=None,  # JS está inline no template HTML
        additional_head=table_css
    )
    
    return html

def criar_pagina_principal_plotly(stats: dict, df_daily: pd.DataFrame, df_tags: pd.DataFrame, df_main: pd.DataFrame) -> go.Figure:
    """Cria a figura Plotly para o index.html (Estilo Apple) - VERSÃO LEGADA."""
    
    fig = make_subplots(
        rows=2, 
        cols=2,
        specs=[
            [{"type": "table"}, {"type": "table"}],
            [{"type": "table"}, {"type": "table"}]
        ],
        subplot_titles=(
            "Metrics", "Top 5 Tags (by ROI)",
            "Daily Summary (Last 10)", "Stake Distribution"
        ),
        row_heights=[0.45, 0.55],
        column_widths=[0.4, 0.6], 
        vertical_spacing=0.1,
        horizontal_spacing=0.05
    )
    
    fig.add_trace(_criar_tabela_kpi(stats), row=1, col=1)
    fig.add_trace(_criar_tabela_top_tags(df_tags), row=1, col=2)
    fig.add_trace(_criar_tabela_diaria(df_daily), row=2, col=1)
    fig.add_trace(_criar_tabela_decis(df_main), row=2, col=2)

    fig.update_layout(
        title=dict(
            text=f'Performance Overview<br><a href="tags.html" style="color: {COLOR_TEXT_SECONDARY}; font-size: 16px; font-weight: 400; text-decoration: none;">View Full Tag Analysis</a>',
            x=0.5, xanchor='center',
            font=dict(size=34, family=FONT_FAMILY, color=COLOR_WHITE, weight=600)
        ),
        showlegend=False, template='plotly_dark',
        paper_bgcolor=COLOR_BLACK,
        plot_bgcolor=COLOR_BLACK,
        margin=dict(t=140, b=80, l=80, r=80),
        font=dict(family=FONT_FAMILY, size=13, color=COLOR_TEXT_SECONDARY)
    )
    
    # Ajuste dos anchors dos títulos
    for i, annot in enumerate(fig.layout.annotations):
        annot.font = dict(size=18, family=FONT_FAMILY, color=COLOR_TEXT_PRIMARY, weight=500)
        annot.xanchor = 'left' 
        if i == 0: annot.x = 0.0      # Título 1 (Metrics)
        if i == 1: annot.x = 0.43     # Título 2 (Top 5 Tags) - (0.4 + 0.05*0.6) ~ 0.43
        if i == 2: annot.x = 0.0      # Título 3 (Daily)
        if i == 3: annot.x = 0.43     # Título 4 (Stake)
            
    return fig

