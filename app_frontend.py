import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sistema Antares", layout="wide")

# ==========================================
# CUSTOMIZAÇÃO VISUAL: Cor exata #6c73b7
# ==========================================
st.markdown("""
    <style>
    /* Cor de fundo global do Streamlit */
    .stApp {
        background-color: #6c73b7;
        color: #FFFFFF;
    }
    
    /* Ajustes para caixas de texto e métricas combinarem com o fundo escuro */
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    
    /* Estilização da barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #585e9e;
    }
    </style>
""", unsafe_allow_html=True)

# Exibição da Logo no Topo
col_logo1, col_logo2, col_logo3 = st.columns([1, 3, 1])
with col_logo2:
    try:
        st.image("logo_antares.jpg", use_container_width=True)
    except:
        st.title("🦂 Sistema Antares: Painel de Avaliação")

st.markdown("<hr style='border: 1px solid #8b91c8;'>", unsafe_allow_html=True)

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
    
    FATOR_DIVISAO = 1000.0  
    df['acidentes_previstos'] = df['acidentes_previstos'] / FATOR_DIVISAO
    
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)
    return df

df_base = carregar_dados()

# Filtros na Barra Lateral (Filtro de mês removido)
st.sidebar.header("⚙️ Filtros do Painel")
lista_estados = ["Todos"] + sorted(df_base['estado'].unique().tolist())
estado_selec = st.sidebar.selectbox("Estado:", lista_estados)

if estado_selec != "Todos":
    opcoes_mun = ["Todos"] + sorted(df_base[df_base['estado'] == estado_selec]['municipio'].unique().tolist())
else:
    opcoes_mun = ["Todos"] + sorted(df_base['municipio'].unique().tolist())

municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)

# Aplicar filtros base (Estado e Município)
df = df_base.copy()
if estado_selec != "Todos": 
    df = df[df['estado'] == estado_selec]
if municipio_selec != "Todos": 
    df = df[df['municipio'] == municipio_selec]

# ==========================================
# TRATAMENTO E MÉDIA MÓVEL (Janela de 4 Meses)
# ==========================================
df_sazonal = df.groupby('mes', observed=False)['acidentes_previstos'].sum().reindex(['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']).reset_index()

referencia_minima = df_base['acidentes_previstos'].mean() * 0.05
df_sazonal['acidentes_previstos'] = df_sazonal['acidentes_previstos'].apply(lambda x: referencia_minima if pd.isna(x) or x <= 0 else x)

# Cálculo da Média Móvel com janela de 4 meses (circular para manter o ano contínuo)
valores_serie = df_sazonal['acidentes_previstos'].values
serie_ciclica = np.concatenate([valores_serie[-2:], valores_serie, valores_serie[:2]])
media_movel_ciclica = pd.Series(serie_ciclica).rolling(window=4, center=True).mean().values[2:-2]

df_sazonal['media_movel'] = media_movel_ciclica

# Para o Mapa de Calor (Visão Anual Consolidada)
df_mapa = df.groupby(['estado', 'municipio', 'latitude', 'longitude'], observed=False)['acidentes_previstos'].sum().reset_index()
df_mapa['intensidade_heatmap'] = np.log1p(df_mapa['acidentes_previstos'])

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader(f"🗺️ Mapa de Calor Contínuo (Risco Anual)")
    
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
        radius=35, 
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
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    def formatar_br(valor):
        if pd.isna(valor): return "0,00"
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    st.subheader("📊 Tendência Sazonal (Média Móvel - 4 Meses)")
    total_anual = df['acidentes_previstos'].sum()
    st.metric("Total Anual Previsto", formatar_br(total_anual))

    # Gráfico combinando as barras mensais e a linha de Média Móvel de 4 meses
    fig_bar = go.Figure()

    fig_bar.add_trace(go.Bar(
        x=df_sazonal['mes'],
        y=df_sazonal['acidentes_previstos'],
        name='Acidentes Previstos',
        marker_color='#d9534f',
        marker_line=dict(color='black', width=1.5)
    ))

    fig_bar.add_trace(go.Scatter(
        x=df_sazonal['mes'],
        y=df_sazonal['media_movel'],
        mode='lines+markers',
        name='Média Móvel (4 Meses)',
        line=dict(color='yellow', width=3)
    ))

    fig_bar.update_layout(
        xaxis_title='Mês do Ano',
        yaxis_title='Volume Esperado',
        height=450,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.markdown(
    "🛠️ **Sistema ANTARES (Automated Neuroevolutionary Tool for Anticipating Risk of Envenomation by Scorpions)** — Uma Ferramenta Neuroevolutiva Automatizada para Antecipar o Risco de Envenonamento por Escorpiões.<br>"
    "Autores: Dr. Welton Dionisio-da-Silva (USP) e Dr. Rodrigo Hirata Willemart (USP).<br>"
    "Financiamento: São Paulo Research Foundation (FAPESP), Brazil, process number #2024/07110-0.",
    unsafe_allow_html=True
)
