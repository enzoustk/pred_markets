import ast
import pandas as pd
import streamlit as st
from helpers import *


def format_tags(x):
    # Se for lista -> juntar por vírgula
    if isinstance(x, list):
        return ", ".join(map(str, x))

    # Se for string que contém colchetes -> limpar
    if isinstance(x, str) and x.startswith("[") and x.endswith("]"):
        try:
            # tenta interpretar como lista
            import ast
            parsed = ast.literal_eval(x)
            if isinstance(parsed, list):
                return ", ".join(map(str, parsed))
        except:
            pass

    # Se for NaN
    if pd.isna(x):
        return ""

    # fallback
    return str(x)

def center_text(text, size=20, weight="normal", color="#fff", bold=False):
    
    # aplica bold se solicitado
    if bold:
        text = f"<b>{text}</b>"
    
    st.markdown(
        f"""
        <p style='
            text-align:center;
            font-size:{size}px;
            font-weight:{weight};
            color:{color};
        '>
            {text}
        </p>
        """,
        unsafe_allow_html=True
    )

def color_positive_negative(v):
    if v > 0:
        return "color: #00FF4C; font-weight:bold;"
    elif v < 0:
        return "color: #FF1744; font-weight:bold;"
    return ""

def float_to_dol(value, decimals=2):
    """Formata um float para dólar (US$)."""
    if value is None:
        return "$ 0.00"
    return f"$ {value:,.{decimals}f}"

def float_to_pct(value, decimals=2):
    """Formata um float para percentual."""
    if value is None:
        return "0%"
    return f"{value * 100:.{decimals}f}%"

def float_to_units(value, decimals = 2):
    if value is None:
        return "0.00u"
    return f"{value:,.{decimals}f}u"