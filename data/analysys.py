import ast
import pandas as pd

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
    def tag_analysys(
        df: pd.DataFrame,
        min_bets: int = 50,
        exclude_tags: list = []
        ):
        """
        Recebe um dataframe e retorna a análise do user por "tag"
        """
        # Método auxiliar para lidar com listas
        def to_list(x):
            if isinstance(x, list):
                return x
            if isinstance(x, str):
                try:
                    v = ast.literal_eval(x)
                    return v if isinstance(v, list) else []
                except:
                    return []
            return []
        
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
