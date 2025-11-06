# Sistema de Templates

Este diretório contém os templates HTML, CSS e JavaScript separados do código Python para facilitar a manutenção e reutilização.

## Estrutura

```
templates/
├── html/          # Templates HTML
├── css/           # Arquivos CSS
├── js/            # Arquivos JavaScript
└── loader.py      # Sistema de carregamento de templates
```

## Como usar

### Carregando templates

```python
from dashboard.templates.loader import load_html, load_css, create_page_html

# Carregar HTML com variáveis
content = load_html('main_page', 
    variable1=value1,
    variable2=value2
)

# Criar página completa
html = create_page_html(
    title='My Page',
    content=content,
    css_files=['main_page'],  # Carrega main_page.css
    js_files=None,
    additional_head='<meta...>'
)
```

### Formato de variáveis

Nos templates HTML, use `{{variable}}` para substituições:
```html
<h1>{{title}}</h1>
<div>{{content}}</div>
```

## Vantagens

1. **Separação de responsabilidades**: HTML, CSS e JS em arquivos próprios
2. **Manutenção facilitada**: Editar CSS/JS sem mexer no Python
3. **Reutilização**: Templates podem ser compartilhados entre páginas
4. **Syntax highlighting**: IDEs reconhecem HTML/CSS/JS nativos
5. **Versionamento**: Mudanças em templates são mais fáceis de rastrear

## Migração

Para migrar uma página existente:

1. Extrair CSS para `templates/css/nome_pagina.css`
2. Extrair JS para `templates/js/nome_pagina.js`
3. Extrair HTML para `templates/html/nome_pagina.html`
4. Atualizar função Python para usar `load_html()` e `create_page_html()`

