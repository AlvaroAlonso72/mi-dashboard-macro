import streamlit as st
from fredapi import Fred
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Mi Dashboard Macro", layout="wide")

st.title("📈 Sistema de Análisis Macroeconómico")

# --- CONFIGURACIÓN DE LA API ---
# Nota: Luego veremos cómo ocultar esto por seguridad, 
# por ahora pon tu clave directamente para probar.
fred = Fred(api_key='593fcb7132e0740b127c77ff20ea57fa')

# --- BARRA LATERAL (filtros) ---
st.sidebar.header("Configuración")
opcion = st.sidebar.selectbox(
    "Selecciona el indicador",
    ("Tipos de Interés (USA)", "PIB USA", "Inflación (CPI)")
)

# Diccionario para traducir nombres a códigos de la FRED
codigos = {
    "Tipos de Interés (USA)": "FEDFUNDS",
    "PIB USA": "GDP",
    "Inflación (CPI)": "CPIAUCSL"
}

# --- OBTENCIÓN DE DATOS ---
try:
    codigo_fred = codigos[opcion]
    data = fred.get_series(codigo_fred)
    
    df = data.to_frame(name='Valor')
    df.index.name = 'Fecha'
    df.reset_index(inplace=True)

    # --- VISUALIZACIÓN ---
    st.subheader(f"Evolución de: {opcion}")
    fig = px.line(df, x='Fecha', y='Valor', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")