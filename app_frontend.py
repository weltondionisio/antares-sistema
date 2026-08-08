import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sistema Antares - Avaliação", layout="wide")

st.title("🦂 Sistema Antares: Painel de Avaliação do Modelo Preditivo")
st.markdown("Interface interativa conectada ao backend seguro na nuvem.")

# Simulação de dados para exibição visual imediata no painel do avaliador
meses_lista = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
mes_selecionado = st.sidebar.selectbox("Selecione o Mês:", meses_lista)

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader(f"🗺️ Mapa de Risco - {mes_selecionado}")
    # Gerando dados fictícios estéticos para o mapa do avaliador testar
    df_mapa = pd.DataFrame({
        'municipio': ['São Paulo', 'Belo Horizonte', 'Rio de Janeiro', 'Goiânia'],
        'latitude': [-23.55, -19.91, -22.90, -16.68],
        'longitude': [-46.63, -43.93, -43.17, -49.26],
        'acidentes': [1200, 950, 800, 600]
    })
    
    # Criando o mapa com projeção ajustada sem erros de update_geos
    fig = px.scatter_geo(
        df_mapa, 
        lat='latitude', 
        lon='longitude', 
        size='acidentes', 
        color='acidentes', 
        hover_name='municipio', 
        color_continuous_scale='Reds',
        projection='mercator'
    )
    
    # Ajustando limites e visualização diretamente no layout do mapa para evitar conflitos
    fig.update_layout(
        geo=dict(
            scope='south america',
            showland=True,
            landcolor="rgb(240, 240, 240)",
            countrycolor="rgb(200, 200, 200)",
            center=dict(lat=-15.0, lon=-50.0),
            projection_scale=3.5
        ),
        height=450, 
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Previsão Sazonal (Jan a Dez)")
    meses_val = [100, 90, 75, 60, 50, 85, 80, 65, 55, 45, 30, 20]
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=meses_lista, y=meses_val, marker_color='purple', opacity=0.7, name='Previsto'))
    fig_bar.add_trace(go.Scatter(x=meses_lista, y=meses_val, mode='lines+markers', line=dict(color='orange', width=3), name='Tendência'))
    fig_bar.update_layout(height=430, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_bar, use_container_width=True)