import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sistema Antares", layout="wide")

# ==========================================
# CUSTOMIZAÇÃO VISUAL
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #6c73b7; color: #FFFFFF; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #585e9e; }
    </style>
""", unsafe_allow_html=True)

# Exibição da Logo no Topo
col_logo1, col_logo2, col_logo3 = st.columns([1, 3, 1])
with col_logo2:
    try:
        st.image("logo_antares.jpg", use_container_width=True)
    except:
        st.title("🦂 Sistema Antares: Painel de Avaliação")

st.markdown("<hr style='border: 1px solid #8b91c8;'>", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    df = pd.read_csv("previsoes_municipios.csv")
    mapa_estados = {
        '11': 'Rondônia', '12': 'Acre', '13': 'Amazonas', '14': 'Roraima', '15': 'Pará', '16': 'Amapá', '17': 'Tocantins',
        '21': 'Maranhão', '22': 'Piauí', '23': 'Ceará', '24': 'Rio Grande do Norte', '25': 'Paraíba', '26': 'Pernambuco', 
        '27': 'Alagoas', '28': 'Sergipe', '29': 'Bahia', '31': 'Minas Gerais', '32': 'Espírito Santo', '33': 'Rio de Janeiro', 
        '35': 'São Paulo', '41': 'Paraná', '42': 'Santa Catarina', '43': 'Rio Grande do Sul', '50': 'Mato Grosso do Sul', 
        '51': 'Mato Grosso', '52': 'Goiás', '53': 'Distrito Federal'
    }
    df['estado_raw'] = df['estado'].astype(str).str.strip()
    df['estado'] = df['estado_raw'].map(mapa_estados).fillna(df['estado_raw'])
    df['municipio'] = df['municipio'].astype(str).str.strip()
    df['acidentes_previstos'] = df['acidentes_previstos'] / 1000.0
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)
    return df

df_base = carregar_dados()
st.sidebar.header("⚙️ Filtros")
estado_selec = st.sidebar.selectbox("Estado:", ["Todos"] + sorted(df_base['estado'].unique().tolist()))
opcoes_mun = ["Todos"] + sorted(df_base[df_base['estado'] == estado_selec]['municipio'].unique().tolist()) if estado_selec != "Todos" else ["Todos"] + sorted(df_base['municipio'].unique().tolist())
municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)

df = df_base.copy()
if estado_selec != "Todos": df = df[df['estado'] == estado_selec]
if municipio_selec != "Todos": df = df[df['municipio'] == municipio_selec]

# ==========================================
# TRATAMENTO PARA MAPA (Garantir preenchimento)
# ==========================================
df_mapa = df_base.groupby(['estado', 'municipio', 'latitude', 'longitude'], observed=False)['acidentes_previstos'].sum().reset_index()
mediana_global = df_base['acidentes_previstos'].median()
df_mapa['acidentes_previstos'] = df_mapa['acidentes_previstos'].clip(lower=mediana_global)

# Escala 0 a 1 forçada
min_v, max_v = df_mapa['acidentes_previstos'].min(), df_mapa['acidentes_previstos'].max()
df_mapa['risco_0_1'] = (df_mapa['acidentes_previstos'] - min_v) / (max_v - min_v + 1e-9)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ Mapa de Risco Contínuo")
    fig = px.density_mapbox(
        df_mapa, lat='latitude', lon='longitude', z='risco_0_1',
        radius=50, mapbox_style="carto-positron", zoom=3 if estado_selec=="Todos" else 6,
        center=dict(lat=df_mapa['latitude'].mean(), lon=df_mapa['longitude'].mean()),
        color_continuous_scale=[[0, 'yellow'], [0.5, 'orange'], [1, 'red']],
        range_color=[0, 1], opacity=0.7
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_sazonal = df.groupby('mes', observed=False)['acidentes_previstos'].sum().reindex(['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']).fillna(mediana_global).reset_index()
    vals = np.concatenate([df_sazonal['acidentes_previstos'].values[-2:], df_sazonal['acidentes_previstos'].values, df_sazonal['acidentes_previstos'].values[:2]])
    df_sazonal['media_movel'] = pd.Series(vals).rolling(window=4, center=True).mean().values[2:-2]
    
    st.subheader("📊 Tendência (Média Móvel - 4 Meses)")
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=df_sazonal['mes'], y=df_sazonal['acidentes_previstos'], marker_color='#d9534f', marker_line=dict(color='black', width=1.5)))
    fig_bar.add_trace(go.Scatter(x=df_sazonal['mes'], y=df_sazonal['media_movel'], mode='lines+markers', line=dict(color='yellow', width=3)))
    fig_bar.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.markdown("🛠️ **Sistema ANTARES** — Autores: Dr. Welton Dionisio-da-Silva e Dr. Rodrigo Hirata Willemart (USP). Financiamento: FAPESP #2024/07110-0.", unsafe_allow_html=True)
