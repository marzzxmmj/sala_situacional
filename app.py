import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Sala Situacional SSU",
    layout="wide"
)

st.title("Sala Situacional de Salud")
st.subheader("Vigilancia epidemiológica")

# Enlace directo a la hoja BASE_CANAL de tu Google Sheet en formato CSV
SHEET_ID = "154r2-YajFh_1MxxNFbHACJX1AWAjAss7xC_fnFTtBnE"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=BASE_CANAL"


# ttl=60 hace que se actualice automáticamente desde Drive cada 60 segundos
@st.cache_data(ttl=60)
def cargar_datos(url: str) -> pd.DataFrame:
    # decimal="," lee correctamente tus números como 90,25 o 200,00
    df_local = pd.read_csv(url, decimal=",")
    df_local["Patologia"] = df_local["Patologia"].astype(str).str.strip()
    return df_local


# Botón manual por si quieres ver los cambios de Drive al instante sin esperar 60s
if st.sidebar.button("🔄 Actualizar datos ahora"):
    st.cache_data.clear()
    st.rerun()

try:
    df = cargar_datos(URL_SHEET)
except Exception as e:
    st.error(
        "No se pudo leer el Google Sheet. Verifica que esté compartido como "
        "'Cualquier persona con el enlace (Lector)'."
    )
    st.exception(e)
    st.stop()

# Filtro de patologías
patologias = sorted(
    p for p in df["Patologia"].dropna().unique() if p and p.lower() != "nan"
)

patologia = st.sidebar.selectbox("Seleccione una patología", patologias)

datos = (
    df[df["Patologia"] == patologia]
    .sort_values("Semana")
    .copy()
)

# Asegurar que las columnas numéricas sean números
cols_numericas = [
    "Casos_Actuales", "Q1", "Q2", "Q3",
    "Zona_Exito", "Zona_Seguridad", "Zona_Alarma", "Zona_Epidemia",
    "Es_Epidemia", "Es_Alerta"
]
for col in cols_numericas:
    if col in datos.columns:
        datos[col] = pd.to_numeric(datos[col], errors="coerce").fillna(0)

# Indicadores (KPIs)
col1, col2, col3 = st.columns(3)

col1.metric("Total de casos", int(datos["Casos_Actuales"].sum()))
col2.metric("Semanas epidémicas", int(datos["Es_Epidemia"].sum()))
col3.metric("Semanas de alerta", int(datos["Es_Alerta"].sum()))

# Construcción del canal endémico
fig = go.Figure()

zonas = [
    ("Zona_Exito", "Éxito", "#81C995"),
    ("Zona_Seguridad", "Seguridad", "#F5DF72"),
    ("Zona_Alarma", "Alarma", "#FFB65C"),
    ("Zona_Epidemia", "Epidemia", "#EF9A9A"),
]

for campo, nombre, color in zonas:
    fig.add_trace(go.Scatter(
        x=datos["Semana"],
        y=datos[campo],
        name=nombre,
        mode="lines",
        stackgroup="canal",
        line=dict(width=0),
        fillcolor=color
    ))

# Línea de casos observados
fig.add_trace(go.Scatter(
    x=datos["Semana"],
    y=datos["Casos_Actuales"],
    name="Casos observados",
    mode="lines+markers",
    connectgaps=False,
    line=dict(color="#163E78", width=3)
))

fig.update_layout(
    title=f"Canal endémico - {patologia}",
    xaxis_title="Semana epidemiológica",
    yaxis_title="Número de casos",
    template="plotly_white",
    hovermode="x unified",
    height=550
)

st.plotly_chart(fig, use_container_width=True)

# Tabla estadística
st.subheader("Detalle epidemiológico")

st.dataframe(
    datos[[
        "Semana",
        "Casos_Actuales",
        "Q1", "Q2", "Q3",
        "Clasificacion"
    ]],
    use_container_width=True,
    hide_index=True
)