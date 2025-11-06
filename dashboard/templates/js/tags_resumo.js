// Tags Resumo Page JavaScript - Chart Updates and Table Initialization
// Variáveis injetadas: tagsPageData, chartData, FONT_FAMILY_VALUE, COLOR_TEXT_SECONDARY_VALUE, COLOR_SEPARATOR_VALUE

// Tornar updateChart disponível globalmente
window.updateChart = function updateChart() {
    console.log('updateChart chamado');
    const metric = document.getElementById('chart-metric').value;
    const sortOrder = document.getElementById('chart-sort').value;
    const metricLabels = {
        'profit': 'Profit',
        'roi': 'ROI (%)',
        'volume': 'Volume',
        'bets': 'Bets'
    };
    
    // Criar array com índices para ordenação
    const dataWithIndex = chartData.map((item, index) => ({
        ...item,
        originalIndex: index,
        metricValue: item[metric]
    }));
    
    // Ordenar os dados
    const sortedData = dataWithIndex.sort((a, b) => {
        const aVal = a.metricValue || 0;
        const bVal = b.metricValue || 0;
        if (sortOrder === 'asc') {
            return aVal - bVal;
        } else {
            return bVal - aVal;
        }
    });
    
    // Extrair dados ordenados
    const metricData = sortedData.map(item => item.metricValue);
    const tags = sortedData.map(item => item.tag);
    const sortedChartData = sortedData.map(item => {
        const original = chartData[item.originalIndex];
        return original;
    });
    
    let colors, colorsBorder, hoverTemplate, customData;
    
    if (metric === 'profit') {
        colors = metricData.map(p => p >= 0 ? '#34C759' : '#FF3B30');
        colorsBorder = metricData.map(p => p >= 0 ? '#28A745' : '#DC3545');
        customData = sortedChartData.map(item => [item.roi, item.volume, item.bets]);
        hoverTemplate = '<b>%{{y}}</b><br>' +
                       '<b>Profit:</b> $%{{x:,.2f}}<br>' +
                       '<b>ROI:</b> %{{customdata[0]:.2f}}%<br>' +
                       '<b>Volume:</b> $%{{customdata[1]:,.2f}}<br>' +
                       '<b>Bets:</b> %{{customdata[2]:.0f}}<extra></extra>';
    } else if (metric === 'roi') {
        colors = metricData.map(r => r >= 0 ? '#34C759' : '#FF3B30');
        colorsBorder = metricData.map(r => r >= 0 ? '#28A745' : '#DC3545');
        customData = sortedChartData.map(item => [item.profit, item.volume, item.bets]);
        hoverTemplate = '<b>%{{y}}</b><br>' +
                       '<b>ROI:</b> %{{x:.2f}}%<br>' +
                       '<b>Profit:</b> $%{{customdata[0]:,.2f}}<br>' +
                       '<b>Volume:</b> $%{{customdata[1]:,.2f}}<br>' +
                       '<b>Bets:</b> %{{customdata[2]:.0f}}<extra></extra>';
    } else if (metric === 'volume') {
        colors = Array(metricData.length).fill('#007AFF');
        colorsBorder = Array(metricData.length).fill('#0056CC');
        customData = sortedChartData.map(item => [item.profit, item.roi, item.bets]);
        hoverTemplate = '<b>%{{y}}</b><br>' +
                       '<b>Volume:</b> $%{{x:,.2f}}<br>' +
                       '<b>Profit:</b> $%{{customdata[0]:,.2f}}<br>' +
                       '<b>ROI:</b> %{{customdata[1]:.2f}}%<br>' +
                       '<b>Bets:</b> %{{customdata[2]:.0f}}<extra></extra>';
    } else {
        colors = Array(metricData.length).fill('#8E8E93');
        colorsBorder = Array(metricData.length).fill('#636366');
        customData = sortedChartData.map(item => [item.profit, item.roi, item.volume]);
        hoverTemplate = '<b>%{{y}}</b><br>' +
                       '<b>Bets:</b> %{{x:.0f}}<br>' +
                       '<b>Profit:</b> $%{{customdata[0]:,.2f}}<br>' +
                       '<b>ROI:</b> %{{customdata[1]:.2f}}%<br>' +
                       '<b>Volume:</b> $%{{customdata[2]:,.2f}}<extra></extra>';
    }
    
    const data = [{
        x: metricData,
        y: tags,
        type: 'bar',
        orientation: 'h',
        marker: {
            color: colors,
            opacity: 0.95,
            line: {
                color: colorsBorder,
                width: 2.5
            }
        },
        hovertemplate: hoverTemplate,
        customdata: customData
    }];
    
    const layout = {
        title: {
            text: 'Tag Analysis - ' + metricLabels[metric],
            x: 0.5,
            xanchor: 'center',
            font: {
                size: 24,
                family: FONT_FAMILY_VALUE,
                color: '#FFFFFF',
                weight: 600
            }
        },
        height: Math.max(600, tags.length * 25),
        showlegend: false,
        template: 'plotly_dark',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 80, b: 80, l: 180, r: 80 },
        font: {
            family: FONT_FAMILY_VALUE,
            size: 13,
            color: COLOR_TEXT_SECONDARY_VALUE
        },
        yaxis: {
            showgrid: false,
            tickfont: {
                size: 12,
                color: '#FFFFFF'
            },
            title: '',
            linecolor: '#FFFFFF',
            tickcolor: '#FFFFFF'
        },
        xaxis: {
            showgrid: true,
            gridcolor: COLOR_SEPARATOR_VALUE,
            zerolinecolor: COLOR_SEPARATOR_VALUE,
            zeroline: true,
            tickfont: {
                size: 12,
                color: '#FFFFFF'
            },
            linecolor: '#FFFFFF',
            tickcolor: '#FFFFFF'
        }
    };
    
    // Verificar se Plotly está disponível
    if (typeof Plotly === 'undefined') {
        console.error('Plotly não está disponível. Aguardando...');
        setTimeout(function() {
            if (typeof Plotly !== 'undefined') {
                window.updateChart();
            } else {
                console.error('Plotly ainda não carregou após espera');
            }
        }, 100);
        return;
    }
    
    // Encontrar o elemento do gráfico
    let chartDiv = document.getElementById('tags-chart');
    
    if (!chartDiv) {
        const container = document.getElementById('chart-container');
        if (container) {
            chartDiv = container.querySelector('#tags-chart');
        }
    }
    
    if (!chartDiv) {
        const container = document.getElementById('chart-container');
        if (container) {
            chartDiv = container.querySelector('.js-plotly-plot') || container.querySelector('[id*="plotly"]');
        }
    }
    
    if (!chartDiv) {
        const container = document.getElementById('chart-container');
        if (container) {
            chartDiv = document.createElement('div');
            chartDiv.id = 'tags-chart';
            container.innerHTML = '';
            container.appendChild(chartDiv);
        } else {
            console.error('Container chart-container não encontrado');
            return;
        }
    }
    
    console.log('Atualizando gráfico para métrica:', metric);
    
    const hasExistingPlot = chartDiv.querySelector && chartDiv.querySelector('.plotly');
    
    const config = {
        displayModeBar: false,
        responsive: true
    };
    
    if (hasExistingPlot) {
        console.log('Atualizando gráfico com animação suave');
        
        const plotlyDiv = chartDiv.querySelector('.plotly');
        if (plotlyDiv) {
            plotlyDiv.classList.add('animating');
            plotlyDiv.style.transition = 'opacity 0.25s ease-out, transform 0.25s ease-out';
            plotlyDiv.style.opacity = '0.6';
            plotlyDiv.style.transform = 'scale(0.97)';
        }
        
        setTimeout(function() {
            Plotly.restyle('tags-chart', {
                x: [metricData],
                y: [tags],
                'marker.color': [colors],
                'marker.line.color': [colorsBorder],
                'customdata': [customData],
                'hovertemplate': [hoverTemplate]
            }, [0])
                .then(function() {
                    return Plotly.relayout('tags-chart', {
                        'title.text': 'Tag Analysis - ' + metricLabels[metric],
                        'xaxis.tickfont.color': '#FFFFFF',
                        'xaxis.linecolor': '#FFFFFF',
                        'xaxis.tickcolor': '#FFFFFF',
                        'yaxis.tickfont.color': '#FFFFFF',
                        'yaxis.linecolor': '#FFFFFF',
                        'yaxis.tickcolor': '#FFFFFF'
                    });
                })
                .then(function() {
                    console.log('Gráfico atualizado com animação');
                    if (plotlyDiv) {
                        setTimeout(function() {
                            plotlyDiv.style.transition = 'opacity 0.35s ease-in, transform 0.35s ease-in';
                            plotlyDiv.style.opacity = '1';
                            plotlyDiv.style.transform = 'scale(1)';
                            setTimeout(function() {
                                plotlyDiv.classList.remove('animating');
                            }, 350);
                        }, 20);
                    }
                    roundBarCorners();
                })
                .catch(function(err) {
                    console.warn('Erro na animação, usando Plotly.react:', err);
                    if (plotlyDiv) {
                        plotlyDiv.style.opacity = '1';
                        plotlyDiv.style.transform = 'scale(1)';
                        plotlyDiv.classList.remove('animating');
                    }
                    Plotly.react('tags-chart', data, layout, config)
                        .then(function() {
                            console.log('Gráfico atualizado com Plotly.react');
                            roundBarCorners();
                        });
                });
        }, 200);
    } else {
        console.log('Criando novo gráfico com Plotly.newPlot');
        Plotly.newPlot('tags-chart', data, layout, config)
            .then(function() {
                console.log('Gráfico criado com sucesso!');
                roundBarCorners();
            })
            .catch(function(err) {
                console.error('Erro ao criar gráfico:', err);
            });
    }
};

// Função para arredondar cantos das barras
function roundBarCorners() {
    let chartDiv = document.getElementById('tags-chart');
    if (!chartDiv) {
        const container = document.getElementById('chart-container');
        if (container) {
            chartDiv = container.querySelector('#tags-chart') || container.querySelector('.js-plotly-plot');
        }
    }
    if (!chartDiv) return;
    
    function applyRoundCorners() {
        const rects = chartDiv.querySelectorAll('.trace.bars rect, .js-plotly-plot .trace.bars rect');
        rects.forEach(function(rect) {
            rect.setAttribute('rx', '10');
            rect.setAttribute('ry', '10');
            if (!rect.hasAttribute('filter-applied')) {
                rect.setAttribute('filter', 'url(#shadow)');
                rect.setAttribute('filter-applied', 'true');
            }
        });
        
        const paths = chartDiv.querySelectorAll('.trace.bars path, .js-plotly-plot .trace.bars path');
        paths.forEach(function(path) {
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
        });
        
        let svg = chartDiv.querySelector('svg');
        if (svg && !svg.querySelector('#shadow')) {
            const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
            filter.setAttribute('id', 'shadow');
            filter.setAttribute('x', '-50%');
            filter.setAttribute('y', '-50%');
            filter.setAttribute('width', '200%');
            filter.setAttribute('height', '200%');
            const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
            feGaussianBlur.setAttribute('in', 'SourceAlpha');
            feGaussianBlur.setAttribute('stdDeviation', '2');
            const feOffset = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
            feOffset.setAttribute('dx', '0');
            feOffset.setAttribute('dy', '2');
            feOffset.setAttribute('result', 'offsetblur');
            const feComponentTransfer = document.createElementNS('http://www.w3.org/2000/svg', 'feComponentTransfer');
            feComponentTransfer.setAttribute('in', 'offsetblur');
            const feFuncA = document.createElementNS('http://www.w3.org/2000/svg', 'feFuncA');
            feFuncA.setAttribute('type', 'linear');
            feFuncA.setAttribute('slope', '0.3');
            feComponentTransfer.appendChild(feFuncA);
            const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
            const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
            const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
            feMergeNode2.setAttribute('in', 'SourceGraphic');
            feMerge.appendChild(feMergeNode1);
            feMerge.appendChild(feMergeNode2);
            filter.appendChild(feGaussianBlur);
            filter.appendChild(feOffset);
            filter.appendChild(feComponentTransfer);
            filter.appendChild(feMerge);
            defs.appendChild(filter);
            svg.insertBefore(defs, svg.firstChild);
        }
    }
    
    setTimeout(applyRoundCorners, 150);
    setTimeout(applyRoundCorners, 500);
}

// Inicializar controles do gráfico
function initializeChartControls() {
    console.log('Inicializando controles do gráfico...');
    
    const selectMetric = document.getElementById('chart-metric');
    const selectSort = document.getElementById('chart-sort');
    
    if (selectMetric) {
        selectMetric.addEventListener('change', function() {
            console.log('Métrica mudou para:', this.value);
            if (typeof window.updateChart === 'function') {
                window.updateChart();
            } else {
                console.error('updateChart não está disponível');
            }
        });
        console.log('Event listener adicionado ao select chart-metric');
    } else {
        console.error('Elemento chart-metric não encontrado');
    }
    
    if (selectSort) {
        selectSort.addEventListener('change', function() {
            console.log('Ordenação mudou para:', this.value);
            if (typeof window.updateChart === 'function') {
                window.updateChart();
            } else {
                console.error('updateChart não está disponível');
            }
        });
        console.log('Event listener adicionado ao select chart-sort');
    } else {
        console.error('Elemento chart-sort não encontrado');
    }
    
    setTimeout(function() {
        roundBarCorners();
    }, 1000);
}

// Aguardar DOM e Plotly estarem prontos
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM carregado, inicializando...');
        initializeChartControls();
    });
} else {
    console.log('DOM já estava pronto');
    initializeChartControls();
}

