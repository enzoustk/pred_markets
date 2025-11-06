"""
Funções auxiliares reutilizáveis para criação de gráficos Plotly.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from dashboard.constants import *


def hex_to_rgba(hex_color: str, alpha: float = 0.3) -> str:
    """
    Converte cor hex para rgba com transparência.
    
    Args:
        hex_color: Cor em formato hex (ex: '#34C759' ou '34C759')
        alpha: Valor de transparência entre 0 e 1 (padrão: 0.3)
    
    Returns:
        String no formato rgba (ex: 'rgba(52, 199, 89, 0.3)')
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f'rgba({r}, {g}, {b}, {alpha})'


def get_profit_loss_colors(values: List[float]) -> Tuple[List[str], List[str]]:
    """
    Gera cores de preenchimento e borda baseadas em valores (profit/loss).
    
    Args:
        values: Lista de valores numéricos
    
    Returns:
        Tuple de (cores_preenchimento, cores_borda)
        - Verde para valores >= 0
        - Vermelho para valores < 0
    """
    colors_fill = []
    colors_border = []
    
    for val in values:
        if val >= 0:
            colors_fill.append('#34C759')  # Verde mais claro (preenchimento)
            colors_border.append('#28A745')  # Verde mais escuro (borda)
        else:
            colors_fill.append('#FF3B30')  # Vermelho mais claro (preenchimento)
            colors_border.append('#DC3545')  # Vermelho mais escuro (borda)
    
    return colors_fill, colors_border


def apply_default_plotly_layout(
    fig: go.Figure,
    title: str,
    xaxis_title: str = None,
    yaxis_title: str = None,
    height: int = 500,
    showlegend: bool = False,
    margin: Dict = None
) -> go.Figure:
    """
    Aplica configuração padrão de layout para gráficos Plotly.
    
    Args:
        fig: Figura Plotly
        title: Título do gráfico
        xaxis_title: Título do eixo X (opcional)
        yaxis_title: Título do eixo Y (opcional)
        height: Altura do gráfico (padrão: 500)
        showlegend: Mostrar legenda (padrão: False)
        margin: Margens customizadas (opcional)
    
    Returns:
        Figura Plotly atualizada
    """
    if margin is None:
        margin = dict(t=60, b=60, l=80, r=40)
    
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=18, family=FONT_FAMILY, color='#FFFFFF', weight=600)
        ),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
        plot_bgcolor='rgba(0,0,0,0)',  # Fundo do gráfico transparente
        font=dict(family=FONT_FAMILY, size=13, color=COLOR_TEXT_SECONDARY),
        height=height,
        showlegend=showlegend,
        margin=margin
    )
    
    return fig


def apply_default_axes(
    fig: go.Figure,
    x_showgrid: bool = False,
    y_showgrid: bool = True,
    gridcolor: str = 'rgba(255, 255, 255, 0.1)',
    y_layer: str = 'below traces'
) -> go.Figure:
    """
    Aplica configuração padrão de eixos para gráficos Plotly.
    
    Args:
        fig: Figura Plotly
        x_showgrid: Mostrar grade no eixo X (padrão: False)
        y_showgrid: Mostrar grade no eixo Y (padrão: True)
        gridcolor: Cor das linhas de grade
        y_layer: Camada das linhas de grade do eixo Y
    
    Returns:
        Figura Plotly atualizada
    """
    fig.update_xaxes(
        showgrid=x_showgrid,
        zerolinecolor=COLOR_SEPARATOR,
        title_font=dict(color='#FFFFFF', size=13),
        tickfont=dict(color='#FFFFFF', size=12)
    )
    
    fig.update_yaxes(
        showgrid=y_showgrid,
        gridcolor=gridcolor,
        gridwidth=1,
        layer=y_layer,
        zeroline=True,
        zerolinecolor=COLOR_SEPARATOR,
        zerolinewidth=2,
        title_font=dict(color='#FFFFFF', size=13),
        tickfont=dict(color='#FFFFFF', size=12)
    )
    
    return fig


def create_area_chart(
    x_data: List,
    y_data: List,
    title: str,
    area_color: str,
    hover_template: str = None,
    xaxis_title: str = 'Date',
    yaxis_title: str = 'Cumulative Profit'
) -> go.Figure:
    """
    Cria gráfico de área com duas camadas (opaca + transparente).
    
    Args:
        x_data: Dados do eixo X
        y_data: Dados do eixo Y
        title: Título do gráfico
        area_color: Cor da área (será convertida para rgba)
        hover_template: Template de hover (opcional)
        xaxis_title: Título do eixo X
        yaxis_title: Título do eixo Y
    
    Returns:
        Figura Plotly configurada
    """
    if hover_template is None:
        hover_template = '<b>%{x}</b><br><b>Lucro Acumulado:</b> $%{y:,.2f}<extra></extra>'
    
    fig = go.Figure()
    
    # Primeira camada: área opaca para bloquear linhas de grade
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines',
        fill='tozeroy',
        fillcolor=COLOR_CONTENT_BG,
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Segunda camada: área transparente para efeito visual
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines',
        fill='tozeroy',
        fillcolor=hex_to_rgba(area_color, 0.3),
        line=dict(
            color=area_color,
            width=3
        ),
        name='Lucro Acumulado',
        hovertemplate=hover_template
    ))
    
    # Aplicar configurações padrão
    apply_default_plotly_layout(fig, title, xaxis_title, yaxis_title)
    apply_default_axes(fig)
    
    return fig


def prepare_chart_data_by_period(df_daily: pd.DataFrame) -> Dict[str, Dict[str, List]]:
    """
    Prepara dados de gráfico para diferentes períodos.
    
    Args:
        df_daily: DataFrame com dados diários (deve ter colunas 'date' e 'profit')
    
    Returns:
        Dicionário com dados por período:
        {
            'all': {'x': [...], 'y': [...]},
            'year': {'x': [...], 'y': [...]},
            '6months': {'x': [...], 'y': [...]},
            'month': {'x': [...], 'y': [...]},
            '15days': {'x': [...], 'y': [...]},
            '7days': {'x': [...], 'y': [...]}
        }
    """
    # Filtrar apenas dias com profit != 0 e ordenar por data
    daily_filtered = df_daily[df_daily['profit'] != 0].sort_values('date').copy()
    
    # Calcular lucro acumulado
    daily_filtered['cumulative_profit'] = daily_filtered['profit'].cumsum()
    
    # Inicializar resultado
    chart_data_by_period = {
        'all': {'x': [], 'y': []},
        'year': {'x': [], 'y': []},
        '6months': {'x': [], 'y': []},
        'month': {'x': [], 'y': []},
        '15days': {'x': [], 'y': []},
        '7days': {'x': [], 'y': []}
    }
    
    if daily_filtered.empty:
        return chart_data_by_period
    
    # Converter datas para datetime se necessário
    daily_filtered['date_obj'] = pd.to_datetime(daily_filtered['date'])
    today = daily_filtered['date_obj'].max()
    
    # Total (todos os dados)
    total_data = daily_filtered.copy()
    chart_data_by_period['all'] = {
        'x': total_data['date'].astype(str).tolist(),
        'y': total_data['cumulative_profit'].tolist()
    }
    
    # Último ano
    one_year_ago = today - timedelta(days=365)
    year_data = daily_filtered[daily_filtered['date_obj'] >= one_year_ago].copy()
    if not year_data.empty:
        year_data['cumulative_profit'] = year_data['profit'].cumsum()
        chart_data_by_period['year'] = {
            'x': year_data['date'].astype(str).tolist(),
            'y': year_data['cumulative_profit'].tolist()
        }
    
    # Últimos 6 meses
    six_months_ago = today - timedelta(days=180)
    six_months_data = daily_filtered[daily_filtered['date_obj'] >= six_months_ago].copy()
    if not six_months_data.empty:
        six_months_data['cumulative_profit'] = six_months_data['profit'].cumsum()
        chart_data_by_period['6months'] = {
            'x': six_months_data['date'].astype(str).tolist(),
            'y': six_months_data['cumulative_profit'].tolist()
        }
    
    # Último mês
    one_month_ago = today - timedelta(days=30)
    month_data = daily_filtered[daily_filtered['date_obj'] >= one_month_ago].copy()
    if not month_data.empty:
        month_data['cumulative_profit'] = month_data['profit'].cumsum()
        chart_data_by_period['month'] = {
            'x': month_data['date'].astype(str).tolist(),
            'y': month_data['cumulative_profit'].tolist()
        }
    
    # Últimos 15 dias
    fifteen_days_ago = today - timedelta(days=15)
    fifteen_data = daily_filtered[daily_filtered['date_obj'] >= fifteen_days_ago].copy()
    if not fifteen_data.empty:
        fifteen_data['cumulative_profit'] = fifteen_data['profit'].cumsum()
        chart_data_by_period['15days'] = {
            'x': fifteen_data['date'].astype(str).tolist(),
            'y': fifteen_data['cumulative_profit'].tolist()
        }
    
    # Últimos 7 dias
    seven_days_ago = today - timedelta(days=7)
    seven_data = daily_filtered[daily_filtered['date_obj'] >= seven_days_ago].copy()
    if not seven_data.empty:
        seven_data['cumulative_profit'] = seven_data['profit'].cumsum()
        chart_data_by_period['7days'] = {
            'x': seven_data['date'].astype(str).tolist(),
            'y': seven_data['cumulative_profit'].tolist()
        }
    
    return chart_data_by_period

