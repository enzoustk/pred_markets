// Main Page JavaScript - Cumulative Chart Updates

function updateCumulativeChart(period) {
    const container = document.getElementById('cumulative-chart-container');
    const chartDiv = document.getElementById('cumulative-chart');
    
    // Adicionar classe de atualização imediatamente
    container.classList.add('updating');
    
    // Pequeno delay para permitir que a animação CSS comece
    requestAnimationFrame(function() {
        setTimeout(function() {
            let data;
            if (period === 'custom') {
                const startDate = document.getElementById('cumulative-start-date').value;
                const endDate = document.getElementById('cumulative-end-date').value;
                
                if (!startDate || !endDate) {
                    container.classList.remove('updating');
                    return;
                }
                
                // Filtrar dados por intervalo personalizado
                const start = new Date(startDate);
                const end = new Date(endDate);
                const filteredDates = [];
                const filteredProfits = [];
                
                for (let i = 0; i < allCumulativeData.dates.length; i++) {
                    const date = new Date(allCumulativeData.dates[i]);
                    if (date >= start && date <= end) {
                        filteredDates.push(allCumulativeData.dates[i]);
                        filteredProfits.push(allCumulativeData.profits[i]);
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
                data = cumulativeChartData[period] || cumulativeChartData['all'];
            }
            
            // Atualizar gráfico com Plotly.restyle (atualizar ambas as camadas)
            Plotly.restyle('cumulative-chart', {
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

document.getElementById('cumulative-period').addEventListener('change', function() {
    const period = this.value;
    const customDates = document.getElementById('cumulative-custom-dates');
    
    if (period === 'custom') {
        customDates.style.display = 'block';
        // Definir datas padrão (últimos 30 dias)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        document.getElementById('cumulative-end-date').value = endDate.toISOString().split('T')[0];
        document.getElementById('cumulative-start-date').value = startDate.toISOString().split('T')[0];
        
        // Atualizar após um pequeno delay para garantir que as datas foram definidas
        setTimeout(() => updateCumulativeChart('custom'), 100);
    } else {
        customDates.style.display = 'none';
        updateCumulativeChart(period);
    }
});

// Event listeners para datas personalizadas
document.getElementById('cumulative-start-date').addEventListener('change', function() {
    if (document.getElementById('cumulative-period').value === 'custom') {
        updateCumulativeChart('custom');
    }
});

document.getElementById('cumulative-end-date').addEventListener('change', function() {
    if (document.getElementById('cumulative-period').value === 'custom') {
        updateCumulativeChart('custom');
    }
});



