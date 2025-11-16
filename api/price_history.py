"""
Script para coletar preço histórico do Polymarket para múltiplos eventos
Processa um DataFrame e retorna com a odd no início de cada evento
"""
import requests
from datetime import datetime, timedelta
import pytz
import pandas as pd
import json
import time
import random
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from api.config import URLS


def get_price_history(
    timeout,
    market_id: str, 
    start_datetime: datetime, 
    end_datetime: Optional[datetime] = None, 
    window_minutes: Optional[int] = None, 
    fidelity: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Obtém histórico de preços usando a API do Polymarket
    
    Args:
        market_id: ID do mercado (token ID)
        start_datetime: Data e hora de início (UTC)
        end_datetime: Data e hora de fim (UTC). Se None, usa window_minutes
        window_minutes: Janela de tempo após start_datetime (usado se end_datetime for None)
        fidelity: Resolução dos dados em minutos (padrão: 1)
        timeout: Timeout da requisição em segundos
    
    Returns:
        dict com os dados do histórico de preços ou None se houver erro
    """
    # Converter para timestamp Unix
    start_ts = int(start_datetime.timestamp())
    
    if end_datetime:
        end_ts = int(end_datetime.timestamp())
    elif window_minutes:
        end_ts = start_ts + (window_minutes * 60)
    else:
        end_ts = start_ts + 300  # Padrão: 5 minutos
    
    # Endpoint da API
    url = f"{URLS['CLOB']}/prices-history"
    params = {
        "market": market_id,
        "startTs": start_ts,
        "endTs": end_ts,
        "fidelity": fidelity
    }
    
    try:
        response = requests.get(url, params=params, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
            
    except requests.exceptions.RequestException:
        return None


def extract_match_start_price(
    price_history: Dict[str, Any], 
    match_datetime: datetime, 
    max_hours_before: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Extrai o preço mais próximo ANTES ou NO INÍCIO do jogo (nunca depois)
    
    Args:
        price_history: Dados retornados pela API (deve conter campo 'history')
        match_datetime: Data e hora de início da partida
        max_hours_before: Máximo de horas antes do início para considerar (padrão: 1 hora)
    
    Returns:
        dict com timestamp e preço antes/início do jogo, ou None se não encontrado
    """
    if not price_history or "history" not in price_history:
        return None
    
    history = price_history["history"]
    if not history or len(history) == 0:
        return None
    
    match_ts = int(match_datetime.timestamp())
    max_seconds_before = max_hours_before * 3600  # Converter horas para segundos
    min_ts = match_ts - max_seconds_before  # 1 hora antes
    
    # Filtrar apenas preços ANTES ou NO INÍCIO do jogo (entry_ts <= match_ts)
    # E que estejam dentro da janela permitida (entry_ts >= min_ts)
    valid_entries = []
    for entry in history:
        entry_ts = entry.get("t", 0)
        # Deve estar antes ou no início E dentro da janela de 1 hora antes
        if min_ts <= entry_ts <= match_ts:
            valid_entries.append(entry)
    
    if not valid_entries:
        return None
    
    # Ordenar por timestamp (mais próximo do início primeiro)
    valid_entries_sorted = sorted(valid_entries, key=lambda x: x.get("t", 0), reverse=True)
    
    # Retornar o mais próximo do início (último antes ou exatamente no início)
    return valid_entries_sorted[0]


def get_match_start_price(
    market_id: str,
    match_datetime: datetime,
    hours_before: int = 1,
    fidelity: int = 1,
    timeout: int = 0.1
) -> Optional[float]:
    """
    Obtém o preço ANTES ou NO INÍCIO do evento (nunca depois)
    Busca preços de até 1 hora antes do início até o início do jogo
    
    Args:
        market_id: ID do mercado (token ID)
        match_datetime: Data e hora de início do evento (UTC)
        hours_before: Quantas horas antes do início buscar (padrão: 1 hora)
        fidelity: Resolução dos dados em minutos
        timeout: Timeout da requisição em segundos
    
    Returns:
        Preço (float entre 0 e 1) ou None se houver erro
    """
    # Calcular timestamp de início da busca (1 hora antes)
    start_search_datetime = match_datetime - timedelta(hours=hours_before)
    
    # Buscar dados de 1 hora antes até o início do jogo
    # window_minutes será calculado automaticamente baseado na diferença
    price_history = get_price_history(
        market_id=market_id,
        start_datetime=start_search_datetime,
        end_datetime=match_datetime,  # Termina exatamente no início
        fidelity=fidelity,
        timeout=timeout
    )
    
    if not price_history:
        return None
    
    match_start_entry = extract_match_start_price(
        price_history, 
        match_datetime, 
        max_hours_before=hours_before
    )
    
    if match_start_entry:
        return match_start_entry.get("p")
    
    return None


def process_batch(
    rows_data: List[Tuple[int, Dict[str, Any]]],
    market_id_col: str,
    start_time_col: str,
    hours_before: int,
    fidelity: int,
    delay_between_requests: float,
    timeout: int,
    process_id: int,
    num_processes: int
) -> List[Tuple[int, Optional[float]]]:
    """
    Processa um lote de eventos em paralelo
    
    Args:
        rows_data: Lista de tuplas (idx, row_dict) contendo os dados das linhas
        market_id_col: Nome da coluna que contém o market_id
        start_time_col: Nome da coluna que contém a data/hora
        hours_before: Horas antes do início para buscar
        fidelity: Resolução dos dados em minutos
        delay_between_requests: Delay entre requisições
        timeout: Timeout da requisição
        process_id: ID do processo (para logs)
        num_processes: Número total de processos
    
    Returns:
        Lista de tuplas (idx, price) com os resultados
    """
    results = []
    total_batch = len(rows_data)
    
    # Delay inicial para jitter (evitar sincronização)
    initial_delay = random.uniform(0.1, 0.5) * process_id
    if initial_delay > 0:
        time.sleep(initial_delay)
    
    base_delay = delay_between_requests + (process_id * 0.05)  # Delay base com variação por processo
    
    print(f"🔄 Processo {process_id}: Iniciando processamento de {total_batch} eventos")
    
    for batch_idx, (idx, row_dict) in enumerate(rows_data):
        market_id = str(row_dict.get(market_id_col, ''))
        start_time_str = str(row_dict.get(start_time_col, ''))
        
        # Pular se dados incompletos
        if not market_id or market_id == 'nan' or not start_time_str or start_time_str == 'nan':
            results.append((idx, None))
            continue
        
        # Converter start_time para datetime
        try:
            if isinstance(start_time_str, str):
                if '+' in start_time_str or start_time_str.endswith('Z'):
                    match_datetime = pd.to_datetime(start_time_str).to_pydatetime()
                    if match_datetime.tzinfo is None:
                        match_datetime = pytz.UTC.localize(match_datetime)
                    else:
                        match_datetime = match_datetime.astimezone(pytz.UTC)
                else:
                    match_datetime = pd.to_datetime(start_time_str).to_pydatetime()
                    if match_datetime.tzinfo is None:
                        match_datetime = pytz.UTC.localize(match_datetime)
                    else:
                        match_datetime = match_datetime.astimezone(pytz.UTC)
            else:
                match_datetime = pd.to_datetime(start_time_str).to_pydatetime()
                if match_datetime.tzinfo is None:
                    match_datetime = pytz.UTC.localize(match_datetime)
                else:
                    match_datetime = match_datetime.astimezone(pytz.UTC)
        except Exception as e:
            print(f"⚠️  Processo {process_id}, linha {idx}: Erro ao converter start_time: {e}")
            results.append((idx, None))
            continue
        
        # Obter preço
        try:
            price = get_match_start_price(
                market_id=market_id,
                match_datetime=match_datetime,
                hours_before=hours_before,
                fidelity=fidelity,
                timeout=timeout
            )
            results.append((idx, price))
            
        except Exception as e:
            print(f"❌ Processo {process_id}, linha {idx}: Erro ao processar: {e}")
            results.append((idx, None))
        
        # Delay entre requisições (com jitter)
        if delay_between_requests > 0:
            jitter = random.uniform(-0.05, 0.05)
            delay = max(0.05, base_delay + jitter)
            time.sleep(delay)
        
        # Log de progresso a cada 10 eventos
        if (batch_idx + 1) % 10 == 0:
            print(f"✅ Processo {process_id}: Processados {batch_idx + 1}/{total_batch} eventos do lote")
    
    print(f"🏁 Processo {process_id}: Concluído - {total_batch} eventos processados")
    return results


def process_dataframe(
    df: pd.DataFrame,
    market_id_col: str = "asset",
    start_time_col: str = "start_time",
    hours_before: int = 1,
    fidelity: int = 1,
    delay_between_requests: float = 0.1,
    timeout: int = 30,
    num_processes: int = 10,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Processa um DataFrame em paralelo e adiciona coluna com a odd antes/início de cada evento
    Busca preços de até 1 hora ANTES do início até o início do jogo (nunca depois)
    
    Args:
        df: DataFrame com os dados dos eventos (deve ter colunas market_id_col e start_time_col)
        market_id_col: Nome da coluna que contém o market_id (token ID)
        start_time_col: Nome da coluna que contém a data/hora do evento
        hours_before: Quantas horas antes do início buscar (padrão: 1 hora)
        fidelity: Resolução dos dados em minutos
        delay_between_requests: Delay em segundos entre requisições (para evitar rate limit)
        timeout: Timeout da requisição em segundos
        num_processes: Número de processos paralelos (padrão: 10)
        verbose: Se True, imprime progresso
    
    Returns:
        DataFrame original com coluna 'match_start_price' adicionada
    """
    # Criar cópia para não modificar o original
    result_df = df.copy()
    
    # Inicializar coluna de preço
    result_df['match_start_price'] = None
    
    # Verificar se as colunas necessárias existem
    if market_id_col not in df.columns:
        raise ValueError(f"Coluna '{market_id_col}' não encontrada no DataFrame")
    if start_time_col not in df.columns:
        raise ValueError(f"Coluna '{start_time_col}' não encontrada no DataFrame")
    
    total_rows = len(df)
    
    # Calcular tamanho do lote por processo
    events_per_process = max(1, total_rows // num_processes)
    
    if verbose:
        print(f"📊 Processando {total_rows} eventos em {num_processes} processos paralelos...")
        print(f"   Coluna de market_id: '{market_id_col}'")
        print(f"   Coluna de start_time: '{start_time_col}'")
        print(f"   Eventos por processo: ~{events_per_process}")
        print()
    
    # Preparar dados para processamento paralelo
    # Converter DataFrame para lista de dicionários (serializável)
    rows_data_list = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        rows_data_list.append((idx, row_dict))
    
    # Dividir em lotes
    batches = []
    for i in range(num_processes):
        start_idx = i * events_per_process
        end_idx = (i + 1) * events_per_process if i < num_processes - 1 else total_rows
        batch_data = rows_data_list[start_idx:end_idx]
        if batch_data:  # Só adicionar se não estiver vazio
            batches.append((batch_data, i + 1))
    
    if verbose:
        print(f"🔄 Dividido em {len(batches)} lotes para processamento paralelo")
        print()
    
    start_time = time.time()
    all_results = []
    
    # Processar em paralelo
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = []
        for batch_data, process_id in batches:
            future = executor.submit(
                process_batch,
                batch_data,
                market_id_col,
                start_time_col,
                hours_before,
                fidelity,
                delay_between_requests,
                timeout,
                process_id,
                num_processes
            )
            futures.append(future)
        
        # Coletar resultados conforme vão chegando
        for future in as_completed(futures):
            try:
                batch_results = future.result()
                all_results.extend(batch_results)
                if verbose:
                    print(f"✅ Lote concluído: {len(batch_results)} eventos processados")
            except Exception as e:
                if verbose:
                    print(f"❌ Erro em lote: {e}")
    
    # Aplicar resultados ao DataFrame
    for idx, price in all_results:
        result_df.at[idx, 'match_start_price'] = price
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Estatísticas
    success_count = result_df['match_start_price'].notna().sum()
    error_count = total_rows - success_count
    
    if verbose:
        print()
        print("=" * 80)
        print(f"✅ Processamento concluído!")
        print(f"   Tempo total: {elapsed_time:.2f} segundos ({elapsed_time/60:.2f} minutos)")
        print(f"   Total: {total_rows} eventos")
        print(f"   Sucessos: {success_count}")
        print(f"   Erros: {error_count}")
        print(f"   Taxa de sucesso: {(success_count/total_rows*100):.1f}%")
        print("=" * 80)
    
    return result_df


def test_price_history():
    """
    Função de teste para um único evento (mantida para compatibilidade)
    """
    # Exemplo de uso com valores hardcoded para teste
    market_id = "22783991743746237550553121642485977105068398075531979515766696708537144129916"
    match_date = datetime(2025, 10, 26, 18, 45, tzinfo=pytz.UTC)
    
    print("=" * 80)
    print("TESTE: Coleta de Preço no Início da Partida")
    print("=" * 80)
    print(f"Market ID: {market_id}")
    print(f"Horário da partida: {match_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    price = get_match_start_price(market_id, match_date)
    
    if price is not None:
        print(f"✅ Preço no início: {price} ({price * 100:.2f}%)")
    else:
        print("❌ Não foi possível obter o preço")


def main():
    """
    Função principal - demonstra uso com DataFrame
    """
    print("\n🚀 Script de coleta de preços históricos do Polymarket\n")
    
    # Exemplo: carregar CSV e processar
    try:
        print("📂 Carregando sports_data.csv...")
        df = pd.read_csv('sports_data.csv')
        print(f"✅ CSV carregado: {len(df)} linhas")
        print()
        
        # Processar DataFrame - TODOS os eventos
        total_events = len(df)
        estimated_time_minutes = (total_events * 0.1) / 60
        print(f"🔍 Processando TODOS os {total_events} eventos...")
        print(f"   ⏱️  Tempo estimado: ~{estimated_time_minutes:.1f} minutos")
        print(f"   (Delay de {0.1}s entre requisições para evitar rate limit)")
        print()
        
        result_df = process_dataframe(
            df=df,  # Processando todos os eventos
            market_id_col="asset",
            start_time_col="start_time",
            hours_before=1,  # Buscar preços de até 1 hora antes do início
            num_processes=10,  # Número de processos paralelos
            verbose=True
        )
        
        print("\n📊 Resultados (primeiras 10 linhas - amostra):")
        cols_to_show = ['title', 'asset', 'start_time', 'match_start_price']
        # Garantir que as colunas existem
        available_cols = [col for col in cols_to_show if col in result_df.columns]
        print(result_df[available_cols].head(10).to_string())
        print(f"\n   ... (mostrando apenas amostra - total de {len(result_df)} linhas)")
        
        # Estatísticas
        total_with_price = result_df['match_start_price'].notna().sum()
        print(f"\n📈 Estatísticas:")
        print(f"   Total de eventos: {len(result_df)}")
        print(f"   Eventos com preço coletado: {total_with_price}")
        print(f"   Taxa de sucesso: {(total_with_price/len(result_df)*100):.1f}%")
        
        # Salvar resultado
        output_file = 'sports_data_with_prices.csv'
        result_df.to_csv(output_file, index=False)
        print(f"\n💾 Resultados salvos em: {output_file}")
        
    except FileNotFoundError:
        print("❌ Arquivo sports_data.csv não encontrado")
        print("   Executando teste simples...")
        test_price_history()
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
