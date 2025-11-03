import pandas as pd
from helpers import safe_divide, to_list
from api import fetch_clv

class DataAnalyst:
    @staticmethod
    def calculate_stats(df: pd.DataFrame):
        """
        Recebe um dataframe, calcula e retorna:
        Profit, Vol e ROI
        """
        df = df.copy()
        
        df['total_profit'] = df['realizedPnl'].fillna(0) + df['cashPnl'].fillna(0)
        df['volume'] = df['totalBought'] * df['avgPrice']
        df['roi'] = df['total_profit'] / df['volume']

        total_profit = df['total_profit'].sum()
        total_volume = df['volume'].sum()
        total_roi = total_profit / total_volume
        
        return total_profit, total_volume, total_roi
    
    @staticmethod
    def in_depth_tag_analysys(df: pd.DataFrame):
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
    def tag_analysys(
        df: pd.DataFrame,
        min_bets: int = 50,
        exclude_tags: list = []
        ):
        """
        Recebe um dataframe e retorna a análise do user por "tag"
        """
        
        df = df.copy()
        
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
            tag_data = {
                'tag': tag,
                'profit': profit,
                'volume': vol,
                'roi': roi,
                'bets': int(bets_per_tag.get(tag, 0))
            }
            result.append(tag_data)
        
        return pd.DataFrame(result).sort_values(by='roi', ascending=False)

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
        df: pd.DataFrame
        ):
        """
        Recebe um dataframe e calcula o CLV para cada uma das apostas presentes nele.
        Retorna um DataFrame com estatísticas de CLV (predf) e o DataFrame modificado com colunas CLV (df).
        """
        # No dataframe, temos a hora de cada partida, basta ver a transação/preço do item na hora do tip-off.
        # Problema 1: Se o jogador comprou depois? 
        # Problema 2: Se o jogador vendeu antes/cashout?
        # Problema 3: Como puxar o snapshot de um evento já terminado?
        
        # Solução 1 e 2: 
        # https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets?playground=open
        # Filtrar somente transações feitas antes do evento começar.
        
        
        # Receber o DF Positions com: match_start_price
        # Passo 1: Filtrar do DF de Trades somente as trades que ocorreram antes do evento.
            # 1.1 Para elas, calcular o preço médio.
        # Passo 2: Calcular o CLV
        
        # Forma inteligente: 
            # 1- Percorrer o trades_df agrupado para cada ConditionID diferente;
                # Coletar seu match_start_price,
                # Remover trades pós-start
                # Calcular o CLV
                
        # Nesse momento, trades_df é um csv
        df = df.copy()
        
        clv_results = {}
        clv_reasons = {}
        
        # Criar índice composto para lookup: conditionId + asset
        
        def create_key(df: pd.DataFrame) -> pd.Series:
            # Cria uma chave composta e retorna apenas a nova coluna (Series).
            return df['conditionId'].astype(str) + '_' + df['asset'].astype(str)
        
        df['_composite_key'] = create_key(df=df)
        df_lookup = df.set_index(['conditionId', 'asset']).sort_index()
        
        df['start_time_unix'] = pd.to_datetime(
            df['start_time'], format='ISO8601', utc=True
            ).astype('int64') // 10**9
        
        
        # TODO: Lógica para puxar todos os trades vem aqui
        trades_df = fetch_clv.fetch_clv(
            user_address=user_address,
            df=df
            )
        trades_df['_composite_key'] = create_key(df=trades_df)
        
        # Criar conjunto de tuplas do df para busca rápida
        df_keys_set = set(zip(df['conditionId'], df['asset']))
        
        # Entrar no loop e calcular o CLV para todas as apostas
        for (condition_id, asset), group_df in trades_df.groupby(['conditionId', 'asset']):
            composite_key = f"{condition_id}_{asset}"
            
            try:
                # Verificar se o conditionId + asset existe no df
                if (condition_id, asset) not in df_keys_set:
                    continue
                    
                # Definir dados a comparar, Se houver múltiplas linhas, pegar a primeira
                lookup_row = df_lookup.loc[(condition_id, asset)]
                
                if isinstance(lookup_row, pd.DataFrame):
                    lookup_row = lookup_row.iloc[0]
                
                start_time = lookup_row['start_time_unix']
                closing_price = lookup_row['match_start_price']
                                
                # Agora, temos o filtered_df com trades de antes do Tip-Off
                filtered_df = group_df[group_df['timestamp'] < start_time].copy()
                                                
                # Calcular agora o preço médio.
                avg_price = (
                    (filtered_df['size'] * filtered_df['price']).sum() 
                    / filtered_df['size'].sum()
                    )
                
                # Calcular CLV
                price_clv = closing_price - avg_price
                
                # Evitar divisão por zero
                odds_clv = safe_divide(
                    safe_divide(1,avg_price),
                    safe_divide(1,closing_price)
                )

                
                clv_results[composite_key] = {
                    'price_clv': price_clv,
                    'odds_clv': odds_clv,
                    'avg_price': avg_price,
                    'closing_price': closing_price
                }
                
            except Exception as e:
                clv_reasons[composite_key] = f'erro_processamento: {str(e)[:50]}'
                                
        price_clv_map = {key: val['price_clv'] for key, val in clv_results.items()}
        odds_clv_map = {key: val['odds_clv'] for key, val in clv_results.items()}

        # Mapear usando a chave composta (conditionId + asset)
        df['price_clv'] = df['_composite_key'].map(price_clv_map)
        df['odds_clv'] = df['_composite_key'].map(odds_clv_map)
                
        # Remover colunas auxiliares
        df = df.drop(
            columns=['start_time_unix', '_composite_key'], errors='ignore'
            )
        
        # A partir daqui, temos um df 100% funcional com CLV do user.
       
        return df
