"""
Templates reutilizáveis para criação de tabelas HTML.
"""
from typing import List, Optional, Callable, Any, Dict
from dashboard.constants import COLOR_ACCENT
from dashboard.utils.formatters import get_profit_loss_class


def create_html_table(
    headers: List[str],
    rows: List[List[Any]],
    column_formatters: Optional[List[Callable]] = None,
    profit_loss_columns: Optional[List[int]] = None,
    column_classes: Optional[List[str]] = None,
    column_alignments: Optional[List[str]] = None,
    table_class: str = "dashboard-table",
    sortable: bool = False,
    sortable_columns: Optional[List[int]] = None,
    table_id: Optional[str] = None,
    body_id: Optional[str] = None
) -> str:
    """
    Cria uma tabela HTML genérica.
    
    Args:
        headers: Lista de nomes das colunas
        rows: Lista de listas, onde cada lista é uma linha de dados
        column_formatters: Lista opcional de funções para formatar cada coluna
        profit_loss_columns: Índices das colunas que devem ter classes profit/loss
        column_classes: Lista opcional de classes CSS para cada coluna
        column_alignments: Lista opcional de alinhamentos ('left', 'right', 'center')
        table_class: Classe CSS da tabela (padrão: 'dashboard-table')
        sortable: Se True, adiciona classes sortable
        sortable_columns: Índices das colunas ordenáveis (se sortable=True)
        table_id: ID opcional da tabela
        body_id: ID opcional do tbody
        
    Returns:
        String HTML da tabela
    """
    # Valores padrão
    if column_alignments is None:
        column_alignments = ['left'] * len(headers)
    
    if column_classes is None:
        column_classes = [''] * len(headers)
    
    # Criar cabeçalho
    id_attr = f' id="{table_id}"' if table_id else ''
    html = f'<table class="{table_class}"{id_attr}><thead><tr>'
    
    for i, header in enumerate(headers):
        alignment = column_alignments[i] if i < len(column_alignments) else 'left'
        
        # Construir classes do header corretamente
        header_classes = []
        if alignment != 'left':
            header_classes.append(alignment)
        if sortable and (sortable_columns is None or i in sortable_columns):
            header_classes.append('sortable')
        
        header_attrs = []
        if header_classes:
            header_attrs.append(f'class="{" ".join(header_classes)}"')
        if sortable and (sortable_columns is None or i in sortable_columns):
            header_attrs.append(f'data-sort="{header.lower().replace(" ", "_")}"')
            header_attrs.append(f'data-sort-type="{"number" if alignment == "right" else "string"}"')
        
        header_attr_str = ' ' + ' '.join(header_attrs) if header_attrs else ''
        html += f'<th{header_attr_str}>{header}'
        if sortable and (sortable_columns is None or i in sortable_columns):
            html += ' <span class="sort-arrow">↕</span>'
        html += '</th>'
    
    html += '</tr></thead>'
    
    # Criar corpo
    body_id_attr = f' id="{body_id}"' if body_id else ''
    html += f'<tbody{body_id_attr}>'
    
    # Formatar e adicionar linhas
    for row in rows:
        html += '<tr>'
        for i, cell_value in enumerate(row):
            alignment = column_alignments[i] if i < len(column_alignments) else 'left'
            cell_class = column_classes[i] if i < len(column_classes) else ''
            
            # Determinar classe profit/loss ANTES de formatar (precisa do valor bruto)
            if profit_loss_columns and i in profit_loss_columns:
                # Extrair valor escalar se for Series
                raw_value = cell_value
                if hasattr(raw_value, 'item'):
                    try:
                        raw_value = raw_value.item()
                    except (ValueError, AttributeError):
                        pass
                elif hasattr(raw_value, 'iloc'):
                    raw_value = raw_value.iloc[0] if len(raw_value) > 0 else 0
                
                if isinstance(raw_value, (int, float)):
                    profit_loss_class = get_profit_loss_class(raw_value)
                    if cell_class:
                        cell_class += f' {profit_loss_class}'
                    else:
                        cell_class = profit_loss_class
            
            # Aplicar formatação se disponível (DEPOIS de verificar profit/loss)
            if column_formatters and i < len(column_formatters) and column_formatters[i]:
                # Extrair valor escalar se for Series antes de formatar
                if hasattr(cell_value, 'item'):
                    try:
                        cell_value = cell_value.item()
                    except (ValueError, AttributeError):
                        pass
                elif hasattr(cell_value, 'iloc'):
                    cell_value = cell_value.iloc[0] if len(cell_value) > 0 else cell_value
                
                cell_value = column_formatters[i](cell_value)
            
            # Construir atributo class corretamente
            if alignment != 'left' or cell_class:
                classes = []
                if alignment != 'left':
                    classes.append(alignment)
                if cell_class:
                    classes.append(cell_class)
                class_attr = f' class="{" ".join(classes).strip()}"'
            else:
                class_attr = ''
            
            html += f'<td{class_attr}>{cell_value}</td>'
        
        html += '</tr>'
    
    html += '</tbody></table>'
    
    return html


def create_table_row_html(
    values: List[Any],
    column_formatters: Optional[List[Callable]] = None,
    profit_loss_columns: Optional[List[int]] = None,
    column_alignments: Optional[List[str]] = None,
    column_classes: Optional[List[str]] = None
) -> str:
    """
    Cria uma linha HTML de tabela.
    
    Args:
        values: Valores da linha
        column_formatters: Formatadores para cada coluna
        profit_loss_columns: Índices das colunas profit/loss
        column_alignments: Alinhamentos das colunas
        column_classes: Classes CSS das colunas
        
    Returns:
        String HTML da linha (<tr>...</tr>)
    """
    if column_alignments is None:
        column_alignments = ['left'] * len(values)
    
    if column_classes is None:
        column_classes = [''] * len(values)
    
    html = '<tr>'
    
    for i, value in enumerate(values):
        alignment = column_alignments[i] if i < len(column_alignments) else 'left'
        cell_class = column_classes[i] if i < len(column_classes) else ''
        
        # Aplicar formatação
        if column_formatters and i < len(column_formatters) and column_formatters[i]:
            value = column_formatters[i](value)
        
        # Determinar classe profit/loss
        if profit_loss_columns and i in profit_loss_columns:
            if isinstance(value, (int, float)):
                profit_loss_class = get_profit_loss_class(value)
                if cell_class:
                    cell_class += f' {profit_loss_class}'
                else:
                    cell_class = profit_loss_class
        
        # Construir atributo class corretamente
        if alignment != 'left' or cell_class:
            classes = []
            if alignment != 'left':
                classes.append(alignment)
            if cell_class:
                classes.append(cell_class)
            class_attr = f' class="{" ".join(classes).strip()}"'
        else:
            class_attr = ''
        
        html += f'<td{class_attr}>{value}</td>'
    
    html += '</tr>'
    
    return html

