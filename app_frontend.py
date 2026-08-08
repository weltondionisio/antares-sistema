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
    
    # Lista representativa de municípios brasileiros (com foco em áreas de maior incidência e capitais)
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
        {"nome": "Porto Alegre (RS)", "lat": -30.0346, "lon": -51.2177, "base": 130}
    ]
    
    meses_lista = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    registros = []
    for mun in municipios:
        for idx, mes in enumerate(meses_lista):
            # Simula sazonalidade (maior no verão/meses quentes)
            fator_sazonal = 1 + 0.4 * np.sin(2 * np.pi * idx / 12)
            predicao = int(mun['base'] * fator_sazonal * np.random.uniform(0.85, 1.15))
            
            registros.append({
                'municipio': mun['nome'],
                'latitude': mun['lat'],
                'longitude': mun['lon'],
                'mes': mes,
                'mes_num': idx + 1,
                'acidentes_previstos': max(10, predicao)
            })
            
    return pd.DataFrame(registros)

df_global = carregar_dados_sistema()

# ==========================================
# BARRA LATERAL (CONTROLES)
# ==========================================
st.sidebar.header("⚙️ Filtros do Painel")

# Opção de selecionar "Ano" ou um mês específico
opcoes_tempo = ["Ano (Consolidado)"] + ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
periodo_selecionado = st.sidebar.selectbox("Selecione o Período:", opcoes_tempo)

# ==========================================
# FILTRAGEM DE DADOS
# ==========================================
if periodo_selecionado == "Ano (Consolidado)":
    # Agrupa somando o ano inteiro por município
    df_mapa_atual = df_global.groupby(['municipio', 'latitude', 'longitude'])['acidentes_previstos'].sum().reset_index()
    titulo_mapa = "Mapa de Calor de Risco - Consolidado Anual"
else:
    # Filtra apenas o mês selecionado
    df_mapa_atual = df_global[df_global['mes'] == periodo_selecionado]
    titulo_mapa = f"Mapa de Calor de Risco - Mês de {periodo_selecionado}"

# ==========================================
# LAYOUT PRINCIPAL (DUAS COLUNAS)
# ==========================================
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader(f"🗺️ {titulo_mapa}")
    st.info("💡 **Dica:** O mapa exibe um gradiente de calor (*Heatmap*) baseado na densidade e volume de acidentes previstos por município.")
    
    # Criando o mapa no formato de densidade/heatmap geográfico com Plotly
    fig_mapa = px.density_mapbox(
        df_mapa_atual,
        lat='latitude',
        lon='longitude',
        z='acidentes_previstos',
        radius=40,
        center=dict(lat=-15.0, lon=-50.0),
        zoom=3.3,
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
    
    # Gráfico de barras anual fixo mostrando a evolução da demanda de janeiro a dezembro para o Brasil inteiro
    df_sazonalidade = df_global.groupby(['mes', 'mes_num'])['acidentes_previstos'].sum().reset_index().sort_values('mes_num')
    
    fig_bar = go.Figure()
    
    # Barras da quantidade esperada
    fig_bar.add_trace(go.Bar(
        x=df_sazonalidade['mes'],
        y=df_sazonalidade['acidentes_previstos'],
        marker_color='purple',
        opacity=0.6,
        name='Demanda Mensal'
    ))
    
    # Linha de tendência alaranjada por cima
    fig_bar.add_trace(go.Scatter(
        x=df_sazonalidade['mes'],
        y=df_sazonalidade['acidentes_previstos'],
        mode='lines+markers',
        line=dict(color='orange', width=3),
        marker=dict(size=8, color='orange'),
        name='Tendência'
    ))
    
    # Se um mês específico foi selecionado na barra lateral, destacamos ele no gráfico de barras
    if periodo_selecionado != "Ano (Consolidado)":
        val_mes_atual = df_sazonalidade[df_sazonalidade['mes'] == periodo_selecionado]['acidentes_previstos'].values
        fig_bar.add_trace(go.Scatter(
            x=[periodo_selecionado],
            y=val_mes_atual,
            mode='markers',
            marker=dict(size=14, color='red', symbol='star'),
            name=f'Selecionado ({periodo_selecionado})'
        ))
        st.markdown(f"📌 *Exibindo destaque para o mês de **{periodo_selecionado}**.*")
    else:
        st.markdown("📌 *Exibindo comportamento consolidado para o **Ano Inteiro**.*")

    fig_bar.update_layout(
        xaxis_title="Mês do Ano",
        yaxis_title="Número Esperado de Acidentes",
        height=450,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(x=0.01, y=0.99)
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

# Rodapé institucional do painel
st.markdown("---")
st.markdown("🛠️ **Sistema Antares** — Arquitetura de Redes Neurais e Geoprocessamento aplicado à Saúde Pública.")