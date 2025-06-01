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
    """Dashboard principal ejecutivo con KPIs financieros y operativos"""
    # Obtener parámetros de filtro (período, cliente, etc.)
    periodo = request.args.get('periodo', 'all_dates')
    departamento = request.args.get('departamento', 'todos')  # Corregido - usar 'departamento' para coincidir con el form
    cliente_seleccionado = request.args.get('cliente', 'todos')
    estado = request.args.get('estado', 'todos')  # Obtener estado de la URL

    # Cargar datos
    df_edp = read_sheet("edp!A1:V")
    df_log = read_sheet("log!A1:G")
    
    # Calcular KPIs
    kpis = calcular_kpis_ejecutivos(df_edp, df_log, periodo, departamento, cliente_seleccionado, estado)
    
    # Obtener datos para gráficos
    charts_data = obtener_datos_charts_ejecutivos(df_edp, df_log, periodo, departamento, cliente_seleccionado, estado)
    charts_data_clean = clean_nan_values(charts_data)

    charts_data_json = json.dumps(charts_data_clean, default=lambda o: None)

    # Obtener alertas críticas
    alertas = obtener_alertas_criticas(df_edp)
    
    # Datos de predicciones para la sección de tendencias
    predicciones = {
        'crecimiento_proyectado': 8.5,
        'ingresos_proyectados': 3.2,
        'riesgos_identificados': 3,
        'oportunidades_identificadas': 5
    }
    cash_forecast = generar_cash_forecast(df_edp)
        
    df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['validado', 'pagado'])].copy()
    df_pendientes['Monto Aprobado'] = pd.to_numeric(df_pendientes['Monto Aprobado'], errors='coerce')
    
    
    df_pendientes['Próxima Fecha'] = pd.to_datetime(df_pendientes['Fecha Estimada de Pago'], errors='coerce')
    df_pendientes['Días Próx Fecha'] = (df_pendientes['Próxima Fecha'] - datetime.now()).dt.days
    
    top10 = df_pendientes.sort_values('Monto Aprobado', ascending=False).head(10)
    top_edps = []
    for _, row in top10.iterrows():
        top_edps.append({
            'id': row.get('ID', ''),
            'edp': row.get('N° EDP', ''),
            'proyecto': row.get('Proyecto', ''),
            'cliente': row.get('Cliente', ''),
            'monto': float(row.get('Monto Aprobado', 0)) / 1_000_000,  # Convert to millions
            'dias': int(row.get('Días Espera', 0)),
            'encargado': row.get('Jefe de Proyecto', ''),
            'prox_fecha': row['Próxima Fecha'].strftime('%d/%m/%Y') if pd.notna(row['Próxima Fecha']) else '-',
            'dias_prox_fecha': int(row.get('Días Próx Fecha', 0)) if pd.notna(row.get('Días Próx Fecha')) else 0
        })
        
    total_edps = len(df_pendientes)
    jefes_proyecto = df_edp['Jefe de Proyecto'].unique()
    clientes_unicos = df_edp['Cliente'].unique()
    
    
    
    gestores = [{'nombre': jefe} for jefe in jefes_proyecto if jefe and str(jefe).strip()]
    clientes = [{'nombre': cliente} for cliente in clientes_unicos if cliente and str(cliente).strip()]
   

    # Renderizar template
    return render_template('manager/dashboard.html',
                          kpis=kpis,
                          charts_data=charts_data_json,
                          alertas=alertas,
                          predicciones=predicciones,
                          periodo=periodo,
                          departamento=departamento,
                          cash_forecast=cash_forecast,
                          top_edps=top_edps,
                        total_edps=total_edps,
                          gestores=gestores,
                          clientes=clientes,
                          cliente_seleccionado=cliente_seleccionado,)
    

def calcular_kpis_ejecutivos(df_edp, df_log, periodo='all_dates', departamento='todos', cliente='todos', estado='todos'):
    """Calcula los KPIs principales para el dashboard ejecutivo"""
    # Filtrar por período si es necesario
    hoy = datetime.now()
    
    if periodo == 'mes':
        inicio_periodo = hoy - timedelta(days=30)
    elif periodo == 'trimestre':
        inicio_periodo = hoy - timedelta(days=90)
    elif periodo == 'año':
        inicio_periodo = hoy - timedelta(days=365)
    elif periodo == 'all_dates':
        inicio_periodo = datetime(2000, 1, 1)
    else:
        inicio_periodo = datetime(2000, 1, 1)  # Default a todo
    
    # Convertir fechas a datetime para filtrado
    df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
    df_edp['Fecha Envío al Cliente'] = pd.to_datetime(df_edp['Fecha Envío al Cliente'], errors='coerce')
    df_edp['Fecha Estimada de Pago'] = pd.to_datetime(df_edp['Fecha Estimada de Pago'], errors='coerce')
    df_edp['Fecha Conformidad'] = pd.to_datetime(df_edp['Fecha Conformidad'], errors='coerce')
    
    # Calcular días de espera (diferencia entre hoy y fecha de emisión para EDPs no pagados)
    df_edp['Días Espera'] = (hoy - df_edp['Fecha Emisión']).dt.days
    
    # Para EDPs pagados o validados, calcular días reales de espera
    mask_completados = df_edp['Estado'].isin(['pagado', 'validado', 'pagado ', 'validado '])
    df_edp.loc[mask_completados & df_edp['Fecha Conformidad'].notna(), 'Días Espera'] = (
        df_edp['Fecha Conformidad'] - df_edp['Fecha Emisión']).dt.days
    
    # Filtrar por período
    df_periodo = df_edp[df_edp['Fecha Emisión'] >= inicio_periodo].copy()
    
    # Filtrar por departamento si es necesario (usando Jefe de Proyecto como departamento)
    if departamento != 'todos' and departamento in df_periodo['Jefe de Proyecto'].unique():
        df_periodo = df_periodo[df_periodo['Jefe de Proyecto'] == departamento]
    
        # Filtrar por cliente
    if cliente != 'todos' and cliente in df_periodo['Cliente'].unique():
        df_periodo = df_periodo[df_periodo['Cliente'] == cliente]
    
    # Filtrar por estado
    if estado != 'todos':
        df_periodo = df_periodo[df_periodo['Estado'].str.strip() == estado]
    
    # 1. FINANCIEROS - FLUJO DE CAJA
    
    # Convertir montos a numérico
    df_periodo['Monto Propuesto'] = pd.to_numeric(df_periodo['Monto Propuesto'], errors='coerce')
    df_periodo['Monto Aprobado'] = pd.to_numeric(df_periodo['Monto Aprobado'], errors='coerce')
    
    # Calcular montos pendientes y críticos
    estados_pendientes = ['enviado', 'revisión', 'enviado ']
    estados_completados = ['pagado', 'validado', 'pagado ', 'validado ']
    
    df_pendientes = df_periodo[df_periodo['Estado'].str.strip().isin(estados_pendientes)]
    monto_pendiente = df_pendientes['Monto Aprobado'].sum()
    
    # Pendientes críticos (> 30 días)
    df_criticos = df_pendientes[df_pendientes['Días Espera'] > 30]
    monto_pendiente_critico = df_criticos['Monto Aprobado'].sum()
    
    # Costo financiero de la demora
    costo_financiero = sum(row['Monto Aprobado'] * row['Días Espera'] * TASA_DIARIA 
                           for _, row in df_criticos.iterrows())
    
    # DSO (Days Sales Outstanding) - para EDPs pagados o validados
    df_completados = df_periodo[df_periodo['Estado'].str.strip().isin(estados_completados)]
    dias_cobro_total = df_completados['Días Espera'].sum()
    edps_cobrados = len(df_completados)
    
    dso = round(dias_cobro_total / edps_cobrados, 1) if edps_cobrados > 0 else 0
    
    # Porcentaje cobrado vs emitido
    monto_emitido = df_periodo['Monto Propuesto'].sum()
    monto_cobrado = df_periodo[df_periodo['Estado'].str.strip().isin(['pagado','validado'])]['Monto Aprobado'].sum()
    pct_cobrado = round((monto_cobrado / monto_emitido) * 100, 1) if monto_emitido > 0 else 0
    
    # 2. OPERATIVAS - PIPELINE EDP
    
    # Total EDPs pendientes
    backlog_edp = len(df_periodo[~df_periodo['Estado'].str.strip().isin(['validado', 'pagado'])])
    
    # Aging buckets
    bucket_0_15 = len(df_pendientes[df_pendientes['Días Espera'] <= 15])
    bucket_16_30 = len(df_pendientes[(df_pendientes['Días Espera'] > 15) & 
                                    (df_pendientes['Días Espera'] <= 30)])
    bucket_31_60 = len(df_pendientes[(df_pendientes['Días Espera'] > 30) & 
                                    (df_pendientes['Días Espera'] <= 60)])
    bucket_60_plus = len(df_pendientes[df_pendientes['Días Espera'] > 60])
    
    # Avance general
    total_edps = len(df_periodo)
    finalizados = len(df_periodo[df_periodo['Estado'].str.strip().isin(['validado', 'pagado'])])
    pct_avance = round((finalizados / total_edps) * 100, 1) if total_edps > 0 else 0
    
    # 3. CALIDAD DEL PROCESO
    
    # Reprocesos (usando el estado detallado o motivos)
    reprocesos = df_periodo[df_periodo['Estado Detallado'] == 're-trabajo solicitado']
    reprocesos_promedio = 0
    reprocesos_p95 = 0
    
    if not df_log.empty and 'N° EDP' in df_log.columns:
        # Si hay datos de log disponibles
        reprocesos_por_edp = df_log.groupby('N° EDP').size()
        reprocesos_promedio = round(reprocesos_por_edp.mean(), 1) if len(reprocesos_por_edp) > 0 else 0
        reprocesos_p95 = round(np.percentile(reprocesos_por_edp, 95), 1) if len(reprocesos_por_edp) > 0 else 0
    else:
        # Estimate based on Estado Detallado
        reprocesos_conteo = df_periodo.groupby('N° EDP')['Estado Detallado'].apply(
            lambda x: (x == 're-trabajo solicitado').sum())
        if len(reprocesos_conteo) > 0:
            reprocesos_promedio = round(reprocesos_conteo.mean(), 1)
            reprocesos_p95 = round(np.percentile(reprocesos_conteo, 95), 1)
    
    # Tasa de conformidades
    conformidades_ok = len(df_periodo[df_periodo['Conformidad Enviada'] == 'Sí'])
    tasa_conformidad = round((conformidades_ok / total_edps) * 100, 1) if total_edps > 0 else 0
    
    # 4. ESTRATÉGICOS
    
    # Meta "< 30 días" cumplida
    edps_rapidos = len(df_completados[df_completados['Días Espera'] <= 30])
    meta_cumplida = round((edps_rapidos / len(df_completados)) * 100, 1) if len(df_completados) > 0 else 0
    
    # 5. SALUD EN TIEMPO REAL
    
    # Alertas críticas (retrabajo o estado crítico)
    alertas_criticas = len(df_periodo[(df_periodo['Estado Detallado'] == 're-trabajo solicitado') | 
                                     (df_periodo['Días Espera'] > 45)])
    
    

    
    # KPIs por cliente
    clientes = df_periodo['Cliente'].unique()
    ingresos_por_cliente = {
        cliente: round(df_periodo[df_periodo['Cliente'] == cliente]['Monto Aprobado'].sum() / 1_000_000, 1)
        for cliente in clientes
    }
    
    
    if ingresos_por_cliente and len(ingresos_por_cliente) > 0:
        sorted_clients = sorted(ingresos_por_cliente.items(), key=lambda x: x[1], reverse=True)
        total_ingresos = sum(ingresos_por_cliente.values())
        
        # Calculate concentration percentage (top 3 clients or fewer if less available)
        top_clients_count = min(3, len(sorted_clients))
        top_clients_revenue = sum(client[1] for client in sorted_clients[:top_clients_count])
        concentracion_clientes = round((top_clients_revenue / total_ingresos * 100), 1) if total_ingresos > 0 else 0
        
        # Store the main client name and percentage
        cliente_principal = sorted_clients[0][0] if sorted_clients else "N/A"
        pct_ingresos_principal = round((sorted_clients[0][1] / total_ingresos * 100), 1) if total_ingresos > 0 and sorted_clients else 0
    else:
        concentracion_clientes = 0
        cliente_principal = "N/A"
        pct_ingresos_principal = 0
        
        
        
    # Eficiencia por gestor de proyecto
    gestores = df_periodo['Jefe de Proyecto'].unique()
    
    eficiencia_gestores = {}
    for gestor in gestores:
        df_gestor = df_periodo[df_periodo['Jefe de Proyecto'] == gestor]
        if len(df_gestor) > 0:
            completados_gestor = df_gestor['Estado'].str.strip().isin(['validado', 'pagado']).sum()
            eficiencia_gestores[gestor] = round((completados_gestor / len(df_gestor)) * 100, 1)
        # Meta de ingresos (simulated goal - can be replaced with actual business targets)
    meta_ingresos = round(monto_emitido * 0.85 / 1_000_000, 1)  # 85% of issued amount
    
    # % sobre/bajo meta
    vs_meta_ingresos = round((monto_cobrado / (meta_ingresos * 1_000_000) - 1) * 100, 1) if meta_ingresos > 0 else 0
    
    # % de meta alcanzado para barra de progreso
    pct_meta_ingresos = round((monto_cobrado / (meta_ingresos * 1_000_000)) * 100, 1) if meta_ingresos > 0 else 0
    pct_meta_ingresos = min(pct_meta_ingresos, 100)  # Cap at 100%
    
    # Concentración de atraso (% del monto pendiente en proyectos críticos)
    df_criticos = df_pendientes[df_pendientes['Días Espera'] > 60]
    proyectos_criticos = len(df_criticos)
    concentracion_atraso = round((df_criticos['Monto Aprobado'].sum() / monto_pendiente) * 100, 1) if monto_pendiente > 0 else 0
    
    # NPS Inventadas (por ahora)
    nps_score = 75  # Simulated NPS score
    satisfaccion_cliente = 87
    roi_promedio =32
    
    
    tendencia_pendiente = 8.5  # % change in pending amount vs last month (positive = worse)
    
    # Financial health metrics for client concentration and risk
    riesgo_pago_principal = 65  # risk percentage for main client
    tendencia_pago_principal = 'deterioro'  # could be 'mejora', 'estable', or 'deterioro'
    
    # Add new KPIs for operational efficiency
    tiempo_medio_ciclo = 45  # average days for complete cycle
    tiempo_medio_ciclo_pct = 75  # percentage of target (used for progress bar)
    meta_tiempo_ciclo = 30  # target days
    benchmark_tiempo_ciclo = 35  # industry benchmark
    
    # Times by stage (in days)
    tiempo_emision = 8
    tiempo_gestion = 12
    tiempo_conformidad = 15
    tiempo_pago = 10
    
    # Percentages for visualization
    etapa_emision_pct = int(tiempo_emision / tiempo_medio_ciclo * 100)
    etapa_gestion_pct = int(tiempo_gestion / tiempo_medio_ciclo * 100)
    etapa_conformidad_pct = int(tiempo_conformidad / tiempo_medio_ciclo * 100)
    etapa_pago_pct = int(tiempo_pago / tiempo_medio_ciclo * 100)
    
    # Improvement opportunity identification
    oportunidad_mejora = "Reducir tiempo de conformidad con cliente (15 días vs. benchmark 7 días)"
    
    # Calcular top 10 Edps pendientes

    # Retornar todos los KPIs calculados
    return {
        # Financieros
        'ingresos_totales': round(monto_cobrado / 1_000_000, 1),  # En millones
        'crecimiento_ingresos': round((monto_cobrado / monto_emitido - 0.8) * 100, 1) if monto_emitido > 0 else 0,  # Simulando YoY
        'monto_pendiente': round(monto_pendiente / 1_000_000, 1),  # En millones
        'monto_pendiente_critico': round(monto_pendiente_critico / 1_000_000, 1),  # En millones
        'costo_financiero': round(costo_financiero / 1_000_000, 1),  # En millones
        'dso': dso,
        'pct_cobrado': pct_cobrado,

        
        # Client concentration metrics
        'concentracion_clientes': concentracion_clientes,
        'cliente_principal': cliente_principal,
        'pct_ingresos_principal': pct_ingresos_principal,
        
        'meta_ingresos': meta_ingresos,
        'vs_meta_ingresos': vs_meta_ingresos, 
        'pct_meta_ingresos': pct_meta_ingresos,
        'proyectos_criticos': proyectos_criticos,
        'concentracion_atraso': concentracion_atraso,
        
        # Financial trends
        'tendencia_pendiente': tendencia_pendiente,
        'riesgo_pago_principal': riesgo_pago_principal,
        'tendencia_pago_principal': tendencia_pago_principal,
        
        # Operational efficiency metrics
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
        'oportunidad_mejora': oportunidad_mejora,
        
        
        # Customer satisfaction metrics
        'nps_score': nps_score,
        'satisfaccion_cliente': satisfaccion_cliente, 
        'roi_promedio': roi_promedio,
        # Operativos
        'proyectos_activos': backlog_edp,
        'proyectos_on_time': round((bucket_0_15 + bucket_16_30) / backlog_edp * 100 if backlog_edp > 0 else 0, 1),
        'proyectos_retrasados': round((bucket_31_60 + bucket_60_plus) / backlog_edp * 100 if backlog_edp > 0 else 0, 1),
        'proyectos_criticos': bucket_60_plus,
        'pct_avance': pct_avance,
        
        # Calidad
        'indice_calidad': round(100 - (len(reprocesos) / total_edps * 100) if total_edps > 0 else 100, 1),
        'reprocesos_promedio': reprocesos_promedio,
        'reprocesos_p95': reprocesos_p95,
        'retrabajos_reducidos': round((1 - (len(reprocesos) / total_edps if total_edps > 0 else 0)) * 100, 1),
        'tasa_conformidad': tasa_conformidad,
        
        # Estratégicos
        'meta_cumplida': meta_cumplida,
        'eficiencia_global': round(pct_avance * (1 - len(reprocesos) / total_edps if total_edps > 0 else 0), 1),
        'mejora_eficiencia': 5.3,  # Valores de tendencia requieren datos históricos
        
        # Salud en tiempo real
        'alertas_criticas': alertas_criticas,
        'satisfaccion_cliente': round(tasa_conformidad * 0.9, 1),  # Estimación basada en conformidades
        'roi_promedio': round((monto_cobrado / monto_emitido) * 100 - 75 if monto_emitido > 0 else 0, 1),  # Estimación
        'utilizacion_recursos': 87,  # Requiere datos adicionales
        'backlog_valor': round(monto_pendiente / 1_000_000, 1)  # En millones
        
        
        
    }
    
    
    
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
def obtener_datos_charts_ejecutivos(df_edp, df_log, periodo='all_dates', departamento='todos', cliente='todos', estado='todos'):
    """Obtiene datos para los gráficos del dashboard ejecutivo basados en datos reales"""
    # Preparación de datos
    hoy = datetime.now()
    df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
    df_edp['Fecha Estimada de Pago'] = pd.to_datetime(df_edp['Fecha Estimada de Pago'], errors='coerce')
    df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce')
    df_edp['Días Espera'] = (hoy - df_edp['Fecha Emisión']).dt.days
    
    # Filtrar por período
    if periodo == 'mes':
        inicio_periodo = hoy - timedelta(days=30)
    elif periodo == 'trimestre':
        inicio_periodo = hoy - timedelta(days=90)
    elif periodo == 'año':
        inicio_periodo = hoy - timedelta(days=365)
    elif periodo == 'all_dates':
        inicio_periodo = datetime(2000, 1, 1)
    else:
        inicio_periodo = datetime(2000, 1, 1)
    
    df_periodo = df_edp[df_edp['Fecha Emisión'] >= inicio_periodo].copy()
    
    # Filtrar por departamento/gestor si es necesario
    if departamento != 'todos':
        df_periodo = df_periodo[df_periodo['Jefe de Proyecto'] == departamento]
    
    if cliente != 'todos' and cliente in df_periodo['Cliente'].unique():
        df_periodo = df_periodo[df_periodo['Cliente'] == cliente]
    
    if estado != 'todos':
        df_periodo = df_periodo[df_periodo['Estado'].str.strip() == estado]
    
    
    # 1. Cash-In Forecast 30-60-90d
    # Proyección basada en fechas estimadas de pago
    hoy_30d = hoy + timedelta(days=30)
    hoy_60d = hoy + timedelta(days=60)
    hoy_90d = hoy + timedelta(days=90)
    
    # EDPs pendientes por fecha estimada de pago
    df_pendientes = df_periodo[~df_periodo['Estado'].str.strip().isin(['pagado', 'validado'])]
    
    # Calcular probabilidad basada en estado y días de espera
    def calcular_probabilidad(row):
        estado = row['Estado'].strip() if isinstance(row['Estado'], str) else ''
        dias = row['Días Espera']
        
        if estado == 'enviado' and dias < 15:
            return 'alta'
        elif estado == 'enviado' and dias < 30:
            return 'media'
        elif estado == 'revisión':
            return 'media'
        else:
            return 'baja'
    
    df_pendientes['probabilidad'] = df_pendientes.apply(calcular_probabilidad, axis=1)
    
    # Agrupar por período y probabilidad
    cash_30d = df_pendientes[df_pendientes['Fecha Estimada de Pago'] <= hoy_30d].groupby('probabilidad')['Monto Aprobado'].sum() / 1_000_000
    cash_60d = df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_30d) & 
                           (df_pendientes['Fecha Estimada de Pago'] <= hoy_60d)].groupby('probabilidad')['Monto Aprobado'].sum() / 1_000_000
    cash_90d = df_pendientes[(df_pendientes['Fecha Estimada de Pago'] > hoy_60d) & 
                           (df_pendientes['Fecha Estimada de Pago'] <= hoy_90d)].groupby('probabilidad')['Monto Aprobado'].sum() / 1_000_000
    
    cash_in_forecast = {
        'labels': ['30 días', '60 días', '90 días'],
        'datasets': [
            {
                'label': 'Altamente probable',
                'data': [float(cash_30d.get('alta', 0)), float(cash_60d.get('alta', 0)), float(cash_90d.get('alta', 0))],
                'backgroundColor': 'rgba(16, 185, 129, 0.7)'
            },
            {
                'label': 'Probable',
                'data': [float(cash_30d.get('media', 0)), float(cash_60d.get('media', 0)), float(cash_90d.get('media', 0))],
                'backgroundColor': 'rgba(59, 130, 246, 0.7)'
            },
            {
                'label': 'Posible',
                'data': [float(cash_30d.get('baja', 0)), float(cash_60d.get('baja', 0)), float(cash_90d.get('baja', 0))],
                'backgroundColor': 'rgba(249, 115, 22, 0.7)'
            }
        ]
    }
    
    
    # 2. Tendencia financiera por mes
    # Agrupar datos por mes
    df_edp['Mes'] = df_edp['Fecha Emisión'].dt.strftime('%Y-%m')
    ingresos_mensuales = df_edp.groupby('Mes')['Monto Aprobado'].sum() / 1_000_000
    
    # Obtener últimos 6 meses disponibles
    ultimos_meses = sorted(ingresos_mensuales.index)[-6:]
    valores_ultimos_meses = [ingresos_mensuales.get(mes, 0) for mes in ultimos_meses]
    
    # Calcular proyección simple
    proyeccion = [valores_ultimos_meses[-1] * (1 + i*0.05) for i in range(1, 4)]
    valores_con_proyeccion = valores_ultimos_meses + [None, None, None]
    proyeccion_completa = [None, None, None] + proyeccion
    
    tendencia_financiera = {
        'labels': [mes.split('-')[1] for mes in ultimos_meses] + ['P1', 'P2', 'P3'],
        'datasets': [
            {
                'label': 'Real',
                'data': valores_con_proyeccion,
                'borderColor': '#3B82F6',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)'
            },
            {
                'label': 'Proyección',
                'data': proyeccion_completa,
                'borderColor': '#10B981',
                'borderDash': [5, 5],
                'backgroundColor': 'transparent'
            }
        ]
    }
    
    # 3. Rentabilidad por gestor/departamento
    # Usar Jefe de Proyecto como departamento
    margen_por_gestor = {}
    for gestor in df_periodo['Jefe de Proyecto'].unique():
        df_gestor = df_periodo[df_periodo['Jefe de Proyecto'] == gestor]
        if len(df_gestor) > 0:
            # Calcular un "margen" estimado basado en la tasa de éxito y monto promedio
            completados = df_gestor['Estado'].str.strip().isin(['pagado', 'validado']).sum()
            tasa_exito = completados / len(df_gestor) if len(df_gestor) > 0 else 0
            monto_promedio = df_gestor['Monto Aprobado'].mean() / df_gestor['Monto Propuesto'].mean() if df_gestor['Monto Propuesto'].sum() > 0 else 0
            margen_por_gestor[gestor] = round(tasa_exito * monto_promedio * 100, 1)
    
    rentabilidad_departamentos = {
        'labels': list(margen_por_gestor.keys()),
        'datasets': [
            {
                'label': 'Margen (%)',
                'data': list(margen_por_gestor.values()),
                'backgroundColor': [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(249, 115, 22, 0.7)',
                    'rgba(139, 92, 246, 0.7)'
                ]
            }
        ]
    }
    
    # 4. Distribución por cliente
    distribucion_clientes = df_periodo.groupby('Cliente')['Monto Aprobado'].sum() / df_periodo['Monto Aprobado'].sum() * 100
    
    presupuesto_categorias = {
        'labels': distribucion_clientes.index.tolist(),
        'datasets': [
            {
                'label': 'Distribución (%)',
                'data': distribucion_clientes.values.tolist(),
                'backgroundColor': [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(249, 115, 22, 0.7)',
                    'rgba(139, 92, 246, 0.7)'
                ]
            }
        ]
    }
    
    # 5. Estado de proyectos
    estados = df_periodo['Estado'].str.strip()
    a_tiempo = len(df_periodo[df_periodo['Días Espera'] <= 30])
    en_riesgo = len(df_periodo[(df_periodo['Días Espera'] > 30) & (df_periodo['Días Espera'] <= 45)])
    retrasados = len(df_periodo[df_periodo['Días Espera'] > 45])
    completados = len(df_periodo[estados.isin(['pagado', 'validado'])])
    
    estado_proyectos = {
        'labels': ['A tiempo', 'En riesgo', 'Retrasados', 'Completados'],
        'datasets': [
            {
                'data': [a_tiempo, en_riesgo, retrasados, completados],
                'backgroundColor': [
                    '#10B981',  # verde
                    '#FBBF24',  # ámbar
                    '#F87171',  # rojo
                    '#60A5FA'   # azul
                ]
            }
        ]
    }
    
    # 6. Aging bucket distribution
    bucket_0_15 = len(df_periodo[df_periodo['Días Espera'] <= 15])
    bucket_16_30 = len(df_periodo[(df_periodo['Días Espera'] > 15) & (df_periodo['Días Espera'] <= 30)])
    bucket_31_60 = len(df_periodo[(df_periodo['Días Espera'] > 30) & (df_periodo['Días Espera'] <= 60)])
    bucket_60_plus = len(df_periodo[df_periodo['Días Espera'] > 60])
    
    aging_buckets = {
        'labels': ['0-15 días', '16-30 días', '31-60 días', '> 60 días'],
        'datasets': [
            {
                'label': 'Cantidad de EDPs',
                'data': [bucket_0_15, bucket_16_30, bucket_31_60, bucket_60_plus],
                'backgroundColor': [
                    'rgba(16, 185, 129, 0.7)',  # verde
                    'rgba(249, 115, 22, 0.7)',  # naranja 
                    'rgba(244, 63, 94, 0.7)',  # rojo
                    'rgba(244, 63, 94, 0.9)'   # rojo oscuro
                ],
                'borderColor': [
                    '#10B981',
                    '#F97316',
                    '#F43F5E',
                    '#E11D48'
                ]
            }
        ]
    }
    
    # 7. Concentración por cliente (Pareto)
    clientes_montos = df_periodo.groupby('Cliente')['Monto Aprobado'].sum() / 1_000_000
    clientes_montos = clientes_montos.sort_values(ascending=False)
    total = clientes_montos.sum()
 
    
    # Calcular porcentaje acumulado
    acumulado = 0
    porcentajes_acumulados = []
    for monto in clientes_montos:
        acumulado += monto
        porcentajes_acumulados.append(round(acumulado / total * 100 if total > 0 else 0, 1))
    
    concentracion_clientes = {
        'labels': clientes_montos.index.tolist(),
        'datasets': [
            {
                'type': 'bar',
                'label': 'Monto pendiente',
                'data': clientes_montos.values.tolist(),
                'backgroundColor': 'rgba(59, 130, 246, 0.7)',
                'order': 2
            },
            {
                'type': 'line',
                'label': 'Acumulado (%)',
                'data': porcentajes_acumulados,
                'borderColor': '#F59E0B',
                'borderWidth': 2,
                'fill': False,
                'order': 1
            }
        ]
    }
    
    return {
        'cash_in_forecast': cash_in_forecast,
        'tendencia_financiera': tendencia_financiera,
        'rentabilidad_departamentos': rentabilidad_departamentos,
        'presupuesto_categorias': presupuesto_categorias,
        'estado_proyectos': estado_proyectos,
        'aging_buckets': aging_buckets,
        'concentracion_clientes': concentracion_clientes
    }

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


#@login_required
def func_top_edps(df_edp):
    """API que retorna los top 10 EDPs por valor pendiente"""
    df_edp = read_sheet("edp!A1:V")
    
    # Filtrar sólo EDPs pendientes (no validados ni pagados)
    df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['validado', 'pagado'])].copy()
    
    # Convertir Monto Aprobado a numérico
    df_pendientes['Monto Aprobado'] = pd.to_numeric(df_pendientes['Monto Aprobado'], errors='coerce')
    
   
    # Ordenar y tomar top 10
    top10 = df_pendientes.sort_values('Monto Aprobado', ascending=False).head(10)
    # Convertir a lista de diccionarios para API
    result = []
    for _, row in top10.iterrows():
        result.append({
            'id': row.get('ID', ''),
            'edp': row.get('N° EDP', ''),
            'proyecto': row.get('Proyecto', ''),
            'cliente': row.get('Cliente', ''),
            'monto': float(row.get('Monto Aprobado', 0)),
            'dias': int(row.get('Días Espera', 0)),
            'encargado': row.get('Jefe de Proyecto', '')
        })
    
    return jsonify(result)

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