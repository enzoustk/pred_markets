import sys
import time
import requests
import pandas as pd
from api.config import URLS
from threading import Semaphore
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_trades_for_single_market_page(
    market_id: str,
    user_address: str,
    semaphore: Semaphore,
    taker_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    max_retries: int = 3
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Busca uma ÚNICA PÁGINA de trades para um ÚNICO mercado.
    Esta versão usa um loop 'while' para lidar corretamente com
    rate limits sem causar deadlock no semáforo.
    """
    url = URLS["TRADES"]
    params = {
        "limit": limit, "offset": offset, "user": user_address,
        "market": market_id, "takerOnly": "true" if taker_only else "false"
    }
    
    internal_retry_count = 0
    
    # Adquire o semáforo UMA VEZ no início.
    semaphore.acquire()
    
    try:
        while internal_retry_count <= max_retries:
            try:
                # Tentar fazer a requisição
                response = requests.get(url, params=params, timeout=30)
            
            except requests.exceptions.RequestException as e:
                # 1. Falha de Conexão (ex: a internet caiu)
                print(f"Erro de requisição em {market_id[:10]}...: {e}", file=sys.stderr)
                internal_retry_count += 1
                if internal_retry_count > max_retries:
                    print(f"Falha de conexão final em {market_id[:10]}...", file=sys.stderr)
                    return ([], False) # Falha
                time.sleep(5) # Espera 5s antes de retentar conexão
                continue # Tenta o 'while' de novo
            
            # 2. Sucesso na Requisição (analisar o status)
            
            if response.status_code == 200:
                # 2a. SUCESSO TOTAL (200 OK)
                data = response.json()
                result = data if isinstance(data, list) else data.get('trades', [])
                return (result, True) # Sucesso! Sai da função.
            
            elif response.status_code == 429:
                # 2b. RATE LIMIT (429)
                internal_retry_count += 1
                if internal_retry_count > max_retries:
                    print(f"❌ Rate limit final (desistindo) em {market_id[:10]}...", file=sys.stderr)
                    return ([], False) # Falha
                
                delay = min(10 + (2 ** internal_retry_count), 30)
                print(f"Rate limit em {market_id[:10]}... (worker {internal_retry_count}/{max_retries}), aguardando {delay}s", file=sys.stderr)
                
                # DORMIR *DENTRO* DO SEMÁFORO
                # Isso força o script a desacelerar globalmente.
                time.sleep(delay)
                
                # Tentar o 'while' de novo
                continue 
            
            else:
                # 2c. Outros Erros (404, 500, etc)
                print(f"Erro HTTP {response.status_code} em {market_id[:10]}...", file=sys.stderr)
                # Não adianta retentar, falha permanente
                return ([], False)
        
        # Se saiu do loop (max_retries atingido)
        return ([], False)

    finally:
        # QUALQUER que seja o resultado (return True ou False),
        # o 'finally' garante que o semáforo será liberado
        # quando a função terminar.
        semaphore.release()


def fetch_trades_for_market_complete(
    market_id: str,
    semaphore: Semaphore,
    user_address: str,
    taker_only: bool = False,
    limit: int = 100,
    max_retries: int = 3
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Busca TODOS os trades para um ÚNICO mercado, usando paginação completa.
    Retorna (all_trades_list, overall_success_flag)
    """
    all_trades = []
    offset = 0
    page_num = 1
    overall_success = True 
    
    while True:
        # A função de página agora retorna (trades, success)
        page_trades, success = fetch_trades_for_single_market_page(
            market_id=market_id,
            semaphore=semaphore,
            user_address=user_address,
            taker_only=taker_only,
            limit=limit,
            offset=offset,
            max_retries=max_retries
        )
        
        # Se qualquer página falhar, marcamos o mercado todo como falho e saímos
        if not success:
            overall_success = False; break 
        
        # Página vazia, fim normal
        if not page_trades: break 
        
        all_trades.extend(page_trades)
        
        # Fim normal
        if len(page_trades) < limit: break 
        
        offset += limit
        page_num += 1
        time.sleep(0.1)
    
    return (all_trades, overall_success)


def _run_market_processing_loop(
    semaphore: Semaphore,
    taker_only: bool,
    max_workers: int,
    user_address: str,
    markets_to_process: List[str],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Helper function para rodar o loop de processamento paralelo.
    Retorna (lista_de_trades_coletados, lista_de_mercados_que_falharam)
    """
    all_trades_accumulator = []
    failed_markets_accumulator = []
    completed_count = 0
    total_to_process = len(markets_to_process)

    # Wrapper que chama a função 'complete' e retorna o status
    def process_single_market_wrapper(
            market_id: str, 
            # (Não precisa de 'semaphore: Semaphore' aqui)
            ) -> Tuple[str, List[Dict[str, Any]], bool]:
            
            # 3. Este 'semaphore' é pego do escopo "mãe" (closure)
            trades, success = fetch_trades_for_market_complete(
                semaphore=semaphore, 
                market_id=market_id,
                user_address=user_address,
                taker_only=taker_only
            )
            return (market_id, trades, success)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_market = {
            executor.submit(process_single_market_wrapper, market_id): market_id
            for market_id in markets_to_process
        }
        
        for future in as_completed(future_to_market):
            market_id = future_to_market[future]
            completed_count += 1
            progress_prefix = f"[{completed_count}/{total_to_process}]"
            
            try:
                result_market_id, trades, success = future.result()
                
                if success:
                    if trades:
                        for trade in trades:
                            trade['market_id_v3'] = result_market_id
                        all_trades_accumulator.extend(trades)
                        print(f"{progress_prefix} {result_market_id[:20]}...: {len(trades)} trades")
                    else:
                        print(f" -- {progress_prefix} {result_market_id[:20]}...: 0 trades")
                else:
                    # Falha controlada (ex: rate limit)
                    print(f"{progress_prefix} Falha controlada em {result_market_id[:20]}... (marcado para retentativa)")
                    failed_markets_accumulator.append(result_market_id)

            except Exception as e:
                # Falha inesperada (exceção no código)
                print(f"{progress_prefix} Erro CRÍTICO em {market_id[:20]}...: {e}")
                failed_markets_accumulator.append(market_id)
    
    return (all_trades_accumulator, failed_markets_accumulator)


def fetch_all_trades_parallel(
    df: pd.DataFrame,
    semaphore: Semaphore,
    user_address: Optional[str] = None,
    taker_only: bool = False,
    max_workers: int = 20,
) -> pd.DataFrame:
    
    """
    Função principal que orquestra a busca e a retentativa.
    """
        
    # Entender tamanho dos dados
    condition_ids = df['conditionId'].dropna().unique().tolist()
    total_markets = len(condition_ids)
    
    # Ligar o timer
    start_time = time.time()
        
    # Roda a primeira vez
    all_trades, failed_markets = _run_market_processing_loop(
        semaphore=semaphore,
        user_address=user_address,
        taker_only=taker_only,
        max_workers=max_workers,
        markets_to_process=condition_ids,
    )
    
    # Puxar novamente os que falharam
    if failed_markets:
        print(f"Retentando {len(failed_markets)} mercados que falharam...")
       
        
        # Roda o loop novamente, apenas com os mercados que falharam
        retried_trades, final_failed_markets = _run_market_processing_loop(
            semaphore=semaphore,
            markets_to_process=failed_markets,
            user_address=user_address,
            taker_only=taker_only,
            max_workers=max_workers
        )
        
        # Adiciona os trades da retentativa à lista principal
        all_trades.extend(retried_trades)
        
        if final_failed_markets:
            print(f"{len(final_failed_markets)} mercados falharam permanentemente:")
            for market_id in final_failed_markets: print(f"  - {market_id}")
          
        else:
            print(f"\n Sucesso! Todos os mercados que falharam foram processados na retentativa.")
    else:
        print(f"\nSucesso! Nenhum mercado falhou na primeira rodada.")


    elapsed_time = time.time() - start_time

    print(f"Tempo total: {elapsed_time:.2f}s ({elapsed_time/60:.2f} min)") 

    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        print(f"✅ DataFrame criado! Shape: {trades_df.shape}")
        return trades_df
    else:
        print("⚠️ Nenhum trade encontrado.")
        return pd.DataFrame()


def fetch_clv(
    user_address: str,
    df: pd.DataFrame,
    max_workers: int = 25,
    taker_only: bool = False,
    simultaneous_requests: int = 10,
):
    """
    Função principal -> Consolida tudo
    """
    
    return fetch_all_trades_parallel(
        df=df,
        user_address=user_address,
        taker_only=taker_only,
        max_workers=max_workers,
        semaphore=Semaphore(simultaneous_requests)
    )
