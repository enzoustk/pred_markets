import pandas as pd
from helpers import safe_divide, to_list
from api.price_history import process_dataframe
# Import lazy de fetch_clv - só será importado quando calculate_clv for chamado

class DataAnalyst:
    @staticmethod
    def calculate_advanced_stats(df:pd.DataFrame):
        df = df.copy()
        stats = {}
        
        df['staked'] = df['totalBought'] * df['avgPrice']
        df['roi'] = safe_divide(df['realizedPnl'], df['staked'])
        
        stats['flat_profit'] = df['roi'].sum()
        stats['avg_stake'] = df['staked'].mean()
        stats['median_stake'] = df['staked'].median() 
        
        return stats
    
    @staticmethod
    def calculate_stats(df: pd.DataFrame):
        """
        Recebe um dataframe, calcula e retorna:
        Profit, Vol e ROI
        """
        df = df.copy()
        
        # Calcular total_profit: usar cashPnl se existir, senão apenas realizedPnl
        df['total_profit'] = df['realizedPnl'].fillna(0)
        if 'cashPnl' in df.columns:
            df['total_profit'] += df['cashPnl'].fillna(0)
        
        df['volume'] = df['totalBought'] * df['avgPrice']
        df['roi'] = safe_divide(df['total_profit'], df['volume'])

        total_profit = df['total_profit'].sum()
        total_volume = df['volume'].sum()
        total_roi = safe_divide(total_profit, total_volume) or 0
        
        return total_profit, total_volume, total_roi
    
    @staticmethod
    def return_stats(df: pd.DataFrame):
        """
        Alias para calculate_stats para compatibilidade com o dashboard.
        Recebe um dataframe, calcula e retorna:
        Profit, Vol e ROI
        """
        return DataAnalyst.calculate_stats(df)
    
    @staticmethod
    def in_depth_tag_analysis(df: pd.DataFrame):
        """
        Pipeline Completo de Análise para um user.
        TODO: Estudo de Variância de Stake
        """
        df = df.copy()
        df['staked'] = df['totalBought'] * df['avgPrice']
        
        # Lucro Total, Vol e ROI. (Tupled)
        totals = DataAnalyst.calculate_stats(df=df)
        avg_stake = df['staked'].mean()
        
        # Aqui começa a análise detalhada de Stakes
        max_stake = df['staked'].max()
        min_stake = df['staked'].min()
        flat_profit = totals[2] * len(df) # ROI vs Apostas
 
    @staticmethod
    def tag_analysis(
        df: pd.DataFrame,
        min_bets: int = 50,
        exclude_tags: list = [],
        ):
        """
        Recebe um dataframe e retorna a análise do user por "tag"
        """
        
        df = df.copy()
        
        # Verificar se a coluna 'tags' existe
        if 'tags' not in df.columns:
            print("⚠️  Aviso: Coluna 'tags' não encontrada no DataFrame. Retornando DataFrame vazio.")
            return pd.DataFrame(columns=['tag', 'profit', 'volume', 'roi', 'bets'])
        
        removed_tags = ['Games', 'Sports'] + exclude_tags
        
        # Passo 1: Criar o df
        tmp = df.copy()
        tmp['__tags_list'] = tmp['tags'].apply(to_list)
        exploded = tmp.explode('__tags_list', ignore_index=True)
        exploded = exploded.rename(columns={'__tags_list': 'tag'})
        exploded = exploded[exploded['tag'].notna()]
        exploded = exploded[~exploded['tag'].isin(removed_tags)]
        
        # Filtrar quais tags vamos estudar antes de entrar em loop
        bets_per_tag = exploded.groupby('tag').size()
        valid_tags = bets_per_tag[bets_per_tag >= int(min_bets)].index
        
        result = []
        
        for tag in valid_tags:
            tag_df = exploded[exploded['tag'] == tag]
            profit, vol, roi = DataAnalyst.calculate_stats(tag_df)
            adv_stats = DataAnalyst.calculate_advanced_stats(tag_df)
            tag_data = {
                'tag': tag,
                'profit': profit,
                'volume': vol,
                'roi': roi,
                'units': adv_stats['flat_profit'],
                'bets': int(bets_per_tag.get(tag, 0))
            }
            result.append(tag_data)
       
        return pd.DataFrame(result).sort_values(by='roi', ascending=False)

    @staticmethod
    def print_tag_report(
        tag_df: pd.DataFrame
    ) -> None:
        """
        Printa os dados para o user ver a análise de Tags
        """
        
        # Verifica se o DataFrame está vazio
        if tag_df.empty:
            print("Nenhuma tag encontrada para exibir no relatório.")
            return
            
        print("\n--- Relatório de Análise por Tag (Ordenado por ROI) ---")
        
        # Define o formato do cabeçalho
        header = f"{'Tag':<20} | {'ROI':>8} | {'Profit':>10} | {'Volume':>12} | {'Bets':>6}"
        print(header)
        print("-" * len(header))
        
        # Itera sobre as linhas do DataFrame para printar cada tag
        for index, row in tag_df.iterrows():
            
            # Formata as strings para um print alinhado
            tag_str = f"{str(row['tag']):<20}"
            roi_str = f"{row['roi']:>8.2%}"  # Formata como porcentagem
            profit_str = f"{row['profit']:>10.2f}"
            volume_str = f"{row['volume']:>12.2f}"
            bets_str = f"{row['bets']:>6}"
            
            # Monta a linha de output
            line = f"{tag_str} | {roi_str} | {profit_str} | {volume_str} | {bets_str}"
            print(line)
            
        print("-" * len(header))
        print("--- Fim do Relatório ---")

    @staticmethod
    def daily_balance(df: pd.DataFrame):
        """
        Recebe um dataframe e retorna o PL 
        separado por dia
        """
        df = df.copy()
        df['endDate'] = pd.to_datetime(
            df['endDate'], format='ISO8601', utc=True
            ).dt.tz_localize(None).dt.to_period('D')
        
        all_data = []
        
        
        for date, date_df in df.groupby('endDate'):
            profit, vol, roi = DataAnalyst.calculate_stats(date_df)
            single_date = {
                'date': date,
                'profit': profit,
                'volume': vol,
                'roi': roi
            }
            all_data.append(single_date)
        
        return pd.DataFrame(all_data)
    
    @staticmethod
    def monthly_balance(df: pd.DataFrame):
        """
        Recebe um dataframe e retorna o PL 
        separado por mês
        """
        df = df.copy()       
        df['month'] = pd.to_datetime(
            df['endDate'], format='ISO8601', utc=True
            ).dt.tz_localize(None).dt.to_period('M')
        
        all_data = []
        
        for date, date_df in df.groupby('month'):
            profit, vol, roi = DataAnalyst.calculate_stats(date_df)
            single_date = {
                'date': date,
                'profit': profit,
                'volume': vol,
                'roi': roi
            }
            all_data.append(single_date)
        
        return pd.DataFrame(all_data)

    @staticmethod
    def calculate_clv(
        user_address: str,
        df: pd.DataFrame,
    ):
        
        print("--- INICIANDO calculate_clv ---")
        
        df = df.copy()
        
        # Colocar o df na forma correta
        clv_df = process_dataframe(df)
        
        clv_results = {}
        clv_reasons = {}
        
        def create_key(df: pd.DataFrame) -> pd.Series:
            return df['conditionId'].astype(str) + '_' + df['asset'].astype(str)
        
        clv_df['_composite_key'] = create_key(df=clv_df)
        
        try:
            clv_df['start_time_unix'] = pd.to_datetime(
                clv_df['start_time'], format='ISO8601', utc=True
            ).astype('int64') // 10**9
            print(f"DataFrame principal (df) preparado. {len(df)} linhas.")
            print(f"Exemplo start_time_unix: {clv_df['start_time_unix'].iloc[0]}")
        
        except Exception as e:
            print(f"Erro CRÍTICO ao converter 'start_time' no df principal: {e}")
            return clv_df # Retorna o df original se falhar aqui

        df_lookup = clv_df.set_index(['conditionId', 'asset']).sort_index()
        
        from api import fetch_clv
        print("Buscando trades da API (fetch_clv)...")
        trades_df = fetch_clv.fetch_clv(
            user_address=user_address,
            df=df
        )
        
        if trades_df.empty:
            print("❌ ERRO: fetch_clv retornou um DataFrame VAZIO. Nenhum trade para processar.")
            print("--- FINALIZANDO calculate_clv (sem dados) ---")
            clv_df = clv_df.drop(columns=['start_time_unix', '_composite_key'], errors='ignore')
            return clv_df
            
        print(f"✅ Trades recebidos. Shape do trades_df: {trades_df.shape}")

        try:
            # *** DEBUG: Vamos inspecionar o timestamp ANTES de converter ***
            raw_timestamp_example = trades_df['timestamp'].iloc[0]
            print(f"Exemplo de 'timestamp' RAW da API: {raw_timestamp_example} (Tipo: {type(raw_timestamp_example)})")
            
            trades_df['timestamp_seconds'] = trades_df['timestamp'].astype(float) // 1000
            
            print(f"Exemplo de 'timestamp_seconds' CONVERTIDO: {trades_df['timestamp_seconds'].iloc[0]}")
            
        except KeyError:
            print("❌ ERRO: A coluna 'timestamp' não foi encontrada no trades_df.")
            clv_df = clv_df.drop(columns=['start_time_unix', '_composite_key'], errors='ignore')
            return clv_df
        
        except Exception as e:
            print(f"❌ ERRO ao converter timestamp do trades_df: {e}")
            clv_df = clv_df.drop(columns=['start_time_unix', '_composite_key'], errors='ignore')
            return clv_df

        trades_df['_composite_key'] = create_key(df=trades_df)
        df_keys_set = set(zip(clv_df['conditionId'], clv_df['asset']))
        
        print(f"--- Iniciando loop por {len(trades_df.groupby(['conditionId', 'asset']))} grupos de trades ---")
        
        # Entrar no loop e calcular o CLV para todas as apostas
        for (condition_id, asset), group_df in trades_df.groupby(['conditionId', 'asset']):
            composite_key =  f"{condition_id}_{asset}"
                       
            try:
                if (condition_id, asset) not in df_keys_set:
                    print("  -> SKIP: Chave não encontrada no df principal.")
                    continue
                    
                lookup_row = df_lookup.loc[(condition_id, asset)]
                
                if isinstance(lookup_row, pd.DataFrame):
                    lookup_row = lookup_row.iloc[0]
                
                # *** DEBUG: Inspecionar os valores de lookup ***
                start_time = lookup_row['start_time_unix']
                closing_price = lookup_row['match_start_price']
                
                # *** DEBUG: Checar se o closing_price é NaN ***
                if pd.isna(closing_price):
                    print("  -> ERRO: 'match_start_price' (Closing Price) é NaN. Pulando.")
                    clv_reasons[composite_key] = 'closing_price_is_nan'
                    continue
                                
                # Usar a coluna 'timestamp_seconds' para o filtro
                filtered_df = group_df[group_df['timestamp_seconds'] < start_time].copy()
                                
                total_size = filtered_df['size'].sum()
                
                if total_size == 0:
                    print("  -> SKIP: Nenhum trade encontrado antes do start_time (Total Size = 0).")
                    clv_reasons[composite_key] = 'sem_trades_pre_market'
                    continue 

                # Calcular agora o preço médio.
                avg_price = (
                    (filtered_df['size'] * filtered_df['price']).sum() 
                    / total_size
                    )
                
                price_clv = closing_price - avg_price

                odds_clv = safe_divide(1,avg_price) - safe_divide(1,closing_price)
            
                
                clv_results[composite_key] = {
                    'price_clv': price_clv, 'odds_clv': odds_clv,
                    'avg_price': avg_price, 'closing_price': closing_price
                }
                
            except Exception as e:
                print(f"  -> ERRO CRÍTICO no loop: {e}")
                clv_reasons[composite_key] = f'erro_processamento: {str(e)[:50]}'
                                
        print("\n--- Loop finalizado. Mapeando resultados ---")
        
        price_clv_map = {key: val['price_clv'] for key, val in clv_results.items()}
        odds_clv_map = {key: val['odds_clv'] for key, val in clv_results.items()}

        clv_df['price_clv'] = clv_df['_composite_key'].map(price_clv_map)
        clv_df['odds_clv'] = clv_df['_composite_key'].map(odds_clv_map)
                
        clv_df = clv_df.drop(
            columns=['start_time_unix', '_composite_key'], errors='ignore'
            )
        
        # Imprimir um resumo dos problemas
        if clv_reasons:
            print("\nRelatório de CLV (itens não calculados):")
            reason_counts = pd.Series(clv_reasons).value_counts()
            print(reason_counts)
        
        print("Estatísticas do CLV:")
        print("\n" + "-" * 40)
        print("-" * 40)
        
        # 1. Isolar os valores de CLV que foram calculados com sucesso (não-nulos)
        valid_clv = clv_df['price_clv'].dropna()
        total_calculated = len(valid_clv)
        
        # 2. Verificar se temos dados para calcular
        if total_calculated == 0:
            print("  Nenhum valor de CLV foi calculado com sucesso.")
            print("  Estatísticas indisponíveis.")
        
        else:
            # 3. Calcular as métricas
            mean_clv = valid_clv.mean()
            median_clv = valid_clv.median()
            
            # Calcular percentuais
            pos_percent = (valid_clv > 0).sum() / total_calculated * 100
            neg_percent = (valid_clv < 0).sum() / total_calculated * 100
            zero_percent = (valid_clv == 0).sum() / total_calculated * 100
            
            
        
        print("-" * 40)
        print("--- FINALIZANDO calculate_clv (com sucesso) ---")
        
        return clv_df