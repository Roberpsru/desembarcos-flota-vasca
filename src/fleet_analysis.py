"""
================================================================================
FLEET ANALYSIS - Funciones de análisis de flota
================================================================================
Proyecto: Desembarco_Estudio_2026
Descripción: Funciones para analizar presencia, continuidad y rotación de buques.
================================================================================
"""

import pandas as pd
import numpy as np

# =============================================================================
# ANÁLISIS DE PRESENCIA
# =============================================================================

def analisis_presencia_flota(df: pd.DataFrame) -> dict:
    """
    Analiza la presencia de buques por año.
    
    Args:
        df: DataFrame de desembarcos (ya filtrado si es necesario)
        
    Returns:
        dict: Diccionario con resultados del análisis
            - años: lista de años
            - buques_por_año: dict {año: set de buques}
            - buques_todos: set de todos los buques únicos
            - buques_info: dict con info de cada buque
            - resumen_por_año: DataFrame con métricas por año
    """
    # Asegurar que existe Año_int
    if 'Año_int' not in df.columns:
        df = df.copy()
        df['Año_int'] = df['Año'].apply(lambda x: int(str(x)[:4]) if pd.notna(x) else None)
    
    años = sorted(df['Año_int'].dropna().unique().tolist())
    
    # Buques por año
    buques_por_año = {}
    resumen_por_año = []
    
    for año in años:
        df_año = df[df['Año_int'] == año]
        buques_año = set(df_año['Nombre buque'].unique())
        buques_por_año[año] = buques_año
        
        resumen_por_año.append({
            'Año': año,
            'Buques': len(buques_año),
            'Operaciones': len(df_año),
            'Peso (Kg)': df_año['Peso (Kg)'].sum(),
            'Facturación (€)': df_año['Total precio (€)'].sum(),
            'Especies': df_año['Especie - Nombre comercial'].nunique()
        })
    
    # Total de buques únicos
    buques_todos = set()
    for año in años:
        buques_todos = buques_todos.union(buques_por_año[año])
    
    # Info de cada buque
    buques_info = df.groupby('Nombre buque').agg({
        'Censo_Segmento': 'first',
        'Puerto base': 'first'
    }).to_dict('index')
    
    return {
        'años': años,
        'buques_por_año': buques_por_año,
        'buques_todos': buques_todos,
        'buques_info': buques_info,
        'resumen_por_año': pd.DataFrame(resumen_por_año)
    }


def generar_cuadro_presencia(resultado_analisis: dict) -> pd.DataFrame:
    """
    Genera el cuadro de presencia (Buque × Año).
    
    Args:
        resultado_analisis: Resultado de analisis_presencia_flota()
        
    Returns:
        pd.DataFrame: Cuadro con presencia Sí/No por buque y año
            Columnas: Buque, Segmento, Puerto, [años...], Total
    """
    años = resultado_analisis['años']
    buques_por_año = resultado_analisis['buques_por_año']
    buques_todos = resultado_analisis['buques_todos']
    buques_info = resultado_analisis['buques_info']
    
    # Construir datos del cuadro
    datos = []
    for buque in sorted(buques_todos):
        info = buques_info.get(buque, {})
        fila = {
            'Buque': buque,
            'Segmento': info.get('Censo_Segmento', ''),
            'Puerto': info.get('Puerto base', '')
        }
        
        años_activo = 0
        for año in años:
            if buque in buques_por_año[año]:
                fila[str(año)] = 'Sí'
                años_activo += 1
            else:
                fila[str(año)] = 'No'
        
        fila['Total'] = años_activo
        datos.append(fila)
    
    df_cuadro = pd.DataFrame(datos)
    
    # Ordenar por Total descendente, luego por nombre
    df_cuadro = df_cuadro.sort_values(['Total', 'Buque'], ascending=[False, True])
    df_cuadro = df_cuadro.reset_index(drop=True)
    df_cuadro.index = df_cuadro.index + 1  # Empezar en 1
    df_cuadro.index.name = '#'
    
    return df_cuadro


# =============================================================================
# ANÁLISIS DE CONTINUIDAD
# =============================================================================

def analisis_continuidad(resultado_analisis: dict) -> dict:
    """
    Analiza la continuidad de la flota (cuántos años activo cada buque).
    
    Args:
        resultado_analisis: Resultado de analisis_presencia_flota()
        
    Returns:
        dict: Diccionario con métricas de continuidad
            - conteo_años_activos: dict {n_años: [lista de buques]}
            - resumen_continuidad: DataFrame con distribución
            - buques_todos_años: set de buques activos todos los años
            - n_años: número total de años
            - total_buques: número total de buques únicos
    """
    años = resultado_analisis['años']
    buques_por_año = resultado_analisis['buques_por_año']
    buques_todos = resultado_analisis['buques_todos']
    n_años = len(años)
    
    # Contar buques por número de años activos
    conteo_años_activos = {}
    for buque in buques_todos:
        años_activo = sum([1 for a in años if buque in buques_por_año[a]])
        if años_activo not in conteo_años_activos:
            conteo_años_activos[años_activo] = []
        conteo_años_activos[años_activo].append(buque)
    
    # Crear DataFrame de resumen
    resumen_continuidad = []
    for n in sorted(conteo_años_activos.keys(), reverse=True):
        buques_n = conteo_años_activos[n]
        pct = len(buques_n) / len(buques_todos) * 100
        resumen_continuidad.append({
            'Años activo': n,
            'Buques': len(buques_n),
            '%': pct
        })
    
    # Buques activos todos los años
    buques_todos_años = buques_por_año[años[0]]
    for año in años[1:]:
        buques_todos_años = buques_todos_años.intersection(buques_por_año[año])
    
    return {
        'conteo_años_activos': conteo_años_activos,
        'resumen_continuidad': pd.DataFrame(resumen_continuidad),
        'buques_todos_años': buques_todos_años,
        'n_años': n_años,
        'total_buques': len(buques_todos)
    }


def analisis_entradas_salidas(resultado_analisis: dict) -> pd.DataFrame:
    """
    Analiza las entradas (nuevos buques) y salidas (bajas) por año.
    
    Args:
        resultado_analisis: Resultado de analisis_presencia_flota()
        
    Returns:
        pd.DataFrame: Tabla con entradas y salidas por año
            Columnas: Año, Activos, Nuevos, Bajas
    """
    años = resultado_analisis['años']
    buques_por_año = resultado_analisis['buques_por_año']
    
    datos = []
    for i, año in enumerate(años):
        if i == 0:
            datos.append({
                'Año': año,
                'Activos': len(buques_por_año[año]),
                'Nuevos': len(buques_por_año[año]),  # Todos son "nuevos" el primer año
                'Bajas': 0
            })
        else:
            año_anterior = años[i-1]
            nuevos = len(buques_por_año[año] - buques_por_año[año_anterior])
            bajas = len(buques_por_año[año_anterior] - buques_por_año[año])
            activos = len(buques_por_año[año])
            datos.append({
                'Año': año,
                'Activos': activos,
                'Nuevos': nuevos,
                'Bajas': bajas
            })
    
    return pd.DataFrame(datos)


# =============================================================================
# DETALLE POR BUQUE
# =============================================================================

def detalle_buque(df: pd.DataFrame, nombre_buque: str) -> dict:
    """
    Obtiene el detalle de actividad de un buque específico.
    
    Args:
        df: DataFrame de desembarcos
        nombre_buque: Nombre del buque a analizar
        
    Returns:
        dict: Diccionario con métricas del buque o None si no existe
            - nombre, segmento, puerto
            - operaciones, peso_total, facturacion_total, precio_medio
            - especies_distintas, años_activo
            - top_especies: DataFrame con top 5 especies
            - evolucion_anual: DataFrame con evolución por año
    """
    df_buque = df[df['Nombre buque'] == nombre_buque]
    
    if len(df_buque) == 0:
        return None
    
    # Asegurar Año_int
    if 'Año_int' not in df_buque.columns:
        df_buque = df_buque.copy()
        df_buque['Año_int'] = df_buque['Año'].apply(lambda x: int(str(x)[:4]) if pd.notna(x) else None)
    
    # Métricas generales
    peso_total = df_buque['Peso (Kg)'].sum()
    fact_total = df_buque['Total precio (€)'].sum()
    
    metricas = {
        'nombre': nombre_buque,
        'segmento': df_buque['Censo_Segmento'].iloc[0] if 'Censo_Segmento' in df_buque.columns else '',
        'puerto': df_buque['Puerto base'].iloc[0] if 'Puerto base' in df_buque.columns else '',
        'operaciones': len(df_buque),
        'peso_total': peso_total,
        'facturacion_total': fact_total,
        'precio_medio': fact_total / peso_total if peso_total > 0 else 0,
        'especies_distintas': df_buque['Especie - Nombre comercial'].nunique(),
        'años_activo': df_buque['Año_int'].nunique()
    }
    
    # Top especies
    top_especies = df_buque.groupby('Especie - Nombre comercial').agg({
        'Peso (Kg)': 'sum',
        'Total precio (€)': 'sum'
    }).sort_values('Peso (Kg)', ascending=False).head(5)
    top_especies = top_especies.reset_index()
    
    metricas['top_especies'] = top_especies
    
    # Evolución anual
    evolucion = df_buque.groupby('Año_int').agg({
        'Peso (Kg)': 'sum',
        'Total precio (€)': 'sum'
    }).reset_index()
    evolucion.columns = ['Año', 'Peso (Kg)', 'Facturación (€)']
    
    metricas['evolucion_anual'] = evolucion
    
    return metricas


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def obtener_buques_por_criterio(resultado_analisis: dict, criterio: str) -> list:
    """
    Obtiene lista de buques según un criterio de continuidad.
    
    Args:
        resultado_analisis: Resultado de analisis_presencia_flota()
        criterio: 'todos_años', 'solo_primero', 'solo_ultimo', 'intermitentes'
        
    Returns:
        list: Lista de nombres de buques
    """
    años = resultado_analisis['años']
    buques_por_año = resultado_analisis['buques_por_año']
    buques_todos = resultado_analisis['buques_todos']
    
    if criterio == 'todos_años':
        # Buques activos todos los años
        resultado = buques_por_año[años[0]]
        for año in años[1:]:
            resultado = resultado.intersection(buques_por_año[año])
        return sorted(list(resultado))
    
    elif criterio == 'solo_primero':
        # Buques que solo aparecen el primer año
        return sorted([b for b in buques_por_año[años[0]] 
                      if all(b not in buques_por_año[a] for a in años[1:])])
    
    elif criterio == 'solo_ultimo':
        # Buques que solo aparecen el último año
        return sorted([b for b in buques_por_año[años[-1]] 
                      if all(b not in buques_por_año[a] for a in años[:-1])])
    
    elif criterio == 'intermitentes':
        # Buques que aparecen algunos años pero no todos
        buques_todos_años = buques_por_año[años[0]]
        for año in años[1:]:
            buques_todos_años = buques_todos_años.intersection(buques_por_año[año])
        return sorted([b for b in buques_todos 
                      if b not in buques_todos_años and 
                      sum([1 for a in años if b in buques_por_año[a]]) > 1])
    
    return []
