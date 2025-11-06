"""
Templates reutilizáveis para criação de páginas HTML completas.
"""
from typing import Optional
from dashboard.constants import COLOR_BLACK


def create_page_html(
    title: str,
    content: str,
    styles: Optional[str] = None,
    scripts: Optional[str] = None,
    body_class: Optional[str] = None,
    lang: str = "pt-BR",
    additional_head: Optional[str] = None
) -> str:
    """
    Cria uma página HTML completa com estrutura padrão.
    
    Args:
        title: Título da página
        content: Conteúdo HTML do body
        styles: CSS adicional (opcional)
        scripts: JavaScript adicional (opcional)
        body_class: Classe CSS do body (opcional)
        lang: Idioma da página (padrão: 'pt-BR')
        additional_head: HTML adicional para o head (opcional)
        
    Returns:
        String com HTML completo da página
    """
    body_attr = f' class="{body_class}"' if body_class else ''
    
    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {styles if styles else ''}
    {additional_head if additional_head else ''}
</head>
<body{body_attr}>
    {content}
    {scripts if scripts else ''}
</body>
</html>'''
    
    return html


def create_page_section(
    title: str,
    content: str,
    section_class: Optional[str] = None
) -> str:
    """
    Cria uma seção de página com título e conteúdo.
    
    Args:
        title: Título da seção
        content: Conteúdo HTML da seção
        section_class: Classe CSS da seção (opcional)
        
    Returns:
        String com HTML da seção
    """
    class_attr = f' class="{section_class}"' if section_class else ''
    
    return f'''
    <div{class_attr}>
        <h3>{title}</h3>
        {content}
    </div>
    '''


def create_dashboard_container(
    content: str,
    container_class: str = "dashboard-container"
) -> str:
    """
    Cria um container de dashboard.
    
    Args:
        content: Conteúdo HTML
        container_class: Classe CSS do container
        
    Returns:
        String com HTML do container
    """
    return f'''
    <div class="{container_class}">
        {content}
    </div>
    '''

