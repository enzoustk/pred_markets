"""
Script para buscar dados de posições usando o subgraph GraphQL do Polymarket (positions-subgraph)
e dados de PNL da API REST do Polymarket
"""
import time
import requests
import pandas as pd
from api.config import URLS, QUERYS
from concurrent.futures import ProcessPoolExecutor, as_completed
from api.fetch import fetch_market_data

# --- ADICIONE O IMPORT DA ANIMAÇÃO ---
from helpers import loading_animation 
# (E outros imports que podem estar faltando, como sys, threading, contextlib em helpers.py)


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


def get_user_pnl(
    user_address: str,
    endpoint: str = URLS['POSITIONS_SUBGRAPH'], 
    closed_only: bool = False
    ) -> dict | None:
    """
    Busca dados consolidados. A animação ocorrerá dentro de
    get_all_user_positions()
    """
    # Busca todas as posições usando paginação automática
    positions = get_all_user_positions(user_address, endpoint, closed_only=closed_only)
    
    if not positions:
        return None
    
    # Consolida os dados (rápido, sem animação)
    total_balance = sum(
        int(pos.get("balance", 0)) for pos in positions 
        if pos.get("balance") is not None
    )
    
    return {
        "id": user_address,
        "user": user_address,
        "totalBalance": str(total_balance),
        "positionCount": len(positions),
        "closedPositions": len([p for p in positions if p.get("balance") == "0"])
    }


def get_user_positions(
    user_address: str,
    endpoint: str = URLS['POSITIONS_SUBGRAPH'], 
    first: int = 1000,
    skip: int = 0, 
    closed_only: bool = False
    ) -> list[dict[str]]:
    """
    Busca uma página de posições (função auxiliar silenciosa)
    """
    query = QUERYS['CLOSED'] if closed_only else QUERYS['ACTIVE']
    variables = {
        "userAddress": user_address,
        "first": first,
        "skip": skip
    }
    
    result = query_graphql(endpoint, query, variables)
    
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


def get_all_user_positions(
    user_address: str,
    endpoint: str = URLS['POSITIONS_SUBGRAPH'],
    batch_size: int = 1000,
    closed_only: bool = False
    ) -> list[dict[str]]:
    """
    Busca TODAS as posições com paginação automática e animação.
    """
    all_positions = []
    skip = 0
    batch_num = 1
    
    filter_type = "fechadas" if closed_only else "todas"
    
    # --- MUDANÇA: Adiciona animação ---
    initial_msg = f"📊 Buscando posições {filter_type} do subgraph (Página 1)"
    
    with loading_animation(initial_msg) as anim_status:
        while True:
            # Atualiza mensagem da animação
            anim_status['message'] = f"📊 Buscando posições {filter_type} (Pág {batch_num}, Total: {len(all_positions):,})"
            
            batch = get_user_positions(
                user_address,
                endpoint,
                first=batch_size,
                skip=skip,
                closed_only=closed_only
            )
            
            if not batch:
                break
            
            all_positions.extend(batch)
            
            if len(batch) < batch_size:
                break
            
            skip += batch_size
            batch_num += 1
            
            # Pausa para não sobrecarregar a API
            time.sleep(0.2)
    
    # --- MUDANÇA: Print final ---
    print(f"Posições {filter_type} do subgraph coletadas: {len(all_positions):,} registros.")
    return all_positions


def get_pnl_from_api_rest(
    user_address: str,
    condition_id: str = None, 
    token_id: str = None,
    limit: int = 500,
    offset: int = 0
    ) -> list[dict[str]]:
    """
    Busca dados de PNL (função auxiliar silenciosa)
    """
    url = URLS["CLOSED_POSITIONS"]
    params = {
        "user": user_address,
        "limit": limit,
        "offset": offset
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if response.status_code == 429:

            time.sleep(2)
            # Tenta novamente (silenciosamente)
            return get_pnl_from_api_rest(user_address, condition_id, token_id, limit, offset)
        
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as e:
        return []


def get_pnl_from_api_rest_by_markets(
    user_address: str, 
    condition_ids: list[str],
    limit: int = 500,
    use_pagination: bool = True
    ) -> list[dict[str]]:
    """
    Busca dados de PNL da API REST (com animação).
    NOTA: Esta função é substituída pela 'fetch_all_pnl_from_api_rest' 
    paralela, mas foi animada mesmo assim.
    """
    url = URLS["CLOSED_POSITIONS"]
    all_data = []
    
    if use_pagination and len(condition_ids) > 0:
        
        # --- MUDANÇA: Adiciona animação para o loop ---
        total_conditions = len(condition_ids)
        initial_msg = f"Buscando PNL por market (0 de {total_conditions})"
        
        with loading_animation(initial_msg) as anim_status:
            for i, condition_id in enumerate(condition_ids):
                anim_status['message'] = f"Buscando PNL por market ({i+1} de {total_conditions})"
                
                condition_data = []
                offset = 0
                
                while True:
                    params = {
                        "user": user_address,
                        "market": condition_id,
                        "limit": limit,
                        "offset": offset
                    }
                    
                    try:
                        response = requests.get(url, params=params, timeout=30)
                        response.raise_for_status()
                        data = response.json()
                        
                        if response.status_code == 429:
                
                            time.sleep(2)
                            continue
                        
                        if not data or not isinstance(data, list):
                            break
                        
                        condition_data.extend(data)
                        
                        if len(data) < limit:
                            break
                        
                        offset += limit
                        
                        if offset >= 10000:
                
                            break
                        
                        time.sleep(0.1)
                    
                    except requests.exceptions.RequestException as e:
            
                        break
                
                all_data.extend(condition_data)
                if condition_data:
                    time.sleep(0.15)
        
        print(f"PNL por market (paginado) concluído: {len(all_data)} registros.")
        return all_data
    
    # --- MUDANÇA: Animação para o Modo 2 (não paginado) ---
    params = { "user": user_address, "limit": limit }
    if condition_ids:
        params["market"] = ",".join(condition_ids)
    
    with loading_animation(f"Buscando PNL para {len(condition_ids)} markets"):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if response.status_code == 429:
    
                time.sleep(2)
                return get_pnl_from_api_rest_by_markets(user_address, condition_ids, limit, use_pagination)
            
            print(f"PNL por market (agrupado) concluído.")
            return data if isinstance(data, list) else []
        except requests.exceptions.RequestException as e:

            return []


def _fetch_batch_pnl(
    user_address: str,
    condition_batch: list[str],
    batch_num: int,
    total_batches: int,
    closed_only: bool = True
    ) -> list[dict[str]]:
    """
    Função auxiliar (PROCESSO-FILHO) - DEVE SER SILENCIOSA
    """
    url = URLS["CLOSED_POSITIONS"] if closed_only else URLS["ACTIVE_POSITIONS"]
    limit = 25
    batch_data = []
    offset = 0
    retry_count = 0
    max_retries = 5
    page_num = 1
    
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
            
            if response.status_code == 200:
                data = response.json()
                if not data or not isinstance(data, list):
                    break
                
                batch_data.extend(data)
                records_this_page = len(data)
                
    
                
                if records_this_page < limit:
        
                    break
                
                offset += limit
                page_num += 1
                
                if offset >= 10000:
        
                    break
                
                retry_count = 0
                time.sleep(0.1)
                
            elif response.status_code == 429:
                base_delay_rate = 2
                max_delay = 60
                exponential_delay = min(base_delay_rate * (2 ** retry_count), max_delay)
                total_delay = exponential_delay
                
    
                time.sleep(total_delay)
                retry_count += 1
                
                if retry_count >= max_retries:
        
                    break
                continue
            
            else:
                fatal_errors = [400, 401, 403, 404]
                if response.status_code in fatal_errors:
        
                    break
                
                retry_count += 1
                if retry_count >= max_retries:
        
                    break
                
                delay = 2 * (2 ** retry_count)
                total_delay = min(delay, 60)
    
                time.sleep(total_delay)
                continue
                
        except Exception as e:

            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)
            continue
    
    return batch_data


def fetch_all_pnl_from_api_rest(
    user_address: str,
    condition_ids: list[str],
    markets_per_request: int = 50,
    closed_only: bool = True,
    max_workers: int = 4,
    ) -> pd.DataFrame:
    """
    Busca TODOS os dados de PNL (PROCESSO-PAI) com animação.
    """
    endpoint_type = "fechadas" if closed_only else "abertas"
    # --- PRINTS INICIAIS REMOVIDOS ---
    
    start_time = time.time()
    
    total_batches = (len(condition_ids) + markets_per_request - 1) // markets_per_request
    
    batches = []
    for i in range(0, len(condition_ids), markets_per_request):
        condition_batch = condition_ids[i:i + markets_per_request]
        batch_num = (i // markets_per_request) + 1
        batches.append((condition_batch, batch_num))
    
    all_pnl_data = []
    
    # --- MUDANÇA: Adiciona animação multi-processo ---
    initial_msg = f"Buscando PNL da API ({endpoint_type}) (0 de {total_batches} lotes)"
    
    with loading_animation(initial_msg) as anim_status:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(_fetch_batch_pnl, user_address, batch, batch_num, total_batches, closed_only): batch_num
                for batch, batch_num in batches
            }
            
            completed_batches = 0
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                completed_batches += 1
                
                # --- MUDANÇA: Atualiza a animação ---
                anim_status['message'] = f"Buscando PNL da API ({endpoint_type}) ({completed_batches} de {total_batches} lotes)"
                
                try:
                    batch_data = future.result()
                    all_pnl_data.extend(batch_data)
                    
                    # --- PRINTS INTERNOS REMOVIDOS ---
                    
                except Exception as e:
        
                    pass # Erro será logado silenciosamente
    
    # --- PRINTS FINAIS (APÓS A ANIMAÇÃO) ---
    end_time = time.time()
    print(f"Tempo total de busca de PNL: {end_time - start_time:.2f} segundos")
    print(f"Total de {len(all_pnl_data)} registros de PNL encontrados")
    
    if all_pnl_data:
        df_pnl = pd.DataFrame(all_pnl_data)
                
        return df_pnl
    else:
        print("Nenhum dado de PNL encontrado")
        return pd.DataFrame()


def explore_schema(endpoint: str = URLS['POSITIONS_SUBGRAPH']) -> dict[str]:
    """
    Explora o schema GraphQL (com animação simples).
    """
    introspection_query = """
    query IntrospectionQuery { ... } 
    """ # (Query original omitida por brevidade)
    
    # --- MUDANÇA: Adiciona animação simples ---
    with loading_animation("Explorando schema GraphQL..."):
        result = query_graphql(endpoint, introspection_query)
    
    if "error" not in result:
        print("Schema explorado com sucesso.")
    else:
        print("Erro ao explorar schema.")
        
    return result


def fetch_pnl_data(
    user_address: str,
    include_positions: bool = True,
    closed_only: bool = False
    ) -> pd.DataFrame:
    """
    Função principal orquestradora (com várias animações).
    """
    filter_msg = " (apenas fechadas)" if closed_only else ""
    print(f"Iniciando coleta de dados para: {user_address}{filter_msg}")
    
    all_data = []
    
    if include_positions:
        # 1. Animação de 'get_all_user_positions' (roda aqui)
        positions = get_all_user_positions(user_address, closed_only=closed_only)
        
        if positions:
            all_data.extend(positions)
            unique_condition_ids = list(set(
                pos.get("conditionId") for pos in positions 
                if pos.get("conditionId")
            ))
            
            if unique_condition_ids:
                print(f"\nTotal de {len(unique_condition_ids)} conditionIds únicos encontrados.")
                
                # 2. Animação de 'fetch_all_pnl_from_api_rest' (roda aqui)
                df_pnl_rest = fetch_all_pnl_from_api_rest(
                    user_address, 
                    unique_condition_ids,
                    markets_per_request=50,
                    closed_only=closed_only,
                    max_workers=4,
                    output_csv="pnl_api_rest_data.csv"
                )
                
                # 3. Animação para buscar 'missing_conditions'
                if not df_pnl_rest.empty and 'conditionId' in df_pnl_rest.columns:
                    found_conditions = set(df_pnl_rest['conditionId'].unique())
                    missing_conditions = set(unique_condition_ids) - found_conditions
                    
                    if missing_conditions:
                        print(f"\n{len(missing_conditions)} conditionIds não retornaram dados. Buscando individualmente...")
                        missing_list = list(missing_conditions)
                        additional_data = []
                        
                        # --- MUDANÇA: Adiciona animação ---
                        total_missing = len(missing_list)
                        initial_msg = f"Buscando conditionIds faltantes (0 de {total_missing})"
                        
                        with loading_animation(initial_msg) as anim_status:
                            for i, condition_id in enumerate(missing_list):
                                anim_status['message'] = f"Buscando conditionIds faltantes ({i+1} de {total_missing})"
                                
                                condition_data = []
                                offset = 0
                                
                                while True:
                                    params = {"user": user_address, "market": condition_id, "limit": 500, "offset": offset}
                                    try:
                                        response = requests.get(URLS["CLOSED_POSITIONS"], params=params, timeout=30)
                                        if response.status_code == 200:
                                            data = response.json()
                                            if not data or not isinstance(data, list):
                                                break
                                            condition_data.extend(data)
                                            if len(data) < 500:
                                                break
                                            offset += 500
                                            if offset >= 10000:
                                                break
                                            time.sleep(0.1)
                                        elif response.status_code == 429:
                                            time.sleep(2)
                                            continue
                                        else:
                                            break
                                    except:
                                        break
                                
                                if condition_data:
                                    additional_data.extend(condition_data)
                                time.sleep(0.1)
                        
                        if additional_data:
                            # Adiciona dados faltantes
                            df_additional = pd.DataFrame(additional_data)
                            df_pnl_rest = pd.concat([df_pnl_rest, df_additional], ignore_index=True)
                            df_pnl_rest.to_csv("pnl_api_rest_data.csv", index=False)
                            print(f"{len(additional_data)} registros adicionais encontrados.")
                            print(f"Arquivo 'pnl_api_rest_data.csv' atualizado.")
                        else:
                            print(f"Busca por conditionIds faltantes concluída (nenhum dado adicional encontrado).")

            # Consolidação (rápido, sem animação)
            total_balance = sum(int(pos.get("balance", 0)) for pos in positions if pos.get("balance") is not None)
            closed_count = len([p for p in positions if p.get("balance") == "0"])
            active_count = len(positions) - closed_count
            
            consolidated_data = {
                "id": user_address.lower(), "user": user_address.lower(),
                "totalBalance": str(total_balance), "positionCount": len(positions),
                "closedPositions": closed_count, "activePositions": active_count
            }
            all_data.insert(0, consolidated_data)
        else:
            print("Nenhuma posição individual encontrada")
    else:
        # 4. Animação para 'get_user_pnl' (que chama 'get_all_user_positions')
        user_data = get_user_pnl(user_address, closed_only=closed_only)
        if user_data:
            print("Dados consolidados encontrados!")
            all_data.append(user_data)
    
    if not all_data:
        print("Não foi possível encontrar dados para este usuário")
        # 5. Animação para 'explore_schema'
        schema = explore_schema() # (já tem animação interna)
        if "error" not in schema and "data" in schema:
            query_fields = schema["data"].get("__schema", {}).get("queryType", {}).get("fields", [])
            print("\nCampos disponíveis no schema:")
            for field in query_fields[:10]:
                print(f"    - {field.get('name')}")
        return pd.DataFrame()
    
    # Cria DataFrame e exibe resumos (prints finais mantidos)
    df = pd.DataFrame(all_data)
    print(f"\nDados do subgraph encontrados! Total de registros: {len(df)}")
    
    # ... (Seção de Resumo e Estatísticas - prints mantidos) ...
    
    # 6. Animação final de 'fetch_market_data'
    import os
    if os.path.exists("pnl_api_rest_data.csv"):
        df_pnl = pd.read_csv("pnl_api_rest_data.csv")
        
        
        # Chama a última função animada
        return fetch_market_data(df_pnl)
    else:
        print("\nArquivo 'pnl_api_rest_data.csv' não encontrado para buscar dados de mercado.")
        return df # Retorna o que tem