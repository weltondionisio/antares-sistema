import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Sistema Antares", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("previsoes_municipios.csv")
    
    # Dicionário oficial de mapeamento de códigos IBGE/numéricos para Nomes de Estados por extenso
    mapa_estados = {
        '11': 'Rondônia', '12': 'Acre', '13': 'Amazonas', '14': 'Roraima', '15': 'Pará', '16': 'Amapá', '17': 'Tocantins',
        '21': 'Maranhão', '22': 'Piauí', '23': 'Ceará', '24': 'Rio Grande do Norte', '25': 'Paraíba', '26': 'Pernambuco', 
        '27': 'Alagoas', '28': 'Sergipe', '29': 'Bahia', '31': 'Minas Gerais', '32': 'Espírito Santo', '33': 'Rio de Janeiro', 
        '35': 'São Paulo', '41': 'Paraná', '42': 'Santa Catarina', '43': 'Rio Grande do Sul', '50': 'Mato Grosso do Sul', 
        '51': 'Mato Grosso', '52': 'Goiás', '53': 'Distrito Federal'
    }
    
    # Normaliza estado e município
    df['estado_raw'] = df['estado'].astype(str).str.strip()
    df['estado'] = df['estado_raw'].map(mapa_estados).fillna(df['estado_raw'])
    df['municipio'] = df['municipio'].astype(str).str.strip()
    
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)
    return df

df_base = carregar_dados()

# Filtros na Barra Lateral
st.sidebar.header("⚙️ Filtros do Painel")
lista_estados = ["Todos"] + sorted(df_base['estado'].unique().tolist())
estado_selec = st.sidebar.selectbox("Estado:", lista_estados)

# Filtragem dinâmica de Município com base no estado escolhido
if estado_selec != "Todos":
    opcoes_mun = ["Todos"] + sorted(df_base[df_base['estado'] == estado_selec]['municipio'].unique().tolist())
else:
    opcoes_mun = ["Todos"] + sorted(df_base['municipio'].unique().tolist())

municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)
mes_selec = st.sidebar.selectbox("Mês:", ["Ano"] + df_base['mes'].cat.categories.tolist())

# Aplicar filtros ao dataframe base
df = df_base.copy()
if estado_selec != "Todos": 
    df = df[df['estado'] == estado_selec]
if municipio_selec != "Todos": 
    df = df[df['municipio'] == municipio_selec]
if mes_selec != "Ano": 
    df = df[df['mes'] == mes_selec]

# Tratamento para o Mapa: Agrupamento em modo "Ano"
if mes_selec == "Ano":
    df_mapa = df.groupby(['estado', 'municipio', 'latitude', 'longitude'], observed=False)['acidentes_previstos'].sum().reset_index()
else:
    df_mapa = df.copy()

# APLICAÇÃO DE INTENSIDADE LOGARÍTMICA PARA O HEATMAP CONTÍNUO
# Isso comprime a disparidade entre grandes metrópoles e pequenas cidades, 
# garantindo que o gradiente de calor pinte todo o país de forma fluida.
df_mapa['intensidade_heatmap'] = np.log1p(df_mapa['acidentes_previstos'])

# Configurações de Mapa e Zoom Dinâmico
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader(f"🗺️ Mapa de Calor Contínuo (Risco de Acidentes)")
    
    if estado_selec == "Todos":
        zoom = 3.0
        lat_center, lon_center = -14.2350, -51.9253
    else:
        zoom = 6.0
        lat_center = df_mapa['latitude'].mean() if not df_mapa.empty else -14.2350
        lon_center = df_mapa['longitude'].mean() if not df_mapa.empty else -51.9253
    
    # Retornamos ao density_mapbox com a intensidade suavizada para manter o efeito contínuo
    fig = px.density_mapbox(
        df_mapa, 
        lat='latitude', 
        lon='longitude', 
        z='intensidade_heatmap',  # Utiliza a escala logarítmica para colorir o fundo continuamente
        radius=25, 
        mapbox_style="carto-positron", 
        zoom=zoom, 
        center=dict(lat=lat_center, lon=lon_center),
        hover_name='municipio',
        hover_data={'estado': True, 'acidentes_previstos': True, 'intensidade_heatmap': False},
        color_continuous_scale="Reds"  # Tons de vermelho contínuos
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal")
    st.metric("Total de Acidentes Previstos", f"{df['acidentes_previstos'].sum():,.0f}")
    
    # Gráfico de barras ordenado cronologicamente de Jan a Dez
    df_bar = df.groupby('mes', observed=False)['acidentes_previstos'].sum().reindex(df_base['mes'].cat.categories).fillna(0)
    st.bar_chart(df_bar)

st.markdown("---")
st.markdown("🛠️ **Sistema Antares** — Inteligência Preditiva aplicada à Saúde Pública.")