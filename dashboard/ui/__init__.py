"""
Módulos de UI (estilos CSS e templates JavaScript) para o dashboard.
"""
from .styles import (
    get_base_styles,
    get_table_styles,
    get_table_container_styles,
    get_scrollbar_styles,
    get_sortable_table_styles,
    get_chart_container_styles,
    get_dashboard_grid_styles,
    get_nav_links_styles,
    get_all_styles
)

from .js_templates import (
    get_sortable_table_js,
    get_format_currency_js,
    get_format_percentage_js,
    get_chart_update_animation_css,
    get_modal_styles,
    get_column_visibility_modal_js,
    get_plotly_chart_update_js,
    get_table_row_renderer_js,
    get_daily_table_renderer_js
)
from .table_templates import (
    create_html_table,
    create_table_row_html
)
from .page_templates import (
    create_page_html,
    create_page_section,
    create_dashboard_container
)

__all__ = [
    # Styles
    'get_base_styles',
    'get_table_styles',
    'get_table_container_styles',
    'get_scrollbar_styles',
    'get_sortable_table_styles',
    'get_chart_container_styles',
    'get_dashboard_grid_styles',
    'get_nav_links_styles',
    'get_all_styles',
    # JS Templates
    'get_sortable_table_js',
    'get_format_currency_js',
    'get_format_percentage_js',
    'get_chart_update_animation_css',
    'get_modal_styles',
    'get_column_visibility_modal_js',
    'get_plotly_chart_update_js',
    'get_table_row_renderer_js',
    'get_daily_table_renderer_js',
    # Table Templates
    'create_html_table',
    'create_table_row_html',
    # Page Templates
    'create_page_html',
    'create_page_section',
    'create_dashboard_container'
]

