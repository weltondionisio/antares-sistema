import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Sistema Antares", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")

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
    
    # CORREÇÃO DE ESCALA: Se o seu modelo gerou valores multiplicados por 1000, ajustamos aqui:
    # (Altere o divisor caso o fator real de expansão do seu dataset seja diferente)
    FATOR_DIVISAO = 1000.0  
    df['acidentes_previstos'] = df['acidentes_previstos'] / FATOR_DIVISAO
    
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)
    return df

df_base = carregar_dados()

# Filtros na Barra Lateral
st.sidebar.header("⚙️ Filtros do Painel")
lista_estados = ["Todos"] + sorted(df_base['estado'].unique().tolist())
estado_selec = st.sidebar.selectbox("Estado:", lista_estados)

if estado_selec != "Todos":
    opcoes_mun = ["Todos"] + sorted(df_base[df_base['estado'] == estado_selec]['municipio'].unique().tolist())
else:
    opcoes_mun = ["Todos"] + sorted(df_base['municipio'].unique().tolist())

municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)
mes_selec = st.sidebar.selectbox("Mês:", ["Ano"] + df_base['mes'].cat.categories.tolist())

# Aplicar filtros
df = df_base.copy()
if estado_selec != "Todos": 
    df = df[df['estado'] == estado_selec]
if municipio_selec != "Todos": 
    df = df[df['municipio'] == municipio_selec]
if mes_selec != "Ano": 
    df = df[df['mes'] == mes_selec]

if mes_selec == "Ano":
    df_mapa = df.groupby(['estado', 'municipio', 'latitude', 'longitude'], observed=False)['acidentes_previstos'].sum().reset_index()
else:
    df_mapa = df.copy()

df_mapa['intensidade_heatmap'] = np.log1p(df_mapa['acidentes_previstos'])

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
    
    fig = px.density_mapbox(
        df_mapa, 
        lat='latitude', 
        lon='longitude', 
        z='intensidade_heatmap', 
        radius=25, 
        mapbox_style="carto-positron", 
        zoom=zoom, 
        center=dict(lat=lat_center, lon=lon_center),
        hover_name='municipio',
        hover_data={'estado': True, 'acidentes_previstos': True, 'intensidade_heatmap': False},
        color_continuous_scale="Reds"
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal (Mediana)")
    st.metric("Mediana de Acidentes Previstos", f"{df['acidentes_previstos'].median():,.2f}")
    
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_bar = df.groupby('mes', observed=False)['acidentes_previstos'].median().reindex(ordem_meses).reset_index()
    
    fig_bar = px.bar(
        df_bar, 
        x='mes', 
        y='acidentes_previstos',
        category_orders={'mes': ordem_meses},
        labels={'mes': 'Mês do Ano', 'acidentes_previstos': 'Mediana Esperada de Acidentes'}
    )
    fig_bar.update_layout(height=450, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.markdown("🛠️ **Sistema Antares** — Inteligência Preditiva aplicada à Saúde Pública.")