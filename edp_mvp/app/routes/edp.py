"""
Refactored EDP Controller using the new layered architecture.
This demonstrates how the monolithic controller can be restructured.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import login_required, current_user
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import pandas as pd
import os
import tempfile
import time
import traceback
import io

from ..services.edp_service import EDPService
from ..services.dashboard_service import ControllerService
from ..services.kpi_service import KPIService
from ..repositories.edp_repository import EDPRepository
from ..repositories.project_repository import ProjectRepository
from ..services.manager_service import ManagerService
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils
from ..models import EDP


# Create Blueprint
edp_management_bp = Blueprint("edp_management", __name__, url_prefix="/edp-management")

# Initialize services
edp_service = EDPService()
controller_service = ControllerService()
kpi_service = KPIService()
edp_repository = EDPRepository()
project_repository = ProjectRepository()
manager_service = ManagerService()

# Configuración de archivos permitidos
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Caché global para optimizar validación de duplicados
_GLOBAL_EDP_CACHE = {
    'data': {},  # {f"{n_edp}_{proyecto}": True/False}
    'last_update': 0,
    'cache_duration': 300  # 5 minutos
}


@edp_management_bp.route("/")
def index():
    """Main EDP dashboard page."""
    try:
        # Get dashboard overview data
        overview_response = controller_service.get_dashboard_overview()
        
        if not overview_response.success:
            flash(f"Error loading dashboard: {overview_response.message}", "error")
            return render_template("error.html", message=overview_response.message)
        
        dashboard_data = overview_response.data
        
        return render_template(
            "edp/dashboard.html",
            overview_metrics=dashboard_data.get('overview_metrics', {}),
            chart_data=dashboard_data.get('chart_data', {}),
            recent_activity=dashboard_data.get('recent_activity', []),
            alerts=dashboard_data.get('alerts', []),
            kpi_summary=dashboard_data.get('kpi_summary', {}),
            last_updated=dashboard_data.get('last_updated')
        )
    
    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "error")
        return render_template("error.html", message="An unexpected error occurred")


@edp_management_bp.route("/list")
@login_required
def list_edps():
    """List all EDPs with filtering and pagination."""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        search_query = request.args.get('search', '')
        
        # Get all EDPs
        edps_response = edp_service.get_all_edps()
        
        if not edps_response.success:
            flash(f"Error loading EDPs: {edps_response.message}", "error")
            return render_template("edp/list.html", edps=[], pagination=None)
        
        edps_data = edps_response.data
        
        # Apply filters
        if status_filter:
            edps_data = [edp for edp in edps_data if edp['status'] == status_filter]
        
        if priority_filter:
            edps_data = [edp for edp in edps_data if edp['priority'] == priority_filter]
        
        if search_query:
            search_lower = search_query.lower()
            edps_data = [
                edp for edp in edps_data 
                if search_lower in edp['name'].lower() 
                or search_lower in edp['responsible'].lower()
                or search_lower in edp.get('description', '').lower()
            ]
        
        # Simple pagination (in a real app, this would be done at the database level)
        total = len(edps_data)
        start = (page - 1) * per_page
        end = start + per_page
        edps_page = edps_data[start:end]
        
        # Create pagination info
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page < (total + per_page - 1) // per_page
        }
        
        return render_template(
            "edp/list.html",
            edps=edps_page,
            pagination=pagination,
            filters={
                'status': status_filter,
                'priority': priority_filter,
                'search': search_query
            }
        )
    
    except Exception as e:
        flash(f"Error loading EDPs: {str(e)}", "error")
        return render_template("edp/list.html", edps=[], pagination=None)


@edp_management_bp.route("/<edp_id>")
@login_required
def view_edp(edp_id: str):
    """View detailed information for a specific EDP."""
    try:
        # Get EDP details
        edp_response = edp_service.get_edp_by_id(edp_id)
        
        if not edp_response.success:
            flash(f"EDP not found: {edp_response.message}", "error")
            return redirect(url_for('edp_management.list_edps'))
        
        edp_data = edp_response.data
        
        # Get KPIs for this EDP
        kpi_response = kpi_service.calculate_edp_kpis(edp_id)
        kpi_data = kpi_response.data if kpi_response.success else {}
        
        # Get KPI trends
        trend_response = kpi_service.get_kpi_trends(edp_id, days=30)
        trend_data = trend_response.data if trend_response.success else {}
        
        return render_template(
            "edp/detail.html",
            edp=edp_data,
            kpis=kpi_data,
            trends=trend_data
        )
    
    except Exception as e:
        flash(f"Error loading EDP: {str(e)}", "error")
        return redirect(url_for('edp_management.list_edps'))


@edp_management_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_edp():
    """Create a new EDP."""
    if request.method == "GET":
        return render_template("edp/create.html")
    
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Add current user (in a real app, this would come from authentication)
        form_data['user'] = session.get('user', 'admin')
        
        # Validate data
        validation_result = ValidationUtils.validate_edp_data(form_data)
        
        if not validation_result['valid']:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'errors': validation_result['errors']
                }), 400
            else:
                for field, messages in validation_result['errors'].items():
                    for message in messages:
                        flash(f"{field}: {message}", "error")
                return render_template("edp/create.html", form_data=form_data)
        
        # Create EDP
        create_response = edp_service.create_edp(form_data)
        
        if create_response.success:
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': create_response.message,
                    'edp_id': create_response.data['id']
                })
            else:
                flash(create_response.message, "success")
                return redirect(url_for('edp_management.view_edp', edp_id=create_response.data['id']))
        else:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': create_response.message
                }), 400
            else:
                flash(create_response.message, "error")
                return render_template("edp/create.html", form_data=form_data)
    
    except Exception as e:
        error_message = f"Error creating EDP: {str(e)}"
        if request.is_json:
            return jsonify({'success': False, 'message': error_message}), 500
        else:
            flash(error_message, "error")
            return render_template("edp/create.html", form_data=request.form.to_dict())


@edp_management_bp.route("/<edp_id>/edit", methods=["GET", "POST"])
@login_required
def edit_edp(edp_id: str):
    """Edit an existing EDP."""
    if request.method == "GET":
        # Get EDP for editing
        edp_response = edp_service.get_edp_by_id(edp_id)
        
        if not edp_response.success:
            flash(f"EDP not found: {edp_response.message}", "error")
            return redirect(url_for('edp_management.list_edps'))
        
        return render_template("edp/edit.html", edp=edp_response.data)
    
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Add current user
        form_data['user'] = session.get('user', 'admin')
        
        # Validate data
        validation_result = ValidationUtils.validate_edp_data(form_data)
        
        if not validation_result['valid']:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'errors': validation_result['errors']
                }), 400
            else:
                for field, messages in validation_result['errors'].items():
                    for message in messages:
                        flash(f"{field}: {message}", "error")
                
                # Get EDP again for form redisplay
                edp_response = edp_service.get_edp_by_id(edp_id)
                edp_data = edp_response.data if edp_response.success else {}
                return render_template("edp/edit.html", edp=edp_data, form_data=form_data)
        
        # Update EDP
        update_response = edp_service.update_edp(edp_id, form_data)
        
        if update_response.success:
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': update_response.message,
                    'updated_fields': update_response.data.get('updated_fields', [])
                })
            else:
                flash(update_response.message, "success")
                return redirect(url_for('edp_management.view_edp', edp_id=edp_id))
        else:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': update_response.message
                }), 400
            else:
                flash(update_response.message, "error")
                
                # Get EDP again for form redisplay
                edp_response = edp_service.get_edp_by_id(edp_id)
                edp_data = edp_response.data if edp_response.success else {}
                return render_template("edp/edit.html", edp=edp_data, form_data=form_data)
    
    except Exception as e:
        error_message = f"Error updating EDP: {str(e)}"
        if request.is_json:
            return jsonify({'success': False, 'message': error_message}), 500
        else:
            flash(error_message, "error")
            return redirect(url_for('edp_management.view_edp', edp_id=edp_id))


@edp_management_bp.route("/<edp_id>/kpis", methods=["GET", "POST"])
@login_required
def manage_kpis(edp_id: str):
    """Manage KPIs for an EDP."""
    if request.method == "GET":
        # Get current KPIs
        kpi_response = kpi_service.calculate_edp_kpis(edp_id)
        
        if not kpi_response.success:
            flash(f"Error loading KPIs: {kpi_response.message}", "error")
            return redirect(url_for('edp_management.view_edp', edp_id=edp_id))
        
        return render_template("edp/kpis.html", edp_id=edp_id, kpis=kpi_response.data)
    
    try:
        # Update KPI targets
        kpi_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Convert string values to float for numeric KPIs
        numeric_kpis = ['completion_rate', 'budget_utilization', 'time_efficiency', 'quality_score']
        targets = {}
        
        for kpi_name in numeric_kpis:
            target_key = f"{kpi_name}_target"
            if target_key in kpi_data:
                try:
                    targets[kpi_name] = float(kpi_data[target_key])
                except (ValueError, TypeError):
                    pass
        
        if targets:
            update_response = kpi_service.update_kpi_targets(edp_id, targets)
            
            if update_response.success:
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': update_response.message
                    })
                else:
                    flash(update_response.message, "success")
            else:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': update_response.message
                    }), 400
                else:
                    flash(update_response.message, "error")
        
        return redirect(url_for('edp_management.manage_kpis', edp_id=edp_id))
    
    except Exception as e:
        error_message = f"Error updating KPI targets: {str(e)}"
        if request.is_json:
            return jsonify({'success': False, 'message': error_message}), 500
        else:
            flash(error_message, "error")
            return redirect(url_for('edp_management.view_edp', edp_id=edp_id))


@edp_management_bp.route("/statistics")
@login_required
def statistics():
    """View comprehensive EDP statistics."""
    try:
        # Get EDP statistics
        stats_response = edp_service.get_edp_statistics()
        
        if not stats_response.success:
            flash(f"Error loading statistics: {stats_response.message}", "error")
            return render_template("edp/statistics.html", statistics={})
        
        # Get KPI benchmarks
        benchmarks_response = kpi_service.get_kpi_benchmarks()
        benchmarks = benchmarks_response.data if benchmarks_response.success else {}
        
        # Get health scores
        health_response = dashboard_service.get_edp_health_scores()
        health_data = health_response.data if health_response.success else []
        
        return render_template(
            "edp/statistics.html",
            statistics=stats_response.data,
            benchmarks=benchmarks,
            health_scores=health_data
        )
    
    except Exception as e:
        flash(f"Error loading statistics: {str(e)}", "error")
        return render_template("edp/statistics.html", statistics={})


# API endpoints for AJAX requests
@edp_management_bp.route("/api/health-scores")
@login_required
def api_health_scores():
    """API endpoint to get health scores for all EDPs."""
    try:
        health_response = dashboard_service.get_edp_health_scores()
        
        if health_response.success:
            return jsonify({
                'success': True,
                'data': health_response.data
            })
        else:
            return jsonify({
                'success': False,
                'message': health_response.message
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving health scores: {str(e)}"
        }), 500


@edp_management_bp.route("/api/recent-activity")
@login_required
def api_recent_activity():
    """API endpoint to get recent activity."""
    try:
        limit = request.args.get('limit', 10, type=int)
        activity_response = dashboard_service.get_recent_activity(limit)
        
        if activity_response.success:
            return jsonify({
                'success': True,
                'data': activity_response.data
            })
        else:
            return jsonify({
                'success': False,
                'message': activity_response.message
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving recent activity: {str(e)}"
        }), 500


@edp_management_bp.route("/api/alerts")
@login_required
def api_alerts():
    """API endpoint to get current alerts."""
    try:
        alerts_response = dashboard_service.get_alerts_and_notifications()
        
        if alerts_response.success:
            return jsonify({
                'success': True,
                'data': alerts_response.data
            })
        else:
            return jsonify({
                'success': False,
                'message': alerts_response.message
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving alerts: {str(e)}"
        }), 500


# Template filters for formatting
@edp_management_bp.app_template_filter('format_currency')
def format_currency_filter(amount):
    """Template filter to format currency."""
    return FormatUtils.format_currency(amount)


@edp_management_bp.app_template_filter('format_percentage')
def format_percentage_filter(value):
    """Template filter to format percentage."""
    return FormatUtils.format_percentage(value)


@edp_management_bp.app_template_filter('format_date')
def format_date_filter(date_value):
    """Template filter to format dates."""
    return DateUtils.format_date(date_value)


@edp_management_bp.app_template_filter('relative_time')
def relative_time_filter(date_value):
    """Template filter to get relative time."""
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value)
        except ValueError:
            return date_value
    return DateUtils.get_relative_time_string(date_value)


@edp_management_bp.app_template_filter('status_badge')
def status_badge_filter(status):
    """Template filter to format status badge."""
    return FormatUtils.format_status_badge(status)


@edp_management_bp.app_template_filter('priority_badge')
def priority_badge_filter(priority):
    """Template filter to format priority badge."""
    return FormatUtils.format_priority_badge(priority)


@edp_management_bp.app_template_filter('health_score')
def health_score_filter(score):
    """Template filter to format health score."""
    return FormatUtils.format_health_score(score)


# === FUNCIONES DE GESTIÓN DE EDPs ===

@edp_management_bp.route('/manage')
@login_required  
def manage_edps():
    """Vista para gestionar EDPs (listar, editar, eliminar)."""
    return render_template('edp/manage.html')

@edp_management_bp.route('/manage/list', methods=['GET'])
@login_required
def manage_list_edps():
    """Endpoint para obtener lista de EDPs para gestión."""
    try:
        print("📋 Obteniendo lista de EDPs para gestión...")
        
        # Obtener todos los EDPs
        edps_response = edp_repository.find_all()
        
        if not edps_response.get('success', False):
            return jsonify({
                'success': False,
                'message': f'Error obteniendo EDPs: {edps_response.get("message", "Unknown error")}'
            }), 500
        
        edps_list = edps_response.get('data', [])
        
        # Convertir a formato de diccionario para JSON
        edps_data = []
        for edp in edps_list:
            try:
                edp_dict = {
                    'id': getattr(edp, 'id', None),
                    'n_edp': getattr(edp, 'n_edp', ''),
                    'proyecto': getattr(edp, 'proyecto', ''),
                    'cliente': getattr(edp, 'cliente', ''),
                    'gestor': getattr(edp, 'gestor', ''),
                    'jefe_proyecto': getattr(edp, 'jefe_proyecto', ''),
                    'fecha_emision': getattr(edp, 'fecha_emision', None),
                    'monto_propuesto': getattr(edp, 'monto_propuesto', 0),
                    'monto_aprobado': getattr(edp, 'monto_aprobado', None),
                    'estado': getattr(edp, 'estado', ''),
                    'observaciones': getattr(edp, 'observaciones', ''),
                    'registrado_por': getattr(edp, 'registrado_por', ''),
                    'fecha_registro': getattr(edp, 'fecha_registro', None)
                }
                
                # Formatear fechas
                if edp_dict['fecha_emision']:
                    fecha_emision = edp_dict['fecha_emision']
                    if isinstance(fecha_emision, datetime):
                        edp_dict['fecha_emision'] = fecha_emision.strftime('%Y-%m-%d')
                    else:
                        edp_dict['fecha_emision'] = str(fecha_emision)
                
                if edp_dict['fecha_registro']:
                    fecha_registro = edp_dict['fecha_registro']
                    if isinstance(fecha_registro, datetime):
                        edp_dict['fecha_registro'] = fecha_registro.strftime('%Y-%m-%d %H:%M')
                    else:
                        edp_dict['fecha_registro'] = str(fecha_registro)
                
                edps_data.append(edp_dict)
                
            except Exception as e:
                print(f"⚠️ Error procesando EDP: {str(e)}")
                continue
        
        print(f"✅ Lista de EDPs obtenida: {len(edps_data)} registros")
        
        return jsonify({
            'success': True,
            'data': edps_data,
            'total': len(edps_data)
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo lista de EDPs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@edp_management_bp.route('/manage/delete/<int:edp_id>', methods=['DELETE'])
@login_required
def delete_edp_by_id(edp_id):
    """Eliminar EDP por ID."""
    try:
        print(f"🗑️ Solicitud de eliminación de EDP ID: {edp_id}")
        
        # Eliminar EDP usando el repositorio
        result = edp_repository.delete(edp_id)
        
        if result['success']:
            print(f"✅ EDP {edp_id} eliminado exitosamente")
            return jsonify(result)
        else:
            print(f"❌ Error eliminando EDP {edp_id}: {result['message']}")
            return jsonify(result), 400
            
    except Exception as e:
        print(f"💥 Error en delete_edp: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error eliminando EDP: {str(e)}'
        }), 500

@edp_management_bp.route('/manage/delete-by-edp', methods=['POST'])
@login_required
def delete_edp_by_number():
    """Eliminar EDP por número EDP y proyecto."""
    try:
        data = request.get_json()
        
        if not data or 'n_edp' not in data:
            return jsonify({
                'success': False,
                'message': 'Número EDP requerido'
            }), 400
        
        n_edp = data['n_edp']
        proyecto = data.get('proyecto')
        
        print(f"🗑️ Solicitud de eliminación de EDP #{n_edp} (Proyecto: {proyecto or 'cualquiera'})")
        
        # Eliminar EDP usando el repositorio
        result = edp_repository.delete_by_n_edp(n_edp, proyecto)
        
        if result['success']:
            print(f"✅ EDP #{n_edp} eliminado exitosamente")
            return jsonify(result)
        else:
            print(f"❌ Error eliminando EDP #{n_edp}: {result['message']}")
            return jsonify(result), 400
            
    except Exception as e:
        print(f"💥 Error en delete_edp_by_number: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error eliminando EDP: {str(e)}'
        }), 500


# ===== FUNCIONES DE UPLOAD =====

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_edps_cache() -> Dict[str, bool]:
    """Cargar todos los EDPs en caché para validación rápida de duplicados."""
    global _GLOBAL_EDP_CACHE
    current_time = time.time()
    
    # Si el caché es reciente, devolverlo
    if (current_time - _GLOBAL_EDP_CACHE['last_update']) < _GLOBAL_EDP_CACHE['cache_duration']:
        return _GLOBAL_EDP_CACHE['data']
    
    print("🔄 Actualizando caché global de EDPs...")
    start_time = time.time()
    
    try:
        # Obtener todos los EDPs de una vez
        edps_response = edp_repository.find_all()
        if not edps_response.get('success', False):
            print(f"❌ Error obteniendo EDPs: {edps_response.get('message', 'Unknown error')}")
            return {}
        
        edps_list = edps_response.get('data', [])
        cache_data = {}
        
        # Procesar todos los EDPs y crear el caché
        for edp in edps_list:
            try:
                n_edp = str(getattr(edp, 'n_edp', '')).strip()
                proyecto = str(getattr(edp, 'proyecto', '')).strip().upper()
                
                if n_edp and proyecto:
                    cache_key = f"{n_edp}_{proyecto}"
                    cache_data[cache_key] = True
                    
            except Exception as e:
                print(f"⚠️ Error procesando EDP en caché: {str(e)}")
                continue
        
        # Actualizar caché global
        _GLOBAL_EDP_CACHE['data'] = cache_data
        _GLOBAL_EDP_CACHE['last_update'] = current_time
        
        load_time = time.time() - start_time
        print(f"✅ Caché actualizado: {len(cache_data)} EDPs en {load_time:.2f}s")
        
        return cache_data
        
    except Exception as e:
        print(f"❌ Error cargando caché de EDPs: {str(e)}")
        return {}

def check_duplicate_fast(n_edp: int, proyecto: str) -> bool:
    """Verificar duplicados usando caché global (súper rápido)."""
    cache_data = load_edps_cache()
    cache_key = f"{str(n_edp).strip()}_{str(proyecto).strip().upper()}"
    return cache_data.get(cache_key, False)


# ===== RUTAS DE UPLOAD =====

@edp_management_bp.route('/upload', methods=['GET'])
@login_required
def upload_page():
    """Página principal de carga de EDPs (masiva e individual)."""
    try:
        # Obtener opciones para el formulario
        projects_response = project_repository.find_all()
        # project_repository.find_all() devuelve una lista directamente, no un dict con 'success'
        if isinstance(projects_response, list):
            projects = [p.to_dict() if hasattr(p, 'to_dict') else p for p in projects_response]
        else:
            projects = []

        # Obtener managers (este sí puede devolver un dict con 'success')
        try:
            managers_response = manager_service.get_all_managers()
            managers = managers_response.get('data', []) if managers_response.get('success', False) else []
        except:
            managers = []

        form_options = {
            'proyectos': projects,
            'managers': managers,
            'estados': ['INICIO', 'EN_PROCESO', 'FINALIZADO', 'CANCELADO'],
            'prioridades': ['BAJA', 'MEDIA', 'ALTA', 'CRITICA']
        }
        
        return render_template('edp/upload.html', options=form_options)
        
    except Exception as e:
        print(f"❌ Error cargando página de upload: {str(e)}")
        flash(f"Error cargando página: {str(e)}", 'error')
        return render_template('edp/upload.html', options={})

@edp_management_bp.route('/upload/manual', methods=['GET', 'POST'])
@login_required
def manual_upload():
    """Vista para carga manual de EDPs individuales."""
    if request.method == 'GET':
        # Obtener opciones del formulario
        try:
            projects_response = project_repository.find_all()
            # project_repository.find_all() devuelve una lista directamente, no un dict con 'success'
            if isinstance(projects_response, list):
                projects = [p.to_dict() if hasattr(p, 'to_dict') else p for p in projects_response]
            else:
                projects = []

            # Obtener managers (este sí puede devolver un dict con 'success')
            try:
                managers_response = manager_service.get_all_managers()
                managers = managers_response.get('data', []) if managers_response.get('success', False) else []
            except:
                managers = []

            form_options = {
                'proyectos': projects,
                'managers': managers,
                'estados': ['INICIO', 'EN_PROCESO', 'FINALIZADO', 'CANCELADO'],
                'prioridades': ['BAJA', 'MEDIA', 'ALTA', 'CRITICA']
            }
            
            return render_template('edp/upload/manual.html', options=form_options)
            
        except Exception as e:
            print(f"❌ Error obteniendo opciones del formulario: {str(e)}")
            flash(f"Error cargando formulario: {str(e)}", 'error')
            return render_template('edp/upload/manual.html', options={})
    
    # POST - Procesar el formulario
    try:
        print("📝 Procesando EDP manual...")
        
        # Determinar si es JSON o form data
        is_json_request = request.is_json or request.content_type == 'application/json'
        
        if is_json_request:
            form_data = request.get_json()
        else:
            form_data = request.form.to_dict()
            
        print(f"📋 Datos del formulario (JSON: {is_json_request}): {form_data}")
        
        # Validar datos básicos
        if not form_data.get('n_edp') or not form_data.get('proyecto'):
            error_msg = 'Número EDP y Proyecto son obligatorios'
            if is_json_request:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('edp_management.manual_upload'))
        
        # Convertir n_edp a entero
        try:
            n_edp = int(form_data['n_edp'])
        except ValueError:
            error_msg = 'El número EDP debe ser un número válido'
            if is_json_request:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('edp_management.manual_upload'))
        
        # Verificar duplicados
        proyecto = form_data['proyecto'].strip()
        if check_duplicate_fast(n_edp, proyecto):
            error_msg = f'El EDP #{n_edp} ya existe para el proyecto {proyecto}'
            if is_json_request:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('edp_management.manual_upload'))
        
        # Preparar datos para guardar
        # Procesar fecha de emisión y generar mes
        try:
            fecha_emision_str = form_data.get('fecha_emision', datetime.now().strftime('%Y-%m-%d'))
            fecha_emision_dt = datetime.strptime(fecha_emision_str, '%Y-%m-%d')
            mes = fecha_emision_dt.strftime('%Y-%m')
            print(f"✅ fecha_emision y mes procesados: {fecha_emision_str}, mes: {mes}")
        except (ValueError, TypeError) as e:
            print(f"⚠️ Error procesando fecha_emision, usando fecha actual: {e}")
            fecha_emision_dt = datetime.now()
            fecha_emision_str = fecha_emision_dt.strftime('%Y-%m-%d')
            mes = fecha_emision_dt.strftime('%Y-%m')
        
        # Procesar fecha estimada de pago
        fecha_estimada_pago = form_data.get('fecha_estimada_pago')
        if fecha_estimada_pago and str(fecha_estimada_pago).strip() and str(fecha_estimada_pago).strip().lower() != 'nan':
            try:
                # Validar formato de fecha
                datetime.strptime(str(fecha_estimada_pago), '%Y-%m-%d')
                fecha_estimada_pago_final = str(fecha_estimada_pago)
                print(f"✅ fecha_estimada_pago procesada: {fecha_estimada_pago_final}")
            except ValueError:
                print("⚠️ fecha_estimada_pago inválida, calculando 30 días desde emisión")
                fecha_estimada_pago_final = (fecha_emision_dt + timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            # Calcular 30 días desde emisión si no se proporciona
            fecha_estimada_pago_final = (fecha_emision_dt + timedelta(days=30)).strftime('%Y-%m-%d')
            print(f"✅ fecha_estimada_pago calculada (30 días): {fecha_estimada_pago_final}")
        
        # Procesar gestor (None si está vacío)
        gestor = form_data.get('gestor', '')
        gestor_final = str(gestor).strip() if gestor and str(gestor).strip() != '' else None
        
        # Procesar observaciones (None si está vacío)
        observaciones = form_data.get('observaciones', '')
        observaciones_final = str(observaciones).strip() if observaciones and str(observaciones).strip() != '' else None
        
        edp_data = {
            'n_edp': str(n_edp),  # El repositorio lo convertirá a int
            'proyecto': proyecto,
            'cliente': form_data.get('cliente', ''),
            'gestor': gestor_final,  # None si está vacío
            'jefe_proyecto': form_data.get('jefe_proyecto', ''),
            'mes': mes,  # Calculado correctamente
            'fecha_emision': fecha_emision_str,  # String en formato ISO
            'fecha_envio_cliente': None,  # Se puede completar después
            'monto_propuesto': float(form_data.get('monto_propuesto', 0)) if form_data.get('monto_propuesto') else 0.0,  # El repositorio lo convertirá a int
            'monto_aprobado': float(form_data.get('monto_aprobado', 0)) if form_data.get('monto_aprobado') and str(form_data.get('monto_aprobado')).strip() else None,  # El repositorio lo convertirá a int
            'fecha_estimada_pago': fecha_estimada_pago_final,  # Calculado correctamente
            'conformidad_enviada': False,  # Booleano, no string
            'n_conformidad': '',
            'fecha_conformidad': None,
            'estado': form_data.get('estado', 'pendiente'),  # Estado por defecto
            'observaciones': observaciones_final,  # None si está vacío
            'estado_detallado': '',
            'registrado_por': current_user.username if current_user.is_authenticated else 'admin',
            'fecha_registro': datetime.now().isoformat(),  # String ISO para Supabase
            'motivo_no_aprobado': '',
            'tipo_falla': ''
        }
        
        print(f"💾 Datos a guardar: {edp_data}")
        
        # Crear objeto EDP desde el diccionario
        edp_object = EDP.from_dict(edp_data)
        print(f"🔧 Objeto EDP creado: {edp_object}")
        
        # Crear EDP
        create_result = edp_repository.create(edp_object)
        
        if create_result:
            print(f"✅ EDP #{n_edp} creado exitosamente con ID: {create_result}")
            success_msg = f'EDP #{n_edp} creado exitosamente'
            
            # Invalidar caché
            global _GLOBAL_EDP_CACHE
            _GLOBAL_EDP_CACHE['last_update'] = 0
            
            if is_json_request:
                return jsonify({
                    'success': True,
                    'message': success_msg,
                    'edp_id': create_result
                })
            else:
                flash(success_msg, 'success')
                return redirect(url_for('edp_management.manage_edps'))
        else:
            print("❌ Error creando EDP")
            error_msg = 'Error creando EDP'
            if is_json_request:
                return jsonify({'success': False, 'message': error_msg}), 500
            else:
                flash(error_msg, 'error')
                return redirect(url_for('edp_management.manual_upload'))
            
    except Exception as e:
        print(f"❌ Error en manual_upload: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        error_msg = f'Error procesando EDP: {str(e)}'
        
        if request.is_json or request.content_type == 'application/json':
            return jsonify({'success': False, 'message': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('edp_management.manual_upload'))


@edp_management_bp.route('/upload/template')
@login_required
def download_template():
    """Descargar plantilla Excel para carga masiva."""
    try:
        # Crear DataFrame con columnas requeridas
        template_data = {
            'n_edp': [1001, 1002, 1003],
            'proyecto': ['PROYECTO_A', 'PROYECTO_B', 'PROYECTO_C'],
            'cliente': ['Cliente Ejemplo 1', 'Cliente Ejemplo 2', 'Cliente Ejemplo 3'],
            'descripcion': ['Descripción ejemplo 1', 'Descripción ejemplo 2', 'Descripción ejemplo 3'],
            'monto_propuesto': [50000.00, 75000.00, 100000.00],
            'estado': ['INICIO', 'EN_PROCESO', 'FINALIZADO'],
            'prioridad': ['MEDIA', 'ALTA', 'CRITICA'],
            'responsable': ['Responsable 1', 'Responsable 2', 'Responsable 3']
        }
        
        df = pd.DataFrame(template_data)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='EDPs', index=False)
            
            # Obtener el workbook y worksheet para formatear
            workbook = writer.book
            worksheet = writer.sheets['EDPs']
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'plantilla_edps_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"❌ Error generando plantilla: {str(e)}")
        flash(f'Error generando plantilla: {str(e)}', 'error')
        return redirect(url_for('edp_management.index'))


@edp_management_bp.route('/upload/options')
@login_required
def get_form_options():
    """Obtener opciones para los campos del formulario desde la BD."""
    try:
        print("🔍 Obteniendo opciones del formulario...")
        
        # Obtener datos desde EDPs existentes para opciones del formulario
        result = edp_repository.find_all()
        print(f"🔍 Resultado de edp_repository.find_all(): {type(result)}")
        print(f"🔍 Keys del resultado: {result.keys() if isinstance(result, dict) else 'No es dict'}")
        
        # Verificar si la operación fue exitosa
        if not result or not result.get('success', False):
            print(f"❌ Error en find_all: {result.get('message', 'Unknown error') if result else 'No result'}")
            # Devolver opciones vacías si hay error
            return jsonify({
                'success': True,
                'options': {
                    'proyectos': [],
                    'clientes': [],
                    'gestores': [],
                    'jefes_proyecto': []
                },
                'projects_info': {}
            })
        
        # Extraer la lista de EDPs del resultado
        edps_list = result.get('data', [])
        print(f"🔍 EDPs extraídos: {type(edps_list)} - Cantidad: {len(edps_list) if edps_list else 0}")
        
        # Inicializar conjuntos para opciones
        proyectos = set()
        clientes = set()
        gestores = set()
        jefes_proyecto = set()
        projects_info = {}
        
        # Si hay EDPs, extraer datos
        if edps_list and len(edps_list) > 0:
            print(f"🔍 Procesando {len(edps_list)} EDPs...")
            
            for i, edp in enumerate(edps_list):
                # Los EDPs pueden ser objetos EDP o diccionarios
                if hasattr(edp, 'to_dict'):
                    # Es un objeto EDP, convertir a diccionario
                    edp_dict = edp.to_dict()
                elif isinstance(edp, dict):
                    # Ya es un diccionario
                    edp_dict = edp
                else:
                    print(f"⚠️ EDP {i+1} no es ni objeto ni diccionario: {type(edp)}")
                    continue
                
                proyecto = edp_dict.get('proyecto', '')
                cliente = edp_dict.get('cliente', '')
                gestor = edp_dict.get('gestor', '')
                jefe = edp_dict.get('jefe_proyecto', '')
                
                if i < 3:  # Mostrar solo los primeros 3 para debug
                    print(f"🔍 EDP {i+1}: proyecto='{proyecto}', cliente='{cliente}', gestor='{gestor}', jefe='{jefe}'")
                
                if proyecto:
                    proyectos.add(proyecto)
                    if proyecto not in projects_info:
                        projects_info[proyecto] = {
                            'cliente': cliente,
                            'jefe_proyecto': jefe,
                            'gestor': gestor
                        }
                
                if cliente:
                    clientes.add(cliente)
                if gestor:
                    gestores.add(gestor)
                if jefe:
                    jefes_proyecto.add(jefe)
        else:
            print("⚠️ No hay EDPs en la base de datos")
        
        # Si no hay datos de EDPs, agregar opciones básicas de ejemplo
        if not proyectos:
            print("🔧 Agregando opciones básicas de ejemplo...")
            proyectos_ejemplo = [
                'PROYECTO_DEMO_A',
                'PROYECTO_DEMO_B', 
                'PROYECTO_DEMO_C'
            ]
            clientes_ejemplo = [
                'Cliente Demo 1',
                'Cliente Demo 2',
                'Cliente Demo 3'
            ]
            gestores_ejemplo = [
                'Gestor Demo 1',
                'Gestor Demo 2'
            ]
            jefes_ejemplo = [
                'Jefe Demo 1',
                'Jefe Demo 2'
            ]
            
            proyectos.update(proyectos_ejemplo)
            clientes.update(clientes_ejemplo)
            gestores.update(gestores_ejemplo)
            jefes_proyecto.update(jefes_ejemplo)
            
            # Crear info de proyectos demo
            for i, proyecto in enumerate(proyectos_ejemplo):
                projects_info[proyecto] = {
                    'cliente': clientes_ejemplo[i % len(clientes_ejemplo)],
                    'jefe_proyecto': jefes_ejemplo[i % len(jefes_ejemplo)],
                    'gestor': gestores_ejemplo[i % len(gestores_ejemplo)]
                }
        
        final_options = {
            'proyectos': sorted(list(proyectos)),
            'clientes': sorted(list(clientes)),
            'gestores': sorted(list(gestores)),
            'jefes_proyecto': sorted(list(jefes_proyecto))
        }
        
        print(f"✅ Opciones extraídas:")
        print(f"   - Proyectos: {len(final_options['proyectos'])} ({final_options['proyectos'][:3] if final_options['proyectos'] else []})")
        print(f"   - Clientes: {len(final_options['clientes'])} ({final_options['clientes'][:3] if final_options['clientes'] else []})")
        print(f"   - Gestores: {len(final_options['gestores'])}")
        print(f"   - Jefes: {len(final_options['jefes_proyecto'])}")
        
        return jsonify({
            'success': True,
            'options': final_options,
            'projects_info': projects_info
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo opciones: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@edp_management_bp.route('/upload/validate-duplicate', methods=['POST'])
@login_required
def validate_duplicate():
    """Validar si un número EDP es duplicado."""
    try:
        data = request.get_json()
        n_edp = data.get('n_edp')
        proyecto = data.get('proyecto', '').strip()
        
        if not n_edp:
            return jsonify({
                'success': False,
                'message': 'Número EDP requerido'
            }), 400
        
        # Convertir a entero
        try:
            n_edp = int(n_edp)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Número EDP debe ser un número válido'
            }), 400
        
        # Verificar duplicado
        is_duplicate = check_duplicate_fast(n_edp, proyecto)
        
        return jsonify({
            'success': True,
            'is_duplicate': is_duplicate,
            'message': f'EDP #{n_edp} {"ya existe" if is_duplicate else "está disponible"}' + (f' para el proyecto {proyecto}' if proyecto else '')
        })
        
    except Exception as e:
        print(f"Error validando duplicado: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
