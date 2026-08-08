import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sistema Antares", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("previsoes_municipios.csv")
    df['estado'] = df['estado'].astype(str)
    return df

df = carregar_dados()

# Definindo a ordem cronológica correta dos meses
ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

# Filtros
st.sidebar.header("⚙️ Filtros do Painel")
estado_selec = st.sidebar.selectbox("Estado:", ["Todos"] + sorted(df['estado'].unique().tolist()))

# Filtragem de Município baseada no Estado
opcoes_mun = ["Todos"] + sorted(df[df['estado'] == estado_selec]['municipio'].unique().tolist()) if estado_selec != "Todos" else ["Todos"]
municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)

mes_selec = st.sidebar.selectbox("Mês:", ["Ano"] + ordem_meses)

# Filtragem do dataframe
df_filtrado = df.copy()
if estado_selec != "Todos": df_filtrado = df_filtrado[df_filtrado['estado'] == estado_selec]
if municipio_selec != "Todos": df_filtrado = df_filtrado[df_filtrado['municipio'] == municipio_selec]
if mes_selec != "Ano": df_filtrado = df_filtrado[df_filtrado['mes'] == mes_selec]

# Visualização
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader(f"🗺️ Mapa de Calor")
    
    # Lógica de Zoom: Brasil inteiro (zoom 3.5) ou Estado (zoom 6)
    zoom_level = 6 if estado_selec != "Todos" else 3.5
    centro_lat = df_filtrado['latitude'].mean() if estado_selec != "Todos" else -14.23
    centro_lon = df_filtrado['longitude'].mean() if estado_selec != "Todos" else -51.92
    
    fig = px.density_mapbox(df_filtrado, lat='latitude', lon='longitude', z='acidentes_previstos', 
                            radius=30, mapbox_style="carto-positron", 
                            zoom=zoom_level,
                            center=dict(lat=centro_lat, lon=centro_lon))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal")
    st.metric("Total de Acidentes Previstos", f"{df_filtrado['acidentes_previstos'].sum():,.0f}")
    
    # Gráfico ordenado corretamente de Jan a Dez
    df_bar = df_filtrado.groupby('mes')['acidentes_previstos'].sum().reindex(ordem_meses).fillna(0)
    st.bar_chart(df_bar)

st.markdown("---")
st.markdown("🛠️ **Sistema Antares** — Inteligência Preditiva aplicada à Saúde Pública.")