"""
Tabelas HTML nativas para o dashboard.
"""
import pandas as pd
import numpy as np
import json
import random
from dashboard.constants import *
from dashboard.utils import safe_divide
from dashboard.utils.formatters import format_currency, format_percentage, get_profit_loss_class
from dashboard.utils.data_preparation import (
    prepare_df_columns,
    calculate_flat_profit_by_period,
    calculate_deciles
)
from dashboard.ui.js_templates import (
    get_format_currency_js,
    get_format_percentage_js,
    get_sortable_table_js,
    get_daily_table_renderer_js
)
from dashboard.ui.table_templates import create_html_table, create_table_row_html

def _criar_tabela_kpi_html(stats: dict, drawdown_data: dict = None, drawdown_table_html: str = None) -> str:
    """Cria tabela HTML de Métricas Principais."""
    kpi_metrics = [
        'Profit Total', 'Flat Profit', 'ROI Total', 
        'Volume Total', 'Stake Médio', 'Stake Mediano'
    ]
    # Usar formatadores reutilizáveis
    kpi_raw_values = [
        stats.get('total_profit', 0), stats.get('flat_profit', 0), stats.get('total_roi', 0),
        stats.get('total_volume', 0), stats.get('mean_stake', 0), stats.get('median_stake', 0)
    ]
    
    kpi_values_formatted = [
        format_currency(kpi_raw_values[0]), 
        format_currency(kpi_raw_values[1]), 
        format_percentage(kpi_raw_values[2]),
        format_currency(kpi_raw_values[3]), 
        format_currency(kpi_raw_values[4]), 
        format_currency(kpi_raw_values[5])
    ]
    
    html = '<table class="dashboard-table"><thead><tr><th>Métrica</th><th class="text-right">Valor</th></tr></thead><tbody>'
    
    for metric, value, raw_val in zip(kpi_metrics, kpi_values_formatted, kpi_raw_values):
        # Determinar classe baseada no tipo de métrica e valor
        if "profit" in metric.lower() or "roi" in metric.lower():
            cell_class = get_profit_loss_class(raw_val)
        else:
            cell_class = 'neutral'
        html += f'<tr><td>{metric}</td><td class="text-right {cell_class}">{value}</td></tr>'
    
    # Adicionar Drawdown Máximo se disponível
    modal_id = None
    open_function = None
    close_function = None
    
    if drawdown_data is not None:
        max_dd_profit = drawdown_data.get('max_drawdown_profit', 0)
        # Gerar ID único para o modal baseado em timestamp ou random
        modal_id = f"drawdown-modal-{random.randint(1000, 9999)}"
        open_function = f"openDrawdownModal_{modal_id.split('-')[-1]}"
        close_function = f"closeDrawdownModal_{modal_id.split('-')[-1]}"
        
        metric_name_html = f'<a href="#" onclick="event.preventDefault(); {open_function}(); return false;" style="color: {COLOR_ACCENT}; text-decoration: underline; cursor: pointer;">Drawdown Máximo</a>'
        html += f'<tr><td>{metric_name_html}</td><td class="text-right loss">${max_dd_profit:,.2f}</td></tr>'
    
    html += '</tbody></table>'
    
    # Adicionar modal com tabela completa de drawdown
    if drawdown_table_html is not None and drawdown_data is not None and modal_id is not None:
        from dashboard.templates.loader import load_html, load_template, render_template
        
        # Carregar CSS do modal
        modal_css_template = load_template('drawdown_modal', 'css')
        modal_css = f'<style>\n{modal_css_template}\n</style>'
        
        # Carregar template HTML do modal
        modal_html = load_html('drawdown_modal',
            modal_id=modal_id,
            open_function=open_function,
            close_function=close_function,
            drawdown_table_html=drawdown_table_html
        )
        
        html += modal_css + modal_html
    
    return html

def _criar_tabela_top_tags_html(df_tags: pd.DataFrame) -> str:
    """Cria tabela HTML com Todas as Tags com ordenação interativa."""
    if df_tags.empty:
        return '<table class="dashboard-table sortable-table" id="tags-table"><thead><tr><th class="sortable" data-sort="tag">Tag <span class="sort-arrow">↕</span></th><th class="sortable text-right" data-sort="profit">Profit <span class="sort-arrow">↕</span></th><th class="sortable text-right" data-sort="roi">ROI <span class="sort-arrow">↕</span></th><th class="sortable text-right" data-sort="volume">Volume <span class="sort-arrow">↕</span></th><th class="sortable text-right" data-sort="bets">Bets <span class="sort-arrow">↕</span></th></tr></thead><tbody></tbody></table>'
    
    # Preparar dados com todas as tags
    tags_data = []
    for _, row in df_tags.iterrows():
        tag_name = row['tag']
        profit = row['profit']
        roi = row['roi']
        volume = row.get('volume', 0)
        bets = row.get('bets', 0)
        safe_tag_name = "".join(c if c.isalnum() else "_" for c in tag_name)
        tags_data.append({
            'tag': tag_name,
            'tag_link': f'tags/{safe_tag_name}.html',
            'profit': profit,
            'roi': roi,
            'volume': volume,
            'bets': bets
        })
    
    # Converter para JSON para JavaScript
    import json
    tags_json = json.dumps(tags_data)
    
    html = f'''
    <script>
        const tagsData = {tags_json};
    </script>
    <div style="max-height: 280px; overflow-y: auto; overflow-x: hidden;">
    <table class="dashboard-table sortable-table" id="tags-table" style="position: relative;">
        <thead style="position: sticky; top: 0; z-index: 10; background-color: {COLOR_BLACK};">
            <tr>
                <th class="sortable" data-sort="tag" data-sort-type="string">Tag <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="profit" data-sort-type="number">Profit <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="roi" data-sort-type="number">ROI <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="volume" data-sort-type="number">Volume <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="bets" data-sort-type="number">Bets <span class="sort-arrow">↕</span></th>
            </tr>
        </thead>
        <tbody id="tags-table-body">
        </tbody>
    </table>
    </div>
    {get_sortable_table_js(
        data_variable='tagsData',
        table_id='tags-table',
        body_id='tags-table-body',
        initial_sort={'column': 'roi', 'direction': 'desc'},
        render_row_callback=f'''
        function renderRow(row, index) {{
            const profitClass = row.profit >= 0 ? 'profit' : 'loss';
            const roiClass = row.roi >= 0 ? 'profit' : 'loss';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><a href="${{row.tag_link}}" style="color: {COLOR_ACCENT};">${{row.tag}}</a></td>
                <td class="text-right ${{profitClass}}">$${{row.profit.toLocaleString('en-US', {{maximumFractionDigits: 0}})}}</td>
                <td class="text-right ${{roiClass}}">${{(row.roi * 100).toFixed(2)}}%</td>
                <td class="text-right neutral">$${{row.volume.toLocaleString('en-US', {{maximumFractionDigits: 0}})}}</td>
                <td class="text-right neutral">${{row.bets}}</td>
            `;
            return tr;
        }}
        '''
    )}
    '''
    return html

def _criar_tabela_diaria_html(df_daily: pd.DataFrame, df_main: pd.DataFrame = None, df_monthly: pd.DataFrame = None, df_yearly: pd.DataFrame = None) -> str:
    """Cria tabela HTML de Resumo Diário/Mensal/Anual com Flat Profit e controles de filtragem."""
    import json
    
    # Calcular flat_profit por dia usando função reutilizável
    # A função calculate_flat_profit_by_period já prepara o df_main internamente
    if df_main is not None:
        df_daily_copy = calculate_flat_profit_by_period(df_daily, df_main, period='D')
    else:
        df_daily_copy = df_daily.copy()
        df_daily_copy['flat_profit'] = 0
    
    # Filtrar apenas dias com profit != 0
    df_daily_filtered = df_daily_copy[df_daily_copy['profit'] != 0].copy()
    
    if df_daily_filtered.empty:
        return '''
        <div class="daily-controls">
            <select id="daily-limit" style="margin-right: 10px; padding: 5px 10px; background: #1C1C1E; color: #FFFFFF; border: 1px solid #38383A; border-radius: 6px;">
                <option value="10">Últimos 10 dias</option>
                <option value="15">Últimos 15 dias</option>
                <option value="30">Últimos 30 dias</option>
                <option value="all">Todos</option>
            </select>
            <input type="date" id="date-from" style="margin-right: 10px; padding: 5px 10px; background: #1C1C1E; color: #FFFFFF; border: 1px solid #38383A; border-radius: 6px;">
            <input type="date" id="date-to" style="margin-right: 10px; padding: 5px 10px; background: #1C1C1E; color: #FFFFFF; border: 1px solid #38383A; border-radius: 6px;">
            <button onclick="filterDaily()" style="padding: 5px 15px; background: #007AFF; color: #FFFFFF; border: none; border-radius: 6px; cursor: pointer;">Filtrar</button>
        </div>
        <table class="dashboard-table" id="daily-table"><thead><tr><th>Data</th><th class="text-right">Saldo</th><th class="text-right">Flat Profit</th><th class="text-right">ROI</th></tr></thead><tbody></tbody></table>
        '''
    
    # Calcular dados mensais
    monthly_data = []
    if df_monthly is not None and not df_monthly.empty:
        df_monthly_copy = df_monthly.copy()
        df_monthly_copy['date'] = df_monthly_copy['date'].astype(str)
        
        if df_main is not None:
            df_monthly_copy = calculate_flat_profit_by_period(df_monthly_copy, df_main, period='M')
        
        for _, row in df_monthly_copy[df_monthly_copy['profit'] != 0].iterrows():
            monthly_data.append({
                'date': str(row['date']),
                'profit': float(row['profit']),
                'flat_profit': float(row.get('flat_profit', 0)),
                'roi': float(row['roi'])
            })
    
    # Calcular dados anuais
    yearly_data = []
    if df_yearly is not None and not df_yearly.empty:
        df_yearly_copy = df_yearly.copy()
        df_yearly_copy['date'] = df_yearly_copy['date'].astype(str)
        
        if df_main is not None:
            df_yearly_copy = calculate_flat_profit_by_period(df_yearly_copy, df_main, period='Y')
        
        for _, row in df_yearly_copy[df_yearly_copy['profit'] != 0].iterrows():
            yearly_data.append({
                'date': str(row['date']),
                'profit': float(row['profit']),
                'flat_profit': float(row.get('flat_profit', 0)),
                'roi': float(row['roi'])
            })
    
    # Preparar dados diários
    daily_data = []
    for _, row in df_daily_filtered.iterrows():
        date_str = str(row['date'])
        profit = float(row['profit'])
        flat_profit = float(row.get('flat_profit', 0))
        roi = float(row['roi'])
        daily_data.append({
            'date': date_str,
            'profit': profit,
            'flat_profit': flat_profit,
            'roi': roi
        })
    
    daily_json = json.dumps(daily_data)
    monthly_json = json.dumps(monthly_data)
    yearly_json = json.dumps(yearly_data)
    
    # Carregar templates
    from dashboard.templates.loader import load_html, load_template, load_css, render_template
    
    # Carregar CSS (sem tag <style>, será adicionada no template)
    daily_css_template = load_template('daily_table', 'css')
    daily_css = f'<style>\n{daily_css_template}\n</style>'
    
    # Carregar JS do renderer de tabela diária
    daily_renderer_js = get_daily_table_renderer_js()
    
    # Carregar template JS
    daily_js_template = load_template('daily_table', 'js')
    daily_table_js = render_template(daily_js_template, daily_table_renderer_js=daily_renderer_js)
    
    # Carregar template HTML
    html = load_html('daily_table',
        daily_json=daily_json,
        monthly_json=monthly_json,
        yearly_json=yearly_json,
        COLOR_PROFIT=COLOR_PROFIT,
        COLOR_LOSS=COLOR_LOSS,
        daily_table_css=daily_css,
        daily_table_js=daily_table_js
    )
    return html

def _criar_tabela_decis_html(df: pd.DataFrame) -> str:
    """Cria tabela HTML de Distribuição de Stake."""
    # Usar função reutilizável para calcular decis
    deciles_df = calculate_deciles(df, column='staked', include_flat_profit=True)
    
    if deciles_df.empty:
        return create_html_table(
            headers=['Decil', 'Range', 'Bets', 'Volume', 'Profit', 'ROI', 'Flat Profit'],
            rows=[],
            column_alignments=['left', 'right', 'right', 'right', 'right', 'right', 'right']
        )
    
    # Preparar dados para a tabela (usar valores brutos para profit/loss)
    rows = []
    for idx, row in deciles_df.iterrows():
        # Extrair valores escalares (iterrows pode retornar Series)
        def get_scalar(value):
            if hasattr(value, 'item'):
                try:
                    return value.item()
                except (ValueError, AttributeError):
                    return value
            elif hasattr(value, 'iloc'):
                return value.iloc[0] if len(value) > 0 else value
            return value
        
        decil_val = str(row['decil'])
        range_min = get_scalar(row['range_min'])
        range_max = get_scalar(row['range_max'])
        bets_val = int(get_scalar(row['bets']))
        volume_val = get_scalar(row['volume'])
        profit_val = get_scalar(row['profit'])
        roi_val = get_scalar(row['roi'])
        flat_profit_val = get_scalar(row['flat_profit'])
        
        rows.append([
            decil_val,
            f"${range_min:,.2f} - ${range_max:,.2f}",
            bets_val,      # Valor bruto para formatação
            volume_val,    # Valor bruto para formatação
            profit_val,    # Valor bruto para verificação profit/loss
            roi_val,      # Valor bruto para verificação profit/loss
            flat_profit_val # Valor bruto para verificação profit/loss
        ])
    
    # Formatters para colunas que precisam formatação
    column_formatters = [
        None,  # Decil - string
        None,  # Range - string
        lambda x: f"{int(x):,}",  # Bets - formatar como inteiro com separador
        format_currency,  # Volume - formatar
        format_currency,  # Profit - formatar
        format_percentage,  # ROI - formatar
        format_currency  # Flat Profit - formatar
    ]
    
    return create_html_table(
        headers=['Decil', 'Range', 'Bets', 'Volume', 'Profit', 'ROI', 'Flat Profit'],
        rows=rows,
        column_formatters=column_formatters,
        profit_loss_columns=[4, 5, 6],  # Profit, ROI, Flat Profit (valores brutos)
        column_alignments=['left', 'right', 'right', 'right', 'right', 'right', 'right'],
        column_classes=['', 'neutral', 'neutral', 'neutral', '', '', '']
    )

def _calcular_drawdown(df_daily: pd.DataFrame, df_main: pd.DataFrame = None, start_date: str = None, end_date: str = None) -> dict:
    """
    Calcula drawdown máximo e mediano em $ e flat profit.
    
    Args:
        df_daily: DataFrame com dados diários (date, profit, volume, roi)
        df_main: DataFrame principal para calcular flat profit (opcional)
        start_date: Data inicial para filtrar (formato string 'YYYY-MM-DD')
        end_date: Data final para filtrar (formato string 'YYYY-MM-DD')
    
    Returns:
        dict com:
        - max_drawdown_profit: drawdown máximo em $
        - max_drawdown_flat_profit: drawdown máximo em flat profit
        - median_drawdown_profit: drawdown mediano em $
        - median_drawdown_flat_profit: drawdown mediano em flat profit
        - max_drawdown_period: período do drawdown máximo (datas)
        - max_drawdown_days: número de dias do drawdown máximo
    """
    df_daily_copy = df_daily.copy()
    
    # Filtrar por período se especificado
    if start_date or end_date:
        df_daily_copy['date_obj'] = pd.to_datetime(df_daily_copy['date'].astype(str))
        if start_date:
            df_daily_copy = df_daily_copy[df_daily_copy['date_obj'] >= pd.to_datetime(start_date)]
        if end_date:
            df_daily_copy = df_daily_copy[df_daily_copy['date_obj'] <= pd.to_datetime(end_date)]
        df_daily_copy = df_daily_copy.drop('date_obj', axis=1)
    
    # Filtrar apenas dias com profit != 0 e ordenar por data
    df_daily_filtered = df_daily_copy[df_daily_copy['profit'] != 0].sort_values('date').copy()
    
    if df_daily_filtered.empty:
        return {
            'max_drawdown_profit': 0,
            'max_drawdown_flat_profit': 0,
            'median_drawdown_profit': 0,
            'median_drawdown_flat_profit': 0,
            'max_drawdown_period': 'N/A',
            'max_drawdown_days': 0,
            'max_drawdown_start_date': 'N/A',
            'max_drawdown_end_date': 'N/A'
        }
    
    # Calcular flat profit por dia usando função reutilizável
    if df_main is not None:
        df_daily_filtered = calculate_flat_profit_by_period(df_daily_filtered, df_main, period='D')
    else:
        df_daily_filtered['flat_profit'] = 0
    
    # Calcular lucro acumulado e flat profit acumulado
    df_daily_filtered['cumulative_profit'] = df_daily_filtered['profit'].cumsum()
    df_daily_filtered['cumulative_flat_profit'] = df_daily_filtered['flat_profit'].cumsum()
    
    # Calcular picos (rolling max até aquele ponto)
    df_daily_filtered['peak_profit'] = df_daily_filtered['cumulative_profit'].expanding().max()
    df_daily_filtered['peak_flat_profit'] = df_daily_filtered['cumulative_flat_profit'].expanding().max()
    
    # Calcular drawdown (pico - valor atual, sempre >= 0)
    df_daily_filtered['drawdown_profit'] = df_daily_filtered['peak_profit'] - df_daily_filtered['cumulative_profit']
    df_daily_filtered['drawdown_flat_profit'] = df_daily_filtered['peak_flat_profit'] - df_daily_filtered['cumulative_flat_profit']
    
    # Encontrar drawdown máximo
    max_dd_idx_profit = df_daily_filtered['drawdown_profit'].idxmax()
    max_dd_idx_flat = df_daily_filtered['drawdown_flat_profit'].idxmax()
    
    max_drawdown_profit = df_daily_filtered.loc[max_dd_idx_profit, 'drawdown_profit'] if not pd.isna(max_dd_idx_profit) else 0
    max_drawdown_flat_profit = df_daily_filtered.loc[max_dd_idx_flat, 'drawdown_flat_profit'] if not pd.isna(max_dd_idx_flat) else 0
    
    # Encontrar período do drawdown máximo em profit
    max_drawdown_period = 'N/A'
    max_drawdown_days = 0
    max_drawdown_start_date = 'N/A'
    max_drawdown_end_date = 'N/A'
    if not pd.isna(max_dd_idx_profit) and max_drawdown_profit > 0:
        # Encontrar o pico anterior (o último valor máximo antes do drawdown)
        peak_value = df_daily_filtered.loc[max_dd_idx_profit, 'peak_profit']
        # Encontrar o último índice onde o cumulative_profit atingiu o pico
        peak_indices = df_daily_filtered[df_daily_filtered['cumulative_profit'] == peak_value].index
        if not peak_indices.empty:
            peak_idx = peak_indices[0]  # Primeira ocorrência do pico
        else:
            peak_idx = max_dd_idx_profit
        
        # Encontrar quando o drawdown começou (quando o lucro acumulado começou a cair do pico)
        # Encontrar quando voltou ao pico (ou último ponto se ainda não voltou)
        drawdown_start_idx = peak_idx
        drawdown_end_idx = max_dd_idx_profit
        
        # Verificar se há um ponto após o máximo drawdown onde voltou ao pico
        if drawdown_end_idx < df_daily_filtered.index[-1]:
            remaining = df_daily_filtered.loc[drawdown_end_idx:, 'cumulative_profit']
            recovery_idx = remaining[remaining >= peak_value]
            if not recovery_idx.empty:
                drawdown_end_idx = recovery_idx.index[0]
        
        start_date_str = df_daily_filtered.loc[drawdown_start_idx, 'date']
        end_date_str = df_daily_filtered.loc[drawdown_end_idx, 'date']
        
        # Calcular dias e formatar datas
        try:
            start_date_obj = pd.to_datetime(str(start_date_str))
            end_date_obj = pd.to_datetime(str(end_date_str))
            max_drawdown_days = (end_date_obj - start_date_obj).days
            max_drawdown_start_date = start_date_obj.strftime('%d/%b/%Y')
            max_drawdown_end_date = end_date_obj.strftime('%d/%b/%Y')
        except:
            max_drawdown_days = 0
            try:
                max_drawdown_start_date = str(start_date_str)
                max_drawdown_end_date = str(end_date_str)
            except:
                max_drawdown_start_date = 'N/A'
                max_drawdown_end_date = 'N/A'
    
    # Calcular drawdown mediano (apenas valores > 0)
    drawdown_profit_values = df_daily_filtered[df_daily_filtered['drawdown_profit'] > 0]['drawdown_profit']
    drawdown_flat_values = df_daily_filtered[df_daily_filtered['drawdown_flat_profit'] > 0]['drawdown_flat_profit']
    
    median_drawdown_profit = drawdown_profit_values.median() if not drawdown_profit_values.empty else 0
    median_drawdown_flat_profit = drawdown_flat_values.median() if not drawdown_flat_values.empty else 0
    
    return {
        'max_drawdown_profit': max_drawdown_profit,
        'max_drawdown_flat_profit': max_drawdown_flat_profit,
        'median_drawdown_profit': median_drawdown_profit,
        'median_drawdown_flat_profit': median_drawdown_flat_profit,
        'max_drawdown_period': max_drawdown_period,
        'max_drawdown_days': max_drawdown_days,
        'max_drawdown_start_date': max_drawdown_start_date,
        'max_drawdown_end_date': max_drawdown_end_date
    }

def _criar_tabela_drawdown_html(df_daily: pd.DataFrame, df_main: pd.DataFrame = None, include_controls: bool = True) -> str:
    """
    Cria tabela HTML de análise de drawdown com filtros de período.
    """
    # Calcular drawdown para diferentes períodos
    from datetime import datetime, timedelta
    
    drawdown_all = _calcular_drawdown(df_daily, df_main)
    
    # Calcular para períodos fixos
    today = datetime.now().date()
    drawdown_15 = _calcular_drawdown(df_daily, df_main, start_date=str(today - timedelta(days=15)))
    drawdown_30 = _calcular_drawdown(df_daily, df_main, start_date=str(today - timedelta(days=30)))
    drawdown_180 = _calcular_drawdown(df_daily, df_main, start_date=str(today - timedelta(days=180)))
    drawdown_365 = _calcular_drawdown(df_daily, df_main, start_date=str(today - timedelta(days=365)))
    
    # Preparar dados para JavaScript
    dates_json = json.dumps(df_daily['date'].astype(str).tolist())
    drawdown_data = {
        'all': drawdown_all,
        '15': drawdown_15,
        '30': drawdown_30,
        '180': drawdown_180,
        '365': drawdown_365
    }
    drawdown_data_json = json.dumps(drawdown_data)
    
    # Carregar templates
    from dashboard.templates.loader import load_html, load_template, render_template
    
    # Preparar controles HTML
    controls_html = ''
    if include_controls:
        controls_html = f'''
        <div class="drawdown-controls">
            <select id="drawdown-period">
                <option value="15">Últimos 15 dias</option>
                <option value="30">Último mês</option>
                <option value="180">Últimos 6 meses</option>
                <option value="365">Último ano</option>
                <option value="all" selected>Total</option>
                <option value="custom">Personalizado</option>
            </select>
            <div id="drawdown-custom-dates">
                <input type="date" id="drawdown-start-date">
                <input type="date" id="drawdown-end-date">
                <button onclick="updateDrawdownTable()">Aplicar</button>
            </div>
        </div>
        '''
    
    # Carregar CSS
    drawdown_css_template = load_template('drawdown_table', 'css')
    drawdown_css = f'<style>\n{drawdown_css_template}\n</style>'
    
    # Carregar JS
    format_currency_js = get_format_currency_js()
    drawdown_js_template = load_template('drawdown_table', 'js')
    drawdown_table_js = render_template(drawdown_js_template, format_currency_js=format_currency_js)
    
    # Carregar template HTML
    html = load_html('drawdown_table',
        drawdown_css=drawdown_css,
        controls_html=controls_html,
        dates_json=dates_json,
        drawdown_data_json=drawdown_data_json,
        drawdown_table_js=drawdown_table_js
    )
    
    return html

