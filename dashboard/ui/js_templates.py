"""
Templates JavaScript reutilizáveis para o dashboard.
Centraliza código JavaScript comum para evitar duplicação.
"""
from typing import Optional
from dashboard.constants import *


def get_sortable_table_js(
    data_variable: str,
    table_id: str,
    body_id: str,
    initial_sort: dict = None,
    render_row_callback: str = None
) -> str:
    """
    Gera código JavaScript para tabelas ordenáveis.
    
    Args:
        data_variable: Nome da variável JavaScript com os dados (ex: 'tagsData')
        table_id: ID da tabela HTML
        body_id: ID do tbody da tabela
        initial_sort: Dict com 'column' e 'direction' para ordenação inicial
        render_row_callback: Função JavaScript customizada para renderizar linhas.
                             Deve ser uma string com código JavaScript que define renderRow().
                             Se None, usa renderização padrão.
    
    Returns:
        String com código JavaScript completo
    """
    if initial_sort is None:
        initial_sort = {'column': 'profit', 'direction': 'desc'}
    
    if render_row_callback is None:
        # Renderização padrão (precisa ser customizada por contexto)
        render_row_callback = '''
        function renderRow(row, index) {
            const profitClass = row.profit >= 0 ? 'profit' : 'loss';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${row.tag || row.date || 'N/A'}</td>
                <td class="text-right ${profitClass}">$${(row.profit || 0).toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
            `;
            return tr;
        }
        '''
    
    return f'''
    <script>
        // Verificar se a variável já existe (deve ter sido definida antes)
        if (typeof {data_variable} === 'undefined') {{
            console.error('Variável {data_variable} não foi definida. Certifique-se de definir antes de chamar get_sortable_table_js.');
            // Tentar esperar um pouco e verificar novamente (para scripts assíncronos)
            setTimeout(function() {{
                if (typeof {data_variable} !== 'undefined') {{
                    initSortableTable();
                }} else {{
                    console.error('Variável {data_variable} ainda não está disponível após espera.');
                }}
            }}, 100);
        }} else {{
            initSortableTable();
        }}
        
        function initSortableTable() {{
            let currentSort = {{ column: '{initial_sort['column']}', direction: '{initial_sort['direction']}' }};
            let sortedData = [];
            
            // Definir função de renderização de linha
            {render_row_callback}
            
            function renderTable(data) {{
                const tbody = document.getElementById('{body_id}');
                if (!tbody) {{
                    console.error('Elemento {body_id} não encontrado');
                    return;
                }}
                tbody.innerHTML = '';
                
                if (!data || data.length === 0) {{
                    console.warn('Nenhum dado para renderizar');
                    return;
                }}
                
                data.forEach((row, index) => {{
                    const tr = renderRow(row, index);
                    tbody.appendChild(tr);
                }});
            }}
            
            function sortTable(column, type) {{
                const direction = currentSort.column === column && currentSort.direction === 'asc' ? 'desc' : 'asc';
                currentSort = {{ column, direction }};
                
                if (typeof {data_variable} === 'undefined') {{
                    console.error('Variável {data_variable} não disponível para ordenação');
                    return;
                }}
                
                sortedData = [...{data_variable}].sort((a, b) => {{
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
            
            // Renderizar inicialmente
            if (typeof {data_variable} !== 'undefined' && {data_variable}.length > 0) {{
                sortedData = {data_variable}.sort((a, b) => {{
                    const aVal = a['{initial_sort['column']}'];
                    const bVal = b['{initial_sort['column']}'];
                    return '{initial_sort['direction']}' === 'asc' ? 
                        (aVal > bVal ? 1 : aVal < bVal ? -1 : 0) :
                        (aVal < bVal ? 1 : aVal > bVal ? -1 : 0);
                }});
                renderTable(sortedData);
                updateSortArrows('{initial_sort['column']}', '{initial_sort['direction']}');
            }} else {{
                console.warn('Nenhum dado disponível para renderização inicial');
            }}
        }}
    </script>
    '''


def get_format_currency_js() -> str:
    """Retorna função JavaScript para formatação de moeda."""
    return '''
    function formatCurrency(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '$0.00';
        }
        return '$' + value.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    '''


def get_format_percentage_js() -> str:
    """Retorna função JavaScript para formatação de porcentagem."""
    return '''
    function formatPercentage(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '0.00%';
        }
        return (value * 100).toFixed(2) + '%';
    }
    '''


def get_chart_update_animation_css() -> str:
    """Retorna CSS para animação de atualização de gráficos."""
    return '''
    <style>
        .chart-container {
            transition: opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .chart-container.updating {
            opacity: 0.75;
            transform: scale(0.985);
        }
        .chart-container .plotly {
            transition: opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .chart-container.updating .plotly {
            opacity: 0.85;
        }
    </style>
    '''


def get_modal_styles() -> str:
    """Retorna estilos CSS para modais."""
    return f'''
    <style>
        .modal {{
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
        .modal.active {{
            display: flex;
        }}
        .modal-content {{
            background-color: {COLOR_CONTENT_BG};
            border: 1px solid {COLOR_SEPARATOR};
            border-radius: 12px;
            padding: 30px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            color: #FFFFFF;
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid {COLOR_SEPARATOR};
        }}
        .modal-header h3 {{
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
    </style>
    '''

def get_column_visibility_modal_js(modal_id: str = 'column-modal') -> str:
    """
    Gera JavaScript completo para modal de visibilidade de colunas.
    
    Args:
        modal_id: ID do modal (padrão: 'column-modal')
    
    Returns:
        String com código JavaScript completo
    """
    return f'''
    <script>
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
                    const modal = document.getElementById('{modal_id}');
                    if (modal) {{
                        modal.classList.add('active');
                    }}
                }});
            }}
            
            // Fechar modal
            const closeBtn = document.getElementById('close-modal-btn');
            if (closeBtn) {{
                closeBtn.addEventListener('click', function() {{
                    const modal = document.getElementById('{modal_id}');
                    if (modal) {{
                        modal.classList.remove('active');
                    }}
                }});
            }}
            
            // Fechar modal ao clicar fora
            const modal = document.getElementById('{modal_id}');
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
                    const modal = document.getElementById('{modal_id}');
                    if (modal) {{
                        modal.classList.remove('active');
                    }}
                }});
            }}
        }});
    </script>
    '''

def get_plotly_chart_update_js(
    chart_id: str,
    data_variable: str,
    update_function_name: str = 'updateChart'
) -> str:
    """
    Gera JavaScript para atualização dinâmica de gráficos Plotly.
    
    Args:
        chart_id: ID do elemento do gráfico (ex: 'tags-chart')
        data_variable: Nome da variável JavaScript com os dados
        update_function_name: Nome da função de atualização (padrão: 'updateChart')
    
    Returns:
        String com código JavaScript base para atualização
    """
    return f'''
    <script>
        // Função auxiliar para encontrar elemento do gráfico
        function findChartElement(chartId) {{
            let chartDiv = document.getElementById(chartId);
            
            // Se não encontrou pelo ID, procurar dentro do container
            if (!chartDiv) {{
                const container = document.getElementById(chartId + '-container');
                if (container) {{
                    chartDiv = container.querySelector('#' + chartId);
                }}
            }}
            
            // Se ainda não encontrou, procurar qualquer elemento plotly
            if (!chartDiv) {{
                const container = document.getElementById(chartId + '-container');
                if (container) {{
                    chartDiv = container.querySelector('.js-plotly-plot') || container.querySelector('[id*="plotly"]');
                }}
            }}
            
            // Se ainda não encontrou, criar novo elemento
            if (!chartDiv) {{
                const container = document.getElementById(chartId + '-container');
                if (container) {{
                    chartDiv = document.createElement('div');
                    chartDiv.id = chartId;
                    container.innerHTML = '';
                    container.appendChild(chartDiv);
                }}
            }}
            
            return chartDiv;
        }}
        
        // Verificar se Plotly está disponível
        function waitForPlotly(callback) {{
            if (typeof Plotly !== 'undefined') {{
                callback();
            }} else {{
                console.error('Plotly não está disponível. Aguardando...');
                setTimeout(function() {{
                    if (typeof Plotly !== 'undefined') {{
                        callback();
                    }} else {{
                        console.error('Plotly ainda não carregou após espera');
                    }}
                }}, 100);
            }}
        }}
        
        // Função genérica para atualizar gráfico Plotly
        function {update_function_name}(data, layout, config) {{
            waitForPlotly(function() {{
                const chartDiv = findChartElement('{chart_id}');
                if (!chartDiv) {{
                    console.error('Elemento do gráfico não encontrado');
                    return;
                }}
                
                // Verificar se já existe um gráfico Plotly neste elemento
                const hasExistingPlot = chartDiv.querySelector && chartDiv.querySelector('.plotly');
                
                const defaultConfig = {{
                    displayModeBar: false,
                    responsive: true
                }};
                const finalConfig = config || defaultConfig;
                
                // Usar Plotly.react se já existe gráfico, senão Plotly.newPlot
                if (hasExistingPlot) {{
                    Plotly.react(chartDiv, data, layout, finalConfig)
                        .then(function() {{
                            console.log('Gráfico atualizado com sucesso');
                        }})
                        .catch(function(err) {{
                            console.error('Erro ao atualizar gráfico:', err);
                        }});
                }} else {{
                    Plotly.newPlot(chartDiv, data, layout, finalConfig)
                        .then(function() {{
                            console.log('Gráfico criado com sucesso');
                        }})
                        .catch(function(err) {{
                            console.error('Erro ao criar gráfico:', err);
                        }});
                }}
            }});
        }}
        
        // Tornar função disponível globalmente
        window.{update_function_name} = {update_function_name};
    </script>
    '''


def get_table_row_renderer_js(
    column_configs: list,
    table_id: Optional[str] = None
) -> str:
    """
    Gera JavaScript para renderizar linhas de tabela de forma genérica.
    
    Args:
        column_configs: Lista de dicionários com configuração de cada coluna:
            - 'field': Nome do campo no objeto row
            - 'format': 'currency', 'percentage', 'integer', 'date', ou None
            - 'class': Classe CSS adicional
            - 'profit_loss': True se deve aplicar classes profit/loss
            - 'alignment': 'left', 'right', 'center'
            - 'link': Função JS que retorna URL (opcional)
        table_id: ID da tabela (opcional)
        
    Returns:
        String com função JavaScript renderRow()
    """
    render_code = '''
    function renderRow(row, index) {
        const tr = document.createElement('tr');
        let html = '';
    '''
    
    for i, config in enumerate(column_configs):
        field = config.get('field', f'col{i}')
        format_type = config.get('format')
        profit_loss = config.get('profit_loss', False)
        alignment = config.get('alignment', 'left')
        link_func = config.get('link')
        extra_class = config.get('class', '')
        
        # Determinar classes
        classes = []
        if alignment != 'left':
            classes.append(alignment)
        if extra_class:
            classes.append(extra_class)
        
        # Formatação
        value_code = f'row.{field}'
        if format_type == 'currency':
            value_code = f"formatCurrency({value_code})"
        elif format_type == 'percentage':
            value_code = f"formatPercentage({value_code})"
        elif format_type == 'integer':
            value_code = f"{value_code}.toLocaleString('en-US', {{maximumFractionDigits: 0}})"
        
        # Classe profit/loss
        if profit_loss:
            classes.append(f"`${{row.{field} >= 0 ? 'profit' : 'loss'}}`")
        
        class_attr = ' class="' + ' '.join(classes).replace('`', '').replace('${', '').replace('}', '') + '"' if classes else ''
        
        # Link
        if link_func:
            render_code += f'''
        const linkUrl = {link_func}(row);
        html += `<td{class_attr}><a href="${{linkUrl}}" style="color: {COLOR_ACCENT};">${{{value_code}}}</a></td>`;
            '''
        else:
            render_code += f'''
        html += `<td{class_attr}>${{{value_code}}}</td>`;
            '''
    
    render_code += '''
        tr.innerHTML = html;
        return tr;
    }
    '''
    
    return render_code


def get_daily_table_renderer_js() -> str:
    """Retorna função JavaScript para renderizar tabela diária."""
    return f'''
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
        if (typeof updateTotals === 'function') {{
            updateTotals(data);
        }}
    }}
    '''

