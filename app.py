import streamlit as st
import wbgapi as wb
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(
    page_title="Terminal Macro Global",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS para mejorar la interfaz
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

# --- FUNCIONES CON CACHÉ (86400 segundos = 24 horas) ---

@st.cache_data(ttl=86400)
def obtener_nombres_paises():
    """Descarga la lista de países del Banco Mundial"""
    try:
        economias = wb.economy.info()
        return {e['id']: e['value'] for e in economias.items}
    except:
        return {"USA": "United States", "ESP": "Spain"} # Fallback básico

@st.cache_data(ttl=86400)
def cargar_datos_banco_mundial(indicador, paises):
    """Descarga y transpone los datos"""
    if not paises:
        return pd.DataFrame()
    try:
        d = wb.data.DataFrame(indicador, paises, mrv=40).T
        d.index = d.index.str.replace('YR', '').astype(int)
        return d
    except:
        return pd.DataFrame()

# --- LÓGICA DE NAVEGACIÓN ---

nombres_paises = obtener_nombres_paises()

with st.sidebar:
    st.title("🛡️ Panel de Control")
    st.markdown("### Configuración de Datos")
    
    paises_seleccionados = st.multiselect(
        "Seleccionar Países:",
        options=list(nombres_paises.keys()),
        default=["USA", "CHN", "ESP", "BRA", "IND"],
        format_func=lambda x: nombres_paises[x]
    )
    
    st.divider()
    st.caption(f"Actualización automática cada 24h")
    st.caption(f"Sincronizado: {datetime.now().strftime('%H:%M:%S')}")

# --- CUERPO PRINCIPAL ---

st.title("📊 Terminal Macroeconómica Global")

if not paises_seleccionados:
    st.warning("👈 Selecciona países en la barra lateral para comenzar el análisis.")
else:
    # Pestañas principales
    tab_nom, tab_real, tab_info = st.tabs(["💵 Tasa Nominal", "📉 Tasa Real", "ℹ️ Ayuda"])

    # --- PESTAÑA NOMINAL ---
    with tab_nom:
        st.subheader("Tipos de Interés Nominales")
        st.info("Tasa activa bancaria (Lending Rate): El interés que los bancos cobran por préstamos.")
        
        df_nom = cargar_datos_banco_mundial('FR.INR.LEND', paises_seleccionados)
        
        if not df_nom.empty:
            # Limpieza y nombres de columnas
            df_nom.columns = [nombres_paises.get(c, c) for c in df_nom.columns]
            
            # Gráfico
            fig_nom = px.line(df_nom, template="plotly_dark")
            fig_nom.update_layout(hovermode="x unified", legend_title="Países", yaxis_title="Porcentaje %")
            st.plotly_chart(fig_nom, use_container_width=True)
            
            # Métricas con ESCUDO DE SEGURIDAD para evitar IndexError
            st.markdown("#### Últimos valores registrados")
            cols = st.columns(len(paises_seleccionados[:6])) # Máximo 6 para evitar amontonamiento
            for i, pais in enumerate(paises_seleccionados[:6]):
                nombre_p = nombres_paises.get(pais, pais)
                if nombre_p in df_nom.columns:
                    serie = df_nom[nombre_p].dropna()
                    if not serie.empty:
                        valor = serie.iloc[-1]
                        cols[i].metric(nombre_p, f"{valor:.2f}%")
                    else:
                        cols[i].metric(nombre_p, "N/D")
        else:
            st.error("No se encontraron datos nominales para los países seleccionados.")

    # --- PESTAÑA REAL ---
    with tab_real:
        st.subheader("Tipos de Interés Reales")
        st.info("Tasa ajustada por inflación: Refleja el coste real del dinero tras descontar el aumento de precios.")

        df_real = cargar_datos_banco_mundial('FR.INR.RINR', paises_seleccionados)

        if not df_real.empty:
            df_real.columns = [nombres_paises.get(c, c) for c in df_real.columns]
            
            # Gráfico
            fig_real = px.line(df_real, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_real.update_layout(hovermode="x unified", legend_title="Países", yaxis_title="Porcentaje %")
            st.plotly_chart(fig_real, use_container_width=True)
            
            # Métricas con ESCUDO DE SEGURIDAD
            st.markdown("#### Últimos valores registrados")
            cols_r = st.columns(len(paises_seleccionados[:6]))
            for i, pais in enumerate(paises_seleccionados[:6]):
                nombre_p = nombres_paises.get(pais, pais)
                if nombre_p in df_real.columns:
                    serie_r = df_real[nombre_p].dropna()
                    if not serie_r.empty:
                        valor_r = serie_r.iloc[-1]
                        cols_r[i].metric(nombre_p, f"{valor_r:.2f}%")
                    else:
                        cols_r[i].metric(nombre_p, "N/D")
        else:
            st.error("No se encontraron datos reales para los países seleccionados.")

    # --- PESTAÑA INFORMACIÓN ---
    with tab_info:
        st.markdown("""
        ### Sobre esta herramienta
        Este dashboard consume datos directamente de la API del **Banco Mundial**.
        
        * **Tasa Nominal:** Es la tasa de interés activa que cobran los bancos sobre préstamos.
        * **Tasa Real:** Es la tasa nominal ajustada por la inflación medida a través del deflactor del PIB.
        
        **Nota sobre errores:** Si un país aparece como 'N/D' o no muestra línea en el gráfico, significa que no ha reportado datos oficiales al Banco Mundial para ese periodo específico.
        """)

st.divider()
st.caption("Fuente de datos: World Bank Open Data (vía wbgapi) | Desarrollado con Python y Streamlit")
