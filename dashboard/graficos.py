import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Tuple 

# --- Paleta de Cores e Estilo (Apple HIG Dark Mode) ---

COLOR_BLACK = '#000000'           # Fundo principal
COLOR_CONTENT_BG = '#1C1C1E'      # Fundo dos "cartões"
COLOR_WHITE = '#FFFFFF'           # Texto principal
COLOR_TEXT_PRIMARY = '#F2F2F7'    # Texto principal (ligeiramente off-white)
COLOR_TEXT_SECONDARY = '#8E8E93'  # Texto secundário (cinza Apple)
COLOR_ACCENT = '#0A84FF'          # Azul vibrante (links, destaques)
COLOR_PROFIT = '#30D158'          # Verde vibrante (lucro)
COLOR_LOSS = '#FF453A'            # Vermelho vibrante (prejuízo)
COLOR_NEUTRAL = '#8E8E93'         # Cinza neutro para contagem de apostas

# Fundos de célula translúcidos
COLOR_BG_PROFIT = 'rgba(48, 209, 88, 0.15)'
COLOR_BG_LOSS = 'rgba(255, 69, 58, 0.15)'
COLOR_SEPARATOR = 'rgba(142, 142, 147, 0.3)' # Separador Apple

FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"

# ⬇️ --- CORREÇÃO APLICADA AQUI --- ⬇️
# Esta função local agora é robusta e lida com números únicos ou colunas.
def safe_divide(numerator, denominator):
    """Função auxiliar local para evitar divisão por zero (vetorizada)."""
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
# ⬆️ --- FIM DA CORREÇÃO --- ⬆️

# --- Funções de Componentes Gráficos (Estilo Apple) ---

def _criar_tabela_kpi_html(stats: dict) -> str:
    """Cria tabela HTML de Métricas Principais."""
    kpi_metrics = [
        'Profit Total', 'Flat Profit', 'ROI Total', 
        'Volume Total', 'Stake Médio', 'Stake Mediano'
    ]
    kpi_values_formatted = [
        f"${stats.get('total_profit', 0):,.2f}", 
        f"${stats.get('flat_profit', 0):,.2f}", 
        f"{stats.get('total_roi', 0) * 100:,.2f}%",
        f"${stats.get('total_volume', 0):,.2f}", 
        f"${stats.get('mean_stake', 0):,.2f}", 
        f"${stats.get('median_stake', 0):,.2f}"
    ]
    
    kpi_raw_values = [
        stats.get('total_profit', 0), stats.get('flat_profit', 0), stats.get('total_roi', 0),
        stats.get('total_volume', 0), stats.get('mean_stake', 0), stats.get('median_stake', 0)
    ]
    
    html = '<table class="dashboard-table"><thead><tr><th>Métrica</th><th class="text-right">Valor</th></tr></thead><tbody>'
    
    for metric, value, raw_val in zip(kpi_metrics, kpi_values_formatted, kpi_raw_values):
        if "profit" in metric.lower() or "roi" in metric.lower():
            cell_class = 'profit' if raw_val >= 0 else 'loss'
        else:
            cell_class = 'neutral'
        html += f'<tr><td>{metric}</td><td class="text-right {cell_class}">{value}</td></tr>'
    
    html += '</tbody></table>'
    return html

def _criar_tabela_kpi(stats: dict) -> go.Table:
    """Cria o bloco de Métricas Principais (estilo tabela minimalista)."""
    kpi_metrics = [
        'Profit Total', 'Flat Profit', 'ROI Total', 
        'Volume Total', 'Stake Médio', 'Stake Mediano'
    ]
    kpi_values_formatted = [
        f"${stats.get('total_profit', 0):,.2f}", 
        f"${stats.get('flat_profit', 0):,.2f}", 
        f"{stats.get('total_roi', 0) * 100:,.2f}%",
        f"${stats.get('total_volume', 0):,.2f}", 
        f"${stats.get('mean_stake', 0):,.2f}", 
        f"${stats.get('median_stake', 0):,.2f}"
    ]
    
    kpi_raw_values = [
        stats.get('total_profit', 0), stats.get('flat_profit', 0), stats.get('total_roi', 0),
        stats.get('total_volume', 0), stats.get('mean_stake', 0), stats.get('median_stake', 0)
    ]
    
    # Mudar apenas a cor do TEXTO, não o fundo
    kpi_value_colors = []
    for val, metric in zip(kpi_raw_values, kpi_metrics):
        if "profit" in metric.lower() or "roi" in metric.lower():
            kpi_value_colors.append(COLOR_PROFIT if val >= 0 else COLOR_LOSS)
        else:
            kpi_value_colors.append(COLOR_TEXT_PRIMARY) # Cor de texto normal

    return go.Table(
        header=dict(values=['Métrica', 'Valor'], fill_color=COLOR_CONTENT_BG,
                    font=dict(size=13, color=COLOR_WHITE, family=FONT_FAMILY, weight=500),
                    align=['left', 'right'], line_color=COLOR_SEPARATOR, height=40),
        cells=dict(
            values=[kpi_metrics, kpi_values_formatted],
            fill_color=COLOR_CONTENT_BG,
            align=['left', 'right'],
            font=dict(size=15, color=COLOR_WHITE, family=FONT_FAMILY, weight=400),
            # Aplicar cores de texto dinâmicas à segunda coluna
            font_color=[[COLOR_WHITE]*len(kpi_metrics), kpi_value_colors],
            height=45,
            line_color=COLOR_SEPARATOR
        )
    )

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
    <script>
        const tagsData = {tags_json};
        let currentSort = {{ column: 'roi', direction: 'desc' }};
        let sortedData = [];
        
        function renderTable(data, showAll = false) {{
            const tbody = document.getElementById('tags-table-body');
            tbody.innerHTML = '';
            
            // Mostrar apenas 5 por vez, mas manter todos os dados para scroll
            const dataToShow = showAll ? data : data;
            
            dataToShow.forEach((row, index) => {{
                // Renderizar todas as linhas, mas limitar visualmente com CSS
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
                tbody.appendChild(tr);
            }});
        }}
        
        function sortTable(column, type) {{
            const direction = currentSort.column === column && currentSort.direction === 'asc' ? 'desc' : 'asc';
            currentSort = {{ column, direction }};
            
            sortedData = [...tagsData].sort((a, b) => {{
                let aVal = a[column];
                let bVal = b[column];
                
                if (type === 'number') {{
                    aVal = Number(aVal);
                    bVal = Number(bVal);
                }} else {{
                    aVal = String(aVal).toLowerCase();
                    bVal = String(bVal).toLowerCase();
                }}
                
                if (direction === 'asc') {{
                    return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
                }} else {{
                    return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
                }}
            }});
            
            renderTable(sortedData, true);
            updateSortArrows(column, direction);
        }}
        
        function updateSortArrows(activeColumn, direction) {{
            document.querySelectorAll('.sort-arrow').forEach(arrow => {{
                arrow.textContent = '↕';
            }});
            const activeHeader = document.querySelector(`[data-sort="${{activeColumn}}"] .sort-arrow`);
            if (activeHeader) {{
                activeHeader.textContent = direction === 'asc' ? '↑' : '↓';
            }}
        }}
        
        document.querySelectorAll('.sortable').forEach(header => {{
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {{
                const column = header.getAttribute('data-sort');
                const type = header.getAttribute('data-sort-type') || 'string';
                sortTable(column, type);
            }});
        }});
        
        // Renderizar inicialmente ordenado por ROI desc
        sortedData = tagsData.sort((a, b) => b.roi - a.roi);
        renderTable(sortedData, true);
        updateSortArrows('roi', 'desc');
    </script>
    '''
    return html

def _criar_tabela_top_tags(df_tags: pd.DataFrame) -> go.Table:
    """Cria tabela com Top 5 Tags e links (Estilo Apple)."""
    if df_tags.empty:
        return go.Table(header=dict(values=['Tag', 'Profit', 'ROI']), cells=dict(values=[[], [], []]))

    df_top_tags = df_tags.nlargest(5, 'roi')
    
    # ⬇️ --- CORREÇÃO APLICADA --- ⬇️
    # O go.Table não renderiza HTML. Passamos apenas o texto puro da tag.
    links = df_top_tags['tag'].tolist()
    # ⬆️ --- FIM DA CORREÇÃO --- ⬆️

    rois = [f"{roi*100:,.2f}%" for roi in df_top_tags['roi']]
    profits = [f"${profit:,.0f}" for profit in df_top_tags['profit']]
    
    # Cores de texto para profit/roi
    profit_colors = [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in df_top_tags['profit']]
    roi_colors = [COLOR_PROFIT if r >= 0 else COLOR_LOSS for r in df_top_tags['roi']]

    return go.Table(
        header=dict(
            values=['Tag', 'Profit', 'ROI'],
            fill_color=COLOR_CONTENT_BG,
            align=['left', 'right', 'right'],
            font=dict(size=13, color=COLOR_WHITE, family=FONT_FAMILY, weight=500),
            line_color=COLOR_SEPARATOR, height=40
        ),
        cells=dict(
            values=[links, profits, rois],
            fill_color=COLOR_CONTENT_BG,
            align=['left', 'right', 'right'],
            # O peso 400 (normal) é aplicado a todas as células
            font=dict(size=15, color=COLOR_WHITE, family=FONT_FAMILY, weight=400),
            
            # ⬇️ --- CORREÇÃO APLICADA --- ⬇️
            # Aqui, definimos a cor por coluna.
            # A primeira coluna (índice 0) usará a cor de destaque (azul) para simular o link.
            font_color=[[COLOR_ACCENT]*len(links), profit_colors, roi_colors], 
            # ⬆️ --- FIM DA CORREÇÃO --- ⬆️
            
            height=45,
            line_color=COLOR_SEPARATOR
        )
    )

def _criar_tabela_diaria_html(df_daily: pd.DataFrame, df_main: pd.DataFrame = None, df_monthly: pd.DataFrame = None, df_yearly: pd.DataFrame = None) -> str:
    """Cria tabela HTML de Resumo Diário/Mensal/Anual com Flat Profit e controles de filtragem."""
    import json
    
    # Calcular flat_profit por dia se df_main for fornecido
    df_daily_copy = df_daily.copy()
    if df_main is not None:
        df_main_copy = df_main.copy()
        if 'total_profit' not in df_main_copy.columns:
            df_main_copy['total_profit'] = df_main_copy['realizedPnl'].fillna(0) + df_main_copy['cashPnl'].fillna(0)
        if 'staked' not in df_main_copy.columns:
            df_main_copy['staked'] = df_main_copy['totalBought'] * df_main_copy['avgPrice']
        df_main_copy['roi_individual'] = safe_divide(df_main_copy['total_profit'], df_main_copy['staked'])
        
        # Agrupar por data e calcular flat_profit
        if 'endDate' in df_main_copy.columns:
            df_main_copy['date_period'] = pd.to_datetime(
                df_main_copy['endDate'], format='ISO8601', utc=True
            ).dt.tz_localize(None).dt.to_period('D')
            
            flat_profit_by_date = df_main_copy.groupby('date_period')['roi_individual'].sum()
            
            # Converter date_period para string para fazer match
            df_daily_copy['date_str'] = df_daily_copy['date'].astype(str)
            flat_profit_dict = {str(k): v for k, v in flat_profit_by_date.items()}
            df_daily_copy['flat_profit'] = df_daily_copy['date_str'].map(flat_profit_dict).fillna(0)
        else:
            df_daily_copy['flat_profit'] = 0
    else:
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
            df_main_copy = df_main.copy()
            if 'total_profit' not in df_main_copy.columns:
                df_main_copy['total_profit'] = df_main_copy['realizedPnl'].fillna(0) + df_main_copy['cashPnl'].fillna(0)
            if 'staked' not in df_main_copy.columns:
                df_main_copy['staked'] = df_main_copy['totalBought'] * df_main_copy['avgPrice']
            df_main_copy['roi_individual'] = safe_divide(df_main_copy['total_profit'], df_main_copy['staked'])
            
            if 'endDate' in df_main_copy.columns:
                df_main_copy['month_period'] = pd.to_datetime(
                    df_main_copy['endDate'], format='ISO8601', utc=True
                ).dt.tz_localize(None).dt.to_period('M')
                flat_profit_by_month = df_main_copy.groupby('month_period')['roi_individual'].sum()
                flat_profit_dict = {str(k): v for k, v in flat_profit_by_month.items()}
                df_monthly_copy['flat_profit'] = df_monthly_copy['date'].map(flat_profit_dict).fillna(0)
        
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
            df_main_copy = df_main.copy()
            if 'total_profit' not in df_main_copy.columns:
                df_main_copy['total_profit'] = df_main_copy['realizedPnl'].fillna(0) + df_main_copy['cashPnl'].fillna(0)
            if 'staked' not in df_main_copy.columns:
                df_main_copy['staked'] = df_main_copy['totalBought'] * df_main_copy['avgPrice']
            df_main_copy['roi_individual'] = safe_divide(df_main_copy['total_profit'], df_main_copy['staked'])
            
            if 'endDate' in df_main_copy.columns:
                df_main_copy['year_period'] = pd.to_datetime(
                    df_main_copy['endDate'], format='ISO8601', utc=True
                ).dt.tz_localize(None).dt.to_period('Y')
                flat_profit_by_year = df_main_copy.groupby('year_period')['roi_individual'].sum()
                flat_profit_dict = {str(k): v for k, v in flat_profit_by_year.items()}
                df_yearly_copy['flat_profit'] = df_yearly_copy['date'].map(flat_profit_dict).fillna(0)
        
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
    
    html = f'''
    <div class="daily-controls" style="margin-bottom: 15px; display: flex; align-items: center; flex-wrap: wrap; gap: 10px;">
        <label style="color: #FFFFFF; margin-right: 5px;">Período:</label>
        <button id="period-daily" onclick="switchPeriod('daily')" style="padding: 5px 15px; background: #007AFF; color: #FFFFFF; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">Diário</button>
        <button id="period-monthly" onclick="switchPeriod('monthly')" style="padding: 5px 15px; background: #38383A; color: #FFFFFF; border: none; border-radius: 6px; cursor: pointer;">Mensal</button>
        <button id="period-yearly" onclick="switchPeriod('yearly')" style="padding: 5px 15px; background: #38383A; color: #FFFFFF; border: none; border-radius: 6px; cursor: pointer;">Anual</button>
        <label style="color: #FFFFFF; margin-left: 15px; margin-right: 5px;">Mostrar:</label>
        <select id="daily-limit" style="padding: 5px 10px; background: #1C1C1E; color: #FFFFFF; border: 1px solid #38383A; border-radius: 6px; cursor: pointer;">
            <option value="10">Últimos 10</option>
            <option value="15">Últimos 15</option>
            <option value="30">Últimos 30</option>
            <option value="all">Todos</option>
        </select>
        <label style="color: #FFFFFF; margin-left: 15px; margin-right: 5px;">Data de:</label>
        <input type="date" id="date-from" style="padding: 5px 10px; background: #1C1C1E; color: #FFFFFF; border: 1px solid #38383A; border-radius: 6px;">
        <label style="color: #FFFFFF; margin-left: 5px; margin-right: 5px;">até:</label>
        <input type="date" id="date-to" style="padding: 5px 10px; background: #1C1C1E; color: #FFFFFF; border: 1px solid #38383A; border-radius: 6px;">
        <button onclick="filterDaily()" style="padding: 5px 15px; background: #007AFF; color: #FFFFFF; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">Filtrar</button>
        <button onclick="resetDailyFilter()" style="padding: 5px 15px; background: #38383A; color: #FFFFFF; border: none; border-radius: 6px; cursor: pointer;">Limpar</button>
    </div>
    <div id="daily-summary-totals" style="margin-bottom: 15px; padding: 15px; background-color: {COLOR_CONTENT_BG}; border-radius: 8px; border: 1px solid {COLOR_SEPARATOR}; display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">
        <div style="text-align: center;">
            <div style="color: {COLOR_TEXT_SECONDARY}; font-size: 12px; margin-bottom: 5px;">Saldo Total</div>
            <div id="total-profit" style="color: #FFFFFF; font-size: 20px; font-weight: 600;">$0.00</div>
        </div>
        <div style="text-align: center;">
            <div style="color: {COLOR_TEXT_SECONDARY}; font-size: 12px; margin-bottom: 5px;">Flat Profit Total</div>
            <div id="total-flat-profit" style="color: #FFFFFF; font-size: 20px; font-weight: 600;">$0.00</div>
        </div>
        <div style="text-align: center;">
            <div style="color: {COLOR_TEXT_SECONDARY}; font-size: 12px; margin-bottom: 5px;">ROI Médio</div>
            <div id="total-roi" style="color: #FFFFFF; font-size: 20px; font-weight: 600;">0.00%</div>
        </div>
    </div>
    <div style="max-height: 400px; overflow-y: auto; overflow-x: hidden;">
    <table class="dashboard-table" id="daily-table" style="position: relative;">
        <thead style="position: sticky; top: 0; z-index: 10; background-color: {COLOR_BLACK};">
            <tr>
                <th>Data</th>
                <th class="text-right">Saldo</th>
                <th class="text-right">Flat Profit</th>
                <th class="text-right">ROI</th>
            </tr>
        </thead>
        <tbody id="daily-table-body">
        </tbody>
    </table>
    </div>
    <script>
        const dailyData = {daily_json};
        const monthlyData = {monthly_json};
        const yearlyData = {yearly_json};
        let currentPeriod = 'daily';
        let currentData = [...dailyData];
        let filteredData = [...dailyData];
        
        function switchPeriod(period) {{
            currentPeriod = period;
            
            // Atualizar botões
            document.getElementById('period-daily').style.background = period === 'daily' ? '#007AFF' : '#38383A';
            document.getElementById('period-monthly').style.background = period === 'monthly' ? '#007AFF' : '#38383A';
            document.getElementById('period-yearly').style.background = period === 'yearly' ? '#007AFF' : '#38383A';
            
            // Trocar dados
            if (period === 'daily') {{
                currentData = [...dailyData];
                // Para período diário, mostrar últimos 10 dias a partir de hoje
                filterByLastNDays(10);
            }} else if (period === 'monthly') {{
                currentData = [...monthlyData];
                filterDaily();
            }} else if (period === 'yearly') {{
                currentData = [...yearlyData];
                filterDaily();
            }}
        }}
        
        function updateTotals(data) {{
            // Calcular totais dos dados filtrados
            const totalProfit = data.reduce((sum, row) => sum + row.profit, 0);
            const totalFlatProfit = data.reduce((sum, row) => sum + row.flat_profit, 0);
            
            // Calcular ROI médio (pesado pelo volume, mas como não temos volume nos dados filtrados, vamos calcular média simples)
            const avgROI = data.length > 0 ? data.reduce((sum, row) => sum + row.roi, 0) / data.length : 0;
            
            // Atualizar elementos
            const profitElement = document.getElementById('total-profit');
            const flatProfitElement = document.getElementById('total-flat-profit');
            const roiElement = document.getElementById('total-roi');
            
            profitElement.textContent = '$' + totalProfit.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
            profitElement.style.color = totalProfit >= 0 ? '{COLOR_PROFIT}' : '{COLOR_LOSS}';
            
            flatProfitElement.textContent = '$' + totalFlatProfit.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
            flatProfitElement.style.color = totalFlatProfit >= 0 ? '{COLOR_PROFIT}' : '{COLOR_LOSS}';
            
            roiElement.textContent = (avgROI * 100).toFixed(2) + '%';
            roiElement.style.color = avgROI >= 0 ? '{COLOR_PROFIT}' : '{COLOR_LOSS}';
        }}
        
        function renderDailyTable(data) {{
            const tbody = document.getElementById('daily-table-body');
            tbody.innerHTML = '';
            
            data.forEach(row => {{
                const profitClass = row.profit >= 0 ? 'profit' : 'loss';
                const flatProfitClass = row.flat_profit >= 0 ? 'profit' : 'loss';
                const roiClass = row.roi >= 0 ? 'profit' : 'loss';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${{row.date}}</td>
                    <td class="text-right ${{profitClass}}">$${{row.profit.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</td>
                    <td class="text-right ${{flatProfitClass}}">$${{row.flat_profit.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}</td>
                    <td class="text-right ${{roiClass}}">${{(row.roi * 100).toFixed(2)}}%</td>
                `;
                tbody.appendChild(tr);
            }});
            
            // Atualizar totais sempre que a tabela for renderizada
            updateTotals(data);
        }}
        
        function filterDaily() {{
            const limit = document.getElementById('daily-limit').value;
            const dateFrom = document.getElementById('date-from').value;
            const dateTo = document.getElementById('date-to').value;
            
            filteredData = [...currentData];
            
            // Filtrar por datas
            if (dateFrom) {{
                filteredData = filteredData.filter(row => row.date >= dateFrom);
            }}
            if (dateTo) {{
                filteredData = filteredData.filter(row => row.date <= dateTo);
            }}
            
            // Ordenar por data (mais recente primeiro)
            filteredData.sort((a, b) => b.date.localeCompare(a.date));
            
            // Limitar quantidade
            if (limit !== 'all') {{
                filteredData = filteredData.slice(0, parseInt(limit));
            }}
            
            renderDailyTable(filteredData);
            updateTotals(filteredData);
        }}
        
        function resetDailyFilter() {{
            document.getElementById('daily-limit').value = '10';
            document.getElementById('date-from').value = '';
            document.getElementById('date-to').value = '';
            filterByLastNDays(10);
        }}
        
        function getLastNDays(n) {{
            // Retorna os últimos N dias a partir de hoje
            const today = new Date();
            const result = [];
            
            for (let i = 0; i < n; i++) {{
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                const dateStr = date.toISOString().split('T')[0];
                result.push(dateStr);
            }}
            return result;
        }}
        
        function filterByLastNDays(n) {{
            // Filtrar para mostrar apenas os últimos N dias a partir de hoje
            const lastNDays = getLastNDays(n);
            filteredData = currentData.filter(row => {{
                // Extrair apenas a data (YYYY-MM-DD) do formato do dado
                const rowDate = row.date.split(' ')[0].split('T')[0];
                return lastNDays.includes(rowDate);
            }});
            
            // Ordenar por data (mais recente primeiro)
            filteredData.sort((a, b) => b.date.localeCompare(a.date));
            
            renderDailyTable(filteredData);
            updateTotals(filteredData);
        }}
        
        // Renderizar inicialmente com últimos 10 dias a partir de hoje
        const limitSelect = document.getElementById('daily-limit');
        limitSelect.addEventListener('change', function() {{
            if (this.value === '10') {{
                filterByLastNDays(10);
            }} else if (this.value === '15') {{
                filterByLastNDays(15);
            }} else if (this.value === '30') {{
                filterByLastNDays(30);
            }} else {{
                filterDaily();
            }}
        }});
        
        // Inicializar mostrando últimos 10 dias
        filterByLastNDays(10);
    </script>
    '''
    return html

def _criar_tabela_diaria(df_daily: pd.DataFrame) -> go.Table:
    """Cria a tabela de Resumo Diário (Estilo Apple)."""
    df_daily_filtered = df_daily[df_daily['profit'] != 0].sort_values('date', ascending=False).head(10) # Limitar a 10
    
    if df_daily_filtered.empty:
        return go.Table(header=dict(values=['Data', 'Saldo', 'ROI']), cells=dict(values=[[], [], []]))
        
    dates = df_daily_filtered['date'].astype(str)
    formatted_profits = [f"${p:,.2f}" for p in df_daily_filtered['profit'].values]
    formatted_rois = [f"{r*100:.2f}%" for r in df_daily_filtered['roi'].values]
    
    profit_colors = [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in df_daily_filtered['profit'].values]
    roi_colors = [COLOR_PROFIT if r >= 0 else COLOR_LOSS for r in df_daily_filtered['roi'].values]

    return go.Table(
        header=dict(
            values=['Data', 'Saldo', 'ROI'],
            fill_color=COLOR_CONTENT_BG,
            align=['left', 'right', 'right'],
            font=dict(size=13, color=COLOR_WHITE, family=FONT_FAMILY, weight=500),
            line_color=COLOR_SEPARATOR, height=40
        ),
        cells=dict(
            values=[dates, formatted_profits, formatted_rois],
            fill_color=COLOR_CONTENT_BG,
            align=['left', 'right', 'right'],
            font=dict(size=15, color=COLOR_WHITE, family=FONT_FAMILY, weight=400),
            font_color=[[COLOR_WHITE]*len(dates), profit_colors, roi_colors],
            height=45,
            line_color=COLOR_SEPARATOR
        )
    )

def _criar_tabela_decis_html(df: pd.DataFrame) -> str:
    """Cria tabela HTML de Distribuição de Stake."""
    df = df.copy()  # Evitar SettingWithCopyWarning
    if 'staked' not in df.columns:
        df['staked'] = df['totalBought'] * df['avgPrice']
    
    # Calcular volume: totalBought * avgPrice
    if 'volume_calc' not in df.columns:
        df['volume_calc'] = df['totalBought'] * df['avgPrice']
        
    stakes = df['staked']
    total_count = len(stakes)
    if total_count == 0:
        return '<table class="dashboard-table"><thead><tr><th>Decil</th><th class="text-right">Range</th><th class="text-right">Bets</th><th class="text-right">Volume</th><th class="text-right">Profit</th><th class="text-right">ROI</th><th class="text-right">Flat Profit</th></tr></thead><tbody></tbody></table>'

    percentiles = np.arange(0, 101, 10)
    decile_values = np.percentile(stakes, percentiles)
    
    if 'total_profit' not in df.columns:
        df['total_profit'] = df['realizedPnl'].fillna(0) + df['cashPnl'].fillna(0)

    html = '<table class="dashboard-table"><thead><tr><th>Decil</th><th class="text-right">Range</th><th class="text-right">Bets</th><th class="text-right">Volume</th><th class="text-right">Profit</th><th class="text-right">ROI</th><th class="text-right">Flat Profit</th></tr></thead><tbody>'
    
    # Calcular ROI individual para cada aposta usando staked
    if 'staked' not in df.columns:
        df['staked'] = df['totalBought'] * df['avgPrice']
    if 'roi_individual' not in df.columns:
        df['roi_individual'] = safe_divide(df['total_profit'], df['staked'])
    
    for i in range(len(decile_values) - 1):
        if i == len(decile_values) - 2:
            decil_mask = (stakes >= decile_values[i]) & (stakes <= decile_values[i+1])
        else:
            decil_mask = (stakes >= decile_values[i]) & (stakes < decile_values[i+1])
        
        count = decil_mask.sum()
        profit_total = df[decil_mask]['total_profit'].sum() if count > 0 else 0
        volume_total = df[decil_mask]['volume_calc'].sum() if count > 0 else 0
        
        # Calcular ROI médio do decil e Flat Profit (soma dos ROIs individuais)
        roi = safe_divide(profit_total, volume_total)
        flat_profit = df[decil_mask]['roi_individual'].sum() if count > 0 else 0
        
        label = f"{i*10}-{(i+1)*10}%"
        range_str = f"${decile_values[i]:,.2f} - ${decile_values[i+1]:,.2f}"
        
        profit_class = 'profit' if profit_total >= 0 else 'loss'
        roi_class = 'profit' if roi >= 0 else 'loss'
        flat_profit_class = 'profit' if flat_profit >= 0 else 'loss'
        html += f'<tr><td>{label}</td><td class="text-right neutral">{range_str}</td><td class="text-right neutral">{count:,}</td><td class="text-right neutral">${volume_total:,.2f}</td><td class="text-right {profit_class}">${profit_total:,.2f}</td><td class="text-right {roi_class}">{roi*100:,.2f}%</td><td class="text-right {flat_profit_class}">${flat_profit:,.2f}</td></tr>'
    
    html += '</tbody></table>'
    return html

def _criar_tabela_decis(df: pd.DataFrame) -> go.Table:
    """Cria a tabela de Distribuição de Stake (Estilo Apple)."""
    df = df.copy()  # Evitar SettingWithCopyWarning
    if 'staked' not in df.columns:
        df['staked'] = df['totalBought'] * df['avgPrice']
    
    # Calcular volume: totalBought * avgPrice
    if 'volume_calc' not in df.columns:
        df['volume_calc'] = df['totalBought'] * df['avgPrice']
        
    stakes = df['staked']
    total_count = len(stakes)
    if total_count == 0:
        return go.Table(header=dict(values=['Decil', 'Range', 'Bets', 'Volume', 'Profit', 'ROI', 'Flat Profit']), cells=dict(values=[[], [], [], [], [], [], []]))

    percentiles = np.arange(0, 101, 10)
    decile_values = np.percentile(stakes, percentiles)
    
    if 'total_profit' not in df.columns:
        df['total_profit'] = df['realizedPnl'].fillna(0) + df['cashPnl'].fillna(0)

    # Calcular ROI individual para cada aposta usando staked
    if 'staked' not in df.columns:
        df['staked'] = df['totalBought'] * df['avgPrice']
    if 'roi_individual' not in df.columns:
        df['roi_individual'] = safe_divide(df['total_profit'], df['staked'])

    decile_labels = []
    decile_bets = []
    decile_volumes = []
    decile_profits = []
    decile_rois = []
    decile_flat_profits = []
    
    for i in range(len(decile_values) - 1):
        if i == len(decile_values) - 2:
            decil_mask = (stakes >= decile_values[i]) & (stakes <= decile_values[i+1])
        else:
            decil_mask = (stakes >= decile_values[i]) & (stakes < decile_values[i+1])
        
        count = decil_mask.sum()
        profit_total = df[decil_mask]['total_profit'].sum() if count > 0 else 0
        volume_total = df[decil_mask]['volume_calc'].sum() if count > 0 else 0
        
        # Calcular ROI médio do decil e Flat Profit (soma dos ROIs individuais)
        roi = safe_divide(profit_total, volume_total)
        flat_profit = df[decil_mask]['roi_individual'].sum() if count > 0 else 0
        
        decile_bets.append(count)
        decile_volumes.append(volume_total)
        decile_profits.append(profit_total)
        decile_rois.append(roi)
        decile_flat_profits.append(flat_profit)
        label = f"{i*10}-{(i+1)*10}%"
        decile_labels.append(label)
        
    table_ranges = [f"${decile_values[i]:,.2f} - ${decile_values[i+1]:,.2f}" for i in range(len(decile_values) - 1)]
    table_bets = [f"{b:,}" for b in decile_bets]
    table_volumes = [f"${v:,.2f}" for v in decile_volumes]
    table_profits = [f"${p:,.2f}" for p in decile_profits]
    table_rois = [f"{r*100:,.2f}%" for r in decile_rois]
    table_flat_profits = [f"${fp:,.2f}" for fp in decile_flat_profits]
    
    # Cores para profit, ROI e flat profit
    profit_colors = [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in decile_profits]
    roi_colors = [COLOR_PROFIT if r >= 0 else COLOR_LOSS for r in decile_rois]
    flat_profit_colors = [COLOR_PROFIT if fp >= 0 else COLOR_LOSS for fp in decile_flat_profits]

    return go.Table(
        header=dict(
            values=['Decil', 'Range', 'Bets', 'Volume', 'Profit', 'ROI', 'Flat Profit'],
            fill_color=COLOR_CONTENT_BG,
            align=['left', 'right', 'right', 'right', 'right', 'right', 'right'],
            font=dict(size=13, color=COLOR_WHITE, family=FONT_FAMILY, weight=500),
            line_color=COLOR_SEPARATOR, height=40
        ),
        cells=dict(
            values=[decile_labels, table_ranges, table_bets, table_volumes, table_profits, table_rois, table_flat_profits],
            fill_color=COLOR_CONTENT_BG,
            align=['left', 'right', 'right', 'right', 'right', 'right', 'right'],
            font=dict(size=15, color=COLOR_WHITE, family=FONT_FAMILY, weight=400),
            # Aplicar cores: labels (branco), ranges (branco), bets (branco), volumes (branco), profit (verde/vermelho), ROI (verde/vermelho), flat_profit (verde/vermelho)
            font_color=[[COLOR_WHITE]*len(decile_labels), [COLOR_WHITE]*len(decile_labels), [COLOR_WHITE]*len(decile_labels), [COLOR_WHITE]*len(decile_labels), profit_colors, roi_colors, flat_profit_colors],
            height=45,
            line_color=COLOR_SEPARATOR
        )
    )
# --- Funções de Criação de Páginas ---

def criar_pagina_principal(stats: dict, df_daily: pd.DataFrame, df_tags: pd.DataFrame, df_main: pd.DataFrame, df_monthly: pd.DataFrame = None, df_yearly: pd.DataFrame = None):
    """
    Cria a página principal com tabelas HTML nativas e retorna HTML completo.
    """
    # CSS global para todas as tabelas do dashboard
    table_css = f'''
    <style>
        .dashboard-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            color: #FFFFFF;
            background-color: {COLOR_CONTENT_BG};
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid {COLOR_SEPARATOR};
        }}
        .dashboard-table thead {{
            background-color: {COLOR_BLACK};
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .dashboard-table th {{
            padding: 12px 15px;
            text-align: left;
            color: #FFFFFF;
            font-weight: 600;
            font-size: 12px;
            border-bottom: 2px solid {COLOR_SEPARATOR};
            border-right: 1px solid {COLOR_SEPARATOR};
            white-space: nowrap;
            background-color: {COLOR_BLACK};
        }}
        .dashboard-table th.text-right {{
            text-align: right;
        }}
        .dashboard-table th:last-child {{
            border-right: none;
        }}
        .dashboard-table tbody tr {{
            background-color: {COLOR_CONTENT_BG};
            color: #FFFFFF;
            border-bottom: 1px solid {COLOR_SEPARATOR};
        }}
        .dashboard-table tbody tr:nth-child(even) {{
            background-color: rgba(142, 142, 147, 0.05);
        }}
        .dashboard-table tbody tr:hover {{
            background-color: rgba(10, 132, 255, 0.1);
        }}
        .dashboard-table td {{
            padding: 10px 15px;
            border-right: 1px solid {COLOR_SEPARATOR};
            color: #FFFFFF;
            white-space: nowrap;
        }}
        .dashboard-table td.text-right {{
            text-align: right;
        }}
        .dashboard-table td:last-child {{
            border-right: none;
        }}
        .dashboard-table .profit {{
            color: {COLOR_PROFIT} !important;
            font-weight: 500;
        }}
        .dashboard-table .loss {{
            color: {COLOR_LOSS} !important;
            font-weight: 500;
        }}
        .dashboard-table .neutral {{
            color: #FFFFFF;
        }}
        .dashboard-table a {{
            color: {COLOR_ACCENT};
            text-decoration: none;
            font-weight: 500;
        }}
        .dashboard-table a:hover {{
            text-decoration: underline;
        }}
        .dashboard-table-container {{
            background-color: {COLOR_CONTENT_BG};
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {COLOR_SEPARATOR};
            margin-bottom: 30px;
            overflow-x: auto;
        }}
        .dashboard-table-container::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}
        .dashboard-table-container::-webkit-scrollbar-track {{
            background: {COLOR_BLACK};
            border-radius: 6px;
        }}
        .dashboard-table-container::-webkit-scrollbar-thumb {{
            background: {COLOR_SEPARATOR};
            border-radius: 6px;
        }}
        .dashboard-table-container::-webkit-scrollbar-thumb:hover {{
            background: {COLOR_TEXT_SECONDARY};
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }}
        .dashboard-section {{
            background-color: {COLOR_CONTENT_BG};
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {COLOR_SEPARATOR};
        }}
        .dashboard-section h3 {{
            color: #FFFFFF;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            margin-top: 0;
        }}
        .sortable {{
            cursor: pointer;
            user-select: none;
            position: relative;
        }}
        .sortable:hover {{
            background-color: rgba(142, 142, 147, 0.1);
        }}
        .sort-arrow {{
            margin-left: 5px;
            font-size: 10px;
            color: {COLOR_TEXT_SECONDARY};
        }}
    </style>
    '''
    
    html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Performance Overview</title>
        {table_css}
        <style>
            body {{
                background-color: {COLOR_BLACK};
                color: #FFFFFF;
                font-family: {FONT_FAMILY};
                padding: 40px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            h1 {{
                font-size: 34px;
                font-weight: 600;
                color: #FFFFFF;
                margin-bottom: 10px;
            }}
            .nav-link {{
                color: {COLOR_TEXT_SECONDARY};
                text-decoration: none;
                font-size: 16px;
                margin-left: 20px;
            }}
            .nav-link:hover {{
                color: {COLOR_ACCENT};
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Performance Overview <a href="tags.html" class="nav-link">View Full Tag Analysis →</a></h1>
            <div class="dashboard-grid">
                <div class="dashboard-section">
                    <h3>Metrics</h3>
                    <div class="dashboard-table-container">
                        {_criar_tabela_kpi_html(stats)}
                    </div>
                </div>
                <div class="dashboard-section">
                    <h3>All Tags</h3>
                    <div class="dashboard-table-container">
                        {_criar_tabela_top_tags_html(df_tags)}
                    </div>
                </div>
                <div class="dashboard-section">
                    <h3>Daily Summary</h3>
                    <div class="dashboard-table-container">
                        {_criar_tabela_diaria_html(df_daily, df_main, df_monthly, df_yearly)}
                    </div>
                </div>
                <div class="dashboard-section">
                    <h3>Stake Distribution</h3>
                    <div class="dashboard-table-container">
                        {_criar_tabela_decis_html(df_main)}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    
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

def criar_pagina_tags_resumo(tag_df: pd.DataFrame) -> Tuple[str, str]:
    """Cria o HTML completo para a tags.html com layout de dois lados."""
    
    tag_df_sorted = tag_df.sort_values('roi', ascending=True).copy()
    
    tags_list = tag_df_sorted['tag'].tolist()
    profits = tag_df_sorted['profit'].tolist()
    rois = (tag_df_sorted['roi'] * 100).tolist()
    volumes = tag_df_sorted['volume'].tolist()
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
    import json
    
    # Preparar dados para JavaScript
    tags_data = []
    for _, row in tag_df.iterrows():
        tag_name = row['tag']
        safe_filename = "".join(c if c.isalnum() else "_" for c in tag_name) + ".html"
        tags_data.append({
            'tag': tag_name,
            'tag_link': f'tags/{safe_filename}',
            'profit': float(row['profit']),
            'roi': float(row['roi']),
            'volume': float(row.get('volume', 0)),
            'bets': int(row.get('bets', 0))
        })
    
    tags_json = json.dumps(tags_data)
    
    html = f'''
    <style>
        .tag-table-wrapper {{
            margin: 80px auto; 
            max-width: 95%; 
            font-family: {FONT_FAMILY};
        }}
        .tag-table-wrapper h3 {{
            color: #FFFFFF; 
            font-size: 24px; 
            font-weight: 600;
            margin-bottom: 20px;
        }}
        .tag-table-container {{
            background-color: {COLOR_CONTENT_BG};
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {COLOR_SEPARATOR};
            overflow-x: auto;
            overflow-y: auto;
            max-height: calc(100vh - 400px);
        }}
        /* Scrollbar customizada */
        .tag-table-container::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}
        .tag-table-container::-webkit-scrollbar-track {{
            background: {COLOR_BLACK};
            border-radius: 6px;
        }}
        .tag-table-container::-webkit-scrollbar-thumb {{
            background: {COLOR_SEPARATOR};
            border-radius: 6px;
        }}
        .tag-table-container::-webkit-scrollbar-thumb:hover {{
            background: {COLOR_TEXT_SECONDARY};
        }}
        .tag-table {{
            width: 100%; 
            border-collapse: collapse;
            font-size: 13px;
            color: #FFFFFF;
            min-width: 100%;
        }}
        .tag-table thead {{
            background-color: {COLOR_BLACK};
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .tag-table th {{
            padding: 12px 15px; 
            text-align: left; 
            font-family: {FONT_FAMILY}; 
            font-size: 12px; 
            color: #FFFFFF; 
            font-weight: 600;
            border-bottom: 2px solid {COLOR_SEPARATOR};
            border-right: 1px solid {COLOR_SEPARATOR};
            white-space: nowrap;
            background-color: {COLOR_BLACK};
        }}
        .tag-table th.text-right {{ text-align: right; }}
        .tag-table th:last-child {{ border-right: none; }}
        .tag-table tbody tr {{
            background-color: {COLOR_CONTENT_BG};
            color: #FFFFFF;
            border-bottom: 1px solid {COLOR_SEPARATOR};
        }}
        .tag-table tbody tr:nth-child(even) {{
            background-color: rgba(142, 142, 147, 0.05);
        }}
        .tag-table tbody tr:hover {{
            background-color: rgba(10, 132, 255, 0.1);
        }}
        .tag-table td {{
            padding: 10px 15px; 
            font-size: 14px; 
            font-weight: 400; 
            color: #FFFFFF;
            border-right: 1px solid {COLOR_SEPARATOR};
            white-space: nowrap;
        }}
        .tag-table td.text-right {{ text-align: right; }}
        .tag-table td:last-child {{ border-right: none; }}
        .tag-table td.profit {{ color: {COLOR_PROFIT} !important; font-weight: 500; }}
        .tag-table td.loss {{ color: {COLOR_LOSS} !important; font-weight: 500; }}
        .tag-table td.neutral {{ color: #FFFFFF; }}
        .tag-table a {{
            color: {COLOR_ACCENT}; 
            text-decoration: none; 
            font-weight: 500;
        }}
        .tag-table a:hover {{ text-decoration: underline; }}
        .sortable {{
            cursor: pointer;
            user-select: none;
            position: relative;
        }}
        .sortable:hover {{
            background-color: rgba(142, 142, 147, 0.1);
        }}
        .sort-arrow {{
            margin-left: 5px;
            font-size: 10px;
            color: {COLOR_TEXT_SECONDARY};
        }}
    </style>
    <div class="tag-table-wrapper">
    <h3>All Tags ({len(tag_df)})</h3>
    <div class="tag-table-container">
    <table class="tag-table sortable-table" id="tags-page-table">
        <thead>
            <tr>
                <th class="sortable" data-sort="tag" data-sort-type="string">Tag <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="profit" data-sort-type="number">Profit <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="volume" data-sort-type="number">Volume <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="roi" data-sort-type="number">ROI <span class="sort-arrow">↕</span></th>
                <th class="sortable text-right" data-sort="bets" data-sort-type="number">Bets <span class="sort-arrow">↕</span></th>
        <th>Details</th>
            </tr>
        </thead>
        <tbody id="tags-page-table-body">
        </tbody>
    </table>
    </div>
    </div>
    <script>
        const tagsPageData = {tags_json};
        let currentSort = {{ column: 'profit', direction: 'desc' }};
        let sortedData = [];
        
        function renderTable(data) {{
            const tbody = document.getElementById('tags-page-table-body');
            tbody.innerHTML = '';
            
            data.forEach(row => {{
                const profitClass = row.profit >= 0 ? 'profit' : 'loss';
                const roiClass = row.roi >= 0 ? 'profit' : 'loss';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${{row.tag}}</td>
                    <td class="text-right ${{profitClass}}">$${{row.profit.toLocaleString('en-US', {{maximumFractionDigits: 0}})}}</td>
                    <td class="text-right neutral">$${{row.volume.toLocaleString('en-US', {{maximumFractionDigits: 0}})}}</td>
                    <td class="text-right ${{roiClass}}">${{(row.roi * 100).toFixed(2)}}%</td>
                    <td class="text-right neutral">${{row.bets}}</td>
                    <td><a href="${{row.tag_link}}">View</a></td>
                `;
                tbody.appendChild(tr);
            }});
        }}
        
        function sortTable(column, type) {{
            const direction = currentSort.column === column && currentSort.direction === 'asc' ? 'desc' : 'asc';
            currentSort = {{ column, direction }};
            
            sortedData = [...tagsPageData].sort((a, b) => {{
                let aVal = a[column];
                let bVal = b[column];
                
                if (type === 'number') {{
                    aVal = Number(aVal);
                    bVal = Number(bVal);
                }} else {{
                    aVal = String(aVal).toLowerCase();
                    bVal = String(bVal).toLowerCase();
                }}
                
                if (direction === 'asc') {{
                    return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
                }} else {{
                    return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
                }}
            }});
            
            renderTable(sortedData);
            updateSortArrows(column, direction);
        }}
        
        function updateSortArrows(activeColumn, direction) {{
            document.querySelectorAll('.sort-arrow').forEach(arrow => {{
                arrow.textContent = '↕';
            }});
            const activeHeader = document.querySelector(`[data-sort="${{activeColumn}}"] .sort-arrow`);
            if (activeHeader) {{
                activeHeader.textContent = direction === 'asc' ? '↑' : '↓';
            }}
        }}
        
        document.querySelectorAll('.sortable').forEach(header => {{
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {{
                const column = header.getAttribute('data-sort');
                const type = header.getAttribute('data-sort-type') || 'string';
                sortTable(column, type);
            }});
        }});
        
        // Renderizar inicialmente ordenado por Profit desc
        sortedData = tagsPageData.sort((a, b) => b.profit - a.profit);
        renderTable(sortedData);
        updateSortArrows('profit', 'desc');
    </script>
    '''
    
    # Criar gráfico Plotly único customizável
    chart_json = json.dumps(chart_data)
    
    # Criar figura inicial com Profit
    # Cores: preenchimento mais claro, borda verde/vermelho mais escura
    profit_colors_fill = []
    profit_colors_border = []
    for p in profits:
        if p >= 0:
            profit_colors_fill.append('#34C759')  # Verde mais claro (preenchimento)
            profit_colors_border.append('#28A745')  # Verde mais escuro (borda)
        else:
            profit_colors_fill.append('#FF3B30')  # Vermelho mais claro (preenchimento)
            profit_colors_border.append('#DC3545')  # Vermelho mais escuro (borda)
    
    fig_chart = go.Figure(data=[go.Bar(
        x=profits,
        y=tags_list,
        orientation='h',
        marker=dict(
            color=profit_colors_fill,
            line=dict(
                color=profit_colors_border,  # Bordas verde/vermelho mais escuras
                width=2.5
            ),
            opacity=0.9
        ),
        hovertemplate='<b>%{{y}}</b><br>' +
                      '<b>Profit:</b> $%{{x:,.2f}}<br>' +
                      '<b>ROI:</b> %{{customdata[0]:.2f}}%<br>' +
                      '<b>Volume:</b> $%{{customdata[1]:,.2f}}<br>' +
                      '<b>Bets:</b> %{{customdata[2]}}<extra></extra>',
        customdata=[[rois[i], volumes[i], bets[i]] for i in range(len(rois))]
    )])
    
    fig_chart.update_layout(
        title=dict(
            text='Tag Analysis - Profit',
            x=0.5,
            xanchor='center',
            font=dict(size=24, family=FONT_FAMILY, color=COLOR_WHITE, weight=600)
        ),
        height=max(600, len(tags_list) * 25),
        showlegend=False,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
        plot_bgcolor='rgba(0,0,0,0)',  # Área do gráfico transparente
        margin=dict(t=80, b=80, l=180, r=80),
        font=dict(family=FONT_FAMILY, size=13, color=COLOR_TEXT_SECONDARY)
    )
    
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
    
    # HTML completo com layout de dois lados
    page_html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tag Analysis</title>
        <style>
            body {{
                background-color: {COLOR_BLACK};
                color: #FFFFFF;
                font-family: {FONT_FAMILY};
                margin: 0;
                padding: 20px;
            }}
            .page-header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .page-header h1 {{
                font-size: 34px;
                font-weight: 600;
                color: #FFFFFF;
                margin-bottom: 10px;
            }}
            .page-header a {{
                color: {COLOR_TEXT_SECONDARY};
                text-decoration: none;
                font-size: 16px;
            }}
            .page-header a:hover {{
                color: {COLOR_ACCENT};
            }}
            .tags-layout {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                max-width: 1800px;
                margin: 0 auto;
            }}
            .left-panel {{
                background-color: {COLOR_CONTENT_BG};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid {COLOR_SEPARATOR};
            }}
            .right-panel {{
                background-color: {COLOR_CONTENT_BG};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid {COLOR_SEPARATOR};
            }}
            .chart-controls {{
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            .chart-controls label {{
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 500;
            }}
            .chart-controls select {{
                padding: 8px 15px;
                background: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid #38383A;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-family: {FONT_FAMILY};
            }}
            .chart-controls select:focus {{
                outline: none;
                border-color: {COLOR_ACCENT};
            }}
            #tags-chart {{
                width: 100%;
                height: 100%;
                background: transparent;
            }}
            #chart-container {{
                background: transparent;
            }}
            .js-plotly-plot {{
                background: transparent !important;
            }}
            .js-plotly-plot .plotly {{
                background: transparent !important;
            }}
            /* Tentativa de arredondar cantos das barras usando SVG */
            .js-plotly-plot .trace.bars path {{
                stroke-linecap: round;
                stroke-linejoin: round;
            }}
        </style>
    </head>
    <body>
        <div class="page-header">
            <h1>Tag Analysis <a href="index.html">← Back to Overview</a></h1>
        </div>
        <div class="tags-layout">
            <div class="left-panel">
                {html}
            </div>
            <div class="right-panel">
                <div class="chart-controls">
                    <label>Mostrar:</label>
                    <select id="chart-metric">
                        <option value="profit">Profit</option>
                        <option value="roi">ROI</option>
                        <option value="volume">Volume</option>
                        <option value="bets">Bets</option>
                    </select>
                </div>
                <div id="chart-container">
                    {chart_html}
                </div>
            </div>
        </div>
        <script>
            const chartData = {chart_json};
            
            // Tornar updateChart disponível globalmente
            window.updateChart = function updateChart() {{
                console.log('updateChart chamado');
                const metric = document.getElementById('chart-metric').value;
                const metricLabels = {{
                    'profit': 'Profit',
                    'roi': 'ROI (%)',
                    'volume': 'Volume',
                    'bets': 'Bets'
                }};
                
                const metricData = chartData.map(item => item[metric]);
                const tags = chartData.map(item => item.tag);
                
                let colors, colorsBorder, hoverTemplate, customData;
                
                if (metric === 'profit') {{
                    colors = metricData.map(p => p >= 0 ? '#34C759' : '#FF3B30');
                    colorsBorder = metricData.map(p => p >= 0 ? '#28A745' : '#DC3545');
                    customData = chartData.map(item => [item.roi, item.volume, item.bets]);
                    // Formatando: x é profit, customdata[0] é roi (em %), customdata[1] é volume, customdata[2] é bets
                    hoverTemplate = '<b>%{{y}}</b><br>' +
                                   '<b>Profit:</b> $%{{x:,.2f}}<br>' +
                                   '<b>ROI:</b> %{{customdata[0]:.2f}}%<br>' +
                                   '<b>Volume:</b> $%{{customdata[1]:,.2f}}<br>' +
                                   '<b>Bets:</b> %{{customdata[2]:.0f}}<extra></extra>';
                }} else if (metric === 'roi') {{
                    colors = metricData.map(r => r >= 0 ? '#34C759' : '#FF3B30');
                    colorsBorder = metricData.map(r => r >= 0 ? '#28A745' : '#DC3545');
                    customData = chartData.map(item => [item.profit, item.volume, item.bets]);
                    // Formatando: x é roi (já em %), customdata[0] é profit, customdata[1] é volume, customdata[2] é bets
                    hoverTemplate = '<b>%{{y}}</b><br>' +
                                   '<b>ROI:</b> %{{x:.2f}}%<br>' +
                                   '<b>Profit:</b> $%{{customdata[0]:,.2f}}<br>' +
                                   '<b>Volume:</b> $%{{customdata[1]:,.2f}}<br>' +
                                   '<b>Bets:</b> %{{customdata[2]:.0f}}<extra></extra>';
                }} else if (metric === 'volume') {{
                    colors = Array(metricData.length).fill('#007AFF');
                    colorsBorder = Array(metricData.length).fill('#0056CC');
                    customData = chartData.map(item => [item.profit, item.roi, item.bets]);
                    // Formatando: x é volume, customdata[0] é profit, customdata[1] é roi (em %), customdata[2] é bets
                    hoverTemplate = '<b>%{{y}}</b><br>' +
                                   '<b>Volume:</b> $%{{x:,.2f}}<br>' +
                                   '<b>Profit:</b> $%{{customdata[0]:,.2f}}<br>' +
                                   '<b>ROI:</b> %{{customdata[1]:.2f}}%<br>' +
                                   '<b>Bets:</b> %{{customdata[2]:.0f}}<extra></extra>';
                }} else {{
                    colors = Array(metricData.length).fill('#8E8E93');
                    colorsBorder = Array(metricData.length).fill('#636366');
                    customData = chartData.map(item => [item.profit, item.roi, item.volume]);
                    // Formatando: x é bets, customdata[0] é profit, customdata[1] é roi (em %), customdata[2] é volume
                    hoverTemplate = '<b>%{{y}}</b><br>' +
                                   '<b>Bets:</b> %{{x:.0f}}<br>' +
                                   '<b>Profit:</b> $%{{customdata[0]:,.2f}}<br>' +
                                   '<b>ROI:</b> %{{customdata[1]:.2f}}%<br>' +
                                   '<b>Volume:</b> $%{{customdata[2]:,.2f}}<extra></extra>';
                }}
                
                const data = [{{
                    x: metricData,
                    y: tags,
                    type: 'bar',
                    orientation: 'h',
                    marker: {{
                        color: colors,
                        opacity: 0.9,
                        line: {{
                            color: colorsBorder,
                            width: 2.5
                        }}
                    }},
                    hovertemplate: hoverTemplate,
                    customdata: customData
                }}];
                
                const layout = {{
                    title: {{
                        text: 'Tag Analysis - ' + metricLabels[metric],
                        x: 0.5,
                        xanchor: 'center',
                        font: {{
                            size: 24,
                            family: '{FONT_FAMILY}',
                            color: '#FFFFFF',
                            weight: 600
                        }}
                    }},
                    height: Math.max(600, tags.length * 25),
                    showlegend: false,
                    template: 'plotly_dark',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    margin: {{ t: 80, b: 80, l: 180, r: 80 }},
                    font: {{
                        family: '{FONT_FAMILY}',
                        size: 13,
                        color: '{COLOR_TEXT_SECONDARY}'
                    }},
                    yaxis: {{
                        showgrid: false,
                        tickfont: {{
                            size: 12,
                            color: '{COLOR_TEXT_SECONDARY}'
                        }},
                        title: ''
                    }},
                    xaxis: {{
                        showgrid: true,
                        gridcolor: '{COLOR_SEPARATOR}',
                        zerolinecolor: '{COLOR_SEPARATOR}',
                        zeroline: true
                    }}
                }};
                
                // Usar Plotly.react se o gráfico já existe, senão Plotly.newPlot
                const chartDiv = document.getElementById('tags-chart');
                if (chartDiv && typeof Plotly !== 'undefined') {{
                    // Verificar se o gráfico já foi inicializado - Plotly armazena dados de forma diferente
                    let hasExistingPlot = false;
                    try {{
                        const plotlyDiv = chartDiv.querySelector('.plotly');
                        hasExistingPlot = plotlyDiv !== null && plotlyDiv !== undefined;
                    }} catch(e) {{
                        // Ignorar erro
                    }}
                    
                    // Sempre usar Plotly.react - ele funciona mesmo na primeira vez se o elemento existe
                    Plotly.react('tags-chart', data, layout, {{
                        displayModeBar: false,
                        responsive: true
                    }}).then(function() {{
                        console.log('Gráfico atualizado com sucesso');
                        roundBarCorners();
                    }}).catch(function(err) {{
                        console.warn('Plotly.react falhou, tentando Plotly.newPlot:', err);
                        // Se react falhar, usar newPlot
                        Plotly.newPlot('tags-chart', data, layout, {{
                            displayModeBar: false,
                            responsive: true
                        }}).then(function() {{
                            console.log('Gráfico recriado com Plotly.newPlot');
                            roundBarCorners();
                        }});
                    }});
                }} else {{
                    console.error('Plotly não está disponível ou elemento tags-chart não encontrado');
                }}
            }}
            
            // Função para arredondar cantos das barras (aproximação via SVG)
            function roundBarCorners() {{
                const chartDiv = document.getElementById('tags-chart');
                if (!chartDiv) return;
                
                // Tentar arredondar paths SVG das barras
                setTimeout(function() {{
                    // Para barras horizontais, modificar os retângulos SVG se existirem
                    const rects = chartDiv.querySelectorAll('.trace.bars rect');
                    rects.forEach(function(rect) {{
                        rect.setAttribute('rx', '8');
                        rect.setAttribute('ry', '8');
                    }});
                    
                    // Para paths, tentar suavizar cantos
                    const paths = chartDiv.querySelectorAll('.trace.bars path');
                    paths.forEach(function(path) {{
                        path.setAttribute('stroke-linecap', 'round');
                        path.setAttribute('stroke-linejoin', 'round');
                    }});
                }}, 100);
            }}
            
            // Adicionar event listener após o DOM e Plotly estarem prontos
            function initChartControls() {{
                const selectElement = document.getElementById('chart-metric');
                if (selectElement) {{
                    // Usar onchange diretamente (mais confiável)
                    selectElement.onchange = function() {{
                        console.log('Select mudou para:', selectElement.value);
                        if (typeof window.updateChart === 'function') {{
                            window.updateChart();
                        }} else {{
                            console.error('updateChart não está disponível');
                        }}
                    }};
                    console.log('Event listener anexado ao select chart-metric');
                }} else {{
                    console.error('Elemento chart-metric não encontrado');
                }}
            }}
            
            // Aguardar Plotly carregar
            function waitForPlotly(callback, maxAttempts = 100) {{
                let attempts = 0;
                function check() {{
                    attempts++;
                    if (typeof Plotly !== 'undefined') {{
                        callback();
                    }} else if (attempts < maxAttempts) {{
                        setTimeout(check, 50);
                    }} else {{
                        console.error('Plotly não carregou após', maxAttempts * 50, 'ms');
                    }}
                }}
                check();
            }}
            
            // Inicializar quando a página estiver pronta
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', function() {{
                    waitForPlotly(function() {{
                        initChartControls();
                        // Arredondar cantos após o gráfico inicial ser renderizado
                        setTimeout(function() {{
                            roundBarCorners();
                        }}, 500);
                    }});
                }});
            }} else {{
                waitForPlotly(function() {{
                    initChartControls();
                    setTimeout(function() {{
                        roundBarCorners();
                    }}, 500);
                }});
            }}
            
            // Também adicionar event listener inline como fallback
            window.addEventListener('load', function() {{
                const selectElement = document.getElementById('chart-metric');
                if (selectElement && !selectElement.hasAttribute('data-listener-attached')) {{
                    selectElement.setAttribute('data-listener-attached', 'true');
                    selectElement.addEventListener('change', updateChart);
                }}
            }});
        </script>
    </body>
    </html>
    '''
    
    return page_html, ''  # Retorna HTML completo e string vazia (não precisa mais do fig_tags separado)

def criar_pagina_detalhe_tag(df_tag: pd.DataFrame, tag_name: str, df_daily: pd.DataFrame):
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
    
    # Criar gráfico de barras diário
    daily_filtered = df_daily[df_daily['profit'] != 0].sort_values('date')
    bar_colors = [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in daily_filtered['profit']]
    
    fig_bar = go.Figure(data=[go.Bar(
        x=daily_filtered['date'].astype(str),
        y=daily_filtered['profit'],
        marker_color=bar_colors,
        name='Profit Diário'
    )])
    
    fig_bar.update_layout(
        title=f'Daily Performance for \'{tag_name}\'',
        xaxis_title='Date',
        yaxis_title='Profit',
        template='plotly_dark',
        paper_bgcolor=COLOR_BLACK,
        plot_bgcolor=COLOR_CONTENT_BG,
        font=dict(family=FONT_FAMILY, size=13, color=COLOR_TEXT_SECONDARY),
        height=400
    )
    
    fig_bar.update_xaxes(showgrid=True, gridcolor=COLOR_SEPARATOR, zerolinecolor=COLOR_SEPARATOR)
    fig_bar.update_yaxes(showgrid=False, zeroline=False)
    
    bar_chart_html = fig_bar.to_html(full_html=False, include_plotlyjs='cdn', div_id='daily-chart')
    
    # Criar nome do arquivo seguro para link
    safe_filename = "".join(c if c.isalnum() else "_" for c in tag_name)
    apostas_filename = f"{safe_filename}_apostas.html"
    
    # CSS compartilhado
    table_css = f'''
    <style>
        body {{
            background-color: {COLOR_BLACK};
            color: #FFFFFF;
            font-family: {FONT_FAMILY};
            padding: 40px 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 34px;
            font-weight: 600;
            color: #FFFFFF;
            margin-bottom: 10px;
        }}
        .nav-links {{
            margin-top: 10px;
            margin-bottom: 30px;
        }}
        .nav-links a {{
            color: {COLOR_TEXT_SECONDARY};
            text-decoration: none;
            font-size: 16px;
            margin-right: 20px;
        }}
        .nav-links a:hover {{
            color: {COLOR_ACCENT};
        }}
        .nav-links a.highlight {{
            color: {COLOR_ACCENT};
            font-weight: 500;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }}
        .dashboard-section {{
            background-color: {COLOR_CONTENT_BG};
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {COLOR_SEPARATOR};
        }}
        .dashboard-section h3 {{
            color: #FFFFFF;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            margin-top: 0;
        }}
        .dashboard-table-container {{
            background-color: {COLOR_CONTENT_BG};
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {COLOR_SEPARATOR};
            overflow-x: auto;
        }}
        .dashboard-table-container::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}
        .dashboard-table-container::-webkit-scrollbar-track {{
            background: {COLOR_BLACK};
            border-radius: 6px;
        }}
        .dashboard-table-container::-webkit-scrollbar-thumb {{
            background: {COLOR_SEPARATOR};
            border-radius: 6px;
        }}
        .dashboard-table-container::-webkit-scrollbar-thumb:hover {{
            background: {COLOR_TEXT_SECONDARY};
        }}
        .dashboard-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            color: #FFFFFF;
            background-color: {COLOR_CONTENT_BG};
        }}
        .dashboard-table thead {{
            background-color: {COLOR_BLACK};
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .dashboard-table th {{
            padding: 12px 15px;
            text-align: left;
            color: #FFFFFF;
            font-weight: 600;
            font-size: 12px;
            border-bottom: 2px solid {COLOR_SEPARATOR};
            border-right: 1px solid {COLOR_SEPARATOR};
            white-space: nowrap;
            background-color: {COLOR_BLACK};
        }}
        .dashboard-table th.text-right {{
            text-align: right;
        }}
        .dashboard-table th:last-child {{
            border-right: none;
        }}
        .dashboard-table tbody tr {{
            background-color: {COLOR_CONTENT_BG};
            color: #FFFFFF;
            border-bottom: 1px solid {COLOR_SEPARATOR};
        }}
        .dashboard-table tbody tr:nth-child(even) {{
            background-color: rgba(142, 142, 147, 0.05);
        }}
        .dashboard-table tbody tr:hover {{
            background-color: rgba(10, 132, 255, 0.1);
        }}
        .dashboard-table td {{
            padding: 10px 15px;
            border-right: 1px solid {COLOR_SEPARATOR};
            color: #FFFFFF;
            white-space: nowrap;
        }}
        .dashboard-table td.text-right {{
            text-align: right;
        }}
        .dashboard-table td:last-child {{
            border-right: none;
        }}
        .dashboard-table .profit {{
            color: {COLOR_PROFIT} !important;
            font-weight: 500;
        }}
        .dashboard-table .loss {{
            color: {COLOR_LOSS} !important;
            font-weight: 500;
        }}
        .dashboard-table .neutral {{
            color: #FFFFFF;
        }}
        .chart-container {{
            background-color: {COLOR_CONTENT_BG};
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {COLOR_SEPARATOR};
        }}
    </style>
    '''
    
    html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Detailed Analysis: {tag_name}</title>
        {table_css}
    </head>
    <body>
        <div class="container">
            <h1>Detailed Analysis: {tag_name}</h1>
            <div class="nav-links">
                <a href="../index.html">← Back to Overview</a>
                <a href="../tags.html">← Back to All Tags</a>
                <a href="{apostas_filename}" class="highlight">📋 Ver Todas as Apostas</a>
            </div>
            
            <div class="dashboard-grid">
                <div class="dashboard-section">
                    <h3>Tag Metrics</h3>
                    <div class="dashboard-table-container">
                        {_criar_tabela_kpi_html(stats)}
                    </div>
                </div>
                <div class="dashboard-section">
                    <h3>Daily Performance for '{tag_name}'</h3>
                    <div class="chart-container">
                        {bar_chart_html}
                    </div>
                </div>
                <div class="dashboard-section">
                    <h3>Daily Summary (Last 10)</h3>
                    <div class="dashboard-table-container">
                        {_criar_tabela_diaria_html(df_daily)}
                    </div>
                </div>
                <div class="dashboard-section">
                    <h3>Stake Distribution</h3>
                    <div class="dashboard-table-container">
                        {_criar_tabela_decis_html(df_tag)}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    
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
    
    daily_filtered = df_daily[df_daily['profit'] != 0].sort_values('date')
    bar_colors = [COLOR_PROFIT if p >= 0 else COLOR_LOSS for p in daily_filtered['profit']]
    fig.add_trace(go.Bar(
        x=daily_filtered['date'].astype(str),
        y=daily_filtered['profit'],
        marker_color=bar_colors,
        name='Profit Diário'
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
    
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_SEPARATOR, zerolinecolor=COLOR_SEPARATOR, row=1, col=2)
    fig.update_yaxes(showgrid=False, zeroline=False, row=1, col=2)
    
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
    total_profit = df_tag['total_profit'].sum() if 'total_profit' in df_tag.columns else (df_tag.get('realizedPnl', pd.Series([0])).fillna(0).sum() + df_tag.get('cashPnl', pd.Series([0])).fillna(0).sum())
    total_volume = df_tag['volume'].sum() if 'volume' in df_tag.columns else (df_tag['totalBought'] * df_tag['avgPrice']).sum()
    
    # Ordenar por data (mais recente primeiro) - priorizar colunas de data
    date_col = None
    if 'createdTimestamp' in df_tag.columns:
        date_col = 'createdTimestamp'
        df_sorted = df_tag.sort_values('createdTimestamp', ascending=False).copy()
    elif 'timestamp' in df_tag.columns:
        date_col = 'timestamp'
        df_sorted = df_tag.sort_values('timestamp', ascending=False).copy()
    elif 'date' in df_tag.columns:
        date_col = 'date'
        df_sorted = df_tag.sort_values('date', ascending=False).copy()
    else:
        df_sorted = df_tag.copy()
    
    # Pegar TODAS as colunas do DataFrame
    all_columns = df_sorted.columns.tolist()
    
    # Reordenar colunas: data primeiro, depois as outras em ordem original
    ordered_columns = []
    if date_col and date_col in all_columns:
        ordered_columns.append(date_col)
    
    # Adicionar outras colunas (exceto a de data que já foi adicionada)
    for col in all_columns:
        if col != date_col:
            ordered_columns.append(col)
    
    # Criar lista de (label, col) para todas as colunas
    existing_cols = []
    for col in ordered_columns:
        # Usar o nome da coluna como label (podemos melhorar depois com nomes mais amigáveis)
        label = col
        existing_cols.append((label, col))
    
    # Função auxiliar para detectar tipo de coluna
    def detect_column_type(col_name, sample_value):
        """Detecta o tipo de coluna baseado no nome e valor."""
        col_lower = str(col_name).lower()
        
        # IDs e códigos longos
        if any(x in col_lower for x in ['id', 'condition', 'market', 'token', 'hash', 'address']):
            return 'id_string'
        
        # Timestamps e datas
        if any(x in col_lower for x in ['timestamp', 'time', 'date', 'created', 'updated']):
            return 'datetime'
        
        # Valores monetários
        if any(x in col_lower for x in ['profit', 'pnl', 'price', 'stake', 'volume', 'value', 'amount']):
            return 'currency'
        
        # Quantidades inteiras
        if any(x in col_lower for x in ['bought', 'sold', 'quantity', 'count', 'totalbought', 'totalsold']):
            return 'integer'
        
        # Números decimais
        if isinstance(sample_value, (int, float)) and not pd.isna(sample_value):
            return 'number'
        
        # Strings longas
        if isinstance(sample_value, str) and len(str(sample_value)) > 30:
            return 'long_string'
        
        return 'string'
    
    # Criar HTML
    html = f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Todas as Apostas - {tag_name}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background-color: {COLOR_BLACK};
                color: #FFFFFF;
                font-family: {FONT_FAMILY};
                padding: 40px 20px;
                line-height: 1.6;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .header {{
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid {COLOR_SEPARATOR};
            }}
            
            h1 {{
                font-size: 34px;
                font-weight: 600;
                color: #FFFFFF;
                margin-bottom: 10px;
            }}
            
            .table-wrapper {{
                background-color: {COLOR_CONTENT_BG};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid {COLOR_SEPARATOR};
                overflow-x: auto;
                overflow-y: auto;
                max-height: calc(100vh - 300px);
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
                color: #FFFFFF;
                min-width: 100%;
            }}
            
            thead {{
                background-color: {COLOR_BLACK};
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            
            th {{
                padding: 12px 15px;
                text-align: left;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 12px;
                border-bottom: 2px solid {COLOR_SEPARATOR};
                border-right: 1px solid {COLOR_SEPARATOR};
                white-space: nowrap;
                background-color: {COLOR_BLACK};
            }}
            
            th.text-right {{
                text-align: right;
            }}
            
            th:last-child {{
                border-right: none;
            }}
            
            tbody tr {{
                background-color: {COLOR_CONTENT_BG};
                color: #FFFFFF;
                border-bottom: 1px solid {COLOR_SEPARATOR};
            }}
            
            tbody tr:nth-child(even) {{
                background-color: rgba(142, 142, 147, 0.05);
            }}
            
            tbody tr:hover {{
                background-color: rgba(10, 132, 255, 0.1);
            }}
            
            td {{
                padding: 10px 15px;
                border-right: 1px solid {COLOR_SEPARATOR};
                color: #FFFFFF;
                white-space: nowrap;
            }}
            
            td.text-right {{
                text-align: right;
            }}
            
            td:last-child {{
                border-right: none;
            }}
            
            .profit {{
                color: {COLOR_PROFIT} !important;
                font-weight: 500;
            }}
            
            .loss {{
                color: {COLOR_LOSS} !important;
                font-weight: 500;
            }}
            
            .hidden-row {{
                display: none;
            }}
            
            /* Scrollbar customizada */
            .table-wrapper::-webkit-scrollbar {{
                width: 12px;
                height: 12px;
            }}
            
            .table-wrapper::-webkit-scrollbar-track {{
                background: {COLOR_BLACK};
                border-radius: 6px;
            }}
            
            .table-wrapper::-webkit-scrollbar-thumb {{
                background: {COLOR_SEPARATOR};
                border-radius: 6px;
            }}
            
            .table-wrapper::-webkit-scrollbar-thumb:hover {{
                background: {COLOR_TEXT_SECONDARY};
            }}
            
            .load-more-btn {{
                margin-top: 20px;
                padding: 12px 24px;
                background-color: {COLOR_ACCENT};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            
            .load-more-btn:hover {{
                background-color: #0071E3;
            }}
            
            .load-more-btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            
            .column-controls {{
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
                align-items: center;
            }}
            
            .toggle-columns-btn {{
                padding: 10px 20px;
                background-color: {COLOR_CONTENT_BG};
                color: #FFFFFF;
                border: 1px solid {COLOR_SEPARATOR};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .toggle-columns-btn:hover {{
                background-color: rgba(10, 132, 255, 0.1);
                border-color: {COLOR_ACCENT};
            }}
            
            /* Modal para seleção de colunas */
            .column-modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }}
            
            .column-modal.active {{
                display: flex;
            }}
            
            .column-modal-content {{
                background-color: {COLOR_CONTENT_BG};
                border: 1px solid {COLOR_SEPARATOR};
                border-radius: 12px;
                padding: 30px;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
                color: #FFFFFF;
            }}
            
            .column-modal-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid {COLOR_SEPARATOR};
            }}
            
            .column-modal-header h3 {{
                margin: 0;
                color: #FFFFFF;
                font-size: 20px;
            }}
            
            .close-modal {{
                background: none;
                border: none;
                color: #FFFFFF;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background-color 0.2s;
            }}
            
            .close-modal:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            
            .column-checkboxes {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}
            
            .column-checkbox-item {{
                display: flex;
                align-items: center;
                padding: 8px;
                border-radius: 6px;
                transition: background-color 0.2s;
            }}
            
            .column-checkbox-item:hover {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
            
            .column-checkbox-item input[type="checkbox"] {{
                margin-right: 10px;
                width: 18px;
                height: 18px;
                cursor: pointer;
            }}
            
            .column-checkbox-item label {{
                color: #FFFFFF;
                cursor: pointer;
                font-size: 14px;
                flex: 1;
            }}
            
            .modal-actions {{
                display: flex;
                gap: 10px;
                justify-content: flex-end;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid {COLOR_SEPARATOR};
            }}
            
            .modal-btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .modal-btn.select-all {{
                background-color: {COLOR_ACCENT};
                color: #FFFFFF;
            }}
            
            .modal-btn.select-all:hover {{
                background-color: #0071E3;
            }}
            
            .modal-btn.apply {{
                background-color: {COLOR_PROFIT};
                color: #FFFFFF;
            }}
            
            .modal-btn.apply:hover {{
                background-color: #28C050;
            }}
            
            .hidden-column {{
                display: none;
            }}
            
            .stats {{
                display: flex;
                gap: 30px;
                margin-top: 20px;
                flex-wrap: wrap;
            }}
            
            .stat-box {{
                background-color: {COLOR_CONTENT_BG};
                padding: 15px 20px;
                border-radius: 12px;
                border: 1px solid {COLOR_SEPARATOR};
            }}
            
            .stat-label {{
                font-size: 13px;
                color: {COLOR_TEXT_SECONDARY};
                margin-bottom: 5px;
            }}
            
            .stat-value {{
                font-size: 20px;
                font-weight: 600;
                color: #FFFFFF;
            }}
            
            .stat-value.profit {{
                color: {COLOR_PROFIT};
            }}
            
            .stat-value.loss {{
                color: {COLOR_LOSS};
            }}
            
            .stat-value.neutral {{
                color: #FFFFFF;
            }}
            
            .nav-links {{
                margin-top: 15px;
            }}
            
            .nav-links a {{
                color: {COLOR_TEXT_SECONDARY};
                text-decoration: none;
                font-size: 16px;
                margin-right: 15px;
                transition: color 0.2s;
            }}
            
            .nav-links a:hover {{
                color: {COLOR_ACCENT};
            }}
            
            .table-container {{
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Todas as Apostas: {tag_name}</h1>
                <div class="nav-links">
                    <a href="{safe_filename}">← Voltar ao Detalhe</a>
                    <a href="../tags.html">← Ver Todas as Tags</a>
                    <a href="../index.html">← Página Inicial</a>
                </div>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-label">Total de Apostas</div>
                        <div class="stat-value neutral">{total_bets:,}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Profit Total</div>
                        <div class="stat-value {'profit' if total_profit >= 0 else 'loss'}">
                            ${total_profit:,.2f}
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Volume Total</div>
                        <div class="stat-value neutral">${total_volume:,.2f}</div>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                <div class="column-controls">
                    <button id="toggle-columns-btn" class="toggle-columns-btn">📋 Mostrar/Ocultar Colunas</button>
                </div>
                
                <div class="table-wrapper">
                    <table id="trades-table">
                        <thead>
                            <tr>
    '''
    
    # Adicionar cabeçalhos da tabela com data-column para identificação
    column_ids = []
    for label, col in existing_cols:
        # Detectar tipo para alinhamento
        sample_val = None
        if len(df_sorted) > 0:
            for val in df_sorted[col]:
                if pd.notna(val):
                    sample_val = val
                    break
        
        col_type = detect_column_type(col, sample_val)
        is_numeric = col_type in ['currency', 'integer', 'number']
        align_class = 'text-right' if is_numeric else ''
        column_id = f"col_{col}"
        column_ids.append(column_id)
        html += f'                                <th class="{align_class}" data-column="{column_id}">{label}</th>\n'
    
    html += '''                            </tr>
                        </thead>
                        <tbody>
    '''
    
    # Limite de caracteres para strings longas
    MAX_STRING_LENGTH = 30
    
    # Adicionar todas as linhas (mas inicialmente só mostrar 50)
    row_index = 0
    for _, row in df_sorted.iterrows():
        row_class = '' if row_index < 50 else 'hidden-row'
        html += f'                            <tr class="{row_class}" data-index="{row_index}">\n'
        
        col_idx = 0
        for label, col in existing_cols:
            column_id = column_ids[col_idx]
            value = row[col]
            col_type = detect_column_type(col, value)
            
            # Formatar valores baseado no tipo
            if pd.isna(value):
                formatted_value = '<span style="opacity: 0.5;">-</span>'
                cell_class = ''
            elif col_type == 'datetime':
                try:
                    from datetime import datetime
                    if isinstance(value, (int, float)) and pd.notna(value):
                        ts = value / 1000 if value > 1e10 else value
                        dt = datetime.fromtimestamp(ts)
                        formatted_value = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        formatted_value = str(value)
                except:
                    formatted_value = str(value)
                cell_class = ''
            elif col_type == 'currency':
                formatted_value = f'${value:,.2f}'
                if 'profit' in str(col).lower() or 'pnl' in str(col).lower():
                    cell_class = 'profit' if value >= 0 else 'loss'
                else:
                    cell_class = ''
            elif col_type == 'integer':
                formatted_value = f'{int(value):,}'
                cell_class = ''
            elif col_type == 'number':
                if abs(value) < 0.01:
                    formatted_value = f'{value:.6f}'
                elif abs(value) < 1:
                    formatted_value = f'{value:.4f}'
                else:
                    formatted_value = f'{value:,.2f}'
                cell_class = ''
            elif col_type == 'id_string' or col_type == 'long_string':
                str_value = str(value)
                if len(str_value) > MAX_STRING_LENGTH:
                    formatted_value = f'<span title="{str_value}">{str_value[:MAX_STRING_LENGTH]}...</span>'
                else:
                    formatted_value = str_value
                cell_class = ''
            else:
                str_value = str(value)
                if len(str_value) > MAX_STRING_LENGTH:
                    formatted_value = f'<span title="{str_value}">{str_value[:MAX_STRING_LENGTH]}...</span>'
                else:
                    formatted_value = str_value
                cell_class = ''
            
            # Determinar alinhamento
            is_numeric = col_type in ['currency', 'integer', 'number']
            align_class = 'text-right' if is_numeric else ''
            
            html += f'                                <td class="{align_class}" data-column="{column_id}"><span class="{cell_class}">{formatted_value}</span></td>\n'
            col_idx += 1
        
        html += '                            </tr>\n'
        row_index += 1
    
    html += f'''                        </tbody>
                    </table>
                </div>
                <button id="load-more-btn" class="load-more-btn" style="display: {'block' if len(df_sorted) > 50 else 'none'};">Carregar mais 50 (50 / {len(df_sorted)} mostrados)</button>
            </div>
        </div>
        
        <!-- Modal para seleção de colunas -->
        <div id="column-modal" class="column-modal">
            <div class="column-modal-content">
                <div class="column-modal-header">
                    <h3>Mostrar/Ocultar Colunas</h3>
                    <button class="close-modal" id="close-modal-btn">&times;</button>
                </div>
                <div class="column-checkboxes" id="column-checkboxes">
    '''
    
    # Adicionar checkboxes para cada coluna
    for idx, (label, col) in enumerate(existing_cols):
        column_id = column_ids[idx]
        html += f'''                    <div class="column-checkbox-item">
                        <input type="checkbox" id="checkbox-{column_id}" data-column="{column_id}" checked>
                        <label for="checkbox-{column_id}">{label}</label>
                    </div>
    '''
    
    html += '''                </div>
                <div class="modal-actions">
                    <button class="modal-btn select-all" id="select-all-btn">Marcar Todas</button>
                    <button class="modal-btn select-all" id="deselect-all-btn">Desmarcar Todas</button>
                    <button class="modal-btn apply" id="apply-columns-btn">Aplicar</button>
                </div>
            </div>
        </div>
        
        <script>
            // Aguardar DOM estar pronto
            document.addEventListener('DOMContentLoaded', function() {{
                // Função para mostrar/ocultar colunas
                function toggleColumns() {{
                    const checkboxes = document.querySelectorAll('#column-checkboxes input[type="checkbox"]');
                    checkboxes.forEach(function(checkbox) {{
                        const columnId = checkbox.getAttribute('data-column');
                        const isVisible = checkbox.checked;
                        
                        // Ocultar/mostrar cabeçalhos
                        const headers = document.querySelectorAll('th[data-column="' + columnId + '"]');
                        headers.forEach(function(header) {{
                            if (isVisible) {{
                                header.classList.remove('hidden-column');
                            }} else {{
                                header.classList.add('hidden-column');
                            }}
                        }});
                        
                        // Ocultar/mostrar células
                        const cells = document.querySelectorAll('td[data-column="' + columnId + '"]');
                        cells.forEach(function(cell) {{
                            if (isVisible) {{
                                cell.classList.remove('hidden-column');
                            }} else {{
                                cell.classList.add('hidden-column');
                            }}
                        }});
                    }});
                }}
                
                // Abrir modal
                const toggleBtn = document.getElementById('toggle-columns-btn');
                if (toggleBtn) {{
                    toggleBtn.addEventListener('click', function() {{
                        const modal = document.getElementById('column-modal');
                        if (modal) {{
                            modal.classList.add('active');
                        }}
                    }});
                }}
                
                // Fechar modal
                const closeBtn = document.getElementById('close-modal-btn');
                if (closeBtn) {{
                    closeBtn.addEventListener('click', function() {{
                        const modal = document.getElementById('column-modal');
                        if (modal) {{
                            modal.classList.remove('active');
                        }}
                    }});
                }}
                
                // Fechar modal ao clicar fora
                const modal = document.getElementById('column-modal');
                if (modal) {{
                    modal.addEventListener('click', function(e) {{
                        if (e.target === this) {{
                            this.classList.remove('active');
                        }}
                    }});
                }}
                
                // Marcar todas
                const selectAllBtn = document.getElementById('select-all-btn');
                if (selectAllBtn) {{
                    selectAllBtn.addEventListener('click', function() {{
                        const checkboxes = document.querySelectorAll('#column-checkboxes input[type="checkbox"]');
                        checkboxes.forEach(function(cb) {{
                            cb.checked = true;
                        }});
                    }});
                }}
                
                // Desmarcar todas
                const deselectAllBtn = document.getElementById('deselect-all-btn');
                if (deselectAllBtn) {{
                    deselectAllBtn.addEventListener('click', function() {{
                        const checkboxes = document.querySelectorAll('#column-checkboxes input[type="checkbox"]');
                        checkboxes.forEach(function(cb) {{
                            cb.checked = false;
                        }});
                    }});
                }}
                
                // Aplicar mudanças
                const applyBtn = document.getElementById('apply-columns-btn');
                if (applyBtn) {{
                    applyBtn.addEventListener('click', function() {{
                        toggleColumns();
                        const modal = document.getElementById('column-modal');
                        if (modal) {{
                            modal.classList.remove('active');
                        }}
                    }});
                }}
            }});
        </script>
        
        <script>
            let currentSize = 50;
            const totalRows = {len(df_sorted)};
            const rows = document.querySelectorAll('#trades-table tbody tr');
            
            function updateTable() {{
                rows.forEach((row, index) => {{
                    if (index < currentSize) {{
                        row.classList.remove('hidden-row');
                    }} else {{
                        row.classList.add('hidden-row');
                    }}
                }});
                
                const loadMoreBtn = document.getElementById('load-more-btn');
                if (currentSize < totalRows) {{
                    loadMoreBtn.style.display = 'block';
                    loadMoreBtn.textContent = `Carregar mais 50 (${{currentSize}} / ${{totalRows}} mostrados)`;
                }} else {{
                    loadMoreBtn.style.display = 'none';
                }}
            }}
            
            document.getElementById('load-more-btn').addEventListener('click', function() {{
                currentSize = Math.min(currentSize + 50, totalRows);
                updateTable();
            }});
        </script>
    </body>
    </html>
    '''
    
    return html