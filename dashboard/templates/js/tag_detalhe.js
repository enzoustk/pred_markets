// Tag Detalhe Page JavaScript - Daily Chart Updates
// Similar to main_page.js but for daily chart

function updateDailyChart(period) {
    const container = document.getElementById('daily-chart-container');
    const chartDiv = document.getElementById('daily-chart');
    
    // Adicionar classe de atualização imediatamente
    container.classList.add('updating');
    
    // Pequeno delay para permitir que a animação CSS comece
    requestAnimationFrame(function() {
        setTimeout(function() {
            let data;
            if (period === 'custom') {
                const startDate = document.getElementById('daily-start-date').value;
                const endDate = document.getElementById('daily-end-date').value;
                
                if (!startDate || !endDate) {
                    container.classList.remove('updating');
                    return;
                }
                
                // Filtrar dados por intervalo personalizado
                const start = new Date(startDate);
                const end = new Date(endDate);
                const filteredDates = [];
                const filteredProfits = [];
                
                for (let i = 0; i < allDailyData.dates.length; i++) {
                    const date = new Date(allDailyData.dates[i]);
                    if (date >= start && date <= end) {
                        filteredDates.push(allDailyData.dates[i]);
                        filteredProfits.push(allDailyData.profits[i]);
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
                data = dailyChartData[period] || dailyChartData['all'];
            }
            
            // Atualizar gráfico com Plotly.restyle (atualizar ambas as camadas)
            Plotly.restyle('daily-chart', {
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

document.getElementById('daily-period').addEventListener('change', function() {
    const period = this.value;
    const customDates = document.getElementById('daily-custom-dates');
    
    if (period === 'custom') {
        customDates.style.display = 'flex';
        // Definir datas padrão (últimos 30 dias)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        document.getElementById('daily-end-date').value = endDate.toISOString().split('T')[0];
        document.getElementById('daily-start-date').value = startDate.toISOString().split('T')[0];
        
        // Atualizar após um pequeno delay para garantir que as datas foram definidas
        setTimeout(() => updateDailyChart('custom'), 100);
    } else {
        customDates.style.display = 'none';
        updateDailyChart(period);
    }
});

// Event listeners para datas personalizadas
document.getElementById('daily-start-date').addEventListener('change', function() {
    if (document.getElementById('daily-period').value === 'custom') {
        updateDailyChart('custom');
    }
});

document.getElementById('daily-end-date').addEventListener('change', function() {
    if (document.getElementById('daily-period').value === 'custom') {
        updateDailyChart('custom');
    }
});

