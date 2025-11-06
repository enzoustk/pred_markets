// Apostas Tag Page JavaScript - Table interactions (sorting, pagination, filtering, column resizing)
// Variables injected: totalRows

document.addEventListener('DOMContentLoaded', function() {
    // Variáveis de paginação
    let itemsPerPage = 50;
    let currentPage = 1;
    let totalRows = {{totalRows}};
    let allRows = Array.from(document.querySelectorAll('#trades-table tbody tr'));
    let filteredRows = allRows; // Inicialmente, todas as linhas estão visíveis
    let rows = allRows; // Linhas para ordenação
    let currentSort = { column: null, direction: 'asc' };
    let activeFilters = {}; // Armazenar filtros ativos
    
    // Calcular total de páginas baseado em linhas filtradas
    function getTotalPages() {
        return Math.ceil(filteredRows.length / itemsPerPage);
    }
    
    // Função para atualizar cores alternadas das linhas
    function updateRowColors() {
        const visibleRows = Array.from(document.querySelectorAll('#trades-table tbody tr:not(.hidden-row)'));
        visibleRows.forEach((row, index) => {
            // Remover classes anteriores
            row.classList.remove('even-row', 'odd-row');
            // Adicionar classe baseada no índice visível
            if (index % 2 === 0) {
                row.classList.add('even-row');
            } else {
                row.classList.add('odd-row');
            }
        });
    }
    
    // Função para atualizar a exibição da tabela baseada na página atual
    function updateTableDisplay() {
        // Primeiro, ocultar todas as linhas
        allRows.forEach(row => {
            row.classList.add('hidden-row');
        });
        
        // Depois, mostrar apenas as linhas filtradas na página atual
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, filteredRows.length);
        
        for (let i = startIndex; i < endIndex; i++) {
            if (filteredRows[i]) {
                filteredRows[i].classList.remove('hidden-row');
            }
        }
        
        // Atualizar cores alternadas
        updateRowColors();
        
        // Atualizar informações de paginação
        updatePaginationInfo();
    }
    
    // Função para atualizar informações de paginação
    function updatePaginationInfo() {
        const totalPages = getTotalPages();
        const startIndex = filteredRows.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
        const endIndex = Math.min(currentPage * itemsPerPage, filteredRows.length);
        
        // Atualizar texto da página
        const pageInfo = document.getElementById('page-info');
        if (pageInfo) {
            if (filteredRows.length > 0) {
                pageInfo.textContent = `Página ${currentPage} de ${totalPages} (${startIndex}-${endIndex} de ${filteredRows.length})`;
            } else {
                pageInfo.textContent = `Nenhum resultado encontrado`;
            }
        }
        
        // Atualizar botões de navegação
        const prevBtn = document.getElementById('prev-page-btn');
        const nextBtn = document.getElementById('next-page-btn');
        
        if (prevBtn) {
            prevBtn.disabled = currentPage <= 1 || filteredRows.length === 0;
        }
        if (nextBtn) {
            nextBtn.disabled = currentPage >= totalPages || filteredRows.length === 0;
        }
    }
    
    // Função para obter valor de célula para ordenação
    function getCellValue(row, columnIndex, sortType) {
        const cell = row.querySelectorAll('td')[columnIndex];
        if (!cell) return '';
        
        let text = cell.textContent.trim();
        
        if (sortType === 'number') {
            // Remover caracteres não numéricos exceto sinal negativo e ponto decimal
            text = text.replace(/[^0-9.-]/g, '');
            const num = parseFloat(text);
            return isNaN(num) ? 0 : num;
        } else {
            return text.toLowerCase();
        }
    }
    
    // Função para ordenar tabela
    function sortTable(columnIndex, sortType) {
        const direction = currentSort.column === columnIndex && currentSort.direction === 'asc' ? 'desc' : 'asc';
        currentSort = { column: columnIndex, direction: direction };
        
        // Ordenar todas as linhas (não apenas as filtradas)
        allRows.sort((a, b) => {
            const aVal = getCellValue(a, columnIndex, sortType);
            const bVal = getCellValue(b, columnIndex, sortType);
            
            if (sortType === 'number') {
                return direction === 'asc' ? aVal - bVal : bVal - aVal;
            } else {
                if (aVal < bVal) return direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return direction === 'asc' ? 1 : -1;
                return 0;
            }
        });
        
        // Reordenar no DOM
        const tbody = document.querySelector('#trades-table tbody');
        allRows.forEach(row => tbody.appendChild(row));
        
        // Reaplicar filtros se houver filtros ativos
        if (Object.keys(activeFilters).length > 0) {
            applyFilters();
        } else {
            // Se não houver filtros, atualizar filteredRows para refletir a nova ordem
            filteredRows = allRows;
        }
        
        // Resetar para primeira página após ordenação
        currentPage = 1;
        
        // Atualizar exibição da tabela
        updateTableDisplay();
        
        // Atualizar indicadores de ordenação
        document.querySelectorAll('#trades-table th.sortable').forEach((th, idx) => {
            const arrow = th.querySelector('.sort-arrow');
            if (arrow) {
                if (idx === columnIndex) {
                    arrow.textContent = direction === 'asc' ? ' ↑' : ' ↓';
                } else {
                    arrow.textContent = ' ↕';
                }
            }
        });
    }
    
    // Função para aplicar filtros
    function applyFilters() {
        activeFilters = {};
        
        // Obter valores dos filtros
        const filters = [
            { name: 'start_time', type: 'datetime' },
            { name: 'totalBought', type: 'number' },
            { name: 'avgPrice', type: 'number' },
            { name: 'realizedPnl', type: 'number' },
            { name: 'staked', type: 'number' },
            { name: 'total_profit', type: 'number' },
            { name: 'roi', type: 'number' }
        ];
        
        filters.forEach(filter => {
            const minInput = document.getElementById(`filter-${filter.name}-min`);
            const maxInput = document.getElementById(`filter-${filter.name}-max`);
            
            if (minInput && minInput.value) {
                activeFilters[filter.name] = activeFilters[filter.name] || {};
                activeFilters[filter.name].min = filter.type === 'datetime' ? new Date(minInput.value) : parseFloat(minInput.value);
            }
            if (maxInput && maxInput.value) {
                activeFilters[filter.name] = activeFilters[filter.name] || {};
                activeFilters[filter.name].max = filter.type === 'datetime' ? new Date(maxInput.value) : parseFloat(maxInput.value);
            }
        });
        
        // Filtrar linhas
        filteredRows = allRows.filter(row => {
            return Object.keys(activeFilters).every(filterName => {
                const filter = activeFilters[filterName];
                const cell = row.querySelector(`td[data-column="col_${filterName}"]`);
                
                if (!cell) return true; // Se não encontrar a célula, manter a linha
                
                let cellValue = cell.textContent.trim();
                
                // Para ROI, converter de percentual para decimal se necessário
                if (filterName === 'roi') {
                    cellValue = parseFloat(cellValue.replace('%', '').replace(/[,]/g, ''));
                    if (isNaN(cellValue)) return true;
                    cellValue = cellValue / 100; // Converter para decimal
                } else if (filterName === 'start_time') {
                    // Converter data para objeto Date
                    try {
                        // Formato esperado: DD/MM/YYYY HH:MM ou YYYY-MM-DD HH:MM:SS
                        const dateStr = cellValue;
                        let dateObj = null;
                        if (dateStr.includes('/')) {
                            // Formato DD/MM/YYYY HH:MM
                            const parts = dateStr.split(' ');
                            const dateParts = parts[0].split('/');
                            const timeParts = parts[1] ? parts[1].split(':') : ['00', '00'];
                            dateObj = new Date(
                                parseInt(dateParts[2]),
                                parseInt(dateParts[1]) - 1,
                                parseInt(dateParts[0]),
                                parseInt(timeParts[0]),
                                parseInt(timeParts[1])
                            );
                        } else {
                            dateObj = new Date(cellValue);
                        }
                        cellValue = dateObj;
                        if (isNaN(cellValue.getTime())) return true;
                    } catch (e) {
                        return true;
                    }
                } else {
                    // Para números, remover caracteres não numéricos (exceto sinal e ponto)
                    cellValue = parseFloat(cellValue.replace(/[^0-9.-]/g, ''));
                    if (isNaN(cellValue)) return true;
                }
                
                // Aplicar filtros
                if (filter.min !== undefined && cellValue < filter.min) return false;
                if (filter.max !== undefined && cellValue > filter.max) return false;
                
                return true;
            });
        });
        
        // Atualizar badge de filtros ativos
        const filterBadge = document.getElementById('filter-badge');
        const activeFilterCount = Object.keys(activeFilters).length;
        if (filterBadge) {
            if (activeFilterCount > 0) {
                filterBadge.textContent = activeFilterCount;
                filterBadge.style.display = 'inline-block';
            } else {
                filterBadge.style.display = 'none';
            }
        }
        
        // Resetar para primeira página
        currentPage = 1;
        
        // Atualizar exibição
        updateTableDisplay();
    }
    
    // Função para limpar filtros
    function clearFilters() {
        const filterInputs = document.querySelectorAll('#filter-modal input');
        filterInputs.forEach(input => input.value = '');
        activeFilters = {};
        
        // Atualizar badge
        const filterBadge = document.getElementById('filter-badge');
        if (filterBadge) {
            filterBadge.style.display = 'none';
        }
        
        // Restaurar todas as linhas
        filteredRows = allRows;
        
        // Resetar para primeira página
        currentPage = 1;
        
        // Atualizar exibição
        updateTableDisplay();
    }
    
    // Adicionar event listeners aos cabeçalhos (exceto no resize handle)
    document.querySelectorAll('#trades-table th.sortable').forEach((th, index) => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', function(e) {
            // Não ordenar se clicar no resize handle
            if (e.target.classList.contains('resize-handle') || e.target.closest('.resize-handle')) {
                return;
            }
            // Não ordenar se acabamos de fazer um resize
            if (justFinishedResizing) {
                justFinishedResizing = false;
                return;
            }
            const sortType = this.dataset.sortType || 'string';
            sortTable(index, sortType);
        });
    });
    
    // Event listeners para modal de filtros
    const filterModal = document.getElementById('filter-modal');
    const toggleFiltersBtn = document.getElementById('toggle-filters-btn');
    const closeFilterModalBtn = document.getElementById('close-filter-modal-btn');
    const applyFiltersBtn = document.getElementById('apply-filters-btn');
    const clearFiltersBtn = document.getElementById('clear-filters-btn');
    
    if (toggleFiltersBtn) {
        toggleFiltersBtn.addEventListener('click', function() {
            if (filterModal) {
                filterModal.classList.add('active');
            }
        });
    }
    
    if (closeFilterModalBtn) {
        closeFilterModalBtn.addEventListener('click', function() {
            if (filterModal) {
                filterModal.classList.remove('active');
            }
        });
    }
    
    if (filterModal) {
        filterModal.addEventListener('click', function(e) {
            if (e.target === filterModal) {
                filterModal.classList.remove('active');
            }
        });
    }
    
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            applyFilters();
            if (filterModal) {
                filterModal.classList.remove('active');
            }
        });
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            clearFilters();
        });
    }
    
    // Inicializar tabela
    updateTableDisplay();
    
    // Event listeners para paginação
    const itemsPerPageSelect = document.getElementById('items-per-page');
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', function() {
            itemsPerPage = parseInt(this.value);
            currentPage = 1; // Resetar para primeira página
            updateTableDisplay();
        });
    }
    
    const prevPageBtn = document.getElementById('prev-page-btn');
    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                updateTableDisplay();
            }
        });
    }
    
    const nextPageBtn = document.getElementById('next-page-btn');
    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', function() {
            const totalPages = getTotalPages();
            if (currentPage < totalPages) {
                currentPage++;
                updateTableDisplay();
            }
        });
    }
    
    // ===== FUNCIONALIDADE DE REDIMENSIONAMENTO DE COLUNAS =====
    let currentResizeColumn = null;
    let startX = 0;
    let startWidth = 0;
    let isResizing = false;
    let justFinishedResizing = false; // Flag para prevenir ordenação após resize
    
    // Função para calcular largura ideal de uma coluna baseada no conteúdo mais longo VISÍVEL
    function getOptimalColumnWidth(columnIndex) {
        const th = document.querySelectorAll('#trades-table th')[columnIndex];
        if (!th) return 80;
        
        // Medir o header (sem símbolos de ordenação)
        const headerText = th.textContent.replace(/↕|↑|↓/g, '').trim();
        const headerStyle = window.getComputedStyle(th);
        
        const tempHeader = document.createElement('div');
        tempHeader.style.position = 'absolute';
        tempHeader.style.visibility = 'hidden';
        tempHeader.style.whiteSpace = 'nowrap';
        tempHeader.style.font = headerStyle.font;
        tempHeader.style.padding = headerStyle.padding;
        tempHeader.textContent = headerText;
        document.body.appendChild(tempHeader);
        const headerWidth = tempHeader.offsetWidth;
        document.body.removeChild(tempHeader);
        
        // Verificar APENAS células VISÍVEIS (não ocultas)
        let maxWidth = headerWidth;
        const visibleRows = Array.from(document.querySelectorAll('#trades-table tbody tr:not(.hidden-row)'));
        
        visibleRows.forEach(row => {
            const cell = row.querySelectorAll('td')[columnIndex];
            if (!cell) return;
            
            // Obter o texto real da célula (sem HTML)
            const cellText = cell.textContent.trim();
            if (!cellText || cellText === '-') return;
            
            // Verificar se é numérica
            const isNumeric = cell.classList.contains('text-right');
            
            // Criar elemento temporário com o mesmo estilo da célula
            const cellStyle = window.getComputedStyle(cell);
            const tempCell = document.createElement('div');
            tempCell.style.position = 'absolute';
            tempCell.style.visibility = 'hidden';
            tempCell.style.font = cellStyle.font;
            tempCell.style.fontFamily = cellStyle.fontFamily;
            tempCell.style.fontSize = cellStyle.fontSize;
            tempCell.style.fontWeight = cellStyle.fontWeight;
            tempCell.style.padding = cellStyle.padding;
            
            let cellWidth;
            
            if (isNumeric) {
                // Para células numéricas: usar nowrap e medir diretamente
                tempCell.style.whiteSpace = 'nowrap';
                tempCell.style.width = 'auto';
                tempCell.style.maxWidth = 'none';
                tempCell.textContent = cellText;
                document.body.appendChild(tempCell);
                cellWidth = tempCell.offsetWidth;
                document.body.removeChild(tempCell);
            } else {
                // Para células de texto: usar a largura atual da célula renderizada
                // A célula já está renderizada com quebra de linha, então podemos usar sua largura
                // Mas primeiro, vamos medir o texto completo sem quebra para ter uma referência
                tempCell.style.whiteSpace = 'nowrap';
                tempCell.style.width = 'auto';
                tempCell.textContent = cellText;
                document.body.appendChild(tempCell);
                const fullWidthNoWrap = tempCell.offsetWidth;
                document.body.removeChild(tempCell);
                
                // Agora medir com a largura atual da célula (que já está renderizada)
                // Pegar a largura atual da célula visível
                const currentCellWidth = cell.offsetWidth;
                
                // Se a célula já tem uma largura definida e o texto quebra, precisamos medir
                // a linha mais longa. Para isso, vamos usar o texto completo e medir
                // em um container com a mesma largura da célula
                tempCell.style.whiteSpace = 'normal';
                tempCell.style.wordWrap = 'break-word';
                tempCell.style.width = currentCellWidth + 'px';
                tempCell.style.maxWidth = currentCellWidth + 'px';
                tempCell.textContent = cellText;
                document.body.appendChild(tempCell);
                
                // Pegar todas as linhas renderizadas e medir a mais longa
                const range = document.createRange();
                range.selectNodeContents(tempCell);
                const rects = range.getClientRects();
                
                let maxLineWidth = 0;
                for (let i = 0; i < rects.length; i++) {
                    if (rects[i].width > maxLineWidth) {
                        maxLineWidth = rects[i].width;
                    }
                }
                
                document.body.removeChild(tempCell);
                
                // Usar a maior entre: largura sem quebra (limitada) ou linha mais longa renderizada
                // Mas limitar a um máximo razoável (500px)
                cellWidth = Math.min(
                    Math.max(fullWidthNoWrap, maxLineWidth > 0 ? maxLineWidth : fullWidthNoWrap),
                    500
                );
            }
            
            if (cellWidth > maxWidth) {
                maxWidth = cellWidth;
            }
        });
        
        // Adicionar padding (15px de cada lado = 30px) + margem de segurança (10px)
        return Math.max(80, maxWidth + 40);
    }
    
    // Função para ajustar largura ideal de uma coluna
    function autoFitColumn(columnIndex) {
        const optimalWidth = getOptimalColumnWidth(columnIndex);
        const th = document.querySelectorAll('#trades-table th')[columnIndex];
        if (!th) return;
        
        th.style.width = optimalWidth + 'px';
        th.style.minWidth = optimalWidth + 'px';
        
        // Aplicar a mesma largura a todas as células da coluna
        document.querySelectorAll('#trades-table tbody tr').forEach(row => {
            const cell = row.querySelectorAll('td')[columnIndex];
            if (cell) {
                cell.style.width = optimalWidth + 'px';
                cell.style.minWidth = optimalWidth + 'px';
            }
        });
    }
    
    // Adicionar event listeners aos resize handles
    document.querySelectorAll('#trades-table th .resize-handle').forEach((handle, index) => {
        const th = handle.parentElement;
        
        // Evento de mousedown para redimensionamento manual
        handle.addEventListener('mousedown', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Impedir que o clique no header dispare ordenação
            
            isResizing = true;
            currentResizeColumn = index;
            startX = e.pageX;
            startWidth = th.offsetWidth;
            
            th.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            
            // Adicionar listeners globais
            document.addEventListener('mousemove', handleResize);
            document.addEventListener('mouseup', stopResize);
        });
        
        // Evento de duplo clique para auto-fit
        let clickTimer = null;
        handle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Impedir que o clique no header dispare ordenação
            
            // Detectar duplo clique
            if (clickTimer === null) {
                clickTimer = setTimeout(() => {
                    clickTimer = null;
                }, 300);
            } else {
                clearTimeout(clickTimer);
                clickTimer = null;
                // Duplo clique detectado
                autoFitColumn(index);
            }
        });
        
        // Também suportar dblclick nativo
        handle.addEventListener('dblclick', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Impedir que o clique no header dispare ordenação
            if (clickTimer) {
                clearTimeout(clickTimer);
                clickTimer = null;
            }
            autoFitColumn(index);
        });
    });
    
    function handleResize(e) {
        if (!isResizing || currentResizeColumn === null) return;
        
        const th = document.querySelectorAll('#trades-table th')[currentResizeColumn];
        if (!th) return;
        
        const diff = e.pageX - startX;
        const newWidth = Math.max(80, startWidth + diff); // Largura mínima de 80px
        
        th.style.width = newWidth + 'px';
        th.style.minWidth = newWidth + 'px';
        
        // Aplicar a mesma largura a todas as células da coluna
        const columnIndex = currentResizeColumn;
        document.querySelectorAll('#trades-table tbody tr').forEach(row => {
            const cell = row.querySelectorAll('td')[columnIndex];
            if (cell) {
                cell.style.width = newWidth + 'px';
                cell.style.minWidth = newWidth + 'px';
            }
        });
    }
    
    function stopResize(e) {
        if (isResizing) {
            // Verificar se houve movimento (real resize) ou foi apenas um clique
            const moved = Math.abs(e.pageX - startX) > 3; // Threshold de 3px
            
            isResizing = false;
            if (currentResizeColumn !== null) {
                const th = document.querySelectorAll('#trades-table th')[currentResizeColumn];
                if (th) {
                    th.classList.remove('resizing');
                }
            }
            currentResizeColumn = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // Se houve movimento, marcar que acabamos de fazer resize
            // Isso previne que o próximo clique no header dispare ordenação
            if (moved) {
                justFinishedResizing = true;
                // Limpar a flag após um pequeno delay para permitir outros cliques
                setTimeout(() => {
                    justFinishedResizing = false;
                }, 100);
            }
            
            // Remover listeners globais
            document.removeEventListener('mousemove', handleResize);
            document.removeEventListener('mouseup', stopResize);
        }
    }
});

