import pandas as pd

def assertion_active(
    active_df: pd.DataFrame,
    closed_df: pd.DataFrame,
    ) -> pd.DataFrame:

    # Cria cópias para não modificar os originais
    active_df = active_df.copy()
    closed_df = closed_df.copy()

    # Identifica posições realmente ativas (redeemable == False)
    real_active_mask = active_df['redeemable'] == False
    
    # Adiciona coluna 'ativo' para active_df
    active_df['active'] = real_active_mask
    
    # Adiciona coluna 'ativo' para closed_df (todas False)
    closed_df['active'] = False
    
    # Combina os dois DataFrames
    return pd.concat([active_df, closed_df], ignore_index=True)
    
def insert_tags(df: pd.DataFrame, batch_size: int = 100):
    """
    Procura tags para todos os mercados usados usando busca em lote otimizada
    Processa em lotes para evitar erro 414 (URI muito longa)
    """
    import time
    import requests
    
    # Verifica se a coluna 'slug' existe
    if 'slug' not in df.columns:
        print("Erro: Coluna 'slug' não encontrada no DataFrame")
        return df
    
    total_start = time.time()
    print(f"Buscando tags para {len(df)} mercados usando busca em lote...")
    
    # Obter slugs únicos para evitar requisições duplicadas
    unique_slugs = df['slug'].unique()
    print(f"Slugs únicos: {len(unique_slugs)}")
    
    # Processar em lotes para evitar URI muito longa
    all_tags_dict = {}
    total_batches = (len(unique_slugs) + batch_size - 1) // batch_size
    
    for i in range(0, len(unique_slugs), batch_size):
        batch_slugs = unique_slugs[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        print(f"Processando lote {batch_num}/{total_batches} ({len(batch_slugs)} slugs)...")
        
        try:
            response = requests.get(
                'https://gamma-api.polymarket.com/markets',
                params={
                    'slug': batch_slugs.tolist(),
                    'include_tag': True,
                    'limit': len(batch_slugs)
                },
                timeout=60
            )
            
            if response.status_code == 200:
                markets = response.json()
                
                # Processar resultados do lote
                batch_tags_dict = {}
                for market in markets:
                    slug = market.get('slug')
                    if slug:
                        tags = market.get('tags', [])
                        labels = [tag.get('label', '') for tag in tags if tag.get('label')]
                        batch_tags_dict[slug] = labels
                
                # Adicionar slugs não encontrados no lote
                for slug in batch_slugs:
                    if slug not in batch_tags_dict:
                        batch_tags_dict[slug] = []
                
                all_tags_dict.update(batch_tags_dict)
                print(f"  Lote {batch_num} concluído: {len([t for t in batch_tags_dict.values() if t])} mercados com tags")
                
            elif response.status_code == 414:
                print(f"  Erro 414 no lote {batch_num}: URI muito longa, reduzindo tamanho do lote...")
                # Tentar com lote menor
                smaller_batch_size = len(batch_slugs) // 2
                if smaller_batch_size > 0:
                    print(f"  Tentando com {smaller_batch_size} slugs...")
                    # Recursivamente processar com lote menor
                    smaller_df = df[df['slug'].isin(batch_slugs)].copy()
                    smaller_result = insert_tags(smaller_df, smaller_batch_size)
                    for idx, row in smaller_result.iterrows():
                        all_tags_dict[row['slug']] = row['tags']
                else:
                    print(f"  Pulando lote {batch_num} - slugs muito longos")
                    
            else:
                print(f"  Erro na API no lote {batch_num}: Status {response.status_code}")
                # Adicionar slugs do lote com tags vazias
                for slug in batch_slugs:
                    all_tags_dict[slug] = []
        
        except Exception as e:
            print(f"  Erro no lote {batch_num}: {e}")
            # Adicionar slugs do lote com tags vazias
            for slug in batch_slugs:
                all_tags_dict[slug] = []
    
    # Mapear tags de volta para o DataFrame
    df['tags'] = df['slug'].map(all_tags_dict)
    
    total_elapsed = time.time() - total_start
    print(f"\nProcessamento concluído em {total_elapsed:.2f} segundos")
    print(f"Tempo médio por mercado: {total_elapsed/len(df):.3f} segundos")
    print(f"Tags encontradas para {len([t for t in df['tags'] if t])} mercados")
    
    return df
    
def process_sports_trades(full_df: pd.DataFrame):
    """
    Filtra todas as linhas que tenham a tag 'Games' OU 'Sports'
    
    Args:
        full_df: DataFrame completo com coluna 'tags'
    
    Returns:
        DataFrame filtrado contendo apenas mercados com tag 'Games' ou 'Sports'
    """

    
    # Verificar se a coluna 'tags' existe
    if 'tags' not in full_df.columns:
        print("Erro: Coluna 'tags' não encontrada no DataFrame")
        return pd.DataFrame()
    
    # Filtrar linhas que tenham a tag 'Games' OU 'Sports'
    sports_games_mask = full_df['tags'].apply(
        lambda tags: ('Games' in tags or 'Sports' in tags) if isinstance(tags, list) else False
    )
    sports_games_df = full_df[sports_games_mask].copy()
    
    print(f"Filtrados {len(sports_games_df)} mercados com tag 'Games' ou 'Sports' de {len(full_df)} total")
    
    return sports_games_df