import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Sistema Antares - Avaliação", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")
st.markdown("Monitoramento preditivo de acidentes escorpiônicos com mapas de calor municipais e sazonalidade baseados em Redes Neurais.")

@st.cache_data
def carregar_dados_reais():
    csv_path = "previsoes_municipios.csv"
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        return pd.DataFrame(columns=['estado', 'municipio', 'latitude', 'longitude', 'mes', 'acidentes_previstos'])

df_global = carregar_dados_reais()

if df_global.empty:
    st.error("⚠️ O arquivo `previsoes_municipios.csv` não foi encontrado na pasta do projeto.")
    st.stop()

# ==========================================
# BARRA LATERAL: FILTROS EM CASCATA
# ==========================================
st.sidebar.header("⚙️ Filtros do Painel")

opcoes_tempo = ["Ano (Consolidado)"] + ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
periodo_selecionado = st.sidebar.selectbox("Selecione o Período:", opcoes_tempo)

# 1. Filtro de Estado Dinâmico
lista_estados = ["Todos os Estados"] + sorted(df_global['estado'].dropna().astype(str).unique().tolist())
estado_selecionado = st.sidebar.selectbox("Filtrar por Estado:", lista_estados)

if estado_selecionado != "Todos os Estados":
    df_filtrado_estado = df_global[df_global['estado'] == estado_selecionado]
else:
    df_filtrado_estado = df_global

# 2. Filtro de Município Dinâmico baseado no estado escolhido
lista_municipios = ["Todos os Municípios"] + sorted(df_filtrado_estado['municipio'].dropna().astype(str).unique().tolist())
municipio_selecionado = st.sidebar.selectbox("Filtrar por Município:", lista_municipios)

# ==========================================
# APLICANDO OS FILTROS AOS DADOS
# ==========================================
if periodo_selecionado == "Ano (Consolidado)":
    df_mapa_base = df_global.groupby(['estado', 'municipio', 'latitude', 'longitude'])['acidentes_previstos'].sum().reset_index()
    titulo_mapa = "Mapa de Calor - Consolidado Anual"
else:
    df_mapa_base = df_global[df_global['mes'] == periodo_selecionado].copy()
    titulo_mapa = f"Mapa de Calor - Mês de {periodo_selecionado}"

if estado_selecionado != "Todos os Estados":
    df_mapa_base = df_mapa_base[df_mapa_base['estado'] == estado_selecionado]

if municipio_selecionado != "Todos os Municípios":
    df_mapa_base = df_mapa_base[df_mapa_base['municipio'] == municipio_selecionado]

# Definir zoom e centro dinâmico do mapa
if not df_mapa_base.empty:
    centro_lat = df_mapa_base['latitude'].mean()
    centro_lon = df_mapa_base['longitude'].mean()
    zoom_mapa = 7.5 if municipio_selecionado != "Todos os Municípios" else (5.2 if estado_selecionado != "Todos os Estados" else 3.2)
else:
    centro_lat, centro_lon, zoom_mapa = -14.23, -51.92, 3.2

# ==========================================
# LAYOUT PRINCIPAL (DUAS COLUNAS)
# ==========================================
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader(f"🗺️ {titulo_mapa}")
    
    fig_mapa = px.density_mapbox(
        df_mapa_base,
        lat='latitude',
        lon='longitude',
        z='acidentes_previstos',
        radius=40,
        center=dict(lat=centro_lat if not pd.isna(centro_lat) else -14.23, lon=centro_lon if not pd.isna(centro_lon) else -51.92),
        zoom=zoom_mapa,
        mapbox_style="carto-positron",
        hover_name='municipio',
        hover_data=['estado', 'acidentes_previstos'],
        color_continuous_scale="Reds"
    )
    
    fig_mapa.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_mapa, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal (Jan a Dez)")
    
    ordem_meses = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 
                   'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12}
    df_global['mes_num'] = df_global['mes'].map(ordem_meses)
    
    df_sazonal_base = df_global.copy()
    if estado_selecionado != "Todos os Estados":
        df_sazonal_base = df_sazonal_base[df_sazonal_base['estado'] == estado_selecionado]
        titulo_barras = f"Demanda - Estado: {estado_selecionado}"
    else:
        titulo_barras = "Demanda Prevista - Brasil (Consolidado)"
        
    if municipio_selecionado != "Todos os Municípios":
        df_sazonal_base = df_sazonal_base[df_sazonal_base['municipio'] == municipio_selecionado]
        titulo_barras = f"Demanda - {municipio_selecionado}"

    df_sazonalidade = df_sazonal_base.groupby(['mes', 'mes_num'])['acidentes_previstos'].sum().reset_index().sort_values('mes_num')
        
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        x=df_sazonalidade['mes'],
        y=df_sazonalidade['acidentes_previstos'],
        marker_color='purple',
        opacity=0.6,
        name='Demanda Mensal'
    ))
    
    fig_bar.add_trace(go.Scatter(
        x=df_sazonalidade['mes'],
        y=df_sazonalidade['acidentes_previstos'],
        mode='lines+markers',
        line=dict(color='orange', width=3),
        marker=dict(size=8, color='orange'),
        name='Tendência'
    ))
    
    if periodo_selecionado != "Ano (Consolidado)":
        val_mes_atual = df_sazonalidade[df_sazonalidade['mes'] == periodo_selecionado]['acidentes_previstos'].values
        if len(val_mes_atual) > 0:
            fig_bar.add_trace(go.Scatter(
                x=[periodo_selecionado],
                y=val_mes_atual,
                mode='markers',
                marker=dict(size=14, color='red', symbol='star'),
                name=f'Selecionado ({periodo_selecionado})'
            ))

    fig_bar.update_layout(
        title=titulo_barras,
        xaxis_title="Mês do Ano",
        yaxis_title="Número Esperado de Acidentes",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(x=0.01, y=0.99)
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.markdown("🛠️ **Sistema Antares** — Inteligência Preditiva Aplicada à Saúde Pública.")