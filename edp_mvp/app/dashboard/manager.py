from flask import Blueprint, render_template, request, jsonify
import json
from flask_login import login_required
from ..utils.gsheet import read_sheet
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import traceback

# Constants
COSTO_CAPITAL_ANUAL = 0.12  # 12% anual
TASA_DIARIA = COSTO_CAPITAL_ANUAL / 360
META_DIAS_COBRO = 30  # Meta de días de cobro

manager_bp = Blueprint('manager_bp', __name__, url_prefix='/manager')

# ===== JSON ENCODER Y UTILIDADES =====
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
    """Recursively clean NaN values from data structures"""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, (float, np.float64, np.float32)):
        try:
            if np.isnan(obj):
                return None
        except:
            pass
    elif obj is np.nan:
        return None
    elif pd.isna(obj):
        return None
    elif isinstance(obj, pd.DataFrame):
        return None
    elif isinstance(obj, pd.Series):
        return None
    
    return obj

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

# ===== FUNCIÓN PRINCIPAL DEL DASHBOARD =====
@manager_bp.route('/dashboard')
#@login_required  
def dashboard():
    try:
        # ===== PASO 1: CREAR RELACIONES SIMPLIFICADAS =====
        datos_relacionados = crear_relaciones_datos_simplificado()
        
        if datos_relacionados is None:
            return render_template('manager/dashboard.html', 
                                 error="Error al cargar datos", 
                                 kpis=obtener_kpis_vacios(),
                                 charts_json="{}",
                                 charts={},
                                 cash_forecast={},
                                 alertas=[],
                                 fecha_inicio=None,
                                 fecha_fin=None,
                                 periodo_rapido=None,
                                 departamento='todos',
                                 cliente='todos',
                                 estado='todos',
                                 vista='general',
                                 monto_min=None,
                                 monto_max=None,
                                 dias_min=None,
                                 jefes_proyecto=[],
                                 clientes=[],
                                 rentabilidad_proyectos=pd.DataFrame(),
                                 rentabilidad_clientes=pd.DataFrame(),
                                 rentabilidad_gestores=pd.DataFrame())
        
        print(f"📊 Datos relacionados simplificados creados exitosamente")
        
        # ===== PASO 2: OBTENER PARÁMETROS DE FILTRO =====
        hoy = datetime.now()
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        periodo_rapido = request.args.get('periodo_rapido')
        departamento = request.args.get('departamento', 'todos')
        cliente = request.args.get('cliente', 'todos')
        estado = request.args.get('estado', 'todos')
        vista = request.args.get('vista', 'general')
        
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
        
        # ===== PASO 3: PREPARAR LISTAS PARA SELECTORES =====
        df_edp = datos_relacionados['df_edp']
        jefes_proyecto = sorted([j for j in df_edp['Jefe de Proyecto'].unique() if pd.notna(j) and str(j).strip()])
        clientes = sorted([c for c in df_edp['Cliente'].unique() if pd.notna(c) and str(c).strip()])
        
        # ===== PASO 4: CALCULAR KPIs SIMPLIFICADOS =====
        try:
            kpis = calcular_kpis_ejecutivos_simplificado(
                datos_relacionados, 
                fecha_inicio, 
                fecha_fin, 
                departamento, 
                cliente, 
                estado
            )
            print("✅ KPIs simplificados calculados exitosamente")
        except Exception as kpi_error:
            print(f"❌ Error calculando KPIs simplificados: {kpi_error}")
            kpis = obtener_kpis_vacios()
        
        try:
            kpis_anuales = calcular_kpis_anuales_reales(datos_relacionados)
            kpis.update(kpis_anuales)
            print("✅ KPIs anuales reales agregados exitosamente")
        except Exception as kpi_anual_error:
            print(f"❌ Error calculando KPIs anuales reales: {kpi_anual_error}")
            kpis_anuales_vacios = obtener_kpis_anuales_vacios()
            kpis.update(kpis_anuales_vacios)
        
        # ===== PASO 5: OBTENER DATOS DE CHARTS SIMPLIFICADOS =====
        try:
            charts_data = obtener_datos_charts_simplificado(
                datos_relacionados,
                departamento, 
                cliente, 
                estado
            )
            print("✅ Charts simplificados generados exitosamente")
        except Exception as chart_error:
            print(f"❌ Error generando charts simplificados: {chart_error}")
            charts_data = {}
        
        # ===== PASO 6: LIMPIAR Y SERIALIZAR =====
        try:
            charts_data_clean = clean_charts_data_for_json(charts_data)
            charts_json = json.dumps(charts_data_clean, cls=CustomJSONEncoder, ensure_ascii=False)
            json.loads(charts_json)  # Test de parsing
            print("✅ Charts JSON serializado y validado")
        except Exception as json_error:
            print(f"❌ Error serializando charts JSON: {json_error}")
            charts_data_clean = {}
            charts_json = "{}"
        
        # ===== PASO 7: DATOS ADICIONALES =====
        try:
            # Aplicar filtros al EDP para cash forecast
            df_filtrado = aplicar_filtros_basicos(df_edp, fecha_inicio, fecha_fin, departamento, cliente, estado)
            cash_forecast_data = generar_cash_forecast(df_filtrado)
            alertas = obtener_alertas_criticas(df_filtrado)
            print("✅ Datos adicionales generados")
        except Exception as extra_error:
            print(f"❌ Error generando datos adicionales: {extra_error}")
            cash_forecast_data = {}
            alertas = []
        
        # ===== PASO 8: RENDERIZAR TEMPLATE =====
        print("🎯 Renderizando template con enfoque simplificado...")
        
        return render_template('manager/dashboard.html', 
                             kpis=kpis,
                             charts=charts_data_clean,
                             charts_json=charts_json,
                             cash_forecast=cash_forecast_data,
                             alertas=alertas,
                             fecha_inicio=fecha_inicio,
                             fecha_fin=fecha_fin,
                             periodo_rapido=periodo_rapido,
                             departamento=departamento,
                             cliente=cliente,
                             estado=estado,
                             vista=vista,
                             monto_min=None,
                             monto_max=None,
                             dias_min=None,
                             jefes_proyecto=jefes_proyecto,
                             clientes=clientes,
                             rentabilidad_proyectos=pd.DataFrame(),
                             rentabilidad_clientes=pd.DataFrame(),
                             rentabilidad_gestores=pd.DataFrame(),
                             error=None)
    
    except Exception as e:
        print(f"❌ Error crítico en dashboard simplificado: {str(e)}")
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
                             clientes=[],
                             rentabilidad_proyectos=pd.DataFrame(),
                             rentabilidad_clientes=pd.DataFrame(),
                             rentabilidad_gestores=pd.DataFrame())

# ===== FUNCIONES DE DATOS SIMPLIFICADAS =====
def crear_relaciones_datos_simplificado():
    """Enfoque simplificado: leer cada hoja por separado y hacer relaciones mínimas"""
    try:
        # Leer todas las hojas por separado
        df_edp = read_sheet("edp!A1:V")
        df_projects = read_sheet("projects!A1:I") 
        df_costs = read_sheet("cost_header!A1:Q")
        df_log = read_sheet("log!A1:V")
        
        print(f"📊 Datos leídos independientemente:")
        print(f"   - EDP: {len(df_edp)} registros")
        print(f"   - Projects: {len(df_projects)} registros") 
        print(f"   - Costs: {len(df_costs)} registros")
        print(f"   - Log: {len(df_log)} registros")
        
        if df_edp.empty:
            print("⚠️ DataFrame EDP está vacío")
            return None
        
        # ===== PREPARAR DATOS BÁSICOS SIN MERGE =====
        hoy = datetime.now()
        
        # Preparar EDP
        df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
        df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce').fillna(0)
        df_edp['Monto Propuesto'] = pd.to_numeric(df_edp['Monto Propuesto'], errors='coerce').fillna(0)
        # print(f'PRoyectos en costos: {df_costs["project_id"].unique()}')
        
        # Asegurar que Días Espera sea numérico
        df_edp['Días Espera'] = pd.to_numeric(df_edp['Días Espera'], errors='coerce').fillna(0)
        
        print(f"✅ EDP preparado: {len(df_edp)} registros con Días Espera calculados")
        
        # ===== CREAR ÍNDICES PARA LOOKUPS RÁPIDOS =====
        
        # Índice de proyectos por ID
        projects_lookup = {}
        if not df_projects.empty and 'project_id' in df_projects.columns:
            df_projects['project_id'] = df_projects['project_id'].astype(str).str.strip()
            projects_lookup = df_projects.set_index('project_id').to_dict('index')
            print(f"✅ Índice de proyectos creado: {len(projects_lookup)} proyectos")
        
        # Índice de costos por proyecto
        costs_lookup = {}
        if not df_costs.empty and 'project_id' in df_costs.columns:
            df_costs['project_id'] = df_costs['project_id'].astype(str).str.strip()
            df_costs['importe_neto'] = pd.to_numeric(df_costs['importe_neto'], errors='coerce').fillna(0)
            
            # Filtrar costos válidos
            df_costs_valid = df_costs[
                (df_costs['project_id'] != 'nan') & 
                (df_costs['project_id'] != '') & 
                (df_costs['project_id'].notna())
            ]
            
            if not df_costs_valid.empty:
                costs_summary = df_costs_valid.groupby('project_id').agg({
                    'importe_neto': 'sum',
                    'cost_id': 'count',
                    'estado_costo': lambda x: (x == 'pagado').sum() if len(x) > 0 else 0,
                }).to_dict('index')
                costs_lookup = costs_summary
                print(f"✅ Índice de costos creado: {len(costs_lookup)} proyectos con costos")
        
        print(f'Debug costs_lookup: {costs_lookup}')
        # Índice de cambios por EDP
        log_lookup = {}
        if not df_log.empty and 'N° EDP' in df_log.columns:
            df_log['N° EDP'] = df_log['N° EDP'].astype(str).str.strip()
            log_summary = df_log.groupby('N° EDP').agg({
                'Campo': 'count',
                'Usuario': 'nunique'
            }).to_dict('index')
            log_lookup = log_summary
            print(f"✅ Índice de log creado: {len(log_lookup)} EDPs con cambios")
        return {
            'df_edp': df_edp,
            'df_projects': df_projects,
            'df_costs': df_costs,
            'df_log': df_log,
            'projects_lookup': projects_lookup,
            'costs_lookup': costs_lookup,
            'log_lookup': log_lookup,
            'estadisticas': {
                'total_edps': len(df_edp),
                'proyectos_con_costos': len(costs_lookup),
                'edps_con_cambios': len(log_lookup),
                'fecha_calculo': hoy.isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Error creando relaciones simplificadas: {e}")
        import traceback
        traceback.print_exc()
        return None

def calcular_kpis_ejecutivos_simplificado(datos_relacionados, fecha_inicio=None, fecha_fin=None, departamento='todos', cliente='todos', estado='todos'):
    """Calcula KPIs usando el enfoque simplificado sin merges complejos"""
    try:
        if datos_relacionados is None:
            return obtener_kpis_vacios()
        
        df_edp = datos_relacionados['df_edp'].copy()
        df_costos = datos_relacionados['df_costs'].copy()
        costs_lookup = datos_relacionados['costs_lookup']
        log_lookup = datos_relacionados['log_lookup']
        
        
        print(df_costos.head())
        # Aplicar filtros básicos
        df_periodo = aplicar_filtros_basicos(df_edp, fecha_inicio, fecha_fin, departamento, cliente, estado)
        
        if df_periodo.empty:
            print("⚠️ No hay datos después de aplicar filtros")
            return obtener_kpis_vacios()
        
        print(f"📊 Calculando KPIs simplificados para {len(df_periodo)} registros")
        
        # ===== CALCULAR MÉTRICAS BÁSICAS =====
        estados_pendientes = ['enviado', 'revisión', 'enviado ']
        estados_completados = ['pagado', 'validado', 'pagado ', 'validado ']
        
        df_pendientes = df_periodo[df_periodo['Estado'].str.strip().isin(estados_pendientes)]
        df_completados = df_periodo[df_periodo['Estado'].str.strip().isin(estados_completados)]
        df_criticos = df_pendientes[df_pendientes['Días Espera'] >= 30] if not df_pendientes.empty else pd.DataFrame()
        
        # Montos básicos
        monto_pendiente = df_pendientes['Monto Aprobado'].sum() if not df_pendientes.empty else 0
        monto_pendiente_critico = df_criticos['Monto Aprobado'].sum() if not df_criticos.empty else 0
        monto_emitido = df_periodo['Monto Aprobado'].sum()
        monto_cobrado = df_completados['Monto Aprobado'].sum() if not df_completados.empty else 0
        
        # ===== ENRIQUECER CON DATOS DE COSTOS =====
        costos_totales_reales = 0
        proyectos_con_costos = 0
        
        for _, row in df_periodo.iterrows():
            proyecto_id = str(row.get('Proyecto', '')).strip()
            if proyecto_id in costs_lookup:
                costo_proyecto = costs_lookup[proyecto_id].get('importe_neto', 0)
                costos_totales_reales += costo_proyecto
                proyectos_con_costos += 1
        
        # ===== ENRIQUECER CON DATOS DE LOG =====
        total_cambios = 0
        edps_con_cambios = 0
        
        for _, row in df_periodo.iterrows():
            edp_id = str(row.get('N° EDP', '')).strip()
            if edp_id in log_lookup:
                cambios_edp = log_lookup[edp_id].get('Campo', 0)
                total_cambios += cambios_edp
                edps_con_cambios += 1
        
        # ===== CALCULAR MÉTRICAS DERIVADAS =====
        pct_critico = (monto_pendiente_critico / monto_pendiente * 100) if monto_pendiente > 0 else 0
        pct_cobrado = (monto_cobrado / monto_emitido * 100) if monto_emitido > 0 else 0
        pct_avance = (len(df_completados) / len(df_periodo) * 100) if len(df_periodo) > 0 else 0
        concentracion_atraso = (monto_pendiente_critico / monto_pendiente * 100) if monto_pendiente > 0 else 0
        
        # DSO
        if not df_completados.empty and 'Días Espera' in df_completados.columns:
            dso = df_completados['Días Espera'].mean()
        else:
            dso = 45
        
        
        # Aging buckets
        bucket_0_15 = len(df_pendientes[df_pendientes['Días Espera'] <= 15]) if not df_pendientes.empty else 0
        bucket_16_30 = len(df_pendientes[(df_pendientes['Días Espera'] > 15) & (df_pendientes['Días Espera'] <= 30)]) if not df_pendientes.empty else 0
        bucket_31_60 = len(df_pendientes[(df_pendientes['Días Espera'] > 30) & (df_pendientes['Días Espera'] <= 60)]) if not df_pendientes.empty else 0
        bucket_60_plus = len(df_pendientes[df_pendientes['Días Espera'] > 60]) if not df_pendientes.empty else 0
        
        # Rentabilidad estimada
        margen_bruto_estimado = monto_cobrado - costos_totales_reales
        rentabilidad_estimada = (margen_bruto_estimado / monto_cobrado * 100) if monto_cobrado > 0 else 0
        
        # ===== MÉTRICAS DE EFICIENCIA =====
        tiempo_medio_ciclo = dso
        meta_tiempo_ciclo = 30
        benchmark_tiempo_ciclo = 35
        
        eficiencia_actual = round(pct_avance * (100 - pct_critico) / 100, 1)
        eficiencia_anterior = max(0, eficiencia_actual - 5.3)
        mejora_eficiencia = round(eficiencia_actual - eficiencia_anterior, 1)
        
        tiempo_medio_ciclo_pct = round((meta_tiempo_ciclo / tiempo_medio_ciclo * 100), 1) if tiempo_medio_ciclo > 0 else 0
        
        # Tiempos por etapa
        tiempo_emision = round(tiempo_medio_ciclo * 0.18, 1)
        tiempo_gestion = round(tiempo_medio_ciclo * 0.27, 1)
        tiempo_conformidad = round(tiempo_medio_ciclo * 0.33, 1)
        tiempo_pago = round(tiempo_medio_ciclo * 0.22, 1)
        
        etapa_emision_pct = int(tiempo_emision / tiempo_medio_ciclo * 100) if tiempo_medio_ciclo > 0 else 18
        etapa_gestion_pct = int(tiempo_gestion / tiempo_medio_ciclo * 100) if tiempo_medio_ciclo > 0 else 27
        etapa_conformidad_pct = int(tiempo_conformidad / tiempo_medio_ciclo * 100) if tiempo_medio_ciclo > 0 else 33
        etapa_pago_pct = int(tiempo_pago / tiempo_medio_ciclo * 100) if tiempo_medio_ciclo > 0 else 22
        
        # Oportunidad de mejora
        if tiempo_conformidad > 15:
            oportunidad_mejora = f"Reducir tiempo de conformidad con cliente ({tiempo_conformidad:.1f} días vs. benchmark 7 días)"
        elif tiempo_gestion > 12:
            oportunidad_mejora = f"Optimizar tiempo de gestión interna ({tiempo_gestion:.1f} días vs. benchmark 8 días)"
        else:
            oportunidad_mejora = "Mantener tiempos actuales dentro del benchmark"
        
        # ===== ANÁLISIS POR CLIENTE =====
        clientes_data = {}
        if 'Cliente' in df_periodo.columns:
            for cliente in df_periodo['Cliente'].dropna().unique():
                df_cliente = df_periodo[df_periodo['Cliente'] == cliente]
                monto_cliente = df_cliente['Monto Aprobado'].sum()
                clientes_data[cliente] = monto_cliente
        
        cliente_principal = max(clientes_data.items(), key=lambda x: x[1])[0] if clientes_data else "N/A"
        pct_ingresos_principal = (max(clientes_data.values()) / monto_emitido * 100) if clientes_data and monto_emitido > 0 else 0
        
        
        dso_cliente_principal = df_periodo[df_periodo['Cliente'] == cliente_principal]['Días Espera'].mean() if cliente_principal != "N/A" else 45
        
        
        # ===== EFICIENCIA POR GESTOR =====
        eficiencia_gestores = {}
        rentabilidad_por_gestor = {}
        
        if 'Jefe de Proyecto' in df_periodo.columns:
            gestores_unicos = df_periodo['Jefe de Proyecto'].dropna().unique()
            for gestor in gestores_unicos:
                if pd.notna(gestor) and str(gestor).strip():
                    df_gestor = df_periodo[df_periodo['Jefe de Proyecto'] == gestor]
                    if len(df_gestor) > 0:
                        completados_gestor = df_gestor['Estado'].str.strip().isin(['validado', 'pagado']).sum()
                        eficiencia_gestores[gestor] = round((completados_gestor / len(df_gestor)) * 100, 1)
                        
                        ingresos_gestor = df_gestor[df_gestor['Estado'].str.strip().isin(['pagado','validado'])]['Monto Aprobado'].sum()
                        tiempo_gestor = df_gestor['Días Espera'].mean() if 'Días Espera' in df_gestor.columns else 45
                        factor_gestor = max(tiempo_gestor / 30, 1.0) if tiempo_gestor > 0 else 1.0
                        
                        costo_gestor = ingresos_gestor * (0.35 * factor_gestor + 0.15 + 0.08)
                        margen_gestor = ingresos_gestor - costo_gestor
                        rentabilidad_gestor = (margen_gestor / ingresos_gestor * 100) if ingresos_gestor > 0 else 0
                        
                        rentabilidad_por_gestor[gestor] = {
                            'margen_porcentaje': round(rentabilidad_gestor, 1),
                            'margen_absoluto': round(margen_gestor / 1_000_000, 2),
                            'eficiencia_tiempo': round(30 / tiempo_gestor if tiempo_gestor > 0 else 0, 2)
                        }
        
        # ===== MÉTRICAS DE CALIDAD =====
        reprocesos = df_periodo[df_periodo['Estado Detallado'] == 're-trabajo solicitado'] if 'Estado Detallado' in df_periodo.columns else pd.DataFrame()
        reprocesos_promedio = round((len(reprocesos) / len(df_periodo)) * 100, 1) if len(df_periodo) > 0 else 0
        retrabajos_reducidos = round(100 - reprocesos_promedio, 1)
        reprocesos_p95 = round(reprocesos_promedio * 1.5, 1)
        
        conformidades_ok = len(df_periodo[df_periodo['Conformidad Enviada'] == 'Sí']) if 'Conformidad Enviada' in df_periodo.columns else len(df_completados)
        tasa_conformidad = round((conformidades_ok / len(df_periodo)) * 100, 1) if len(df_periodo) > 0 else 85
        
        indice_calidad = round(100 - (total_cambios / len(df_periodo) * 10) if len(df_periodo) > 0 else 100, 1)
        
        # ===== RETORNAR KPIs CONSOLIDADOS =====
        return {
            # Financieros básicos
            'monto_pendiente': round(monto_pendiente / 1_000_000, 1),
            'monto_pendiente_critico': round(monto_pendiente_critico / 1_000_000, 1),
            'monto_emitido': round(monto_emitido / 1_000_000, 1),
            'monto_cobrado': round(monto_cobrado / 1_000_000, 1),
            'ingresos_totales': round(monto_cobrado / 1_000_000, 1),
            'pct_critico': round(pct_critico, 1),
            'pct_cobrado': round(pct_cobrado, 1),
            'dso': round(dso, 1),
            'dso_cliente_principal': round(dso_cliente_principal, 1),
            'costo_financiero': 0,
            
            # Operativos
            'total_edps': len(df_periodo),
            'pct_avance': round(pct_avance, 1),
            'bucket_0_15': bucket_0_15,
            'bucket_16_30': bucket_16_30,
            'bucket_31_60': bucket_31_60,
            'bucket_60_plus': bucket_60_plus,
            'q_proyectos_criticos': len(df_criticos),
            'backlog_edp': len(df_pendientes),
            'valor_proyectos_criticos': round(monto_pendiente_critico / 1_000_000, 1),
            
            # Concentración y atraso
            'concentracion_atraso': round(concentracion_atraso, 1),
            'concentracion_clientes': round(sum(sorted(clientes_data.values(), reverse=True)[:3]) / sum(clientes_data.values()) * 100, 1) if len(clientes_data) >= 3 else 100,
            'backlog_valor': round(monto_pendiente / 1_000_000, 1),
            
            # Costos reales
            'costos_totales_reales': round(costos_totales_reales / 1_000_000, 2),
            'costos_totales': round(costos_totales_reales / 1_000_000, 2),
            'proyectos_con_costos': proyectos_con_costos,
            'margen_bruto_estimado': round(margen_bruto_estimado / 1_000_000, 2),
            'margen_bruto_absoluto': round(margen_bruto_estimado / 1_000_000, 2),
            'rentabilidad_estimada': round(rentabilidad_estimada, 1),
            'rentabilidad_general': round(rentabilidad_estimada, 1),
            
            # Rentabilidad y metas
            'tendencia_rentabilidad': 2.3,
            'meta_rentabilidad': 35.0,
            'vs_meta_rentabilidad': round(rentabilidad_estimada - 35.0, 1),
            'pct_meta_rentabilidad': round(rentabilidad_estimada / 35.0 * 100, 1) if rentabilidad_estimada > 0 else 0,
            'roi_calculado': round(margen_bruto_estimado / costos_totales_reales * 100, 1) if costos_totales_reales > 0 else 0,
            
            # Log y cambios
            'total_cambios': total_cambios,
            'edps_con_cambios': edps_con_cambios,
            'promedio_cambios_por_edp': round(total_cambios / len(df_periodo), 1) if len(df_periodo) > 0 else 0,
            'reprocesos_promedio': reprocesos_promedio,
            'reprocesos_p95': reprocesos_p95,
            'retrabajos_reducidos': retrabajos_reducidos,
            
            # Clientes
            'cliente_principal': cliente_principal,
            'pct_ingresos_principal': round(pct_ingresos_principal, 1),
            
            # Gestores
            'eficiencia_gestores': eficiencia_gestores,
            'rentabilidad_por_gestor': rentabilidad_por_gestor,
            
            # Metas y benchmarks
            'meta_ingresos': 3000,
            'vs_meta_ingresos': round(monto_cobrado / 1_000_000 - 3000, 1),
            'pct_meta_ingresos': round(monto_cobrado / 1_000_000 / 3000 * 100, 1),
            'crecimiento_ingresos': 8.5,
            
            # Calidad y eficiencia
            'utilizacion_recursos': round(pct_avance * 0.8 + (100 - pct_critico) * 0.2, 1),
            'indice_calidad': indice_calidad,
            'eficiencia_global': round(pct_avance * (100 - pct_critico) / 100, 1),
            'meta_cumplida': round(pct_avance, 1),
            'tasa_conformidad': tasa_conformidad,
            
            # Métricas de eficiencia y tiempo
            'mejora_eficiencia': mejora_eficiencia,
            'tiempo_medio_ciclo': round(tiempo_medio_ciclo, 1),
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
            
            # Tiempo y aging
            'pct_30d': round((bucket_0_15 + bucket_16_30) / len(df_pendientes) * 100, 1) if len(df_pendientes) > 0 else 0,
            'pct_60d': round(bucket_31_60 / len(df_pendientes) * 100, 1) if len(df_pendientes) > 0 else 0,
            'pct_90d': round(bucket_60_plus / len(df_pendientes) * 100, 1) if len(df_pendientes) > 0 else 0,
            'pct_mas90d': 0,
            'proyectos_on_time': round((bucket_0_15 + bucket_16_30) / len(df_pendientes) * 100, 1) if len(df_pendientes) > 0 else 0,
            'proyectos_retrasados': round((bucket_31_60 + bucket_60_plus) / len(df_pendientes) * 100, 1) if len(df_pendientes) > 0 else 0,
            'proyectos_criticos': bucket_60_plus,
            
            # Alertas y riesgos
            'alertas_criticas': len(df_criticos),
            'riesgo_pago_principal': 25,
            'tendencia_pago_principal': 'mejora',
            'tendencia_pendiente': 5.2,
            
            # Costos detallados
            'costo_personal': round(costos_totales_reales * 0.35 / 1_000_000, 2),
            'costo_overhead': round(costos_totales_reales * 0.15 / 1_000_000, 2),
            'costo_tecnologia': round(costos_totales_reales * 0.08 / 1_000_000, 2),
            'costo_financiero_extra': 0,
            'costo_por_edp': round(costos_totales_reales / len(df_periodo), 0) if len(df_periodo) > 0 else 0,
            'margen_por_edp': round(margen_bruto_estimado / len(df_periodo), 0) if len(df_periodo) > 0 else 0,
            'ebitda': round(margen_bruto_estimado * 0.85 / 1_000_000, 2),
            'ebitda_porcentaje': round((margen_bruto_estimado * 0.85 / monto_cobrado * 100), 1) if monto_cobrado > 0 else 0,
            'factor_tiempo_costo': round(max(tiempo_medio_ciclo / 30, 1.0), 2),
            
            # Adicionales
            'nps_score': 78,
            'satisfaccion_cliente': 85,
            'roi_promedio': round(rentabilidad_estimada, 1),
            'benchmark_industria': 30.0,
            'posicion_vs_benchmark': round(rentabilidad_estimada - 30.0, 1),
            'tiempo_medio_real': round(tiempo_medio_ciclo, 1),
            
            # Metadata
            'fecha_calculo': datetime.now().isoformat(),
            'registros_procesados': len(df_periodo),
            'fuentes_datos': {
                'edp': True,
                'costos': proyectos_con_costos > 0,
                'log': edps_con_cambios > 0
            }
        }
        
    except Exception as e:
        print(f"❌ Error en calcular_kpis_ejecutivos_simplificado: {e}")
        import traceback
        traceback.print_exc()
        return obtener_kpis_vacios()

def obtener_kpis_vacios():
    """Retorna KPIs con valores por defecto cuando no hay datos"""
    return {
        # Financieros básicos
        'monto_pendiente': 0,
        'monto_pendiente_critico': 0,
        'monto_emitido': 0,
        'monto_cobrado': 0,
        'ingresos_totales': 0,
        'pct_critico': 0,
        'pct_cobrado': 0,
        'dso': 45,
        'costo_financiero': 0,
        
        # Operativos
        'total_edps': 0,
        'pct_avance': 0,
        'bucket_0_15': 0,
        'bucket_16_30': 0,
        'bucket_31_60': 0,
        'bucket_60_plus': 0,
        'q_proyectos_criticos': 0,
        'backlog_edp': 0,
        'valor_proyectos_criticos': 0,
        
        # Concentración y atraso
        'concentracion_atraso': 0,
        'concentracion_clientes': 0,
        'backlog_valor': 0,
        
        # Rentabilidad
        'costos_totales_reales': 0,
        'costos_totales': 0,
        'proyectos_con_costos': 0,
        'margen_bruto_estimado': 0,
        'margen_bruto_absoluto': 0,
        'rentabilidad_estimada': 0,
        'rentabilidad_general': 0,
        'tendencia_rentabilidad': 0,
        'meta_rentabilidad': 35.0,
        'vs_meta_rentabilidad': -35.0,
        'pct_meta_rentabilidad': 0,
        'roi_calculado': 0,
        
        # Log y cambios
        'total_cambios': 0,
        'edps_con_cambios': 0,
        'promedio_cambios_por_edp': 0,
        'reprocesos_promedio': 0,
        'reprocesos_p95': 0,
        'retrabajos_reducidos': 100,
        
        # Clientes
        'cliente_principal': "N/A",
        'pct_ingresos_principal': 0,
        
        # Gestores
        'eficiencia_gestores': {},
        'rentabilidad_por_gestor': {},
        
        # Metas
        'meta_ingresos': 3000,
        'vs_meta_ingresos': -3000,
        'pct_meta_ingresos': 0,
        'crecimiento_ingresos': 0,
        
        # Calidad y eficiencia
        'utilizacion_recursos': 75,
        'indice_calidad': 100,
        'eficiencia_global': 0,
        'meta_cumplida': 0,
        'tasa_conformidad': 0,
        
        # Métricas de eficiencia y tiempo
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
        
        # Tiempo y aging
        'pct_30d': 0,
        'pct_60d': 0,
        'pct_90d': 0,
        'pct_mas90d': 0,
        'tiempo_medio_real': 45,
        'proyectos_on_time': 0,
        'proyectos_retrasados': 0,
        'proyectos_criticos': 0,
        
        # Alertas y riesgos
        'alertas_criticas': 0,
        'riesgo_pago_principal': 50,
        'tendencia_pago_principal': 'estable',
        'tendencia_pendiente': 0,
        
        # Costos detallados
        'costo_personal': 0,
        'costo_overhead': 0,
        'costo_tecnologia': 0,
        'costo_financiero_extra': 0,
        'costo_por_edp': 0,
        'margen_por_edp': 0,
        'ebitda': 0,
        'ebitda_porcentaje': 0,
        'factor_tiempo_costo': 1.0,
        
        # Adicionales
        'nps_score': 75,
        'satisfaccion_cliente': 75,
        'roi_promedio': 0,
        'benchmark_industria': 30.0,
        'posicion_vs_benchmark': -30.0,
        
        # Metadata
        'fecha_calculo': datetime.now().isoformat(),
        'registros_procesados': 0,
        'fuentes_datos': {
            'edp': False,
            'costos': False,
            'log': False
        }
    }

def aplicar_filtros_basicos(df_edp, fecha_inicio=None, fecha_fin=None, departamento='todos', cliente='todos', estado='todos'):
    """Aplica filtros básicos al DataFrame de EDP"""
    df_filtrado = df_edp.copy()
    
    # Filtro por fechas
    if fecha_inicio:
        try:
            fecha_inicio_dt = pd.to_datetime(fecha_inicio)
            df_filtrado = df_filtrado[df_filtrado['Fecha Emisión'] >= fecha_inicio_dt]
        except:
            print(f"⚠️ Error al aplicar filtro fecha_inicio: {fecha_inicio}")
    
    if fecha_fin:
        try:
            fecha_fin_dt = pd.to_datetime(fecha_fin)
            df_filtrado = df_filtrado[df_filtrado['Fecha Emisión'] <= fecha_fin_dt]
        except:
            print(f"⚠️ Error al aplicar filtro fecha_fin: {fecha_fin}")
    
    # Filtro por departamento/jefe de proyecto
    if departamento != 'todos' and 'Jefe de Proyecto' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Jefe de Proyecto'] == departamento]
    
    # Filtro por cliente
    if cliente != 'todos' and 'Cliente' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Cliente'] == cliente]
    
    # Filtro por estado
    if estado != 'todos' and 'Estado' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Estado'].str.strip() == estado]
    
    return df_filtrado

def obtener_datos_charts_simplificado(datos_relacionados, departamento='todos', cliente='todos', estado='todos'):
    """Genera datos para charts usando el enfoque simplificado con tendencia mejorada"""
    try:
        if datos_relacionados is None:
            return {}
        
        df_edp = datos_relacionados['df_edp']
        df_cost = read_sheet('cost_header!A1:Q')
        costs_lookup = datos_relacionados['costs_lookup']

        print(f'Debug tipo_costo: {costs_lookup}')
        # Aplicar filtros
        df_periodo = aplicar_filtros_basicos(df_edp, None, None, departamento, cliente, estado)
        
        if df_periodo.empty:
            return {}
        
        print(f"📊 Generando charts mejorados para {len(df_periodo)} registros")
        
        return {
            'cash_in_forecast': build_cash_forecast_simplificado(df_periodo),
            'cash_forecast_detallado': build_cash_forecast_detallado(df_periodo),  # Nuevo
            'estado_proyectos': build_estado_proyectos_simplificado(df_periodo),
            'aging_buckets': build_aging_buckets_simplificado(df_periodo),
            'tendencia_financiera': build_tendencia_mensual_simplificado(df_edp),  # Mejorado
            'rentabilidad_departamentos': build_rentabilidad_simplificado(df_periodo, costs_lookup),
            'analisis_costos': build_analisis_costos(df_cost),
            'concentracion_clientes': build_distribucion_clientes_simplificado(df_periodo),
        }
        
    except Exception as e:
        print(f"❌ Error generando charts mejorados: {e}")
        return {}
def build_cash_forecast_simplificado(df_periodo):
    """Cash forecast sin merge, solo con datos de EDP"""
    try:
        hoy = datetime.now()
        hoy_30d = hoy + timedelta(days=30)
        hoy_60d = hoy + timedelta(days=60)
        hoy_90d = hoy + timedelta(days=90)
        
        # Filtrar solo pendientes
        df_pendientes = df_periodo[~df_periodo['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        if df_pendientes.empty:
            return {'labels': ['30 días', '60 días', '90 días'], 'datasets': []}
        
        # Usar Fecha Estimada de Pago si existe, sino estimar
        if 'Fecha Estimada de Pago' in df_pendientes.columns:
            df_pendientes['Fecha Estimada de Pago'] = pd.to_datetime(df_pendientes['Fecha Estimada de Pago'], errors='coerce')
            fecha_pago_col = 'Fecha Estimada de Pago'
        else:
            df_pendientes = df_pendientes.copy()
            df_pendientes['Fecha_Estimada_Calculada'] = df_pendientes['Fecha Emisión'] + pd.Timedelta(days=45)
            fecha_pago_col = 'Fecha_Estimada_Calculada'
        
        # Calcular montos por período
        monto_30d = df_pendientes[df_pendientes[fecha_pago_col] <= hoy_30d]['Monto Aprobado'].sum() / 1_000_000
        monto_60d = df_pendientes[(df_pendientes[fecha_pago_col] > hoy_30d) & 
                                (df_pendientes[fecha_pago_col] <= hoy_60d)]['Monto Aprobado'].sum() / 1_000_000
        monto_90d = df_pendientes[(df_pendientes[fecha_pago_col] > hoy_60d) & 
                                (df_pendientes[fecha_pago_col] <= hoy_90d)]['Monto Aprobado'].sum() / 1_000_000
        
        return {
            'labels': ['30 días', '60 días', '90 días'],
            'datasets': [
                {
                    'label': 'Flujo proyectado (M$)',
                    'data': [float(monto_30d), float(monto_60d), float(monto_90d)],
                    'backgroundColor': ['rgba(16, 185, 129, 0.7)', 'rgba(59, 130, 246, 0.7)', 'rgba(249, 115, 22, 0.7)']
                }
            ]
        }
    except Exception as e:
        print(f"Error en cash forecast simplificado: {e}")
        return {'labels': [], 'datasets': []}

def build_estado_proyectos_simplificado(df_periodo):
    """Estado de proyectos basado solo en días de espera"""
    try:
        a_tiempo = len(df_periodo[df_periodo['Días Espera'] <= 30])
        en_riesgo = len(df_periodo[(df_periodo['Días Espera'] > 30) & (df_periodo['Días Espera'] <= 45)])
        retrasados = len(df_periodo[df_periodo['Días Espera'] > 45])
        
        return {
            'labels': ['A tiempo', 'En riesgo', 'Retrasados'],
            'datasets': [
                {
                    'data': [a_tiempo, en_riesgo, retrasados],
                    'backgroundColor': ['#10B981', '#FBBF24', '#F87171']
                }
            ]
        }
    except Exception as e:
        print(f"Error en estado proyectos simplificado: {e}")
        return {'labels': [], 'datasets': []}

def build_distribucion_clientes_simplificado(df_periodo):
    """Distribución por cliente usando análisis de Pareto (80/20) con montos en millones"""
    try:
        if 'Cliente' not in df_periodo.columns:
            return {'labels': [], 'datasets': []}
        
        # Calcular montos por cliente y convertir a millones
        clientes_montos = df_periodo.groupby('Cliente')['Monto Aprobado'].sum() / 1_000_000
        
        if clientes_montos.empty:
            return {'labels': [], 'datasets': []}
        
        # Ordenar clientes por monto de mayor a menor
        clientes_ordenados = clientes_montos.sort_values(ascending=False)
        
        # Tomar los top 10 clientes
        top_clientes = clientes_ordenados.head(10)
        
        # Calcular porcentajes acumulados
        total = clientes_ordenados.sum()
        porcentajes_acumulados = (top_clientes.cumsum() / total * 100).round(1)
        
        return {
            'labels': top_clientes.index.tolist(),
            'datasets': [
                {
                    'type': 'bar',
                    'label': 'Monto (M$)',
                    'data': top_clientes.round(1).tolist(),
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.7)',  # blue
                        'rgba(16, 185, 129, 0.7)',  # green
                        'rgba(249, 115, 22, 0.7)',  # orange
                        'rgba(139, 92, 246, 0.7)',  # purple
                        'rgba(244, 63, 94, 0.7)',   # red
                        'rgba(6, 182, 212, 0.7)',   # cyan
                        'rgba(251, 191, 36, 0.7)',  # yellow
                        'rgba(107, 114, 128, 0.7)', # gray
                        'rgba(236, 72, 153, 0.7)',  # pink
                        'rgba(168, 85, 247, 0.7)'   # violet
                    ],
                    'yAxisID': 'y'
                },
                {
                    'type': 'line',
                    'label': 'Porcentaje Acumulado',
                    'data': porcentajes_acumulados.tolist(),
                    'borderColor': 'rgba(234, 88, 12, 1)',
                    'borderWidth': 2,
                    'fill': False,
                    'yAxisID': 'percentage',
                    'pointBackgroundColor': 'rgba(234, 88, 12, 1)',
                    'pointRadius': 4,
                    'pointHoverRadius': 6
                }
            ]
        }
    except Exception as e:
        print(f"Error en distribución clientes Pareto: {e}")
        return {'labels': [], 'datasets': []}

def build_aging_buckets_simplificado(df_periodo):
    """Aging buckets usando solo días de espera"""
    try:
        df_pendientes = df_periodo[~df_periodo['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        if df_pendientes.empty:
            return {'labels': ['0-15', '16-30', '31-60', '>60'], 'datasets': []}
        
        bucket_0_15 = len(df_pendientes[df_pendientes['Días Espera'] <= 15])
        bucket_16_30 = len(df_pendientes[(df_pendientes['Días Espera'] > 15) & (df_pendientes['Días Espera'] <= 30)])
        bucket_31_60 = len(df_pendientes[(df_pendientes['Días Espera'] > 30) & (df_pendientes['Días Espera'] <= 60)])
        bucket_60_plus = len(df_pendientes[df_pendientes['Días Espera'] > 60])
        
        return {
            'labels': ['0-15 días', '16-30 días', '31-60 días', '>60 días'],
            'datasets': [
                {
                    'label': 'Cantidad EDPs',
                    'data': [bucket_0_15, bucket_16_30, bucket_31_60, bucket_60_plus],
                    'backgroundColor': ['rgba(16, 185, 129, 0.7)', 'rgba(249, 115, 22, 0.7)', 'rgba(244, 63, 94, 0.7)', 'rgba(244, 63, 94, 0.9)']
                }
            ]
        }
    except Exception as e:
        print(f"Error en aging buckets simplificado: {e}")
        return {'labels': [], 'datasets': []}


def build_tendencia_mensual_simplificado(df_edp):
    """Tendencia financiera completa: ingresos, costos y proyecciones"""
    try:
        # Preparar datos base
        df_edp_copia = df_edp.copy()
        df_edp_copia['Mes'] = df_edp_copia['Fecha Emisión'].dt.strftime('%Y-%m')
        
        # Obtener datos de costos para enriquecer
        try:
            df_costs = read_sheet("cost_header!A1:Q")
            if not df_costs.empty and 'project_id' in df_costs.columns:
                df_costs['project_id'] = df_costs['project_id'].astype(str).str.strip()
                df_costs['importe_neto'] = pd.to_numeric(df_costs['importe_neto'], errors='coerce').fillna(0)
                df_costs['fecha_costo'] = pd.to_datetime(df_costs.get('fecha_costo', df_costs.get('created_at')), errors='coerce')
                
                # Si no hay fecha de costo, usar fecha de emisión del EDP correspondiente
                if df_costs['fecha_costo'].isna().all():
                    df_costs = df_costs.merge(
                        df_edp_copia[['Proyecto', 'Fecha Emisión']].rename(columns={'Proyecto': 'project_id'}),
                        on='project_id', how='left'
                    )
                    df_costs['fecha_costo'] = df_costs['Fecha Emisión']
                
                df_costs['Mes'] = df_costs['fecha_costo'].dt.strftime('%Y-%m')
        except Exception as e:
            print(f"⚠️ No se pudieron cargar costos para tendencia: {e}")
            df_costs = pd.DataFrame()
        
        # ===== CALCULAR MÉTRICAS POR MES =====
        
        # 1. Ingresos mensuales (EDP completados)
        df_completados = df_edp_copia[df_edp_copia['Estado'].str.strip().isin(['pagado', 'validado'])]
        ingresos_mensuales = df_completados.groupby('Mes')['Monto Aprobado'].sum() / 1_000_000
        
        # 2. Ingresos totales emitidos (todos los EDP)
        ingresos_emitidos = df_edp_copia.groupby('Mes')['Monto Aprobado'].sum() / 1_000_000
        
        # 3. Costos reales mensuales
        costos_mensuales = pd.Series(dtype=float)
        if not df_costs.empty and 'Mes' in df_costs.columns:
            costos_mensuales = df_costs.groupby('Mes')['importe_neto'].sum() / 1_000_000
        
        # ===== DETERMINAR PERÍODO (ÚLTIMOS 6 MESES + 3 PROYECCIONES) =====
        
        # Obtener todos los meses disponibles
        todos_meses = set()
        if len(ingresos_mensuales) > 0:
            todos_meses.update(ingresos_mensuales.index)
        if len(ingresos_emitidos) > 0:
            todos_meses.update(ingresos_emitidos.index)
        if len(costos_mensuales) > 0:
            todos_meses.update(costos_mensuales.index)
        
        if not todos_meses:
            return {'labels': [], 'datasets': []}
        
        # Últimos 6 meses reales
        meses_ordenados = sorted(todos_meses)
        ultimos_6_meses = meses_ordenados[-6:] if len(meses_ordenados) >= 6 else meses_ordenados
        
        # Generar 3 meses de proyección
        ultimo_mes = datetime.strptime(meses_ordenados[-1], '%Y-%m')
        meses_proyeccion = []
        for i in range(1, 4):
            mes_futuro = ultimo_mes + timedelta(days=32*i)
            mes_futuro = mes_futuro.replace(day=1)  # Primer día del mes
            meses_proyeccion.append(mes_futuro.strftime('%Y-%m'))
        
        # Período completo: 6 meses reales + 3 proyecciones
        periodo_completo = ultimos_6_meses + meses_proyeccion
        
        # ===== RECOPILAR DATOS POR MES =====
        
        labels = []
        datos_ingresos_reales = []
        datos_ingresos_emitidos = []
        datos_costos = []
        datos_margen = []
        datos_cashflow_proyectado = []
        
        # Calcular promedios para proyecciones
        avg_ingresos_reales = ingresos_mensuales.tail(3).mean() if len(ingresos_mensuales) >= 3 else 0
        avg_ingresos_emitidos = ingresos_emitidos.tail(3).mean() if len(ingresos_emitidos) >= 3 else 0
        avg_costos = costos_mensuales.tail(3).mean() if len(costos_mensuales) >= 3 else avg_ingresos_reales * 0.65
        crecimiento_mensual = 1.05  # 5% crecimiento mensual proyectado
        
        for i, mes in enumerate(periodo_completo):
            try:
                # Convertir mes a label legible
                fecha = datetime.strptime(mes, '%Y-%m')
                if i < len(ultimos_6_meses):
                    labels.append(fecha.strftime('%b %Y'))
                else:
                    labels.append(fecha.strftime('%b %Y') + ' (P)')  # (P) = Proyección
                
                # Determinar si es mes real o proyección
                es_proyeccion = i >= len(ultimos_6_meses)
                
                if not es_proyeccion:
                    # ===== DATOS REALES =====
                    
                    # Ingresos reales (cobrados)
                    ingreso_real = float(ingresos_mensuales.get(mes, 0))
                    datos_ingresos_reales.append(ingreso_real)
                    
                    # Ingresos emitidos
                    ingreso_emitido = float(ingresos_emitidos.get(mes, 0))
                    datos_ingresos_emitidos.append(ingreso_emitido)
                    
                    # Costos reales
                    costo_real = float(costos_mensuales.get(mes, 0))
                    datos_costos.append(costo_real)
                    
                    # Margen real
                    margen = ingreso_real - costo_real
                    datos_margen.append(margen)
                    
                    # Cash flow real (ingresos - costos del mes)
                    datos_cashflow_proyectado.append(margen)
                    
                else:
                    # ===== PROYECCIONES =====
                    
                    meses_futuros = i - len(ultimos_6_meses) + 1
                    factor_crecimiento = crecimiento_mensual ** meses_futuros
                    
                    # Proyectar ingresos con crecimiento
                    ingreso_proyectado = avg_ingresos_reales * factor_crecimiento
                    datos_ingresos_reales.append(ingreso_proyectado)
                    
                    # Proyectar ingresos emitidos
                    emitido_proyectado = avg_ingresos_emitidos * factor_crecimiento
                    datos_ingresos_emitidos.append(emitido_proyectado)
                    
                    # Proyectar costos (manteniendo ratio)
                    costo_proyectado = ingreso_proyectado * 0.65  # 65% de costos
                    datos_costos.append(costo_proyectado)
                    
                    # Margen proyectado
                    margen_proyectado = ingreso_proyectado - costo_proyectado
                    datos_margen.append(margen_proyectado)
                    
                    # Cash flow proyectado
                    datos_cashflow_proyectado.append(margen_proyectado)
                    
            except Exception as e:
                print(f"Error procesando mes {mes}: {e}")
                labels.append(mes)
                datos_ingresos_reales.append(0)
                datos_ingresos_emitidos.append(0)
                datos_costos.append(0)
                datos_margen.append(0)
                datos_cashflow_proyectado.append(0)
        
        # ===== GENERAR DATASETS =====
        
        datasets = [
            {
                'label': 'Ingresos Cobrados (M$)',
                'data': datos_ingresos_reales,
                'borderColor': '#10B981',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                'fill': False,
                'tension': 0.3,
                'borderWidth': 3,
                'pointBackgroundColor': '#10B981',
                'pointBorderWidth': 2,
                'pointRadius': 4
            },
            {
                'label': 'Ingresos Proyectados (M$)',
                'data': datos_ingresos_emitidos,
                'borderColor': '#3B82F6',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'fill': False,
                'tension': 0.3,
                'borderWidth': 2,
                'borderDash': [5, 5],  # Línea punteada
                'pointBackgroundColor': '#3B82F6',
                'pointRadius': 3
            },
            {
                'label': 'Costos (M$)',
                'data': datos_costos,
                'borderColor': '#F87171',
                'backgroundColor': 'rgba(248, 113, 113, 0.1)',
                'fill': False,
                'tension': 0.3,
                'borderWidth': 2,
                'pointBackgroundColor': '#F87171',
                'pointRadius': 3
            },
            {
                'label': 'Margen Bruto (M$)',
                'data': datos_margen,
                'borderColor': '#8B5CF6',
                'backgroundColor': 'rgba(139, 92, 246, 0.2)',
                'fill': True,
                'tension': 0.3,
                'borderWidth': 2,
                'pointBackgroundColor': '#8B5CF6',
                'pointRadius': 3
            }
        ]
        
        # ===== CALCULAR ESTADÍSTICAS ADICIONALES =====
        
        # Promedio de margen de los últimos 3 meses reales
        margen_real_reciente = [m for i, m in enumerate(datos_margen) if i < len(ultimos_6_meses)]
        promedio_margen = sum(margen_real_reciente[-3:]) / 3 if len(margen_real_reciente) >= 3 else 0
        
        # Tendencia (comparar primer vs último mes real)
        if len(margen_real_reciente) >= 2:
            tendencia_margen = ((margen_real_reciente[-1] - margen_real_reciente[0]) / margen_real_reciente[0] * 100) if margen_real_reciente[0] != 0 else 0
        else:
            tendencia_margen = 0
        
        # Cash flow acumulado proyectado (próximos 3 meses)
        cashflow_3m = sum(datos_cashflow_proyectado[-3:])
        
        return {
            'labels': labels,
            'datasets': datasets,
            'estadisticas': {
                'promedio_margen_3m': round(promedio_margen, 1),
                'tendencia_margen': round(tendencia_margen, 1),
                'cashflow_proyectado_3m': round(cashflow_3m, 1),
                'mejor_mes': labels[datos_margen.index(max(datos_margen))] if datos_margen else 'N/A',
                'ratio_costos_promedio': round(sum(datos_costos[-3:]) / sum(datos_ingresos_reales[-3:]) * 100, 1) if sum(datos_ingresos_reales[-3:]) > 0 else 0
            },
            'opciones_grafico': {
                'responsive': True,
                'interaction': {
                    'mode': 'index',
                    'intersect': False
                },
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Tendencia Financiera - Histórico y Proyecciones'
                    },
                    'legend': {
                        'display': True,
                        'position': 'top'
                    },
                    'tooltip': {
                        'callbacks': {
                            'title': 'function(context) { return context[0].label + (context[0].label.includes("(P)") ? " - Proyección" : " - Real"); }',
                            'label': 'function(context) { return context.dataset.label + ": $" + context.parsed.y.toFixed(1) + "M"; }'
                        }
                    }
                },
                'scales': {
                    'x': {
                        'display': True,
                        'title': {
                            'display': True,
                            'text': 'Período (Últimos 6 meses + 3 proyecciones)'
                        }
                    },
                    'y': {
                        'display': True,
                        'title': {
                            'display': True,
                            'text': 'Millones de pesos (M$)'
                        },
                        'beginAtZero': True
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error en tendencia financiera completa: {e}")
        import traceback
        traceback.print_exc()
        return {
            'labels': [],
            'datasets': [],
            'estadisticas': {
                'promedio_margen_3m': 0,
                'tendencia_margen': 0,
                'cashflow_proyectado_3m': 0,
                'mejor_mes': 'N/A',
                'ratio_costos_promedio': 0
            }
        }

def build_cash_forecast_detallado(df_periodo):
    """Cash forecast detallado con múltiples escenarios"""
    try:
        hoy = datetime.now()
        
        # Filtrar solo pendientes
        df_pendientes = df_periodo[~df_periodo['Estado'].str.strip().isin(['pagado', 'validado'])].copy()
        
        if df_pendientes.empty:
            return {'labels': ['30 días', '60 días', '90 días', '120 días'], 'datasets': []}
        
        # Fechas de referencia
        periodos = [
            (30, hoy + timedelta(days=30)),
            (60, hoy + timedelta(days=60)),
            (90, hoy + timedelta(days=90)),
            (120, hoy + timedelta(days=120))
        ]
        
        # Preparar fechas estimadas de pago
        if 'Fecha Estimada de Pago' in df_pendientes.columns:
            df_pendientes['Fecha Estimada de Pago'] = pd.to_datetime(df_pendientes['Fecha Estimada de Pago'], errors='coerce')
            fecha_pago_col = 'Fecha Estimada de Pago'
        else:
            # Estimar basado en días de espera y tipo de cliente
            df_pendientes['Fecha_Estimada_Calculada'] = df_pendientes['Fecha Emisión'] + pd.Timedelta(days=45)
            fecha_pago_col = 'Fecha_Estimada_Calculada'
        
        # ===== CALCULAR ESCENARIOS =====
        
        labels = [f'{p[0]} días' for p in periodos]
        
        # Escenario optimista (90% de cobranza)
        datos_optimista = []
        # Escenario realista (75% de cobranza)
        datos_realista = []
        # Escenario conservador (60% de cobranza)
        datos_conservador = []
        
        fecha_anterior = hoy
        for dias, fecha_limite in periodos:
            # Montos en el período
            mask_periodo = (df_pendientes[fecha_pago_col] > fecha_anterior) & (df_pendientes[fecha_pago_col] <= fecha_limite)
            monto_periodo = df_pendientes[mask_periodo]['Monto Aprobado'].sum() / 1_000_000
            
            # Aplicar factores de probabilidad
            datos_optimista.append(round(monto_periodo * 0.90, 1))
            datos_realista.append(round(monto_periodo * 0.75, 1))
            datos_conservador.append(round(monto_periodo * 0.60, 1))
            
            fecha_anterior = fecha_limite
        
        # ===== AGREGAR DATOS ACUMULADOS =====
        
        acumulado_optimista = []
        acumulado_realista = []
        acumulado_conservador = []
        
        suma_opt = 0
        suma_real = 0
        suma_cons = 0
        
        for i in range(len(datos_optimista)):
            suma_opt += datos_optimista[i]
            suma_real += datos_realista[i]
            suma_cons += datos_conservador[i]
            
            acumulado_optimista.append(suma_opt)
            acumulado_realista.append(suma_real)
            acumulado_conservador.append(suma_cons)
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Escenario Optimista (90%)',
                    'data': datos_optimista,
                    'backgroundColor': 'rgba(16, 185, 129, 0.7)',
                    'borderColor': '#10B981',
                    'borderWidth': 2
                },
                {
                    'label': 'Escenario Realista (75%)',
                    'data': datos_realista,
                    'backgroundColor': 'rgba(59, 130, 246, 0.7)',
                    'borderColor': '#3B82F6',
                    'borderWidth': 2
                },
                {
                    'label': 'Escenario Conservador (60%)',
                    'data': datos_conservador,
                    'backgroundColor': 'rgba(249, 115, 22, 0.7)',
                    'borderColor': '#F59E0B',
                    'borderWidth': 2
                }
            ],
            'datos_acumulados': {
                'labels': labels,
                'optimista': acumulado_optimista,
                'realista': acumulado_realista,
                'conservador': acumulado_conservador
            },
            'resumen': {
                'total_backlog': round(df_pendientes['Monto Aprobado'].sum() / 1_000_000, 1),
                'cash_120d_realista': round(suma_real, 1),
                'riesgo_cobranza': round((suma_opt - suma_cons), 1),
                'concentracion_30d': round((datos_realista[0] / suma_real * 100), 1) if suma_real > 0 else 0
            }
        }
        
    except Exception as e:
        print(f"Error en cash forecast detallado: {e}")
        return {'labels': [], 'datasets': []}



def build_rentabilidad_simplificado(df_periodo, costs_lookup):
    """Rentabilidad por Jefe de Proyecto usando lookup de costos"""
    try:
        if not costs_lookup or 'Jefe de Proyecto' not in df_periodo.columns:
            return {'labels': ['Sin datos'], 'datasets': []}
        
        # Agrupar por Jefe de Proyecto
        rentabilidad_gestores = {}
        gestores_data = {}
        
        for gestor in df_periodo['Jefe de Proyecto'].dropna().unique():
            if pd.notna(gestor) and str(gestor).strip():
                df_gestor = df_periodo[df_periodo['Jefe de Proyecto'] == gestor]
                
                # Calcular ingresos totales del gestor
                ingresos_totales = 0
                costos_totales = 0
                proyectos_procesados = 0
                
                # Sumar todos los proyectos del gestor
                for _, row in df_gestor.iterrows():
                    proyecto_id = str(row.get('Proyecto', '')).strip()
                    ingreso_proyecto = row.get('Monto Aprobado', 0)
                    
                    # Solo contar si el estado es completado (pagado/validado)
                    if row.get('Estado', '').strip() in ['pagado', 'validado']:
                        ingresos_totales += ingreso_proyecto
                        
                        # Buscar costos del proyecto
                        if proyecto_id in costs_lookup:
                            costo_proyecto = costs_lookup[proyecto_id].get('importe_neto', 0)
                            costos_totales += costo_proyecto
                            proyectos_procesados += 1
                
                # Calcular rentabilidad solo si hay ingresos
                if ingresos_totales > 0:
                    margen = ingresos_totales - costos_totales
                    rentabilidad = (margen / ingresos_totales * 100)
                    
                    gestores_data[gestor] = {
                        'rentabilidad': rentabilidad,
                        'ingresos': ingresos_totales / 1_000_000,  # En millones
                        'margen': margen / 1_000_000,
                        'proyectos': proyectos_procesados
                    }
        
        if not gestores_data:
            return {'labels': ['Sin coincidencias'], 'datasets': []}
        
        # Ordenar por rentabilidad y tomar top 8
        top_gestores = dict(sorted(gestores_data.items(), 
                                 key=lambda x: x[1]['rentabilidad'], 
                                 reverse=True)[:8])
        
        # Generar colores basados en rentabilidad
        colores = []
        rentabilidades = []
        labels = []
        
        for gestor, data in top_gestores.items():
            rent = data['rentabilidad']
            rentabilidades.append(round(rent, 1))
            
            # Truncar nombres largos
            label = f"{gestor[:12]}..." if len(gestor) > 12 else gestor
            # Agregar info de proyectos
            label += f" ({data['proyectos']}p)"
            labels.append(label)
            
            # Colores por performance
            if rent >= 35:
                colores.append('rgba(16, 185, 129, 0.8)')  # Verde - Excelente
            elif rent >= 25:
                colores.append('rgba(34, 197, 94, 0.7)')   # Verde claro - Bueno
            elif rent >= 15:
                colores.append('rgba(59, 130, 246, 0.7)')  # Azul - Aceptable
            elif rent >= 0:
                colores.append('rgba(249, 115, 22, 0.7)')  # Naranja - Bajo
            else:
                colores.append('rgba(239, 68, 68, 0.8)')   # Rojo - Negativo
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Rentabilidad por Gestor (%)',
                    'data': rentabilidades,
                    'backgroundColor': colores,
                    'borderColor': [color.replace('0.7', '1.0').replace('0.8', '1.0') for color in colores],
                    'borderWidth': 1
                }
            ],
            'tooltip_data': {
                gestor: {
                    'rentabilidad': f"{data['rentabilidad']:.1f}%",
                    'ingresos': f"${data['ingresos']:.1f}M",
                    'margen': f"${data['margen']:.1f}M",
                    'proyectos': f"{data['proyectos']} proyectos"
                }
                for gestor, data in top_gestores.items()
            }
        }
        
    except Exception as e:
        print(f"Error en rentabilidad por gestor: {e}")
        return {'labels': [], 'datasets': []}

# ===== FUNCIONES DE UTILIDAD =====

def generar_cash_forecast(df_edp):
    """
    Genera pronóstico de cash flow basado en análisis de días de espera y distribución inteligente
    Enfoque: usar patrones históricos para distribuir el backlog en períodos realistas
    """
    try:
        hoy = datetime.now()
        
        # ===== PREPARAR Y VALIDAR DATOS =====
        df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
        df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce')
        df_edp['Días Espera'] = pd.to_numeric(df_edp['Días Espera'], errors='coerce')
        
        # Filtrar solo pendientes
        df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])].copy()
        
        if df_pendientes.empty:
            return _cash_forecast_vacio()
        
        print(f"🔍 Análisis Cash Forecast Completo:")
        print(f"   - Total registros: {len(df_edp)} EDPs")
        print(f"   - Estados únicos: {df_edp['Estado'].str.strip().unique()}")
        
        # Analizar distribución por estado
        estados_count = df_edp['Estado'].str.strip().value_counts()
        print(f"   - Distribución por estado:")
        for estado, count in estados_count.head(6).items():
            print(f"     • {estado}: {count} EDPs")
        
        # Analizar distribución completa de días de espera
        print(f"   - Análisis días espera (TODOS los EDPs):")
        print(f"     • Mínimo: {df_edp['Días Espera'].min()}")
        print(f"     • Máximo: {df_edp['Días Espera'].max()}")
        print(f"     • Promedio: {df_edp['Días Espera'].mean():.1f}")
        print(f"     • Mediana: {df_edp['Días Espera'].median():.1f}")
        
        # Ver distribución por rangos (todos los estados)
        print(f"   - Distribución general por días:")
        print(f"     • 0-30 días: {len(df_edp[df_edp['Días Espera'] <= 30])}")
        print(f"     • 31-60 días: {len(df_edp[(df_edp['Días Espera'] > 30) & (df_edp['Días Espera'] <= 60)])}")
        print(f"     • >60 días: {len(df_edp[df_edp['Días Espera'] > 60])}")
        
        # Analizar solo pendientes
        print(f"   - PENDIENTES únicamente:")
        print(f"     • Total pendientes: {len(df_pendientes)} EDPs")
        print(f"     • Días espera promedio: {df_pendientes['Días Espera'].mean():.1f}")
        print(f"     • Monto total pendiente: ${df_pendientes['Monto Aprobado'].sum() / 1_000_000:.1f}M")
        
        # ===== ESTRATEGIA DE DISTRIBUCIÓN INTELIGENTE =====
        
        total_backlog = df_pendientes['Monto Aprobado'].sum()
        
        # OPCIÓN A: Si hay distribución natural de días de espera
        df_0_30 = df_pendientes[df_pendientes['Días Espera'] <= 30]
        df_31_60 = df_pendientes[(df_pendientes['Días Espera'] > 30) & (df_pendientes['Días Espera'] <= 60)]
        df_60_plus = df_pendientes[df_pendientes['Días Espera'] > 60]
        
        monto_0_30 = df_0_30['Monto Aprobado'].sum() / 1_000_000
        monto_31_60 = df_31_60['Monto Aprobado'].sum() / 1_000_000
        monto_60_plus = df_60_plus['Monto Aprobado'].sum() / 1_000_000
        
        print(f"   - Distribución natural pendientes:")
        print(f"     • 0-30 días: {len(df_0_30)} EDPs, ${monto_0_30:.1f}M")
        print(f"     • 31-60 días: {len(df_31_60)} EDPs, ${monto_31_60:.1f}M")
        print(f"     • >60 días: {len(df_60_plus)} EDPs, ${monto_60_plus:.1f}M")
        
        # ===== DECIDIR ESTRATEGIA DE DISTRIBUCIÓN =====
        
        # Si la distribución está muy concentrada (>80% en un bucket), redistribuir
        concentracion_maxima = max(monto_0_30, monto_31_60, monto_60_plus) / (total_backlog / 1_000_000) if total_backlog > 0 else 0
        
        if concentracion_maxima > 0.8 or monto_60_plus == 0:
            print(f"   🔄 Aplicando redistribución inteligente (concentración: {concentracion_maxima:.1%})")
            
            # Usar patrones históricos o distribución típica de la industria
            total_30d, total_60d, total_90d = _aplicar_distribucion_inteligente(
                df_pendientes, total_backlog, df_edp
            )
            
            # Recalcular probabilidades basadas en la redistribución
            prob_30d, prob_60d, prob_90d = _calcular_probabilidades_redistribuidas(
                df_pendientes, total_30d, total_60d, total_90d
            )
            
        else:
            print(f"   ✅ Usando distribución natural (concentración: {concentracion_maxima:.1%})")
            
            # Usar distribución natural
            total_30d = round(monto_0_30, 1)
            total_60d = round(monto_31_60, 1)
            total_90d = round(monto_60_plus, 1)
            
            # Calcular probabilidades basadas en días de espera reales
            prob_30d = _calcular_probabilidad_30d(df_0_30)
            prob_60d = _calcular_probabilidad_60d(df_31_60)
            prob_90d = _calcular_probabilidad_90d(df_60_plus)
        
        # ===== AJUSTAR PROBABILIDADES POR CALIDAD DE CLIENTES =====
        
        if 'Cliente' in df_pendientes.columns:
            clientes_confiables = identificar_clientes_confiables(df_edp)
            
            if clientes_confiables:
                prob_30d, prob_60d, prob_90d = _ajustar_probabilidades_por_clientes(
                    df_edp, clientes_confiables, prob_30d, prob_60d, prob_90d
                )
        
        # ===== CALCULAR MÉTRICAS FINALES =====
        
        # Total ponderado por probabilidades
        total_ponderado = round(
            (total_30d * prob_30d / 100) + 
            (total_60d * prob_60d / 100) + 
            (total_90d * prob_90d / 100), 
            1
        )
        
        print(f"📊 Resultados Cash Forecast Final:")
        print(f"   - 30d: ${total_30d}M @ {prob_30d}% = ${total_30d * prob_30d / 100:.1f}M")
        print(f"   - 60d: ${total_60d}M @ {prob_60d}% = ${total_60d * prob_60d / 100:.1f}M")
        print(f"   - 90d: ${total_90d}M @ {prob_90d}% = ${total_90d * prob_90d / 100:.1f}M")
        print(f"   - Total ponderado: ${total_ponderado}M")
        print(f"   - Backlog total: ${total_backlog / 1_000_000:.1f}M")
        
        # ===== ANÁLISIS ADICIONAL DE CONCENTRACIÓN =====
        
        concentracion_info = _analizar_concentracion_por_periodo(df_pendientes, total_30d, total_60d, total_90d)
        
        # ===== ESTADÍSTICAS DE CALIDAD DEL PRONÓSTICO =====
        
        estadisticas = {
            'dias_espera_promedio': round(df_pendientes['Días Espera'].mean(), 1) if len(df_pendientes) > 0 else 0,
            'edps_criticos': len(df_pendientes[df_pendientes['Días Espera'] > 60]),
            'confianza_pronostico': round((prob_30d + prob_60d + prob_90d) / 3, 1),
            'distribucion_aplicada': 'inteligente' if concentracion_maxima > 0.8 else 'natural',
            'factor_concentracion': round(concentracion_maxima, 2),
            'volatilidad': _calcular_volatilidad_backlog(df_pendientes)
        };
        
        return {
            # Montos principales
            'total_30d': total_30d,
            'total_60d': total_60d,
            'total_90d': total_90d,
            
            # Probabilidades
            'prob_30d': prob_30d,
            'prob_60d': prob_60d,
            'prob_90d': prob_90d,
            
            # Total ponderado
            'total_ponderado': total_ponderado,
            
            # Para gráficos
            'labels': ['30 días', '60 días', '90 días'],
            'data': [total_30d, total_60d, total_90d],
            
            # Información adicional para análisis
            'concentracion_info': concentracion_info,
            'total_backlog': round(total_backlog / 1_000_000, 1),
            'edps_30d': _contar_edps_periodo(df_pendientes, 30),
            'edps_60d': _contar_edps_periodo(df_pendientes, 60),
            'edps_90d': _contar_edps_periodo(df_pendientes, 90),
            
            # Estadísticas de calidad del pronóstico
            'estadisticas': estadisticas
        }
        
    except Exception as e:
        print(f"❌ Error en generar_cash_forecast: {e}")
        import traceback
        traceback.print_exc()
        return _cash_forecast_vacio()

def _cash_forecast_vacio():
    """Retorna estructura vacía para cash forecast"""
    return {
        'total_30d': 0,
        'total_60d': 0,
        'total_90d': 0,
        'prob_30d': 85,
        'prob_60d': 75,
        'prob_90d': 60,
        'total_ponderado': 0,
        'labels': ['30 días', '60 días', '90 días'],
        'data': [0, 0, 0],
        'concentracion_info': {},
        'total_backlog': 0,
        'edps_30d': 0,
        'edps_60d': 0,
        'edps_90d': 0,
        'estadisticas': {
            'dias_espera_promedio': 0,
            'edps_criticos': 0,
            'confianza_pronostico': 73,
            'distribucion_aplicada': 'vacia',
            'factor_concentracion': 0,
            'volatilidad': 0
        }
    }

def _aplicar_distribucion_inteligente(df_pendientes, total_backlog, df_edp_completo):
    """
    Aplica distribución inteligente cuando la natural está muy concentrada
    """
    try:
        # Analizar patrones históricos de EDPs completados
        df_completados = df_edp_completo[df_edp_completo['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        if not df_completados.empty and len(df_completados) >= 10:
            # Usar patrones históricos reales
            hist_0_30 = len(df_completados[df_completados['Días Espera'] <= 30]) / len(df_completados)
            hist_31_60 = len(df_completados[(df_completados['Días Espera'] > 30) & (df_completados['Días Espera'] <= 60)]) / len(df_completados)
            hist_60_plus = len(df_completados[df_completados['Días Espera'] > 60]) / len(df_completados)
            
            print(f"   📈 Patrones históricos identificados:")
            print(f"     • 0-30d: {hist_0_30:.1%}")
            print(f"     • 31-60d: {hist_31_60:.1%}")
            print(f"     • >60d: {hist_60_plus:.1%}")
            
            # Aplicar distribución histórica al backlog actual
            factor_30d = max(0.2, min(0.6, hist_0_30))  # Entre 20% y 60%
            factor_60d = max(0.25, min(0.5, hist_31_60))  # Entre 25% y 50%
            factor_90d = max(0.1, min(0.3, hist_60_plus))  # Entre 10% y 30%
            
        else:
            # Usar distribución típica de la industria cuando no hay suficientes datos históricos
            print(f"   🏭 Aplicando distribución típica de industria")
            factor_30d = 0.35  # 35%
            factor_60d = 0.45  # 45%
            factor_90d = 0.20  # 20%
        
        # Normalizar factores para que sumen 100%
        total_factores = factor_30d + factor_60d + factor_90d
        factor_30d = factor_30d / total_factores
        factor_60d = factor_60d / total_factores
        factor_90d = factor_90d / total_factores
        
        # Aplicar distribución
        total_30d = round((total_backlog * factor_30d) / 1_000_000, 1)
        total_60d = round((total_backlog * factor_60d) / 1_000_000, 1)
        total_90d = round((total_backlog * factor_90d) / 1_000_000, 1)
        
        print(f"   🔄 Distribución inteligente aplicada:")
        print(f"     • 30d: ${total_30d}M ({factor_30d:.1%})")
        print(f"     • 60d: ${total_60d}M ({factor_60d:.1%})")
        print(f"     • 90d: ${total_90d}M ({factor_90d:.1%})")
        
        return total_30d, total_60d, total_90d
        
    except Exception as e:
        print(f"Error en distribución inteligente: {e}")
        # Fallback a distribución estándar
        total_30d = round((total_backlog * 0.35) / 1_000_000, 1)
        total_60d = round((total_backlog * 0.45) / 1_000_000, 1) 
        total_90d = round((total_backlog * 0.20) / 1_000_000, 1)
        return total_30d, total_60d, total_90d

def _calcular_probabilidades_redistribuidas(df_pendientes, total_30d, total_60d, total_90d):
    """
    Calcula probabilidades cuando se aplició redistribución inteligente
    """
    try:
        # Probabilidades base ajustadas por contexto
        dias_promedio = df_pendientes['Días Espera'].mean() if len(df_pendientes) > 0 else 45
        
        # Factor de ajuste basado en días promedio de espera
        if dias_promedio <= 25:
            # Backlog "joven" - probabilidades altas
            prob_30d = 85
            prob_60d = 75 
            prob_90d = 60
        elif dias_promedio <= 45:
            # Backlog "maduro" - probabilidades medias
            prob_30d = 75
            prob_60d = 70
            prob_90d = 55
        else:
            # Backlog "envejecido" - probabilidades bajas
            prob_30d = 65
            prob_60d = 60
            prob_90d = 45
        
        # Ajustar por concentración de montos
        total_todos = total_30d + total_60d + total_90d
        if total_todos > 0:
            concentracion_90d = total_90d / total_todos
            if concentracion_90d > 0.3:  # Si más del 30% está en 90d
                prob_90d = max(40, prob_90d - 10)  # Reducir probabilidad
        
        return prob_30d, prob_60d, prob_90d
        
    except Exception as e:
        print(f"Error calculando probabilidades redistribuidas: {e}")
        return 75, 65, 50

def _calcular_probabilidad_30d(df_30d):
    """Calcula probabilidad para bucket de 30 días"""
    if len(df_30d) == 0:
        return 85
    
    dias_promedio = df_30d['Días Espera'].mean()
    if dias_promedio <= 10:
        return 95
    elif dias_promedio <= 20:
        return 85
    else:
        return 75

def _calcular_probabilidad_60d(df_60d):
    """Calcula probabilidad para bucket de 60 días"""
    if len(df_60d) == 0:
        return 70
    
    dias_promedio = df_60d['Días Espera'].mean()
    if dias_promedio <= 40:
        return 80
    elif dias_promedio <= 50:
        return 70
    else:
        return 60

def _calcular_probabilidad_90d(df_90d):
    """Calcula probabilidad para bucket de 90+ días"""
    if len(df_90d) == 0:
        return 55
    
    dias_promedio = df_90d['Días Espera'].mean()
    if dias_promedio <= 75:
        return 65
    elif dias_promedio <= 100:
        return 50
    else:
        return 35

def _ajustar_probabilidades_por_clientes(df_pendientes, clientes_confiables, prob_30d, prob_60d, prob_90d):
    """Ajusta probabilidades basado en calidad de clientes usando data histórica completa"""
    try:
        if not clientes_confiables:
            return prob_30d, prob_60d, prob_90d
        
        # Calcular % de clientes confiables en el backlog PENDIENTE
        total_pendiente = df_pendientes['Monto Aprobado'].sum()
        monto_confiables = df_pendientes[df_pendientes['Cliente'].isin(clientes_confiables)]['Monto Aprobado'].sum()
        
        pct_confiables = (monto_confiables / total_pendiente) if total_pendiente > 0 else 0
        
        # Ajustar probabilidades basado en % de clientes confiables
        ajuste = int(pct_confiables * 15)  # Hasta 15 puntos de mejora
        
        prob_30d = min(95, prob_30d + ajuste)
        prob_60d = min(90, prob_60d + int(ajuste * 0.8))
        prob_90d = min(80, prob_90d + int(ajuste * 0.6))
        
        print(f"   ✅ Ajuste por clientes confiables: {pct_confiables:.1%} del backlog (+{ajuste} puntos)")
        
        return prob_30d, prob_60d, prob_90d
        
    except Exception as e:
        print(f"Error ajustando probabilidades por clientes: {e}")
        return prob_30d, prob_60d, prob_90d
    
def _analizar_concentracion_por_periodo(df_pendientes, total_30d, total_60d, total_90d):
    """Analiza concentración de clientes por período"""
    concentracion_info = {}
    
    try:
        if 'Cliente' not in df_pendientes.columns:
            return concentracion_info
        
        # Simular distribución por período (ya que redistribuimos)
        clientes_principales = df_pendientes.groupby('Cliente')['Monto Aprobado'].sum().nlargest(3)
        
        if len(clientes_principales) > 0:
            cliente_top = clientes_principales.index[0]
            monto_top = clientes_principales.iloc[0] / 1_000_000
            
            concentracion_info['general'] = {
                'cliente_principal': cliente_top,
                'concentracion': round((clientes_principales.iloc[0] / df_pendientes['Monto Aprobado'].sum()) * 100, 1),
                'monto_principal': round(monto_top, 1)
            }
        
        return concentracion_info
        
    except Exception as e:
        print(f"Error analizando concentración: {e}")
        return {}

def _contar_edps_periodo(df_pendientes, periodo):
    """Cuenta EDPs estimados por período"""
    try:
        if periodo == 30:
            return len(df_pendientes[df_pendientes['Días Espera'] <= 30])
        elif periodo == 60:
            return len(df_pendientes[(df_pendientes['Días Espera'] > 30) & (df_pendientes['Días Espera'] <= 60)])
        elif periodo == 90:
            return len(df_pendientes[df_pendientes['Días Espera'] > 60])
        else:
            return 0
    except:
        return 0

def _calcular_volatilidad_backlog(df_pendientes):
    """Calcula volatilidad del backlog basado en distribución de montos"""
    try:
        if len(df_pendientes) == 0:
            return 0
        
        montos = df_pendientes['Monto Aprobado']
        coef_variacion = montos.std() / montos.mean() if montos.mean() > 0 else 0
        
        # Normalizar a escala 0-100
        volatilidad = min(100, coef_variacion * 100)
        return round(volatilidad, 1)
        
    except:
        return 0


def calcular_fecha_estimada_pago(row, fecha_base):
    """Calcula fecha estimada de pago basada en días de espera y patrones"""
    try:
        dias_espera = row.get('Días Espera', 0)
        fecha_emision = row.get('Fecha Emisión', fecha_base)
        cliente = row.get('Cliente', '')
        
        # Base: fecha de emisión + días de espera + tiempo promedio de proceso
        dias_adicionales = 15  # Tiempo promedio de proceso interno
        
        # Ajustar por tipo de cliente (si tenemos información)
        if 'GOBIERNO' in str(cliente).upper() or 'MUNICIPAL' in str(cliente).upper():
            dias_adicionales += 20  # Clientes gubernamentales tardan más
        elif 'BANCO' in str(cliente).upper() or 'FINANCIERA' in str(cliente).upper():
            dias_adicionales += 5   # Clientes financieros son más rápidos
        
        # Ajustar por días de espera actuales
        if dias_espera > 60:
            dias_adicionales += 10  # Si ya lleva mucho tiempo, probablemente tardará más
        elif dias_espera < 15:
            dias_adicionales -= 5   # Si es reciente, podría ser más rápido
        
        # Calcular fecha estimada
        fecha_estimada = fecha_emision + timedelta(days=dias_espera + dias_adicionales)
        
        return fecha_estimada
        
    except Exception as e:
        print(f"Error calculando fecha estimada para fila: {e}")
        return fecha_base + timedelta(days=45)  # Default: 45 días

def identificar_clientes_confiables(df_edp):
    """Identifica clientes con buen historial de pago basado en datos históricos"""
    try:
        if 'Cliente' not in df_edp.columns:
            return []
        
        # Analizar clientes completados (pagados/validados)
        df_completados = df_edp[df_edp['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        if df_completados.empty:
            return []
        
        # Calcular métricas por cliente
        metricas_clientes = df_completados.groupby('Cliente').agg({
            'Días Espera': ['mean', 'count'],
            'Monto Aprobado': 'sum'
        }).round(2)
        
        # Aplanar columnas
        metricas_clientes.columns = ['dias_promedio', 'cantidad_edps', 'monto_total']
        
        # Filtrar clientes con historial suficiente (al menos 3 EDPs)
        clientes_con_historial = metricas_clientes[metricas_clientes['cantidad_edps'] >= 3]
        
        if clientes_con_historial.empty:
            return []
        
        # Identificar clientes confiables:
        # - Días promedio <= 45 días
        # - Al menos 3 EDPs completados
        # - Monto total significativo (top 70% del volumen)
        umbral_dias = 45
        umbral_monto = clientes_con_historial['monto_total'].quantile(0.3)  # Top 70%
        
        clientes_confiables = clientes_con_historial[
            (clientes_con_historial['dias_promedio'] <= umbral_dias) &
            (clientes_con_historial['monto_total'] >= umbral_monto)
        ].index.tolist()
        
        print(f"✅ Identificados {len(clientes_confiables)} clientes confiables: {clientes_confiables[:3]}")
        
        return clientes_confiables
        
    except Exception as e:
        print(f"Error identificando clientes confiables: {e}")
        return []
def obtener_alertas_criticas(df_edp):
    """Genera alertas críticas para el dashboard"""
    try:
        alertas = []
        
        # Preparar datos
        df_edp['Monto Aprobado'] = pd.to_numeric(df_edp['Monto Aprobado'], errors='coerce').fillna(0)
        df_edp['Días Espera'] = pd.to_numeric(df_edp['Días Espera'], errors='coerce').fillna(0)
        
        # Filtrar pendientes
        df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        if df_pendientes.empty:
            return alertas
        
        # Alerta 1: EDPs críticos (>60 días)
        edps_criticos = df_pendientes[df_pendientes['Días Espera'] > 60]
        if len(edps_criticos) > 0:
            monto_critico = edps_criticos['Monto Aprobado'].sum() / 1_000_000
            alertas.append({
                'tipo': 'critico',
                'titulo': f'{len(edps_criticos)} EDPs críticos',
                'mensaje': f'${monto_critico:.1f}M en EDPs con más de 60 días de espera',
                'icono': 'exclamation-triangle'
            })
        
        # Alerta 2: Concentración en un cliente
        if 'Cliente' in df_pendientes.columns:
            clientes_montos = df_pendientes.groupby('Cliente')['Monto Aprobado'].sum()
            if len(clientes_montos) > 0:
                cliente_principal = clientes_montos.idxmax()
                monto_principal = clientes_montos.max()
                concentracion = (monto_principal / df_pendientes['Monto Aprobado'].sum()) * 100
                
                if concentracion > 40:
                    alertas.append({
                        'tipo': 'warning',
                        'titulo': 'Alta concentración',
                        'mensaje': f'{concentracion:.1f}% del backlog en {cliente_principal}',
                        'icono': 'chart-pie'
                    })
        
        # Alerta 3: Montos pendientes altos
        monto_total_pendiente = df_pendientes['Monto Aprobado'].sum() / 1_000_000
        if monto_total_pendiente > 1000:  # Más de 1000M
            alertas.append({
                'tipo': 'info',
                'titulo': 'Backlog alto',
                'mensaje': f'${monto_total_pendiente:.1f}M en EDPs pendientes',
                'icono': 'currency-dollar'
            })
        
        return alertas[:5]  # Máximo 5 alertas
        
    except Exception as e:
        print(f"Error en obtener_alertas_criticas: {e}")
        return []
    
    
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
    
# Agregar estas funciones después de la función calcular_kpis_ejecutivos_simplificado

def calcular_kpis_anuales_reales(datos_relacionados):
    """Calcula KPIs anuales reales basados en datos de Google Sheets"""
    try:
        df_edp = datos_relacionados['df_edp']
        
        if df_edp.empty:
            return obtener_kpis_anuales_vacios()
        
        # Obtener año y mes actual
        hoy = datetime.now()
        año_actual = hoy.year
        mes_actual = hoy.month
        año_anterior = año_actual - 1
        
        print(f"📅 Calculando KPIs anuales para {año_actual} (hasta mes {mes_actual})")
        
        # Preparar fechas
        df_edp['Fecha Emisión'] = pd.to_datetime(df_edp['Fecha Emisión'], errors='coerce')
        df_edp['año'] = df_edp['Fecha Emisión'].dt.year
        df_edp['mes'] = df_edp['Fecha Emisión'].dt.month
        
        # ===== 1. INGRESOS YTD (Year To Date) =====
        # Solo EDPs cobrados (pagados/validados) en el año actual
        df_cobrados_ytd = df_edp[
            (df_edp['año'] == año_actual) & 
            (df_edp['Estado'].str.strip().isin(['pagado', 'validado']))
        ]
        
        ingresos_ytd = df_cobrados_ytd['Monto Aprobado'].sum() / 1_000_000
        
        # ===== 2. INGRESOS AÑO ANTERIOR (mismo período) =====
        # Ingresos del año anterior hasta el mismo mes
        df_cobrados_año_anterior = df_edp[
            (df_edp['año'] == año_anterior) & 
            (df_edp['mes'] <= mes_actual) &  # Hasta el mismo mes
            (df_edp['Estado'].str.strip().isin(['pagado', 'validado']))
        ]
        
        ingresos_año_anterior = df_cobrados_año_anterior['Monto Aprobado'].sum() / 1_000_000
        
        # ===== 3. META ANUAL =====
        # Calcular meta basada en tendencia histórica o usar valor fijo
        meta_anual = calcular_meta_anual_inteligente(df_edp, año_actual)
        
        # ===== 4. PROYECCIÓN ANUAL =====
        proyeccion_anual = calcular_proyeccion_anual_inteligente(
            df_edp, año_actual, mes_actual, ingresos_ytd
        )
        
        # ===== 5. MÉTRICAS ADICIONALES =====
        
        # Días restantes en el mes
        ultimo_dia_mes = hoy.replace(day=1, month=(mes_actual % 12) + 1) - timedelta(days=1) if mes_actual < 12 else hoy.replace(day=31, month=12)
        dias_restantes_mes = (ultimo_dia_mes - hoy).days
        
        # Porcentaje de cumplimiento de objetivos
        pct_cumplimiento_objetivos = calcular_cumplimiento_objetivos_mes(
            df_edp, año_actual, mes_actual, meta_anual
        )
        
        # Crecimiento vs año anterior
        crecimiento_vs_anterior = ((ingresos_ytd - ingresos_año_anterior) / ingresos_año_anterior * 100) if ingresos_año_anterior > 0 else 0
        
        # Variación vs meta
        vs_meta_ingresos = ((proyeccion_anual - meta_anual) / meta_anual * 100) if meta_anual > 0 else 0
        
        print(f"✅ KPIs anuales calculados:")
        print(f"   - YTD: ${ingresos_ytd:.1f}M")
        print(f"   - Año anterior (mismo período): ${ingresos_año_anterior:.1f}M")
        print(f"   - Meta anual: ${meta_anual:.1f}M")
        print(f"   - Proyección: ${proyeccion_anual:.1f}M")
        print(f"   - Crecimiento vs anterior: {crecimiento_vs_anterior:.1f}%")
        print(f"   - Vs meta: {vs_meta_ingresos:.1f}%")
        
        return {
            'ingresos_ytd': round(ingresos_ytd, 1),
            'meta_anual': round(meta_anual, 1),
            'proyeccion_anual': round(proyeccion_anual, 1),
            'ingresos_ano_anterior': round(ingresos_año_anterior, 1),
            'crecimiento_vs_anterior': round(crecimiento_vs_anterior, 1),
            'vs_meta_ingresos': round(vs_meta_ingresos, 1),
            'dias_restantes_mes': max(0, dias_restantes_mes),
            'pct_cumplimiento_objetivos': round(pct_cumplimiento_objetivos, 1),
            'concentracion_atraso': calcular_concentracion_atraso_real(df_edp),
            'proyectos_criticos': contar_proyectos_criticos_real(df_edp),
            'monto_pendiente_critico': calcular_monto_critico_real(df_edp),
            'dso': calcular_dso_real(df_edp),
            'concentracion_clientes': calcular_concentracion_clientes_real(df_edp),
            'costo_financiero': calcular_costo_financiero_real(df_edp)
        }
        
    except Exception as e:
        print(f"❌ Error calculando KPIs anuales reales: {e}")
        import traceback
        traceback.print_exc()
        return obtener_kpis_anuales_vacios()

def calcular_meta_anual_inteligente(df_edp, año_actual):
    """Calcula meta anual basada en tendencias históricas"""
    try:
        # Obtener ingresos completos de años anteriores
        df_edp['año'] = df_edp['Fecha Emisión'].dt.year
        
        años_completos = []
        for año in range(año_actual - 3, año_actual):  # Últimos 3 años
            df_año = df_edp[
                (df_edp['año'] == año) & 
                (df_edp['Estado'].str.strip().isin(['pagado', 'validado']))
            ]
            if len(df_año) > 0:
                ingreso_año = df_año['Monto Aprobado'].sum() / 1_000_000
                años_completos.append(ingreso_año)
        
        if len(años_completos) >= 2:
            # Calcular tendencia de crecimiento
            crecimiento_promedio = 0
            for i in range(1, len(años_completos)):
                if años_completos[i-1] > 0:
                    crecimiento = (años_completos[i] - años_completos[i-1]) / años_completos[i-1]
                    crecimiento_promedio += crecimiento
            
            crecimiento_promedio = crecimiento_promedio / (len(años_completos) - 1)
            
            # Meta = último año completo * (1 + crecimiento promedio * factor ambición)
            ultimo_año_completo = años_completos[-1]
            factor_ambicion = 1.15  # 15% más ambicioso que la tendencia
            meta_calculada = ultimo_año_completo * (1 + crecimiento_promedio * factor_ambicion)
            
            print(f"📊 Meta calculada basada en tendencia: ${meta_calculada:.1f}M")
            print(f"   - Años históricos: {años_completos}")
            print(f"   - Crecimiento promedio: {crecimiento_promedio:.1%}")
            
            return max(meta_calculada, ultimo_año_completo * 1.05)  # Mínimo 5% crecimiento
        else:
            # Fallback: usar promedio histórico + 20%
            promedio_historico = sum(años_completos) / len(años_completos) if años_completos else 250
            return promedio_historico * 1.20
            
    except Exception as e:
        print(f"Error calculando meta inteligente: {e}")
        return 250.0  # Meta por defecto

def calcular_proyeccion_anual_inteligente(df_edp, año_actual, mes_actual, ingresos_ytd):
    """Calcula proyección anual usando múltiples métodos"""
    try:
        # ===== MÉTODO 1: PROYECCIÓN LINEAL SIMPLE =====
        proyeccion_lineal = (ingresos_ytd / mes_actual) * 12 if mes_actual > 0 else ingresos_ytd
        
        # ===== MÉTODO 2: PROYECCIÓN BASADA EN TENDENCIA MENSUAL =====
        df_año_actual = df_edp[
            (df_edp['Fecha Emisión'].dt.year == año_actual) & 
            (df_edp['Estado'].str.strip().isin(['pagado', 'validado']))
        ]
        
        if len(df_año_actual) >= 3:  # Al menos 3 meses de datos
        # Agrupar por mes
            ingresos_mensuales = df_año_actual.groupby(df_año_actual['Fecha Emisión'].dt.month)['Monto Aprobado'].sum() / 1_000_000
            
            # Calcular tendencia de los últimos 3 meses
            ultimos_3_meses = ingresos_mensuales.tail(3)
            if len(ultimos_3_meses) >= 2:
                tendencia_mensual = (ultimos_3_meses.iloc[-1] - ultimos_3_meses.iloc[0]) / (len(ultimos_3_meses) - 1)
                
                # Proyectar meses restantes con tendencia
                meses_restantes = 12 - mes_actual
                ingreso_proyectado_restante = 0
                
                for i in range(meses_restantes):
                    mes_proyectado = ultimos_3_meses.iloc[-1] + (tendencia_mensual * (i + 1))
                    ingreso_proyectado_restante += max(0, mes_proyectado)  # No permitir valores negativos
                
                proyeccion_tendencia = ingresos_ytd + ingreso_proyectado_restante
            else:
                proyeccion_tendencia = proyeccion_lineal
        else:
            proyeccion_tendencia = proyeccion_lineal
        
        # ===== MÉTODO 3: PROYECCIÓN BASADA EN ESTACIONALIDAD =====
        proyeccion_estacional = calcular_proyeccion_estacional(df_edp, año_actual, mes_actual, ingresos_ytd)
        
        # ===== COMBINAR MÉTODOS =====
        # Usar promedio ponderado de los 3 métodos
        peso_lineal = 0.3
        peso_tendencia = 0.4
        peso_estacional = 0.3
        
        proyeccion_final = (
            proyeccion_lineal * peso_lineal + 
            proyeccion_tendencia * peso_tendencia + 
            proyeccion_estacional * peso_estacional
        )
        
        # ===== APLICAR FACTORES DE AJUSTE =====
        
        # Factor de conservadurismo (reducir proyección en 5-10% para ser realistas)
        factor_conservador = 0.95 if mes_actual <= 6 else 0.97  # Más conservador en primera mitad del año
        
        # Factor estacional (Q4 suele ser mejor)
        if mes_actual <= 9:  # Si estamos antes de Q4
            factor_estacional = 1.02  # Pequeño boost esperado para Q4
        else:
            factor_estacional = 1.0
        
        proyeccion_ajustada = proyeccion_final * factor_conservador * factor_estacional
        
        print(f"📈 Proyecciones calculadas:")
        print(f"   - Lineal: ${proyeccion_lineal:.1f}M")
        print(f"   - Tendencia: ${proyeccion_tendencia:.1f}M")
        print(f"   - Estacional: ${proyeccion_estacional:.1f}M")
        print(f"   - Final ajustada: ${proyeccion_ajustada:.1f}M")
        
        return max(proyeccion_ajustada, ingresos_ytd)  # La proyección no puede ser menor que YTD
        
    except Exception as e:
        print(f"Error calculando proyección inteligente: {e}")
        return ingresos_ytd * 1.1  # Fallback: YTD + 10%

def calcular_proyeccion_estacional(df_edp, año_actual, mes_actual, ingresos_ytd):
    """Calcula proyección basada en patrones estacionales históricos"""
    try:
        # Analizar patrones de años anteriores
        df_historico = df_edp[
            (df_edp['Fecha Emisión'].dt.year < año_actual) & 
            (df_edp['Estado'].str.strip().isin(['pagado', 'validado']))
        ]
        
        if df_historico.empty:
            return ingresos_ytd * (12 / mes_actual) if mes_actual > 0 else ingresos_ytd
        
        # Agrupar por año y mes
        ingresos_historicos = df_historico.groupby([
            df_historico['Fecha Emisión'].dt.year,
            df_historico['Fecha Emisión'].dt.month
        ])['Monto Aprobado'].sum() / 1_000_000
        
        # Calcular promedios mensuales históricos
        promedios_mensuales = {}
        for mes in range(1, 13):
            ingresos_mes = []
            for año in ingresos_historicos.index.get_level_values(0).unique():
                if (año, mes) in ingresos_historicos.index:
                    ingresos_mes.append(ingresos_historicos[(año, mes)])
            
            if ingresos_mes:
                promedios_mensuales[mes] = sum(ingresos_mes) / len(ingresos_mes)
            else:
                # Si no hay datos para ese mes, usar promedio general
                promedios_mensuales[mes] = ingresos_historicos.mean() if len(ingresos_historicos) > 0 else 0
        
        # Proyectar meses restantes usando promedios históricos
        ingreso_restante_proyectado = 0
        for mes in range(mes_actual + 1, 13):
            ingreso_restante_proyectado += promedios_mensuales.get(mes, 0)
        
        proyeccion_estacional = ingresos_ytd + ingreso_restante_proyectado
        
        return proyeccion_estacional
        
    except Exception as e:
        print(f"Error en proyección estacional: {e}")
        return ingresos_ytd * (12 / mes_actual) if mes_actual > 0 else ingresos_ytd

def calcular_cumplimiento_objetivos_mes(df_edp, año_actual, mes_actual, meta_anual):
    """Calcula porcentaje de cumplimiento de objetivos del mes actual"""
    try:
        # Meta mensual = meta anual / 12
        meta_mensual = meta_anual / 12
        
        # Ingresos del mes actual
        df_mes_actual = df_edp[
            (df_edp['Fecha Emisión'].dt.year == año_actual) & 
            (df_edp['Fecha Emisión'].dt.month == mes_actual) &
            (df_edp['Estado'].str.strip().isin(['pagado', 'validado']))
        ]
        
        ingresos_mes_actual = df_mes_actual['Monto Aprobado'].sum() / 1_000_000
        
        # Calcular cumplimiento del mes
        cumplimiento_mes = (ingresos_mes_actual / meta_mensual * 100) if meta_mensual > 0 else 0
        
        # Ajustar por días transcurridos del mes
        hoy = datetime.now()
        dias_transcurridos = hoy.day
        dias_totales_mes = (hoy.replace(month=hoy.month+1, day=1) - timedelta(days=1)).day if hoy.month < 12 else 31
        
        factor_dias = dias_transcurridos / dias_totales_mes
        cumplimiento_ajustado = cumplimiento_mes / factor_dias if factor_dias > 0 else cumplimiento_mes
        
        return min(100, cumplimiento_ajustado)  # Máximo 100%
        
    except Exception as e:
        print(f"Error calculando cumplimiento objetivos: {e}")
        return 75  # Valor por defecto

# ===== FUNCIONES AUXILIARES PARA KPIs ESPECÍFICOS =====

def calcular_concentracion_atraso_real(df_edp):
    """Calcula concentración real de atraso"""
    try:
        df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])]
        df_criticos = df_pendientes[df_pendientes['Días Espera'] >= 30]
        
        if df_pendientes.empty:
            return 0
        
        monto_critico = df_criticos['Monto Aprobado'].sum()
        monto_total_pendiente = df_pendientes['Monto Aprobado'].sum()
        
        return round((monto_critico / monto_total_pendiente * 100), 1) if monto_total_pendiente > 0 else 0
        
    except:
        return 45  # Valor por defecto

def contar_proyectos_criticos_real(df_edp):
    """Cuenta proyectos críticos reales"""
    try:
        df_criticos = df_edp[
            (~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])) &
            (df_edp['Días Espera'] >= 30)
        ]
        return len(df_criticos['Proyecto'].dropna().unique())
    except:
        return 3

def calcular_monto_critico_real(df_edp):
    """Calcula monto pendiente crítico real"""
    try:
        df_criticos = df_edp[
            (~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])) &
            (df_edp['Días Espera'] >= 30)
        ]
        return round(df_criticos['Monto Aprobado'].sum() / 1_000_000, 1)
    except:
        return 8.5

def calcular_dso_real(df_edp):
    """Calcula DSO real basado en datos históricos"""
    try:
        df_completados = df_edp[df_edp['Estado'].str.strip().isin(['pagado', 'validado'])]
        return round(df_completados['Días Espera'].mean(), 1) if len(df_completados) > 0 else 85
    except:
        return 85

def calcular_concentracion_clientes_real(df_edp):
    """Calcula concentración real en top 5 clientes"""
    try:
        if 'Cliente' not in df_edp.columns:
            return 65
        
        clientes_montos = df_edp.groupby('Cliente')['Monto Aprobado'].sum()
        top_5 = clientes_montos.nlargest(5)
        
        concentracion = (top_5.sum() / clientes_montos.sum() * 100) if clientes_montos.sum() > 0 else 0
        return round(concentracion, 1)
    except:
        return 65

def calcular_costo_financiero_real(df_edp):
    """Calcula costo financiero real de atrasos"""
    try:
        df_pendientes = df_edp[~df_edp['Estado'].str.strip().isin(['pagado', 'validado'])]
        
        costo_total = 0
        for _, row in df_pendientes.iterrows():
            monto = row.get('Monto Aprobado', 0)
            dias_atraso = max(0, row.get('Días Espera', 0) - META_DIAS_COBRO)
            costo_diario = monto * TASA_DIARIA
            costo_total += costo_diario * dias_atraso
        
        return round(costo_total / 1_000_000, 2)
    except:
        return 1.2

def obtener_kpis_anuales_vacios():
        """Retorna KPIs anuales vacíos"""
        return {
        'ingresos_ytd': 0,
        'meta_anual': 250.0,
        'proyeccion_anual': 0,
        'ingresos_ano_anterior': 0,
        'crecimiento_vs_anterior': 0,
        'vs_meta_ingresos': -100,
        'dias_restantes_mes': 15,
        'pct_cumplimiento_objetivos': 0,
        'concentracion_atraso': 0,
        'proyectos_criticos': 0,
        'monto_pendiente_critico': 0,
        'dso': 85,
        'concentracion_clientes': 0,
        'costo_financiero': 0
    }



# ===== PASO 4.1: AGREGAR KPIs ANUALES REALES =====
from datetime import datetime
import pandas as pd

def build_analisis_costos(df_cost):
    """Construye análisis de costos para el dashboard"""
    try:        
        if df_cost is None or df_cost.empty:
            return {'error': 'No hay datos de costos disponibles'}

        # Limpieza y conversión de columnas clave
        df_cost['project_id'] = df_cost['project_id'].astype(str).str.strip()
        df_cost['tipo_costo'] = df_cost['tipo_costo'].str.lower().fillna('opex')
        df_cost['estado_costo'] = df_cost['estado_costo'].str.lower().fillna('pendiente')
        df_cost['importe_neto'] = pd.to_numeric(df_cost['importe_neto'], errors='coerce').fillna(0)
        df_cost['proveedor'] = df_cost['proveedor'].fillna('Sin especificar')
        if 'fecha_factura' in df_cost.columns:
            df_cost['fecha_factura'] = pd.to_datetime(df_cost['fecha_factura'], errors='coerce')
        elif 'created_at' in df_cost.columns:
            df_cost['fecha_factura'] = pd.to_datetime(df_cost['created_at'], errors='coerce')
        else:
            df_cost['fecha_factura'] = pd.NaT  # o puedes omitir la columna
        df_cost = df_cost.dropna(subset=['fecha_factura'])

        # --- 1. Análisis por tipo de costo
        analisis_tipo = df_cost.groupby('tipo_costo')['importe_neto'].agg(total='sum', count='count').reset_index()
        total_costos = analisis_tipo['total'].sum()

        distribucion_tipo = {
            'labels': analisis_tipo['tipo_costo'].tolist(),
            'datasets': [{
                'data': (analisis_tipo['total'] / 1_000_000).round(2).tolist(),
                'backgroundColor': ['rgba(59, 130, 246, 0.7)', 'rgba(16, 185, 129, 0.7)'],
                'borderColor': ['rgb(59, 130, 246)', 'rgb(16, 185, 129)'],
                'borderWidth': 1
            }]
        }

        # --- 2. Estado de pagos
        analisis_estado = df_cost.groupby('estado_costo')['importe_neto'].agg(total='sum', count='count').reset_index()
        estado_pagos = {
            'labels': analisis_estado['estado_costo'].tolist(),
            'datasets': [{
                'data': (analisis_estado['total'] / 1_000_000).round(2).tolist(),
                'backgroundColor': ['rgba(34, 197, 94, 0.7)', 'rgba(234, 179, 8, 0.7)'],
                'borderColor': ['rgb(34, 197, 94)', 'rgb(234, 179, 8)'],
                'borderWidth': 1
            }]
        }

        # --- 3. Top 5 proveedores por costo total
        top_proveedores = df_cost.groupby('proveedor')['importe_neto'].sum().sort_values(ascending=True).tail(5)
        proveedores_chart = {
            'labels': top_proveedores.index.tolist(),
            'datasets': [{
                'data': (top_proveedores.values / 1_000_000).round(2).tolist(),
                'backgroundColor': [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(234, 179, 8, 0.7)',
                    'rgba(239, 68, 68, 0.7)',
                    'rgba(168, 85, 247, 0.7)'
                ]
            }]
        }

        # --- 4. Tendencia diaria
        tendencia_diaria = df_cost.groupby('fecha_factura')['importe_neto'].sum().reset_index().sort_values('fecha_factura')
        tendencia_chart = {
            'labels': tendencia_diaria['fecha_factura'].dt.strftime('%Y-%m-%d').tolist(),
            'datasets': [{
                'label': 'Costos Diarios',
                'data': (tendencia_diaria['importe_neto'] / 1_000_000).round(2).tolist(),
                'borderColor': 'rgb(59, 130, 246)',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'fill': True
            }]
        }

        # --- 5. Tendencia mensual por tipo
        df_cost['año_mes'] = df_cost['fecha_factura'].dt.strftime('%Y-%m')
        tendencia_mensual = df_cost.groupby(['año_mes', 'tipo_costo'])['importe_neto'].sum().reset_index()
        meses_unicos = sorted(tendencia_mensual['año_mes'].unique())

        datos_opex, datos_capex = [], []
        for mes in meses_unicos:
            opex = tendencia_mensual.query("año_mes == @mes and tipo_costo == 'opex'")['importe_neto'].sum()
            capex = tendencia_mensual.query("año_mes == @mes and tipo_costo == 'capex'")['importe_neto'].sum()
            datos_opex.append(round(opex / 1_000_000, 2))
            datos_capex.append(round(capex / 1_000_000, 2))

        labels_meses = [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in meses_unicos]

        tendencia_mensual_chart = {
            'labels': labels_meses,
            'datasets': [
                {
                    'label': 'OPEX',
                    'data': datos_opex,
                    'backgroundColor': 'rgba(59, 130, 246, 0.7)',
                    'borderColor': 'rgb(59, 130, 246)',
                    'borderWidth': 1
                },
                {
                    'label': 'CAPEX',
                    'data': datos_capex,
                    'backgroundColor': 'rgba(16, 185, 129, 0.7)',
                    'borderColor': 'rgb(16, 185, 129)',
                    'borderWidth': 1
                }
            ]
        }

        # --- 6. KPIs
        pagado_total = analisis_estado.query("estado_costo == 'pagado'")['total'].sum() if 'pagado' in analisis_estado['estado_costo'].values else 0
        opex_total = analisis_tipo.query("tipo_costo == 'opex'")['total'].sum() if 'opex' in analisis_tipo['tipo_costo'].values else 0

        kpis = {
            'total_costos': round(total_costos / 1_000_000, 2),
            'total_facturas': len(df_cost),
            'promedio_factura': round((total_costos / len(df_cost)) / 1_000_000, 2) if len(df_cost) > 0 else 0,
            'porcentaje_pagado': round((pagado_total / total_costos) * 100, 2) if total_costos > 0 else 0,
            'ratio_opex_capex': round((opex_total / total_costos) * 100, 2) if total_costos > 0 else 0
        }
        return {
            'distribucion_tipo': distribucion_tipo,
            'estado_pagos': estado_pagos,
            'top_proveedores': proveedores_chart,
            'tendencia_costos': tendencia_chart,
            'tendencia_mensual': tendencia_mensual_chart,
            'kpis': kpis
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'error': f'❌ Error en análisis de costos: {e}'}
