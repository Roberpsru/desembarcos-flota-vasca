"""
================================================================================
APLICACIÓN STREAMLIT - DESEMBARCOS FLOTA VASCA
================================================================================
Proyecto: Desembarco_Estudio_2026
Descripción: Dashboard interactivo para análisis de desembarcos pesqueros
             de la flota vasca (2018-2025)

Ejecución:
    streamlit run app/app.py

Autor: HAZI
Fecha: Febrero 2026
================================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import sys

# Añadir el directorio src al path para importar módulos
# Funciona tanto en local (app/app.py) como en cloud (app.py en raíz)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Importar módulo de análisis de flota
try:
    from fleet_analysis import (  # type: ignore
        analisis_presencia_flota,
        generar_cuadro_presencia,
        analisis_continuidad,
        analisis_entradas_salidas,
        detalle_buque
    )
except ImportError:
    st.error("❌ No se encontró el módulo fleet_analysis.py en src/")
    st.stop()

# =============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Euskal Flotaren Lehorreratzeak / Desembarcos Flota Vasca",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# ESTILOS CSS PERSONALIZADOS
# =============================================================================
st.markdown("""
<style>
    /* Cambiar color de los tags de multiselect a azul suave */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #4A90A4 !important;
        color: white !important;
        font-size: 0.75rem !important;
    }
    
    /* Reducir tamaño de fuente en sidebar */
    .stSidebar .stMultiSelect label {
        font-size: 0.85rem !important;
    }
    
    .stSidebar .stCheckbox label {
        font-size: 0.85rem !important;
    }
    
    .stSidebar .stSelectbox label {
        font-size: 0.85rem !important;
    }
    
    /* Estilo para textos en euskera (azul) */
    .texto-eu {
        color: #2E86AB;
        font-weight: 600;
    }
    
    /* Estilo para textos en castellano (negro) */
    .texto-es {
        color: #333333;
        font-weight: 600;
        font-size: 0.95em;
    }
    
    /* Reducir padding en sidebar */
    .stSidebar .block-container {
        padding-top: 1rem;
    }
    
    /* Estilo para títulos bilingües */
    .titulo-bilingue {
        margin-bottom: 0.5rem;
    }
    
    /* ============================================= */
    /* ESTILOS PARA MÉTRICAS PERSONALIZADAS */
    /* ============================================= */
    
    /* Contenedor de métrica personalizada */
    .metrica-custom {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 1.2rem;
        border-left: 4px solid #2E86AB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 0.5rem;
    }
    
    .metrica-custom:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    
    /* Label de la métrica - EUSKERA */
    .metrica-label-eu {
        font-size: 0.95rem;
        color: #2E86AB;
        font-weight: 700;
        margin: 0;
        padding: 0;
        line-height: 1.1;
    }
    
    /* Label de la métrica - CASTELLANO */
    .metrica-label-es {
        font-size: 0.9rem;
        color: #333333;
        font-weight: 600;
        margin: 0;
        padding: 0;
        line-height: 1.1;
        margin-bottom: 8px;
    }
    
    /* Valor de la métrica */
    .metrica-valor {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a3a52;
        margin: 0;
        line-height: 1;
    }
    
    /* Delta/variación */
    .metrica-delta {
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
    
    .metrica-delta.positivo {
        color: #28a745;
    }
    
    .metrica-delta.negativo {
        color: #dc3545;
    }
    
    /* Tarjetas KPI destacadas */
    .kpi-destacado {
        background: linear-gradient(135deg, #2E86AB 0%, #1a5276 100%);
        border-radius: 10px;
        padding: 1.2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    .kpi-destacado .metrica-label-eu,
    .kpi-destacado .metrica-label-es {
        color: rgba(255,255,255,0.9);
    }
    
    .kpi-destacado .metrica-valor {
        color: white;
        font-size: 2.4rem;
    }
    
    /* Sección con fondo */
    .seccion-fondo {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FUNCIÓN PARA TEXTOS BILINGÜES
# =============================================================================
def texto_bilingue(texto_eu, texto_es, como_html=True):
    """
    Genera texto bilingüe: euskera en azul arriba, castellano en negro abajo.
    
    Args:
        texto_eu: Texto en euskera
        texto_es: Texto en castellano
        como_html: Si True, devuelve HTML para usar con st.markdown
    """
    if como_html:
        return f'<span class="texto-eu">{texto_eu}</span><br><span class="texto-es">{texto_es}</span>'
    else:
        return f"{texto_eu}\n{texto_es}"


def titulo_seccion(texto_eu, texto_es, nivel="h3"):
    """Muestra un título de sección bilingüe."""
    st.markdown(f"""
    <{nivel} class="titulo-bilingue">
        <span class="texto-eu">{texto_eu}</span><br>
        <span class="texto-es">{texto_es}</span>
    </{nivel}>
    """, unsafe_allow_html=True)


def metrica_personalizada(label_eu, label_es, valor, delta=None, delta_positivo=True, destacado=False):
    """
    Muestra una métrica con estilo personalizado.
    
    Args:
        label_eu: Etiqueta en euskera
        label_es: Etiqueta en castellano
        valor: Valor a mostrar
        delta: Variación opcional (ej: "+15%")
        delta_positivo: Si True, delta verde; si False, delta rojo
        destacado: Si True, usa estilo de tarjeta destacada
    """
    clase_contenedor = "kpi-destacado" if destacado else "metrica-custom"
    
    delta_html = ""
    if delta:
        clase_delta = "positivo" if delta_positivo else "negativo"
        delta_html = f'<div class="metrica-delta {clase_delta}">{delta}</div>'
    
    st.markdown(f"""
    <div class="{clase_contenedor}">
        <div class="metrica-label-eu">{label_eu}</div>
        <div class="metrica-label-es">{label_es}</div>
        <div class="metrica-valor">{valor}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# TEXTOS BILINGÜES (EU / ES)
# =============================================================================
TEXTOS = {
    'titulo_app_eu': "🐟 Euskal Flotaren Lehorreratzeak",
    'titulo_app_es': "Desembarcos Flota Vasca",
    'subtitulo_eu': "Arrantza-desenbarkuen analisia (2018-2025)",
    'subtitulo_es': "Análisis de desembarcos pesqueros (2018-2025)",
    
    # Pestañas
    'tab_dashboard': "📊 Dashboard",
    'tab_flota': "🚢 Flota",
    'tab_dimensional': "📈 Analisia / Análisis",
    'tab_verdel': "🐟 Berdela / Verdel",
    'tab_compradores': "🏪 Erosleak / Compradores",
    'tab_info': "ℹ️ Informazioa / Información",
    
    # Filtros
    'filtros_titulo_eu': "🎛️ Iragazkiak",
    'filtros_titulo_es': "Filtros",
    'filtro_año_eu': "Urtea",
    'filtro_año_es': "Año",
    'filtro_territorio_eu': "Lurraldea",
    'filtro_territorio_es': "Territorio",
    'filtro_puerto_eu': "Portua",
    'filtro_puerto_es': "Puerto",
    'filtro_segmento_eu': "Segmentua",
    'filtro_segmento_es': "Segmento",
    'filtro_especie_eu': "Espeziea",
    'filtro_especie_es': "Especie",
    'filtro_establecimiento_eu': "Establezimendua",
    'filtro_establecimiento_es': "Establecimiento",
}

# =============================================================================
# PALETA DE COLORES
# =============================================================================
COLORES = {
    'primario': '#2E86AB',
    'secundario': '#F18F01',
    'exito': '#2CA02C',
    'alerta': '#C73E1D',
    'info': '#17BECF',
    'gris': '#7F7F7F',
    'azul_claro': '#4A90A4',
    
    # Segmentos
    'Cerco': '#2E86AB',
    'Otras artes': '#F18F01',
    'Arrastre': '#2CA02C',
    'Arrastre de litoral': '#C73E1D',
    
    # Territorios
    'Bizkaia': '#2E86AB',
    'Gipuzkoa': '#F18F01',
}

# =============================================================================
# FUNCIONES DE CARGA DE DATOS
# =============================================================================

@st.cache_data
def cargar_datos():
    """Carga el dataset de desembarcos desde el fichero Parquet."""
    
    rutas_posibles = [
        'data/processed/desembarcos_vascos.parquet',
        '../data/processed/desembarcos_vascos.parquet',
        os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'desembarcos_vascos.parquet')
    ]
    
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            df = pd.read_parquet(ruta)
            # Convertir Año_int a int normal (no nullable) para evitar problemas de memoria
            if 'Año_int' in df.columns:
                df['Año_int'] = df['Año_int'].fillna(0).astype(int)
            return df
    
    st.error("❌ Ez da datu-fitxategia aurkitu / No se encontró el fichero de datos")
    st.stop()


@st.cache_data
def cargar_estadisticas():
    """Carga las estadísticas precalculadas."""
    
    rutas_posibles = [
        'data/processed/estadisticas_datos.json',
        '../data/processed/estadisticas_datos.json',
        os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'estadisticas_datos.json')
    ]
    
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    return {}


# =============================================================================
# FUNCIONES DE FILTRADO
# =============================================================================

def aplicar_filtros(df, años, territorios, puertos, segmentos, especies, establecimientos, buques):
    """Aplica los filtros seleccionados al DataFrame."""
    
    # Crear máscara booleana en lugar de copiar el dataframe
    mask = pd.Series([True] * len(df), index=df.index)
    
    if años and len(años) > 0:
        mask &= df['Año_int'].isin(años)
    
    if territorios and len(territorios) > 0:
        mask &= df['Censo_PueBasTH2'].isin(territorios)
    
    if puertos and len(puertos) > 0:
        mask &= df['Puerto base'].isin(puertos)
    
    if segmentos and len(segmentos) > 0:
        mask &= df['Censo_Segmento'].isin(segmentos)
    
    if especies and len(especies) > 0:
        mask &= df['Especie - Nombre comercial'].isin(especies)
    
    if establecimientos and len(establecimientos) > 0:
        mask &= df['Establecimiento venta - Nombre'].isin(establecimientos)
    
    if buques and len(buques) > 0:
        mask &= df['Nombre buque'].isin(buques)
    
    return df[mask]


def obtener_opciones(df, columna, filtro_previo=None):
    """Obtiene las opciones únicas de una columna."""
    if filtro_previo is not None:
        df = filtro_previo
    return sorted(df[columna].dropna().unique().tolist())


# =============================================================================
# CARGAR DATOS
# =============================================================================

df = cargar_datos()
stats = cargar_estadisticas()

# Obtener opciones para filtros
años_disponibles = obtener_opciones(df, 'Año_int')
territorios_disponibles = obtener_opciones(df, 'Censo_PueBasTH2')
segmentos_disponibles = obtener_opciones(df, 'Censo_Segmento')

# =============================================================================
# SIDEBAR - FILTROS
# =============================================================================

with st.sidebar:
    st.markdown(f"""
    <h2 style="margin-bottom: 0.5rem;">
        <span class="texto-eu">{TEXTOS['filtros_titulo_eu']}</span><br>
        <span class="texto-es" style="font-size: 0.9em;">{TEXTOS['filtros_titulo_es']}</span>
    </h2>
    """, unsafe_allow_html=True)
    
    # Filtro de Año
    st.markdown(f'<p style="margin-bottom: 0.2rem;"><span class="texto-eu">{TEXTOS["filtro_año_eu"]}</span> / <span class="texto-es">{TEXTOS["filtro_año_es"]}</span></p>', unsafe_allow_html=True)
    años_seleccionados = st.multiselect(
        "Año",
        options=años_disponibles,
        default=años_disponibles,
        key='filtro_años',
        label_visibility="collapsed"
    )
    
    # Filtro de Territorio
    st.markdown(f'<p style="margin-bottom: 0.2rem;"><span class="texto-eu">{TEXTOS["filtro_territorio_eu"]}</span> / <span class="texto-es">{TEXTOS["filtro_territorio_es"]}</span></p>', unsafe_allow_html=True)
    territorios_seleccionados = st.multiselect(
        "Territorio",
        options=territorios_disponibles,
        default=territorios_disponibles,
        key='filtro_territorios',
        label_visibility="collapsed"
    )
    
    # Puertos (filtrados por territorio)
    df_temp = df[df['Censo_PueBasTH2'].isin(territorios_seleccionados)] if territorios_seleccionados else df
    puertos_disponibles = obtener_opciones(df_temp, 'Puerto base')
    
    st.markdown(f'<p style="margin-bottom: 0.2rem;"><span class="texto-eu">{TEXTOS["filtro_puerto_eu"]}</span> / <span class="texto-es">{TEXTOS["filtro_puerto_es"]}</span></p>', unsafe_allow_html=True)
    puertos_seleccionados = st.multiselect(
        "Puerto",
        options=puertos_disponibles,
        default=puertos_disponibles,
        key='filtro_puertos',
        label_visibility="collapsed"
    )
    
    # Filtro de Segmento
    st.markdown(f'<p style="margin-bottom: 0.2rem;"><span class="texto-eu">{TEXTOS["filtro_segmento_eu"]}</span> / <span class="texto-es">{TEXTOS["filtro_segmento_es"]}</span></p>', unsafe_allow_html=True)
    segmentos_seleccionados = st.multiselect(
        "Segmento",
        options=segmentos_disponibles,
        default=segmentos_disponibles,
        key='filtro_segmentos',
        label_visibility="collapsed"
    )
    
    # Filtro de Especie (con búsqueda)
    especies_disponibles = obtener_opciones(df, 'Especie - Nombre comercial')
    
    usar_filtro_especie = st.checkbox(
        f"Espezieen arabera iragazi / Filtrar por especie ({len(especies_disponibles)})",
        value=False
    )
    
    if usar_filtro_especie:
        especies_seleccionadas = st.multiselect(
            "Especie",
            options=especies_disponibles,
            default=[],
            key='filtro_especies',
            label_visibility="collapsed"
        )
    else:
        especies_seleccionadas = []
    
    # Filtro de Establecimiento
    establecimientos_disponibles = obtener_opciones(df, 'Establecimiento venta - Nombre')
    
    usar_filtro_establecimiento = st.checkbox(
        f"Establezimenduaren arabera / Filtrar por establecimiento ({len(establecimientos_disponibles)})",
        value=False
    )
    
    if usar_filtro_establecimiento:
        establecimientos_seleccionados = st.multiselect(
            "Establecimiento",
            options=establecimientos_disponibles,
            default=[],
            key='filtro_establecimientos',
            label_visibility="collapsed"
        )
    else:
        establecimientos_seleccionados = []
    
    # Filtro de Buque
    buques_disponibles = obtener_opciones(df, 'Nombre buque')
    
    usar_filtro_buque = st.checkbox(
        f"Ontziaren arabera iragazi / Filtrar por buque ({len(buques_disponibles)})",
        value=False
    )
    
    if usar_filtro_buque:
        buques_seleccionados = st.multiselect(
            "Buque",
            options=buques_disponibles,
            default=[],
            key='filtro_buques',
            label_visibility="collapsed"
        )
    else:
        buques_seleccionados = []
    
    st.markdown("---")
    
    st.caption(f"📊 Kargatutako datuak / Datos cargados: {len(df):,}")

# =============================================================================
# APLICAR FILTROS
# =============================================================================

df_filtrado = aplicar_filtros(
    df,
    años_seleccionados,
    territorios_seleccionados,
    puertos_seleccionados,
    segmentos_seleccionados,
    especies_seleccionadas if usar_filtro_especie else None,
    establecimientos_seleccionados if usar_filtro_establecimiento else None,
    buques_seleccionados if usar_filtro_buque else None
)

with st.sidebar:
    st.caption(f"🔍 Iragazitako erregistroak / Registros filtrados: {len(df_filtrado):,}")

# =============================================================================
# TÍTULO PRINCIPAL - BANNER
# =============================================================================

st.markdown("""
<div style="
    background: linear-gradient(135deg, #2E86AB 0%, #1a5276 100%);
    padding: 1.5rem 2rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
">
    <h1 style="
        color: white;
        margin: 0;
        font-size: 2.2rem;
        display: flex;
        align-items: center;
        gap: 10px;
    ">
        🐟 Euskal Flotaren Lehorreratzeak | Desembarcos Flota Vasca
    </h1>
    <p style="
        color: rgba(255, 255, 255, 0.85);
        margin: 0.5rem 0 0 0;
        font-style: italic;
        font-size: 1.1rem;
    ">
        Arrantza-desenbarkuen analisia (2018-2025) | Análisis de desembarcos pesqueros (2018-2025)
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# PESTAÑAS
# =============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    TEXTOS['tab_dashboard'],
    TEXTOS['tab_flota'],
    TEXTOS['tab_dimensional'],
    TEXTOS['tab_verdel'],
    TEXTOS['tab_compradores'],
    TEXTOS['tab_info']
])

# =============================================================================
# TAB 1: DASHBOARD GENERAL
# =============================================================================

with tab1:
    titulo_seccion("Dashboard Orokorra", "Dashboard General", "h2")
    
    if len(df_filtrado) == 0:
        st.warning("⚠️ Ez dago daturik hautatutako iragazkiekin / No hay datos con los filtros seleccionados")
    else:
        # --- KPIs principales ---
        col1, col2, col3, col4, col5 = st.columns(5)
        
        peso_total = df_filtrado['Peso (Kg)'].sum()
        fact_total = df_filtrado['Total precio (€)'].sum()
        precio_medio = fact_total / peso_total if peso_total > 0 else 0
        n_buques = df_filtrado['Nombre buque'].nunique()
        n_especies = df_filtrado['Especie - Nombre comercial'].nunique()
        
        with col1:
            metrica_personalizada(
                "Pisu totala", "Peso total",
                f"{peso_total/1e6:.1f} M Kg"
            )
        
        with col2:
            metrica_personalizada(
                "Fakturazioa", "Facturación",
                f"{fact_total/1e6:.1f} M €"
            )
        
        with col3:
            metrica_personalizada(
                "Batez besteko prezioa", "Precio medio",
                f"{precio_medio:.2f} €/Kg"
            )
        
        with col4:
            metrica_personalizada(
                "Ontziak", "Buques",
                f"{n_buques}"
            )
        
        with col5:
            metrica_personalizada(
                "Espezieak", "Especies",
                f"{n_especies}"
            )
        
        st.markdown("---")
        
        # --- Evolución temporal ---
        titulo_seccion("Urteko eboluzioa", "Evolución anual", "h3")
        
        evolucion = df_filtrado.groupby('Año_int').agg({
            'Peso (Kg)': 'sum',
            'Total precio (€)': 'sum',
            'Nombre buque': 'nunique'
        }).reset_index()
        evolucion.columns = ['Año', 'Peso (Kg)', 'Facturación (€)', 'Buques']
        evolucion['Precio medio (€/Kg)'] = evolucion['Facturación (€)'] / evolucion['Peso (Kg)']
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(
                x=evolucion['Año'],
                y=evolucion['Peso (Kg)'] / 1e6,
                name='Pisua / Peso (M Kg)',
                line=dict(color=COLORES['primario'], width=3),
                mode='lines+markers'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=evolucion['Año'],
                y=evolucion['Facturación (€)'] / 1e6,
                name='Fakturazioa / Facturación (M €)',
                line=dict(color=COLORES['secundario'], width=3),
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title='Pisu eta fakturazioaren eboluzioa / Evolución de peso y facturación',
            xaxis_title='Urtea / Año',
            hovermode='x unified',
            height=400
        )
        fig.update_yaxes(title_text="Pisua / Peso (M Kg)", secondary_y=False)
        fig.update_yaxes(title_text="Fakturazioa / Facturación (M €)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- Dos columnas ---
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            titulo_seccion("Espezierik nagusiak", "Top especies", "h3")
            
            top_especies = df_filtrado.groupby('Especie - Nombre comercial').agg({
                'Peso (Kg)': 'sum',
                'Total precio (€)': 'sum'
            }).sort_values('Peso (Kg)', ascending=False).head(10).reset_index()
            
            fig_especies = px.bar(
                top_especies,
                x='Peso (Kg)',
                y='Especie - Nombre comercial',
                orientation='h',
                title='Pisuaren arabera 10 espezierik nagusiak / Top 10 especies por peso',
                color_discrete_sequence=[COLORES['primario']]
            )
            fig_especies.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=400,
                showlegend=False
            )
            fig_especies.update_xaxes(title_text="Pisua / Peso (Kg)")
            fig_especies.update_yaxes(title_text="")
            
            st.plotly_chart(fig_especies, use_container_width=True)
        
        with col_der:
            titulo_seccion("Segmentuen arabera", "Por segmento", "h3")
            
            por_segmento = df_filtrado.groupby('Censo_Segmento').agg({
                'Peso (Kg)': 'sum',
                'Total precio (€)': 'sum',
                'Nombre buque': 'nunique'
            }).reset_index()
            por_segmento.columns = ['Segmento', 'Peso (Kg)', 'Facturación (€)', 'Buques']
            
            fig_segmento = px.pie(
                por_segmento,
                values='Peso (Kg)',
                names='Segmento',
                title='Segmentuen araberako banaketa / Distribución por segmento',
                hole=0.4,
                color='Segmento',
                color_discrete_map=COLORES
            )
            fig_segmento.update_layout(height=400)
            
            st.plotly_chart(fig_segmento, use_container_width=True)

# =============================================================================
# TAB 2: ANÁLISIS DE FLOTA
# =============================================================================

with tab2:
    titulo_seccion("Flotaren presentzia", "Presencia de la flota", "h2")
    
    if len(df_filtrado) == 0:
        st.warning("⚠️ Ez dago daturik hautatutako iragazkiekin")
    else:
        resultado_presencia = analisis_presencia_flota(df_filtrado)
        resultado_continuidad = analisis_continuidad(resultado_presencia)
        
        # --- KPIs de flota ---
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            metrica_personalizada(
                "Ontzi guztiak", "Total buques",
                resultado_continuidad['total_buques']
            )
        
        with col2:
            buques_todos_años = len(resultado_continuidad['buques_todos_años'])
            metrica_personalizada(
                f"{resultado_continuidad['n_años']} urtez aktiboak", 
                f"Activos {resultado_continuidad['n_años']} años",
                buques_todos_años
            )
        
        with col3:
            pct_continuidad = buques_todos_años / resultado_continuidad['total_buques'] * 100 if resultado_continuidad['total_buques'] > 0 else 0
            metrica_personalizada(
                "Jarraitutasun %", "% Continuidad",
                f"{pct_continuidad:.1f}%"
            )
        
        with col4:
            años_rango = f"{resultado_presencia['años'][0]} - {resultado_presencia['años'][-1]}"
            metrica_personalizada(
                "Aldia", "Periodo",
                años_rango
            )
        
        st.markdown("---")
        
        # --- Resumen por año ---
        titulo_seccion("Urteko laburpena", "Resumen por año", "h3")
        
        df_resumen = resultado_presencia['resumen_por_año'].copy()
        df_resumen['Peso (Kg)'] = df_resumen['Peso (Kg)'].apply(lambda x: f"{x/1e6:.2f} M")
        df_resumen['Facturación (€)'] = df_resumen['Facturación (€)'].apply(lambda x: f"{x/1e6:.2f} M")
        
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # --- Cuadro de presencia ---
        titulo_seccion("Ontzi eta urte bakoitzeko presentzia-taula", "Cuadro de presencia por buque y año", "h3")
        
        df_cuadro = generar_cuadro_presencia(resultado_presencia)
        
        def colorear_presencia(val):
            if val == 'Sí':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'No':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        columnas_años = [str(a) for a in resultado_presencia['años']]
        
        st.dataframe(
            df_cuadro.style.applymap(colorear_presencia, subset=columnas_años),
            use_container_width=True,
            height=500
        )
        
        st.markdown("---")
        
        # --- Cuadro de Peso/Facturación por buque y año ---
        titulo_seccion("Ontzi eta urte bakoitzeko pisua/fakturazioa", "Peso/Facturación por buque y año", "h3")
        
        # Selector para elegir qué mostrar
        opcion_valor = st.radio(
            "Hautatu bistaratzeko / Seleccionar para visualizar:",
            ["Pisua / Peso (Kg)", "Fakturazioa / Facturación (€)"],
            horizontal=True,
            key="selector_peso_fact"
        )
        
        # Determinar qué columna usar
        if "Pisua" in opcion_valor or "Peso" in opcion_valor:
            columna_valor = 'Peso (Kg)'
            formato_valor = lambda x: f"{x/1e3:,.1f} t" if pd.notna(x) and x > 0 else "—"
            titulo_tabla = "Pisua (t) / Peso (t)"
        else:
            columna_valor = 'Total precio (€)'
            formato_valor = lambda x: f"{x/1e3:,.1f} k€" if pd.notna(x) and x > 0 else "—"
            titulo_tabla = "Fakturazioa (k€) / Facturación (k€)"
        
        # Crear tabla pivotada
        df_pivot = df_filtrado.groupby(['Nombre buque', 'Año_int'])[columna_valor].sum().reset_index()
        df_pivot = df_pivot.pivot(index='Nombre buque', columns='Año_int', values=columna_valor)
        
        # Añadir info del buque (segmento y puerto)
        buques_info_df = df_filtrado.groupby('Nombre buque').agg({
            'Censo_Segmento': 'first',
            'Puerto base': 'first'
        }).reset_index()
        
        df_pivot = df_pivot.reset_index()
        df_pivot = df_pivot.merge(buques_info_df, on='Nombre buque', how='left')
        
        # Reordenar columnas: Buque, Segmento, Puerto, años...
        años_cols = [col for col in df_pivot.columns if isinstance(col, (int, np.integer))]
        otras_cols = ['Nombre buque', 'Censo_Segmento', 'Puerto base']
        df_pivot = df_pivot[otras_cols + sorted(años_cols)]
        
        # Renombrar columnas
        df_pivot.columns = ['Buque', 'Segmento', 'Puerto'] + [str(a) for a in sorted(años_cols)]
        
        # Calcular total por buque
        años_str = [str(a) for a in sorted(años_cols)]
        df_pivot['Total'] = df_pivot[años_str].sum(axis=1)
        
        # Ordenar por total descendente
        df_pivot = df_pivot.sort_values('Total', ascending=False)
        df_pivot = df_pivot.reset_index(drop=True)
        df_pivot.index = df_pivot.index + 1
        
        # Formatear valores
        for col in años_str + ['Total']:
            df_pivot[col] = df_pivot[col].apply(formato_valor)
        
        st.caption(f"📊 {titulo_tabla}")
        st.dataframe(
            df_pivot,
            use_container_width=True,
            height=500
        )
        
        st.markdown("---")
        
        # --- Continuidad y Entradas/Salidas ---
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            titulo_seccion("Jarraitutasuna", "Continuidad", "h3")
            
            df_cont = resultado_continuidad['resumen_continuidad'].copy()
            
            fig_cont = px.bar(
                df_cont,
                x='Años activo',
                y='Buques',
                title='Jarduera-urteen araberako ontziak / Buques por años de actividad',
                color_discrete_sequence=[COLORES['primario']]
            )
            fig_cont.update_layout(height=350)
            
            st.plotly_chart(fig_cont, use_container_width=True)
        
        with col_der:
            titulo_seccion("Sarrerak eta irteerak", "Entradas y salidas", "h3")
            
            df_entradas = analisis_entradas_salidas(resultado_presencia)
            
            fig_ent = go.Figure()
            fig_ent.add_trace(go.Bar(
                x=df_entradas['Año'],
                y=df_entradas['Nuevos'],
                name='Berriak / Nuevos',
                marker_color=COLORES['exito']
            ))
            fig_ent.add_trace(go.Bar(
                x=df_entradas['Año'],
                y=df_entradas['Bajas'],
                name='Bajak / Bajas',
                marker_color=COLORES['alerta']
            ))
            
            fig_ent.update_layout(
                title='Urteko sarrerak eta irteerak / Entradas y salidas por año',
                barmode='group',
                height=350
            )
            
            st.plotly_chart(fig_ent, use_container_width=True)
        
        st.markdown("---")
        
        # --- Detalle por buque ---
        titulo_seccion("Ontziaren xehetasuna", "Detalle por buque", "h3")
        
        buques_lista = sorted(resultado_presencia['buques_todos'])
        buque_seleccionado = st.selectbox(
            "Ontzia hautatu / Seleccionar buque",
            options=buques_lista
        )
        
        if buque_seleccionado:
            detalle = detalle_buque(df_filtrado, buque_seleccionado)
            
            if detalle:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    metrica_personalizada("Segmentua", "Segmento", detalle['segmento'])
                with col2:
                    metrica_personalizada("Portua", "Puerto", detalle['puerto'])
                with col3:
                    metrica_personalizada("Pisu totala", "Peso total", f"{detalle['peso_total']/1e3:.1f} t")
                with col4:
                    metrica_personalizada("Fakturazioa", "Facturación", f"{detalle['facturacion_total']/1e3:.1f} k€")
                
                st.markdown("**Ontziaren espezierik nagusiak / Top especies del buque:**")
                st.dataframe(detalle['top_especies'], use_container_width=True, hide_index=True)

# =============================================================================
# TAB 3: ANÁLISIS DIMENSIONAL
# =============================================================================

with tab3:
    titulo_seccion("Analisi dimentsionala", "Análisis Dimensional", "h2")
    
    if len(df_filtrado) == 0:
        st.warning("⚠️ Ez dago daturik hautatutako iragazkiekin")
    else:
        subtab1, subtab2, subtab3, subtab4 = st.tabs([
            "Segmentuka / Por Segmento",
            "Lurraldeka / Por Territorio",
            "Portuka / Por Puerto",
            "Espezieka / Por Especie"
        ])
        
        with subtab1:
            titulo_seccion("Segmentuen arabera", "Por Segmento", "h3")
            
            por_segmento = df_filtrado.groupby('Censo_Segmento').agg({
                'Peso (Kg)': 'sum',
                'Total precio (€)': 'sum',
                'Nombre buque': 'nunique',
                'Especie - Nombre comercial': 'nunique'
            }).reset_index()
            por_segmento.columns = ['Segmento', 'Peso (Kg)', 'Facturación (€)', 'Buques', 'Especies']
            por_segmento['Precio medio (€/Kg)'] = por_segmento['Facturación (€)'] / por_segmento['Peso (Kg)']
            por_segmento = por_segmento.sort_values('Peso (Kg)', ascending=False)
            
            st.dataframe(
                por_segmento.style.format({
                    'Peso (Kg)': '{:,.0f}',
                    'Facturación (€)': '{:,.0f}',
                    'Precio medio (€/Kg)': '{:.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            fig = px.bar(
                por_segmento,
                x='Segmento',
                y=['Peso (Kg)', 'Facturación (€)'],
                barmode='group',
                title='Pisua eta fakturazioa segmentuka / Peso y facturación por segmento'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # --- Tabla de Peso por Segmento y Año ---
            titulo_seccion("Pisua segmentu eta urteka", "Peso por segmento y año", "h4")
            
            peso_seg_año = df_filtrado.groupby(['Censo_Segmento', 'Año_int'])['Peso (Kg)'].sum().reset_index()
            peso_seg_año_pivot = peso_seg_año.pivot(index='Censo_Segmento', columns='Año_int', values='Peso (Kg)')
            peso_seg_año_pivot = peso_seg_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_peso = [col for col in peso_seg_año_pivot.columns if isinstance(col, (int, np.integer))]
            peso_seg_año_pivot = peso_seg_año_pivot[['Censo_Segmento'] + sorted(años_cols_peso)]
            peso_seg_año_pivot.columns = ['Segmento'] + [str(a) for a in sorted(años_cols_peso)]
            
            # Calcular total
            años_str_peso = [str(a) for a in sorted(años_cols_peso)]
            peso_seg_año_pivot['Total'] = peso_seg_año_pivot[años_str_peso].sum(axis=1)
            
            # Formatear valores
            formato_peso = lambda x: f"{x/1e6:.2f} M" if pd.notna(x) and x > 0 else "—"
            for col in años_str_peso + ['Total']:
                peso_seg_año_pivot[col] = peso_seg_año_pivot[col].apply(formato_peso)
            
            st.dataframe(peso_seg_año_pivot, use_container_width=True, hide_index=True)
            
            # --- Gráfico de líneas de Peso por Segmento y Año ---
            fig_peso_lineas = px.line(
                peso_seg_año,
                x='Año_int',
                y='Peso (Kg)',
                color='Censo_Segmento',
                markers=True,
                title='Pisuaren eboluzioa segmentuka / Evolución del peso por segmento',
                labels={'Año_int': 'Urtea / Año', 'Peso (Kg)': 'Pisua / Peso (Kg)', 'Censo_Segmento': 'Segmentua / Segmento'},
                color_discrete_map=COLORES
            )
            fig_peso_lineas.update_layout(height=400)
            st.plotly_chart(fig_peso_lineas, use_container_width=True)
            
            st.markdown("---")
            
            # --- Tabla de Facturación por Segmento y Año ---
            titulo_seccion("Fakturazioa segmentu eta urteka", "Facturación por segmento y año", "h4")
            
            fact_seg_año = df_filtrado.groupby(['Censo_Segmento', 'Año_int'])['Total precio (€)'].sum().reset_index()
            fact_seg_año_pivot = fact_seg_año.pivot(index='Censo_Segmento', columns='Año_int', values='Total precio (€)')
            fact_seg_año_pivot = fact_seg_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_fact = [col for col in fact_seg_año_pivot.columns if isinstance(col, (int, np.integer))]
            fact_seg_año_pivot = fact_seg_año_pivot[['Censo_Segmento'] + sorted(años_cols_fact)]
            fact_seg_año_pivot.columns = ['Segmento'] + [str(a) for a in sorted(años_cols_fact)]
            
            # Calcular total
            años_str_fact = [str(a) for a in sorted(años_cols_fact)]
            fact_seg_año_pivot['Total'] = fact_seg_año_pivot[años_str_fact].sum(axis=1)
            
            # Formatear valores
            formato_fact = lambda x: f"{x/1e6:.2f} M" if pd.notna(x) and x > 0 else "—"
            for col in años_str_fact + ['Total']:
                fact_seg_año_pivot[col] = fact_seg_año_pivot[col].apply(formato_fact)
            
            st.dataframe(fact_seg_año_pivot, use_container_width=True, hide_index=True)
            
            # --- Gráfico de líneas de Facturación por Segmento y Año ---
            fig_fact_lineas = px.line(
                fact_seg_año,
                x='Año_int',
                y='Total precio (€)',
                color='Censo_Segmento',
                markers=True,
                title='Fakturazioaren eboluzioa segmentuka / Evolución de la facturación por segmento',
                labels={'Año_int': 'Urtea / Año', 'Total precio (€)': 'Fakturazioa / Facturación (€)', 'Censo_Segmento': 'Segmentua / Segmento'},
                color_discrete_map=COLORES
            )
            fig_fact_lineas.update_layout(height=400)
            st.plotly_chart(fig_fact_lineas, use_container_width=True)
        
        with subtab2:
            titulo_seccion("Lurraldeen arabera", "Por Territorio", "h3")
            
            por_territorio = df_filtrado.groupby('Censo_PueBasTH2').agg({
                'Peso (Kg)': 'sum',
                'Total precio (€)': 'sum',
                'Nombre buque': 'nunique',
                'Puerto base': 'nunique'
            }).reset_index()
            por_territorio.columns = ['Territorio', 'Peso (Kg)', 'Facturación (€)', 'Buques', 'Puertos']
            por_territorio['Precio medio (€/Kg)'] = por_territorio['Facturación (€)'] / por_territorio['Peso (Kg)']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    por_territorio.style.format({
                        'Peso (Kg)': '{:,.0f}',
                        'Facturación (€)': '{:,.0f}',
                        'Precio medio (€/Kg)': '{:.2f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                fig = px.pie(
                    por_territorio,
                    values='Peso (Kg)',
                    names='Territorio',
                    title='Lurraldeen araberako banaketa / Distribución por territorio',
                    color='Territorio',
                    color_discrete_map=COLORES
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # --- Tabla de Peso por Territorio y Año ---
            titulo_seccion("Pisua lurralde eta urteka", "Peso por territorio y año", "h4")
            
            peso_terr_año = df_filtrado.groupby(['Censo_PueBasTH2', 'Año_int'])['Peso (Kg)'].sum().reset_index()
            peso_terr_año_pivot = peso_terr_año.pivot(index='Censo_PueBasTH2', columns='Año_int', values='Peso (Kg)')
            peso_terr_año_pivot = peso_terr_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_peso_t = [col for col in peso_terr_año_pivot.columns if isinstance(col, (int, np.integer))]
            peso_terr_año_pivot = peso_terr_año_pivot[['Censo_PueBasTH2'] + sorted(años_cols_peso_t)]
            peso_terr_año_pivot.columns = ['Territorio'] + [str(a) for a in sorted(años_cols_peso_t)]
            
            # Calcular total
            años_str_peso_t = [str(a) for a in sorted(años_cols_peso_t)]
            peso_terr_año_pivot['Total'] = peso_terr_año_pivot[años_str_peso_t].sum(axis=1)
            
            # Formatear valores
            formato_peso_t = lambda x: f"{x/1e6:.2f} M" if pd.notna(x) and x > 0 else "—"
            for col in años_str_peso_t + ['Total']:
                peso_terr_año_pivot[col] = peso_terr_año_pivot[col].apply(formato_peso_t)
            
            st.dataframe(peso_terr_año_pivot, use_container_width=True, hide_index=True)
            
            # --- Gráfico de líneas de Peso por Territorio y Año ---
            fig_peso_terr = px.line(
                peso_terr_año,
                x='Año_int',
                y='Peso (Kg)',
                color='Censo_PueBasTH2',
                markers=True,
                title='Pisuaren eboluzioa lurraldeka / Evolución del peso por territorio',
                labels={'Año_int': 'Urtea / Año', 'Peso (Kg)': 'Pisua / Peso (Kg)', 'Censo_PueBasTH2': 'Lurraldea / Territorio'},
                color_discrete_map=COLORES
            )
            fig_peso_terr.update_layout(height=400)
            st.plotly_chart(fig_peso_terr, use_container_width=True)
            
            st.markdown("---")
            
            # --- Tabla de Facturación por Territorio y Año ---
            titulo_seccion("Fakturazioa lurralde eta urteka", "Facturación por territorio y año", "h4")
            
            fact_terr_año = df_filtrado.groupby(['Censo_PueBasTH2', 'Año_int'])['Total precio (€)'].sum().reset_index()
            fact_terr_año_pivot = fact_terr_año.pivot(index='Censo_PueBasTH2', columns='Año_int', values='Total precio (€)')
            fact_terr_año_pivot = fact_terr_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_fact_t = [col for col in fact_terr_año_pivot.columns if isinstance(col, (int, np.integer))]
            fact_terr_año_pivot = fact_terr_año_pivot[['Censo_PueBasTH2'] + sorted(años_cols_fact_t)]
            fact_terr_año_pivot.columns = ['Territorio'] + [str(a) for a in sorted(años_cols_fact_t)]
            
            # Calcular total
            años_str_fact_t = [str(a) for a in sorted(años_cols_fact_t)]
            fact_terr_año_pivot['Total'] = fact_terr_año_pivot[años_str_fact_t].sum(axis=1)
            
            # Formatear valores
            formato_fact_t = lambda x: f"{x/1e6:.2f} M" if pd.notna(x) and x > 0 else "—"
            for col in años_str_fact_t + ['Total']:
                fact_terr_año_pivot[col] = fact_terr_año_pivot[col].apply(formato_fact_t)
            
            st.dataframe(fact_terr_año_pivot, use_container_width=True, hide_index=True)
            
            # --- Gráfico de líneas de Facturación por Territorio y Año ---
            fig_fact_terr = px.line(
                fact_terr_año,
                x='Año_int',
                y='Total precio (€)',
                color='Censo_PueBasTH2',
                markers=True,
                title='Fakturazioaren eboluzioa lurraldeka / Evolución de la facturación por territorio',
                labels={'Año_int': 'Urtea / Año', 'Total precio (€)': 'Fakturazioa / Facturación (€)', 'Censo_PueBasTH2': 'Lurraldea / Territorio'},
                color_discrete_map=COLORES
            )
            fig_fact_terr.update_layout(height=400)
            st.plotly_chart(fig_fact_terr, use_container_width=True)
        
        with subtab3:
            titulo_seccion("Portuen arabera", "Por Puerto", "h3")
            
            por_puerto = df_filtrado.groupby('Puerto base').agg({
                'Peso (Kg)': 'sum',
                'Total precio (€)': 'sum',
                'Nombre buque': 'nunique'
            }).reset_index()
            por_puerto.columns = ['Puerto', 'Peso (Kg)', 'Facturación (€)', 'Buques']
            por_puerto['Precio medio (€/Kg)'] = por_puerto['Facturación (€)'] / por_puerto['Peso (Kg)']
            por_puerto = por_puerto.sort_values('Peso (Kg)', ascending=False)
            
            fig = px.bar(
                por_puerto,
                x='Peso (Kg)',
                y='Puerto',
                orientation='h',
                title='Portu bakoitzeko pisua / Peso por puerto',
                color_discrete_sequence=[COLORES['primario']]
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # --- Tabla de Peso por Puerto y Año ---
            titulo_seccion("Pisua portu eta urteka", "Peso por puerto y año", "h4")
            
            peso_puerto_año = df_filtrado.groupby(['Puerto base', 'Año_int'])['Peso (Kg)'].sum().reset_index()
            peso_puerto_año_pivot = peso_puerto_año.pivot(index='Puerto base', columns='Año_int', values='Peso (Kg)')
            peso_puerto_año_pivot = peso_puerto_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_peso_p = [col for col in peso_puerto_año_pivot.columns if isinstance(col, (int, np.integer))]
            peso_puerto_año_pivot = peso_puerto_año_pivot[['Puerto base'] + sorted(años_cols_peso_p)]
            peso_puerto_año_pivot.columns = ['Puerto'] + [str(a) for a in sorted(años_cols_peso_p)]
            
            # Calcular total
            años_str_peso_p = [str(a) for a in sorted(años_cols_peso_p)]
            peso_puerto_año_pivot['Total'] = peso_puerto_año_pivot[años_str_peso_p].sum(axis=1)
            
            # Ordenar por total descendente
            peso_puerto_año_pivot = peso_puerto_año_pivot.sort_values('Total', ascending=False)
            
            # Formatear valores
            formato_peso_p = lambda x: f"{x/1e6:.2f} M" if pd.notna(x) and x > 0 else "—"
            for col in años_str_peso_p + ['Total']:
                peso_puerto_año_pivot[col] = peso_puerto_año_pivot[col].apply(formato_peso_p)
            
            st.dataframe(peso_puerto_año_pivot, use_container_width=True, hide_index=True)
            
            # --- Gráfico de líneas de Peso por Puerto y Año ---
            fig_peso_puerto = px.line(
                peso_puerto_año,
                x='Año_int',
                y='Peso (Kg)',
                color='Puerto base',
                markers=True,
                title='Pisuaren eboluzioa portuka / Evolución del peso por puerto',
                labels={'Año_int': 'Urtea / Año', 'Peso (Kg)': 'Pisua / Peso (Kg)', 'Puerto base': 'Portua / Puerto'}
            )
            fig_peso_puerto.update_layout(height=450)
            st.plotly_chart(fig_peso_puerto, use_container_width=True)
            
            st.markdown("---")
            
            # --- Tabla de Facturación por Puerto y Año ---
            titulo_seccion("Fakturazioa portu eta urteka", "Facturación por puerto y año", "h4")
            
            fact_puerto_año = df_filtrado.groupby(['Puerto base', 'Año_int'])['Total precio (€)'].sum().reset_index()
            fact_puerto_año_pivot = fact_puerto_año.pivot(index='Puerto base', columns='Año_int', values='Total precio (€)')
            fact_puerto_año_pivot = fact_puerto_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_fact_p = [col for col in fact_puerto_año_pivot.columns if isinstance(col, (int, np.integer))]
            fact_puerto_año_pivot = fact_puerto_año_pivot[['Puerto base'] + sorted(años_cols_fact_p)]
            fact_puerto_año_pivot.columns = ['Puerto'] + [str(a) for a in sorted(años_cols_fact_p)]
            
            # Calcular total
            años_str_fact_p = [str(a) for a in sorted(años_cols_fact_p)]
            fact_puerto_año_pivot['Total'] = fact_puerto_año_pivot[años_str_fact_p].sum(axis=1)
            
            # Ordenar por total descendente
            fact_puerto_año_pivot = fact_puerto_año_pivot.sort_values('Total', ascending=False)
            
            # Formatear valores
            formato_fact_p = lambda x: f"{x/1e6:.2f} M" if pd.notna(x) and x > 0 else "—"
            for col in años_str_fact_p + ['Total']:
                fact_puerto_año_pivot[col] = fact_puerto_año_pivot[col].apply(formato_fact_p)
            
            st.dataframe(fact_puerto_año_pivot, use_container_width=True, hide_index=True)
            
            # --- Gráfico de líneas de Facturación por Puerto y Año ---
            fig_fact_puerto = px.line(
                fact_puerto_año,
                x='Año_int',
                y='Total precio (€)',
                color='Puerto base',
                markers=True,
                title='Fakturazioaren eboluzioa portuka / Evolución de la facturación por puerto',
                labels={'Año_int': 'Urtea / Año', 'Total precio (€)': 'Fakturazioa / Facturación (€)', 'Puerto base': 'Portua / Puerto'}
            )
            fig_fact_puerto.update_layout(height=450)
            st.plotly_chart(fig_fact_puerto, use_container_width=True)
        
        with subtab4:
            titulo_seccion("20 espezierik nagusiak", "Top 20 especies", "h3")
            
            por_especie = df_filtrado.groupby('Especie - Nombre comercial').agg({
                'Peso (Kg)': 'sum',
                'Total precio (€)': 'sum'
            }).reset_index()
            por_especie.columns = ['Especie', 'Peso (Kg)', 'Facturación (€)']
            por_especie['Precio medio (€/Kg)'] = por_especie['Facturación (€)'] / por_especie['Peso (Kg)']
            por_especie = por_especie.sort_values('Peso (Kg)', ascending=False).head(20)
            
            fig = px.bar(
                por_especie,
                x='Peso (Kg)',
                y='Especie',
                orientation='h',
                title='Pisuaren arabera 20 espezierik nagusiak / Top 20 especies por peso',
                color_discrete_sequence=[COLORES['primario']]
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # --- Tabla de Peso por Especie y Año ---
            titulo_seccion("Pisua especie eta urteka", "Peso por especie y año", "h4")
            
            peso_esp_año = df_filtrado.groupby(['Especie - Nombre comercial', 'Año_int'])['Peso (Kg)'].sum().reset_index()
            peso_esp_año_pivot = peso_esp_año.pivot(index='Especie - Nombre comercial', columns='Año_int', values='Peso (Kg)')
            peso_esp_año_pivot = peso_esp_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_peso_e = [col for col in peso_esp_año_pivot.columns if isinstance(col, (int, np.integer))]
            peso_esp_año_pivot = peso_esp_año_pivot[['Especie - Nombre comercial'] + sorted(años_cols_peso_e)]
            peso_esp_año_pivot.columns = ['Especie'] + [str(a) for a in sorted(años_cols_peso_e)]
            
            # Calcular total
            años_str_peso_e = [str(a) for a in sorted(años_cols_peso_e)]
            peso_esp_año_pivot['Total'] = peso_esp_año_pivot[años_str_peso_e].sum(axis=1)
            
            # Ordenar por total descendente
            peso_esp_año_pivot = peso_esp_año_pivot.sort_values('Total', ascending=False)
            
            # Formatear valores
            formato_peso_e = lambda x: f"{x/1e3:,.1f} t" if pd.notna(x) and x > 0 else "—"
            for col in años_str_peso_e + ['Total']:
                peso_esp_año_pivot[col] = peso_esp_año_pivot[col].apply(formato_peso_e)
            
            st.dataframe(peso_esp_año_pivot, use_container_width=True, hide_index=True, height=500)
            
            st.markdown("---")
            
            # --- Tabla de Facturación por Especie y Año ---
            titulo_seccion("Fakturazioa especie eta urteka", "Facturación por especie y año", "h4")
            
            fact_esp_año = df_filtrado.groupby(['Especie - Nombre comercial', 'Año_int'])['Total precio (€)'].sum().reset_index()
            fact_esp_año_pivot = fact_esp_año.pivot(index='Especie - Nombre comercial', columns='Año_int', values='Total precio (€)')
            fact_esp_año_pivot = fact_esp_año_pivot.reset_index()
            
            # Reordenar columnas
            años_cols_fact_e = [col for col in fact_esp_año_pivot.columns if isinstance(col, (int, np.integer))]
            fact_esp_año_pivot = fact_esp_año_pivot[['Especie - Nombre comercial'] + sorted(años_cols_fact_e)]
            fact_esp_año_pivot.columns = ['Especie'] + [str(a) for a in sorted(años_cols_fact_e)]
            
            # Calcular total
            años_str_fact_e = [str(a) for a in sorted(años_cols_fact_e)]
            fact_esp_año_pivot['Total'] = fact_esp_año_pivot[años_str_fact_e].sum(axis=1)
            
            # Ordenar por total descendente
            fact_esp_año_pivot = fact_esp_año_pivot.sort_values('Total', ascending=False)
            
            # Formatear valores
            formato_fact_e = lambda x: f"{x/1e3:,.1f} k€" if pd.notna(x) and x > 0 else "—"
            for col in años_str_fact_e + ['Total']:
                fact_esp_año_pivot[col] = fact_esp_año_pivot[col].apply(formato_fact_e)
            
            st.dataframe(fact_esp_año_pivot, use_container_width=True, hide_index=True, height=500)

# =============================================================================
# TAB 4: ANÁLISIS DE VERDEL
# =============================================================================

with tab4:
    titulo_seccion("Berdel merkatua", "Mercado de verdel", "h2")
    
    df_verdel = df[
        (df['Especie - Nombre comercial'] == 'CABALLA') &
        (df['Año_int'].isin(años_seleccionados) if años_seleccionados else True) &
        (df['Censo_PueBasTH2'].isin(territorios_seleccionados) if territorios_seleccionados else True) &
        (df['Puerto base'].isin(puertos_seleccionados) if puertos_seleccionados else True) &
        (df['Censo_Segmento'].isin(segmentos_seleccionados) if segmentos_seleccionados else True)
    ].copy()
    
    if len(df_verdel) == 0:
        st.warning("⚠️ Ez dago berdel/kaballarik hautatutako iragazkiekin / No hay datos de verdel/caballa")
    else:
        # --- KPIs ---
        col1, col2, col3, col4, col5 = st.columns(5)
        
        peso_verdel = df_verdel['Peso (Kg)'].sum()
        fact_verdel = df_verdel['Total precio (€)'].sum()
        precio_verdel = fact_verdel / peso_verdel if peso_verdel > 0 else 0
        n_buques_verdel = df_verdel['Nombre buque'].nunique()
        
        peso_total_filtrado = df_filtrado['Peso (Kg)'].sum()
        pct_peso = peso_verdel / peso_total_filtrado * 100 if peso_total_filtrado > 0 else 0
        
        with col1:
            metrica_personalizada("Berdelaren pisua", "Peso verdel", f"{peso_verdel/1e6:.1f} M Kg")
        with col2:
            metrica_personalizada("Fakturazioa", "Facturación", f"{fact_verdel/1e6:.1f} M €")
        with col3:
            metrica_personalizada("Batez besteko prezioa", "Precio medio", f"{precio_verdel:.2f} €/Kg")
        with col4:
            metrica_personalizada("Ontziak", "Buques", n_buques_verdel)
        with col5:
            metrica_personalizada("Totalaren %", "% del total", f"{pct_peso:.1f}%")
        
        st.markdown("---")
        
        # --- La Paradoja del Verdel ---
        titulo_seccion("Berdelaren Paradoxa", "La Paradoja del Verdel", "h3")
        
        evol_verdel = df_verdel.groupby('Año_int').agg({
            'Peso (Kg)': 'sum',
            'Total precio (€)': 'sum',
            'Nombre buque': 'nunique'
        }).reset_index()
        evol_verdel.columns = ['Año', 'Peso (Kg)', 'Facturación (€)', 'Buques']
        evol_verdel['Precio (€/Kg)'] = evol_verdel['Facturación (€)'] / evol_verdel['Peso (Kg)']
        
        if len(evol_verdel) >= 2:
            primer_año = evol_verdel.iloc[0]
            ultimo_año = evol_verdel.iloc[-1]
            
            var_peso = (ultimo_año['Peso (Kg)'] - primer_año['Peso (Kg)']) / primer_año['Peso (Kg)'] * 100
            var_fact = (ultimo_año['Facturación (€)'] - primer_año['Facturación (€)']) / primer_año['Facturación (€)'] * 100
            var_precio = (ultimo_año['Precio (€/Kg)'] - primer_año['Precio (€/Kg)']) / primer_año['Precio (€/Kg)'] * 100
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                metrica_personalizada(
                    f"Pisuaren aldaketa ({int(primer_año['Año'])}-{int(ultimo_año['Año'])})",
                    "Variación peso",
                    f"{var_peso:+.1f}%",
                    delta=f"{var_peso:+.1f}%",
                    delta_positivo=(var_peso > 0)
                )
            
            with col2:
                metrica_personalizada(
                    "Fakturazioaren aldaketa",
                    "Variación facturación",
                    f"{var_fact:+.1f}%",
                    delta=f"{var_fact:+.1f}%",
                    delta_positivo=(var_fact > 0)
                )
            
            with col3:
                metrica_personalizada(
                    "Prezioaren aldaketa",
                    "Variación precio",
                    f"{var_precio:+.1f}%",
                    delta=f"{var_precio:+.1f}%",
                    delta_positivo=(var_precio > 0)
                )
            
            st.info("""
            **Berdelaren Paradoxa / Paradoja del Verdel**: Harrapaketen jaitsiera izan arren, fakturazioa igo egin da prezioaren gorakada indartsuari esker. Honek eskasia egoera bat iradokitzen du eskari jasangarriarekin.
            
            *A pesar de la caída en las capturas, la facturación ha aumentado gracias a la fuerte revalorización del precio. Esto sugiere una situación de escasez con demanda sostenida.*
            """)
        
        st.markdown("---")
        
        # --- Evolución ---
        titulo_seccion("Berdelaren eboluzioa", "Evolución del verdel", "h3")
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Pisua / Peso (Kg)', 'Fakturazioa / Facturación (€)', 
                          'Prezioa / Precio (€/Kg)', 'Ontziak / Buques')
        )
        
        fig.add_trace(go.Scatter(x=evol_verdel['Año'], y=evol_verdel['Peso (Kg)'],
                                  mode='lines+markers', name='Pisua', line=dict(color=COLORES['primario'])),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=evol_verdel['Año'], y=evol_verdel['Facturación (€)'],
                                  mode='lines+markers', name='Fakturazioa', line=dict(color=COLORES['secundario'])),
                      row=1, col=2)
        fig.add_trace(go.Scatter(x=evol_verdel['Año'], y=evol_verdel['Precio (€/Kg)'],
                                  mode='lines+markers', name='Prezioa', line=dict(color=COLORES['exito'])),
                      row=2, col=1)
        fig.add_trace(go.Scatter(x=evol_verdel['Año'], y=evol_verdel['Buques'],
                                  mode='lines+markers', name='Ontziak', line=dict(color=COLORES['info'])),
                      row=2, col=2)
        
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # --- Precios por segmento ---
        titulo_seccion("Segmentuen araberako prezioak", "Precios por segmento", "h3")
        
        precio_segmento = df_verdel.groupby(['Año_int', 'Censo_Segmento']).apply(
            lambda x: (x['Total precio (€)'].sum() / x['Peso (Kg)'].sum()) if x['Peso (Kg)'].sum() > 0 else 0
        ).reset_index()
        precio_segmento.columns = ['Año', 'Segmento', 'Precio (€/Kg)']
        
        fig_precio_seg = px.line(
            precio_segmento,
            x='Año',
            y='Precio (€/Kg)',
            color='Segmento',
            markers=True,
            title='Segmentuen araberako prezioaren eboluzioa / Evolución del precio por segmento',
            color_discrete_map=COLORES
        )
        fig_precio_seg.update_layout(height=400)
        st.plotly_chart(fig_precio_seg, use_container_width=True)
        
        st.markdown("---")
        
        # --- Dependencia del Verdel por Peso - SEGMENTO ---
        titulo_seccion("Berdelaren menpekotasuna pisuan segmentu eta urteka", 
                      "Dependencia del verdel en peso (%) por segmento y año", "h3")
        
        # Calcular peso total por segmento y año (todas las especies, con los filtros aplicados)
        df_base_filtrado = df[
            (df['Año_int'].isin(años_seleccionados) if años_seleccionados else True) &
            (df['Censo_PueBasTH2'].isin(territorios_seleccionados) if territorios_seleccionados else True) &
            (df['Puerto base'].isin(puertos_seleccionados) if puertos_seleccionados else True) &
            (df['Censo_Segmento'].isin(segmentos_seleccionados) if segmentos_seleccionados else True)
        ].copy()
        
        peso_total_seg_año = df_base_filtrado.groupby(['Censo_Segmento', 'Año_int'])['Peso (Kg)'].sum().reset_index()
        peso_total_seg_año.columns = ['Segmento', 'Año_int', 'Peso_Total']
        
        # Calcular peso del verdel por segmento y año
        peso_verdel_seg_año = df_verdel.groupby(['Censo_Segmento', 'Año_int'])['Peso (Kg)'].sum().reset_index()
        peso_verdel_seg_año.columns = ['Segmento', 'Año_int', 'Peso_Verdel']
        
        # Merge y calcular porcentaje
        df_dep_peso_seg = peso_total_seg_año.merge(peso_verdel_seg_año, on=['Segmento', 'Año_int'], how='inner')
        df_dep_peso_seg['Dependencia (%)'] = (df_dep_peso_seg['Peso_Verdel'] / df_dep_peso_seg['Peso_Total'] * 100).round(1)
        
        # Pivotar
        df_dep_peso_seg_pivot = df_dep_peso_seg.pivot(index='Segmento', columns='Año_int', values='Dependencia (%)')
        df_dep_peso_seg_pivot = df_dep_peso_seg_pivot.reset_index()
        
        # Reordenar columnas
        años_cols_seg = [col for col in df_dep_peso_seg_pivot.columns if isinstance(col, (int, np.integer))]
        df_dep_peso_seg_pivot = df_dep_peso_seg_pivot[['Segmento'] + sorted(años_cols_seg)]
        df_dep_peso_seg_pivot.columns = ['Segmento'] + [str(a) for a in sorted(años_cols_seg)]
        
        # Formatear porcentajes
        años_str_seg = [str(a) for a in sorted(años_cols_seg)]
        for col in años_str_seg:
            df_dep_peso_seg_pivot[col] = df_dep_peso_seg_pivot[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        
        st.dataframe(df_dep_peso_seg_pivot, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # --- Dependencia del Verdel por Facturación - SEGMENTO ---
        titulo_seccion("Berdelaren menpekotasuna fakturazioan segmentu eta urteka", 
                      "Dependencia del verdel en facturación (%) por segmento y año", "h3")
        
        # Calcular facturación total por segmento y año
        fact_total_seg_año = df_base_filtrado.groupby(['Censo_Segmento', 'Año_int'])['Total precio (€)'].sum().reset_index()
        fact_total_seg_año.columns = ['Segmento', 'Año_int', 'Fact_Total']
        
        # Calcular facturación del verdel por segmento y año
        fact_verdel_seg_año = df_verdel.groupby(['Censo_Segmento', 'Año_int'])['Total precio (€)'].sum().reset_index()
        fact_verdel_seg_año.columns = ['Segmento', 'Año_int', 'Fact_Verdel']
        
        # Merge y calcular porcentaje
        df_dep_fact_seg = fact_total_seg_año.merge(fact_verdel_seg_año, on=['Segmento', 'Año_int'], how='inner')
        df_dep_fact_seg['Dependencia (%)'] = (df_dep_fact_seg['Fact_Verdel'] / df_dep_fact_seg['Fact_Total'] * 100).round(1)
        
        # Pivotar
        df_dep_fact_seg_pivot = df_dep_fact_seg.pivot(index='Segmento', columns='Año_int', values='Dependencia (%)')
        df_dep_fact_seg_pivot = df_dep_fact_seg_pivot.reset_index()
        
        # Reordenar columnas
        años_cols_seg_f = [col for col in df_dep_fact_seg_pivot.columns if isinstance(col, (int, np.integer))]
        df_dep_fact_seg_pivot = df_dep_fact_seg_pivot[['Segmento'] + sorted(años_cols_seg_f)]
        df_dep_fact_seg_pivot.columns = ['Segmento'] + [str(a) for a in sorted(años_cols_seg_f)]
        
        # Formatear porcentajes
        años_str_seg_f = [str(a) for a in sorted(años_cols_seg_f)]
        for col in años_str_seg_f:
            df_dep_fact_seg_pivot[col] = df_dep_fact_seg_pivot[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        
        st.dataframe(df_dep_fact_seg_pivot, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # --- Dependencia del Verdel por Peso - BUQUE ---
        titulo_seccion("Berdelaren menpekotasuna pisuan ontzi eta urteka", 
                      "Dependencia del verdel en peso (%) por buque y año", "h3")
        
        peso_total_buque_año = df_base_filtrado.groupby(['Nombre buque', 'Año_int'])['Peso (Kg)'].sum().reset_index()
        peso_total_buque_año.columns = ['Nombre buque', 'Año_int', 'Peso_Total']
        
        # Calcular peso del verdel por buque y año
        peso_verdel_buque_año = df_verdel.groupby(['Nombre buque', 'Año_int'])['Peso (Kg)'].sum().reset_index()
        peso_verdel_buque_año.columns = ['Nombre buque', 'Año_int', 'Peso_Verdel']
        
        # Merge y calcular porcentaje
        df_dep_peso = peso_total_buque_año.merge(peso_verdel_buque_año, on=['Nombre buque', 'Año_int'], how='inner')
        df_dep_peso['Dependencia (%)'] = (df_dep_peso['Peso_Verdel'] / df_dep_peso['Peso_Total'] * 100).round(1)
        
        # Pivotar
        df_dep_peso_pivot = df_dep_peso.pivot(index='Nombre buque', columns='Año_int', values='Dependencia (%)')
        
        # Añadir info del buque
        buques_info_verdel = df_verdel.groupby('Nombre buque').agg({
            'Censo_Segmento': 'first',
            'Puerto base': 'first'
        }).reset_index()
        
        df_dep_peso_pivot = df_dep_peso_pivot.reset_index()
        df_dep_peso_pivot = df_dep_peso_pivot.merge(buques_info_verdel, on='Nombre buque', how='left')
        
        # Reordenar columnas
        años_cols_dep = [col for col in df_dep_peso_pivot.columns if isinstance(col, (int, np.integer))]
        df_dep_peso_pivot = df_dep_peso_pivot[['Nombre buque', 'Censo_Segmento', 'Puerto base'] + sorted(años_cols_dep)]
        df_dep_peso_pivot.columns = ['Buque', 'Segmento', 'Puerto'] + [str(a) for a in sorted(años_cols_dep)]
        
        # Formatear porcentajes
        años_str_dep = [str(a) for a in sorted(años_cols_dep)]
        for col in años_str_dep:
            df_dep_peso_pivot[col] = df_dep_peso_pivot[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        
        df_dep_peso_pivot = df_dep_peso_pivot.reset_index(drop=True)
        df_dep_peso_pivot.index = df_dep_peso_pivot.index + 1
        
        st.dataframe(df_dep_peso_pivot, use_container_width=True, height=400)
        
        st.markdown("---")
        
        # --- Dependencia del Verdel por Facturación ---
        titulo_seccion("Berdelaren menpekotasuna fakturazioan ontzi eta urteka", 
                      "Dependencia del verdel en facturación (%) por buque y año", "h3")
        
        # Calcular facturación total por buque y año
        fact_total_buque_año = df_base_filtrado.groupby(['Nombre buque', 'Año_int'])['Total precio (€)'].sum().reset_index()
        fact_total_buque_año.columns = ['Nombre buque', 'Año_int', 'Fact_Total']
        
        # Calcular facturación del verdel por buque y año
        fact_verdel_buque_año = df_verdel.groupby(['Nombre buque', 'Año_int'])['Total precio (€)'].sum().reset_index()
        fact_verdel_buque_año.columns = ['Nombre buque', 'Año_int', 'Fact_Verdel']
        
        # Merge y calcular porcentaje
        df_dep_fact = fact_total_buque_año.merge(fact_verdel_buque_año, on=['Nombre buque', 'Año_int'], how='inner')
        df_dep_fact['Dependencia (%)'] = (df_dep_fact['Fact_Verdel'] / df_dep_fact['Fact_Total'] * 100).round(1)
        
        # Pivotar
        df_dep_fact_pivot = df_dep_fact.pivot(index='Nombre buque', columns='Año_int', values='Dependencia (%)')
        
        df_dep_fact_pivot = df_dep_fact_pivot.reset_index()
        df_dep_fact_pivot = df_dep_fact_pivot.merge(buques_info_verdel, on='Nombre buque', how='left')
        
        # Reordenar columnas
        años_cols_dep_f = [col for col in df_dep_fact_pivot.columns if isinstance(col, (int, np.integer))]
        df_dep_fact_pivot = df_dep_fact_pivot[['Nombre buque', 'Censo_Segmento', 'Puerto base'] + sorted(años_cols_dep_f)]
        df_dep_fact_pivot.columns = ['Buque', 'Segmento', 'Puerto'] + [str(a) for a in sorted(años_cols_dep_f)]
        
        # Formatear porcentajes
        años_str_dep_f = [str(a) for a in sorted(años_cols_dep_f)]
        for col in años_str_dep_f:
            df_dep_fact_pivot[col] = df_dep_fact_pivot[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        
        df_dep_fact_pivot = df_dep_fact_pivot.reset_index(drop=True)
        df_dep_fact_pivot.index = df_dep_fact_pivot.index + 1
        
        st.dataframe(df_dep_fact_pivot, use_container_width=True, height=400)

# =============================================================================
# TAB 5: MERCADO Y COMPRADORES
# =============================================================================

with tab5:
    titulo_seccion("Merkatua eta Erosleak", "Mercado y Compradores", "h2")
    
    df_compradores = df_filtrado.copy()
    
    if len(df_compradores) == 0:
        st.warning("⚠️ Ez dago daturik hautatutako iragazkiekin")
    else:
        n_compradores = df_compradores['Comprador - Nombre'].nunique()
        n_establecimientos = df_compradores['Establecimiento venta - Nombre'].nunique()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            metrica_personalizada("Erosle bakarrak", "Compradores únicos", n_compradores)
        with col2:
            metrica_personalizada("Establezimenduak", "Establecimientos", n_establecimientos)
        with col3:
            metrica_personalizada("Eragiketak", "Operaciones", f"{len(df_compradores):,}")
        
        st.markdown("---")
        
        titulo_seccion("Erosle nagusiak", "Top compradores", "h3")
        
        top_compradores = df_compradores.groupby('Comprador - Nombre').agg({
            'Peso (Kg)': 'sum',
            'Total precio (€)': 'sum'
        }).sort_values('Peso (Kg)', ascending=False).head(15).reset_index()
        
        top_compradores['% Peso'] = top_compradores['Peso (Kg)'] / top_compradores['Peso (Kg)'].sum() * 100
        
        fig_comp = px.bar(
            top_compradores,
            x='Peso (Kg)',
            y='Comprador - Nombre',
            orientation='h',
            title='Pisuaren arabera 15 erosle nagusiak / Top 15 compradores por peso',
            color_discrete_sequence=[COLORES['primario']]
        )
        fig_comp.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
        st.plotly_chart(fig_comp, use_container_width=True)
        
        st.markdown("---")
        
        titulo_seccion("Merkatuaren kontzentrazioa", "Concentración del mercado", "h3")
        
        compradores_ordenados = df_compradores.groupby('Comprador - Nombre')['Peso (Kg)'].sum().sort_values(ascending=False)
        compradores_ordenados_cumsum = compradores_ordenados.cumsum() / compradores_ordenados.sum() * 100
        
        n_80 = (compradores_ordenados_cumsum <= 80).sum() + 1
        top5_pct = compradores_ordenados.head(5).sum() / compradores_ordenados.sum() * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            metrica_personalizada(
                "5 erosle nagusiek kontzentratzen dute", 
                "Top 5 compradores concentran", 
                f"{top5_pct:.1f}%"
            )
        with col2:
            metrica_personalizada(
                "Merkatuaren %80 lortzeko erosleak", 
                "Compradores para 80% del mercado", 
                n_80
            )
        
        df_pareto = pd.DataFrame({
            'Comprador': range(1, len(compradores_ordenados_cumsum) + 1),
            '% Acumulado': compradores_ordenados_cumsum.values
        })
        
        fig_pareto = px.line(
            df_pareto.head(50),
            x='Comprador',
            y='% Acumulado',
            title='Kontzentrazio-kurba (Pareto) / Curva de concentración',
            markers=True
        )
        fig_pareto.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80%")
        fig_pareto.update_layout(height=400)
        st.plotly_chart(fig_pareto, use_container_width=True)

# =============================================================================
# TAB 6: INFORMACIÓN
# =============================================================================

with tab6:
    titulo_seccion("Metodologia eta informazioa", "Metodología e información", "h2")
    
    col1, col2 = st.columns(2)
    
    with col1:
        titulo_seccion("Azterlanaren irismena", "Alcance del estudio", "h3")
        
        st.markdown(f"""
        | Parametroa / Parámetro | Balioa / Valor |
        |------------------------|----------------|
        | **Aldia / Periodo** | 2018 - 2025 (8 urte / años) |
        | **Erregistro guztiak / Registros totales** | {stats.get('registros_totales', 'N/A'):,} |
        | **Ontzi bakarrak / Buques únicos** | {stats.get('buques_unicos', 'N/A')} |
        | **Espezieak / Especies** | {stats.get('especies_unicas', 'N/A')} |
        | **Pisu totala / Peso total** | {stats.get('peso_total_kg', 0)/1e6:.1f} M Kg |
        | **Fakturazio totala / Facturación total** | {stats.get('facturacion_total_eur', 0)/1e6:.1f} M € |
        """)
    
    with col2:
        titulo_seccion("Datu-iturriak", "Fuentes de datos", "h3")
        
        st.markdown("""
        **Datu-fitxategiak / Ficheros de datos:**
        - BD 2018.xlsx - BD 2025.xlsx
        
        **Aplikatutako iragazkiak / Filtros aplicados:**
        - Euskal ontziak bakarrik / Solo barcos vascos
        - Baztertuak / Excluidos: Bacaladero, Atunero Congelador
        
        **Teknologiak / Tecnologías:**
        - Python, Pandas, Streamlit, Plotly
        """)
    
    st.markdown("---")
    
    titulo_seccion("Aurkikuntza nagusiak", "Hallazgos principales", "h3")
    
    st.markdown("""
    ### Sektorearen eboluzioa (2018-2025) / Evolución del sector
    
    - 📉 **Pisua / Peso**: -25.6% (47.4M → 35.3M Kg)
    - 📈 **Fakturazioa / Facturación**: +8.9% (94.4M → 102.7M €)
    - 💰 **Batez besteko prezioa / Precio medio**: +46.3% (1.99 → 2.91 €/Kg)
    
    ### Berdelaren Paradoxa / Paradoja del Verdel
    
    - 📉 **Harrapaketak / Capturas**: -38.8%
    - 📈 **Fakturazioa / Facturación**: +28.6%
    - 💰 **Prezioa / Precio**: +110.2% (0.95 → 2.00 €/Kg)
    
    ### Identifikatutako arriskuak / Riesgos identificados
    
    - ⚠️ Harrapaketen beherakada etengabea / Descenso sostenido de capturas
    - ⚠️ Kontzentrazio geografiko handia / Alta concentración geográfica (3 portu > 71%)
    - ⚠️ Berdel flota espezializatuaren uztea / Abandono de flota especializada en verdel
    - ⚠️ Berdelaren eskasia posiblea / Posible escasez de verdel
    """)
    
    st.markdown("---")
    
    st.caption("""
    **Garatzailea / Desarrollado por:** HAZI  
    **Data / Fecha:** 2026ko Otsaila / Febrero 2026  
    **Bertsioa / Versión:** 1.0
    """)

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Euskal Flotaren Lehorreratzeak / Desembarcos Flota Vasca | 
    Streamlit-ekin garatua / Desarrollado con Streamlit | HAZI 2026</small>
</div>
""", unsafe_allow_html=True)