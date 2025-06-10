"""
Manager Controller - Refactored using the new layered architecture.
This controller replaces the monolithic dashboard/manager.py file.
"""
from flask import Blueprint, render_template, request, jsonify, session, make_response
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import traceback
import json
import pandas as pd
import os
import logging

from ..services.manager_service import ManagerService
from ..services.cashflow_service import CashFlowService
from ..services.analytics_service import AnalyticsService
from ..services.kpi_service import KPIService
from ..services.controller_service import ControllerService
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils

logger = logging.getLogger(__name__)


class DictToObject:
    """Simple class to convert dictionaries to objects with dot notation access."""
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, DictToObject(value))
            else:
                setattr(self, key, value)


# Create Blueprint
manager_controller_bp = Blueprint("manager", __name__, url_prefix="/manager")

# Initialize services
manager_service = ManagerService()
cashflow_service = CashFlowService()
analytics_service = AnalyticsService()
kpi_service = KPIService()
controller_service = ControllerService()

class ManagerControllerError(Exception):
    """Custom exception for manager controller errors"""
    pass

def _handle_controller_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Handle controller errors consistently"""
    error_msg = f"Error in manager controller{': ' + context if context else ''}: {str(error)}"
    print(f"❌ {error_msg}")
    print(f"🔍 Traceback: {traceback.format_exc()}")
    
    return {
        'error': True,
        'message': error_msg,
        'data': None
    }

def _parse_date_filters(request) -> Dict[str, Any]:
    """Parse and validate date filters from request"""
    hoy = datetime.now()
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    periodo_rapido = request.args.get('periodo_rapido')
    
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
    
    return {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'periodo_rapido': periodo_rapido
    }

def _parse_filters(request) -> Dict[str, Any]:
    """Parse all filters from request"""
    date_filters = _parse_date_filters(request)
    
    return {
        **date_filters,
        'departamento': request.args.get('departamento', 'todos'),
        'cliente': request.args.get('cliente', 'todos'),
        'estado': request.args.get('estado', 'todos'),
        'vista': request.args.get('vista', 'general'),
        'monto_min': request.args.get('monto_min'),
        'monto_max': request.args.get('monto_max'),
        'dias_min': request.args.get('dias_min')
    }

def _get_empty_dashboard_data() -> Dict[str, Any]:
    """Get empty dashboard data for error cases"""
    manager_service = ManagerService()
    empty_kpis_dict = manager_service.get_empty_kpis()
    
    return {
        'error': "Error al cargar datos",
        'kpis': DictToObject(empty_kpis_dict),  # Convert to object for dot notation
        'charts_json': "{}",
        'charts': {},
        'cash_forecast': {},
        'alertas': [],
        'fecha_inicio': None,
        'fecha_fin': None,
        'periodo_rapido': None,
        'departamento': 'todos',
        'cliente': 'todos',
        'estado': 'todos',
        'vista': 'general',
        'monto_min': None,
        'monto_max': None,
        'dias_min': None,
        'jefes_proyecto': [],
        'clientes': [],
        'rentabilidad_proyectos': [],
        'rentabilidad_clientes': [],
        'rentabilidad_gestores': [],
        'top_edps': []
    }

@manager_controller_bp.route('/dashboard')
def dashboard():
    """
    Manager Dashboard - Vista ejecutiva con KPIs, análisis financiero y proyecciones.
    Versión híbrida optimizada que combina cache inteligente con datos completos.
    """
    try:
        print("🚀 Iniciando carga del dashboard de manager (híbrido optimizado)...")
        
        # ===== PASO 1: OBTENER FILTROS =====
        filters = _parse_filters(request)
        print(f"📊 Filtros aplicados: {filters}")
        
        # ===== PASO 2: CARGAR DATOS RELACIONADOS =====
        datos_response = manager_service.load_related_data()
        if not datos_response.success:
            print(f"❌ Error cargando datos relacionados: {datos_response.message}")
            return render_template('manager/dashboard.html', **_get_empty_dashboard_data())
        
        datos_relacionados = datos_response.data
        print(f"✅ Datos relacionados cargados exitosamente")
        
        # ===== PASO 3: OBTENER DATOS DEL DASHBOARD (OPTIMIZADO CON CACHE) =====
        # Determinar el tipo de refresh necesario
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        soft_refresh = request.args.get('soft_refresh', 'false').lower() == 'true'
        
        # F5 o navegación normal debería hacer soft_refresh (actualizar solo si datos son muy viejos)
        # Parámetro refresh=true fuerza actualización completa
        # Sin parámetros usa cache si está disponible y no es muy viejo
        
        # Determinar estrategia de cache
        cache_strategy = 'use_cache'  # Default: usar cache si disponible
        
        if force_refresh:
            cache_strategy = 'force_refresh'
            print("🔄 Force refresh solicitado")
        elif soft_refresh or not request.args:
            # En F5 o navegación normal, verificar edad del cache
            cache_strategy = 'smart_refresh'
            print("🔄 Smart refresh - verificando edad del cache")
        
        dashboard_response = manager_service.get_manager_dashboard_data(
            filters=filters, 
            force_refresh=(cache_strategy == 'force_refresh'),
            max_cache_age=30 if cache_strategy == 'smart_refresh' else None  # 30 segundos para smart refresh
        )
        
        if not dashboard_response.success:
            print(f"❌ Error cargando dashboard: {dashboard_response.message}")
            return render_template('manager/dashboard.html', **_get_empty_dashboard_data())
        
        dashboard_data = dashboard_response.data
        
        # Check cache status
        is_immediate = dashboard_data.get('_is_immediate', False)
        is_cached = dashboard_data.get('_is_cached', True)
        is_stale = dashboard_data.get('_is_stale', False)
        task_id = dashboard_data.get('_task_id')
        
        print(f"✅ Dashboard data loaded - Immediate: {is_immediate}, Cached: {is_cached}, Stale: {is_stale}")
        
        # ===== PASO 4: AGREGAR DATOS ADICIONALES NECESARIOS =====
        # Estos datos no están en el cache principal, se calculan por separado para evitar invalidar cache constantemente
        
        # Obtener listas para selectores (rápido, se puede cachear separadamente)
        try:
            selectors_response = manager_service.get_selector_lists(datos_relacionados)
            if selectors_response.success:
                selectors_data = selectors_response.data
                print(f"✅ Selectores obtenidos exitosamente")
            else:
                print(f"⚠️ Warning al obtener selectores: {selectors_response.message}")
                selectors_data = {'jefes_proyecto': [], 'clientes': []}
        except Exception as e:
            print(f"⚠️ Error obteniendo selectores: {e}")
            selectors_data = {'jefes_proyecto': [], 'clientes': []}
        
        # Análisis de rentabilidad (puede ser pesado, usar cache separado)
        try:
            rentabilidad_response = manager_service.analyze_profitability(datos_relacionados, filters)
            if rentabilidad_response.success:
                rentabilidad_data = rentabilidad_response.data
                print(f"✅ Análisis de rentabilidad completado")
            else:
                print(f"⚠️ Warning en análisis de rentabilidad: {rentabilidad_response.message}")
                rentabilidad_data = {'proyectos': [], 'clientes': [], 'gestores': []}
        except Exception as e:
            print(f"⚠️ Error en análisis de rentabilidad: {e}")
            rentabilidad_data = {'proyectos': [], 'clientes': [], 'gestores': []}
        
        # Top EDPs (ligero)
        try:
            top_edps_response = manager_service.get_top_edps(datos_relacionados, limit=10)
            if top_edps_response.success:
                top_edps = top_edps_response.data
                print(f"✅ Top EDPs obtenidos: {len(top_edps)} EDPs")
            else:
                print(f"⚠️ Warning obteniendo top EDPs: {top_edps_response.message}")
                top_edps = []
        except Exception as e:
            print(f"⚠️ Error obteniendo top EDPs: {e}")
            top_edps = []
        
        # Proyecciones de cash flow adicionales (si no están en dashboard_data)
        cash_forecast = dashboard_data.get('cash_forecast', {})
        if not cash_forecast:
            try:
                cashflow_response = cashflow_service.generar_cash_forecast(filters)
                if cashflow_response.success:
                    cash_forecast = cashflow_response.data
                    print(f"✅ Proyecciones de cash flow generadas")
                else:
                    print(f"⚠️ Warning en proyecciones de cash flow: {cashflow_response.message}")
                    cash_forecast = {}
            except Exception as e:
                print(f"⚠️ Error en proyecciones de cash flow: {e}")
                cash_forecast = {}
        
        # Alertas ejecutivas
        alertas = dashboard_data.get('alerts', [])
        if not alertas:
            try:
                kpis_dict = dashboard_data.get('executive_kpis', {})
                kpis_obj = DictToObject(kpis_dict) if kpis_dict else None
                alertas = manager_service.generate_executive_alerts(
                    datos_relacionados, kpis_obj, cash_forecast
                )
                if alertas is None or not isinstance(alertas, list):
                    alertas = []
                print(f"✅ Alertas generadas: {len(alertas)} alertas")
            except Exception as e:
                print(f"⚠️ Error generando alertas: {e}")
                alertas = []
        
        # ===== PASO 5: PREPARAR DATOS PARA LA VISTA =====
        # Convert KPIs to object for dot notation access
        kpis_dict = dashboard_data.get('executive_kpis', {})
        kpis_object = DictToObject(kpis_dict)
        
        # Prepare chart data
        charts = dashboard_data.get('chart_data', {})
        charts_json = json.dumps(charts, default=str, ensure_ascii=False)
        
        # Hybrid template data combining cached dashboard data + additional live data
        template_data = {
            # Core KPIs y charts (desde cache)
            'kpis': kpis_object,
            'charts_json': charts_json,
            'charts': charts,
            'financial_metrics': dashboard_data.get('financial_metrics', {}),
            'cost_management': dashboard_data.get('cost_management', {}),
            
            # Cash flow y alertas (híbrido)
            'cash_forecast': cash_forecast,
            'alertas': alertas,
            
            # Filter state (desde request)
            'fecha_inicio': filters.get('fecha_inicio'),
            'fecha_fin': filters.get('fecha_fin'),
            'periodo_rapido': filters.get('periodo_rapido', '30'),
            'departamento': filters.get('departamento', 'todos'),
            'cliente': filters.get('cliente', 'todos'),
            'estado': filters.get('estado', 'todos'),
            'vista': filters.get('vista', 'general'),
            'monto_min': filters.get('monto_min'),
            'monto_max': filters.get('monto_max'),
            'dias_min': filters.get('dias_min'),
            
            # Filter options y selectores (adicionales)
            'jefes_proyecto': selectors_data.get('jefes_proyecto', []),
            'clientes': selectors_data.get('clientes', []),
            'departamentos': datos_relacionados.get('departamentos', []),
            
            # Performance analysis data (adicionales)
            'rentabilidad_proyectos': rentabilidad_data.get('proyectos', []),
            'rentabilidad_clientes': rentabilidad_data.get('clientes', []),
            'rentabilidad_gestores': rentabilidad_data.get('gestores', []),
            'top_edps': top_edps,
            
            # Data summary
            'data_summary': dashboard_data.get('data_summary', {}),
            
            # Cache status for frontend
            '_cache_status': {
                'is_immediate': is_immediate,
                'is_cached': is_cached,
                'is_stale': is_stale,
                'task_id': task_id,
                'refresh_url': f'/manager/dashboard/refresh?{request.query_string.decode()}'
            }
        }
        
        print("✅ Dashboard híbrido preparado exitosamente")
        return render_template('manager/dashboard.html', **template_data)
        
    except Exception as e:
        print(f"❌ Error crítico en dashboard híbrido: {str(e)}")
        traceback.print_exc()
        return render_template('manager/dashboard.html', **_get_empty_dashboard_data())


@manager_controller_bp.route('/dashboard/refresh')
def dashboard_refresh():
    """
    Force refresh dashboard data and return JSON response.
    """
    try:
        filters = _parse_filters(request)
        
        # Force refresh of dashboard data
        dashboard_response = manager_service.get_manager_dashboard_data(
            filters=filters, 
            force_refresh=True
        )
        
        if not dashboard_response.success:
            return jsonify({
                'success': False,
                'message': dashboard_response.message
            }), 500
        
        dashboard_data = dashboard_response.data
        
        return jsonify({
            'success': True,
            'data': {
                'kpis': dashboard_data.get('executive_kpis', {}),
                'charts': dashboard_data.get('chart_data', {}),
                'financial_metrics': dashboard_data.get('financial_metrics', {}),
                'cash_forecast': dashboard_data.get('cash_forecast', {}),
                'alerts': dashboard_data.get('alerts', []),
                'data_summary': dashboard_data.get('data_summary', {}),
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error refreshing dashboard: {str(e)}'
        }), 500


@manager_controller_bp.route('/dashboard/status/<task_id>')
def dashboard_task_status(task_id):
    """
    Check the status of an async dashboard calculation task.
    """
    try:
        from .. import celery
        
        task = celery.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Task is waiting...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'status': task.info.get('status', ''),
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1)
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'status': 'Task completed!',
                'result': task.result
            }
        else:  # FAILURE
            response = {
                'state': task.state,
                'status': str(task.info),
            }
            
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'state': 'ERROR',
            'status': f'Error checking task status: {str(e)}'
        }), 500

@manager_controller_bp.route('/api/critical_projects')
def api_critical_projects():
    """
    API endpoint for critical projects analysis.
    Reemplaza la función original de análisis de proyectos críticos.
    """
    """API para obtener proyectos críticos con EDP pendientes"""
    try:    
  
        # ===== PASO 2: CARGAR DATOS RELACIONADOS =====
        datos_response = manager_service.load_related_data()
        if not datos_response.success:
            print(f"❌ Error cargando datos relacionados: {datos_response.message}")
      

        # Pextraigo la lista de EDPs y la convierto en DataFrame
        lista_edps = datos_response.data.get('edps', [])

        # CONVIERTO la lista de diccionarios  en DataFrame
        df_edp = pd.DataFrame(lista_edps)

    
        df_edp['monto_aprobado'] = pd.to_numeric(df_edp['monto_aprobado'], errors='coerce')
        
        
        # Filtrar proyectos críticos (> 30 días de espera)
        df_criticos = df_edp[(df_edp['dias_espera'] >= 30) & 
                            (~df_edp['estado'].str.strip().isin(['pagado', 'validado']))].copy()
        
        
        # Agrupar por proyecto y cliente
        proyectos_criticos = []
        for (proyecto, cliente), grupo in df_criticos.groupby(['proyecto', 'cliente']):
            # Saltar si no hay datos válidos
            if pd.isnull(proyecto) or pd.isnull(cliente):
                continue
                
            jefe_proyecto = grupo['jefe_proyecto'].iloc[0] if not grupo['jefe_proyecto'].empty else "Sin asignar"
            valor_total = grupo['monto_aprobado'].sum() / 1_000_000  # Convertir a millones
            max_delay = grupo['dias_espera'].max()
            
            # Obtener EDPs relacionados
            edps_relacionados = []
            for _, row in grupo.iterrows():
                if pd.isnull(row['n_edp']):
                    continue
                    
                # Determinar estado basado en días de retraso
                estado = 'critico' if row['dias_espera'] > 30 else 'Riesgo' if row['dias_espera'] > 15 else 'Pendiente'
                
                fecha_emisión = row['fecha_emision'].strftime('%d/%m/%Y') if not pd.isnull(row['fecha_emision']) else "N/A"
                
                edps_relacionados.append({
                    'id': row['n_edp'],
                    'date': fecha_emisión,
                    'amount': round(row['monto_aprobado'] / 1_000_000, 2),  # Convertir a millones
                    'days': int(row['dias_espera']),
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
    except Exception as e:
        error_info = _handle_controller_error(e, "api_critical_projects")
        return jsonify({
            'success': False,
            'message': error_info['message'],
            'data': []
        })

@manager_controller_bp.route('/api/financial_summary')
def api_financial_summary():
    """
    API endpoint for financial summary.
    Nuevo endpoint para obtener resumen financiero ejecutivo.
    """
    try:
        # ===== OBTENER FILTROS =====
        filters = _parse_filters(request)
        
        # ===== CARGAR DATOS =====
        datos_response = manager_service.load_related_data()
        if not datos_response.success:
            return jsonify({
                'success': False,
                'message': datos_response.message,
                'data': {}
            })
        
        # ===== GENERAR RESUMEN FINANCIERO =====
        summary_response = manager_service.generate_financial_summary(
            datos_response.data, filters
        )
        
        if not summary_response.success:
            return jsonify({
                'success': False,
                'message': summary_response.message,
                'data': {}
            })
        
        return jsonify({
            'success': True,
            'message': 'Resumen financiero generado exitosamente',
            'data': summary_response.data
        })
        
    except Exception as e:
        error_info = _handle_controller_error(e, "api_financial_summary")
        return jsonify({
            'success': False,
            'message': error_info['message'],
            'data': {}
        })

@manager_controller_bp.route('/api/cash_flow_forecast')
def api_cash_flow_forecast():
    """
    API endpoint for cash flow forecast.
    Nuevo endpoint para proyecciones de flujo de caja.
    """
    try:
        # ===== OBTENER PARÁMETROS =====
        filters = _parse_filters(request)
        scenario = request.args.get('scenario', 'optimistic')
        months_ahead = int(request.args.get('months_ahead', 12))
        
        # ===== CARGAR DATOS =====
        datos_response = manager_service.load_related_data()
        if not datos_response.success:
            return jsonify({
                'success': False,
                'message': datos_response.message,
                'data': {}
            })
        
        # ===== GENERAR PROYECCIONES =====
        forecast_response = cashflow_service.generate_detailed_forecast(
            datos_response.data, filters, scenario, months_ahead
        )
        
        if not forecast_response.success:
            return jsonify({
                'success': False,
                'message': forecast_response.message,
                'data': {}
            })
        
        return jsonify({
            'success': True,
            'message': 'Proyecciones de cash flow generadas exitosamente',
            'data': forecast_response.data
        })
        
    except Exception as e:
        error_info = _handle_controller_error(e, "api_cash_flow_forecast")
        return jsonify({
            'success': False,
            'message': error_info['message'],
            'data': {}
        })

@manager_controller_bp.route('/api/profitability_analysis')
def api_profitability_analysis():
    """
    API endpoint for profitability analysis.
    Nuevo endpoint para análisis detallado de rentabilidad.
    """
    try:
        # ===== OBTENER PARÁMETROS =====
        filters = _parse_filters(request)
        analysis_type = request.args.get('type', 'projects')  # projects, clients, managers
        time_period = request.args.get('period', 'ytd')  # ytd, last_quarter, last_year
        
        # ===== CARGAR DATOS =====
        datos_response = manager_service.load_related_data()
        if not datos_response.success:
            return jsonify({
                'success': False,
                'message': datos_response.message,
                'data': {}
            })
        
        # ===== ANÁLISIS DE RENTABILIDAD =====
        profitability_response = manager_service.detailed_profitability_analysis(
            datos_response.data, filters, analysis_type, time_period
        )
        
        if not profitability_response.success:
            return jsonify({
                'success': False,
                'message': profitability_response.message,
                'data': {}
            })
        
        return jsonify({
            'success': True,
            'message': 'Análisis de rentabilidad completado exitosamente',
            'data': profitability_response.data
        })
        
    except Exception as e:
        error_info = _handle_controller_error(e, "api_profitability_analysis")
        return jsonify({
            'success': False,
            'message': error_info['message'],
            'data': {}
        })

@manager_controller_bp.route('/api/executive_alerts')
def api_executive_alerts():
    """
    API endpoint for executive alerts.
    Nuevo endpoint para alertas y notificaciones ejecutivas.
    """
    try:
        # ===== CARGAR DATOS =====
        datos_response = manager_service.load_related_data()
        if not datos_response.success:
            return jsonify({
                'success': False,
                'message': datos_response.message,
                'data': []
            })
        
        # ===== GENERAR ALERTAS =====
        alerts_response = manager_service.generate_comprehensive_alerts(
            datos_response.data
        )
        
        if not alerts_response.success:
            return jsonify({
                'success': False,
                'message': alerts_response.message,
                'data': []
            })
        
        return jsonify({
            'success': True,
            'message': 'Alertas ejecutivas generadas exitosamente',
            'data': alerts_response.data
        })
        
    except Exception as e:
        error_info = _handle_controller_error(e, "api_executive_alerts")
        return jsonify({
            'success': False,
            'message': error_info['message'],
            'data': []
        })

@manager_controller_bp.route('/api/kpis')
def api_kpis():
    """
    API endpoint for real-time KPIs data.
    Returns essential KPIs with minimal processing time.
    """
    try:
        filters = _parse_filters(request)
        
        # Try to get from cache first
        try:
            import redis
            import hashlib
            redis_url = os.getenv("REDIS_URL")
            redis_client = redis.from_url(redis_url) if redis_url else None
            
            if redis_client:
                filters_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:12]
                cache_key = f"kpis:{filters_hash}"
                cached_kpis = redis_client.get(cache_key)
                
                if cached_kpis:
                    return jsonify({
                        'success': True,
                        'data': json.loads(cached_kpis),
                        'source': 'cache',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"Cache lookup failed: {e}")
        
        # Calculate essential KPIs
        dashboard_response = manager_service._get_immediate_dashboard_data(filters)
        
        if dashboard_response and dashboard_response.success:
            kpis = dashboard_response.data.get('executive_kpis', {})
            
            return jsonify({
                'success': True,
                'data': kpis,
                'source': 'calculated',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to calculate KPIs',
                'data': manager_service.get_empty_kpis()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting KPIs: {str(e)}',
            'data': manager_service.get_empty_kpis()
        }), 500


@manager_controller_bp.route('/api/cache/status')
def api_cache_status():
    """
    API endpoint to check cache status and health.
    """
    try:
        import redis
        redis_url = os.getenv("REDIS_URL")
        redis_client = redis.from_url(redis_url) if redis_url else None
        
        if not redis_client:
            return jsonify({
                'redis_available': False,
                'message': 'Redis not configured'
            })
        
        # Get cache statistics
        info = redis_client.info()
        
        # Get our cache keys
        cache_keys = {
            'dashboard_keys': len(redis_client.keys('manager_dashboard:*')),
            'kpi_keys': len(redis_client.keys('kpis:*')),
            'chart_keys': len(redis_client.keys('charts:*')),
            'financial_keys': len(redis_client.keys('financials:*')),
        }
        
        return jsonify({
            'redis_available': True,
            'memory_usage': info.get('used_memory_human'),
            'connected_clients': info.get('connected_clients'),
            'cache_keys': cache_keys,
            'total_keys': sum(cache_keys.values()),
            'uptime': info.get('uptime_in_seconds'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'redis_available': False,
            'error': str(e)
        }), 500


@manager_controller_bp.route('/api/cache/clear')
def api_cache_clear():
    """
    API endpoint to clear specific cache patterns.
    """
    try:
        pattern = request.args.get('pattern', 'manager_dashboard:*')
        
        import redis
        redis_url = os.getenv("REDIS_URL")
        redis_client = redis.from_url(redis_url) if redis_url else None
        
        if not redis_client:
            return jsonify({
                'success': False,
                'message': 'Redis not available'
            })
        
        # Get keys matching pattern
        keys = redis_client.keys(pattern)
        cleared_count = 0
        
        if keys:
            cleared_count = redis_client.delete(*keys)
        
        return jsonify({
            'success': True,
            'cleared_count': cleared_count,
            'pattern': pattern,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error clearing cache: {str(e)}'
        }), 500


@manager_controller_bp.route('/api/performance/metrics')
def api_performance_metrics():
    """
    API endpoint for performance monitoring metrics.
    """
    try:
        # Get basic performance metrics
        start_time = datetime.now()
        
        # Test database connection speed
        db_start = datetime.now()
        edps_response = manager_service.edp_repo.find_all_dataframe()
        db_time = (datetime.now() - db_start).total_seconds()
        
        # Test cache connection speed
        cache_time = None
        try:
            import redis
            redis_url = os.getenv("REDIS_URL")
            redis_client = redis.from_url(redis_url) if redis_url else None
            
            if redis_client:
                cache_start = datetime.now()
                redis_client.ping()
                cache_time = (datetime.now() - cache_start).total_seconds()
        except Exception:
            pass
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return jsonify({
            'performance': {
                'database_query_time': round(db_time, 3),
                'cache_ping_time': round(cache_time, 3) if cache_time else None,
                'total_response_time': round(total_time, 3),
                'database_records': len(edps_response.get('data', [])) if isinstance(edps_response, dict) else 0
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@manager_controller_bp.route('/api/cache/status/dashboard')
def api_dashboard_cache_status():
    """
    API endpoint to check dashboard cache status specifically.
    """
    try:
        filters = _parse_filters(request)
        cache_status = manager_service.get_cache_status(filters)
        
        return jsonify({
            'success': True,
            'cache_status': cache_status,
            'filters': filters,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@manager_controller_bp.route('/api/cache/invalidate', methods=['POST'])
def api_invalidate_cache():
    """
    API endpoint to manually invalidate dashboard cache.
    """
    try:
        data = request.get_json() or {}
        filters = data.get('filters')
        change_type = data.get('change_type', 'general')
        
        if change_type == 'specific' and filters:
            success = manager_service.invalidate_dashboard_cache(filters)
        else:
            success = manager_service.invalidate_cache_on_data_change(change_type)
        
        return jsonify({
            'success': success,
            'message': 'Cache invalidated successfully' if success else 'Failed to invalidate cache',
            'change_type': change_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@manager_controller_bp.route('/api/cache/health', methods=['GET'])
def api_cache_health():
    """
    API endpoint to get cache health report.
    """
    try:
        from ..services.cache_invalidation_service import CacheInvalidationService
        
        cache_service = CacheInvalidationService()
        health_report = cache_service.get_cache_health_report()
        
        return jsonify({
            'success': True,
            'data': health_report,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@manager_controller_bp.route('/api/cache/auto-invalidate', methods=['POST'])
def api_auto_invalidate():
    """
    API endpoint to trigger automatic cache invalidation based on data changes.
    """
    try:
        from ..services.cache_invalidation_service import CacheInvalidationService
        
        data = request.get_json() or {}
        operation = data.get('operation', 'general_update')
        affected_ids = data.get('affected_ids', [])
        metadata = data.get('metadata', {})
        
        cache_service = CacheInvalidationService()
        success = cache_service.register_data_change(operation, affected_ids, metadata)
        
        return jsonify({
            'success': success,
            'message': f'Auto-invalidation triggered for operation: {operation}',
            'operation': operation,
            'affected_ids': affected_ids,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@manager_controller_bp.route('/webhook/data-changed', methods=['POST'])
def webhook_data_changed():
    """
    Webhook endpoint for external systems to notify about data changes.
    Can be called by Google Sheets scripts, ETL processes, etc.
    """
    try:
        data = request.get_json() or {}
        
        # Validate webhook signature/key if needed
        webhook_key = data.get('webhook_key')
        expected_key = os.getenv('CACHE_WEBHOOK_KEY', 'default_key_123')
        
        if webhook_key != expected_key:
            logger.warning(f"Invalid webhook key received: {webhook_key}")
            return jsonify({'success': False, 'error': 'Invalid webhook key'}), 401
        
        # Process the data change notification
        from ..services.cache_invalidation_service import CacheInvalidationService
        
        change_type = data.get('change_type', 'data_import')
        affected_records = data.get('affected_records', [])
        source_system = data.get('source_system', 'external')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        cache_service = CacheInvalidationService()
        success = cache_service.register_data_change(
            operation=change_type,
            affected_ids=affected_records,
            metadata={
                'source_system': source_system,
                'webhook_timestamp': timestamp,
                'external_trigger': True
            }
        )
        
        logger.info(f"✅ Webhook cache invalidation: {change_type} from {source_system}")
        
        return jsonify({
            'success': success,
            'message': f'Cache invalidation triggered from {source_system}',
            'change_type': change_type,
            'affected_records': len(affected_records),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in webhook data-changed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@manager_controller_bp.route('/api/auto-refresh/status', methods=['GET'])
def api_auto_refresh_status():
    """
    Check if auto-refresh is disabled and event-based system is active.
    """
    try:
        from ..services.cache_invalidation_service import CacheInvalidationService
        
        cache_service = CacheInvalidationService()
        health = cache_service.get_cache_health_report()
        
        status = {
            'auto_refresh_disabled': True,  # We disabled all auto-refresh timers
            'event_based_system': True,
            'redis_connected': health.get('redis_available', False),
            'cache_system_active': health.get('redis_available', False),
            'recent_invalidation_events': health.get('recent_events', 0),
            'message': 'Sistema basado en eventos activo - sin auto-refresh por tiempo',
            'last_check': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
