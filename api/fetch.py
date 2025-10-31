import time
import random
import requests
import pandas as pd
from api.config import URLS
from typing import List, Dict, Any
from data.handle import assertion_active
from concurrent.futures import ProcessPoolExecutor, as_completed

def page(
    url: str,
    offset: int,
    user_address: str,
    limit: int = 500,
    process_id: int = None,
    retry_count: int = 0,
    ) -> Dict[str, Any]:
    
    """
    Busca uma página específica de dados;
    Tratamento isolado de rate limit por processo;
    """
    
    params = {
        "limit": limit,
        "offset": offset,
        "user": user_address
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        # se der certo
        if response.status_code == 200:
            data = response.json()
            return {"offset": offset, "data": data, "success": True, "retry_count": retry_count}
        
        # se der too many requests
        elif response.status_code == 429:
            base_delay = 2  
            max_delay = 60  
            
            exponential_delay = min(base_delay * (2 ** retry_count), max_delay)
            # Adiciona jitter baseado no process_id para tornar único
            jitter = random.uniform(0.1, 0.5) * (process_id or 1)
            total_delay = exponential_delay + jitter
            
            process_info = f"Processo {process_id}" if process_id else "Desconhecido"
            print(f"⚠️  {process_info}: Rate limit no offset {offset}, aguardando {total_delay:.2f}s (tentativa {retry_count + 1})...")
            time.sleep(total_delay)
            
            return {"offset": offset, "data": [], "success": False, "error": "Rate limited", "retry_count": retry_count}
        
        else:
            return {"offset": offset, "data": [], "success": False, "error": response.status_code, "retry_count": retry_count}
    
    except Exception as e:
        print(f'Error Puxando página: {e}')
        return {"offset": offset,"data": [],"success": False,"error": str(e),"retry_count": retry_count}

def all_data_parallel(
    url: str,
    user_address: str,
    num_processes: int,
    records_per_process: int = 250,
    ):
    
    """
    Busca todos os dados usando processos paralelos configuráveis
    "Organizador" Principal, chama o fetch_range para cada processo
    """
    
    # Setar os Ranges
    ranges = []
    for i in range(num_processes):
        start_offset = i * records_per_process
        end_offset = (i + 1) * records_per_process
        process_id = i + 1
        ranges.append((start_offset, end_offset, process_id))
    
    
    start_time = time.time()
    all_data = []
    
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submete todas as tarefas
        futures = []
        for start_offset, end_offset, process_id in ranges:
            future = executor.submit(
                fetch_range, # função
                url, #arg1
                user_address, #arg2
                start_offset, #arg3
                end_offset, #arg4
                process_id, #arg5
                num_processes
                )
            futures.append(future)
        
        # Coleta os resultados conforme vão chegando
        for future in as_completed(futures):
            try:
                process_data = future.result()
                all_data.extend(process_data)
                print(f"Processo concluído: {len(process_data):,} registros coletados")
            except Exception as e:
                print(f"Erro em processo: {e}")
    
    end_time = time.time()
    print(f"Tempo total de execução: {end_time - start_time:.2f} segundos")
    print(f"Total de registros obtidos: {len(all_data):,}")
    
    return all_data

def fetch_range(
    url: str,
    user_address: str,
    start_offset: int,
    end_offset: int,
    process_id: int,
    num_processes: int,
    max_limit: int = 500
    ) -> List[Dict[str, Any]]:
    """
    Busca um fetch_range específico de offsets com tratamento isolado de rate limit
    Chama o page várias vezes até coletar tudo o que precisa
    TODO: Melhorar lógica de ultrapassagem de "fetch_range"
    """
    print(f"Processo {process_id}: Buscando offsets {start_offset:,} a {end_offset:,}")
    
    initial_delay = random.uniform(0.1, 0.5) * process_id
    if initial_delay > 0: time.sleep(initial_delay) # Delay para jittering
    
    all_data = []
    current_offset = start_offset
    
    base_delay = 0.3 + (process_id * 0.1) 
    
    while True:
        if process_id < num_processes and current_offset >= end_offset:
            print(f"🏁 Processo {process_id}: Limite atingido no offset {current_offset} (limite: {end_offset})")
            break
        
        if process_id < num_processes:
            # Limita a requisição para não ultrapassar o end_offset
            max_offset_allowed = end_offset - current_offset
            if max_offset_allowed <= 0:
                break  # Já atingiu o limite
            max_limit = min(max_limit, max_offset_allowed)
        
        # Contador de tentativas de retry para este offset específico
        retry_count = 0
        max_retries = 5  
        
        while retry_count < max_retries:
            
            result = page(
                url=url,
                user_address=user_address,
                offset=current_offset,
                limit=max_limit,
                process_id=process_id,
                retry_count=retry_count
                )
            
            if result["success"] and result["data"]:

                all_data.extend(result["data"])                
                current_offset += len(result["data"])
                
                if process_id < num_processes and current_offset > end_offset:
                    # Para processos que não são o último, verifica se ultrapassou o limite após receber dados
                    # (proteção extra caso a API retorne mais registros do que solicitado)
                    excess = current_offset - end_offset
                    if excess > 0:
                        if excess <= len(all_data):
                            all_data = all_data[:-excess]
                            print(f"⚠️  Processo {process_id}: Removendo {excess} registros em excesso (ultrapassou limite {end_offset})")
                        else:
                            print(f"⚠️  Processo {process_id}: Erro - excesso ({excess}) maior que dados coletados ({len(all_data)})")
                            all_data = []
                        current_offset = end_offset
                break  
            
            elif not result["success"]:
                if result.get("error") == "Rate limited":
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Processo {process_id}: Máximo de tentativas atingido após rate limit no offset {current_offset}")
                        break
                    
                    continue
                
                else:
                    print(f"Processo {process_id}: Erro no offset {current_offset}: {result.get('error')}")
                    return all_data  # Retorna o que já coletou em caso de erro grave
            
            else:
                # Dados vazios - chegamos ao fim
                print(f"Processo {process_id}: Fim dos dados no offset {current_offset}")
                return all_data
        
        # Se esgotou todas as tentativas sem sucesso, para este processo
        if retry_count >= max_retries and not (result.get("success") and result.get("data")):
            print(f"Processo {process_id}: Parando após esgotar tentativas no offset {current_offset}")
            break
        
        # Verifica novamente o limite após processar (antes do delay)
        if process_id < num_processes and current_offset >= end_offset:
            break
        
        # Delay único por processo entre requisições (com jitter adicional)
        # Adiciona variação aleatória para evitar sincronização
        jitter = random.uniform(-0.1, 0.1)
        delay = max(0.1, base_delay + jitter)
        time.sleep(delay)
    
    print(f"Processo {process_id}: Concluído - {len(all_data):,} registros")
    return all_data

def user_data(
    user_address: str,
    ):
    """
    Puxa toda as posições para o usuário em um dataframe.
    """    
    
    # Passo 1: Dados de Posições Fechadas:
    closed_data = pd.DataFrame(all_data_parallel(
        user_address=user_address,
        url=URLS['CLOSED_POSITIONS'],
        num_processes=20
        ))
    
    # Passo 2: Dados de posições Ativas:
    active_data = pd.DataFrame(all_data_parallel(
        user_address=user_address,
        url=URLS['ACTIVE_POSITIONS'],
        num_processes=1
    ))
    
    # Retorna o dataframe com os dados 
    
    return fetch_market_data(assertion_active(active_df=active_data, closed_df=closed_data))

def fetch_market_data(
    df: pd.DataFrame,
    batch_size: int = 100,
    ) -> pd.DataFrame:
    """
    Recebe um df e retorna o mesmo df com informações dos mercados:
    1- Tags (ex: ['Games', 'Sports', 'NBA'])
    2- gameStartTime: (ex: 2025-10-11 17:00:00+00)
    3- Volume do Mercado: (ex: 936950.293165)
    """
    
    unique_slugs = df['slug'].unique()
    
    all_data_dict = {}
    
    # de Fato puxar os dados
    for i in range(0, len(unique_slugs), batch_size):
        
        batch_slugs = unique_slugs[i:i+batch_size]
        
        try:
            response = requests.get(
                url=URLS['MARKET'],
                params={
                    'slug': batch_slugs.tolist(),
                    'include_tag': True,
                    'limit': len(batch_slugs)
                },
                timeout=60
            )
            
            if response.status_code == 200:
                markets = response.json()
                
                # Processar Resultados do Lote
                batch_dict = {}
                
                for market in markets:
                    slug = market.get('slug')
                    
                    if not slug: continue
                        
                    # Inicializar o dicionário
                    batch_dict[slug] = {}
                    
                    # Parte 1: Tags
                    tags = market.get('tags', [])
                    labels = [
                        tag.get('label', '')
                        for tag in tags 
                        if tag.get('label')
                        ]
                    batch_dict[slug]['tags'] = labels
                    
                    # Parte 2: gameStartTime
                    game_start_time = market.get('gameStartTime')
                    batch_dict[slug]['start_time'] = game_start_time
                    
                    # Parte 3: Volume
                    volume = market.get('volume')
                    batch_dict[slug]['volume'] = volume
                
                # Lidar com dados faltantes...
                for slug in batch_slugs:
                    if slug not in batch_dict:
                        batch_dict[slug] = {
                            'tags': [],
                            'start_time': None,
                            'volume': None
                        }
                
                all_data_dict.update(batch_dict)
                
            else:
                print(f"  Erro na API no lote {i}: Status {response.status_code}")
                # Adicionar slugs do lote com tags vazias
                for slug in batch_slugs:
                    all_data_dict[slug] = {'tags': [],'start_time': None,'volume': None}
                        
        except Exception as e:
            print(f"  Erro no lote {i}: {e}")
            # Adicionar slugs do lote com tags vazias
            for slug in batch_slugs:
                all_data_dict[slug] = {'tags': [],'start_time': None,'volume': None}
        
        # Agora, com all_data_dict_pronto, vamos colocar no df       
        market_data_df = pd.DataFrame.from_dict(all_data_dict, orient='index')
        combined_df = df.merge(
            market_data_df,
            left_on='slug',
            right_index=True,
            how='left'
        )
        
        return combined_df
