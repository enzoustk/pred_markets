import streamlit as st
from dashboard.ui import elements
from dashboard.pages import user_analysis


# Importar o dataframe que vamos usar para testes


st.set_page_config(layout="wide")

def generate_dashboard():
    elements.top_bar()
    
    tabs = st.tabs(
        ['Dashboard', 'Trading', 'User Analysis'])
    
    # Página Principal
               
    with tabs[0]: 
        'Página para Dashboard'
    
    with tabs[1]:
        'Página para Trading Data'
    
    with tabs[2]: 
        user_analysis.user_analysis()
    
    st.divider()
    elements.top_bar()
        
    


generate_dashboard()