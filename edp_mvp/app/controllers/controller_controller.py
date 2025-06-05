"""
Refactored Controller Dashboard using the new layered architecture.
This controller replaces the monolithic dashboard/controller.py file.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from typing import Dict, Any, Optional, List
import traceback
from datetime import datetime, timedelta
import traceback
from ..services.kanban_service import KanbanService
from ..services.analytics_service import AnalyticsService
from ..services.edp_service import EDPService
from ..services.controller_service import ControllerService
from ..services.kpi_service import KPIService
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils
from ..extensions import socketio
import pandas as pd

class DictToObject:
    """Simple class to convert dictionaries to objects with dot notation access."""
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, DictToObject(value))
            else:
                setattr(self, key, value)

# Create Blueprint
controller_controller_bp = Blueprint("controller", __name__, url_prefix="/controller")

# Initialize services
kanban_service = KanbanService()
analytics_service = AnalyticsService()
edp_service = EDPService()
controller_service = ControllerService()
kpi_service = KPIService()



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
        'jefe_proyecto': request.args.get('jefe_proyecto', 'todos'),
        'monto_min': request.args.get('monto_min'),
        'monto_max': request.args.get('monto_max'),
        'dias_min': request.args.get('dias_min')
    }

def _get_empty_dashboard_data() -> Dict[str, Any]:
    """Get empty dashboard data for error cases"""
    empty_kpis_dict = controller_service.get_empty_kpis()
    
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


@controller_controller_bp.route("/dashboard")
def dashboard_controller():
    """
    Dashboard principal del controlador con KPIs, métricas financieras y análisis de EDPs.
    Refactorizado para usar el servicio especializado de controller manteniendo compatibilidad completa.
    """
    try:
        print("🚀 Iniciando carga del dashboard de controller...")
        
        # ===== PASO 1: OBTENER FILTROS =====
        filters = _parse_filters(request)
        print(f"📊 Filtros aplicados: {filters}")
        
        
        
        # ===== PASO 2: CARGAR DATOS CRUDOS =====
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            print(f"❌ Error cargando datos relacionados: {datos_response.message}")
            return render_template('controller/controller_dashboard.html', **_get_empty_dashboard_data())
        
        datos_relacionados = datos_response.data
        print(f"✅ Datos relacionados cargados exitosamente")
        print(f"🔍 Datos relacionados: {datos_relacionados.keys()}")
        
        # Extract raw DataFrames
        df_edp_raw = pd.DataFrame(datos_relacionados.get('edps', []))
        df_log_raw = pd.DataFrame(datos_relacionados.get('logs', []))
        
        # ===== PASO 3: Aplicar Filtros a df_edp_raw =====
      
        
        if df_edp_raw is None or df_edp_raw.empty:
            print("❌ Error: No se pudo cargar el DataFrame de EDP")
            return render_template('controller/controller_dashboard.html', **_get_empty_dashboard_data())
        
        # ===== PASO 3: PROCESAR CON EL NUEVO SERVICIO =====
        dashboard_response = controller_service.get_processed_dashboard_context(df_edp_raw, df_log_raw, filters)
        
        if not dashboard_response.success:
            print(f"❌ Error procesando dashboard: {dashboard_response.message}")
            return render_template('controller/controller_dashboard.html', **dashboard_response.data)
        
        dashboard_context = dashboard_response.data
        print(f"✅ Dashboard procesado exitosamente")
        
        # ===== PASO 4: RENDERIZAR TEMPLATE =====
        print(f"🎯 Dashboard de controller cargado exitosamente")
        return render_template('controller/controller_dashboard.html', **dashboard_context)
        
    except Exception as e:
        error_info = _handle_controller_error(e, "dashboard")
        print(f"💥 Error crítico en dashboard de controller: {error_info}")
        
        # Return default context on critical error
        try:
            default_context = controller_service._get_default_processed_context(filters if 'filters' in locals() else {})
            return render_template('controller/controller_dashboard.html', **default_context)
        except:
            return render_template('controller/controller_dashboard.html', **_get_empty_dashboard_data())
  
        
    except Exception as e:
        error_info = _handle_controller_error(e, "dashboard")
        print(f"💥 Error crítico en dashboard de controller: {error_info}")
        return render_template('controller/controller_dashboard.html', **_get_empty_dashboard_data())
    
    
@controller_controller_bp.route("/kanban")
def vista_kanban():
    """Kanban board view with filtering and real-time updates."""
    try:
        # Get filters from request
        filters = {
            "mes": request.args.get("mes"),
            "encargado": request.args.get("encargado"), 
            "cliente": request.args.get("cliente"),
            "estado_detallado": request.args.get("estado_detallado"),
            "mostrar_validados_antiguos": request.args.get("mostrar_validados_antiguos", "false").lower() == "true"
        }
        
        # Get kanban data
        kanban_response = kanban_service.get_kanban_board_data(filters)
        
        if not kanban_response.success:
            flash(f"Error loading kanban: {kanban_response.message}", "error")
            return redirect(url_for("controller.dashboard_controller"))
        
        kanban_data = kanban_response.data
        
        return render_template(
            "controller/controller_kanban.html",
            columnas=kanban_data.get('columns', {}),
            filtros=filters,
            meses=kanban_data.get('filter_options', {}).get('meses', []),
            encargados=kanban_data.get('filter_options', {}).get('encargados', []),
            clientes=kanban_data.get('filter_options', {}).get('clientes', []),
            estados_detallados=kanban_data.get('filter_options', {}).get('estados_detallados', []),
            now=datetime.now(),
            total_validados_antiguos=kanban_data.get('stats', {}).get('total_validados_antiguos', 0),
            estadisticas=kanban_data.get('stats', {})
        )
    
    except Exception as e:
        flash(f"Error al cargar tablero Kanban: {str(e)}", "error")
        return redirect(url_for("controller.dashboard_controller"))

@controller_controller_bp.route("/kanban/update_estado", methods=["POST"])
def actualizar_estado_kanban():
    """Update EDP status from kanban board."""
    try:
        edp_id = request.form.get("edp_id")
        nuevo_estado = request.form.get("nuevo_estado")
        usuario = session.get("usuario", "Kanban User")
        
        if not edp_id or not nuevo_estado:
            return jsonify({
                "success": False,
                "message": "EDP ID y nuevo estado son requeridos"
            }), 400
        
        # Update using kanban service
        update_response = kanban_service.update_edp_status(edp_id, nuevo_estado, usuario)
        
        if update_response.success:
            # Emit socket event for real-time updates
            socketio.emit("estado_actualizado", {
                "edp_id": edp_id,
                "nuevo_estado": nuevo_estado,
                "cambios": update_response.data.get('changes', {})
            })
            
            return jsonify({
                "success": True,
                "message": f"EDP {edp_id} actualizado correctamente",
                "cambios": update_response.data.get('changes', {}),
                "edp_data": update_response.data.get('edp_data', {})
            })
        else:
            return jsonify({
                "success": False,
                "message": update_response.message
            }, 400)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al actualizar: {str(e)}"
        }), 500

@controller_controller_bp.route("/kanban/update_estado_detallado", methods=["POST"])
def actualizar_estado_detallado():
    """Update EDP status with detailed information."""
    try:
        edp_id = request.form.get("edp_id")
        nuevo_estado = request.form.get("nuevo_estado")
        usuario = session.get("usuario", "Kanban Modal User")
        
        # Collect additional fields
        additional_data = {}
        if nuevo_estado == "pagado":
            additional_data["Fecha Conformidad"] = request.form.get("fecha_pago")
            additional_data["N° Conformidad"] = request.form.get("n_conformidad")
            additional_data["Conformidad Enviada"] = "Sí"
        elif nuevo_estado == "validado":
            additional_data["Fecha Estimada de Pago"] = request.form.get("fecha_estimada_pago")
            additional_data["Conformidad Enviada"] = "Sí"
        
        # Update using kanban service
        update_response = kanban_service.update_edp_status_detailed(
            edp_id, nuevo_estado, usuario, additional_data
        )
        
        if update_response.success:
            # Emit socket event for real-time updates
            socketio.emit("estado_actualizado", {
                "edp_id": edp_id,
                "nuevo_estado": nuevo_estado,
                "cambios": update_response.data.get('changes', {})
            })
            
            return jsonify({
                "success": True,
                "message": f"EDP {edp_id} actualizado correctamente con detalles adicionales"
            })
        else:
            return jsonify({
                "success": False,
                "message": update_response.message
            }, 400)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al actualizar: {str(e)}"
        }), 500

@controller_controller_bp.route("/encargado/<nombre>")
def vista_encargado(nombre):
    """Individual manager view with personal metrics."""
    try:
        # Get manager analytics
        analytics_response = analytics_service.get_manager_individual_view(nombre)
        
        if not analytics_response.success:
            flash(f"Error loading manager data: {analytics_response.message}", "error")
            return redirect(url_for("controller.dashboard_controller"))
        
        manager_data = analytics_response.data
        
        return render_template(
            "controller/controller_encargado.html",
            nombre=nombre,
            **manager_data
        )
    
    except Exception as e:
        flash(f"Error al cargar datos del encargado: {str(e)}", "error")
        return redirect(url_for("controller.dashboard_controller"))

@controller_controller_bp.route("/encargado/<nombre>/<proyecto>")
def vista_proyecto_de_encargado(nombre, proyecto):
    """Project-specific view for a manager."""
    try:
        # Get project analytics for manager
        analytics_response = analytics_service.get_manager_project_view(nombre, proyecto)
        
        if not analytics_response.success:
            flash(f"No hay EDP registrados para {nombre} en el proyecto {proyecto}", "warning")
            return redirect(url_for("controller.vista_encargado", nombre=nombre))
        
        project_data = analytics_response.data
        
        return render_template(
            "controller/controller_encargado_proyecto.html",
            nombre=nombre,
            proyecto=proyecto,
            **project_data
        )
    
    except Exception as e:
        flash(f"Error al cargar datos del proyecto: {str(e)}", "error")
        return redirect(url_for("controller.vista_encargado", nombre=nombre))

@controller_controller_bp.route("/encargados")
def vista_global_encargados():
    """Global managers view with comparative metrics."""
    try:
        # Get filters from request
        filters = {
            "mes": request.args.get("mes"),
            "cliente": request.args.get("cliente"),
            "ordenar_por": request.args.get("ordenar_por", "pagado_desc")
        }
        
        # Get global managers analytics
        analytics_response = analytics_service.get_managers_global_view(filters)
        
        if not analytics_response.success:
            flash(f"Error loading managers data: {analytics_response.message}", "error")
            return redirect(url_for("controller.dashboard_controller"))
        
        managers_data = analytics_response.data
        
        return render_template(
            "controller/controller_encargados_global.html",
            **managers_data,
            filtros=filters,
            now=datetime.now()
        )
    
    except Exception as e:
        flash(f"Error al cargar datos de encargados: {str(e)}", "error")
        return redirect(url_for("controller.dashboard_controller"))

@controller_controller_bp.route("/retrabajos")
def analisis_retrabajos():
    """Specialized dashboard for rework analysis."""
    try:
        # Get filters from request
        filters = {
            "fecha_inicio": request.args.get("fecha_inicio"),
            "fecha_fin": request.args.get("fecha_fin"),
            "proyecto": request.args.get("proyecto"),
            "encargado": request.args.get("encargado"),
            "motivo": request.args.get("motivo"),
            "tipo_falla": request.args.get("tipo_falla")
        }
        
        # Get rework analysis
        rework_response = analytics_service.get_rework_analysis(filters)
        
        if not rework_response.success:
            flash(f"Error al cargar análisis de re-trabajos: {rework_response.message}", "error")
            return redirect(url_for("controller.dashboard_controller"))
        
        rework_data = rework_response.data
        
        return render_template(
            "controller/controller_retrabajos.html",
            **rework_data,
            filtros=filters
        )
    
    except Exception as e:
        flash(f"Error al cargar el análisis de re-trabajos: {str(e)}", "error")
        return redirect(url_for("controller.dashboard_controller"))

@controller_controller_bp.route("/id/<n_edp>", methods=["GET", "POST"])
def detalle_edp(n_edp):
    """EDP detail view with editing capabilities."""
    try:
        if request.method == "GET":
            # Get EDP details
            edp_response = edp_service.get_edp_by_id(n_edp)
            
            if not edp_response.success:
                flash(f"Error al cargar EDP: {edp_response.message}", "error")
                return redirect(url_for("controller.dashboard_controller"))
            
            edp_data = edp_response.data
            
            return render_template(
                "controller/controller_edp_detalle.html",
                edp=edp_data,
                row=edp_data.get('row_index', 0)
            )
        
        elif request.method == "POST":
            # Update EDP
            form_data = request.form.to_dict()
            usuario = session.get("usuario", "Sistema")
            
            update_response = edp_service.update_edp(n_edp, form_data, usuario)
            
            if update_response.success:
                flash("EDP actualizado correctamente", "success")
                return redirect(url_for("controller.detalle_edp", n_edp=n_edp))
            else:
                flash(f"Error al actualizar EDP: {update_response.message}", "error")
                return render_template(
                    "controller/controller_edp_detalle.html",
                    edp=form_data,
                    row=0
                )
    
    except Exception as e:
        flash(f"Error inesperado: {str(e)}", "error")
        return redirect(url_for("controller.dashboard_controller"))

@controller_controller_bp.route("/log/<n_edp>")
def ver_log_edp(n_edp):
    """View EDP change log."""
    try:
        # Get EDP log
        log_response = analytics_service.get_edp_change_log(n_edp)
        
        if not log_response.success:
            flash(f"Error al cargar historial: {log_response.message}", "error")
            return redirect(url_for("controller.dashboard_controller"))
        
        log_data = log_response.data
        
        return render_template(
            "controller/controller_log_edp.html",
            n_edp=n_edp,
            **log_data
        )
    
    except Exception as e:
        flash(f"Error al cargar historial: {str(e)}", "error")
        return redirect(url_for("controller.dashboard_controller"))

@controller_controller_bp.route("/log/<n_edp>/csv")
def descargar_log_csv(n_edp):
    """Download EDP change log as CSV."""
    try:
        # Get CSV data
        csv_response = analytics_service.get_edp_log_csv(n_edp)
        
        if not csv_response.success:
            flash(f"Error al generar CSV: {csv_response.message}", "error")
            return redirect(url_for("controller.ver_log_edp", n_edp=n_edp))
        
        csv_data = csv_response.data
        
        # Create response
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename=log_edp_{n_edp}.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        
        return response
    
    except Exception as e:
        flash(f"Error al descargar CSV: {str(e)}", "error")
        return redirect(url_for("controller.ver_log_edp", n_edp=n_edp))

@controller_controller_bp.route("/issues")
def vista_issues():
    """Issues management view."""
    try:
        # Get filters from request
        filters = {
            "estado": request.args.get("estado", "todas"),
            "tipo": request.args.get("tipo", "todos"),
            "proyecto": request.args.get("proyecto", "todos"),
            "fecha_inicio": request.args.get("fecha_inicio"),
            "fecha_fin": request.args.get("fecha_fin")
        }
        
        # Get issues data using analytics service
        issues_response = analytics_service.get_issues_analysis(filters)
        
        if not issues_response.success:
            flash(f"Error al cargar incidencias: {issues_response.message}", "error")
            return redirect(url_for("controller.dashboard_controller"))
        
        issues_data = issues_response.data
        
        return render_template(
            "controller/controller_issues.html",
            **issues_data,
            filtros=filters,
            now=datetime.now()
        )
    
    except Exception as e:
        flash(f"Error al cargar incidencias: {str(e)}", "error")
        return redirect(url_for("controller.dashboard_controller"))

@controller_controller_bp.route("/issues/analisis")
def analisis_issues():
    """Issues analysis dashboard."""
    try:
        # Get comprehensive issues analysis
        analysis_response = analytics_service.get_comprehensive_issues_analysis()
        
        if not analysis_response.success:
            flash(f"Error al cargar análisis: {analysis_response.message}", "error")
            return redirect(url_for("controller.vista_issues"))
        
        analysis_data = analysis_response.data
        
        return render_template(
            "controller/controller_issues_analisis.html",
            **analysis_data
        )
    
    except Exception as e:
        flash(f"Error al cargar análisis: {str(e)}", "error")
        return redirect(url_for("controller.vista_issues"))

# === HELPER FUNCTIONS ===

def _calcular_dso_simple(registros):
    """
    Calcula DSO simple para una lista de registros (diccionarios)
    """
    if not registros:
        return 0
    
    registros_validos = []
    for r in registros:
        if r.get("Fecha Emisión") and (r.get("Fecha Pago") or r.get("Fecha Conformidad")):
            try:
                fecha_emision = datetime.strptime(str(r["Fecha Emisión"]), "%Y-%m-%d")
                fecha_final = None
                
                if r.get("Fecha Pago"):
                    fecha_final = datetime.strptime(str(r["Fecha Pago"]), "%Y-%m-%d")
                elif r.get("Fecha Conformidad"):
                    fecha_final = datetime.strptime(str(r["Fecha Conformidad"]), "%Y-%m-%d")
                
                if fecha_final:
                    dias_cobro = (fecha_final - fecha_emision).days
                    if dias_cobro >= 0:
                        registros_validos.append({
                            'dias': dias_cobro,
                            'monto': float(r.get("monto_aprobado", 0))
                        })
            except:
                continue
    
    if not registros_validos:
        return 0
    
    # Calculate weighted average
    total_monto = sum(r['monto'] for r in registros_validos)
    if total_monto == 0:
        return 0
    
    dso = sum(r['dias'] * r['monto'] for r in registros_validos) / total_monto
    return round(dso, 1)


def _calcular_variaciones_mensuales(df_full_dict, mes_actual_param, meses_disponibles, total_pagado_global, META_GLOBAL):
    """
    Calcula las variaciones de métricas respecto al mes anterior.
    """
    variaciones = {
        "meta_var_porcentaje": 0,
        "pagado_var_porcentaje": 0,
        "pendiente_var_porcentaje": 0,
        "avance_var_porcentaje": 0
    }
    
    if not meses_disponibles or len(meses_disponibles) <= 1:
        return variaciones
    
    mes_actual = mes_actual_param if mes_actual_param else max(meses_disponibles)
    mes_anterior = None
    
    if mes_actual and len(meses_disponibles) > 1:
        try:
            idx_mes_actual = meses_disponibles.index(mes_actual)
            mes_anterior = meses_disponibles[idx_mes_actual - 1] if idx_mes_actual > 0 else None
        except ValueError:
            pass
    
    if mes_anterior:
        # Filter records for previous month
        registros_mes_anterior = [r for r in df_full_dict if r.get("Mes") == mes_anterior]
        
        # Previous month metrics
        meta_mes_anterior = META_GLOBAL  # Assuming constant META_GLOBAL
        pagado_mes_anterior = sum(float(r.get("monto_aprobado", 0)) for r in registros_mes_anterior if r.get("estado") == "pagado")
        avance_mes_anterior = round(pagado_mes_anterior / meta_mes_anterior * 100, 1) if meta_mes_anterior > 0 else 0
        
        # Calculate variations
        variaciones["pagado_var_porcentaje"] = round(
            ((total_pagado_global - pagado_mes_anterior) / pagado_mes_anterior * 100) if pagado_mes_anterior else 0, 1
        )
        
        # Pending variations
        pendiente_actual = META_GLOBAL - total_pagado_global
        pendiente_anterior = meta_mes_anterior - pagado_mes_anterior
        variaciones["pendiente_var_porcentaje"] = round(
            ((pendiente_actual - pendiente_anterior) / pendiente_anterior * 100) if pendiente_anterior else 0, 1
        )
        
        # Progress variation (in percentage points)
        avance_global = round(total_pagado_global / META_GLOBAL * 100, 1) if META_GLOBAL > 0 else 0
        variaciones["avance_var_porcentaje"] = round(avance_global - avance_mes_anterior, 1)
    
    return variaciones

# API endpoints for real-time data
@controller_controller_bp.route("/api/kanban/stats")
def api_kanban_stats():
    """API endpoint for kanban statistics."""
    try:
        stats_response = kanban_service.get_kanban_statistics()
        
        if stats_response.success:
            return jsonify({
                'success': True,
                'data': stats_response.data
            })
        else:
            return jsonify({
                'success': False,
                'message': stats_response.message
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving stats: {str(e)}"
        }), 500

@controller_controller_bp.route("/api/analytics/summary")
def api_analytics_summary():
    """API endpoint for analytics summary."""
    try:
        summary_response = analytics_service.get_analytics_summary()
        
        if summary_response.success:
            return jsonify({
                'success': True,
                'data': summary_response.data
            })
        else:
            return jsonify({
                'success': False,
                'message': summary_response.message
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving summary: {str(e)}"
        }), 500
