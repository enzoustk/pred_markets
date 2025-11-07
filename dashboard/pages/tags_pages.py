"""
Páginas relacionadas a tags.
"""
import json
import numpy as np
import pandas as pd
from typing import Tuple
from datetime import datetime, timedelta
from dashboard.constants import *
from dashboard.ui.styles import (
    get_table_styles, 
    get_table_container_styles, 
    get_sortable_table_styles,
    get_chart_container_styles,
    get_dashboard_grid_styles,
    get_nav_links_styles,
    get_base_styles
)
from dashboard.ui.js_templates import (
    get_chart_update_animation_css,
    get_column_visibility_modal_js,
    get_sortable_table_js
)
from dashboard.ui.styles import get_all_styles
from dashboard.templates.loader import load_html, load_template, create_page_html
from dashboard.charts.plotly_helpers import (
    hex_to_rgba,
    get_profit_loss_colors,
    apply_default_plotly_layout,
    apply_default_axes,
    create_area_chart,
    prepare_chart_data_by_period
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dashboard.utils import safe_divide
from dashboard.tables.html_tables import (
    _criar_tabela_kpi_html,
    _criar_tabela_decis_html,
    _criar_tabela_diaria_html,
    _criar_tabela_drawdown_html,
    _calcular_drawdown
)

from dashboard.tables.plotly_tables import (
    _criar_tabela_kpi,
    _criar_tabela_decis,
    _criar_tabela_diaria
)

def criar_pagina_tags_resumo(tag_df: pd.DataFrame) -> Tuple[str, str]:
    """Cria o HTML completo para a tags.html com layout de dois lados."""
    
    tag_df_sorted = tag_df.sort_values('roi', ascending=True).copy()
    
    tags_list = tag_df_sorted['tag'].tolist()
    profits = tag_df_sorted['profit'].replace(np.nan, None).tolist()
    rois = (tag_df_sorted['roi'].replace(np.nan, None) * 100).tolist()
    volumes = tag_df_sorted['volume'].replace(np.nan, None).tolist()
    bets = tag_df_sorted['bets'].tolist()
    
    # Preparar dados para o gráfico interativo
    chart_data = []
    for i, tag in enumerate(tags_list):
        chart_data.append({
            'tag': tag,
            'profit': profits[i],
            'roi': rois[i],
            'volume': volumes[i],
            'bets': bets[i]
        })


    # --- Criar Tabela HTML com Ordenação Interativa (como na página principal) ---
    
    # Preparar dados para JavaScript
    tags_data = []
    for _, row in tag_df.iterrows():
        tag_name = row['tag']
        safe_filename = "".join(c if c.isalnum() else "_" for c in tag_name) + ".html"
        tags_data.append({
            'tag': tag_name,
            'tag_link': f'tags/{safe_filename}',
            'profit': float(row['profit']) if pd.notna(row['profit']) else None,
            'roi': float(row['roi']) if pd.notna(row['roi']) else None,
            'volume': float(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
            'bets': int(row.get('bets', 0))
        })
    
    tags_json = json.dumps(tags_data)
    chart_json = json.dumps(chart_data)
    
    # Criar gráfico Plotly único customizável
    
    # Usar função reutilizável para gerar cores
    profit_colors_fill, profit_colors_border = get_profit_loss_colors(profits)
    
    # Criar hovertemplate corretamente (Plotly espera %{variable})
    hovertemplate_str = (
        '<b>%{y}</b><br>' +
        '<b>Profit:</b> $%{x:,.2f}<br>' +
        '<b>ROI:</b> %{customdata[0]:.2f}%<br>' +
        '<b>Volume:</b> $%{customdata[1]:,.2f}<br>' +
        '<b>Bets:</b> %{customdata[2]}<extra></extra>'
    )
    
    fig_chart = go.Figure(data=[go.Bar(
        x=profits,
        y=tags_list,
        orientation='h',
        marker=dict(
            color=profit_colors_fill,
            line=dict(
                color=profit_colors_border,
                width=2.5
            ),
            opacity=0.9
        ),
        hovertemplate=hovertemplate_str,
        customdata=[[rois[i], volumes[i], bets[i]] for i in range(len(rois))]
    )])
    
    # Aplicar layout padrão
    apply_default_plotly_layout(
        fig_chart,
        title='Tag Analysis - Profit',
        height=max(600, len(tags_list) * 25),
        margin=dict(t=80, b=80, l=180, r=80)
    )
    
    # Aplicar eixos padrão (com customizações para este gráfico)
    fig_chart.update_yaxes(
        showgrid=False,
        tickfont=dict(size=12, color=COLOR_TEXT_SECONDARY),
        title=''
    )
    fig_chart.update_xaxes(
        showgrid=True,
        gridcolor=COLOR_SEPARATOR,
        zerolinecolor=COLOR_SEPARATOR,
        zeroline=True
    )
    
    chart_html = fig_chart.to_html(full_html=False, include_plotlyjs='cdn', div_id='tags-chart')
    
    # Carregar templates e estilos reutilizáveis
    table_css = get_all_styles()
    sortable_table_js = get_sortable_table_js(
        data_variable='tagsPageData',
        table_id='tags-page-table',
        body_id='tags-page-table-body',
        initial_sort={'column': 'profit', 'direction': 'desc'},
        render_row_callback='''
        function renderRow(row, index) {
            const profitClass = (row.profit !== null && row.profit !== undefined && row.profit >= 0) ? 'profit' : 'loss';
            const roiClass = (row.roi !== null && row.roi !== undefined && row.roi >= 0) ? 'profit' : 'loss';
            const tr = document.createElement('tr');
            const profitValue = (row.profit !== null && row.profit !== undefined) ? row.profit : 0;
            const volumeValue = (row.volume !== null && row.volume !== undefined) ? row.volume : 0;
            const roiValue = (row.roi !== null && row.roi !== undefined) ? row.roi : 0;
            const betsValue = (row.bets !== null && row.bets !== undefined) ? row.bets : 0;
            tr.innerHTML = `
                <td>${row.tag || 'N/A'}</td>
                <td class="text-right ${profitClass}">$${profitValue.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
                <td class="text-right neutral">$${volumeValue.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
                <td class="text-right ${roiClass}">${(roiValue * 100).toFixed(2)}%</td>
                <td class="text-right neutral">${betsValue}</td>
                <td><a href="${row.tag_link || '#'}">View</a></td>
            `;
            return tr;
        }
        '''
    )
    chart_js = load_template('tags_resumo', 'js')
    
    # Preparar conteúdo HTML usando template
    content = load_html('tags_resumo',
        tags_count=len(tag_df),
        sortable_table_js=sortable_table_js,
        chart_html=chart_html,
        tags_json=tags_json,
        chart_json=chart_json,
        FONT_FAMILY_JSON=json.dumps(FONT_FAMILY),
        COLOR_TEXT_SECONDARY=COLOR_TEXT_SECONDARY,
        COLOR_SEPARATOR=COLOR_SEPARATOR,
        chart_js=chart_js
    )
    
    # Criar página HTML completa usando templates
    page_html = create_page_html(
        title='Tag Analysis',
        content=content,
        css_files=['tags_resumo'],
        js_files=None,  # JS está inline no template HTML
        additional_head=table_css
    )
    
    return page_html, ''  # Retorna HTML completo e string vazia (não precisa mais do fig_tags separado)

def criar_pagina_detalhe_tag(df_tag: pd.DataFrame, tag_name: str, df_daily: pd.DataFrame, user_address: str = None):
    """
    Cria a página de detalhe de uma tag com tabelas HTML nativas e gráfico Plotly.
    Retorna HTML completo.
    """
    df_tag = df_tag.copy()  # Evitar SettingWithCopyWarning
    stats = {}
    if not df_tag.empty:
        stats['total_profit'] = df_tag['total_profit'].sum()
        stats['total_volume'] = df_tag['volume'].sum()
        stats['total_roi'] = safe_divide(stats['total_profit'], stats['total_volume'])
        
        # Calcular flat profit individualmente para cada aposta e depois somar
        if 'staked' not in df_tag.columns:
            df_tag['staked'] = df_tag['totalBought'] * df_tag['avgPrice']
        if 'roi_individual' not in df_tag.columns:
            df_tag['roi_individual'] = safe_divide(df_tag['total_profit'], df_tag['staked'])
        stats['flat_profit'] = df_tag['roi_individual'].sum()
        
        stats['mean_stake'] = df_tag['staked'].mean()
        stats['median_stake'] = df_tag['staked'].median()
    
    # Calcular drawdown
    drawdown_data = _calcular_drawdown(df_daily, df_tag)
    drawdown_table_html = _criar_tabela_drawdown_html(df_daily, df_tag, include_controls=True)
    
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
    fig_bar = create_area_chart(
        x_data=initial_data['x'],
        y_data=initial_data['y'],
        title=f'Daily Performance for \'{tag_name}\'',
        area_color=area_color
    )
    
    # Ajustar altura do gráfico para se ajustar ao container
    fig_bar.update_layout(
        height=None,  # Remove altura fixa para se ajustar ao container
        autosize=True  # Permite que o gráfico se ajuste automaticamente
    )
    
    bar_chart_html = fig_bar.to_html(full_html=False, include_plotlyjs='cdn', div_id='daily-chart')
    
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
    
    # Criar nome do arquivo seguro para link
    safe_filename = "".join(c if c.isalnum() else "_" for c in tag_name)
    apostas_filename = f"{safe_filename}_apostas.html"
    
    # Preparar dados do dataframe para CLV (converter para JSON)
    # Passar todas as colunas do dataframe para o cálculo de CLV
    df_tag_for_clv = df_tag.copy()
    # Converter para JSON, mantendo todas as colunas necessárias para o cálculo
    df_tag_for_clv_json = df_tag_for_clv.to_json(orient='records', date_format='iso')
    
    # CSS e estilos reutilizáveis
    table_css = get_all_styles()
    chart_animation_css = get_chart_update_animation_css().replace('.chart-container', '#daily-chart-container')
    chart_js = load_template('tag_detalhe', 'js')
    clv_analysis_js = load_template('clv_analysis', 'js')
    
    # Importar função para métricas principais
    from dashboard.tables.html_tables import (
        _criar_tabela_metricas_principais_html
    )
    
    # Preparar conteúdo HTML usando template
    content = load_html('tag_detalhe',
        tag_name=tag_name,
        apostas_filename=apostas_filename,
        metrics_main_html=_criar_tabela_metricas_principais_html(stats, drawdown_data),
        metrics_table_html=_criar_tabela_kpi_html(stats, drawdown_data, drawdown_table_html),
        chart_html=bar_chart_html,
        chart_data_json=chart_data_json,
        all_data_json=all_data_json,
        chart_animation_css=chart_animation_css,
        chart_js=chart_js,
        clv_analysis_js=clv_analysis_js,
        daily_summary_table_html=_criar_tabela_diaria_html(df_daily, df_main=df_tag),
        stake_distribution_table_html=_criar_tabela_decis_html(df_tag),
        user_address=user_address or '',
        df_tag_json=df_tag_for_clv_json
    )
    
    # Criar página HTML completa usando templates
    html = create_page_html(
        title=f'Detailed Analysis: {tag_name}',
        content=content,
        css_files=['tag_detalhe'],
        js_files=None,  # JS está inline no template HTML
        additional_head=table_css
    )
    
    return html

def criar_pagina_detalhe_tag_plotly(df_tag: pd.DataFrame, tag_name: str, df_daily: pd.DataFrame) -> go.Figure:
    """Cria a figura Plotly para a página de detalhe de uma tag (Estilo Apple) - VERSÃO LEGADA."""
    df_tag = df_tag.copy()  # Evitar SettingWithCopyWarning
    
    stats = {}
    if not df_tag.empty:
        stats['total_profit'] = df_tag['total_profit'].sum()
        stats['total_volume'] = df_tag['volume'].sum()
        stats['total_roi'] = safe_divide(stats['total_profit'], stats['total_volume'])
        
        # Calcular flat profit individualmente para cada aposta e depois somar
        if 'staked' not in df_tag.columns:
            df_tag['staked'] = df_tag['totalBought'] * df_tag['avgPrice']
        if 'roi_individual' not in df_tag.columns:
            df_tag['roi_individual'] = safe_divide(df_tag['total_profit'], df_tag['staked'])
        stats['flat_profit'] = df_tag['roi_individual'].sum()
        
        stats['mean_stake'] = df_tag['staked'].mean()
        stats['median_stake'] = df_tag['staked'].median()

    
    fig = make_subplots(
        rows=2, 
        cols=2,
        specs=[
            [{"type": "table"}, {"type": "xy"}],
            [{"type": "table"}, {"type": "table"}]
        ],
        subplot_titles=(
            "Tag Metrics", f"Daily Performance for '{tag_name}'",
            "Daily Summary (Last 10)", "Stake Distribution"
        ),
        row_heights=[0.5, 0.5],
        column_widths=[0.4, 0.6],
        vertical_spacing=0.1,
        horizontal_spacing=0.05
    )
    
    fig.add_trace(_criar_tabela_kpi(stats), row=1, col=1)
    
    # Criar gráfico de área com lucro acumulado
    daily_filtered = df_daily[df_daily['profit'] != 0].sort_values('date').copy()
    
    # Calcular lucro acumulado
    daily_filtered['cumulative_profit'] = daily_filtered['profit'].cumsum()
    
    # Determinar cor baseada no lucro acumulado final
    final_profit = daily_filtered['cumulative_profit'].iloc[-1] if not daily_filtered.empty else 0
    area_color = COLOR_PROFIT if final_profit >= 0 else COLOR_LOSS
    
    # Converter cor hex para rgba com transparência
    def hex_to_rgba(hex_color, alpha=0.3):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
    
    # Criar hovertemplate
    hover_template = '<b>%{x}</b><br>' + '<b>Lucro Acumulado:</b> $%{y:,.2f}<extra></extra>'
    
    fig.add_trace(go.Scatter(
        x=daily_filtered['date'].astype(str),
        y=daily_filtered['cumulative_profit'],
        mode='lines',
        fill='tozeroy',
        fillcolor=hex_to_rgba(area_color, 0.3),
        line=dict(
            color=area_color,
            width=3
        ),
        name='Lucro Acumulado',
        hovertemplate=hover_template
    ), row=1, col=2)
    
    fig.add_trace(_criar_tabela_diaria(df_daily), row=2, col=1)
    fig.add_trace(_criar_tabela_decis(df_tag), row=2, col=2)
    
    # Criar nome do arquivo seguro para link
    safe_filename = "".join(c if c.isalnum() else "_" for c in tag_name)
    apostas_filename = f"{safe_filename}_apostas.html"
    
    fig.update_layout(
        title=dict(
            text=f'Detailed Analysis: {tag_name}<br><a href="../index.html" style="color: {COLOR_TEXT_SECONDARY}; font-size: 16px; font-weight: 400; text-decoration: none;">Back to Overview</a> | <a href="../tags.html" style="color: {COLOR_TEXT_SECONDARY}; font-size: 16px; font-weight: 400; text-decoration: none;">Back to All Tags</a> | <a href="{apostas_filename}" style="color: {COLOR_ACCENT}; font-size: 16px; font-weight: 500; text-decoration: none;">📋 Ver Todas as Apostas</a>',
            x=0.5, xanchor='center',
            font=dict(size=34, family=FONT_FAMILY, color=COLOR_WHITE, weight=600)
        ),
        showlegend=False, template='plotly_dark',
        paper_bgcolor=COLOR_BLACK, 
        plot_bgcolor=COLOR_CONTENT_BG,
        margin=dict(t=140, b=80, l=80, r=80),
        font=dict(family=FONT_FAMILY, size=13, color=COLOR_TEXT_SECONDARY)
    )
    
    fig.update_xaxes(showgrid=False, zerolinecolor=COLOR_SEPARATOR, row=1, col=2)
    fig.update_yaxes(
        showgrid=True,  # Linhas de grade horizontais
        gridcolor='rgba(255, 255, 255, 0.1)',  # Branco bem transparente
        gridwidth=1,
        layer='below traces',  # Colocar linhas de grade atrás do gráfico
        zeroline=True,
        zerolinecolor=COLOR_SEPARATOR,
        zerolinewidth=2,
        title_text='Cumulative Profit',
        row=1, col=2
    )
    
    # Ajuste dos anchors dos títulos para o novo column_widths
    for i, annot in enumerate(fig.layout.annotations):
        annot.font = dict(size=18, family=FONT_FAMILY, color=COLOR_TEXT_PRIMARY, weight=500)
        annot.xanchor = 'left' # Alinhar títulos à esquerda
        if i == 0: annot.x = 0.0      # Título 1 (Metrics)
        if i == 1: annot.x = 0.43     # Título 2 (Daily Perf)
        if i == 2: annot.x = 0.0      # Título 3 (Daily Sum)
        if i == 3: annot.x = 0.43     # Título 4 (Stake)
            
    return fig

def criar_pagina_apostas_tag(df_tag: pd.DataFrame, tag_name: str) -> str:
    """
    Cria uma página HTML com tabela de todas as apostas de uma tag.
    
    Args:
        df_tag: DataFrame com todas as apostas da tag
        tag_name: Nome da tag
    
    Returns:
        str: HTML completo da página
    """
    # Criar nome do arquivo seguro para o link de volta
    safe_filename = "".join(c if c.isalnum() else "_" for c in tag_name) + ".html"
    
    # Garantir que temos a coluna 'staked'
    df_tag = df_tag.copy()
    if 'staked' not in df_tag.columns:
        if 'totalBought' in df_tag.columns and 'avgPrice' in df_tag.columns:
            df_tag['staked'] = df_tag['totalBought'] * df_tag['avgPrice']
    
    # Calcular estatísticas básicas
    total_bets = len(df_tag)
    # CORREÇÃO: Usar apenas realizedPnl para evitar duplicação
    total_profit = df_tag['total_profit'].sum() if 'total_profit' in df_tag.columns else df_tag.get('realizedPnl', pd.Series([0])).fillna(0).sum()
    total_volume = df_tag['volume'].sum() if 'volume' in df_tag.columns else (df_tag['totalBought'] * df_tag['avgPrice']).sum()
    
    # Ordenar por start_time (mais recente primeiro)
    if 'start_time' in df_tag.columns:
        # Converter start_time para datetime se necessário
        df_tag_copy = df_tag.copy()
        df_tag_copy['start_time'] = pd.to_datetime(df_tag_copy['start_time'], errors='coerce', utc=True)
        df_sorted = df_tag_copy.sort_values('start_time', ascending=False, na_position='last').copy()
        # Converter de volta para string para manter compatibilidade
        df_sorted['start_time'] = df_sorted['start_time'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
    elif 'createdTimestamp' in df_tag.columns:
        df_sorted = df_tag.sort_values('createdTimestamp', ascending=False).copy()
    elif 'timestamp' in df_tag.columns:
        df_sorted = df_tag.sort_values('timestamp', ascending=False).copy()
    elif 'date' in df_tag.columns:
        df_sorted = df_tag.sort_values('date', ascending=False).copy()
    else:
        df_sorted = df_tag.copy()
    
    # Colunas padrão a serem exibidas (nessa ordem)
    default_columns = [
        'start_time', 'title', 'outcome', 'totalBought', 'size', 
        'avgPrice', 'staked', 'currentValue', 'cashPnl', 'realizedPnl', 
        'total_profit', 'roi'
    ]
    
    # Pegar TODAS as colunas do DataFrame
    all_columns = df_sorted.columns.tolist()
    
    # Reordenar colunas: primeiro as padrão (na ordem especificada), depois as outras
    ordered_columns = []
    
    # Adicionar colunas padrão na ordem especificada
    for col in default_columns:
        if col in all_columns:
            ordered_columns.append(col)
    
    # Adicionar outras colunas que não estão na lista padrão
    for col in all_columns:
        if col not in default_columns:
            ordered_columns.append(col)
    
    # Criar lista de (label, col) para todas as colunas
    existing_cols = []
    for col in ordered_columns:
        # Usar o nome da coluna como label (podemos melhorar depois com nomes mais amigáveis)
        label = col
        existing_cols.append((label, col))
    
    # Importar formatadores reutilizáveis
    from dashboard.utils.formatters import (
        format_currency, format_percentage, format_integer, format_date,
        get_profit_loss_class
    )
    
    # Função auxiliar para detectar tipo de coluna
    def _safe_isna(value):
        """
        Verifica se um valor é NaN de forma segura, mesmo quando é um array/Series.
        Retorna True se o valor for NaN ou None, False caso contrário.
        """
        try:
            # Se for array/Series/list, verificar se está vazio ou se todos são NaN
            if isinstance(value, (list, tuple, np.ndarray, pd.Series)):
                if len(value) == 0:
                    return True
                # Para arrays, verificar se todos são NaN
                if isinstance(value, pd.Series):
                    return value.isna().all()
                elif isinstance(value, np.ndarray):
                    return np.isnan(value).all() if value.dtype.kind in 'fc' else False
                else:
                    # Lista/tupla - verificar se todos são None ou NaN
                    return all(_safe_isna(v) for v in value)
            # Para valores escalares, usar pd.isna normalmente
            return pd.isna(value)
        except (ValueError, TypeError, AttributeError):
            # Se houver erro, considerar como não-NaN
            return False

    def _safe_notna(value):
        """Inverso de _safe_isna"""
        return not _safe_isna(value)

    def detect_column_type(col_name, sample_value):
        """Detecta o tipo de coluna baseado no nome e valor."""
        col_lower = str(col_name).lower()
        
        # Percentuais e ROI - verificar ANTES de currency para evitar conflito
        if any(x in col_lower for x in ['percent', 'roi', 'percentage', 'percentpnl', 'percentrealizedpnl']):
            return 'percentage'
        
        # IDs e códigos longos
        if any(x in col_lower for x in ['id', 'condition', 'market', 'token', 'hash', 'address', 'wallet', 'asset', 'eventid']):
            return 'id_string'
        
        # Timestamps e datas
        if any(x in col_lower for x in ['timestamp', 'time', 'date', 'created', 'updated', 'enddate', 'start_time']):
            return 'datetime'
        
        # Valores monetários (mas não percentRealizedPnl que já foi capturado acima)
        if any(x in col_lower for x in ['profit', 'pnl', 'price', 'stake', 'volume', 'value', 'amount', 'avgprice', 'curprice', 'initialvalue', 'currentvalue']) and 'percent' not in col_lower:
            return 'currency'
        
        # Quantidades inteiras
        if any(x in col_lower for x in ['bought', 'sold', 'quantity', 'count', 'totalbought', 'totalsold', 'size', 'outcomeindex']):
            return 'integer'
        
        # Números decimais
        if isinstance(sample_value, (int, float)) and not _safe_isna(sample_value):
            return 'number'
        
        # Strings longas
        if isinstance(sample_value, str) and len(str(sample_value)) > 30:
            return 'long_string'
        
        return 'string'
    
    # Gerar cabeçalhos da tabela
    table_headers = []
    column_ids = []
    for label, col in existing_cols:
        # Detectar tipo para alinhamento
        sample_val = None
        if len(df_sorted) > 0:
            # Usar dropna() para remover valores NaN e pegar o primeiro valor válido
            try:
                col_series = df_sorted[col].dropna()
                if len(col_series) > 0:
                    first_val = col_series.iloc[0]
                    # Se o valor for um array/lista, pegar o primeiro elemento
                    if isinstance(first_val, (list, tuple, np.ndarray)):
                        if len(first_val) > 0:
                            sample_val = first_val[0] if isinstance(first_val, (list, tuple)) else first_val.item() if hasattr(first_val, 'item') else first_val.flat[0] if hasattr(first_val, 'flat') else first_val
                    else:
                        sample_val = first_val
            except (ValueError, TypeError, AttributeError, IndexError):
                # Se houver erro, tentar método alternativo
                try:
                    for idx, val in df_sorted[col].items():
                        if val is not None and not (isinstance(val, float) and np.isnan(val)):
                            if isinstance(val, (list, tuple, np.ndarray)):
                                if len(val) > 0:
                                    sample_val = val[0] if isinstance(val, (list, tuple)) else val.item() if hasattr(val, 'item') else val
                                    break
                            else:
                                sample_val = val
                                break
                except (ValueError, TypeError, AttributeError):
                    pass
        
        col_type = detect_column_type(col, sample_val)
        is_numeric = col_type in ['currency', 'integer', 'number', 'percentage']
        align_class = 'text-right' if is_numeric else ''
        column_id = f"col_{col}"
        column_ids.append(column_id)
        
        # Determinar se coluna deve estar visível por padrão
        is_default = col in default_columns
        hidden_class = '' if is_default else 'hidden-column'
        
        # Adicionar classe sortable e atributos para ordenação
        sort_type = 'number' if is_numeric else 'string'
        table_headers.append(f'<th class="{align_class} sortable {hidden_class}" data-column="{column_id}" data-sort="{col}" data-sort-type="{sort_type}" style="width: auto;">{label} <span class="sort-arrow">↕</span><div class="resize-handle"></div></th>')
    
    table_headers_html = '\n                        '.join(table_headers)
    
    # Gerar linhas da tabela
    table_rows = []
    row_index = 0
    for _, row in df_sorted.iterrows():
        row_cells = []
        col_idx = 0
        for label, col in existing_cols:
            column_id = column_ids[col_idx]
            value = row[col]
            col_type = detect_column_type(col, value)
            
            # Formatar valores baseado no tipo
            if _safe_isna(value):
                formatted_value = '<span style="opacity: 0.5;">-</span>'
                cell_class = ''
            elif col_type == 'datetime':
                try:
                    # Tentar diferentes formatos de data
                    if isinstance(value, str):
                        # Se for string ISO8601
                        if 'T' in value or '+' in value:
                            dt = pd.to_datetime(value, format='ISO8601', utc=True, errors='coerce')
                            if _safe_notna(dt):
                                dt = dt.tz_localize(None) if dt.tz else dt
                                formatted_value = dt.strftime('%d/%m/%Y %H:%M')
                            else:
                                formatted_value = str(value)
                        else:
                            # Tentar parsear como data
                            dt = pd.to_datetime(value, errors='coerce')
                            if _safe_notna(dt):
                                formatted_value = dt.strftime('%d/%m/%Y %H:%M')
                            else:
                                formatted_value = str(value)
                    elif isinstance(value, (int, float)):
                        # Timestamp numérico
                        ts = value / 1000 if value > 1e10 else value
                        dt = datetime.fromtimestamp(ts)
                        formatted_value = dt.strftime('%d/%m/%Y %H:%M')
                    elif isinstance(value, pd.Timestamp):
                        formatted_value = value.strftime('%d/%m/%Y %H:%M')
                    else:
                        formatted_value = str(value)
                except Exception as e:
                    formatted_value = str(value)
                cell_class = ''
            elif col_type == 'percentage':
                # Formatar como percentual
                if isinstance(value, (int, float)) and _safe_notna(value):
                    col_lower = str(col).lower()
                    if 'percent' in col_lower:
                        percent_value = value
                    else:
                        percent_value = value * 100
                    
                    if abs(percent_value) >= 1000:
                        formatted_value = f"{percent_value:,.2f}%"
                    else:
                        formatted_value = f"{percent_value:.2f}%"
                    
                    if 'percent' in str(col).lower():
                        roi_value_for_class = value / 100
                    else:
                        roi_value_for_class = value
                else:
                    formatted_value = format_percentage(value, decimals=2, multiply=True)
                    roi_value_for_class = value
                if 'roi' in str(col).lower():
                    cell_class = get_profit_loss_class(roi_value_for_class)
                else:
                    cell_class = ''
            elif col_type == 'currency':
                formatted_value = format_currency(value, decimals=2)
                if 'profit' in str(col).lower() or 'pnl' in str(col).lower():
                    cell_class = get_profit_loss_class(value)
                else:
                    cell_class = ''
            elif col_type == 'integer':
                formatted_value = format_integer(value)
                cell_class = ''
            elif col_type == 'number':
                if isinstance(value, (int, float)) and _safe_notna(value):
                    if abs(value) < 0.01:
                        formatted_value = f'{value:.6f}'
                    elif abs(value) < 1:
                        formatted_value = f'{value:.4f}'
                    else:
                        formatted_value = f'{value:,.2f}'
                else:
                    formatted_value = str(value)
                cell_class = ''
            elif col_type == 'id_string' or col_type == 'long_string':
                str_value = str(value)
                formatted_value = str_value
                cell_class = ''
            else:
                str_value = str(value)
                formatted_value = str_value
                cell_class = ''
            
            # Determinar alinhamento
            is_numeric = col_type in ['currency', 'integer', 'number', 'percentage']
            align_class = 'text-right' if is_numeric else ''
            
            # Determinar se célula deve estar oculta por padrão
            is_default = col in default_columns
            hidden_class = '' if is_default else 'hidden-column'
            
            row_cells.append(f'<td class="{align_class} {hidden_class}" data-column="{column_id}"><span class="{cell_class}">{formatted_value}</span></td>')
            col_idx += 1
        
        table_rows.append(f'<tr class="hidden-row" data-index="{row_index}">\n                                ' + '\n                                '.join(row_cells) + '\n                            </tr>')
        row_index += 1
    
    table_rows_html = '\n                            '.join(table_rows)
    
    # Gerar checkboxes das colunas
    column_checkboxes = []
    for idx, (label, col) in enumerate(existing_cols):
        column_id = column_ids[idx]
        is_default = col in default_columns
        checked_attr = 'checked' if is_default else ''
        column_checkboxes.append(f'<div class="column-checkbox-item"><input type="checkbox" id="checkbox-{column_id}" data-column="{column_id}" {checked_attr}><label for="checkbox-{column_id}">{label}</label></div>')
    
    column_checkboxes_html = '\n                    '.join(column_checkboxes)
    
    # Preparar dados para template
    profit_class = 'profit' if total_profit >= 0 else 'loss'
    total_bets_formatted = f'{total_bets:,}'
    total_profit_formatted = f'${total_profit:,.2f}'
    total_volume_formatted = f'${total_volume:,.2f}'
    
    # Carregar templates
    from dashboard.templates.loader import render_template
    column_modal_js = get_column_visibility_modal_js()
    table_js_template = load_template('apostas_tag', 'js')
    table_js = render_template(table_js_template, totalRows=len(df_sorted))
    
    # Preparar conteúdo HTML usando template
    content = load_html('apostas_tag',
        tag_name=tag_name,
        safe_filename=safe_filename,
        total_bets=total_bets_formatted,
        total_profit=total_profit_formatted,
        total_volume=total_volume_formatted,
        profit_class=profit_class,
        table_headers=table_headers_html,
        table_rows=table_rows_html,
        column_checkboxes=column_checkboxes_html,
        column_modal_js=column_modal_js,
        table_js=table_js
    )
    
    # Criar página HTML completa usando templates
    html = create_page_html(
        title=f'Todas as Apostas - {tag_name}',
        content=content,
        css_files=['apostas_tag'],
        js_files=None,  # JS está inline no template HTML
        additional_head=None  # CSS já está no template
    )
    
    return html

