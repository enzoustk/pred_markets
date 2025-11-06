// Drawdown Table JavaScript
function updateDrawdownTable() {
    const periodSelect = document.getElementById('drawdown-period');
    const customDates = document.getElementById('drawdown-custom-dates');
    const period = periodSelect.value;
    
    if (period === 'custom') {
        customDates.style.display = 'block';
        // Para período personalizado, usar dados totais por enquanto
        // (seria necessário calcular no servidor para período customizado)
        const drawdownData = drawdownDataAll['all'];
        renderDrawdownTable(drawdownData);
        return;
    } else {
        customDates.style.display = 'none';
    }
    
    // Usar dados pré-calculados para o período selecionado
    const drawdownData = drawdownDataAll[period] || drawdownDataAll['all'];
    renderDrawdownTable(drawdownData);
}

{{format_currency_js}}

function renderDrawdownTable(drawdownData) {
    const tbody = document.getElementById('drawdown-table-body');
    
    // Renderizar tabela
    let html = '';
    
    // Drawdown Máximo em $
    const periodDays = drawdownData.max_drawdown_days || 0;
    const startDate = drawdownData.max_drawdown_start_date || 'N/A';
    const endDate = drawdownData.max_drawdown_end_date || 'N/A';
    
    html += `<tr>
        <td><strong>Drawdown Máximo (Profit)</strong></td>
        <td class="text-right loss">$${formatCurrency(drawdownData.max_drawdown_profit)}</td>
        <td>${periodDays} dias</td>
        <td>${startDate}</td>
        <td>${endDate}</td>
    </tr>`;
    
    // Drawdown Máximo em Flat Profit
    html += `<tr>
        <td><strong>Drawdown Máximo (Flat Profit)</strong></td>
        <td class="text-right loss">$${formatCurrency(drawdownData.max_drawdown_flat_profit)}</td>
        <td>${periodDays} dias</td>
        <td>${startDate}</td>
        <td>${endDate}</td>
    </tr>`;
    
    // Drawdown Mediano em $
    html += `<tr>
        <td><strong>Drawdown Mediano (Profit)</strong></td>
        <td class="text-right loss">$${formatCurrency(drawdownData.median_drawdown_profit)}</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
    </tr>`;
    
    // Drawdown Mediano em Flat Profit
    html += `<tr>
        <td><strong>Drawdown Mediano (Flat Profit)</strong></td>
        <td class="text-right loss">$${formatCurrency(drawdownData.median_drawdown_flat_profit)}</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
    </tr>`;
    
    tbody.innerHTML = html;
}

// Event listener para mudança de período
document.getElementById('drawdown-period').addEventListener('change', function() {
    if (this.value === 'custom') {
        document.getElementById('drawdown-custom-dates').style.display = 'block';
    } else {
        document.getElementById('drawdown-custom-dates').style.display = 'none';
        updateDrawdownTable();
    }
});

// Inicializar tabela
updateDrawdownTable();

