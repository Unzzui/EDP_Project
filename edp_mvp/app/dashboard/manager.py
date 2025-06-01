from flask import Blueprint, render_template, request, jsonify
import json
from flask_login import login_required
from app.utils.gsheet import read_sheet
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Constants
COSTO_CAPITAL_ANUAL = 0.12  # 12% anual, ajustar según realidad de la empresa
TASA_DIARIA = COSTO_CAPITAL_ANUAL / 360
META_DIAS_COBRO = 30  # Meta de días de cobro

manager_bp = Blueprint('manager_bp', __name__, url_prefix='/manager')



# Add this custom JSON encoder class to handle Python-specific types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        if pd.isna(obj):
            return None
        return super().default(obj)



def clean_nan_values(obj):
    """Recursively clean NaN values from data structures to ensure proper JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, (float, np.float64, np.float32)):
        # Handle all floating point types and check if it's NaN
        try:
            if np.isnan(obj):
                return None
        except:
            pass
    elif obj is np.nan:
        return None
    elif pd.isna(obj):
        return None
    
    return obj
    
    
@manager_bp.route('/dashboard')
#@login_required
def dashboard():
    try:
        # ===== PASO 1: LEER DATOS =====
        df_edp = read_sheet("edp!A1:V")
        df_log = read_sheet("log!A1:V")
        
        print(f"📊 Datos leídos: df_edp={len(df_edp)} filas, df_log={len(df_log)} filas")
        
        if df_edp.empty:
            print("⚠️ DataFrame EDP está vacío")
            return render_template('manager/dashboard.html', 
                                 error="No hay datos disponibles", 
                                 kpis=obtener_kpis_vacios(),
                                 charts_json="{}",
                                 charts={})
        
        # ===== PASO 2: PREPARAR DATOS BÁSICOS TEMPRANO =====
        hoy = datetime.now()
        df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
        df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce').fillna(0)
        df_edp['Monto Propuesto'] = pd.to_numeric(df_edp['Monto Propuesto'], errors='coerce').fillna(0)
        
        # CALCULAR DÍAS DE ESPERA TEMPRANO - CLAVE PARA CHARTS
        if 'Días Espera' not in df_edp.columns:
            df_edp['Días Espera'] = (hoy - df_edp['Fecha Emisión']).dt.days
            print(f"✅ Días Espera calculados para {len(df_edp)} registros")
        else:
            print("✅ Columna Días Espera ya existe")
        
        # ===== PASO 3: OBTENER PARÁMETROS DE FILTRO =====
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        periodo_rapido = request.args.get('periodo_rapido')
        departamento = request.args.get('departamento', 'todos')
        cliente = request.args.get('cliente', 'todos')
        estado = request.args.get('estado', 'todos')
        vista = request.args.get('vista', 'general')
        monto_min = request.args.get('monto_min', type=float)
        monto_max = request.args.get('monto_max', type=float)
        dias_min = request.args.get('dias_min', type=int)
        
        # Procesar filtros de fecha rápidos
        if periodo_rapido:
            if periodo_rapido == '7':
                fecha_inicio = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
                fecha_fin = hoy.strftime('%Y-%m-%d')
            elif periodo_rapido == '30':
                fecha_inicio = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')
                fecha_fin = hoy.strftime('%Y-%m-%d')
            elif periodo_rapido == '90':
                fecha_inicio = (hoy - timedelta(days=90)).strftime('%Y-%m-%d')
                fecha_fin = hoy.strftime('%Y-%m-%d')
            elif periodo_rapido == '365':
                fecha_inicio = (hoy - timedelta(days=365)).strftime('%Y-%m-%d')
                fecha_fin = hoy.strftime('%Y-%m-%d')
        
        # ===== PASO 4: PREPARAR LISTAS PARA SELECTORES =====
        jefes_proyecto = sorted([j for j in df_edp['Jefe de Proyecto'].unique() if pd.notna(j) and j.strip()])
        clientes = sorted([c for c in df_edp['Cliente'].unique() if pd.notna(c) and c.strip()])
        
        # ===== PASO 5: APLICAR FILTROS =====
        df_filtrado = df_edp.copy()
        
        # Aplicar filtro de fechas personalizado
        if fecha_inicio or fecha_fin:
            df_filtrado = aplicar_filtro_fechas(df_filtrado, fecha_inicio, fecha_fin)
        
        # Filtro por vista especial
        if vista == 'criticos':
            if 'Crítico' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Crítico'] == True]
            else:
                df_filtrado = df_filtrado[df_filtrado['Días Espera'] > 30]
        elif vista == 'completados':
            df_filtrado = df_filtrado[df_filtrado['Estado'].str.strip().isin(['pagado', 'validado'])]
        elif vista == 'alto_valor':
            df_filtrado = df_filtrado[df_filtrado['Monto Aprobado'] > 50_000_000]
        
        # Filtros adicionales
        if monto_min is not None:
            df_filtrado = df_filtrado[df_filtrado['Monto Aprobado'] >= monto_min * 1_000_000]
        if monto_max is not None:
            df_filtrado = df_filtrado[df_filtrado['Monto Aprobado'] <= monto_max * 1_000_000]
        if dias_min is not None:
            df_filtrado = df_filtrado[df_filtrado['Días Espera'] >= dias_min]
        
        print(f"📊 Datos después de filtros: {len(df_filtrado)} registros")
        
        # ===== PASO 6: OBTENER DATOS DE CHARTS CON VALIDACIÓN =====
        if df_filtrado.empty:
            print("⚠️ DataFrame filtrado está vacío, usando datos por defecto")
        else:
            print(f"📊 Columnas disponibles para charts: {list(df_filtrado.columns)}")
            
            try:
                charts_data = obtener_datos_charts_ejecutivos(df_filtrado, df_log, None, departamento, cliente, estado)
                print("✅ Charts data obtenidos exitosamente")
                print(f"📊 Charts generados: {list(charts_data.keys())}")
            except Exception as chart_error:
                print(f"❌ Error obteniendo charts data: {chart_error}")
                import traceback
                traceback.print_exc()
        
        # ===== PASO 7: CALCULAR KPIs =====
        try:
            kpis = calcular_kpis_ejecutivos_con_fechas(df_filtrado, df_log, fecha_inicio, fecha_fin, departamento, cliente, estado)
            kpis = clean_nan_values(kpis)
            print("✅ KPIs calculados exitosamente")
        except Exception as kpi_error:
            print(f"❌ Error calculando KPIs: {kpi_error}")
            import traceback
            traceback.print_exc()
            kpis = obtener_kpis_vacios()
        
        # ===== PASO 8: LIMPIAR Y SERIALIZAR CHARTS DATA =====
        try:
            # Limpiar datos para JSON
            charts_data_clean = clean_charts_data_for_json(charts_data)
            print("✅ Charts data limpiados")
            
            # Serializar a JSON
            charts_json = json.dumps(charts_data_clean, cls=CustomJSONEncoder, ensure_ascii=False)
            print(f"✅ Charts JSON serializado: {len(charts_json)} caracteres")
            
            # Verificar que el JSON es válido
            json.loads(charts_json)  # Test de parsing
            print("✅ JSON válido confirmado")
            
        except Exception as json_error:
            print(f"❌ Error serializando charts JSON: {json_error}")
            import traceback
            traceback.print_exc()
            

        
        # ===== PASO 9: OBTENER DATOS ADICIONALES =====
        try:
            cash_forecast_data = generar_cash_forecast(df_filtrado)
            alertas = obtener_alertas_criticas(df_filtrado)
            print("✅ Datos adicionales obtenidos")
        except Exception as extra_error:
            print(f"❌ Error obteniendo datos adicionales: {extra_error}")
            cash_forecast_data = {}
            alertas = []
        
        # ===== PASO 10: RENDERIZAR TEMPLATE =====
        print("🎯 Renderizando template...")
        
        return render_template('manager/dashboard.html', 
                             kpis=kpis,
                             charts=charts_data_clean,     # Para uso directo en template
                             charts_json=charts_json,      # Para JavaScript
                             cash_forecast=cash_forecast_data,
                             alertas=alertas,
                             fecha_inicio=fecha_inicio,
                             fecha_fin=fecha_fin,
                             periodo_rapido=periodo_rapido,
                             departamento=departamento,
                             cliente=cliente,
                             estado=estado,
                             vista=vista,
                             monto_min=monto_min,
                             monto_max=monto_max,
                             dias_min=dias_min,
                             jefes_proyecto=jefes_proyecto,
                             clientes=clientes,
                             error=None)
    
    except Exception as e:
        print(f"❌ Error crítico en dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return render_template('manager/dashboard.html', 
                             error=f"Error al cargar el dashboard: {str(e)}", 
                             kpis=obtener_kpis_vacios(),
                             charts={},
                             charts_json="{}",
                             cash_forecast={},
                             alertas=[],
                             fecha_inicio=None,
                             fecha_fin=None,
                             departamento='todos',
                             cliente='todos',
                             estado='todos',
                             vista='general',
                             jefes_proyecto=[],
                             clientes=[])
        
        
        
def aplicar_filtro_fechas(df_edp, fecha_inicio=None, fecha_fin=None):
    """Aplica filtros de fecha al DataFrame"""
    df_filtrado = df_edp.copy()
    
    # Asegurar que las fechas están en formato datetime
    if 'Fecha Emisión' in df_filtrado.columns:
        df_filtrado['Fecha Emisión'] = pd.to_datetime(df_filtrado['Fecha Emisión'], errors='coerce')
    
    # Aplicar filtro de fecha inicio
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            df_filtrado = df_filtrado[df_filtrado['Fecha Emisión'] >= fecha_inicio_dt]
        except ValueError:
            print(f"Error al parsear fecha_inicio: {fecha_inicio}")
    
    # Aplicar filtro de fecha fin
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            # Incluir todo el día final
            fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
            df_filtrado = df_filtrado[df_filtrado['Fecha Emisión'] <= fecha_fin_dt]
        except ValueError:
            print(f"Error al parsear fecha_fin: {fecha_fin}")
    
    return df_filtrado


def calcular_kpis_ejecutivos_con_fechas(df_edp, df_log, fecha_inicio=None, fecha_fin=None, departamento='todos', cliente='todos', estado='todos'):
    """Calcula los KPIs principales para el dashboard ejecutivo con filtros de fecha personalizados"""
    
    # 1. Preparar y filtrar datos con fechas personalizadas
    df_periodo = preparar_y_filtrar_datos_con_fechas(df_edp, fecha_inicio, fecha_fin, departamento, cliente, estado)
    
    if df_periodo.empty:
        return obtener_kpis_vacios()
    
    # 2-8. Usar las mismas funciones de cálculo existentes
    metricas_financieras = calcular_metricas_financieras(df_periodo)
    metricas_operativas = calcular_metricas_operativas(df_periodo)
    metricas_rentabilidad = calcular_metricas_rentabilidad(df_periodo, metricas_financieras)
    metricas_calidad = calcular_metricas_calidad(df_periodo, df_log)
    metricas_estrategicas = calcular_metricas_estrategicas(df_periodo)
    analisis_clientes = calcular_analisis_clientes(df_periodo)
    analisis_gestores = calcular_analisis_gestores(df_periodo, metricas_rentabilidad)
    
    # 9. Combinar todos los KPIs
    return combinar_kpis(
        metricas_financieras,
        metricas_operativas,
        metricas_rentabilidad,
        metricas_calidad,
        metricas_estrategicas,
        analisis_clientes,
        analisis_gestores
    )
    
    
# 2. Función de preparación de datos
def preparar_y_filtrar_datos_con_fechas(df_edp, fecha_inicio=None, fecha_fin=None, departamento='todos', cliente='todos', estado='todos'):
    """Prepara y filtra los datos según fechas personalizadas y otros parámetros"""
    
    # Convertir fechas
    columnas_fecha = ['Fecha Emisión', 'Fecha Envío al Cliente', 'Fecha Estimada de Pago', 'Fecha Conformidad']
    for col in columnas_fecha:
        if col in df_edp.columns:
            df_edp[col] = pd.to_datetime(df_edp[col], errors='coerce')
    
    # Filtrar por fechas personalizadas
    df_periodo = df_edp.copy()
    
    if fecha_inicio:
        try:
            inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            df_periodo = df_periodo[df_periodo['Fecha Emisión'] >= inicio_dt]
        except ValueError:
            print(f"Error al parsear fecha_inicio: {fecha_inicio}")
    
    if fecha_fin:
        try:
            fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            fin_dt = fin_dt.replace(hour=23, minute=59, second=59)
            df_periodo = df_periodo[df_periodo['Fecha Emisión'] <= fin_dt]
        except ValueError:
            print(f"Error al parsear fecha_fin: {fecha_fin}")
    
    # Aplicar filtros adicionales
    if departamento != 'todos' and departamento in df_periodo['Jefe de Proyecto'].unique():
        df_periodo = df_periodo[df_periodo['Jefe de Proyecto'] == departamento]
    
    if cliente != 'todos' and cliente in df_periodo['Cliente'].unique():
        df_periodo = df_periodo[df_periodo['Cliente'] == cliente]
    
    if estado != 'todos':
        df_periodo = df_periodo[df_periodo['Estado'].str.strip() == estado]
    
    # Convertir montos
    df_periodo['Monto Propuesto'] = pd.to_numeric(df_periodo['Monto Propuesto'], errors='coerce')
    df_periodo['Monto Aprobado'] = pd.to_numeric(df_periodo['Monto Aprobado'], errors='coerce')
    
    return df_periodo

# 3. Métricas financieras
def calcular_metricas_financieras(df_periodo):
    """Calcula todas las métricas financieras"""
    estados_pendientes = ['enviado', 'revisión', 'enviado ']
    estados_completados = ['pagado', 'validado', 'pagado ', 'validado ']
    
    # Dataframes base
    df_pendientes = df_periodo[df_periodo['Estado'].str.strip().isin(estados_pendientes)]
    df_completados = df_periodo[df_periodo['Estado'].str.strip().isin(estados_completados)]
    df_criticos = df_pendientes[df_pendientes['Días Espera'] >= 30]
    
    # Cálculos básicos
    monto_pendiente = df_pendientes['Monto Aprobado'].sum()
    monto_pendiente_critico = df_criticos['Monto Aprobado'].sum()
    monto_emitido = df_periodo['Monto Propuesto'].sum()
    monto_cobrado = df_completados['Monto Aprobado'].sum()
    
    # Costo financiero de demoras
    costo_financiero = sum(
        row['Monto Aprobado'] * row['Días Espera'] * TASA_DIARIA 
        for _, row in df_criticos.iterrows()
    )
    
    # DSO (Days Sales Outstanding)
    dias_cobro_total = df_completados['Días Espera'].sum()
    edps_cobrados = len(df_completados)
    dso = round(dias_cobro_total / edps_cobrados, 1) if edps_cobrados > 0 else 0
    
    # Porcentaje cobrado
    pct_cobrado = round((monto_cobrado / monto_emitido) * 100, 1) if monto_emitido > 0 else 0
    
    # Métricas adicionales
    meta_ingresos = round(monto_emitido * 0.85 / 1_000_000, 1)
    vs_meta_ingresos = round((monto_cobrado / (meta_ingresos * 1_000_000) - 1) * 100, 1) if meta_ingresos > 0 else 0
    pct_meta_ingresos = min(round((monto_cobrado / (meta_ingresos * 1_000_000)) * 100, 1), 100) if meta_ingresos > 0 else 0
    
    return {
        'monto_pendiente': monto_pendiente,
        'monto_pendiente_critico': monto_pendiente_critico,
        'monto_emitido': monto_emitido,
        'monto_cobrado': monto_cobrado,
        'costo_financiero': costo_financiero,
        'dso': dso,
        'pct_cobrado': pct_cobrado,
        'meta_ingresos': meta_ingresos,
        'vs_meta_ingresos': vs_meta_ingresos,
        'pct_meta_ingresos': pct_meta_ingresos,
        'df_pendientes': df_pendientes,
        'df_completados': df_completados,
        'df_criticos': df_criticos
    }

# 4. Métricas operativas
def calcular_metricas_operativas(df_periodo):
    """Calcula métricas operativas y de pipeline"""
    estados_completados = ['pagado', 'validado', 'pagado ', 'validado ']
    df_pendientes = df_periodo[~df_periodo['Estado'].str.strip().isin(estados_completados)]
    
    # Aging buckets
    bucket_0_15 = len(df_pendientes[df_pendientes['Días Espera'] <= 15])
    bucket_16_30 = len(df_pendientes[(df_pendientes['Días Espera'] > 15) & (df_pendientes['Días Espera'] <= 30)])
    bucket_31_60 = len(df_pendientes[(df_pendientes['Días Espera'] > 30) & (df_pendientes['Días Espera'] <= 60)])
    bucket_60_plus = len(df_pendientes[df_pendientes['Días Espera'] > 60])
    
    # Porcentajes de aging
    total_pendientes = bucket_0_15 + bucket_16_30 + bucket_31_60 + bucket_60_plus
    if total_pendientes > 0:
        pct_30d = round((bucket_0_15 + bucket_16_30) / total_pendientes * 100, 1)
        pct_60d = round(bucket_31_60 / total_pendientes * 100, 1)
        pct_90d = round(bucket_60_plus / total_pendientes * 100, 1)
        pct_mas90d = max(0, 100 - pct_30d - pct_60d - pct_90d)
    else:
        pct_30d = pct_60d = pct_90d = pct_mas90d = 0
    
    # Avance general
    total_edps = len(df_periodo)
    finalizados = len(df_periodo[df_periodo['Estado'].str.strip().isin(estados_completados)])
    pct_avance = round((finalizados / total_edps) * 100, 1) if total_edps > 0 else 0
    
    # Backlog
    backlog_edp = len(df_periodo[~df_periodo['Estado'].str.strip().isin(estados_completados)])
    
    # Proyectos críticos
    df_criticos = df_pendientes[df_pendientes['Días Espera'] > 30]
    q_proyectos_criticos = len(df_criticos)
    valor_proyectos_criticos = round(df_criticos['Monto Aprobado'].sum() / 1_000_000, 1)
    
    return {
        'bucket_0_15': bucket_0_15,
        'bucket_16_30': bucket_16_30,
        'bucket_31_60': bucket_31_60,
        'bucket_60_plus': bucket_60_plus,
        'pct_30d': pct_30d,
        'pct_60d': pct_60d,
        'pct_90d': pct_90d,
        'pct_mas90d': pct_mas90d,
        'total_edps': total_edps,
        'pct_avance': pct_avance,
        'backlog_edp': backlog_edp,
        'q_proyectos_criticos': q_proyectos_criticos,
        'valor_proyectos_criticos': valor_proyectos_criticos,
        'proyectos_on_time': round((bucket_0_15 + bucket_16_30) / backlog_edp * 100 if backlog_edp > 0 else 0, 1),
        'proyectos_retrasados': round((bucket_31_60 + bucket_60_plus) / backlog_edp * 100 if backlog_edp > 0 else 0, 1),
        'proyectos_criticos': bucket_60_plus
    }

# 5. Métricas de rentabilidad
def calcular_metricas_rentabilidad(df_periodo, metricas_financieras):
    """Calcula métricas de rentabilidad y costos"""
    ingresos_totales_raw = metricas_financieras['monto_cobrado']
    df_completados = metricas_financieras['df_completados']
    costo_financiero = metricas_financieras['costo_financiero']
    
    # Porcentajes de costos
    costo_personal_porcentaje = 0.35
    costo_overhead_porcentaje = 0.15
    costo_tecnologia_porcentaje = 0.08
    
    # Factor de eficiencia temporal
    if len(df_completados) > 0:
        tiempo_medio_real = df_completados['Días Espera'].mean()
        factor_tiempo = max(tiempo_medio_real / 30, 1.0)
    else:
        tiempo_medio_real = 45
        factor_tiempo = 1.5
    
    # Costos calculados
    costo_personal = ingresos_totales_raw * costo_personal_porcentaje * factor_tiempo
    costo_overhead = ingresos_totales_raw * costo_overhead_porcentaje
    costo_tecnologia = ingresos_totales_raw * costo_tecnologia_porcentaje
    costos_totales = costo_personal + costo_overhead + costo_tecnologia + costo_financiero
    
    # Métricas de rentabilidad
    margen_bruto = ingresos_totales_raw - costos_totales
    rentabilidad_general = (margen_bruto / ingresos_totales_raw * 100) if ingresos_totales_raw > 0 else 0
    
    # Tendencia simulada
    reprocesos = df_periodo[df_periodo['Estado Detallado'] == 're-trabajo solicitado']
    total_edps = len(df_periodo)
    eficiencia_actual = round(metricas_financieras.get('pct_avance', 0) * (1 - len(reprocesos) / total_edps if total_edps > 0 else 0), 1)
    rentabilidad_anterior = rentabilidad_general - (eficiencia_actual - 70) * 0.3
    tendencia_rentabilidad = round(rentabilidad_general - rentabilidad_anterior, 1)
    
    # Metas y benchmarks
    meta_rentabilidad = 35.0
    vs_meta_rentabilidad = round(rentabilidad_general - meta_rentabilidad, 1)
    pct_meta_rentabilidad = min((rentabilidad_general / meta_rentabilidad * 100), 100) if meta_rentabilidad > 0 else 0
    
    # ROI y EBITDA
    roi_calculado = (margen_bruto / costos_totales * 100) if costos_totales > 0 else 0
    ebitda = margen_bruto * 0.85
    ebitda_porcentaje = (ebitda / ingresos_totales_raw * 100) if ingresos_totales_raw > 0 else 0
    
    # Benchmark
    benchmark_industria = 30.0
    posicion_vs_benchmark = round(rentabilidad_general - benchmark_industria, 1)
    
    return {
        'rentabilidad_general': round(rentabilidad_general, 1),
        'tendencia_rentabilidad': tendencia_rentabilidad,
        'meta_rentabilidad': meta_rentabilidad,
        'vs_meta_rentabilidad': vs_meta_rentabilidad,
        'pct_meta_rentabilidad': round(pct_meta_rentabilidad, 1),
        'costos_totales': round(costos_totales / 1_000_000, 2),
        'costo_personal': round(costo_personal / 1_000_000, 2),
        'costo_overhead': round(costo_overhead / 1_000_000, 2),
        'costo_tecnologia': round(costo_tecnologia / 1_000_000, 2),
        'costo_financiero_extra': round(costo_financiero / 1_000_000, 2),
        'margen_bruto_absoluto': round(margen_bruto / 1_000_000, 2),
        'roi_calculado': round(roi_calculado, 1),
        'ebitda': round(ebitda / 1_000_000, 2),
        'ebitda_porcentaje': round(ebitda_porcentaje, 1),
        'factor_tiempo_costo': round(factor_tiempo, 2),
        'benchmark_industria': benchmark_industria,
        'posicion_vs_benchmark': posicion_vs_benchmark,
        'tiempo_medio_real': round(tiempo_medio_real, 1),
        'costo_por_edp': round(costos_totales / total_edps, 0) if total_edps > 0 else 0,
        'margen_por_edp': round(margen_bruto / total_edps, 0) if total_edps > 0 else 0
    }

# 6. Métricas de calidad
def calcular_metricas_calidad(df_periodo, df_log):
    """Calcula métricas de calidad del proceso"""
    total_edps = len(df_periodo)
    reprocesos = df_periodo[df_periodo['Estado Detallado'] == 're-trabajo solicitado']
    
    # Cálculo de reprocesos
    reprocesos_promedio = 0
    reprocesos_p95 = 0
    
    if not df_log.empty and 'N° EDP' in df_log.columns:
        reprocesos_por_edp = df_log.groupby('N° EDP').size()
        reprocesos_promedio = round(reprocesos_por_edp.mean(), 1) if len(reprocesos_por_edp) > 0 else 0
        reprocesos_p95 = round(np.percentile(reprocesos_por_edp, 95), 1) if len(reprocesos_por_edp) > 0 else 0
    else:
        reprocesos_conteo = df_periodo.groupby('N° EDP')['Estado Detallado'].apply(
            lambda x: (x == 're-trabajo solicitado').sum())
        if len(reprocesos_conteo) > 0:
            reprocesos_promedio = round(reprocesos_conteo.mean(), 1)
            reprocesos_p95 = round(np.percentile(reprocesos_conteo, 95), 1)
    
    # Conformidades
    conformidades_ok = len(df_periodo[df_periodo['Conformidad Enviada'] == 'Sí'])
    tasa_conformidad = round((conformidades_ok / total_edps) * 100, 1) if total_edps > 0 else 0
    
    # Índice de calidad
    indice_calidad = round(100 - (len(reprocesos) / total_edps * 100) if total_edps > 0 else 100, 1)
    
    # Alertas críticas
    alertas_criticas = len(df_periodo[(df_periodo['Estado Detallado'] == 're-trabajo solicitado') | 
                                     (df_periodo['Días Espera'] > 45)])
    
    return {
        'reprocesos_promedio': reprocesos_promedio,
        'reprocesos_p95': reprocesos_p95,
        'retrabajos_reducidos': round((1 - (len(reprocesos) / total_edps if total_edps > 0 else 0)) * 100, 1),
        'tasa_conformidad': tasa_conformidad,
        'indice_calidad': indice_calidad,
        'alertas_criticas': alertas_criticas
    }

# 7. Métricas estratégicas
def calcular_metricas_estrategicas(df_periodo):
    """Calcula métricas estratégicas y de tiempo"""
    estados_completados = ['pagado', 'validado', 'pagado ', 'validado ']
    df_completados = df_periodo[df_periodo['Estado'].str.strip().isin(estados_completados)]
    total_edps = len(df_periodo)
    reprocesos = df_periodo[df_periodo['Estado Detallado'] == 're-trabajo solicitado']
    
    # Meta de tiempo cumplida
    edps_rapidos = len(df_completados[df_completados['Días Espera'] <= 30])
    meta_cumplida = round((edps_rapidos / len(df_completados)) * 100, 1) if len(df_completados) > 0 else 0
    
    # Eficiencia global
    pct_avance = round((len(df_completados) / total_edps) * 100, 1) if total_edps > 0 else 0
    eficiencia_global = round(pct_avance * (1 - len(reprocesos) / total_edps if total_edps > 0 else 0), 1)
    
    # Métricas de tiempo (simuladas)
    tiempo_medio_ciclo = 45
    tiempo_medio_ciclo_pct = 75
    meta_tiempo_ciclo = 30
    benchmark_tiempo_ciclo = 35
    
    # Tiempos por etapa
    tiempo_emision = 8
    tiempo_gestion = 12
    tiempo_conformidad = 15
    tiempo_pago = 10
    
    # Porcentajes para visualización
    etapa_emision_pct = int(tiempo_emision / tiempo_medio_ciclo * 100)
    etapa_gestion_pct = int(tiempo_gestion / tiempo_medio_ciclo * 100)
    etapa_conformidad_pct = int(tiempo_conformidad / tiempo_medio_ciclo * 100)
    etapa_pago_pct = int(tiempo_pago / tiempo_medio_ciclo * 100)
    
    return {
        'meta_cumplida': meta_cumplida,
        'eficiencia_global': eficiencia_global,
        'mejora_eficiencia': 5.3,
        'tiempo_medio_ciclo': tiempo_medio_ciclo,
        'tiempo_medio_ciclo_pct': tiempo_medio_ciclo_pct,
        'meta_tiempo_ciclo': meta_tiempo_ciclo,
        'benchmark_tiempo_ciclo': benchmark_tiempo_ciclo,
        'tiempo_emision': tiempo_emision,
        'tiempo_gestion': tiempo_gestion,
        'tiempo_conformidad': tiempo_conformidad,
        'tiempo_pago': tiempo_pago,
        'etapa_emision_pct': etapa_emision_pct,
        'etapa_gestion_pct': etapa_gestion_pct,
        'etapa_conformidad_pct': etapa_conformidad_pct,
        'etapa_pago_pct': etapa_pago_pct,
        'oportunidad_mejora': "Reducir tiempo de conformidad con cliente (15 días vs. benchmark 7 días)",
        'pct_avance': pct_avance
    }

# 8. Análisis por cliente
def calcular_analisis_clientes(df_periodo):
    """Calcula análisis de concentración y riesgo por cliente"""
    clientes = df_periodo['Cliente'].unique()
    ingresos_por_cliente = {
        cliente: round(df_periodo[df_periodo['Cliente'] == cliente]['Monto Aprobado'].sum() / 1_000_000, 1)
        for cliente in clientes
    }
    
    if ingresos_por_cliente and len(ingresos_por_cliente) > 0:
        sorted_clients = sorted(ingresos_por_cliente.items(), key=lambda x: x[1], reverse=True)
        total_ingresos = sum(ingresos_por_cliente.values())
        
        # Concentración de clientes
        top_clients_count = min(3, len(sorted_clients))
        top_clients_revenue = sum(client[1] for client in sorted_clients[:top_clients_count])
        concentracion_clientes = round((top_clients_revenue / total_ingresos * 100), 1) if total_ingresos > 0 else 0
        
        # Cliente principal
        cliente_principal = sorted_clients[0][0] if sorted_clients else "N/A"
        pct_ingresos_principal = round((sorted_clients[0][1] / total_ingresos * 100), 1) if total_ingresos > 0 and sorted_clients else 0
    else:
        concentracion_clientes = 0
        cliente_principal = "N/A"
        pct_ingresos_principal = 0
    
    return {
        'concentracion_clientes': concentracion_clientes,
        'cliente_principal': cliente_principal,
        'pct_ingresos_principal': pct_ingresos_principal,
        'riesgo_pago_principal': 65,
        'tendencia_pago_principal': 'deterioro'
    }

# 9. Análisis por gestor
def calcular_analisis_gestores(df_periodo, metricas_rentabilidad):
    """Calcula análisis de eficiencia y rentabilidad por gestor"""
    gestores = df_periodo['Jefe de Proyecto'].unique()
    
    # Eficiencia por gestor
    eficiencia_gestores = {}
    rentabilidad_por_gestor = {}
    
    for gestor in gestores:
        df_gestor = df_periodo[df_periodo['Jefe de Proyecto'] == gestor]
        if len(df_gestor) > 0:
            # Eficiencia
            completados_gestor = df_gestor['Estado'].str.strip().isin(['validado', 'pagado']).sum()
            eficiencia_gestores[gestor] = round((completados_gestor / len(df_gestor)) * 100, 1)
            
            # Rentabilidad individual
            ingresos_gestor = df_gestor[df_gestor['Estado'].str.strip().isin(['pagado','validado'])]['Monto Aprobado'].sum()
            tiempo_gestor = df_gestor['Días Espera'].mean() if 'Días Espera' in df_gestor.columns else 45
            factor_gestor = max(tiempo_gestor / 30, 1.0) if tiempo_gestor > 0 else 1.0
            
            # Costos proporcionales
            costo_gestor = ingresos_gestor * (0.35 * factor_gestor + 0.15 + 0.08)
            margen_gestor = ingresos_gestor - costo_gestor
            rentabilidad_gestor = (margen_gestor / ingresos_gestor * 100) if ingresos_gestor > 0 else 0
            
            rentabilidad_por_gestor[gestor] = {
                'margen_porcentaje': round(rentabilidad_gestor, 1),
                'margen_absoluto': round(margen_gestor / 1_000_000, 2),
                'eficiencia_tiempo': round(30 / tiempo_gestor if tiempo_gestor > 0 else 0, 2)
            }
    
    return {
        'eficiencia_gestores': eficiencia_gestores,
        'rentabilidad_por_gestor': rentabilidad_por_gestor
    }

# 10. Combinar KPIs
def combinar_kpis(metricas_financieras, metricas_operativas, metricas_rentabilidad, 
                  metricas_calidad, metricas_estrategicas, analisis_clientes, analisis_gestores):
    """Combina todas las métricas en un solo diccionario"""
    
    # Métricas simuladas adicionales
    metricas_adicionales = {
        'tendencia_pendiente': 8.5,
        'nps_score': 75,
        'satisfaccion_cliente': 87,
        'roi_promedio': 32,
        'utilizacion_recursos': 87,
        'backlog_valor': round(metricas_financieras['monto_pendiente'] / 1_000_000, 1),
        'concentracion_atraso': round((metricas_financieras['monto_pendiente_critico'] / metricas_financieras['monto_pendiente']) * 100, 1) if metricas_financieras['monto_pendiente'] > 0 else 0
    }
    
    # Convertir montos a millones para presentación
    kpis_finales = {
        # Financieros
        'ingresos_totales': round(metricas_financieras['monto_cobrado'] / 1_000_000, 1),
        'crecimiento_ingresos': round((metricas_financieras['monto_cobrado'] / metricas_financieras['monto_emitido'] - 0.8) * 100, 1) if metricas_financieras['monto_emitido'] > 0 else 0,
        'monto_pendiente': round(metricas_financieras['monto_pendiente'] / 1_000_000, 1),
        'monto_pendiente_critico': round(metricas_financieras['monto_pendiente_critico'] / 1_000_000, 1),
        'costo_financiero': round(metricas_financieras['costo_financiero'] / 1_000_000, 1),
        'dso': metricas_financieras['dso'],
        'pct_cobrado': metricas_financieras['pct_cobrado'],
        'meta_ingresos': metricas_financieras['meta_ingresos'],
        'vs_meta_ingresos': metricas_financieras['vs_meta_ingresos'],
        'pct_meta_ingresos': metricas_financieras['pct_meta_ingresos'],
    }
    
    # Combinar todos los diccionarios
    kpis_finales.update(metricas_operativas)
    kpis_finales.update(metricas_rentabilidad)
    kpis_finales.update(metricas_calidad)
    kpis_finales.update(metricas_estrategicas)
    kpis_finales.update(analisis_clientes)
    kpis_finales.update(analisis_gestores)
    kpis_finales.update(metricas_adicionales)
    
    return kpis_finales

# 11. KPIs vacíos (cuando no hay datos) - ACTUALIZAR PARA INCLUIR TODOS LOS CAMPOS
def obtener_kpis_vacios():
    """Retorna KPIs con valores por defecto cuando no hay datos"""
    return {
        # Financieros básicos
        'ingresos_totales': 0,
        'crecimiento_ingresos': 0,
        'monto_pendiente': 0,
        'monto_pendiente_critico': 0,
        'costo_financiero': 0,
        'dso': 0,
        'pct_cobrado': 0,
        'meta_ingresos': 0,
        'vs_meta_ingresos': 0,  # CAMPO FALTANTE
        'pct_meta_ingresos': 0,
        
        # Rentabilidad
        'rentabilidad_general': 0,
        'tendencia_rentabilidad': 0,
        'meta_rentabilidad': 35.0,
        'vs_meta_rentabilidad': -35.0,
        'pct_meta_rentabilidad': 0,
        'costos_totales': 0,
        'costo_personal': 0,
        'costo_overhead': 0,
        'costo_tecnologia': 0,
        'costo_financiero_extra': 0,
        'margen_bruto_absoluto': 0,
        'roi_calculado': 0,
        'ebitda': 0,
        'ebitda_porcentaje': 0,
        'factor_tiempo_costo': 1.0,
        'benchmark_industria': 30.0,
        'posicion_vs_benchmark': -30.0,
        'tiempo_medio_real': 45,
        'costo_por_edp': 0,
        'margen_por_edp': 0,
        
        # Operativos
        'bucket_0_15': 0,
        'bucket_16_30': 0,
        'bucket_31_60': 0,
        'bucket_60_plus': 0,
        'pct_30d': 0,
        'pct_60d': 0,
        'pct_90d': 0,
        'pct_mas90d': 0,
        'total_edps': 0,
        'pct_avance': 0,
        'backlog_edp': 0,
        'q_proyectos_criticos': 0,
        'valor_proyectos_criticos': 0,
        'proyectos_on_time': 0,
        'proyectos_retrasados': 0,
        'proyectos_criticos': 0,
        
        # Calidad
        'reprocesos_promedio': 0,
        'reprocesos_p95': 0,
        'retrabajos_reducidos': 100,
        'tasa_conformidad': 0,
        'indice_calidad': 100,
        'alertas_criticas': 0,
        
        # Estratégicos
        'meta_cumplida': 0,
        'eficiencia_global': 0,
        'mejora_eficiencia': 0,
        'tiempo_medio_ciclo': 45,
        'tiempo_medio_ciclo_pct': 75,
        'meta_tiempo_ciclo': 30,
        'benchmark_tiempo_ciclo': 35,
        'tiempo_emision': 8,
        'tiempo_gestion': 12,
        'tiempo_conformidad': 15,
        'tiempo_pago': 10,
        'etapa_emision_pct': 18,
        'etapa_gestion_pct': 27,
        'etapa_conformidad_pct': 33,
        'etapa_pago_pct': 22,
        'oportunidad_mejora': "No hay datos suficientes para análisis",
        
        # Clientes
        'concentracion_clientes': 0,
        'cliente_principal': "N/A",
        'pct_ingresos_principal': 0,
        'riesgo_pago_principal': 50,
        'tendencia_pago_principal': 'estable',
        
        # Gestores
        'eficiencia_gestores': {},
        'rentabilidad_por_gestor': {},
        
        # Adicionales
        'tendencia_pendiente': 0,
        'nps_score': 75,
        'satisfaccion_cliente': 75,
        'roi_promedio': 0,
        'utilizacion_recursos': 75,
        'backlog_valor': 0,
        'concentracion_atraso': 0
    }
@manager_bp.route('/api/critical_projects')
#@login_required
def critical_projects():
    """API para obtener proyectos críticos con EDP pendientes"""
    df_edp = read_sheet("edp!A1:V")
   
    # Preparar datos
   
    df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
    df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce')
    
    
    # Filtrar proyectos críticos (> 30 días de espera)
    df_criticos = df_edp[(df_edp['Días Espera'] >= 30) & 
                        (~df_edp['Estado'].str.strip().isin(['pagado', 'validado']))].copy()
    
    print(f'Número de proyectos críticos encontrados: {len(df_criticos)}')
    
    # Agrupar por proyecto y cliente
    proyectos_criticos = []
    for (proyecto, cliente), grupo in df_criticos.groupby(['Proyecto', 'Cliente']):
        # Saltar si no hay datos válidos
        if pd.isnull(proyecto) or pd.isnull(cliente):
            continue
            
        jefe_proyecto = grupo['Jefe de Proyecto'].iloc[0] if not grupo['Jefe de Proyecto'].empty else "Sin asignar"
        valor_total = grupo['Monto Aprobado'].sum() / 1_000_000  # Convertir a millones
        max_delay = grupo['Días Espera'].max()
        
        # Obtener EDPs relacionados
        edps_relacionados = []
        for _, row in grupo.iterrows():
            if pd.isnull(row['N° EDP']):
                continue
                
            # Determinar estado basado en días de retraso
            estado = 'Crítico' if row['Días Espera'] > 30 else 'Riesgo' if row['Días Espera'] > 15 else 'Pendiente'
            
            fecha_emisión = row['Fecha Emisión'].strftime('%d/%m/%Y') if not pd.isnull(row['Fecha Emisión']) else "N/A"
            
            edps_relacionados.append({
                'id': row['N° EDP'],
                'date': fecha_emisión,
                'amount': round(row['Monto Aprobado'] / 1_000_000, 2),  # Convertir a millones
                'days': int(row['Días Espera']),
                'status': estado
            })
        
        if edps_relacionados:  # Solo agregar si tiene EDPs relacionados
            proyectos_criticos.append({
                'name': proyecto,
                'client': cliente,
                'value': round(valor_total, 2),
                'delay': int(max_delay),
                'manager': jefe_proyecto,
                'edps': edps_relacionados
            })
    # Ordenar por valor total descendente
    proyectos_criticos = sorted(proyectos_criticos, key=lambda x: x['value'], reverse=True)
    
    # Calcular valor total en riesgo
    total_value = sum(p['value'] for p in proyectos_criticos)
    
    return jsonify({
        'projects': proyectos_criticos,
        'total_value': round(total_value, 2),
        'count': len(proyectos_criticos)
    })
    
def generar_cash_forecast(df_edp):
    """Generate cash forecast data for the dashboard template"""
    # Similar to the cash_forecast API endpoint but returning a dict instead of JSON
    hoy = datetime.now()
    df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
    df_edp['Fecha Estimada de Pago'] = pd.to_datetime(df_edp['Fecha Estimada de Pago'], errors='coerce')
    df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce')
    
    # Filter only pending EDPs
    df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])].copy()
    
    # Define forecast periods
    hoy_30d = hoy + timedelta(days=30)
    hoy_60d = hoy + timedelta(days=60)
    hoy_90d = hoy + timedelta(days=90)
    
    # Calculate totals for each period
    total_30d = round(df_pendientes[df_pendientes['Fecha Estimada de Pago'] <= hoy_30d]['Monto Aprobado'].sum() / 1_000_000, 1)
    total_60d = round(df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_30d) & 
                                  (df_pendientes['Fecha Estimada de Pago'] <= hoy_60d)]['Monto Aprobado'].sum() / 1_000_000, 1)
    total_90d = round(df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_60d) & 
                                  (df_pendientes['Fecha Estimada de Pago'] <= hoy_90d)]['Monto Aprobado'].sum() / 1_000_000, 1)
    
    # Calculate probability-weighted totals
    prob_30d = round(total_30d * 0.9, 1)  # 90% probability for 30d
    prob_60d = round(total_60d * 0.7, 1)  # 70% probability for 60d
    prob_90d = round(total_90d * 0.5, 1)  # 50% probability for 90d
    total_ponderado = round(prob_30d + prob_60d + prob_90d, 1)
    
    return {
        'total_30d': total_30d,
        'total_60d': total_60d,
        'total_90d': total_90d,
        'prob_30d': prob_30d,
        'prob_60d': prob_60d,
        'prob_90d': prob_90d,
        'total_ponderado': total_ponderado
    }
# Actualizar la función principal para incluir todas las nuevas funciones
def obtener_datos_charts_ejecutivos(df_edp, df_log, periodo='all_dates', departamento='todos', cliente='todos', estado='todos'):
    """Obtiene datos para los gráficos del dashboard ejecutivo basados en datos reales"""
    
    try:
        # Validar entrada
        if df_edp.empty:
            print("⚠️ DataFrame vacío, retornando datos por defecto")
      
        
        print(f"📊 Procesando {len(df_edp)} registros para charts")
        
        # Preparación de datos
        hoy = datetime.now()
        df_edp = df_edp.copy()
        
        # Asegurar conversiones de tipos
        df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
        df_edp['Fecha Estimada de Pago'] = pd.to_datetime(df_edp['Fecha Estimada de Pago'], errors='coerce')
        df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce').fillna(0)
        df_edp['Monto Propuesto'] = pd.to_numeric(df_edp['Monto Propuesto'], errors='coerce').fillna(0)
        
        # Calcular días de espera si no existe
        if 'Días Espera' not in df_edp.columns:
            df_edp['Días Espera'] = (hoy - df_edp['Fecha Emisión']).dt.days
        
        # Filtrar por período
        if periodo == 'mes':
            inicio_periodo = hoy - timedelta(days=30)
        elif periodo == 'trimestre':
            inicio_periodo = hoy - timedelta(days=90)
        elif periodo == 'año':
            inicio_periodo = hoy - timedelta(days=365)
        else:
            inicio_periodo = datetime(2000, 1, 1)
        
        df_periodo = df_edp[df_edp['Fecha Emisión'] >= inicio_periodo].copy()
        
        # Aplicar filtros adicionales
        if departamento != 'todos' and 'Jefe de Proyecto' in df_periodo.columns:
            df_periodo = df_periodo[df_periodo['Jefe de Proyecto'] == departamento]
        
        if cliente != 'todos' and 'Cliente' in df_periodo.columns:
            df_periodo = df_periodo[df_periodo['Cliente'] == cliente]
        
        if estado != 'todos' and 'Estado' in df_periodo.columns:
            df_periodo = df_periodo[df_periodo['Estado'].str.strip() == estado]
        
        print(f"📊 Datos filtrados: {len(df_periodo)} registros")
        
        # Construir todos los datasets de charts
        result = {
            'cash_in_forecast': build_cash_forecast_data(df_periodo, hoy),
            'tendencia_financiera': build_financial_trend_data(df_edp),  # Usar df_edp completo para tendencia
            'rentabilidad_departamentos': build_department_profitability_data(df_periodo),
            'presupuesto_categorias': build_client_distribution_data(df_periodo),
            'estado_proyectos': build_project_status_data(df_periodo),
            'aging_buckets': build_aging_buckets_data(df_periodo),
            'concentracion_clientes': build_client_concentration_data(df_periodo)
        }
        
        # Agregar métricas adicionales opcionales
        result['forecast_breakdown'] = build_financial_forecast_breakdown(df_periodo)
        result['efficiency_metrics'] = build_efficiency_metrics(df_periodo)
        
        print("✅ Datos de charts generados exitosamente")
        return result
        
    except Exception as e:
        print(f"❌ Error en obtener_datos_charts_ejecutivos: {e}")
        import traceback
        traceback.print_exc()
        return print(f"❌ Error en obtener_datos_charts_ejecutivos: {e}")

        # 2. Tendencia financiera por mes
def obtener_alertas_criticas(df_edp):
    """Obtiene alertas que requieren atención ejecutiva basadas en datos reales"""
    hoy = datetime.now()
    df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
    df_edp['Días Espera'] = (hoy - df_edp['Fecha Emisión']).dt.days
    df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce')
    
    alertas = []
    
    # 1. Proyectos de alto valor con retraso
    df_alto_valor = df_edp[(df_edp['Monto Aprobado'] > 100000000) & 
                           (df_edp['Días Espera'] > 30) & 
                           (df_edp['Estado'] != 'pagado')]
    
    for _, row in df_alto_valor.iterrows():
        alertas.append({
            'titulo': f'Proyecto {row["Proyecto"]} en riesgo',
            'descripcion': f'Cliente {row["Cliente"]}, monto {round(row["Monto Aprobado"]/1000000, 1)}M',
            'impacto': 'alto',
            'accion': 'Revisión urgente',
            'fecha': hoy.strftime('%Y-%m-%d')
        })
    
    # 2. Retrabajos solicitados
    df_retrabajos = df_edp[df_edp['Estado Detallado'] == 're-trabajo solicitado']
    
    for _, row in df_retrabajos.iterrows():
        alertas.append({
            'titulo': f'Retrabajo en {row["Proyecto"]}',
            'descripcion': f'Cliente {row["Cliente"]}, {row.get("Observaciones", "Sin detalles")}',
            'impacto': 'medio',
            'accion': 'Analizar causa raíz',
            'fecha': hoy.strftime('%Y-%m-%d')
        })
    
    # 3. Concentración de problemas por gestor
    gestores_problemas = {}
    for gestor in df_edp['Jefe de Proyecto'].unique():
        df_gestor = df_edp[df_edp['Jefe de Proyecto'] == gestor]
        problemas = len(df_gestor[(df_gestor['Estado Detallado'] == 're-trabajo solicitado') | 
                                (df_gestor['Días Espera'] > 45)])
        if problemas >= 2:  # Umbral para alerta
            gestores_problemas[gestor] = problemas
    
    for gestor, problemas in gestores_problemas.items():
        alertas.append({
            'titulo': f'Alta tasa de problemas',
            'descripcion': f'{problemas} casos con {gestor}',
            'impacto': 'medio',
            'accion': 'Reunión de seguimiento',
            'fecha': hoy.strftime('%Y-%m-%d')
        })
    
    # Limitar a máximo 10 alertas
    return alertas[:10]



@manager_bp.route('/api/cash_forecast')
#@login_required
def cash_forecast():
    """API para proyección de flujo de caja basada en datos reales de EDPs pendientes"""
    df_edp = read_sheet("edp!A1:V")
    
    # Preparar datos
    hoy = datetime.now()
    df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
    df_edp['Fecha Estimada de Pago'] = pd.to_datetime(df_edp['Fecha Estimada de Pago'], errors='coerce')
    df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce')
    df_edp['Días Espera'] = (hoy - df_edp['Fecha Emisión']).dt.days
    
    # Filtrar solo EDPs pendientes (no pagados ni validados)
    df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])].copy()
    
    # Definir periodos de proyección
    hoy_30d = hoy + timedelta(days=30)
    hoy_60d = hoy + timedelta(days=60)
    hoy_90d = hoy + timedelta(days=90)
    
    # Asignar probabilidad de cobro basada en estado y días de espera
    def asignar_probabilidad(row):
        estado = row['Estado'].strip() if isinstance(row['Estado'], str) else ''
        dias = row['Días Espera']
        cliente = row['Cliente'] if isinstance(row['Cliente'], str) else ''
        
        # Alta probabilidad: EDPs en estado enviado con menos de 15 días o clientes con buen historial
        if estado == 'enviado' and dias < 15:
            return 'alta_prob'
        # Probabilidad media: EDPs en revisión o enviados con tiempo moderado
        elif estado == 'enviado' and dias < 30:
            return 'media_prob'
        elif estado == 'revisión':
            return 'media_prob'
        # Clientes específicos con buen historial
        elif cliente in ['Codelco', 'Enel'] and dias < 40:
            return 'media_prob'
        # Baja probabilidad para el resto
        else:
            return 'baja_prob'
    
    df_pendientes['probabilidad'] = df_pendientes.apply(asignar_probabilidad, axis=1)
    
    # Calcular montos por periodo y probabilidad
    periodos = {
        '30d': df_pendientes[df_pendientes['Fecha Estimada de Pago'] <= hoy_30d],
        '60d': df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_30d) & 
                           (df_pendientes['Fecha Estimada de Pago'] <= hoy_60d)],
        '90d': df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_60d) & 
                           (df_pendientes['Fecha Estimada de Pago'] <= hoy_90d)]
    }
    
    forecast = {}
    
    for periodo, df in periodos.items():
        # Agrupar por probabilidad y sumar montos
        if not df.empty:
            por_prob = df.groupby('probabilidad')['Monto Aprobado'].sum().to_dict()
            forecast[periodo] = {
                'alta_prob': int(por_prob.get('alta_prob', 0)),
                'media_prob': int(por_prob.get('media_prob', 0)),
                'baja_prob': int(por_prob.get('baja_prob', 0))
            }
        else:
            forecast[periodo] = {
                'alta_prob': 0,
                'media_prob': 0,
                'baja_prob': 0
            }
    
    # Añadir totales y métricas adicionales
    totales = {
        'total_30d': sum(forecast['30d'].values()),
        'total_60d': sum(forecast['60d'].values()),
        'total_90d': sum(forecast['90d'].values()),
        'total_ponderado': (
            sum(forecast['30d'].values()) * 0.9 +
            sum(forecast['60d'].values()) * 0.7 +
            sum(forecast['90d'].values()) * 0.5
        )
    }
    
    # Medir la distribución de riesgo (% del flujo de alta probabilidad)
    if sum(totales.values()) > 0:
        distribucion_riesgo = {
            'bajo_riesgo': (
                forecast['30d']['alta_prob'] + 
                forecast['60d']['alta_prob'] + 
                forecast['90d']['alta_prob']
            ) / (totales['total_30d'] + totales['total_60d'] + totales['total_90d']) * 100 
            if (totales['total_30d'] + totales['total_60d'] + totales['total_90d']) > 0 else 0
        }
    else:
        distribucion_riesgo = {'bajo_riesgo': 0}
    
    return jsonify({
        'proyeccion': forecast,
        'totales': totales,
        'metricas': distribucion_riesgo
    })
    

def build_cash_forecast_data(df_periodo, hoy):
    """Construir datos de cash forecast"""
    try:
        hoy_30d = hoy + timedelta(days=30)
        hoy_60d = hoy + timedelta(days=60)
        hoy_90d = hoy + timedelta(days=90)
        
        df_pendientes = df_periodo[~df_periodo['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        # Función para calcular probabilidad
        def calcular_probabilidad(row):
            estado = str(row.get('Estado', '')).strip()
            dias = row.get('Días Espera', 0)
            
            if estado == 'enviado' and dias < 15:
                return 'alta'
            elif estado == 'enviado' and dias < 30:
                return 'media'
            elif estado == 'revisión':
                return 'media'
            else:
                return 'baja'
        
        df_pendientes['probabilidad'] = df_pendientes.apply(calcular_probabilidad, axis=1)
        
        # Calcular montos por período
        cash_30d = df_pendientes[df_pendientes['Fecha Estimada de Pago'] <= hoy_30d].groupby('probabilidad')['Monto Aprobado'].sum() / 1_000_000
        cash_60d = df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_30d) & 
                               (df_pendientes['Fecha Estimada de Pago'] <= hoy_60d)].groupby('probabilidad')['Monto Aprobado'].sum() / 1_000_000
        cash_90d = df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_60d) & 
                               (df_pendientes['Fecha Estimada de Pago'] <= hoy_90d)].groupby('probabilidad')['Monto Aprobado'].sum() / 1_000_000
        
        return {
            'labels': ['30 días', '60 días', '90 días'],
            'datasets': [
                {
                    'label': 'Altamente probable',
                    'data': [
                        float(cash_30d.get('alta', 0)),
                        float(cash_60d.get('alta', 0)),
                        float(cash_90d.get('alta', 0))
                    ],
                    'backgroundColor': 'rgba(16, 185, 129, 0.7)'
                },
                {
                    'label': 'Probable',
                    'data': [
                        float(cash_30d.get('media', 0)),
                        float(cash_60d.get('media', 0)),
                        float(cash_90d.get('media', 0))
                    ],
                    'backgroundColor': 'rgba(59, 130, 246, 0.7)'
                },
                {
                    'label': 'Posible',
                    'data': [
                        float(cash_30d.get('baja', 0)),
                        float(cash_60d.get('baja', 0)),
                        float(cash_90d.get('baja', 0))
                    ],
                    'backgroundColor': 'rgba(249, 115, 22, 0.7)'
                }
            ]
        }
    except Exception as e:
        print(f"Error en build_cash_forecast_data: {e}")
      
    
    

def build_financial_trend_data(df_edp):
    """Construir datos de tendencia financiera por mes"""
    try:
        # Agrupar datos por mes
        df_edp['Mes'] = df_edp['Fecha Emisión'].dt.strftime('%Y-%m')
        ingresos_mensuales = df_edp.groupby('Mes')['Monto Aprobado'].sum() / 1_000_000
        
        # Obtener últimos 6 meses disponibles
        if len(ingresos_mensuales) == 0:
            # Usar datos por defecto si no hay datos
            return print(f"⚠️ No hay datos de ingresos mensuales, retornando datos por defecto")
        
        ultimos_meses = sorted(ingresos_mensuales.index)[-6:]
        valores_ultimos_meses = [float(ingresos_mensuales.get(mes, 0)) for mes in ultimos_meses]
        
        # Calcular proyección simple (5% de crecimiento mensual)
        ultimo_valor = valores_ultimos_meses[-1] if valores_ultimos_meses else 0
        proyeccion = [ultimo_valor * (1 + i*0.05) for i in range(1, 4)]
        
        # Preparar datasets
        valores_con_proyeccion = valores_ultimos_meses + [None, None, None]
        proyeccion_completa = [None] * len(valores_ultimos_meses) + proyeccion
        
        # Convertir mes-año a solo mes para labels
        labels_meses = []
        for mes in ultimos_meses:
            try:
                fecha = datetime.strptime(mes, '%Y-%m')
                labels_meses.append(fecha.strftime('%b'))
            except:
                labels_meses.append(mes.split('-')[1])
        
        return {
            'labels': labels_meses + ['P1', 'P2', 'P3'],
            'datasets': [
                {
                    'label': 'Real',
                    'data': valores_con_proyeccion,
                    'borderColor': '#3B82F6',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'tension': 0.3,
                    'fill': False
                },
                {
                    'label': 'Proyección',
                    'data': proyeccion_completa,
                    'borderColor': '#10B981',
                    'borderDash': [5, 5],
                    'backgroundColor': 'transparent',
                    'tension': 0.3,
                    'fill': False
                }
            ]
        }
    except Exception as e:
        print(f"Error en build_financial_trend_data: {e}")
        return print(f"⚠️ Error al construir datos de tendencia financiera: {e}") 

def build_department_profitability_data(df_periodo):
    """Construir datos de rentabilidad por departamento/gestor"""
    try:
        if df_periodo.empty or 'Jefe de Proyecto' not in df_periodo.columns:
            return print(f"⚠️ DataFrame vacío o sin columna 'Jefe de Proyecto', retornando datos por defecto") 
        
        # Calcular margen por gestor
        margen_por_gestor = {}
        gestores_unicos = df_periodo['Jefe de Proyecto'].dropna().unique()
        
        for gestor in gestores_unicos:
            if pd.isna(gestor) or str(gestor).strip() == '':
                continue
                
            df_gestor = df_periodo[df_periodo['Jefe de Proyecto'] == gestor]
            
            if len(df_gestor) > 0:
                # Calcular tasa de éxito (proyectos completados vs total)
                completados = df_gestor['Estado'].str.strip().isin(['pagado', 'validado']).sum()
                tasa_exito = completados / len(df_gestor) if len(df_gestor) > 0 else 0
                
                # Calcular ratio de aprobación (monto aprobado vs propuesto)
                monto_aprobado_total = df_gestor['Monto Aprobado'].sum()
                monto_propuesto_total = df_gestor['Monto Propuesto'].sum()
                ratio_aprobacion = monto_aprobado_total / monto_propuesto_total if monto_propuesto_total > 0 else 0
                
                # Calcular eficiencia temporal (penalizar por días de espera)
                dias_promedio = df_gestor['Días Espera'].mean() if 'Días Espera' in df_gestor.columns else 30
                factor_tiempo = max(0.5, 30 / max(dias_promedio, 15))  # Penalizar si excede 30 días
                
                # Margen estimado combinando factores
                margen_estimado = (tasa_exito * ratio_aprobacion * factor_tiempo) * 100
                margen_por_gestor[str(gestor)] = round(margen_estimado, 1)
        
        if not margen_por_gestor:
            return print(f"⚠️ No se encontraron gestores con datos válidos, retornando datos por defecto")
        
        # Limitar a los top 8 gestores para visualización
        top_gestores = dict(sorted(margen_por_gestor.items(), key=lambda x: x[1], reverse=True)[:8])
        
        # Colores dinámicos basados en rendimiento
        colores = []
        for margen in top_gestores.values():
            if margen >= 40:
                colores.append('rgba(16, 185, 129, 0.7)')  # Verde para alto rendimiento
            elif margen >= 30:
                colores.append('rgba(59, 130, 246, 0.7)')   # Azul para buen rendimiento
            elif margen >= 20:
                colores.append('rgba(249, 115, 22, 0.7)')   # Naranja para rendimiento medio
            else:
                colores.append('rgba(239, 68, 68, 0.7)')    # Rojo para bajo rendimiento
        
        return {
            'labels': list(top_gestores.keys()),
            'datasets': [
                {
                    'label': 'Margen Estimado (%)',
                    'data': list(top_gestores.values()),
                    'backgroundColor': colores
                }
            ]
        }
    except Exception as e:
        print(f"Error en build_department_profitability_data: {e}")
        return print(f"⚠️ Error al construir datos de rentabilidad por departamento: {e}") 

def build_client_distribution_data(df_periodo):
    """Construir datos de distribución por cliente"""
    try:
        if df_periodo.empty or 'Cliente' not in df_periodo.columns:
            return print(f"⚠️ DataFrame vacío o sin columna 'Cliente', retornando datos por defecto")
        # Calcular distribución por cliente
        monto_total = df_periodo['Monto Aprobado'].sum()
        if monto_total == 0:
            return print(f"⚠️ Monto total es 0, retornando datos por defecto")
        distribucion_clientes = df_periodo.groupby('Cliente')['Monto Aprobado'].sum()
        distribucion_porcentaje = (distribucion_clientes / monto_total * 100).round(1)
        
        # Ordenar por valor descendente y tomar top 10
        distribucion_porcentaje = distribucion_porcentaje.sort_values(ascending=False).head(10)
        
        # Si hay muchos clientes pequeños, agrupar en "Otros"
        if len(distribucion_porcentaje) > 8:
            top_7 = distribucion_porcentaje.head(7)
            otros = distribucion_porcentaje.tail(-7).sum()
            
            labels = top_7.index.tolist() + ['Otros']
            values = top_7.values.tolist() + [otros]
        else:
            labels = distribucion_porcentaje.index.tolist()
            values = distribucion_porcentaje.values.tolist()
        
        # Colores diferenciados
        colores_base = [
            'rgba(59, 130, 246, 0.7)',   # Azul
            'rgba(16, 185, 129, 0.7)',   # Verde
            'rgba(249, 115, 22, 0.7)',   # Naranja
            'rgba(139, 92, 246, 0.7)',   # Púrpura
            'rgba(244, 63, 94, 0.7)',    # Rosa
            'rgba(6, 182, 212, 0.7)',    # Cyan
            'rgba(251, 191, 36, 0.7)',   # Amarillo
            'rgba(107, 114, 128, 0.7)'   # Gris para "Otros"
        ]
        
        colores = colores_base[:len(labels)]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Distribución (%)',
                    'data': [float(val) for val in values],
                    'backgroundColor': colores
                }
            ]
        }
    except Exception as e:
        print(f"Error en build_client_distribution_data: {e}")
        return print(f"⚠️ Error al construir datos de distribución por cliente: {e}")

def build_project_status_data(df_periodo):
    """Construir datos de estado de proyectos"""
    try:
        if df_periodo.empty or 'Días Espera' not in df_periodo.columns:
            return print(f"⚠️ DataFrame vacío o sin columna 'Días Espera', retornando datos por defecto")
        
        # Calcular estados basados en días de espera y estado actual
        estados = df_periodo['Estado'].str.strip()
        dias_espera = df_periodo['Días Espera']
        
        # Definir categorías
        completados = len(df_periodo[estados.isin(['pagado', 'validado'])])
        a_tiempo = len(df_periodo[(dias_espera <= 30) & (~estados.isin(['pagado', 'validado']))])
        en_riesgo = len(df_periodo[(dias_espera > 30) & (dias_espera <= 45) & (~estados.isin(['pagado', 'validado']))])
        retrasados = len(df_periodo[(dias_espera > 45) & (~estados.isin(['pagado', 'validado']))])
        
        # Validar que tengamos datos
        total = completados + a_tiempo + en_riesgo + retrasados
        if total == 0:
            return print(f"⚠️ No hay proyectos para mostrar, retornando datos por defecto")
        
        return {
            'labels': ['A tiempo', 'En riesgo', 'Retrasados', 'Completados'],
            'datasets': [
                {
                    'data': [a_tiempo, en_riesgo, retrasados, completados],
                    'backgroundColor': [
                        '#10B981',  # Verde - A tiempo
                        '#FBBF24',  # Ámbar - En riesgo
                        '#F87171',  # Rojo - Retrasados
                        '#60A5FA'   # Azul - Completados
                    ],
                    'borderWidth': 0,
                    'hoverOffset': 4
                }
            ]
        }
    except Exception as e:
        print(f"Error en build_project_status_data: {e}")
        return print(f"⚠️ Error al construir datos de estado de proyectos: {e}")

def build_aging_buckets_data(df_periodo):
    """Construir datos de aging buckets"""
    try:
        if df_periodo.empty or 'Días Espera' not in df_periodo.columns:
            return print(f"⚠️ DataFrame vacío o sin columna 'Días Espera', retornando datos por defecto")
        
        # Filtrar solo proyectos pendientes
        df_pendientes = df_periodo[~df_periodo['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        if df_pendientes.empty:
            return {
                'labels': ['0-15 días', '16-30 días', '31-60 días', '> 60 días'],
                'datasets': [
                    {
                        'label': 'Cantidad de EDPs',
                        'data': [0, 0, 0, 0],
                        'backgroundColor': [
                            'rgba(16, 185, 129, 0.7)',
                            'rgba(249, 115, 22, 0.7)',
                            'rgba(244, 63, 94, 0.7)',
                            'rgba(244, 63, 94, 0.9)'
                        ]
                    }
                ]
            }
        
        # Calcular buckets de aging
        bucket_0_15 = len(df_pendientes[df_pendientes['Días Espera'] <= 15])
        bucket_16_30 = len(df_pendientes[(df_pendientes['Días Espera'] > 15) & (df_pendientes['Días Espera'] <= 30)])
        bucket_31_60 = len(df_pendientes[(df_pendientes['Días Espera'] > 30) & (df_pendientes['Días Espera'] <= 60)])
        bucket_60_plus = len(df_pendientes[df_pendientes['Días Espera'] > 60])
        
        return {
            'labels': ['0-15 días', '16-30 días', '31-60 días', '> 60 días'],
            'datasets': [
                {
                    'label': 'Cantidad de EDPs',
                    'data': [bucket_0_15, bucket_16_30, bucket_31_60, bucket_60_plus],
                    'backgroundColor': [
                        'rgba(16, 185, 129, 0.7)',  # Verde - Buenos
                        'rgba(249, 115, 22, 0.7)',  # Naranja - Atentos
                        'rgba(244, 63, 94, 0.7)',   # Rojo - Problema
                        'rgba(244, 63, 94, 0.9)'    # Rojo oscuro - Crítico
                    ],
                    'borderColor': [
                        '#10B981',
                        '#F97316',
                        '#F43F5E',
                        '#E11D48'
                    ],
                    'borderWidth': 1
                }
            ]
        }
    except Exception as e:
        print(f"Error en build_aging_buckets_data: {e}")
        return print(f"⚠️ Error al construir datos de aging buckets: {e}")

def build_client_concentration_data(df_periodo):
    """Construir datos de concentración por cliente (Pareto)"""
    try:
        if df_periodo.empty or 'Cliente' not in df_periodo.columns:
            return print(f"⚠️ DataFrame vacío o sin columna 'Cliente', retornando datos por defecto")
        
        # Agrupar por cliente y calcular montos
        clientes_montos = df_periodo.groupby('Cliente')['Monto Aprobado'].sum() / 1_000_000
        
        if clientes_montos.empty or clientes_montos.sum() == 0:
            return print(f"⚠️ No hay montos por cliente, retornando datos por defecto")
        
        # Ordenar por monto descendente
        clientes_montos = clientes_montos.sort_values(ascending=False)
        
        # Tomar top 10 para visualización
        if len(clientes_montos) > 10:
            top_9 = clientes_montos.head(9)
            otros = clientes_montos.tail(-9).sum()
            if otros > 0:
                clientes_montos = pd.concat([top_9, pd.Series([otros], index=['Otros'])])
            else:
                clientes_montos = top_9
        
        total = clientes_montos.sum()
        
        # Calcular porcentaje acumulado
        acumulado = 0
        porcentajes_acumulados = []
        for monto in clientes_montos:
            acumulado += monto
            porcentaje_acum = round(acumulado / total * 100 if total > 0 else 0, 1)
            porcentajes_acumulados.append(porcentaje_acum)
        
        return {
            'labels': clientes_montos.index.tolist(),
            'datasets': [
                {
                    'type': 'bar',
                    'label': 'Monto pendiente',
                    'data': [float(val) for val in clientes_montos.values],
                    'backgroundColor': 'rgba(59, 130, 246, 0.7)',
                    'borderColor': '#3B82F6',
                    'borderWidth': 1,
                    'order': 2
                },
                {
                    'type': 'line',
                    'label': 'Acumulado (%)',
                    'data': porcentajes_acumulados,
                    'borderColor': '#F59E0B',
                    'backgroundColor': 'transparent',
                    'borderWidth': 2,
                    'pointRadius': 4,
                    'pointBackgroundColor': '#F59E0B',
                    'fill': False,
                    'order': 1,
                    'yAxisID': 'percentage'
                }
            ]
        }
    except Exception as e:
        print(f"Error en build_client_concentration_data: {e}")
        return print(f"⚠️ Error al construir datos de concentración por cliente: {e}")

def build_financial_forecast_breakdown(df_periodo):
    """Construir breakdown detallado del forecast financiero"""
    try:
        if df_periodo.empty:
            return {}
        
        
        # Proyecciones por sector/tipo de cliente
        sectores_forecast = {}
        if 'Cliente' in df_periodo.columns:
            # Clasificar clientes por sector (simplificado)
            sector_mapping = {
                'Codelco': 'Minería',
                'Enel': 'Energía',
                'Banco': 'Financiero',
                'Gobierno': 'Público'
            }
            
            for cliente in df_periodo['Cliente'].unique():
                if pd.isna(cliente):
                    continue
                    
                # Determinar sector
                sector = 'Otros'
                for key, value in sector_mapping.items():
                    if key.lower() in str(cliente).lower():
                        sector = value
                        break
                
                df_cliente = df_periodo[df_periodo['Cliente'] == cliente]
                df_pendiente = df_cliente[~df_cliente['Estado'].str.strip().isin(['pagado', 'validado'])]
                
                if not df_pendiente.empty:
                    monto_pendiente = df_pendiente['Monto Aprobado'].sum() / 1_000_000
                    dias_promedio = df_pendiente['Días Espera'].mean() if 'Días Espera' in df_pendiente.columns else 30
                    
                    # Calcular probabilidad de cobro basada en historial
                    if dias_promedio <= 30:
                        probabilidad = 0.85
                    elif dias_promedio <= 45:
                        probabilidad = 0.65
                    else:
                        probabilidad = 0.40
                    
                    if sector not in sectores_forecast:
                        sectores_forecast[sector] = {
                            'monto_total': 0,
                            'monto_probable': 0,
                            'clientes': 0
                        }
                    
                    sectores_forecast[sector]['monto_total'] += monto_pendiente
                    sectores_forecast[sector]['monto_probable'] += monto_pendiente * probabilidad
                    sectores_forecast[sector]['clientes'] += 1
        
        return sectores_forecast
    except Exception as e:
        print(f"Error en build_financial_forecast_breakdown: {e}")
        return {}

def build_efficiency_metrics(df_periodo):
    """Construir métricas de eficiencia del proceso"""
    try:
        if df_periodo.empty:
            return {}
        
        # Métricas de tiempo por etapa del proceso
        etapas_tiempo = {
            'emision_a_envio': [],
            'envio_a_revision': [],
            'revision_a_conformidad': [],
            'conformidad_a_pago': []
        }
        
        # Simular tiempos por etapa basados en estado actual
        for _, row in df_periodo.iterrows():
            estado = str(row.get('Estado', '')).strip()
            dias_total = row.get('Días Espera', 0)
            
            if estado == 'enviado':
                # Distribución estimada del tiempo
                etapas_tiempo['emision_a_envio'].append(min(dias_total * 0.2, 5))
                etapas_tiempo['envio_a_revision'].append(dias_total * 0.8)
            elif estado == 'revisión':
                etapas_tiempo['emision_a_envio'].append(min(dias_total * 0.15, 5))
                etapas_tiempo['envio_a_revision'].append(dias_total * 0.3)
                etapas_tiempo['revision_a_conformidad'].append(dias_total * 0.55)
            elif estado in ['validado', 'pagado']:
                etapas_tiempo['emision_a_envio'].append(min(dias_total * 0.12, 5))
                etapas_tiempo['envio_a_revision'].append(dias_total * 0.25)
                etapas_tiempo['revision_a_conformidad'].append(dias_total * 0.4)
                etapas_tiempo['conformidad_a_pago'].append(dias_total * 0.23)
        
        # Calcular promedios
        metricas_eficiencia = {}
        for etapa, tiempos in etapas_tiempo.items():
            if tiempos:
                metricas_eficiencia[etapa] = {
                    'promedio': round(np.mean(tiempos), 1),
                    'mediana': round(np.median(tiempos), 1),
                    'p95': round(np.percentile(tiempos, 95), 1) if len(tiempos) > 1 else round(np.mean(tiempos), 1)
                }
            else:
                metricas_eficiencia[etapa] = {
                    'promedio': 0,
                    'mediana': 0,
                    'p95': 0
                }
        
        return metricas_eficiencia
    except Exception as e:
        print(f"Error en build_efficiency_metrics: {e}")
        return {}



# Función auxiliar para limpiar todos los datos antes de enviar
def clean_charts_data_for_json(charts_data):
    """Limpia y prepara los datos de charts para serialización JSON"""
    try:
        cleaned_data = {}
        
        for chart_name, chart_data in charts_data.items():
            if isinstance(chart_data, dict):
                cleaned_chart = {}
                
                # Limpiar labels
                if 'labels' in chart_data:
                    cleaned_chart['labels'] = [
                        str(label) if label is not None else ''
                        for label in chart_data['labels']
                    ]
                
                # Limpiar datasets
                if 'datasets' in chart_data:
                    cleaned_datasets = []
                    for dataset in chart_data['datasets']:
                        cleaned_dataset = {}
                        
                        for key, value in dataset.items():
                            if key == 'data':
                                # Limpiar datos numéricos
                                cleaned_data_values = []
                                for val in value:
                                    if val is None:
                                        cleaned_data_values.append(None)
                                    elif pd.isna(val):
                                        cleaned_data_values.append(None)
                                    elif np.isnan(val) if isinstance(val, (int, float)) else False:
                                        cleaned_data_values.append(None)
                                    else:
                                        try:
                                            cleaned_data_values.append(float(val))
                                        except (ValueError, TypeError):
                                            cleaned_data_values.append(0)
                                cleaned_dataset[key] = cleaned_data_values
                            else:
                                cleaned_dataset[key] = value
                        
                        cleaned_datasets.append(cleaned_dataset)
                    
                    cleaned_chart['datasets'] = cleaned_datasets
                
                # Copiar otras propiedades
                for key, value in chart_data.items():
                    if key not in ['labels', 'datasets']:
                        cleaned_chart[key] = value
                
                cleaned_data[chart_name] = cleaned_chart
            else:
                cleaned_data[chart_name] = chart_data
        
        return cleaned_data
    except Exception as e:
        print(f"Error en clean_charts_data_for_json: {e}")
        return charts_data



# ===== AGREGAR FUNCIÓN DE DEBUG =====
@manager_bp.route('/debug/charts')
def debug_charts():
    """Endpoint de debugging para charts"""
    try:
        df_edp = read_sheet("edp!A1:V")
        
        if df_edp.empty:
            return jsonify({"error": "No data available"})
        
        # Preparar datos básicos
        hoy = datetime.now()
        df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
        df_edp['Días Espera'] = (hoy - df_edp['Fecha Emisión']).dt.days
        df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce').fillna(0)
        
        print(f"🔍 Debug: {len(df_edp)} registros procesados")
        print(f"🔍 Debug: Columnas disponibles: {list(df_edp.columns)}")
        
        # Obtener charts data
        charts_data = obtener_datos_charts_ejecutivos(df_edp, pd.DataFrame(), None, 'todos', 'todos', 'todos')
        
        # Limpiar datos
        charts_data_clean = clean_charts_data_for_json(charts_data)
        
        # Crear muestra de datos para debugging
        sample_data = {}
        for key, data in charts_data_clean.items():
            if isinstance(data, dict):
                sample_data[key] = {
                    "labels": data.get("labels", [])[:3] if isinstance(data.get("labels"), list) else [],
                    "datasets_count": len(data.get("datasets", [])) if isinstance(data.get("datasets"), list) else 0,
                    "first_dataset_sample": {
                        "label": data.get("datasets", [{}])[0].get("label", "") if data.get("datasets") else "",
                        "data_points": len(data.get("datasets", [{}])[0].get("data", [])) if data.get("datasets") else 0
                    } if data.get("datasets") else {}
                }
            else:
                sample_data[key] = f"Type: {type(data)}"
        
        return jsonify({
            "status": "success",
            "records_processed": len(df_edp),
            "columns_available": list(df_edp.columns),
            "data_keys": list(charts_data_clean.keys()),
            "sample_data": sample_data,
            "json_serializable": True
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        })