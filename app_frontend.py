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
    "navy": "#102B41",
    "navy_dark": "#0A1D31",
    "teal": "#11A696",
    "teal_light": "#E4F6F2",
    "text": "#182F43",
    "muted": "#687E91",
    "grid": "#E8EFF3",
    "amber": "#E5A544",
    "red": "#D85E55",
}

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --navy:#102B41; --teal:#11A696; --ink:#182F43; --muted:#687E91; }
html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
}
.stApp {
    color: var(--ink);
    background: #F4F7FA;
}
[data-testid="stAppViewContainer"] { background: #F4F7FA; }
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
    background: linear-gradient(160deg, #112F46 0%, #0B2034 100%);
    border-right: 1px solid rgba(255,255,255,.09);
}
[data-testid="stSidebar"] > div:first-child { padding-top:1.3rem; }
[data-testid="stSidebar"] * { color: #EAF1F6; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label { color:#C4D5E1 !important; font-size:.82rem; font-weight:600; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #173A52 !important;
    border: 1px solid #38546A !important;
    border-radius: 10px !important;
    min-height: 44px;
}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] input { color:#FFFFFF !important; }
[data-testid="stSidebar"] [data-baseweb="select"] svg { fill:#CDDDE9 !important; }
[data-testid="stSidebar"] div[role="radiogroup"] label { padding:.3rem 0; }
[data-testid="stSidebar"] [data-testid="stButton"] button {
    border:1px solid #557287;
    background:transparent;
    color:#EAF1F6 !important;
    border-radius:10px;
    min-height:42px;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background:#1B4056;
    border-color:#69ADAA;
}
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.16); }
.sidebar-brand { padding: 10px 0 26px; display:flex; gap:12px; align-items:center; }
.sidebar-icon {
    display:flex; align-items:center; justify-content:center;
    width:44px; height:44px; border-radius:14px;
    background:rgba(22,190,172,.18); border:1px solid rgba(55,204,186,.25);
    color:#8DF0DF; font-size:23px;
}
.sidebar-wordmark { font-family:'Manrope',sans-serif; font-weight:800; font-size:1.35rem; letter-spacing:.12em; color:white; }
.sidebar-sub { font-size:.62rem; color:#A5C4D3; letter-spacing:.16em; font-weight:700; }
.sidebar-kicker { font-size: .66rem; font-weight:800; letter-spacing:.18em; color:#82AAA9; margin:16px 0 9px; }
.sidebar-help {
    margin-top:1.6rem; padding:16px; border:1px solid #315169;
    border-radius:14px; background:rgba(255,255,255,.04);
    font-size:.78rem; line-height:1.55; color:#B9CAD8;
}
.sidebar-help b {color:#EDF8F7;}
.sidebar-footer {font-size:.67rem;color:#8DA7B7;line-height:1.7;margin-top:13px;}
.hero {
    border-radius:22px;
    background:
      radial-gradient(ellipse at 88% 14%,rgba(38,179,162,.24) 0, transparent 34%),
      radial-gradient(ellipse at 70% 100%,rgba(25,117,147,.19) 0, transparent 39%),
      linear-gradient(112deg,#102B41 0%,#0E3A4B 100%);
    box-shadow: 0 15px 38px rgba(11,37,58,.08);
    padding:30px 36px;
    margin-bottom:22px;
    overflow:hidden;
    position:relative;
}
.hero:after {
    content:""; position:absolute; right:22px; bottom:-95px;
    width:330px; height:330px; border:1px solid rgba(151,240,227,.10);
    border-radius:50%; box-shadow:0 0 0 55px rgba(151,240,227,.035),0 0 0 110px rgba(151,240,227,.02);
    pointer-events:none;
}
.hero-kicker { color:#8FDECF; letter-spacing:.20em; font-size:.68rem; font-weight:800; margin-bottom:11px; }
.hero-title {color:#FFFFFF;font-family:'Manrope',sans-serif;font-size:clamp(1.65rem,2.35vw,2.7rem);font-weight:800;line-height:1.19;letter-spacing:-.048em;margin:0 0 12px;max-width:850px;}
.hero-description {color:#C5D8E0;font-size:.91rem;line-height:1.65;margin:0;max-width:720px;}
.hero-meta {margin-top:19px;display:flex;gap:8px;flex-wrap:wrap;}
.hero-chip {display:inline-block;padding:6px 12px;border:1px solid rgba(173,220,217,.24);border-radius:999px;background:rgba(255,255,255,.06);color:#D1EAE8;font-size:.71rem;font-weight:600;}
.topline {display:flex;align-items:center;justify-content:space-between;margin:0 0 15px;gap:15px;}
.topline-left {font-size:.70rem;letter-spacing:.16em;font-weight:800;color:#738A9A;}
.topline-right {font-size:.72rem;color:#8498A7;}
.metric-card {background:#FFFFFF;border:1px solid #E4EDF2;border-radius:16px;padding:18px 19px 16px;min-height:133px;box-shadow:0 3px 10px rgba(14,52,75,.025);}
.metric-top {display:flex;justify-content:space-between;align-items:center;gap:6px;margin-bottom:13px;}
.metric-label {font-size:.74rem;font-weight:700;letter-spacing:.015em;color:#698193;}
.metric-icon {width:31px;height:31px;border-radius:9px;background:#EBF5F6;color:#148A88;display:flex;align-items:center;justify-content:center;font-size:17px;}
.metric-value {font-family:'Manrope',sans-serif;font-size:clamp(1.2rem,1.8vw,1.95rem);font-weight:800;line-height:1.18;color:#142D41;letter-spacing:-.06em;}
.metric-note {font-size:.70rem;color:#8DA0AF;margin-top:9px;}
.section-overline {font-size:.69rem;font-weight:800;letter-spacing:.15em;color:#168B86;margin-bottom:5px;}
.section-title {font-size:1.27rem;font-family:'Manrope',sans-serif;font-weight:800;color:#182F43;letter-spacing:-.035em;line-height:1.3;margin:0 0 5px;}
.section-desc {font-size:.78rem;color:#7A8E9D;margin:0 0 17px;line-height:1.5;}
.card-shell {background:#FFFFFF;border:1px solid #E4EDF2;border-radius:17px;padding:20px 19px 15px;box-shadow:0 4px 13px rgba(13,41,61,.026);}
.card-shell [data-testid="stPlotlyChart"] { border-radius: 12px;overflow:hidden; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-anchor) {
    background:#FFFFFF;
    border:1px solid #E4EDF2;
    border-radius:17px;
    box-shadow:0 4px 13px rgba(13,41,61,.026);
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-anchor) > div { padding: 18px 18px 10px; }
.chart-anchor {display:none;}
.support-box {padding:13px 15px;border-radius:11px;background:#EDF8F6;border:1px solid #D6EEE9;color:#397C79;font-size:.77rem;line-height:1.55;}
.support-box.warning {background:#FFF7EC;border-color:#FBE5C4;color:#9D722D;}
.section-gap {height:20px;}
hr {border-color:#DDE6ED !important;}
[data-testid="stPlotlyChart"] {margin-top:2px;}
[data-testid="stExpander"] {border:1px solid #DDE7ED;border-radius:14px;background:#FFFFFF;}
[data-testid="stExpander"] summary {color:#233B4D;font-weight:600;}
[data-testid="stAlert"] {border-radius:12px;}
[data-testid="stPopover"] button {
    border-radius:12px;
    background:#11A696;
    border:1px solid #11A696;
    min-height:43px;
    color:white;
    font-weight:700;
    box-shadow:0 5px 15px rgba(17,166,150,.16);
}
[data-testid="stPopover"] button:hover {background:#0A8D80;border-color:#0A8D80;color:white;}
[data-testid="stPopover"] button * {color:inherit !important;}
[data-testid="stPopoverBody"] {border-radius:16px;background:#FFFFFF;}
[data-testid="stPopoverBody"] * {color:#1B364A;}
[data-testid="stPopoverBody"] [data-testid="stChatMessage"] {border-radius:11px;}
[data-testid="stPopoverBody"] textarea,[data-testid="stPopoverBody"] input {color:#182F43 !important;}
[data-testid="stMain"] a { color:#0B8279; }
[data-testid="stMain"] a:hover {color:#095E58;}
.footer {padding:18px 2px 1px;border-top:1px solid #DDE6EC;font-size:.74rem;color:#7D91A1;line-height:1.7;}
.footer strong {color:#2B4C60;}
@media (max-width: 1000px) {
    .block-container {padding-left:1.1rem;padding-right:1.1rem;padding-top:1.2rem;}
    .hero {padding:25px 22px;border-radius:18px;}
    .hero-title {font-size:1.65rem;}
    .metric-card {min-height:121px;}
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
    if os.path.exists("logo_antares.jpg"):
        with st.expander("Ver identidade visual original"):
            st.image("logo_antares.jpg", use_container_width=True)
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
    st.markdown('<div class="sidebar-footer">ANTARES • USP<br>Pesquisa apoiada pela FAPESP</div>', unsafe_allow_html=True)


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
# VISUALIZAÇÃO PRINCIPAL
# ============================================================
col_mapa, col_lateral = st.columns([1.37, 1], gap="medium")

with col_mapa:
    with st.container(border=True):
        st.markdown('<div class="chart-anchor"></div>', unsafe_allow_html=True)
        if tipo_mapa == "Mapa de Risco":
            st.markdown('<div class="section-overline">DISTRIBUIÇÃO GEOGRÁFICA</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Mapa de intensidade prevista</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-desc">Concentração espacial relativa das projeções no recorte selecionado</div>', unsafe_allow_html=True)

            df_mapa = (
                df_filtrado.dropna(subset=["latitude", "longitude"])
                .groupby(["estado", "municipio", "latitude", "longitude"], observed=True)["acidentes_ajustados"]
                .sum().reset_index()
            )
            if df_mapa.empty:
                st.info("Não há coordenadas disponíveis para este recorte.")
            else:
                df_mapa["val_log"] = np.log1p(df_mapa["acidentes_ajustados"])
                min_v, max_v = df_mapa["val_log"].min(), df_mapa["val_log"].max()
                if max_v == min_v:
                    df_mapa["risco_z"] = 1.0
                else:
                    df_mapa["risco_z"] = 0.2 + 0.8 * ((df_mapa["val_log"] - min_v) / (max_v - min_v))
                zoom = 8 if municipio_selec != "Todos" else (6 if estado_selec != "Todos" else 3)
                fig_mapa = px.density_map(
                    df_mapa, lat="latitude", lon="longitude", z="risco_z",
                    radius=48, map_style="carto-positron", zoom=zoom,
                    center={"lat": float(df_mapa["latitude"].mean()), "lon": float(df_mapa["longitude"].mean())},
                    hover_name="municipio",
                    hover_data={"estado": True, "acidentes_ajustados": ":.2f", "risco_z": False,
                                "latitude": False, "longitude": False},
                    color_continuous_scale=[[0.0, "#F7E5A1"], [0.5, "#F1A34F"], [1.0, "#D84C51"]],
                    range_color=[0, 1], opacity=.82,
                )
                fig_mapa.update_layout(
                    height=465, margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    coloraxis_colorbar=dict(
                        title=dict(text="Intensidade", font=dict(size=11, color="#526B7B")),
                        thickness=10, len=.56, tickvals=[0, .5, 1],
                        ticktext=["Baixa", "Média", "Alta"], tickfont=dict(size=10, color="#526B7B"),
                        bgcolor="rgba(255,255,255,.9)", outlinewidth=0,
                    ),
                )
                st.plotly_chart(fig_mapa, use_container_width=True, config={"displaylogo": False, "scrollZoom": False})
            st.markdown(
                '<div class="support-box">A escala expressa <b>intensidade relativa das previsões</b> dentro '
                'do filtro selecionado; não representa probabilidade individual de acidente.</div>',
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
                fig_soro.update_traces(marker=dict(size=13, color=CORES["teal"], opacity=.93))
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
                marker=dict(color="#70BDB1", line=dict(color="#5AAEA4", width=0)),
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
