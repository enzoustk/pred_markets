"""
Estilos CSS reutilizáveis para o dashboard.
Centraliza todos os estilos CSS para evitar duplicação.
"""
from dashboard.constants import *


def get_base_styles() -> str:
    """Retorna estilos CSS base para o body e containers principais."""
    return f'''
    body {{
        background-color: {COLOR_BLACK};
        color: #FFFFFF;
        font-family: {FONT_FAMILY};
        margin: 0;
        padding: 20px;
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
    '''


def get_table_styles(table_class: str = 'dashboard-table') -> str:
    """
    Retorna estilos CSS para tabelas.
    
    Args:
        table_class: Nome da classe CSS para a tabela (padrão: 'dashboard-table')
    """
    return f'''
    .{table_class} {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        color: #FFFFFF;
        background-color: {COLOR_CONTENT_BG};
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {COLOR_SEPARATOR};
    }}
    .{table_class} thead {{
        background-color: {COLOR_BLACK};
        position: sticky;
        top: 0;
        z-index: 10;
    }}
    .{table_class} th {{
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
    .{table_class} th.text-right {{
        text-align: right;
    }}
    .{table_class} th:last-child {{
        border-right: none;
    }}
    .{table_class} tbody tr {{
        background-color: {COLOR_CONTENT_BG};
        color: #FFFFFF;
        border-bottom: 1px solid {COLOR_SEPARATOR};
    }}
    .{table_class} tbody tr:nth-child(even) {{
        background-color: rgba(142, 142, 147, 0.05);
    }}
    .{table_class} tbody tr:hover {{
        background-color: rgba(10, 132, 255, 0.1);
    }}
    .{table_class} td {{
        padding: 10px 15px;
        border-right: 1px solid {COLOR_SEPARATOR};
        color: #FFFFFF;
        white-space: nowrap;
    }}
    .{table_class} td.text-right {{
        text-align: right;
    }}
    .{table_class} td:last-child {{
        border-right: none;
    }}
    .{table_class} .profit {{
        color: {COLOR_PROFIT} !important;
        font-weight: 500;
    }}
    .{table_class} .loss {{
        color: {COLOR_LOSS} !important;
        font-weight: 500;
    }}
    .{table_class} .neutral {{
        color: #FFFFFF;
    }}
    .{table_class} a {{
        color: {COLOR_ACCENT};
        text-decoration: none;
        font-weight: 500;
    }}
    .{table_class} a:hover {{
        text-decoration: underline;
    }}
    '''


def get_table_container_styles() -> str:
    """Retorna estilos CSS para containers de tabelas."""
    return f'''
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
    '''


def get_scrollbar_styles() -> str:
    """Retorna estilos CSS genéricos para scrollbars."""
    return f'''
    ::-webkit-scrollbar {{
        width: 12px;
        height: 12px;
    }}
    ::-webkit-scrollbar-track {{
        background: {COLOR_BLACK};
        border-radius: 6px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: {COLOR_SEPARATOR};
        border-radius: 6px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLOR_TEXT_SECONDARY};
    }}
    '''


def get_sortable_table_styles() -> str:
    """Retorna estilos CSS para tabelas ordenáveis."""
    return f'''
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
    '''


def get_chart_container_styles() -> str:
    """Retorna estilos CSS para containers de gráficos."""
    return f'''
    .chart-container {{
        background-color: {COLOR_CONTENT_BG};
        border-radius: 12px;
        padding: 20px;
        border: 1px solid {COLOR_SEPARATOR};
    }}
    .chart-section {{
        background-color: {COLOR_CONTENT_BG};
        border-radius: 12px;
        padding: 20px;
        border: 1px solid {COLOR_SEPARATOR};
        margin-bottom: 30px;
    }}
    .chart-section h3 {{
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 15px;
        margin-top: 0;
    }}
    '''


def get_dashboard_grid_styles() -> str:
    """Retorna estilos CSS para grid layout do dashboard."""
    return f'''
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
    '''


def get_nav_links_styles() -> str:
    """Retorna estilos CSS para links de navegação."""
    return f'''
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
    .nav-link {{
        color: {COLOR_TEXT_SECONDARY};
        text-decoration: none;
        font-size: 16px;
        margin-left: 20px;
    }}
    .nav-link:hover {{
        color: {COLOR_ACCENT};
    }}
    '''


def get_all_styles() -> str:
    """Retorna todos os estilos CSS combinados."""
    return f'''
    <style>
    {get_base_styles()}
    {get_table_styles()}
    {get_table_container_styles()}
    {get_scrollbar_styles()}
    {get_sortable_table_styles()}
    {get_chart_container_styles()}
    {get_dashboard_grid_styles()}
    {get_nav_links_styles()}
    </style>
    '''

