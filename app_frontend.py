import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Sistema Antares - Avaliação", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")
st.markdown("Monitoramento preditivo de acidentes escorpiônicos com mapas de calor municipais e sazonalidade baseados em Redes Neurais.")

# ==========================================
# CARREGAR O CSV DE PREVISÕES REAIS
# ==========================================
@st.cache_data
def carregar_dados_reais():
    # Caminho do CSV gerado pelo seu script de inferência
    csv_path = "previsoes_municipios.csv"
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        # Fallback caso o CSV não seja encontrado no diretório
        return pd.DataFrame(columns=['municipio', 'latitude', 'longitude', 'mes', 'acidentes_previstos'])

df_global = carregar_dados_reais()

if df_global.empty:
    st.error("⚠️ O arquivo `previsoes_municipios.csv` não foi encontrado na pasta do projeto. Certifique-se de enviá-lo para o GitHub junto com o app.")
    st.stop()

# ==========================================
# BARRA LATERAL (CONTROLES E FILTROS)
# ==========================================
st.sidebar.header("⚙️ Filtros do Painel")

# 1. Filtro de Período (Ano ou Mês)
opcoes_tempo = ["Ano (Consolidado)"] + ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
periodo_selecionado = st.sidebar.selectbox("Selecione o Período:", opcoes_tempo)

# 2. Filtro por Município Específico
lista_municipios = ["Todos os Municípios (Visão Geral)"] + sorted(df_global['municipio'].unique().tolist())
municipio_selecionado = st.sidebar.selectbox("Filtrar por Município:", lista_municipios)

# ==========================================
# APLICANDO FILTROS AOS DADOS
# ==========================================
if periodo_selecionado == "Ano (Consolidado)":
    df_mapa_atual = df_global.groupby(['municipio', 'latitude', 'longitude'])['acidentes_previstos'].sum().reset_index()
    titulo_mapa = "Mapa de Calor - Consolidado Anual"
else:
    df_mapa_atual = df_global[df_global['mes'] == periodo_selecionado].copy()
    titulo_mapa = f"Mapa de Calor - Mês de {periodo_selecionado}"

# Filtrar por município se selecionado
if municipio_selecionado != "Todos os Municípios (Visão Geral)":
    df_mapa_filtrado = df_mapa_atual[df_mapa_atual['municipio'] == municipio_selecionado]
    zoom_mapa = 6
    if not df_mapa_filtrado.empty:
        centro_lat = df_mapa_filtrado['latitude'].values[0]
        centro_lon = df_mapa_filtrado['longitude'].values[0]
    else:
        centro_lat, centro_lon = -15.0, -50.0
else:
    df_mapa_filtrado = df_mapa_atual
    zoom_mapa = 3.2
    centro_lat, centro_lon = -14.23, -51.92

# ==========================================
# LAYOUT PRINCIPAL (DUAS COLUNAS)
# ==========================================
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader(f"🗺️ {titulo_mapa}")
    if municipio_selecionado != "Todos os Municípios (Visão Geral)":
        st.caption(f"Focado no município: **{municipio_selecionado}**")
    
    # Mapa de calor interativo cobrindo o território com base nos dados reais
    fig_mapa = px.density_mapbox(
        df_mapa_filtrado,
        lat='latitude',
        lon='longitude',
        z='acidentes_previstos',
        radius=45,
        center=dict(lat=centro_lat, lon=centro_lon),
        zoom=zoom_mapa,
        mapbox_style="carto-positron",
        hover_name='municipio',
        hover_data=['acidentes_previstos'],
        color_continuous_scale="Reds"
    )
    
    fig_mapa.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig_mapa, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal (Jan a Dez)")
    
    # Mapeamento para ordenação correta dos meses no gráfico
    ordem_meses = {'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6, 
                   'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12}
    
    df_global['mes_num'] = df_global['mes'].map(ordem_meses)
    
    if municipio_selecionado == "Todos os Municípios (Visão Geral)":
        df_sazonalidade = df_global.groupby(['mes', 'mes_num'])['acidentes_previstos'].sum().reset_index().sort_values('mes_num')
        titulo_barras = "Demanda Prevista - Geral (Consolidado)"
    else:
        df_sazonalidade = df_global[df_global['municipio'] == municipio_selecionado].sort_values('mes_num')
        titulo_barras = f"Demanda Prevista - {municipio_selecionado}"
        
    fig_bar = go.Figure()
    
    # Barras de volume previsto
    fig_bar.add_trace(go.Bar(
        x=df_sazonalidade['mes'],
        y=df_sazonalidade['acidentes_previstos'],
        marker_color='purple',
        opacity=0.6,
        name='Demanda Mensal'
    ))
    
    # Linha de tendência
    fig_bar.add_trace(go.Scatter(
        x=df_sazonalidade['mes'],
        y=df_sazonalidade['acidentes_previstos'],
        mode='lines+markers',
        line=dict(color='orange', width=3),
        marker=dict(size=8, color='orange'),
        name='Tendência'
    ))
    
    # Destaque com estrela vermelha se um mês específico estiver selecionado
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

# Rodapé institucional
st.markdown("---")
st.markdown("🛠️ **Sistema Antares** — Inteligência Preditiva Aplicada à Saúde Pública.")