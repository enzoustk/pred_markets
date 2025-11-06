// Reusable Chart Period Update JavaScript
// Use this for any chart that needs period filtering (daily, cumulative, etc.)
// Variables injected: chartData, allData, chartId, containerId, periodSelectId, startDateId, endDateId

function updateChartPeriod() {
    const period = document.getElementById(periodSelectId).value;
    const container = document.getElementById(containerId);
    const chartDiv = document.getElementById(chartId);
    
    // Adicionar classe de atualização imediatamente
    container.classList.add('updating');
    
    // Pequeno delay para permitir que a animação CSS comece
    requestAnimationFrame(function() {
        setTimeout(function() {
            let data;
            if (period === 'custom') {
                const startDate = document.getElementById(startDateId).value;
                const endDate = document.getElementById(endDateId).value;
                
                if (!startDate || !endDate) {
                    container.classList.remove('updating');
                    return;
                }
                
                // Filtrar dados por intervalo personalizado
                const start = new Date(startDate);
                const end = new Date(endDate);
                const filteredDates = [];
                const filteredProfits = [];
                
                for (let i = 0; i < allData.dates.length; i++) {
                    const date = new Date(allData.dates[i]);
                    if (date >= start && date <= end) {
                        filteredDates.push(allData.dates[i]);
                        filteredProfits.push(allData.profits[i]);
                    }
                }
                
                // Calcular lucro acumulado para o período filtrado
                let cumulative = 0;
                const cumulativeValues = filteredProfits.map(profit => {
                    cumulative += profit;
                    return cumulative;
                });
                
                data = {
                    x: filteredDates,
                    y: cumulativeValues
                };
            } else {
                data = chartData[period] || chartData['all'];
            }
            
            // Atualizar gráfico com Plotly.restyle (atualizar ambas as camadas)
            Plotly.restyle(chartId, {
                'x': [data.x, data.x],
                'y': [data.y, data.y]
            }, [0, 1]).then(function() {
                // Aguardar um pouco antes de remover a classe para animação suave
                setTimeout(function() {
                    container.classList.remove('updating');
                }, 150);
            });
        }, 30);
    });
}

document.getElementById(periodSelectId).addEventListener('change', function() {
    const period = this.value;
    const customDates = document.getElementById(customDatesId);
    
    if (period === 'custom') {
        customDates.style.display = 'block';
        // Definir datas padrão (últimos 30 dias)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        document.getElementById(endDateId).value = endDate.toISOString().split('T')[0];
        document.getElementById(startDateId).value = startDate.toISOString().split('T')[0];
        
        // Atualizar após um pequeno delay para garantir que as datas foram definidas
        setTimeout(() => updateChartPeriod('custom'), 100);
    } else {
        customDates.style.display = 'none';
        updateChartPeriod(period);
    }
});

// Event listeners para datas personalizadas
document.getElementById(startDateId).addEventListener('change', function() {
    if (document.getElementById(periodSelectId).value === 'custom') {
        updateChartPeriod('custom');
    }
});

document.getElementById(endDateId).addEventListener('change', function() {
    if (document.getElementById(periodSelectId).value === 'custom') {
        updateChartPeriod('custom');
    }
});

