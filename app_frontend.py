import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sistema Antares - Avaliação", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")
st.markdown("Monitoramento preditivo de acidentes escorpiônicos com mapas de calor municipais e sazonalidade.")

# ==========================================
# GERAÇÃO DE DADOS DE EXEMPLO (MUNICÍPIOS REAIS)
# ==========================================
@st.cache_data
def carregar_dados_sistema():
    np.random.seed(42)
    
    # Lista representativa de municípios brasileiros em várias regiões
    municipios = [
        {"nome": "São Paulo (SP)", "lat": -23.5505, "lon": -46.6333, "base": 350},
        {"nome": "Campinas (SP)", "lat": -22.9056, "lon": -47.0608, "base": 280},
        {"nome": "Ribeirão Preto (SP)", "lat": -21.1775, "lon": -47.8103, "base": 240},
        {"nome": "Belo Horizonte (MG)", "lat": -19.9167, "lon": -43.9345, "base": 320},
        {"nome": "Uberlândia (MG)", "lat": -18.9186, "lon": -48.2772, "base": 190},
        {"nome": "Rio de Janeiro (RJ)", "lat": -22.9068, "lon": -43.1729, "base": 290},
        {"nome": "Salvador (BA)", "lat": -12.9714, "lon": -38.5014, "base": 210},
        {"nome": "Goiânia (GO)", "lat": -16.6869, "lon": -49.2648, "base": 180},
        {"nome": "Brasília (DF)", "lat": -15.7975, "lon": -47.8919, "base": 150},
        {"nome": "Porto Alegre (RS)", "lat": -30.0346, "lon": -51.2177, "base": 130},
        {"nome": "Manaus (AM)", "lat": -3.1190, "lon": -60.0217, "base": 90},
        {"nome": "Fortaleza (CE)", "lat": -3.7172, "lon": -38.5433, "base": 200}
    ]
    
    meses_lista = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    registros = []
    for mun in municipios:
        for idx, mes in enumerate(meses_lista):
            # Sazonalidade variando de acordo com o mês
            fator_sazonal = 1 + 0.5 * np.sin(2 * np.pi * idx / 12)
            predicao = int(mun['base'] * fator_sazonal * np.random.uniform(0.8, 1.2))
            
            registros.append({
                'municipio': mun['nome'],
                'latitude': mun['lat'],
                'longitude': mun['lon'],
                'mes': mes,
                'mes_num': idx + 1,
                'acidentes_previstos': max(15, predicao)
            })
            
    return pd.DataFrame(registros)

df_global = carregar_dados_sistema()

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
# Filtrar dados para o Mapa
if periodo_selecionado == "Ano (Consolidado)":
    df_mapa_atual = df_global.groupby(['municipio', 'latitude', 'longitude'])['acidentes_previstos'].sum().reset_index()
    titulo_mapa = "Mapa de Calor - Consolidado Anual"
else:
    df_mapa_atual = df_global[df_global['mes'] == periodo_selecionado].copy()
    titulo_mapa = f"Mapa de Calor - Mês de {periodo_selecionado}"

# Se um município específico foi selecionado no filtro lateral, focamos nele também no mapa
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
    
    # Criando o mapa de calor ajustado com raio maior para preencher melhor as regiões
    fig_mapa = px.density_mapbox(
        df_mapa_filtrado,
        lat='latitude',
        lon='longitude',
        z='acidentes_previstos',
        radius=65,  # Raio aumentado para espalhar bem a mancha do heatmap
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
    
    # Filtrar dados para o Gráfico de Barras de acordo com o município escolhido
    if municipio_selecionado == "Todos os Municípios (Visão Geral)":
        df_sazonalidade = df_global.groupby(['mes', 'mes_num'])['acidentes_previstos'].sum().reset_index().sort_values('mes_num')
        titulo_barras = "Demanda Prevista - Brasil (Consolidado)"
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