import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sistema Antares", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("previsoes_municipios.csv")
    # Garante que a coluna mes seja tratada como categórica com ordem fixa
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)
    return df

df_base = carregar_dados()

# Filtros na Barra Lateral
st.sidebar.header("⚙️ Filtros do Painel")
estado_selec = st.sidebar.selectbox("Estado:", ["Todos"] + sorted(df_base['estado'].astype(str).unique().tolist()))

# Filtragem dinâmica de Município
opcoes_mun = ["Todos"] + sorted(df_base[df_base['estado'] == estado_selec]['municipio'].unique().tolist()) if estado_selec != "Todos" else ["Todos"]
municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)

mes_selec = st.sidebar.selectbox("Mês:", ["Ano"] + df_base['mes'].cat.categories.tolist())

# Aplicar filtros
df = df_base.copy()
if estado_selec != "Todos": df = df[df['estado'] == estado_selec]
if municipio_selec != "Todos": df = df[df['municipio'] == municipio_selec]
if mes_selec != "Ano": df = df[df['mes'] == mes_selec]

# Configurações de Mapa (Brasil centralizado se "Todos" selecionado)
col1, col2 = st.columns([1.5, 1])
with col1:
    st.subheader(f"🗺️ Mapa de Calor")
    
    # Se "Todos", usa centro do Brasil e zoom baixo. Se estado, foca nele.
    zoom = 3.5 if estado_selec == "Todos" else 6.0
    lat_center = -14.2350 if estado_selec == "Todos" else df['latitude'].mean()
    lon_center = -51.9253 if estado_selec == "Todos" else df['longitude'].mean()
    
    fig = px.density_mapbox(df, lat='latitude', lon='longitude', z='acidentes_previstos', 
                            radius=25, mapbox_style="carto-positron", 
                            zoom=zoom, center=dict(lat=lat_center, lon=lon_center))
    # Ajusta margens para garantir que o mapa não seja cortado
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal")
    st.metric("Total de Acidentes Previstos", f"{df['acidentes_previstos'].sum():,.0f}")
    
    # Gráfico de barras ordenado
    df_bar = df.groupby('mes', observed=False)['acidentes_previstos'].sum()
    st.bar_chart(df_bar)