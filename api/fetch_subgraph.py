import time
import requests
import pandas as pd
from api.config import URLS, QUERYS
from helpers import loading_animation 
from api.fetch import fetch_market_data
from concurrent.futures import ProcessPoolExecutor, as_completed


def query_graphql(
    endpoint: str,
    query: str,
    variables: dict | None = None
    ) -> dict:
    """
    Executa uma query GraphQL (agora silenciosa em caso de erro)
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_all_user_positions(
    user_address: str,
    endpoint: str = URLS['POSITIONS_SUBGRAPH'],
    batch_size: int = 1000,
    ) -> list[dict[str]]:
    """
    Busca TODAS as posições com paginação automática e animação.
    """
    all_positions = []
    skip = 0
    batch_num = 1
    
    initial_msg = f"Buscando posições do subgraph (Página 1)"
    
    with loading_animation(initial_msg) as anim_status:
        while True:
            anim_status['message'] = f"Buscando posições (Pág {batch_num}, Total: {len(all_positions):,})"
            
            batch = get_user_positions(
                user_address,
                endpoint,
                first=batch_size,
                skip=skip,
            )
            
            if not batch:
                break
            
            all_positions.extend(batch)
            
            if len(batch) < batch_size:
                break
            
            skip += batch_size
            batch_num += 1
            
            time.sleep(0.2)
    
    # --- MUDANÇA: Print final ---
    print(f"Posições do subgraph coletadas: {len(all_positions):,} registros.")
    
    
    # Aqui, temos uma lista de dicts, contendo tanto posições abertas quanto fechadas.
    return all_positions


def get_user_positions(
    user_address: str,
    endpoint: str = URLS['POSITIONS_SUBGRAPH'], 
    first: int = 1000,
    skip: int = 0, 
    ) -> list[dict[str]]:
    """
    Busca uma página de posições (função auxiliar silenciosa)
    """
    variables = {
        "userAddress": user_address,
        "first": first,
        "skip": skip
    }
    
    result = query_graphql(endpoint, QUERYS['ACTIVE'], variables)
    
    if "error" in result:
        return []
    
    if "data" in result and result["data"]:
        positions = result["data"].get("userBalances", [])
        # Transforma os dados
        transformed = []
        for pos in positions:
            transformed.append({
                "id": pos.get("id"),
                "user": pos.get("user"),
                "balance": pos.get("balance", "0"),
                "tokenId": pos.get("asset", {}).get("id"),
                "conditionId": pos.get("asset", {}).get("condition", {}).get("id"),
                "outcomeIndex": pos.get("asset", {}).get("outcomeIndex")
            })
        return transformed
    
    return []


def split_positions(positions: list) -> tuple[list, list]:
    # Recebe as posições "cruas" e separa por ativas e fechadas
    active = []
    closed = []
    
    for pos in positions:
        # Pega o 'balance', tratando como "0" se estiver ausente
        balance_str = pos.get("balance", "0")
        
        if balance_str == "0":
            closed.append(pos)
        else:
            active.append(pos)
            
    return active, closed


def _fetch_batch_pnl(
    user_address: str,
    condition_batch: list[str],
    closed: bool = True,
    limit: int = 25,
    max_retries: int = 5
    ) -> list[dict[str]]:
    """
    Função auxiliar (PROCESSO-FILHO) - DEVE SER SILENCIOSA
    """
    
    # Definições Iniciais
    batch_data = []
    offset = 0
    retry_count = 0
    page_num = 1
    url = URLS["CLOSED_POSITIONS"] if closed \
        else URLS["ACTIVE_POSITIONS"]
    
    # Loop para puxar os dados
    while True:
        market_param = ",".join(condition_batch)
        params = {
            "user": user_address,
            "market": market_param,
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            # Se deu Certo:
            if response.status_code == 200:
                data = response.json()
                if not data or not isinstance(data, list): break
                batch_data.extend(data)
                records_this_page = len(data)
                
                if records_this_page < limit: break
                
                offset += limit
                page_num += 1
                
                if offset >= 10000: break
                retry_count = 0
                
                time.sleep(0.1)
                
            # Lidar com timeout
            elif response.status_code == 429:
                base_delay_rate = 2
                max_delay = 60
                exponential_delay = min(base_delay_rate * (2 ** retry_count), max_delay)
                total_delay = exponential_delay
                
    
                time.sleep(total_delay)
                retry_count += 1
                
                if retry_count >= max_retries: break
                continue
            
            # Lidar com erros comuns
            else:
                fatal_errors = [400, 401, 403, 404]
                if response.status_code in fatal_errors: break
                
                retry_count += 1
                if retry_count >= max_retries: break
                
                delay = 2 * (2 ** retry_count)
                total_delay = min(delay, 60)
    
                time.sleep(total_delay)
                continue
        
        # Se for Algum outro Erro
        except Exception:

            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)
            continue
    
    return batch_data


def fetch_from_rest(
    user_address: str,
    condition_ids: list[str],
    markets_per_request: int = 50,
    closed: bool = True,
    max_workers: int = 4,
    ) -> pd.DataFrame:
    """
    Busca TODOS os dados de PNL (PROCESSO-PAI) com animação.
    """
    

    # Contar o tempo de Procecsso
    start_time = time.time()
    
    # Dividir em Batches
    batches = []
    total_ids = len(condition_ids)
    
    total_batches = ((
        total_ids + markets_per_request - 1)
        // markets_per_request)
    
    
    
    for i in range(0, total_ids, markets_per_request):
        condition_batch = condition_ids[i:i + markets_per_request]
        batch_num = (i // markets_per_request) + 1
        batches.append((condition_batch, batch_num))
    
    all_pnl_data = []
    
    
    initial_msg = f"Buscando PNL da API (0 de {total_batches} lotes)"
    
    # Começar de Fato o Processamento
    with loading_animation(initial_msg) as anim_status:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(
                    _fetch_batch_pnl,
                    user_address,
                    batch,
                    closed
                    ): batch_num
                for batch, batch_num in batches
            }
            
            completed_batches = 0
            
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                completed_batches += 1
                
                # --- MUDANÇA: Atualiza a animação ---
                anim_status['message'] = f"Buscando PNL da API ({completed_batches} de {total_batches} lotes)"
                
                try:
                    batch_data = future.result()
                    all_pnl_data.extend(batch_data)
                    
                    
                    
                except Exception as e:
                    # TODO: Printar erro para facilitar
                    pass 
    
   
    end_time = time.time()
    print(f"Tempo total de busca de PNL: {end_time - start_time:.2f} segundos")
    print(f"Total de {len(all_pnl_data)} registros de PNL encontrados")
    
    if all_pnl_data:
        df_pnl = pd.DataFrame(all_pnl_data)
                
        return df_pnl
    else:
        print("Nenhum dado de PNL encontrado")
        return pd.DataFrame()


def fetch_missing(
    user_address: str,
    missing: set,
    closed: bool,
    ):
    
    url = URLS["CLOSED_POSITIONS"] if closed \
        else URLS["ACTIVE_POSITIONS"]
    
    
    missing_list = list(missing)
    total_missing = len(missing_list)
    print(f"{total_missing} conditionIds não retornaram dados. Buscando individualmente...")
    additional_data = []

    initial_msg = f"Buscando conditionIds faltantes (0 de {total_missing})"
    
    with loading_animation(initial_msg) as anim_status:
        for i, condition_id in enumerate(missing_list):
            
            anim_status['message'] = f"Buscando conditionIds faltantes ({i+1} de {total_missing})"
            
            # Definições Iniciais
            condition_data = []
            offset = 0
            
            while True:
                params = {
                    "user": user_address,
                    "market": condition_id,
                    "limit": 500,
                    "offset": offset
                }
                try:
                    response = requests.get(url, params=params, timeout=30)  
                    
                    # Se deu Certo -> Mais dados
                    if response.status_code == 200:
                        data = response.json()
                        
                        if not data or not isinstance(data, list): 
                            break  # Condição de Saída
                        
                        # Aumenta os dados
                        condition_data.extend(data)
                        
                        if len(data) < 500: break # Menor que o máx -> Acabou
                        
                        # Se não acabou, aumenta o offset
                        offset += 500
                        
                        # Condição de parada do Offset
                        if offset >= 10000: break
                        
                        # Descansar né
                        time.sleep(0.1)
                    
                    # Timeout
                    elif response.status_code == 429:
                        time.sleep(2)
                        continue
                    
                    # Algum erro
                    else: break    
                
                except: break
            
            if condition_data:
                additional_data.extend(condition_data)
                time.sleep(0.1)
            
        if not additional_data:
            print(f"Busca por conditionIds faltantes concluída (nenhum dado adicional encontrado).")
            return pd.DataFrame()

        return pd.DataFrame(additional_data)
        
 
def fetch_positions_from_rest(
    user_address: str,
    positions: list,
    closed: bool
    ):
    
    # Listar os condition_ids a buscar
    unique_condition_ids = list(
        set(
        pos.get("conditionId") for pos in positions 
        if pos.get("conditionId")
        )
    )
    
    print('Tipo: ', 'Fechadas' if closed else 'Ativas')
    print(f"Total de {len(unique_condition_ids)} conditionIds únicos")
    
    # Agora, puxar de fato os dados da API Rest:
    df_rest = fetch_from_rest(
        user_address, 
        unique_condition_ids,
        markets_per_request=50,
        closed=closed,
        max_workers=4,
    )
    
    # Buscar dados Faltantes:
    if not df_rest.empty and 'conditionId' in df_rest.columns:
        found = set(df_rest['conditionId'].unique())
        missing = set(unique_condition_ids) - found
        
        # De fato buscar:
        if missing:
            missing_df = fetch_missing(user_address, missing, closed)
            
            if not missing_df.empty:
                df_rest = pd.concat([df_rest, missing_df])
    
    
    # Puxar metadados de mercado
    return fetch_market_data(df_rest)
                

            
    
def fetch_pnl_data(
    user_address: str,
    ) -> pd.DataFrame:
    """
    Função principal orquestradora (com várias animações).
    """
    print(f"Iniciando coleta de dados para: {user_address}")
    
    
    # Buscar Todas as Posições
    active_positions, closed_positions = split_positions(
        get_all_user_positions(user_address)
    )
    
    # Aqui começa a lógica de puxar dados em rest
    # Retorna em pd.DataFrame
    active_df = fetch_positions_from_rest(user_address,active_positions, closed=False)
    closed_df = fetch_positions_from_rest(user_address, closed_positions, closed=True)
    
    return closed_df, active_df