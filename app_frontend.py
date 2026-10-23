"""ANTARES — dashboard epidemiológico em Streamlit, tema roxo v2.1.

Arquivos esperados no mesmo diretório:
  - previsoes_municipios.csv
  - Pontos Estratégicos de Soro Antiveneno de Escorpiões.csv
  - logo_antares.jpg (opcional)
Configuração do Gemini: GEMINI_API_KEY nos Secrets do Streamlit.
"""

import base64
import html
import io
import os
from pathlib import Path
import unicodedata
import urllib.parse

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from scipy.spatial import cKDTree
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
# Paleta original do ANTARES.
ROXO_PRINCIPAL = "#6C73B7"
ROXO_LATERAL = "#585E9E"
CORES = {
    "roxo": ROXO_PRINCIPAL,
    "roxo_escuro": ROXO_LATERAL,
    "roxo_claro": "#F0EEFA",
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
:root { --antares-purple:#6C73B7; --antares-sidebar:#585E9E; --ink:#2D2A49; --muted:#766F8B; }
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
/* Preserve white for sidebar labels, without overriding select values. */
[data-testid="stSidebar"] .sidebar-brand,
[data-testid="stSidebar"] .sidebar-kicker,
[data-testid="stSidebar"] .sidebar-help,
[data-testid="stSidebar"] .sidebar-footer,
[data-testid="stSidebar"] [data-testid="stRadio"] p,
[data-testid="stSidebar"] [data-testid="stRadio"] span {
    color: #F9F7FF;
}
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
    color:#000000 !important;
    -webkit-text-fill-color:#000000 !important;
}
[data-baseweb="select"] svg,
[data-testid="stSidebar"] [data-baseweb="select"] svg {fill:#413B6C !important; color:#413B6C !important;}
/* Opened dropdown is rendered separately from the sidebar in Streamlit. */
[data-baseweb="popover"] [role="listbox"],
[role="listbox"] {background:#FFFFFF !important;color:#000000 !important;}
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
[role="listbox"] [role="option"],
[role="listbox"] [role="option"] * {
    color:#000000 !important;
    -webkit-text-fill-color:#000000 !important;
}
[role="listbox"] [role="option"][aria-selected="true"] {background:#F0EEFA !important;}
[role="listbox"] [role="option"]:hover {background:#F4F1FB !important;}
[data-baseweb="select"] input::placeholder {color:#444444 !important;-webkit-text-fill-color:#444444 !important;}
[data-testid="stSidebar"] div[role="radiogroup"] label { padding:.3rem 0; }
[data-testid="stSidebar"] [data-testid="stButton"] button {
    border:1px solid #BFC0DF;
    background:transparent;
    color:#F9F7FF !important;
    border-radius:10px;
    min-height:42px;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background:#6C73B7;
    border-color:#FFFFFF;
}
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.16); }
.sidebar-brand { padding: 10px 0 26px; display:flex; gap:12px; align-items:center; }
.sidebar-icon {
    display:flex; align-items:center; justify-content:center;
    width:44px; height:44px; border-radius:14px;
    background:rgba(238,232,255,.16); border:1px solid rgba(238,232,255,.28);
    color:#EFE9FF; font-size:23px;
}
.sidebar-wordmark { font-family:'Manrope',sans-serif; font-weight:800; font-size:1.35rem; letter-spacing:.12em; color:white; }
.sidebar-sub { font-size:.62rem; color:#ECE9FF; letter-spacing:.16em; font-weight:700; }
.sidebar-kicker { font-size: .66rem; font-weight:800; letter-spacing:.18em; color:#EEEAFE; margin:16px 0 9px; }
.sidebar-help {
    margin-top:1.6rem; padding:16px; border:1px solid #9EA2CB;
    border-radius:14px; background:rgba(255,255,255,.04);
    font-size:.78rem; line-height:1.55; color:#F4F1FF;
}
.sidebar-help b {color:#F4F1FF;}
.sidebar-footer {font-size:.67rem;color:#ECE9FF;line-height:1.7;margin-top:13px;}
.hero {
    border-radius:22px;
    background:
      radial-gradient(ellipse at 88% 14%,rgba(203,193,255,.24) 0, transparent 34%),
      radial-gradient(ellipse at 70% 100%,rgba(128,116,197,.20) 0, transparent 39%),
      linear-gradient(112deg,#6c73b7 0%,#585e9e 100%);
    box-shadow: 0 15px 38px rgba(11,37,58,.08);
    padding:30px 36px;
    margin-bottom:22px;
    overflow:hidden;
    position:relative;
}
.hero:after {
    content:""; position:absolute; right:22px; bottom:-95px;
    width:330px; height:330px; border:1px solid rgba(237,232,255,.15);
    border-radius:50%; box-shadow:0 0 0 55px rgba(237,232,255,.055),0 0 0 110px rgba(237,232,255,.04);
    pointer-events:none;
}
.hero-kicker { color:#F7F1FF; letter-spacing:.20em; font-size:.68rem; font-weight:800; margin-bottom:11px; }
.hero-title {color:#FFFFFF;font-family:'Manrope',sans-serif;font-size:clamp(1.65rem,2.35vw,2.7rem);font-weight:800;line-height:1.19;letter-spacing:-.048em;margin:0 0 12px;max-width:850px;}
.hero-description {color:#F3F1FF;font-size:.91rem;line-height:1.65;margin:0;max-width:720px;}
.hero-meta {margin-top:19px;display:flex;gap:8px;flex-wrap:wrap;}
.hero-chip {display:inline-block;padding:6px 12px;border:1px solid rgba(250,247,255,.29);border-radius:999px;background:rgba(255,255,255,.06);color:#F8F6FF;font-size:.71rem;font-weight:600;}
.topline {display:flex;align-items:center;justify-content:space-between;margin:0 0 15px;gap:15px;}
.topline-left {font-size:.70rem;letter-spacing:.16em;font-weight:800;color:#827B97;}
.topline-right {font-size:.72rem;color:#8E88A3;}
.metric-card {background:#FFFFFF;border:1px solid #E8E3F2;border-radius:16px;padding:18px 19px 16px;min-height:133px;box-shadow:0 3px 10px rgba(14,52,75,.025);}
.metric-top {display:flex;justify-content:space-between;align-items:center;gap:6px;margin-bottom:13px;}
.metric-label {font-size:.74rem;font-weight:700;letter-spacing:.015em;color:#746F8D;}
.metric-icon {width:31px;height:31px;border-radius:9px;background:#F0EDFB;color:#6663A9;display:flex;align-items:center;justify-content:center;font-size:17px;}
.metric-value {font-family:'Manrope',sans-serif;font-size:clamp(1.2rem,1.8vw,1.95rem);font-weight:800;line-height:1.18;color:#2D2A49;letter-spacing:-.06em;}
.metric-note {font-size:.70rem;color:#8B86A0;margin-top:9px;}
.section-overline {font-size:.69rem;font-weight:800;letter-spacing:.15em;color:#6564AC;margin-bottom:5px;}
.section-title {font-size:1.27rem;font-family:'Manrope',sans-serif;font-weight:800;color:#2D2A49;letter-spacing:-.035em;line-height:1.3;margin:0 0 5px;}
.section-desc {font-size:.78rem;color:#79728D;margin:0 0 17px;line-height:1.5;}
.card-shell {background:#FFFFFF;border:1px solid #E8E3F2;border-radius:17px;padding:20px 19px 15px;box-shadow:0 4px 13px rgba(13,41,61,.026);}
.card-shell [data-testid="stPlotlyChart"] { border-radius: 12px;overflow:hidden; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-anchor) {
    background:#FFFFFF;
    border:1px solid #E8E3F2;
    border-radius:17px;
    box-shadow:0 4px 13px rgba(13,41,61,.026);
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-anchor) > div { padding: 18px 18px 10px; }
.chart-anchor {display:none;}
.support-box {padding:13px 15px;border-radius:11px;background:#F3F0FB;border:1px solid #E5DFF4;color:#615A8B;font-size:.77rem;line-height:1.55;}
.support-box.warning {background:#FFF7EC;border-color:#FBE5C4;color:#9D722D;}
.section-gap {height:20px;}
hr {border-color:#E5E0EF !important;}
[data-testid="stPlotlyChart"] {margin-top:2px;}
[data-testid="stExpander"] {border:1px solid #E5E0EF;border-radius:14px;background:#FFFFFF;}
[data-testid="stExpander"] summary {color:#322E53;font-weight:600;}
[data-testid="stAlert"] {border-radius:12px;}
[data-testid="stPopover"] button {
    border-radius:12px;
    background:#6C73B7;
    border:1px solid #6C73B7;
    min-height:43px;
    color:white;
    font-weight:700;
    box-shadow:0 5px 15px rgba(88,94,158,.22);
}
[data-testid="stPopover"] button:hover {background:#585E9E;border-color:#585E9E;color:white;}
[data-testid="stPopover"] button * {color:inherit !important;}
[data-testid="stPopoverBody"] {border-radius:16px;background:#FFFFFF;}
[data-testid="stPopoverBody"] * {color:#2D2A49;}
[data-testid="stPopoverBody"] [data-testid="stChatMessage"] {border-radius:11px;}
[data-testid="stPopoverBody"] textarea,[data-testid="stPopoverBody"] input {color:#2D2A49 !important;}
[data-testid="stMain"] a { color:#6263AE; }
[data-testid="stMain"] a:hover {color:#4D4E94;}
.footer {padding:18px 2px 1px;border-top:1px solid #E5E0EF;font-size:.74rem;color:#807B97;line-height:1.7;}
.footer strong {color:#413B6C;}
@media (max-width: 1000px) {
    .block-container {padding-left:1.1rem;padding-right:1.1rem;padding-top:1.2rem;}
    .hero {padding:25px 22px;border-radius:18px;}
    .hero-title {font-size:1.65rem;}
    .metric-card {min-height:121px;}
}

/* Imagem do logo original no início da área principal. */
[data-testid="stMain"] div[data-testid="stImage"] img {
    object-fit: contain;
    max-height: 205px;
}

/* ANTARES v2.1: alta especificidade para os selects (valor selecionado). */
section[data-testid="stSidebar"] div[data-baseweb="select"],
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-color: #D3CFE4 !important;
    color-scheme: light;
}
/* Todos os níveis do seletor: texto, span, valor, input e placeholder. */
section[data-testid="stSidebar"] [data-baseweb="select"] div,
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] input,
section[data-testid="stSidebar"] [data-baseweb="select"] p,
[data-testid="stMain"] [data-baseweb="select"] div,
[data-testid="stMain"] [data-baseweb="select"] span,
[data-testid="stMain"] [data-baseweb="select"] input,
[data-testid="stMain"] [data-baseweb="select"] p {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] input::placeholder,
[data-testid="stMain"] [data-baseweb="select"] input::placeholder {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
}
/* Menus BaseWeb normalmente aparecem fora do contêiner da barra lateral. */
body [data-baseweb="popover"] [role="listbox"],
body [data-baseweb="popover"] [data-baseweb="menu"],
body [role="listbox"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    color-scheme: light;
}
body [data-baseweb="popover"] [role="option"],
body [data-baseweb="popover"] [role="option"] *,
body [data-baseweb="menu"] [role="option"],
body [data-baseweb="menu"] [role="option"] *,
body [role="listbox"] [role="option"],
body [role="listbox"] [role="option"] * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
body [role="listbox"] [aria-selected="true"],
body [data-baseweb="menu"] [aria-selected="true"] {
    background-color: #E9E5F5 !important;
}
body [role="listbox"] [role="option"]:hover,
body [data-baseweb="menu"] [role="option"]:hover {
    background-color: #F0EEFA !important;
}

/* FINAL OVERRIDE: black selected values and dropdown options. */
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [role="combobox"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    color-scheme: light;
    opacity: 1 !important;
}

/* Includes selected text, e.g. Todos, and nested typography. */
[data-testid="stSelectbox"] [data-baseweb="select"] *:not(svg):not(path),
[data-testid="stSelectbox"] [data-baseweb="select"] input {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
    filter: none !important;
}

/* Search placeholder and input in selectboxes. */
[data-testid="stSelectbox"] input::placeholder,
[data-baseweb="popover"] input::placeholder {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
}

/* Dropdown options are rendered in an external BaseWeb portal. */
body [data-baseweb="popover"] [role="listbox"],
body [data-baseweb="popover"] [data-baseweb="menu"],
body [role="listbox"],
body [data-baseweb="menu"] {
    background-color: #FFFFFF !important;
    color-scheme: light;
}
body [data-baseweb="popover"] [role="option"],
body [data-baseweb="popover"] [role="option"] *:not(svg):not(path),
body [role="listbox"] [role="option"],
body [role="listbox"] [role="option"] *:not(svg):not(path),
body [data-baseweb="menu"] [role="option"],
body [data-baseweb="menu"] [role="option"] *:not(svg):not(path),
body [data-baseweb="menu"] li,
body [data-baseweb="menu"] li *:not(svg):not(path) {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# LEITURA E PREPARAÇÃO DOS DADOS
# ============================================================
ORDEM_MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MAPA_ESTADOS = {
    "11": "Rondônia", "12": "Acre", "13": "Amazonas", "14": "Roraima", "15": "Pará", "16": "Amapá", "17": "Tocantins",
    "21": "Maranhão", "22": "Piauí", "23": "Ceará", "24": "Rio Grande do Norte", "25": "Paraíba", "26": "Pernambuco",
    "27": "Alagoas", "28": "Sergipe", "29": "Bahia", "31": "Minas Gerais", "32": "Espírito Santo", "33": "Rio de Janeiro",
    "35": "São Paulo", "41": "Paraná", "42": "Santa Catarina", "43": "Rio Grande do Sul", "50": "Mato Grosso do Sul",
    "51": "Mato Grosso", "52": "Goiás", "53": "Distrito Federal",
}


def texto_normalizado(valor):
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).strip().lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def formatar_numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def h(valor):
    return html.escape(str(valor))


@st.cache_data(show_spinner=False)
def carregar_dados():
    df = pd.read_csv("previsoes_municipios.csv")
    necessarias = {"estado", "municipio", "mes", "acidentes_previstos", "latitude", "longitude"}
    faltantes = necessarias - set(df.columns)
    if faltantes:
        raise ValueError("Colunas ausentes no CSV de previsões: " + ", ".join(sorted(faltantes)))
    df["estado_raw"] = df["estado"].astype(str).str.strip()
    df["estado"] = df["estado_raw"].map(MAPA_ESTADOS).fillna(df["estado_raw"])
    df["municipio"] = df["municipio"].astype(str).str.strip()
    df["acidentes_previstos"] = pd.to_numeric(df["acidentes_previstos"], errors="coerce") / 1000.0
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["mes"] = pd.Categorical(df["mes"], categories=ORDEM_MESES, ordered=True)
    return df


@st.cache_data(show_spinner=False)
def carregar_pontos_soro():
    caminho = "Pontos Estratégicos de Soro Antiveneno de Escorpiões.csv"
    if os.path.exists(caminho):
        try:
            df_soro = pd.read_csv(caminho, sep=";", dtype=str).fillna("")
            if len(df_soro.columns) == 1:
                df_soro = pd.read_csv(caminho, sep=",", dtype=str).fillna("")
        except Exception:
            df_soro = pd.DataFrame()
    else:
        df_soro = pd.DataFrame()
    df_soro.columns = [c.strip() for c in df_soro.columns]
    for coluna in ["Estado", "Município", "Unidade de Saúde", "Endereço", "Contato", "CNES"]:
        if coluna not in df_soro.columns:
            df_soro[coluna] = "Indisponível"
    def gerar_link_maps(linha):
        busca = f"{linha['Unidade de Saúde']}, {linha['Município']} - {linha['Estado']}, {linha['Endereço']}"
        return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(busca)
    df_soro["google_maps_link"] = df_soro.apply(gerar_link_maps, axis=1)
    return df_soro


try:
    df_base = carregar_dados()
except Exception as erro:
    st.error(f"Não foi possível carregar previsoes_municipios.csv: {erro}")
    st.stop()
df_soro_base = carregar_pontos_soro()

# Tratamento original: substituição dos valores <= 0 pela mediana municipal.
medianas_por_mun = df_base.groupby(["estado", "municipio"], observed=True)["acidentes_previstos"].transform("median")
mediana_geral = df_base["acidentes_previstos"].median()
if pd.isna(mediana_geral) or mediana_geral <= 0:
    mediana_geral = 0.01
df_base["acidentes_ajustados"] = df_base["acidentes_previstos"]
mask_zero = df_base["acidentes_ajustados"].isna() | (df_base["acidentes_ajustados"] <= 0)
df_base.loc[mask_zero, "acidentes_ajustados"] = medianas_por_mun[mask_zero]
df_base["acidentes_ajustados"] = df_base["acidentes_ajustados"].fillna(mediana_geral)
df_base.loc[df_base["acidentes_ajustados"] <= 0, "acidentes_ajustados"] = mediana_geral


# ============================================================
# MENU LATERAL E FILTROS
# ============================================================
def limpar_municipio():
    st.session_state["municipio_filtro"] = "Todos"
    st.session_state["unidade_clicada"] = "Selecione..."


def limpar_filtros():
    st.session_state["estado_filtro"] = "Todos"
    st.session_state["municipio_filtro"] = "Todos"
    st.session_state["modo_mapa"] = "Mapa de Risco"
    st.session_state["unidade_clicada"] = "Selecione..."


with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><div class="sidebar-icon">◈</div>'
        '<div><div class="sidebar-wordmark">ANTARES</div>'
        '<div class="sidebar-sub">EPIDEMIOLOGICAL INTELLIGENCE</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-kicker">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    tipo_mapa = st.radio(
        "Camada de visualização",
        ["Mapa de Risco", "Mapa de Centros de Atendimento"],
        format_func=lambda item: "◉  Intensidade das previsões" if item == "Mapa de Risco" else "✚  Centros de soro antiveneno",
        key="modo_mapa",
    )
    st.divider()
    st.markdown('<div class="sidebar-kicker">FILTROS GEOGRÁFICOS</div>', unsafe_allow_html=True)
    lista_estados = ["Todos"] + sorted(df_base["estado"].dropna().unique().tolist())
    estado_selec = st.selectbox("Estado", lista_estados, key="estado_filtro", on_change=limpar_municipio)
    if estado_selec == "Todos":
        municipios = df_base["municipio"]
    else:
        municipios = df_base.loc[df_base["estado"] == estado_selec, "municipio"]
    opcoes_mun = ["Todos"] + sorted(municipios.dropna().unique().tolist())
    if st.session_state.get("municipio_filtro", "Todos") not in opcoes_mun:
        st.session_state["municipio_filtro"] = "Todos"
    municipio_selec = st.selectbox("Município", opcoes_mun, key="municipio_filtro")
    st.button("↺  Limpar filtros", use_container_width=True, on_click=limpar_filtros)
    st.markdown(
        '<div class="sidebar-help"><b>Sobre as previsões</b><br>'
        'Explore estimativas municipais de acidentes por escorpiões e a rede de pontos estratégicos '
        'de soro antiveneno. Os mapas refletem os filtros selecionados.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-footer">ANTARES • USP<br>Pesquisa apoiada pela FAPESP<br>Tema roxo · v2.1</div>', unsafe_allow_html=True)


df_filtrado = df_base
if estado_selec != "Todos":
    df_filtrado = df_filtrado.loc[df_filtrado["estado"] == estado_selec]
if municipio_selec != "Todos":
    df_filtrado = df_filtrado.loc[df_filtrado["municipio"] == municipio_selec]

df_soro_filtrado = df_soro_base
if estado_selec != "Todos":
    df_soro_filtrado = df_soro_filtrado.loc[
        df_soro_filtrado["Estado"].map(texto_normalizado) == texto_normalizado(estado_selec)
    ]
if municipio_selec != "Todos":
    df_soro_filtrado = df_soro_filtrado.loc[
        df_soro_filtrado["Município"].map(texto_normalizado) == texto_normalizado(municipio_selec)
    ]

qtd_municipios = df_filtrado[["estado", "municipio"]].drop_duplicates().shape[0]
qtd_estados = df_filtrado["estado"].nunique()
qtd_centros = len(df_soro_filtrado)
total_previsoes = df_filtrado["acidentes_ajustados"].sum() * 1000
regiao = municipio_selec if municipio_selec != "Todos" else (estado_selec if estado_selec != "Todos" else "Brasil")

# ============================================================
# CABEÇALHO
# ============================================================
# Usa o logo verdadeiro, buscando primeiro ao lado deste arquivo Python.
# Assim o Streamlit Cloud nao depende do diretorio de onde o processo foi iniciado.
def encontrar_logo():
    diretorios = [Path(__file__).resolve().parent, Path.cwd()]
    nomes = ["logo_antares.jpg", "logo_antares.jpeg", "logo_antares.png"]
    for diretorio in diretorios:
        for nome in nomes:
            caminho = diretorio / nome
            if caminho.is_file():
                return caminho
    return None


logo_arquivo = encontrar_logo()
if logo_arquivo is not None:
    _, coluna_logo, _ = st.columns([1, 3, 1])
    with coluna_logo:
        st.image(str(logo_arquivo), use_container_width=True)
else:
    st.markdown(
        '<div style="text-align:center;padding:12px 0 20px;'
        'font-weight:800;font-size:1.55rem;letter-spacing:.14em;color:#585E9E">'
        'ANTARES</div>',
        unsafe_allow_html=True,
    )
    st.caption("Para exibir a logo original, mantenha logo_antares.jpg na pasta do aplicativo.")

st.markdown(
    '<div class="topline"><div class="topline-left">VISÃO GERAL / ESCORPIONISMO</div>'
    '<div class="topline-right">Sistema preditivo • Brasil</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero">'
    '<div class="hero-kicker">▰  SISTEMA ANTARES · INTELIGÊNCIA EPIDEMIOLÓGICA</div>'
    '<div class="hero-title">Dados que ajudam a antecipar cenários.</div>'
    '<p class="hero-description">Explore a distribuição geográfica e a dinâmica sazonal '
    'das previsões de acidentes por escorpiões, com consulta à rede de atendimento com soro antiveneno.</p>'
    f'<div class="hero-meta"><span class="hero-chip">◉ Área selecionada: {h(regiao)}</span>'
    '<span class="hero-chip">◷ Visão municipal e mensal</span>'
    '<span class="hero-chip">✦ Modelagem preditiva</span></div>'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# INDICADORES PRINCIPAIS
# ============================================================
def mostrar_cartao(titulo, valor, nota, icone):
    st.markdown(
        '<div class="metric-card">'
        f'<div class="metric-top"><span class="metric-label">{h(titulo)}</span>'
        f'<span class="metric-icon">{icone}</span></div>'
        f'<div class="metric-value">{h(valor)}</div>'
        f'<div class="metric-note">{h(nota)}</div></div>',
        unsafe_allow_html=True,
    )


st.markdown('<div class="section-overline">INDICADORES DO RECORTE</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4, gap="small")
with k1:
    mostrar_cartao("Acidentes previstos", formatar_numero(total_previsoes), "Total estimado no recorte", "↗")
with k2:
    mostrar_cartao("Municípios", formatar_numero(qtd_municipios), "Com previsões disponíveis", "▦")
with k3:
    mostrar_cartao("Unidades federativas", str(qtd_estados), "Abrangência territorial", "◎")
with k4:
    mostrar_cartao("Pontos de soro", formatar_numero(qtd_centros), "Registros na base consultada", "✚")

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# ============================================================
# MAPA: INTERPOLAÇÃO IDW SOBRE GRADE CONTÍNUA
# ============================================================
# Limite territorial simplificado: Natural Earth 1:110m, domínio público.
# Usado apenas para recortar a interpolação ao território brasileiro.
LIMITE_BRASIL = [[-53.374,-33.768],[-53.651,-33.202],[-53.21,-32.728],[-53.788,-32.047],[-54.572,-31.495],[-55.602,-30.854],[-55.973,-30.883],[-56.976,-30.11],[-57.625,-30.216],[-56.291,-28.853],[-55.162,-27.882],[-54.491,-27.475],[-53.649,-26.923],[-53.628,-26.125],[-54.13,-25.548],[-54.625,-25.739],[-54.429,-25.162],[-54.293,-24.571],[-54.293,-24.021],[-54.653,-23.84],[-55.028,-24.001],[-55.401,-23.957],[-55.518,-23.572],[-55.611,-22.656],[-55.798,-22.357],[-56.473,-22.086],[-56.882,-22.282],[-57.937,-22.09],[-57.871,-20.733],[-58.166,-20.177],[-57.854,-19.97],[-57.95,-19.4],[-57.676,-18.962],[-57.498,-18.174],[-57.735,-17.552],[-58.281,-17.272],[-58.388,-16.877],[-58.241,-16.3],[-60.158,-16.258],[-60.543,-15.094],[-60.251,-15.077],[-60.264,-14.646],[-60.459,-14.354],[-60.503,-13.776],[-61.084,-13.479],[-61.713,-13.489],[-62.127,-13.199],[-62.803,-13.001],[-63.196,-12.627],[-64.316,-12.462],[-65.402,-11.566],[-65.322,-10.896],[-65.445,-10.511],[-65.338,-9.762],[-66.647,-9.931],[-67.174,-10.307],[-68.048,-10.712],[-68.271,-11.015],[-68.786,-11.036],[-69.53,-10.952],[-70.094,-11.124],[-70.549,-11.009],[-70.482,-9.49],[-71.302,-10.079],[-72.185,-10.054],[-72.563,-9.52],[-73.227,-9.462],[-73.015,-9.033],[-73.571,-8.424],[-73.987,-7.524],[-73.723,-7.341],[-73.724,-6.919],[-73.12,-6.63],[-73.22,-6.089],[-72.965,-5.741],[-72.892,-5.275],[-71.748,-4.594],[-70.929,-4.402],[-70.795,-4.251],[-69.894,-4.298],[-69.444,-1.556],[-69.42,-1.123],[-69.577,-0.55],[-70.021,-0.185],[-70.016,0.541],[-69.452,0.706],[-69.252,0.603],[-69.219,0.986],[-69.805,1.089],[-69.817,1.715],[-67.869,1.692],[-67.538,2.037],[-67.26,1.72],[-67.065,1.13],[-66.876,1.253],[-66.326,0.724],[-65.548,0.789],[-65.355,1.095],[-64.611,1.329],[-64.199,1.493],[-64.083,1.916],[-63.369,2.201],[-63.423,2.411],[-64.27,2.497],[-64.409,3.127],[-64.368,3.797],[-64.816,4.056],[-64.629,4.148],[-63.888,4.021],[-63.093,3.771],[-62.805,4.007],[-62.085,4.162],[-60.967,4.536],[-60.601,4.918],[-60.734,5.2],[-60.214,5.244],[-59.981,5.014],[-60.111,4.575],[-59.767,4.424],[-59.538,3.959],[-59.815,3.606],[-59.975,2.755],[-59.719,2.25],[-59.646,1.787],[-59.031,1.318],[-58.54,1.268],[-58.429,1.464],[-58.113,1.507],[-57.661,1.683],[-57.336,1.949],[-56.783,1.864],[-56.539,1.9],[-55.996,1.818],[-55.906,2.022],[-56.073,2.221],[-55.973,2.51],[-55.57,2.422],[-55.098,2.524],[-54.525,2.312],[-54.088,2.106],[-53.779,2.377],[-53.555,2.335],[-53.418,2.053],[-52.94,2.125],[-52.556,2.505],[-52.249,3.241],[-51.658,4.156],[-51.317,4.203],[-51.07,3.65],[-50.509,1.902],[-49.974,1.736],[-49.947,1.046],[-50.699,0.223],[-50.388,-0.078],[-48.621,-0.235],[-48.584,-1.238],[-47.825,-0.582],[-46.567,-0.941],[-44.906,-1.552],[-44.418,-2.138],[-44.582,-2.691],[-43.419,-2.383],[-41.473,-2.912],[-39.979,-2.873],[-38.5,-3.701],[-37.223,-4.821],[-36.453,-5.109],[-35.598,-5.15],[-35.235,-5.465],[-34.896,-6.738],[-34.73,-7.343],[-35.128,-8.996],[-35.637,-9.649],[-37.047,-11.041],[-37.684,-12.171],[-38.424,-13.038],[-38.674,-13.058],[-38.953,-13.793],[-38.882,-15.667],[-39.161,-17.208],[-39.267,-17.868],[-39.584,-18.262],[-39.761,-19.599],[-40.775,-20.905],[-40.945,-21.937],[-41.754,-22.371],[-41.988,-22.97],[-43.075,-22.968],[-44.648,-23.352],[-45.352,-23.797],[-46.472,-24.089],[-47.649,-24.885],[-48.495,-25.877],[-48.641,-26.624],[-48.475,-27.176],[-48.662,-28.186],[-48.888,-28.674],[-49.587,-29.224],[-50.697,-30.984],[-51.576,-31.778],[-52.256,-32.245],[-52.712,-33.197],[-53.374,-33.768]]

ESCALA_INTENSIDADE = [
    (0.00, "#F9E27D"),
    (0.20, "#FFD15D"),
    (0.40, "#FFAC40"),
    (0.60, "#FF7835"),
    (0.78, "#F34432"),
    (0.90, "#D91F2A"),
    (1.00, "#AC0824"),
]


def mascara_brasil(longitudes, latitudes):
    """Testa pontos dentro do contorno brasileiro (ray casting vetorizado)."""
    xx = np.asarray(longitudes, dtype=float).ravel()
    yy = np.asarray(latitudes, dtype=float).ravel()
    mask = np.zeros(xx.shape, dtype=bool)
    polygon = np.asarray(LIMITE_BRASIL, dtype=float)
    for (x1, y1), (x2, y2) in zip(polygon[:-1], polygon[1:]):
        if y1 == y2:
            continue
        atravessa = (y1 > yy) != (y2 > yy)
        corte = x1 + (yy - y1) * (x2 - x1) / (y2 - y1)
        mask ^= atravessa & (xx < corte)
    return mask.reshape(np.shape(longitudes))


def para_xyz(latitudes, longitudes):
    """Converte latitude/longitude em coordenadas sobre uma esfera unitária."""
    latitude = np.radians(np.asarray(latitudes, dtype=float))
    longitude = np.radians(np.asarray(longitudes, dtype=float))
    return np.column_stack((
        np.cos(latitude) * np.cos(longitude),
        np.cos(latitude) * np.sin(longitude),
        np.sin(latitude),
    ))


def interpolar_idw(lats_amostras, lons_amostras, ranks, lats_grid, lons_grid):
    """IDW em distâncias esféricas com os 8 vizinhos mais próximos."""
    pontos = para_xyz(lats_amostras, lons_amostras)
    consultas = para_xyz(lats_grid, lons_grid)
    k = min(8, len(pontos))
    distancias, indices = cKDTree(pontos).query(consultas, k=k)
    distancias = np.asarray(distancias).reshape(-1, k)
    indices = np.asarray(indices).reshape(-1, k)
    pesos = 1.0 / np.maximum(distancias, 1e-9) ** 3.2
    pesos /= pesos.sum(axis=1, keepdims=True)
    return np.sum(pesos * np.asarray(ranks)[indices], axis=1)


def rgb_da_intensidade(valores):
    """Transforma percentis interpolados em escala amarela até vermelho-escuro."""
    pontos = np.array([x for x, _ in ESCALA_INTENSIDADE], dtype=float)
    cores = np.array([
        [int(c[i:i + 2], 16) for i in (1, 3, 5)]
        for _, c in ESCALA_INTENSIDADE
    ], dtype=float)
    valores = np.clip(np.asarray(valores, dtype=float), 0, 1)
    return np.column_stack([np.interp(valores, pontos, cores[:, i]) for i in range(3)]).astype(np.uint8)


@st.cache_data(show_spinner=False, max_entries=8)
def criar_camada_idw(amostras, oeste, leste, sul, norte, largura=650):
    """Gera PNG transparente, colorido em TODAS as células terrestres do recorte."""
    # Grade uniforme em Mercator para alinhamento com o mapa de base.
    altura = max(220, int(largura * (norte - sul) / max(leste - oeste, .01)))
    altura = min(750, altura)
    coluna_lon = np.linspace(oeste, leste, largura)
    mercator = lambda lat: np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    linhas_y = np.linspace(mercator(norte), mercator(sul), altura)
    linha_lat = np.degrees(2 * np.arctan(np.exp(linhas_y)) - np.pi / 2)
    lon_grid, lat_grid = np.meshgrid(coluna_lon, linha_lat)
    dentro = mascara_brasil(lon_grid, lat_grid)

    rgba = np.zeros((altura, largura, 4), dtype=np.uint8)
    if dentro.any():
        pontos = np.asarray(amostras, dtype=float)
        interpolados = interpolar_idw(
            pontos[:, 0], pontos[:, 1], pontos[:, 2],
            lat_grid[dentro], lon_grid[dentro],
        )
        rgba[dentro, :3] = rgb_da_intensidade(interpolados)
        rgba[dentro, 3] = 225  # O menor valor também fica visivelmente colorido.

    buffer = io.BytesIO()
    Image.fromarray(rgba).save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return "data:image/png;base64," + encoded


# ============================================================
# VISUALIZAÇÃO PRINCIPAL
# ============================================================
col_mapa, col_lateral = st.columns([1.37, 1], gap="medium")

with col_mapa:
    with st.container(border=True):
        st.markdown('<div class="chart-anchor"></div>', unsafe_allow_html=True)
        if tipo_mapa == "Mapa de Risco":
            st.markdown('<div class="section-overline">DISTRIBUIÇÃO GEOGRÁFICA</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Mapa de intensidade prevista</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-desc">Superfície IDW da intensidade relativa das previsões municipais, sem espaços artificiais de baixa densidade</div>', unsafe_allow_html=True)

            df_mapa = (
                df_filtrado.dropna(subset=["latitude", "longitude"])
                .groupby(["estado", "municipio", "latitude", "longitude"], observed=True)["acidentes_ajustados"]
                .sum().reset_index()
            )
            if df_mapa.empty:
                st.info("Não há coordenadas disponíveis para este recorte.")
            else:
                # Percentis dos municípios preservam os contrastes de intensidade.
                df_mapa["intensidade"] = df_mapa["acidentes_ajustados"].rank(pct=True)
                df_mapa["total_previsto"] = df_mapa["acidentes_ajustados"] * 1000

                if municipio_selec != "Todos":
                    zoom, margem = 8, 0.85
                elif estado_selec != "Todos":
                    zoom, margem = 6, 1.4
                else:
                    zoom, margem = 3, 0.65

                if estado_selec == "Todos" and municipio_selec == "Todos":
                    oeste, leste, sul, norte = -74.65, -34.0, -34.4, 5.9
                else:
                    oeste = max(-74.65, float(df_mapa["longitude"].min()) - margem)
                    leste = min(-34.0, float(df_mapa["longitude"].max()) + margem)
                    sul = max(-34.4, float(df_mapa["latitude"].min()) - margem)
                    norte = min(5.9, float(df_mapa["latitude"].max()) + margem)

                centro = {
                    "lat": float(df_mapa["latitude"].mean()),
                    "lon": float(df_mapa["longitude"].mean()),
                }
                if len(df_mapa) >= 3:
                    pontos_idw = tuple(
                        map(tuple, df_mapa[["latitude", "longitude", "intensidade"]].to_numpy())
                    )
                    camada = criar_camada_idw(pontos_idw, oeste, leste, sul, norte)
                    fig_mapa = go.Figure()
                    # A camada é um raster georreferenciado, não um mapa de densidade.
                    fig_mapa.update_layout(map={
                        "style": "carto-positron",
                        "center": centro,
                        "zoom": zoom,
                        "layers": [{
                            "sourcetype": "image", "type": "raster", "source": camada,
                            "coordinates": [
                                [oeste, norte], [leste, norte],
                                [leste, sul], [oeste, sul],
                            ],
                            "below": "traces", "opacity": 0.96,
                        }],
                    })
                    # Marcadores praticamente transparentes mantêm o hover municipal.
                    fig_mapa.add_trace(go.Scattermap(
                        lat=df_mapa["latitude"], lon=df_mapa["longitude"],
                        mode="markers", name="Municípios",
                        customdata=list(zip(
                            df_mapa["municipio"], df_mapa["estado"],
                            df_mapa["total_previsto"].astype(float),
                        )),
                        hovertemplate=(
                            "<b>%{customdata[0]}</b> — %{customdata[1]}"
                            "<br>Acidentes previstos: %{customdata[2]:,.0f}<extra></extra>"
                        ),
                        marker={
                            "size": 9, "opacity": 0.015,
                            "color": df_mapa["intensidade"],
                            "colorscale": ESCALA_INTENSIDADE,
                            "cmin": 0, "cmax": 1, "showscale": True,
                            "colorbar": {
                                "title": {"text": "Intensidade", "font": {"size": 11, "color": "#655E81"}},
                                "thickness": 11, "len": .60,
                                "tickvals": [0, .25, .5, .75, 1],
                                "ticktext": ["Muito baixa", "Baixa", "Média", "Alta", "Muito alta"],
                                "tickfont": {"size": 10, "color": "#655E81"},
                                "outlinewidth": 0,
                            },
                        },
                    ))
                else:
                    # Menos de 3 pontos não fornecem suporte para interpolação espacial.
                    fig_mapa = px.scatter_map(
                        df_mapa, lat="latitude", lon="longitude", zoom=zoom,
                        center=centro, map_style="carto-positron", hover_name="municipio",
                        hover_data={"estado": True, "total_previsto": ":.0f",
                                    "latitude": False, "longitude": False},
                    )
                    fig_mapa.update_traces(marker={"size": 19, "color": "#B5001B"})
                    st.caption("Recorte com poucos municípios: exibidos pontos, sem extrapolação IDW.")

                fig_mapa.update_layout(
                    height=465, margin={"l": 0, "r": 0, "t": 0, "b": 0},
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                )
                st.plotly_chart(
                    fig_mapa, use_container_width=True,
                    config={"displaylogo": False, "scrollZoom": False},
                )
            st.markdown(
                '<div class="support-box">A cor representa <b>intensidade relativa interpolada (IDW)</b>, calculada a partir dos valores municipais. '
                'A superfície cobre o território brasileiro no recorte, mas as cores entre os centroides são estimativas '
                'espaciais, não previsões observadas para cada ponto; não indicam probabilidade individual de acidente.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="section-overline">REDE DE ASSISTÊNCIA</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Centros de atendimento</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-desc">Pontos estratégicos de distribuição de soro antiveneno</div>', unsafe_allow_html=True)
            df_geo = df_base[["estado", "municipio", "latitude", "longitude"]].drop_duplicates(subset=["estado", "municipio"]).copy()
            df_geo["estado_key"] = df_geo["estado"].map(texto_normalizado)
            df_geo["municipio_key"] = df_geo["municipio"].map(texto_normalizado)
            df_soro_geo = df_soro_filtrado.copy()
            df_soro_geo["estado_key"] = df_soro_geo["Estado"].map(texto_normalizado)
            df_soro_geo["municipio_key"] = df_soro_geo["Município"].map(texto_normalizado)
            df_soro_mapa = pd.merge(df_soro_geo, df_geo, on=["estado_key", "municipio_key"], how="inner")
            df_soro_mapa = df_soro_mapa.dropna(subset=["latitude", "longitude"])

            if df_soro_mapa.empty:
                st.info("Nenhuma coordenada municipal disponível para os centros deste recorte.")
            else:
                zoom = 9 if municipio_selec != "Todos" else (6 if estado_selec != "Todos" else 3)
                fig_soro = px.scatter_map(
                    df_soro_mapa, lat="latitude", lon="longitude", hover_name="Unidade de Saúde",
                    hover_data={"Município": True, "Endereço": True, "Contato": True,
                                "latitude": False, "longitude": False},
                    map_style="carto-positron", zoom=zoom,
                    center={"lat": float(df_soro_mapa["latitude"].mean()),
                            "lon": float(df_soro_mapa["longitude"].mean())},
                    custom_data=["Unidade de Saúde"],
                )
                fig_soro.update_traces(marker=dict(size=13, color=CORES["roxo"], opacity=.93))
                fig_soro.update_layout(height=465, margin=dict(l=0, r=0, t=0, b=0))
                evento_mapa = st.plotly_chart(
                    fig_soro, use_container_width=True, on_select="rerun",
                    selection_mode="points", config={"displaylogo": False},
                )
                if evento_mapa and evento_mapa.selection.points:
                    ponto = evento_mapa.selection.points[0]
                    if ponto.get("customdata"):
                        st.session_state["unidade_clicada"] = ponto["customdata"][0]
            st.markdown(
                '<div class="support-box warning"><b>Atenção:</b> os pontos estão situados nas '
                'coordenadas municipais fornecidas na base de previsões, não no endereço exato '
                'da unidade. Confirme o endereço antes do deslocamento.</div>',
                unsafe_allow_html=True,
            )

with col_lateral:
    with st.container(border=True):
        st.markdown('<div class="chart-anchor"></div>', unsafe_allow_html=True)
        if tipo_mapa == "Mapa de Risco":
            st.markdown('<div class="section-overline">PADRÃO TEMPORAL</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Sazonalidade das previsões</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-desc">Distribuição mensal e tendência suavizada por média móvel de 4 meses</div>', unsafe_allow_html=True)

            df_sazonal = (
                df_filtrado.groupby("mes", observed=False)["acidentes_ajustados"]
                .sum().reindex(ORDEM_MESES, fill_value=0).reset_index()
            )
            # Na origem, os valores foram convertidos para milhares.
            # O gráfico reconstitui a quantidade estimada de acidentes.
            serie = df_sazonal["acidentes_ajustados"].to_numpy(dtype=float) * 1000
            vals = np.concatenate([serie[-2:], serie, serie[:2]])
            media_movel = pd.Series(vals).rolling(window=4, center=True).mean().to_numpy()[2:-2]
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=ORDEM_MESES, y=serie, name="Acidentes previstos",
                marker=dict(color="#A29AD4", line=dict(color="#9388C5", width=0)),
                hovertemplate="%{x}<br>%{y:,.0f} acidentes<extra></extra>",
            ))
            fig_bar.add_trace(go.Scatter(
                x=ORDEM_MESES, y=media_movel, mode="lines+markers", name="Média móvel (4 meses)",
                line=dict(color="#D56B54", width=3, shape="spline", smoothing=.5),
                marker=dict(size=5, color="#D56B54"),
                hovertemplate="%{x}<br>Média móvel: %{y:,.0f}<extra></extra>",
            ))
            fig_bar.update_layout(
                height=366, margin=dict(l=6, r=4, t=8, b=3),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans, Segoe UI, sans-serif", color=CORES["muted"], size=11),
                xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10)),
                yaxis=dict(title=None, showline=False, zeroline=False, gridcolor=CORES["grid"],
                           separatethousands=True, rangemode="tozero"),
                legend=dict(orientation="h", x=0, y=-.15, xanchor="left", font=dict(size=10)),
                bargap=.34, hovermode="x unified",
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displaylogo": False})
            if len(serie):
                mes_pico = ORDEM_MESES[int(np.nanargmax(serie))]
                pico = np.nanmax(serie)
                st.markdown(
                    f'<div class="support-box">Maior valor mensal no recorte: <b>{h(mes_pico)}</b> '
                    f'({h(formatar_numero(pico))} acidentes previstos).</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div class="section-overline">CONSULTA À REDE</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Detalhes da unidade</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-desc">Selecione uma unidade para consultar endereço, contato e CNES</div>', unsafe_allow_html=True)
            if df_soro_filtrado.empty:
                st.warning("Nenhum centro de atendimento consta na base para esta seleção.")
            else:
                lista_unidades = sorted(df_soro_filtrado["Unidade de Saúde"].dropna().unique().tolist())
                unidade_atual = st.session_state.get("unidade_clicada", "Selecione...")
                opcoes_unidades = ["Selecione..."] + lista_unidades
                if unidade_atual not in opcoes_unidades:
                    unidade_atual = "Selecione..."
                    st.session_state["unidade_clicada"] = unidade_atual
                unidade_escolhida = st.selectbox(
                    "Unidade de atendimento", opcoes_unidades,
                    index=opcoes_unidades.index(unidade_atual),
                    key=f"seletor_unidade_{unidade_atual}",
                )
                if unidade_escolhida != "Selecione...":
                    st.session_state["unidade_clicada"] = unidade_escolhida
                    info = df_soro_filtrado.loc[df_soro_filtrado["Unidade de Saúde"] == unidade_escolhida].iloc[0]
                    st.markdown(f"**Unidade:** {h(info['Unidade de Saúde'])}")
                    st.markdown(f"**Localidade:** {h(info['Município'])} – {h(info['Estado'])}")
                    st.markdown(f"**Endereço:** {h(info['Endereço'])}")
                    st.markdown(f"**Contato:** {h(info['Contato'])}")
                    st.markdown(f"**CNES:** {h(info['CNES'])}")
                    st.link_button("↗  Consultar endereço no Google Maps", info["google_maps_link"], use_container_width=True)
                else:
                    st.info("Clique em um ponto do mapa ou selecione uma unidade acima para consultar os detalhes.")

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# ============================================================
# ASSISTENTE GEMINI COM NOVAS TENTATIVAS AUTOMÁTICAS
# ============================================================
col_explicacao, col_chat = st.columns([3, 1], gap="medium", vertical_alignment="center")
with col_explicacao:
    st.markdown(
        '<div class="section-overline">PRECISA DE APOIO NA INTERPRETAÇÃO?</div>'
        '<div class="section-title">Converse com o assistente ANTARES</div>'
        '<div class="section-desc">Tire dúvidas sobre as previsões exibidas e prevenção de acidentes.</div>',
        unsafe_allow_html=True,
    )
with col_chat:
    with st.popover("✦  Abrir assistente", use_container_width=True):
        st.markdown("### 🦂 Assistente ANTARES")
        st.caption("Pergunte sobre o recorte atual ou cuidados diante de acidentes por escorpiões.")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Digite sua dúvida..."):
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
            except Exception:
                api_key = None
            if not api_key:
                st.error("A chave GEMINI_API_KEY não foi encontrada nos Secrets do Streamlit.")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.spinner("Analisando sua pergunta..."):
                    try:
                        retry_options = types.HttpRetryOptions(
                            attempts=3, initial_delay=1.0, max_delay=6.0,
                            exp_base=2.0, jitter=1.0,
                            http_status_codes=[408, 429, 500, 502, 503, 504],
                        )
                        client = genai.Client(
                            api_key=api_key,
                            http_options=types.HttpOptions(retry_options=retry_options),
                        )
                        contexto_filtros = (
                            f"Estado: {estado_selec}. Município: {municipio_selec}. "
                            f"Total estimado para o recorte: {total_previsoes:,.0f} acidentes. "
                            "Os pontos de soro no mapa usam coordenadas municipais aproximadas."
                        )
                        system_instruction = (
                            "Você é o assistente virtual do Sistema ANTARES "
                            "(Automated Neuroevolutionary Tool for Anticipating Risk of Envenomation by Scorpions). "
                            "Sua função é auxiliar gestores de saúde pública e cidadãos com análises "
                            "baseadas nos dados do painel e orientações de segurança sobre escorpionismo "
                            "(prevenção, primeiros socorros, procura de atendimento e soro antiescorpiônico). "
                            "Não invente dados nem apresente projeções como notificações confirmadas."
                        )
                        prompt_completo = (
                            f"Contexto atual do painel: {contexto_filtros}\n\nPergunta do usuário: {prompt}"
                        )
                        resposta_texto = None
                        ultimo_erro = None
                        for modelo in ["gemini-3.5-flash", "gemini-3.5-flash-lite"]:
                            try:
                                response = client.models.generate_content(
                                    model=modelo, contents=prompt_completo,
                                    config={"system_instruction": system_instruction, "temperature": 0.3},
                                )
                                resposta_texto = response.text
                                if not resposta_texto:
                                    raise ValueError("O Gemini retornou uma resposta vazia.")
                                break
                            except errors.APIError as erro:
                                if erro.code not in (408, 429, 500, 502, 503, 504):
                                    raise
                                ultimo_erro = erro
                            except ValueError as erro:
                                ultimo_erro = erro
                        if resposta_texto is None:
                            raise RuntimeError(
                                "O Gemini permanece indisponível após novas tentativas. "
                                "Tente novamente em alguns instantes."
                            ) from ultimo_erro
                        st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
                        st.rerun()
                    except Exception as erro:
                        st.error(f"Não foi possível obter resposta do Gemini: {erro}")

st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
with st.expander("Metodologia e limitações da visualização"):
    st.markdown(
        "As estimativas são exibidas por município e mês. No arquivo de entrada, os valores da variável "
        "`acidentes_previstos` são divididos por 1.000 para reproduzir o tratamento original do painel, "
        "e depois apresentados como contagens estimadas. Valores não positivos ou ausentes são substituídos "
        "pela mediana municipal; se necessário, utiliza-se a mediana geral. A camada de densidade usa "
        "normalização logarítmica relativa ao recorte. A sazonalidade mostra a soma mensal e uma média "
        "móvel circular de quatro meses. Os centros de soro são localizados por coordenadas municipais "
        "da base de previsões, e não por geocodificação dos endereços."
    )

st.markdown(
    '<div class="footer"><strong>Sistema ANTARES</strong> · Automated Neuroevolutionary Tool for '
    'Anticipating Risk of Envenomation by Scorpions<br>'
    'Dr. Welton Dionisio-da-Silva · Universidade de São Paulo (USP) · '
    'Apoio: Fundação de Amparo à Pesquisa do Estado de São Paulo (FAPESP), processo 2024/07110-0.<br>'
    'As projeções são estimativas e não substituem a vigilância epidemiológica oficial nem a avaliação profissional de saúde.'
    '</div>',
    unsafe_allow_html=True,
)
