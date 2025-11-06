"""
Módulos para criação e configuração de gráficos Plotly.
"""
from .plotly_helpers import (
    hex_to_rgba,
    get_profit_loss_colors,
    apply_default_plotly_layout,
    apply_default_axes,
    create_area_chart,
    prepare_chart_data_by_period
)
from .table_templates import (
    create_plotly_table,
    create_kpi_table_plotly,
    create_profit_loss_table_plotly
)

__all__ = [
    'hex_to_rgba',
    'get_profit_loss_colors',
    'apply_default_plotly_layout',
    'apply_default_axes',
    'create_area_chart',
    'prepare_chart_data_by_period',
    'create_plotly_table',
    'create_kpi_table_plotly',
    'create_profit_loss_table_plotly'
]

