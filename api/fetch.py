import time
import random
import requests
import pandas as pd
from api.config import URLS
from typing import List, Dict, Any
from helpers import loading_animation  # Assumindo que está em helpers.py
from data.handle import assertion_active
from concurrent.futures import ProcessPoolExecutor, as_completed

# --------------------------------------------------------------------------
# FUNÇÕES-FILHAS (EXECUTADAS EM PROCESSOS SEPARADOS)
# Elas devem ser silenciosas para não quebrar a animação no processo-pai.
# --------------------------------------------------------------------------

def page(
    url: str,
    offset: int,
    user_address: str,
    limit: int = 500,
    process_id: int = None,
    retry_count: int = 0,
    ) -> Dict[str, Any]:
    
    """
    Busca uma página específica de dados.
    Esta função é SILENCIOSA (sem prints) para rodar em paralelo.
    """
    
    params = {"limit": limit, "offset": offset, "user": user_address}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {"offset": offset, "data": data, "success": True, "retry_count": retry_count}
        
        elif response.status_code == 429:
            base_delay = 2  
            max_delay = 60  
            exponential_delay = min(base_delay * (2 ** retry_count), max_delay)
            jitter = random.uniform(0.1, 0.5) * (process_id or 1)
            total_delay = exponential_delay + jitter
            
            # --- PRINT REMOVIDO ---
            # print(f"⚠️  {process_info}: Rate limit...")
            time.sleep(total_delay)
            
            return {"offset": offset, "data": [], "success": False, "error": "Rate limited", "retry_count": retry_count}
        
        else:
            return {"offset": offset, "data": [], "success": False, "error": response.status_code, "retry_count": retry_count}
    
    except Exception as e:
        # --- PRINT REMOVIDO ---
        # print(f'Error Puxando página: {e}')
        return {"offset": offset,"data": [],"success": False,"error": str(e),"retry_count": retry_count}

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
    Busca um range específico de offsets.
    Esta função é SILENCIOSA (sem prints) para rodar em paralelo.
    """
    # --- PRINT REMOVIDO ---
    # print(f"Processo {process_id}: Buscando offsets...")
    
    initial_delay = random.uniform(0.1, 0.5) * process_id
    if initial_delay > 0: time.sleep(initial_delay)
    
    all_data = []
    current_offset = start_offset
    base_delay = 0.3 + (process_id * 0.1) 
    
    while True:
        if process_id < num_processes and current_offset >= end_offset:
            # --- PRINT REMOVIDO ---
            # print(f"🏁 Processo {process_id}: Limite atingido...")
            break
        
        if process_id < num_processes:
            max_offset_allowed = end_offset - current_offset
            if max_offset_allowed <= 0:
                break
            max_limit = min(max_limit, max_offset_allowed)
        
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
                registros_coletados = len(result["data"])
                all_data.extend(result["data"])                
                current_offset += len(result["data"])
                
                # --- PRINT REMOVIDO ---
                # print(f"✓ Processo {process_id}: Coletados...")
                
                if process_id < num_processes and current_offset > end_offset:
                    excess = current_offset - end_offset
                    if excess > 0:
                        if excess <= len(all_data):
                            all_data = all_data[:-excess]
                            # --- PRINT REMOVIDO ---
                        else:
                            # --- PRINT REMOVIDO ---
                            all_data = []
                        current_offset = end_offset
                break  
            
            elif not result["success"]:
                if result.get("error") == "Rate limited":
                    retry_count += 1
                    if retry_count >= max_retries:
                        # --- PRINT REMOVIDO ---
                        break
                    continue
                else:
                    # --- PRINT REMOVIDO ---
                    return all_data
            
            else:
                # --- PRINT REMOVIDO ---
                return all_data
        
        if retry_count >= max_retries and not (result.get("success") and result.get("data")):
            # --- PRINT REMOVIDO ---
            break
        
        if process_id < num_processes and current_offset >= end_offset:
            break
        
        jitter = random.uniform(-0.1, 0.1)
        delay = max(0.1, base_delay + jitter)
        time.sleep(delay)
    
    # --- PRINT REMOVIDO ---
    # print(f"Processo {process_id}: Concluído...")
    return all_data

# --------------------------------------------------------------------------
# FUNÇÕES-PAI (ORQUESTRADORAS)
# Elas controlam a animação no processo principal.
# --------------------------------------------------------------------------

def all_data_parallel(
    url: str,
    user_address: str,
    num_processes: int,
    display_message: str,  # <-- NOVO PARÂMETRO
    records_per_process: int = 250,
    ):
    """
    Busca todos os dados usando processos paralelos e exibe animação.
    """
    ranges = []
    for i in range(num_processes):
        start_offset = i * records_per_process
        end_offset = (i + 1) * records_per_process
        process_id = i + 1
        ranges.append((start_offset, end_offset, process_id))
    
    all_data = []
    
    # --- LÓGICA DE ANIMAÇÃO ADICIONADA ---
    initial_msg = f"📊 {display_message} (0 de {num_processes} processos)"
    
    with loading_animation(initial_msg) as anim_status:
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            futures = []
            for start_offset, end_offset, process_id in ranges:
                future = executor.submit(
                    fetch_range,
                    url,
                    user_address,
                    start_offset,
                    end_offset,
                    process_id,
                    num_processes
                )
                futures.append(future)
            
            processos_concluidos = 0
            for future in as_completed(futures):
                try:
                    process_data = future.result()
                    all_data.extend(process_data)
                    processos_concluidos += 1
                    
                    # --- ATUALIZA A MENSAGEM DA ANIMAÇÃO ---
                    anim_status['message'] = f"📊 {display_message} ({processos_concluidos} de {num_processes} processos)"
                    
                except Exception as e:
                    # (Silencioso para não quebrar a animação)
                    # Você pode querer adicionar um log aqui
                    pass
    
    # --- PRINT FINAL ---
    print(f"✓ {display_message} concluída. Total: {len(all_data):,} registros.")
    return all_data

def user_data(
    user_address: str,
    ):
    """
    Puxa toda as posições para o usuário em um dataframe.
    """    
    
    # Passo 1: Posições Fechadas
    closed_data = pd.DataFrame(all_data_parallel(
        user_address=user_address,
        url=URLS['CLOSED_POSITIONS'],
        num_processes=20,
        display_message="Buscando Posições Fechadas" # <-- Passa a mensagem
    ))
    
    # Passo 2: Posições Ativas
    active_data = pd.DataFrame(all_data_parallel(
        user_address=user_address,
        url=URLS['ACTIVE_POSITIONS'],
        num_processes=1,
        display_message="Buscando Posições Ativas" # <-- Passa a mensagem
    ))
    
    # Passo 3: Dados de Mercado (já tinha a animação)
    return fetch_market_data(assertion_active(active_df=active_data, closed_df=closed_data))

def fetch_market_data(
    df: pd.DataFrame,
    batch_size: int = 100,
    ) -> pd.DataFrame:
    """
    (Função original - já estava correta, sem mudanças)
    """
    unique_slugs = df['slug'].unique()
    all_data_dict = {}
    total_batches = (len(unique_slugs) + batch_size - 1) // batch_size
    
    initial_msg = f"📊 Buscando dados de Mercado (0 de {total_batches})"
    
    with loading_animation(initial_msg) as anim_status:
        for i in range(0, len(unique_slugs), batch_size):
            batch_slugs = unique_slugs[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            anim_status['message'] = f"📊 Buscando dados de Mercado ({batch_num} de {total_batches})"
            
            response = None
            try:
                response = requests.get(
                    url=URLS['MARKET'],
                    params={'slug': batch_slugs.tolist(), 'include_tag': True, 'limit': len(batch_slugs)},
                    timeout=60
                )
            except Exception as e:
                pass 

            if response and response.status_code == 200:
                markets = response.json()
                batch_dict = {}
                for market in markets:
                    slug = market.get('slug')
                    if not slug: continue
                    batch_dict[slug] = {}
                    tags = market.get('tags', [])
                    labels = [tag.get('label', '') for tag in tags if tag.get('label')]
                    batch_dict[slug]['tags'] = labels
                    game_start_time = market.get('gameStartTime')
                    batch_dict[slug]['start_time'] = game_start_time
                    volume = market.get('volume')
                    batch_dict[slug]['volume'] = volume
                
                for slug in batch_slugs:
                    if slug not in batch_dict:
                        batch_dict[slug] = {'tags': [], 'start_time': None, 'volume': None}
                all_data_dict.update(batch_dict)
            else:
                for slug in batch_slugs:
                    all_data_dict[slug] = {'tags': [],'start_time': None,'volume': None}

        anim_status['message'] = "Concluindo..."

    print("✓ Coleta de dados de mercado concluída.")
    
    market_data_df = pd.DataFrame.from_dict(all_data_dict, orient='index')
    combined_df = df.merge(
        market_data_df,
        left_on='slug',
        right_index=True,
        how='left'
    )
    return combined_df

def fetch_total_trades(
    user_address
    ) -> int:
    """
    Busca o número total de trades de um usuário (com animação simples).
    """
    params = {"user": user_address}
    
    try:
        response = requests.get(URLS['TOTAL_TRADES'], params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "traded" in data:
            return data["traded"]
        else: 
            return -1

    except Exception as e:
        return -1