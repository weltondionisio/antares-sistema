import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

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
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    def formatar_br(valor):
        if pd.isna(valor): return "0,00"
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if mes_selec == "Ano":
        st.subheader("📊 Previsão Sazonal (Total Anual)")
        total_anual = df.groupby('municipio', observed=False)['acidentes_previstos'].sum().sum() if municipio_selec == "Todos" else df['acidentes_previstos'].sum()
        st.metric("Total de Acidentes Previstos no Ano", formatar_br(total_anual))
        
        df_bar = df.groupby('mes', observed=False)['acidentes_previstos'].sum().reindex(ordem_meses).reset_index()
        y_label = 'Total Esperado de Acidentes'
    else:
        st.subheader(f"📊 Previsão Sazonal (Mediana - {mes_selec})")
        mediana_mes = df['acidentes_previstos'].median()
        st.metric(f"Mediana de Acidentes ({mes_selec})", formatar_br(mediana_mes))
        
        df_bar = df.groupby('mes', observed=False)['acidentes_previstos'].median().reindex(ordem_meses).reset_index()
        y_label = 'Mediana Esperada de Acidentes'

    fig_bar = px.bar(
        df_bar, 
        x='mes', 
        y='acidentes_previstos',
        category_orders={'mes': ordem_meses},
        labels={'mes': 'Mês do Ano', 'acidentes_previstos': y_label}
    )
    fig_bar.update_layout(height=450, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.markdown(
    "🛠️ **Sistema ANTARES** — Inteligência Preditiva aplicada à Saúde Pública.<br>"
    "Autores: Dr. Welton Dionisio-da-Silva e Dr. Rodrigo Hirata Willemart.<br>"
    "Financiamento: São Paulo Research Foundation (FAPESP), Brazil, process number #2024/07110-0.",
    unsafe_allow_html=True
)
