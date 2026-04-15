import streamlit as st
import wbgapi as wb
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuración de la página (Debe ser lo primero)
st.set_page_config(
    page_title="Terminal Macro v1.0",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para un look más "Fintech"
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES CON CACHÉ (24 HORAS = 86400 SEGUNDOS) ---

@st.cache_data(ttl=86400)
def obtener_nombres_paises():
    """Obtiene la lista oficial de países y sus códigos ISO3"""
    economias = wb.economy.info()
    return {e['id']: e['value'] for e in economias.items}

@st.cache_data(ttl=86400)
def cargar_datos_banco_mundial(indicador, paises):
    """Descarga datos del Banco Mundial y los limpia"""
    if not paises:
        return pd.DataFrame()
    
    # mrv=40 trae los últimos 40 años con datos
    d = wb.data.DataFrame(indicador, paises, mrv=40).T
    d.index = d.index.str.replace('YR', '').astype(int)
    return d

# --- LÓGICA DE LA APLICACIÓN ---

nombres_paises = obtener_nombres_paises()

# BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Filtros Globales")
    st.info("Los datos se actualizan automáticamente cada 24h.")
    
    paises_seleccionados = st.multiselect(
        "Seleccionar Países:",
        options=list(nombres_paises.keys()),
        default=["USA", "CHN", "ESP", "BRA"],
        format_func=lambda x: nombres_paises[x]
    )
    
    st.divider()
    st.caption(f"Última sincronización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# CUERPO PRINCIPAL
st.title("📊 Sistema de Análisis de Tipos de Interés")

if not paises_seleccionados:
    st.warning("⚠️ Por favor, selecciona al menos un país en la barra lateral para visualizar los datos.")
else:
    # Creamos dos pestañas profesionales
    tab_nominal, tab_real = st.tabs(["💵 Tasa Nominal (Lending Rate)", "📉 Tasa Real (Ajustada Inflación)"])

    # --- PESTAÑA NOMINAL ---
    with tab_nominal:
        st.subheader("Evolución de la Tasa de Interés Nominal")
        st.markdown("_Tasa de interés que cobran los bancos por préstamos a clientes de primer orden._")
        
        df_nom = cargar_datos_banco_mundial('FR.INR.LEND', paises_seleccionados)
        
        if not df_nom.empty:
            # Renombrar columnas para el gráfico
            df_nom.columns = [nombres_paises[c] for c in df_nom.columns]
            
            fig_nom = px.line(
                df_nom, 
                template="plotly_dark",
                labels={'value': 'Tasa %', 'index': 'Año'},
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_nom.update_layout(hovermode="x unified", legend_title="Países")
            st.plotly_chart(fig_nom, use_container_width=True)
            
            # Métricas rápidas (Último dato disponible)
            cols = st.columns(len(paises_seleccionados[:5])) # Máximo 5 columnas para no saturar
            for i, pais in enumerate(paises_seleccionados[:5]):
                ultimo_valor = df_nom[nombres_paises[pais]].dropna().iloc[-1]
                cols[i].metric(nombres_paises[pais], f"{ultimo_valor:.2f}%", "Nominal")
        else:
            st.error("No hay datos de Tasa Nominal disponibles para la selección actual.")

    # --- PESTAÑA REAL ---
    with tab_real:
        st.subheader("Evolución de la Tasa de Interés Real")
        st.markdown("_Tasa de interés nominal ajustada por la inflación (deflactor del PIB)._")

        df_real = cargar_datos_banco_mundial('FR.INR.RINR', paises_seleccionados)

        if not df_real.empty:
            df_real.columns = [nombres_paises[c] for c in df_real.columns]
            
            fig_real = px.line(
                df_real, 
                template="plotly_dark",
                labels={'value': 'Tasa %', 'index': 'Año'},
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig_real.update_layout(hovermode="x unified", legend_title="Países")
            st.plotly_chart(fig_real, use_container_width=True)
            
            # Métricas rápidas
            cols_r = st.columns(len(paises_seleccionados[:5]))
            for i, pais in enumerate(paises_seleccionados[:5]):
                ultimo_valor_r = df_real[nombres_paises[pais]].dropna().iloc[-1]
                cols_r[i].metric(nombres_paises[pais], f"{ultimo_valor_r:.2f}%", "Real")
        else:
            st.error("No hay datos de Tasa Real disponibles para la selección actual.")

# Pie de página
st.divider()
st.caption("Fuente: Banco Mundial (World Bank Open Data). Los datos pueden presentar lagunas según la política de reporte de cada país.")
