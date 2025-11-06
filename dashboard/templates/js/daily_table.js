// Daily Table JavaScript
let currentPeriod = 'daily';
let currentData = [...dailyData];
let filteredData = [...dailyData];

function switchPeriod(period) {
    currentPeriod = period;
    
    // Atualizar botões
    document.getElementById('period-daily').style.background = period === 'daily' ? '#007AFF' : '#38383A';
    document.getElementById('period-monthly').style.background = period === 'monthly' ? '#007AFF' : '#38383A';
    document.getElementById('period-yearly').style.background = period === 'yearly' ? '#007AFF' : '#38383A';
    
    // Trocar dados
    if (period === 'daily') {
        currentData = [...dailyData];
        // Para período diário, mostrar últimos 10 dias a partir de hoje
        filterByLastNDays(10);
    } else if (period === 'monthly') {
        currentData = [...monthlyData];
        filterDaily();
    } else if (period === 'yearly') {
        currentData = [...yearlyData];
        filterDaily();
    }
}

function updateTotals(data) {
    // Calcular totais dos dados filtrados
    const totalProfit = data.reduce((sum, row) => sum + row.profit, 0);
    const totalFlatProfit = data.reduce((sum, row) => sum + row.flat_profit, 0);
    
    // Calcular ROI médio (pesado pelo volume, mas como não temos volume nos dados filtrados, vamos calcular média simples)
    const avgROI = data.length > 0 ? data.reduce((sum, row) => sum + row.roi, 0) / data.length : 0;
    
    // Atualizar elementos
    const profitElement = document.getElementById('total-profit');
    const flatProfitElement = document.getElementById('total-flat-profit');
    const roiElement = document.getElementById('total-roi');
    
    profitElement.textContent = '$' + totalProfit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    profitElement.style.color = totalProfit >= 0 ? COLOR_PROFIT : COLOR_LOSS;
    
    flatProfitElement.textContent = '$' + totalFlatProfit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    flatProfitElement.style.color = totalFlatProfit >= 0 ? COLOR_PROFIT : COLOR_LOSS;
    
    roiElement.textContent = (avgROI * 100).toFixed(2) + '%';
    roiElement.style.color = avgROI >= 0 ? COLOR_PROFIT : COLOR_LOSS;
}

{{daily_table_renderer_js}}

function filterDaily() {
    const limit = document.getElementById('daily-limit').value;
    const dateFrom = document.getElementById('date-from').value;
    const dateTo = document.getElementById('date-to').value;
    
    filteredData = [...currentData];
    
    // Filtrar por datas
    if (dateFrom) {
        filteredData = filteredData.filter(row => row.date >= dateFrom);
    }
    if (dateTo) {
        filteredData = filteredData.filter(row => row.date <= dateTo);
    }
    
    // Ordenar por data (mais recente primeiro)
    filteredData.sort((a, b) => b.date.localeCompare(a.date));
    
    // Limitar quantidade
    if (limit !== 'all') {
        filteredData = filteredData.slice(0, parseInt(limit));
    }
    
    renderDailyTable(filteredData);
    updateTotals(filteredData);
}

function resetDailyFilter() {
    document.getElementById('daily-limit').value = '10';
    document.getElementById('date-from').value = '';
    document.getElementById('date-to').value = '';
    filterByLastNDays(10);
}

function getLastNDays(n) {
    // Retorna os últimos N dias a partir de hoje
    const today = new Date();
    const result = [];
    
    for (let i = 0; i < n; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        result.push(dateStr);
    }
    return result;
}

function filterByLastNDays(n) {
    // Filtrar para mostrar apenas os últimos N dias a partir de hoje
    const lastNDays = getLastNDays(n);
    filteredData = currentData.filter(row => {
        // Extrair apenas a data (YYYY-MM-DD) do formato do dado
        const rowDate = row.date.split(' ')[0].split('T')[0];
        return lastNDays.includes(rowDate);
    });
    
    // Ordenar por data (mais recente primeiro)
    filteredData.sort((a, b) => b.date.localeCompare(a.date));
    
    renderDailyTable(filteredData);
    updateTotals(filteredData);
}

// Renderizar inicialmente com últimos 10 dias a partir de hoje
const limitSelect = document.getElementById('daily-limit');
limitSelect.addEventListener('change', function() {
    if (this.value === '10') {
        filterByLastNDays(10);
    } else if (this.value === '15') {
        filterByLastNDays(15);
    } else if (this.value === '30') {
        filterByLastNDays(30);
    } else {
        filterDaily();
    }
});

// Inicializar mostrando últimos 10 dias
filterByLastNDays(10);

