"""
Refactored Controller Dashboard using the new layered architecture.
This controller replaces the monolithic dashboard/controller.py file.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

from ..services.kanban_service import KanbanService
from ..services.analytics_service import AnalyticsService
from ..services.edp_service import EDPService
from ..services.dashboard_service import DashboardService
from ..services.kpi_service import KPIService
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils
from ..extensions import socketio

# Create Blueprint
controller_controller_bp = Blueprint("controller", __name__, url_prefix="/controller")

# Initialize services
kanban_service = KanbanService()
analytics_service = AnalyticsService()
edp_service = EDPService()
dashboard_service = DashboardService()
kpi_service = KPIService()

@controller_controller_bp.route("/dashboard")
def dashboard_controller():
    """Main controller dashboard with KPIs, metrics and analysis."""
    try:
        # Get filters from request
        filters = {
            "mes": request.args.get("mes"),
            "encargado": request.args.get("encargado"),
            "cliente": request.args.get("cliente"),
            "estado": request.args.get("estado"),
            "estado_detallado": request.args.get("estado_detallado")
        }
        
        # Get dashboard overview data
        dashboard_response = dashboard_service.get_dashboard_overview(filters)
        
        if not dashboard_response.success:
            flash(f"Error loading dashboard: {dashboard_response.message}", "error")
            return render_template("error.html", message=dashboard_response.message)
        
        dashboard_data = dashboard_response.data
        
        # Get KPIs data
        kpis_response = kpi_service.calculate_comprehensive_kpis(filters)
        kpis_data = kpis_response.data if kpis_response.success else {}
        
        return render_template(
            "controller/controller_dashboard.html",
            # Datos base
            registros=dashboard_data.get('records', []),
            filtros=filters,
            
            # Opciones para filtros
            meses=dashboard_data.get('filter_options', {}).get('meses', []),
            encargados=dashboard_data.get('filter_options', {}).get('encargados', []),
            clientes=dashboard_data.get('filter_options', {}).get('clientes', []),
            estados_detallados=dashboard_data.get('filter_options', {}).get('estados_detallados', []),
            
            # KPIs y métricas
            **kpis_data,
            **dashboard_data.get('metrics', {}),
            
            # Datos adicionales
            chart_data=dashboard_data.get('chart_data', {}),
            recent_activity=dashboard_data.get('recent_activity', []),
            alerts=dashboard_data.get('alerts', []),
            last_updated=dashboard_data.get('last_updated')
        )
    
    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "error")
        return render_template("error.html", message="An unexpected error occurred")

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
            }), 400
    
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
            }), 400
    
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
