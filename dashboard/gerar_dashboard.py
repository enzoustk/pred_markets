import pandas as pd
import os
import sys
import ast 
import webbrowser
import http.server
import socketserver
import threading
import time

# Adiciona o diretório raiz (um nível acima) ao path

try:
    from data.analysys import DataAnalyst
    from helpers import to_list, safe_divide  # <--- Importa o safe_divide CORRETO
    # Imports diretos dos módulos refatorados
    from dashboard.pages.main_page import criar_pagina_principal
    from dashboard.pages.tags_pages import (
        criar_pagina_tags_resumo,
        criar_pagina_detalhe_tag,
        criar_pagina_apostas_tag
    )
except ImportError as e:
    print(f"Erro: Não foi possível importar os módulos. Verifique sua estrutura de arquivos.")
    print(f"Detalhe: {e}")
    print("Certifique-se que os módulos estão corretos.")
    sys.exit(1)

# --- Funções Auxiliares de Dados ---

def get_exploded_df(df: pd.DataFrame, exclude_tags: list = []) -> pd.DataFrame:
    """
    Cria DataFrame exploded com tags para análise detalhada.
    Usa a lógica de 'tag_analysys' para duplicar a funcionalidade.
    """
    df = df.copy()
    removed_tags = ['Games', 'Sports'] + exclude_tags
    
    tmp = df.copy()
    tmp['__tags_list'] = tmp['tags'].apply(to_list)
    exploded = tmp.explode('__tags_list', ignore_index=True)
    exploded = exploded.rename(columns={'__tags_list': 'tag'})
    exploded = exploded[exploded['tag'].notna()]
    exploded = exploded[~exploded['tag'].isin(removed_tags)]
    
    # CORREÇÃO: Usar apenas realizedPnl para evitar duplicação
    exploded['total_profit'] = exploded['realizedPnl'].fillna(0)
    exploded['volume'] = exploded['totalBought'] * exploded['avgPrice']
    exploded['staked'] = exploded['totalBought'] * exploded['avgPrice']
    
    # ⬇️ --- CORREÇÃO APLICADA AQUI --- ⬇️
    # Usar o safe_divide importado de 'helpers', não o de 'graficos'
    exploded['roi'] = safe_divide(exploded['total_profit'], exploded['volume'])
    # ⬆️ --- FIM DA CORREÇÃO --- ⬆️
    
    return exploded

# --- Variáveis globais para servidor ---
_httpd = None
_port = None

def _adicionar_css_tabelas_plotly(html_path: str):
    """
    Adiciona CSS customizado para melhorar as tabelas Plotly com scrollbars e texto branco.
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # CSS para melhorar tabelas Plotly
        plotly_table_css = '''
        <style>
            /* Melhorar tabelas Plotly */
            .js-plotly-plot .plotly table {
                color: #FFFFFF !important;
            }
            .js-plotly-plot .plotly table thead th {
                color: #FFFFFF !important;
                background-color: #1C1C1E !important;
            }
            .js-plotly-plot .plotly table tbody td {
                color: #FFFFFF !important;
            }
            /* Scrollbars para containers Plotly */
            .js-plotly-plot {
                overflow: auto;
            }
            .js-plotly-plot::-webkit-scrollbar {
                width: 12px;
                height: 12px;
            }
            .js-plotly-plot::-webkit-scrollbar-track {
                background: #000000;
                border-radius: 6px;
            }
            .js-plotly-plot::-webkit-scrollbar-thumb {
                background: rgba(142, 142, 147, 0.3);
                border-radius: 6px;
            }
            .js-plotly-plot::-webkit-scrollbar-thumb:hover {
                background: rgba(142, 142, 147, 0.5);
            }
        </style>
        '''
        
        # Inserir CSS antes do fechamento do </head> ou no início do <body>
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', plotly_table_css + '</head>')
        elif '<body>' in html_content:
            html_content = html_content.replace('<body>', '<body>' + plotly_table_css)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível adicionar CSS customizado: {e}")

def _start_temp_server(directory, port=8000):
    """Inicia um servidor HTTP temporário para servir os arquivos HTML."""
    global _httpd, _port
    original_dir = os.getcwd()
    try:
        os.chdir(directory)
        handler = http.server.SimpleHTTPRequestHandler
        
        # Tentar criar servidor com reutilização de porta
        for attempt in range(100):  # Tenta até 8100
            try:
                _httpd = socketserver.TCPServer(("", port), handler, bind_and_activate=False)
                _httpd.allow_reuse_address = True
                _httpd.server_bind()
                _httpd.server_activate()
                _port = port
                print(f"🌐 Servidor iniciado em http://localhost:{port}")
                _httpd.serve_forever()
                break
            except OSError:
                if port < 8100:
                    port += 1
                    continue
                else:
                    raise
    finally:
        os.chdir(original_dir)

def criar_dashboard(df: pd.DataFrame, min_bets_per_tag: int = 50, auto_open: bool = True):
    """
    Cria um dashboard interativo a partir de um DataFrame.
    
    Args:
        df: DataFrame com os dados para análise
        min_bets_per_tag: Número mínimo de apostas por tag para incluir na análise
        auto_open: Se True, abre automaticamente no navegador e inicia servidor localhost
    
    Returns:
        dict: Dicionário com informações do dashboard (output_dir, main_path, url, etc.)
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    OUTPUT_DIR = os.path.join(BASE_DIR, 'dashboard_output') 
    TAGS_DIR = os.path.join(OUTPUT_DIR, 'tags') 
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TAGS_DIR, exist_ok=True)
    print(f"Diretórios de saída '{OUTPUT_DIR}' e '{TAGS_DIR}' estão prontos.")
    
    # Preparar dados
    print("Analisando dados... (Isso pode levar um momento)")
    df_main = df.copy()
    df_main['staked'] = df_main['totalBought'] * df_main['avgPrice']
    
    total_profit, total_volume, total_roi = DataAnalyst.return_stats(df_main)
    
    # Calcular flat profit individualmente para cada aposta e depois somar
    # CORREÇÃO: Usar apenas realizedPnl para evitar duplicação
    if 'total_profit' not in df_main.columns:
        df_main['total_profit'] = df_main['realizedPnl'].fillna(0)
    if 'staked' not in df_main.columns:
        df_main['staked'] = df_main['totalBought'] * df_main['avgPrice']
    df_main['roi_individual'] = safe_divide(df_main['total_profit'], df_main['staked'])
    flat_profit_total = df_main['roi_individual'].sum()
    
    stats_gerais = {
        'total_profit': total_profit,
        'total_volume': total_volume,
        'total_roi': total_roi,
        'flat_profit': flat_profit_total,
        'mean_stake': df_main['staked'].mean(),
        'median_stake': df_main['staked'].median(),
        'total_bets': len(df_main)
    }
    
    df_daily = DataAnalyst.daily_balance(df_main)
    df_daily['date'] = df_daily['date'].astype(str)
    
    df_monthly = DataAnalyst.monthly_balance(df_main)
    df_monthly['date'] = df_monthly['date'].astype(str)
    
    # Calcular balance anual (similar ao monthly_balance)
    df_yearly = df_main.copy()
    df_yearly['year'] = pd.to_datetime(df_yearly['endDate'], format='ISO8601', utc=True).dt.tz_localize(None).dt.to_period('Y')
    yearly_data = []
    for year, year_df in df_yearly.groupby('year'):
        profit, vol, roi = DataAnalyst.return_stats(year_df)
        yearly_data.append({
            'date': year,
            'profit': profit,
            'volume': vol,
            'roi': roi
        })
    df_yearly = pd.DataFrame(yearly_data)
    df_yearly['date'] = df_yearly['date'].astype(str)
    
    df_tags = DataAnalyst.tag_analysys(df_main, min_bets=min_bets_per_tag)
    exploded_df = get_exploded_df(df_main)
    print("Análise concluída.")
    
    # --- GERAR DASHBOARD PRINCIPAL (index.html) ---
    print("Gerando index.html (Página Principal)...")
    html_main = criar_pagina_principal(
        stats=stats_gerais,
        df_daily=df_daily,
        df_tags=df_tags,
        df_main=df_main,
        df_monthly=df_monthly,
        df_yearly=df_yearly
    )
    main_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(html_main)
    print(f"✅ Página Principal salva em: {main_path}")
    
    # --- GERAR PÁGINA DE TAGS (tags.html) ---
    print(f"Gerando tags.html (Resumo de {len(df_tags)} tags)...")
    if not df_tags.empty:
        html_completo, _ = criar_pagina_tags_resumo(df_tags)
        tags_path = os.path.join(OUTPUT_DIR, 'tags.html')
        
        with open(tags_path, 'w', encoding='utf-8') as f:
            f.write(html_completo)
        print(f"✅ Página de Tags salva em: {tags_path}")
    else:
        print(f"... Pulado (Nenhuma tag atingiu o mínimo de {min_bets_per_tag} apostas).")
    
    # --- GERAR PÁGINAS DE DETALHE (tags/nome_da_tag.html) ---
    print(f"Gerando {len(df_tags)} páginas de detalhe de tags...")
    count = 0
    apostas_count = 0
    if not df_tags.empty:
        for _, row in df_tags.iterrows():
            tag_name = row['tag']
            df_tag_especifica = exploded_df[exploded_df['tag'] == tag_name]
            
            if df_tag_especifica.empty:
                continue
                
            df_daily_tag = DataAnalyst.daily_balance(df_tag_especifica)
            df_daily_tag['date'] = df_daily_tag['date'].astype(str) 
            
            # Criar página de detalhe
            html_detalhe = criar_pagina_detalhe_tag(df_tag_especifica, tag_name, df_daily_tag)
            
            safe_filename = "".join(c if c.isalnum() else "_" for c in tag_name) + ".html"
            detail_path = os.path.join(TAGS_DIR, safe_filename)
            
            with open(detail_path, 'w', encoding='utf-8') as f:
                f.write(html_detalhe)
            count += 1
            
            # Criar página de apostas com todas as colunas
            apostas_html = criar_pagina_apostas_tag(df_tag_especifica, tag_name)
            apostas_filename = safe_filename.replace(".html", "_apostas.html")
            apostas_path = os.path.join(TAGS_DIR, apostas_filename)
            
            with open(apostas_path, 'w', encoding='utf-8') as f:
                f.write(apostas_html)
            apostas_count += 1
    print(f"✅ {count} Páginas de detalhe salvas em: {TAGS_DIR}")
    print(f"✅ {apostas_count} Páginas de apostas salvas em: {TAGS_DIR}")
    
    print("\n✅ Processo concluído com sucesso!")
    
    # Retornar informações
    result = {
        'output_dir': OUTPUT_DIR,
        'main_path': main_path,
        'tags_dir': TAGS_DIR
    }
    
    # Se auto_open, iniciar servidor e abrir navegador
    if auto_open:
        print("\n" + "="*70)
        print("🚀 Dashboard pronto! Iniciando servidor...")
        print("="*70)
        
        port_to_use = 8000
        
        def start_server():
            global _port
            try:
                _start_temp_server(OUTPUT_DIR, port_to_use)
            except Exception as e:
                print(f"❌ Erro ao iniciar servidor: {e}")
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Aguardar servidor iniciar
        time.sleep(1.5)
        
        # Usar a porta que foi atribuída
        port = _port if _port else port_to_use
        url = f'http://localhost:{port}/index.html'
        result['url'] = url
        result['port'] = port
        
        # Abrir no navegador
        webbrowser.open(url)
        print(f"🌐 Dashboard aberto no navegador!")
        print(f"   URL: {url}")
        print(f"   Pressione Ctrl+C para fechar o servidor")
        print("="*70)
        
        # Manter o script rodando
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Encerrando servidor...")
            global _httpd
            if _httpd:
                try:
                    _httpd.shutdown()
                except:
                    pass
            print("👋 Encerrado!")
            sys.exit(0)
    else:
        # Se não auto_open, apenas imprimir link de arquivo
        try:
            file_url = f'file://{os.path.abspath(main_path)}'
            
            print("\n" + "="*70)
            print("🚀 Dashboard pronto! Copie o link abaixo e cole no seu navegador:")
            print(f"\n{file_url}\n")
            print("="*70)
            print(f"(Os ficheiros do dashboard estão salvos em: {OUTPUT_DIR})")
        except Exception as e:
            print(f"Ocorreu um erro ao tentar gerar o link do ficheiro: {e}")
    
    return result

# --- Execução quando chamado como script ---
if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DATA_FILE = os.path.join(BASE_DIR, 'sports_data.csv') 
    MIN_BETS_PER_TAG = 50 
    
    print(f"Carregando dados de '{DATA_FILE}'...")
    try:
        df_main = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{DATA_FILE}' não encontrado.")
        print(f"Certifique-se que 'sports_data.csv' está em: {BASE_DIR}")
        sys.exit(1)
    
    # Criar dashboard automaticamente
    criar_dashboard(df_main, min_bets_per_tag=MIN_BETS_PER_TAG)