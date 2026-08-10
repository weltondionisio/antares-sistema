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
    .stApp { background-color: #6c73b7; color: #FFFFFF; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #585e9e; }
    </style>
""", unsafe_allow_html=True)

# Exibição da Logo no Topo
col_logo1, col_logo2, col_logo3 = st.columns([1, 3, 1])
with col_logo2:
    try:
        st.image("logo_antares.jpg", use_container_width=True)
    except:
        st.title("Scorpion System Antares: Painel de Avaliação")

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
    df['acidentes_previstos'] = df['acidentes_previstos'] / 1000.0
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)
    return df

df_base = carregar_dados()

# Filtros na Barra Lateral
st.sidebar.header("⚙️ Filtros")
estado_selec = st.sidebar.selectbox("Estado:", ["Todos"] + sorted(df_base['estado'].unique().tolist()))
opcoes_mun = ["Todos"] + sorted(df_base[df_base['estado'] == estado_selec]['municipio'].unique().tolist()) if estado_selec != "Todos" else ["Todos"] + sorted(df_base['municipio'].unique().tolist())
municipio_selec = st.sidebar.selectbox("Município:", opcoes_mun)

# ==========================================
# TRATAMENTO COM MEDIANA MUNICIPAL
# ==========================================
medianas_por_mun = df_base.groupby(['estado', 'municipio'], observed=False)['acidentes_previstos'].transform(lambda x: x.median())
mediana_geral = df_base['acidentes_previstos'].median()
if pd.isna(mediana_geral) or mediana_geral <= 0:
    mediana_geral = 0.01

df_base['acidentes_ajustados'] = df_base['acidentes_previstos']
mask_zero = df_base['acidentes_ajustados'].isna() | (df_base['acidentes_ajustados'] <= 0)
df_base.loc[mask_zero, 'acidentes_ajustados'] = medianas_por_mun[mask_zero]
df_base['acidentes_ajustados'] = df_base['acidentes_ajustados'].fillna(mediana_geral)
df_base['acidentes_ajustados'] = df_base['acidentes_ajustados'].apply(lambda x: mediana_geral if x <= 0 else x)

# Aplicar filtros selecionados
df_filtrado = df_base.copy()
if estado_selec != "Todos": 
    df_filtrado = df_filtrado[df_filtrado['estado'] == estado_selec]
if municipio_selec != "Todos": 
    df_filtrado = df_filtrado[df_filtrado['municipio'] == municipio_selec]

# ==========================================
# PREPARAÇÃO DADOS DO MAPA (Anual por Município no Escopo Atual)
# ==========================================
df_mapa = df_filtrado.groupby(['estado', 'municipio', 'latitude', 'longitude'], observed=False)['acidentes_ajustados'].sum().reset_index()

# Suavização Logarítmica para evitar imprecisões e escala [0.2, 1.0] para que o Mapbox NUNCA deixe opacidade 0 (branco)
df_mapa['val_log'] = np.log1p(df_mapa['acidentes_ajustados'])
min_v = df_mapa['val_log'].min()
max_v = df_mapa['val_log'].max()

if max_v == min_v:
    df_mapa['risco_z'] = 1.0
else:
    # Garante intervalo entre 0.2 e 1.0 (impedindo a transparência do Mapbox no menor valor)
    df_mapa['risco_z'] = 0.2 + 0.8 * ((df_mapa['val_log'] - min_v) / (max_v - min_v))

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ Mapa de Risco")
    
    lat_center = df_mapa['latitude'].mean() if not df_mapa.empty else -14.2350
    lon_center = df_mapa['longitude'].mean() if not df_mapa.empty else -51.9253
    zoom = 6 if estado_selec != "Todos" else 3

    gradiente_amarelo_laranja_vermelho = [
        [0.0, 'yellow'],
        [0.5, 'orange'],
        [1.0, 'red']
    ]

    fig = px.density_mapbox(
        df_mapa, 
        lat='latitude', 
        lon='longitude', 
        z='risco_z',
        radius=45, 
        mapbox_style="carto-positron", 
        zoom=zoom,
        center=dict(lat=lat_center, lon=lon_center),
        hover_name='municipio',
        hover_data={'estado': True, 'acidentes_ajustados': ':.2f', 'risco_z': False, 'latitude': False, 'longitude': False},
        color_continuous_scale=gradiente_amarelo_laranja_vermelho,
        range_color=[0, 1], 
        opacity=0.75
    )
    
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_sazonal = df_filtrado.groupby('mes', observed=False)['acidentes_ajustados'].sum().reindex(ordem_meses).reset_index()
    
    # Média móvel de 4 meses circular
    vals = np.concatenate([df_sazonal['acidentes_ajustados'].values[-2:], df_sazonal['acidentes_ajustados'].values, df_sazonal['acidentes_ajustados'].values[:2]])
    df_sazonal['media_movel'] = pd.Series(vals).rolling(window=4, center=True).mean().values[2:-2]
    
    def formatar_br(v): 
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    st.subheader("📊 Tendência Sazonal (Média Móvel - 4 Meses)")
    st.metric("Total Anual Previsto", formatar_br(df_filtrado['acidentes_ajustados'].sum()))

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df_sazonal['mes'], 
        y=df_sazonal['acidentes_ajustados'], 
        name='Acidentes', 
        marker_color='#d9534f', 
        marker_line=dict(color='black', width=1.5)
    ))
    fig_bar.add_trace(go.Scatter(
        x=df_sazonal['mes'], 
        y=df_sazonal['media_movel'], 
        mode='lines+markers', 
        name='Média Móvel', 
        line=dict(color='yellow', width=3)
    ))
    
    # Eixos X e Y em branco e layout otimizado
    fig_bar.update_layout(
        height=320, 
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        font=dict(color='white'),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            title=dict(text="Mês", font=dict(color='white')),
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            title=dict(text="Número estimado de acidentes", font=dict(color='white')),
            tickfont=dict(color='white')
        )
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.markdown("🛠️ **Sistema ANTARES** — Dr. Welton Dionisio-da-Silva e Dr. Rodrigo Hirata Willemart (USP). Financiamento: FAPESP #2024/07110-0.", unsafe_allow_html=True)
