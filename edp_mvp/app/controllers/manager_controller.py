"""
Manager Controller - Refactored using the new layered architecture.
This controller replaces the monolithic dashboard/manager.py file.
"""
from flask import Blueprint, render_template, request, jsonify, session, make_response
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import traceback
import json

from ..services.manager_service import ManagerService
from ..services.cashflow_service import CashFlowService
from ..services.analytics_service import AnalyticsService
from ..services.kpi_service import KPIService
from ..services.dashboard_service import DashboardService
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils


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
dashboard_service = DashboardService()

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
        'top_edps': [],
        
        # ===== RENTABILIDAD GENERAL KPIs - VALORES POR DEFECTO =====
        'rentabilidad_general': 0,
        'tendencia_rentabilidad': 0,
        'posicion_vs_benchmark': 0,
        'vs_meta_rentabilidad': 0,
        'meta_rentabilidad': 35.0,
        'pct_meta_rentabilidad': 0,
        'mejora_eficiencia': 0,
        'eficiencia_global': 0,
        'margen_bruto_absoluto': 0,
        'costos_totales': 0,
        'ingresos_totales': 0
    }

@manager_controller_bp.route('/dashboard')
def dashboard():
    """
    Manager Dashboard - Vista ejecutiva con KPIs, análisis financiero y proyecciones.
    Reemplaza la función dashboard() monolítica original.
    """
    try:
        print("🚀 Iniciando carga del dashboard de manager...")
        
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
        
        # ===== PASO 3: OBTENER LISTAS PARA SELECTORES =====
        selectors_response = manager_service.get_selector_lists(datos_relacionados)
        if not selectors_response.success:
            print(f"⚠️ Warning al obtener listas de selectores: {selectors_response.message}")
            selectors_data = {'jefes_proyecto': [], 'clientes': []}
        else:
            selectors_data = selectors_response.data
        
        # ===== PASO 4: CALCULAR KPIs PRINCIPALES =====
        kpis_response = manager_service.calculate_executive_kpis(datos_relacionados, filters)
        if not kpis_response.success:
            print(f"❌ Error calculando KPIs: {kpis_response.message}")
            kpis_dict = manager_service.get_empty_kpis()
        else:
            kpis_dict = kpis_response.data
            print(f"✅ KPIs calculados: {len(kpis_dict)} métricas")
        
        # Convert KPIs dictionary to object for dot notation access in template
        kpis = DictToObject(kpis_dict)
        

        # ===== PASO 5: GENERAR GRÁFICOS =====
        charts_response = manager_service.generate_executive_charts(datos_relacionados, filters)
        if not charts_response.success:
            print(f"❌ Error generando gráficos: {charts_response.message}")
            charts = {}
            charts_json = "{}"
        else:
            charts = charts_response.data
            charts_json = FormatUtils.to_json_safe(charts)
            print(f"✅ Gráficos generados: {len(charts)} charts")
        
        # ===== PASO 6: ANÁLISIS DE RENTABILIDAD =====
        rentabilidad_response = manager_service.analyze_profitability(datos_relacionados, filters)
        if not rentabilidad_response.success:
            print(f"⚠️ Warning en análisis de rentabilidad: {rentabilidad_response.message}")
            rentabilidad_data = {
                'proyectos': [],
                'clientes': [],
                'gestores': []
            }
        else:
            rentabilidad_data = rentabilidad_response.data
            print(f"✅ Análisis de rentabilidad completado")
        
        # ===== PASO 7: TOP EDPs =====
        top_edps_response = manager_service.get_top_edps(datos_relacionados, limit=10)
        if not top_edps_response.success:
            print(f"⚠️ Warning obteniendo top EDPs: {top_edps_response.message}")
            top_edps = []
        else:
            top_edps = top_edps_response.data
            print(f"✅ Top EDPs obtenidos: {len(top_edps)} EDPs")
        
        # ===== PASO 8: PROYECCIONES DE CASH FLOW =====
        cashflow_response = cashflow_service.generar_cash_forecast(filters)
        if not cashflow_response.success:
            print(f"⚠️ Warning en proyecciones de cash flow: {cashflow_response.message}")
            cash_forecast = {}
        else:
            cash_forecast = cashflow_response.data
            print(f"✅ Proyecciones de cash flow generadas")
        
        # ===== PASO 9: ALERTAS EJECUTIVAS =====
        alertas_response = manager_service.generate_executive_alerts(
            datos_relacionados, kpis, cash_forecast
        )
        if not alertas_response.success:
            print(f"⚠️ Warning generando alertas: {alertas_response.message}")
            alertas = []
        else:
            alertas = alertas_response.data
            print(f"✅ Alertas generadas: {len(alertas)} alertas")
        
        # ===== PASO 10: PREPARAR CONTEXTO PARA TEMPLATE =====
        template_context = {
            'kpis': kpis,
            'charts': charts,
            'charts_json': charts_json,
            'cash_forecast': cash_forecast,
            'alertas': alertas,
            'top_edps': top_edps,
            'jefes_proyecto': selectors_data.get('jefes_proyecto', []),
            'clientes': selectors_data.get('clientes', []),
            'rentabilidad_proyectos': rentabilidad_data.get('proyectos', []),
            'rentabilidad_clientes': rentabilidad_data.get('clientes', []),
            'rentabilidad_gestores': rentabilidad_data.get('gestores', []),
            
            # ===== RENTABILIDAD GENERAL KPIs - USING REAL COST DATA =====
            'rentabilidad_general': kpis_dict.get('rentabilidad_general', 0),  # Real profitability using cost data
            'tendencia_rentabilidad': kpis_dict.get('tendencia_rentabilidad', 0),  # Trend
            'posicion_vs_benchmark': kpis_dict.get('posicion_vs_benchmark', 0),  # Benchmark comparison
            'vs_meta_rentabilidad': kpis_dict.get('vs_meta_rentabilidad', 0),  # Real vs target
            'meta_rentabilidad': kpis_dict.get('meta_rentabilidad', 35.0),  # Target profitability percentage
            'pct_meta_rentabilidad': kpis_dict.get('pct_meta_rentabilidad', 0),  # Real percentage of target achieved
            'mejora_eficiencia': kpis_dict.get('mejora_eficiencia', 0),  # Efficiency improvement
            'eficiencia_global': kpis_dict.get('eficiencia_global', 0),  # Global efficiency
            'margen_bruto_absoluto': kpis_dict.get('margen_bruto_absoluto', 0),  # Real gross margin
            'costos_totales': kpis_dict.get('costos_totales', 0),  # Real total costs
            'ingresos_totales': kpis_dict.get('ingresos_totales', 0),  # Total revenue
            
            # Filtros aplicados (para mantener estado en formularios)
            **filters
        }
        
        print(f"🎯 Dashboard de manager cargado exitosamente")
        return render_template('manager/dashboard.html', **template_context)
        
    except Exception as e:
        error_info = _handle_controller_error(e, "dashboard")
        print(f"💥 Error crítico en dashboard de manager: {error_info}")
        return render_template('manager/dashboard.html', **_get_empty_dashboard_data())

@manager_controller_bp.route('/api/critical_projects')
def api_critical_projects():
    """
    API endpoint for critical projects analysis.
    Reemplaza la función original de análisis de proyectos críticos.
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
                'data': []
            })
        
        # ===== ANALIZAR PROYECTOS CRÍTICOS =====
        critical_response = manager_service.analyze_critical_projects(
            datos_response.data, filters
        )
        
        if not critical_response.success:
            return jsonify({
                'success': False,
                'message': critical_response.message,
                'data': []
            })
        
        return jsonify({
            'success': True,
            'message': 'Proyectos críticos analizados exitosamente',
            'data': critical_response.data
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

# Error handlers for the blueprint
@manager_controller_bp.errorhandler(ManagerControllerError)
def handle_manager_controller_error(error):
    """Handle custom manager controller errors"""
    return jsonify({
        'success': False,
        'message': str(error),
        'data': None
    }), 400

@manager_controller_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors"""
    return jsonify({
        'success': False,
        'message': 'Error interno del servidor en controlador de manager',
        'data': None
    }), 500
