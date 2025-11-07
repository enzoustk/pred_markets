/**
 * CLV Analysis JavaScript
 * Gerencia o estado do botão, barra de carregamento e exibição dos resultados.
 */

// Estado do CLV
let clvState = {
    isLoading: false,
    data: null,
    tagName: null
};

/**
 * Inicializa o CLV Analysis
 */
function initCLVAnalysis(tagName) {
    clvState.tagName = tagName;
    
    const requestBtn = document.getElementById('request-clv-btn');
    if (requestBtn) {
        requestBtn.addEventListener('click', handleCLVRequest);
    }
    
    const viewByDateBtn = document.getElementById('view-clv-by-date-btn');
    if (viewByDateBtn) {
        viewByDateBtn.addEventListener('click', handleViewCLVByDate);
    }
}

/**
 * Manipula o clique no botão "Request CLV Analysis"
 */
async function handleCLVRequest() {
    if (clvState.isLoading) {
        return; // Já está carregando
    }
    
    // Verificar se já temos dados
    if (clvState.data) {
        // Se já temos dados, apenas mostrar novamente
        showCLVResults(clvState.data);
        return;
    }
    
    // Verificar se temos os dados necessários
    if (typeof userAddress === 'undefined' || !userAddress) {
        showErrorState('Endereço do usuário não disponível');
        return;
    }
    
    if (typeof dfTagData === 'undefined' || !dfTagData || dfTagData.length === 0) {
        showErrorState('Dados da tag não disponíveis');
        return;
    }
    
    // Iniciar carregamento
    clvState.isLoading = true;
    showLoadingState();
    
    try {
        // Chamar API para calcular CLV
        const clvData = await calculateCLVFromAPI(dfTagData, userAddress);
        
        clvState.data = clvData;
        clvState.isLoading = false;
        
        // Mostrar resultados
        showCLVResults(clvData);
        
    } catch (error) {
        console.error('Erro ao calcular CLV:', error);
        clvState.isLoading = false;
        showErrorState(error.message || 'Erro ao calcular CLV');
    }
}

/**
 * Calcula CLV chamando a API Flask
 */
async function calculateCLVFromAPI(dfData, userAddress) {
    // Determinar URL da API
    // Se estiver na porta 5000, usar a mesma origem
    // Se estiver em outra porta, tentar localhost:5000
    let apiUrl;
    if (window.location.port === '5000') {
        apiUrl = `${window.location.origin}/api/calculate_clv`;
    } else {
        // Tentar localhost:5000 primeiro
        apiUrl = 'http://localhost:5000/api/calculate_clv';
    }
    
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                df_data: dfData,
                user_address: userAddress
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
            throw new Error(errorData.error || `Erro HTTP: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        // Se for erro de conexão, fornecer mensagem mais clara
        if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
            throw new Error(
                'Servidor Flask não está rodando. ' +
                'Por favor, inicie o servidor Flask executando: python -m dashboard.server ' +
                'ou regenere o dashboard com criar_dashboard(..., auto_open=True)'
            );
        }
        throw error;
    }
}

/**
 * Mostra o estado de carregamento
 */
function showLoadingState() {
    const requestBtn = document.getElementById('request-clv-btn');
    const loadingDiv = document.getElementById('clv-loading');
    const resultsDiv = document.getElementById('clv-results');
    const clvContent = document.getElementById('clv-content');
    
    if (requestBtn) {
        requestBtn.disabled = true;
        requestBtn.textContent = 'Analyzing...';
    }
    
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
    }
    
    if (resultsDiv) {
        resultsDiv.style.display = 'none';
    }
    
    // Ajustar altura do conteúdo
    if (clvContent) {
        clvContent.style.justifyContent = 'flex-start';
    }
}

/**
 * Mostra os resultados do CLV
 */
function showCLVResults(data) {
    const requestBtn = document.getElementById('request-clv-btn');
    const loadingDiv = document.getElementById('clv-loading');
    const resultsDiv = document.getElementById('clv-results');
    const clvContent = document.getElementById('clv-content');
    
    // Ocultar botão e loading
    if (requestBtn) {
        requestBtn.style.display = 'none';
    }
    
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
    
    // Mostrar resultados
    if (resultsDiv) {
        resultsDiv.style.display = 'block';
    }
    
    // Preencher dados
    updateCLVDisplay(data);
    
    // Ajustar altura do conteúdo
    if (clvContent) {
        clvContent.style.justifyContent = 'flex-start';
        clvContent.style.alignItems = 'stretch';
    }
    
    // Re-sincronizar altura após mostrar resultados
    if (typeof syncChartHeights === 'function') {
        setTimeout(syncChartHeights, 100);
    }
}

/**
 * Atualiza a exibição dos dados do CLV
 */
function updateCLVDisplay(data) {
    // Formatar percentuais
    const formatPercent = (value) => {
        return `${value.toFixed(2)}%`;
    };
    
    const formatOdds = (value) => {
        return value.toFixed(2);
    };
    
    // CLV+ %
    const clvPositiveEl = document.getElementById('clv-positive-percent');
    if (clvPositiveEl) {
        clvPositiveEl.textContent = formatPercent(data.clv_positive_percent);
        clvPositiveEl.className = 'clv-stat-value positive';
    }
    
    // CLV 0 %
    const clvZeroEl = document.getElementById('clv-zero-percent');
    if (clvZeroEl) {
        clvZeroEl.textContent = formatPercent(data.clv_zero_percent);
        clvZeroEl.className = 'clv-stat-value neutral';
    }
    
    // CLV - %
    const clvNegativeEl = document.getElementById('clv-negative-percent');
    if (clvNegativeEl) {
        clvNegativeEl.textContent = formatPercent(data.clv_negative_percent);
        clvNegativeEl.className = 'clv-stat-value negative';
    }
    
    // Avg CLV (Percent)
    const avgPercentEl = document.getElementById('avg-clv-percent');
    if (avgPercentEl) {
        avgPercentEl.textContent = formatPercent(data.avg_clv_percent);
    }
    
    // Median CLV (Percent)
    const medianPercentEl = document.getElementById('median-clv-percent');
    if (medianPercentEl) {
        medianPercentEl.textContent = formatPercent(data.median_clv_percent);
    }
    
    // Avg CLV (Odds)
    const avgOddsEl = document.getElementById('avg-clv-odds');
    if (avgOddsEl) {
        avgOddsEl.textContent = formatOdds(data.avg_clv_odds);
    }
    
    // Median CLV (Odds)
    const medianOddsEl = document.getElementById('median-clv-odds');
    if (medianOddsEl) {
        medianOddsEl.textContent = formatOdds(data.median_clv_odds);
    }
}

/**
 * Mostra estado de erro
 */
function showErrorState(errorMessage) {
    const requestBtn = document.getElementById('request-clv-btn');
    const loadingDiv = document.getElementById('clv-loading');
    
    if (requestBtn) {
        requestBtn.disabled = false;
        requestBtn.textContent = 'Request CLV Analysis';
    }
    
    if (loadingDiv) {
        loadingDiv.innerHTML = `
            <div style="color: #FF3B30; text-align: center; padding: 16px;">
                <p style="margin: 0;">Error: ${errorMessage}</p>
                <button onclick="handleCLVRequest()" style="margin-top: 12px; padding: 8px 16px; background: #0A84FF; color: white; border: none; border-radius: 6px; cursor: pointer;">Retry</button>
            </div>
        `;
    }
}

/**
 * Manipula o clique no botão "View CLV by Date"
 */
function handleViewCLVByDate() {
    // TODO: Implementar visualização de CLV por data
    console.log('View CLV by Date clicked');
    alert('View CLV by Date functionality will be implemented soon.');
}

