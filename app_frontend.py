import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sistema Antares", layout="wide")

# ==========================================
# CUSTOMIZAÇÃO VISUAL: Cor exata #6c73b7
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background-color: #6c73b7;
        color: #FFFFFF;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #585e9e;
    }
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
    
    FATOR_DIVISAO = 1000.0  
    df['acidentes_previstos'] = df['acidentes_previstos'] / FATOR_DIVISAO
    
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)
    return df

df_base = carregar_dados()

st.sidebar.header("⚙️ Filtros do Painel")
lista_estados = ["Todos"] + sorted(df_base['estado'].unique().tolist())
estado_selec = st.sidebar.selectbox("Estado:", lista_estados)

if estado_selec != "Todos":
    opcoes_mun = ["Todos"] + sorted(df_base[df_base['estado'] == estado_selec]['municipio'].unique().tolist())
else:
    opcoes_mun = ["Todos"] + sorted(df_base['municipio'].unique().tolist())

municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)

df = df_base.copy()
if estado_selec != "Todos": df = df[df['estado'] == estado_selec]
if municipio_selec != "Todos": df = df[df['municipio'] == municipio_selec]

# ==========================================
# MAPA DE RISCO DINÂMICO (Escala 0 a 1 e Amarelo como mínimo)
# ==========================================
df_mapa = df.groupby(['estado', 'municipio', 'latitude', 'longitude'], observed=False)['acidentes_previstos'].sum().reset_index()

mediana_global = df_base['acidentes_previstos'].median()
if pd.isna(mediana_global) or mediana_global <= 0:
    mediana_global = 0.01

df_mapa['acidentes_previstos'] = df_mapa['acidentes_previstos'].apply(lambda x: mediana_global if pd.isna(x) or x <= 0 else x)

min_v = df_mapa['acidentes_previstos'].min()
max_v = df_mapa['acidentes_previstos'].max()
if max_v == min_v:
    df_mapa['risco_0_1'] = 1.0
else:
    df_mapa['risco_0_1'] = (df_mapa['acidentes_previstos'] - min_v) / (max_v - min_v)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader(f"🗺️ Mapa de Risco")
    
    if estado_selec != "Todos" and not df.empty:
        zoom = 6.0
        lat_center = df_mapa['latitude'].mean()
        lon_center = df_mapa['longitude'].mean()
    else:
        zoom = 3.0
        lat_center, lon_center = -14.2350, -51.9253

    # Gradiente estrito iniciando em amarelo forte para o valor 0 (mínimo)
    gradiente_amarelo_laranja_vermelho = [
        [0.0, 'yellow'],
        [0.5, 'orange'],
        [1.0, 'red']
    ]

    fig = px.density_mapbox(
        df_mapa, 
        lat='latitude', lon='longitude', z='risco_0_1', 
        radius=50, mapbox_style="carto-positron", 
        zoom=zoom, center=dict(lat=lat_center, lon=lon_center),
        hover_name='municipio',
        hover_data={'estado': True, 'acidentes_previstos': True, 'risco_0_1': False},
        color_continuous_scale=gradiente_amarelo_laranja_vermelho,
        opacity=0.75
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    df_sazonal = df.groupby('mes', observed=False)['acidentes_previstos'].sum().reindex(ordem_meses).fillna(mediana_global).reset_index()
    valores = df_sazonal['acidentes_previstos'].values
    serie_ciclica = np.concatenate([valores[-2:], valores, valores[:2]])
    df_sazonal['media_movel'] = pd.Series(serie_ciclica).rolling(window=4, center=True).mean().values[2:-2]

    def formatar_br(v): return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    st.subheader("📊 Tendência Sazonal (Média Móvel - 4 Meses)")
    st.metric("Total Anual Previsto", formatar_br(df['acidentes_previstos'].sum()))

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=df_sazonal['mes'], y=df_sazonal['acidentes_previstos'], name='Acidentes', marker_color='#d9534f', marker_line=dict(color='black', width=1.5)))
    fig_bar.add_trace(go.Scatter(x=df_sazonal['mes'], y=df_sazonal['media_movel'], mode='lines+markers', name='Média Móvel', line=dict(color='yellow', width=3)))
    fig_bar.update_layout(height=450, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.markdown("🛠️ **Sistema ANTARES** — Uma Ferramenta Neuroevolutiva Automatizada para Antecipar o Risco de Envenonamento por Escorpiões.<br>Autores: Dr. Welton Dionisio-da-Silva (USP) e Dr. Rodrigo Hirata Willemart (USP).<br>Financiamento: FAPESP, process number #2024/07110-0.", unsafe_allow_html=True)
