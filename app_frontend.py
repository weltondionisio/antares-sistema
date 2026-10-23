"""ANTARES — dashboard epidemiológico em Streamlit.

Arquivos esperados no mesmo diretório:
  - previsoes_municipios.csv
  - Pontos Estratégicos de Soro Antiveneno de Escorpiões.csv
  - logo_antares.jpg (opcional)
Configuração do Gemini: GEMINI_API_KEY nos Secrets do Streamlit.
"""

import html
import os
import unicodedata
import urllib.parse

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google import genai
from google.genai import errors, types


st.set_page_config(
    page_title="ANTARES | Inteligência Epidemiológica",
    page_icon="🦂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# IDENTIDADE VISUAL
# ============================================================
CORES = {
    "navy": "#585E9E",
    "navy_dark": "#454B83",
    "teal": "#6C73B7",
    "teal_light": "#F0EEFA",
    "text": "#2D2A49",
    "muted": "#766F8B",
    "grid": "#ECE8F4",
    "amber": "#E5A544",
    "red": "#D85E55",
}

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --navy:#585E9E; --teal:#6C73B7; --ink:#2D2A49; --muted:#766F8B; }
html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
}
.stApp {
    color: var(--ink);
    background: #F8F7FC;
}
[data-testid="stAppViewContainer"] { background: #F8F7FC; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 1rem; }
.block-container {
    max-width: 1540px;
    padding-top: 1.75rem;
    padding-bottom: 2.5rem;
    padding-left: 2.4rem;
    padding-right: 2.4rem;
}
h1,h2,h3,h4 { font-family:'Manrope','Segoe UI',sans-serif; color:var(--ink); letter-spacing:-.035em; }
p { color:inherit; }
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #585e9e 0%, #4D538B 100%);
    border-right: 1px solid rgba(255,255,255,.09);
}
[data-testid="stSidebar"] > div:first-child { padding-top:1.3rem; }
[data-testid="stSidebar"] * { color: #F9F7FF; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label { color:#F0EEFA !important; font-size:.82rem; font-weight:600; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1px solid #D3CFE4 !important;
    border-radius: 10px !important;
    min-height: 44px;
}
/* Selects: white background, high-contrast BLACK text, including chosen values. */
[data-baseweb="select"] > div {
    background:#FFFFFF !important;
    color:#000000 !important;
    border:1px solid #D3CFE4 !important;
    border-radius:10px !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] input,
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] div {
