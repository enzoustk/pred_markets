import pandas as pd
import streamlit as st
from helpers import get_exploded_df
from dashboard.ui.formatting import *
from data.analysis import DataAnalyst
from datetime import datetime, timedelta
from dashboard import data_helpers as dh
from dateutil.relativedelta import relativedelta


def header():
    st.image('images/striker_logo/logo-reduzido_negativo.svg', width=150)
    center_text("PolyMarket in-depth Analysis for trader", size=50, bold=True)

    
def user_stats(df: pd.DataFrame) -> None:
    profit, staked, roi = DataAnalyst.calculate_stats(df)
    stats = DataAnalyst.calculate_advanced_stats(df)
    header_columns = st.columns(7)
    
    with header_columns[0]: 
        center_text(f'Profit:', size=24)
        center_text(float_to_dol(profit), bold=True)
    
    with header_columns[1]:
        center_text("ROI", size=24)
        center_text(float_to_pct(roi), bold=True)
    
    with header_columns[2]:
        center_text("Staked", size=24)
        center_text(float_to_dol(staked), bold=True)
    
    with header_columns[3]:
        center_text("Flat Profit", size=24)
        center_text(float_to_units(stats['flat_profit']), bold=True)
    
    with header_columns[4]:
        center_text("Avg Stake", size=24)
        center_text(float_to_dol(stats['avg_stake']), bold=True)
    
    with header_columns[5]:
        center_text("Median Stake", size=24);
        center_text(float_to_dol(stats['median_stake']), bold=True)
    
    with header_columns[6]:
        center_text("Max Drawdown", size=24)
        center_text('Loading...')
    


def cum_profit(df: pd.DataFrame) -> None:
    cum_profit = dh.cum_pnl(df=df, date_column='endDate')
    
    # Gráfico de Lucro acumulado
    st.subheader('Cumulative Profit')
    
    
    st.area_chart(
        cum_profit,
        x='Date',
        y='Cumulative Profit'
    ) 

    
def daily_profit(df: pd.DataFrame) -> None:
    # TODO: Botões de Filtro por data
    daily_profit_data = dh.create_daily_summary(df)
    st.subheader('Daily Profit')
    st.dataframe(
        data=daily_profit_data,
        hide_index=True,
        height=700
        )


def closed_positions(df: pd.DataFrame) -> None:
    
    # TODO: Colorir coluna Profit
    st.subheader('Closed Positions:')
    formated_df = dh.filter_and_format(df=df)
    
    st.dataframe(
        data=formated_df,
        hide_index=True,
        column_order=[
            col for col in formated_df.columns
            if col not in ["Slug", "Tags"]
        ],
        height=450
    )


def tag_df(df: pd.DataFrame) -> None:
    st.subheader('Tag Analisys')
    st.dataframe(
        data=df,
        hide_index=True,
        column_order=[
            col for col in df.columns
            if col not in ["Staked"]],
        height=700
    )


def time_filter_buttons(df):

    # Available filter options
    options = [
        "Current Week",
        "Current Month",
        "Previous Month",
        "Last 3 Months",
        "Last 6 Months",
        "YTD",
        "Last Year",
        "Total",
        "Custom"
    ]

    today = datetime.today()

    # Default values to avoid UnboundLocalError
    start = None
    end = None

    selected = st.pills(
        label="",
        options=options,
        default="Current Month",
    )

    # ------------------------------------------------------------------
    # Period-based filters
    # ------------------------------------------------------------------

    if selected == "Current Week":
        start = today - timedelta(days=today.weekday())  # Monday of current week
        end = today

    elif selected == "Current Month":
        start = today.replace(day=1)
        end = today

    elif selected == "Previous Month":
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        start = last_day_prev_month.replace(day=1)
        end = last_day_prev_month

    elif selected == "Last 3 Months":
        start = today - relativedelta(months=3)
        end = today

    elif selected == "Last 6 Months":
        start = today - relativedelta(months=6)
        end = today

    elif selected == "YTD":
        start = today.replace(month=1, day=1)
        end = today

    elif selected == "Last Year":
        start = datetime(today.year - 1, 1, 1)
        end = datetime(today.year - 1, 12, 31)

    elif selected == "Total":
        # no date filtering
        start = None
        end = None

    elif selected == "Custom":
        start, end = st.date_input(
            "Select a custom date range",
            value=(df["endDate"].min(), df["endDate"].max()),
        )

    return selected, start, end

 
def tag_buttons(tags: list) -> list:

    return st.pills(
        '',
        options=tags,
        selection_mode='multi'
        )

    
def get_filtered_df(
    df: pd.DataFrame,
    tags: list = [],
    start_date=None,
    end_date=None
) -> dict:

    # Normaliza datas
    df["endDate"] = pd.to_datetime(df["endDate"], utc=True).dt.tz_localize(None)

    df["endDate"] = pd.to_datetime(df["endDate"], utc=False, errors="coerce")

    # ---------------------------------------------------------------------
    # 💡 Só aplica filtro se start_date e end_date forem datetime válidos
    # ---------------------------------------------------------------------
    if isinstance(start_date, (datetime, pd.Timestamp)) and \
       isinstance(end_date, (datetime, pd.Timestamp)):
        
        df = df[(df["endDate"] >= start_date) &
                (df["endDate"] <= end_date)]

    # exploded pós-filtro
    exploded_df = get_exploded_df(df=df)

    # ---------------------------------------------------------------------
    # TAG FILTER
    # ---------------------------------------------------------------------
    if tags:
        raw_df = exploded_df[exploded_df["tag"].isin(tags)]
        main_df = dh.filter_and_format(raw_df)
        tag_trades_df = dh.filter_and_format(raw_df)
    else:
        raw_df = df
        main_df = dh.filter_and_format(df)
        tag_trades_df = dh.filter_and_format(exploded_df)

    return {
        "raw": raw_df,
        "main": main_df,
        "exploded": tag_trades_df
    }


