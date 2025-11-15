from dashboard.pages import main_page
from dashboard.ui import elements
import pandas as pd
import streamlit as st
from data.analysis import DataAnalyst
from dashboard import data_helpers as dh


# Importar o dataframe que vamos usar para testes


st.set_page_config(layout="wide")

def generate_dashboard():
    
    # ============================================
    df = pd.read_csv('marketed.csv')
    # ============================================
    tabs = st.tabs(
        ['Dashboard', 'Trading', 'User Analysis'])
    
    # Página Principal
               
    with tabs[0]: 
        'Página para Dashboard'
    
    with tabs[1]:
        'Página para Trading Data'
    
    with tabs[2]: 
        main_page.main_page(df=df)
        
    


generate_dashboard()