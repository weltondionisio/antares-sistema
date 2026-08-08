import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Sistema Antares", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("previsoes_municipios.csv")
    
    # Dicionário de conversão de códigos numéricos de estado para siglas (ajuste conforme necessário)
    # Se os códigos forem IBGE, 11 é Rondônia (RO), mas parece estar misturado no seu CSV. 
    # Converter para string garante que o filtro funcione.
    df['estado'] = df['estado'].astype(str)
    return df

df = carregar_dados()

# Filtros
st.sidebar.header("⚙️ Filtros do Painel")
estado_selec = st.sidebar.selectbox("Estado:", ["Todos"] + sorted(df['estado'].unique().tolist()))
if estado_selec != "Todos":
    df = df[df['estado'] == estado_selec]

municipio_selec = st.sidebar.selectbox("Município:", ["Todos"] + sorted(df['municipio'].unique().tolist()))
if municipio_selec != "Todos":
    df = df[df['municipio'] == municipio_selec]

mes_selec = st.sidebar.selectbox("Mês:", ["Ano"] + ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'])
if mes_selec != "Ano":
    df = df[df['mes'] == mes_selec]

# Exibição
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader(f"🗺️ Mapa de Calor")
    # Usa média das coordenadas para centralizar
    fig = px.density_mapbox(df, lat='latitude', lon='longitude', z='acidentes_previstos', 
                            radius=30, mapbox_style="carto-positron", 
                            zoom=4 if estado_selec == "Todos" else 6,
                            center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal")
    st.metric("Total de Acidentes Previstos", f"{df['acidentes_previstos'].sum():,.0f}")
    
    # Ordenação correta dos meses
    ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_bar = df.groupby('mes')['acidentes_previstos'].sum().reindex(ordem).fillna(0)
    st.bar_chart(df_bar)

st.markdown("🛠️ **Sistema Antares** — Inteligência Preditiva aplicada à Saúde Pública.")