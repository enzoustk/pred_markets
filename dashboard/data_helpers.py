import numpy as np
import pandas as pd
from helpers import *
from non_ai_dashboard import ui
from data.analysis import DataAnalyst



def filter_and_format(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Filtrar apenas as colunas usadas
    new_df = df[[
        'endDate', 'title', 'outcome',
        'totalBought', 'avgPrice', 'curPrice',
        'realizedPnl', 'slug', 'tags'
    ]].copy()

    # 2. Renomear
    new_df = new_df.rename(columns={
        'endDate': 'End Date',
        'avgPrice': 'Average Price',
        'totalBought': 'Total Bought',
        'realizedPnl': 'Realized Profit',
        'curPrice': 'Current Price',
        'title': 'Event',
        'outcome': 'Bet',
        'slug': 'Slug',
        'tags': 'Tags'
    })

    # 3. Criar versões formatadas
    df_fmt = pd.DataFrame()

    # Data formatada
    df_fmt["End Date"] = pd.to_datetime(new_df["End Date"]) \
        .dt.strftime("%d/%m/%Y %H:%M")

    # Texto
    df_fmt["Event"] = new_df["Event"]
    df_fmt["Bet"] = new_df["Bet"]
    df_fmt["Slug"] = new_df["Slug"]

    # Números formatados
    df_fmt["Total Bought"] = new_df["Total Bought"].apply(lambda x: f"{x:,}")
    df_fmt["Average Price"] = new_df["Average Price"].apply(lambda x: f"{x:.2f}")
    df_fmt["Current Price"] = new_df["Current Price"].apply(lambda x: f"{x:.2f}")
    df_fmt["Realized Profit"] = new_df["Realized Profit"].apply(lambda x: f"$ {x:,.2f}")

    # Tags (string)
    df_fmt["Tags"] = new_df["Tags"].apply(ui.format_tags)


    # 4. RETORNAR SOMENTE O DF FORMATADO
    return df_fmt

def cum_pnl(
    df: pd.DataFrame,
    pnl_column: str = 'realizedPnl',
    date_column: str = 'endDate'
) -> pd.DataFrame: 
    """
    Recebe um dataframe e retorna um DataFrame com o
    lucro diário e o lucro cumulativo.
    Colunas: ['Date', 'Daily Profit', 'Cumulative Profit']
    """
    df = df.copy()
    
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.sort_values(by=date_column)
    
   
    daily_profit = df.groupby(df[date_column].dt.normalize())[pnl_column].sum()
    out_df = daily_profit.reset_index()
    out_df.columns = ['Date', 'Profit']
    
    # 4. Calcular o lucro CUMULATIVO
    out_df['Cumulative Profit'] = out_df['Profit'].cumsum()
        
    return out_df

def create_daily_summary(
    df: pd.DataFrame,
    pnl_column: str = 'realizedPnl',
    date_column: str = 'endDate'
) -> pd.DataFrame:
    
    df = df.copy()

    df[date_column] = pd.to_datetime(df[date_column])
    df = df.sort_values(by=date_column)
    
    df['staked'] = df['totalBought'] * df['avgPrice']
    df['roi'] = safe_divide(df[pnl_column], df['staked'])

    rows = []

    for date, sub_df in df.groupby(df[date_column].dt.normalize()):
        profit = sub_df[pnl_column].sum()
        bets = len(sub_df)
        roi = safe_divide(profit, sub_df['staked'].sum())
        units = sub_df['roi'].sum()

        rows.append({
            "Date": date,
            "Bets": bets,
            "Profit": profit,
            "ROI": roi,
            "Units": units,
        })

    out = pd.DataFrame(rows).sort_values(by='Date', ascending=False)

    # Formatar coluna de data para YYYY-MM-DD
    out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")

  
    # Aplicar formatações
    
    styler = (
        out.style
            .format({
                "Profit": ui.float_to_dol,
                "ROI": ui.float_to_pct,
                "Units": ui.float_to_dol,
            })
            .map(ui.color_positive_negative, subset=["Profit", "ROI", "Units"])
    )

    return styler

def create_tag_df(
    df: pd.DataFrame,
    ) -> pd.DataFrame:
    # Recebe o dataframe geral e retorna o dataframe de tags
    # 100% Formatado
    
    tag_df = DataAnalyst.tag_analysis(df=df)
    
    tag_df = tag_df.rename(columns={
        'tag': 'Tag',
        'profit': 'Profit',
        'volume': 'Staked',
        'roi': 'ROI',
        'units': 'Units',
        'bets': 'Total Bets',
    })
    
    styler = (
        tag_df.style
            .format({
                'Profit': ui.float_to_dol,
                'Staked': ui.float_to_dol,
                'ROI': ui.float_to_pct,
                'Units': ui.float_to_units,
            })
            .map(
                ui.color_positive_negative,
                subset=['Profit', 'ROI', 'Units'] # Colunas para colorir
            )
    )
    
    return styler