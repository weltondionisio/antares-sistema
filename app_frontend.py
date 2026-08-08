import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sistema Antares", layout="wide")
st.title("🦂 Sistema Antares: Painel de Avaliação")

@st.cache_data
def carregar_dados():
    return pd.read_csv("previsoes_municipios.csv")

df = carregar_dados()

# Filtros
st.sidebar.header("Filtros")
estado = st.sidebar.selectbox("Estado:", ["Todos"] + sorted(df['estado'].unique().tolist()))
if estado != "Todos": df = df[df['estado'] == estado]

municipio = st.sidebar.selectbox("Município:", ["Todos"] + sorted(df['municipio'].unique().tolist()))
if municipio != "Todos": df = df[df['municipio'] == municipio]

mes = st.sidebar.selectbox("Mês:", ["Ano"] + sorted(df['mes'].unique().tolist()))
if mes != "Ano": df = df[df['mes'] == mes]

# Visualização
col1, col2 = st.columns([1.5, 1])
with col1:
    fig = px.density_mapbox(df, lat='latitude', lon='longitude', z='acidentes_previstos', 
                            radius=30, mapbox_style="carto-positron", zoom=4)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric("Total Previsto", f"{df['acidentes_previstos'].sum():,.0f}")
    # Ordenar meses corretamente
    ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_bar = df.groupby('mes')['acidentes_previstos'].sum().reindex(ordem).fillna(0)
    st.bar_chart(df_bar)