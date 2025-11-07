"""
Sistema de carregamento de templates (HTML, CSS, JS).
Permite carregar arquivos de template e fazer substituições de variáveis.
"""
import os
from pathlib import Path
from typing import Dict, Optional
from dashboard.constants import COLOR_ACCENT


def get_template_path(relative_path: str) -> Path:
    """Retorna o caminho absoluto para um template."""
    base_dir = Path(__file__).parent
    return base_dir / relative_path


def load_template(template_name: str, template_type: str = 'html') -> str:
    """
    Carrega um arquivo de template.
    
    Args:
        template_name: Nome do template (sem extensão)
        template_type: Tipo do template ('html', 'css', 'js')
    
    Returns:
        Conteúdo do arquivo como string
    """
    template_path = get_template_path(f'{template_type}/{template_name}.{template_type}')
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template_content: str, **kwargs) -> str:
    """
    Renderiza um template com substituições de variáveis.
    Usa formato {{variable}} para substituições.
    
    Args:
        template_content: Conteúdo do template
        **kwargs: Variáveis para substituição
    
    Returns:
        Template renderizado
    """
    result = template_content
    
    # Substituir variáveis no formato {{variable}}
    for key, value in kwargs.items():
        placeholder = f'{{{{{key}}}}}'
        result = result.replace(placeholder, str(value))
    
    return result


def load_css(css_name: str) -> str:
    """Carrega um arquivo CSS e retorna como tag <style>."""
    css_content = load_template(css_name, 'css')
    return f'<style>\n{css_content}\n</style>'


def load_js(js_name: str, **kwargs) -> str:
    """
    Carrega um arquivo JavaScript e renderiza com variáveis.
    Retorna como tag <script>.
    """
    js_content = load_template(js_name, 'js')
    js_content = render_template(js_content, **kwargs)
    return f'<script>\n{js_content}\n</script>'


def load_html(html_name: str, **kwargs) -> str:
    """Carrega um arquivo HTML e renderiza com variáveis."""
    html_content = load_template(html_name, 'html')
    return render_template(html_content, **kwargs)


def create_page_html(
    title: str,
    content: str,
    css_files: Optional[list] = None,
    js_files: Optional[Dict[str, Dict]] = None,
    additional_head: Optional[str] = None
) -> str:
    """
    Cria uma página HTML completa usando templates.
    
    Args:
        title: Título da página
        content: Conteúdo HTML do body
        css_files: Lista de nomes de arquivos CSS (sem extensão)
        js_files: Dict com {nome_arquivo: {vars}} para JS com variáveis
        additional_head: HTML adicional para o head
    
    Returns:
        HTML completo da página
    """
    styles = ''
    if css_files:
        for css_file in css_files:
            styles += load_css(css_file) + '\n'
    
    scripts = ''
    if js_files:
        for js_file, js_vars in js_files.items():
            scripts += load_js(js_file, **js_vars) + '\n'
    
    return render_template(
        load_template('base', 'html'),
        title=title,
        content=content,
        styles=styles,
        scripts=scripts,
        additional_head=additional_head or ''
    )



