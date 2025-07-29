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
edp_management_bp = Blueprint("edp_management", __name__, url_prefix="/edp")

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
            'estado': form_data.get('estado', 'revisión'),  # Estado por defecto
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

@edp_management_bp.route('/upload/bulk', methods=['POST'])
@login_required
def bulk_upload():
    """Carga masiva de EDPs desde archivo Excel/CSV."""
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        # Verificar extensión y tamaño
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Tipo de archivo no permitido. Use .xlsx, .xls o .csv'
            }), 400
        
        # Leer archivo
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error leyendo archivo: {str(e)}'
            }), 400
        
        # Validar estructura del archivo
        validation_result = validate_bulk_data(df)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'message': 'Estructura de archivo inválida',
                'errors': validation_result['errors']
            }), 400
        
        # Procesar datos en lotes para mejor rendimiento
        results = process_bulk_upload(df, session.get('user', 'admin'))
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error procesando archivo: {str(e)}'
        }), 500

def process_bulk_upload(df: pd.DataFrame, user: str) -> Dict[str, Any]:
    """Procesar carga masiva de EDPs con optimización de rendimiento."""
    success_count = 0
    error_count = 0
    errors = []
    batch_size = 100  # Aumentar tamaño de lote para mejor rendimiento
    
    try:
        # Preparar datos para inserción masiva
        valid_edps = []
        
        for idx, row in df.iterrows():
            try:
                # Preparar datos de la fila
                row_data = row.to_dict()
                row_data['registrado_por'] = user
                row_data['fecha_registro'] = datetime.now()
                
                # Validar fila individual
                validation = validate_edp_data(row_data)
                if not validation['valid']:
                    error_count += 1
                    errors.append({
                        'row': idx + 2,
                        'errors': validation['errors']
                    })
                    continue
                
                # Preparar datos y crear modelo
                edp_data = prepare_edp_data(row_data)
                edp = EDP.from_dict(edp_data)
                valid_edps.append(edp)
                
            except Exception as e:
                error_count += 1
                errors.append({
                    'row': idx + 2,
                    'error': str(e)
                })
        
        # Inserción masiva optimizada por lotes
        for i in range(0, len(valid_edps), batch_size):
            batch = valid_edps[i:i + batch_size]
            try:
                # Usar inserción masiva optimizada
                result = edp_repository.create_bulk(batch)
                if result['success']:
                    success_count += len(batch)
                else:
                    error_count += len(batch)
                    errors.append({
                        'batch': f'{i+1}-{i+len(batch)}',
                        'error': result['message']
                    })
            except Exception as e:
                error_count += len(batch)
                errors.append({
                    'batch': f'{i+1}-{i+len(batch)}',
                    'error': str(e)
                })
        
        # Limpiar caché de EDPs después del procesamiento masivo
        if success_count > 0:
            global _GLOBAL_EDP_CACHE
            _GLOBAL_EDP_CACHE['data'] = {}
            _GLOBAL_EDP_CACHE['last_update'] = 0
            print(f"🔄 Caché de EDPs limpiado después de crear {success_count} EDPs")
        
        return {
            'success': success_count > 0,
            'message': f'Procesamiento completado: {success_count} exitosos, {error_count} errores',
            'stats': {
                'total_rows': len(df),
                'success_count': success_count,
                'error_count': error_count,
                'success_rate': (success_count / len(df)) * 100 if len(df) > 0 else 0
            },
            'errors': errors[:10]  # Limitar errores mostrados
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error en procesamiento masivo: {str(e)}',
            'stats': {
                'total_rows': len(df),
                'success_count': success_count,
                'error_count': error_count
            },
            'errors': errors
        } 
        
       
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


def validate_bulk_data(df: pd.DataFrame, preview_mode: bool = False) -> Dict[str, Any]:
    """Validar estructura y contenido del archivo para carga masiva."""
    try:
        print("🔍 Iniciando validate_bulk_data...")
        errors = []
        warnings = []
        
        # Caché temporal para duplicados durante esta validación
        duplicate_cache = {}
        
        # Pre-cargar caché global para máximo rendimiento
        print("🚀 Pre-cargando caché de EDPs para validación rápida...")
        cache_start = time.time()
        load_edps_cache()  # Esto carga el caché global si es necesario
        cache_time = time.time() - cache_start
        print(f"⚡ Caché listo en {cache_time:.2f}s")
        
        # Verificar que el DataFrame no esté vacío
        if df.empty:
            print("❌ DataFrame está vacío")
            errors.append('El archivo está vacío')
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        print(f"📊 DataFrame shape: {df.shape}")
        print(f"📋 Columnas originales: {list(df.columns)}")
        
        # Limpiar nombres de columnas
        df_work = df.copy()  # Crear una copia para trabajar
        df_work.columns = df_work.columns.str.strip().str.lower()
        print(f"📋 Columnas después de limpiar: {list(df_work.columns)}")
        
        # Columnas obligatorias
        required_columns = ['n_edp', 'proyecto', 'cliente', 'jefe_proyecto', 'fecha_emision', 'monto_propuesto']
        
        # Verificar columnas obligatorias
        missing_columns = [col for col in required_columns if col not in df_work.columns]
        if missing_columns:
            print(f"❌ Faltan columnas: {missing_columns}")
            errors.append(f'Faltan las siguientes columnas obligatorias: {", ".join(missing_columns)}')
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        print("✅ Todas las columnas obligatorias están presentes")
        
        # Validar que no hay filas completamente vacías
        df_clean = df_work.dropna(how='all').copy()
        if df_clean.empty:
            print("❌ No hay datos válidos después de limpiar")
            errors.append('No hay datos válidos en el archivo')
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        print(f"📊 Filas válidas después de limpiar: {len(df_clean)}")
        
        # Limpiar y normalizar datos
        try:
            print("🧹 Limpiando y normalizando datos...")
            
            # Reemplazar NaN con valores apropiados antes de procesar
            df_clean = df_clean.fillna({
                'fecha_envio_cliente': '',
                'monto_aprobado': '',
                'observaciones': '',
                'gestor': ''
            })
            
            # Asegurar que los montos sean enteros sin decimales
            for idx in df_clean.index:
                try:
                    if pd.notna(df_clean.at[idx, 'monto_propuesto']) and str(df_clean.at[idx, 'monto_propuesto']).strip() != '':
                        monto_str = str(df_clean.at[idx, 'monto_propuesto']).replace(',', '').replace(' ', '')
                        monto = float(monto_str)
                        df_clean.at[idx, 'monto_propuesto'] = int(monto)
                except Exception as e:
                    print(f"⚠️ Error procesando monto_propuesto en fila {idx}: {e}")
                
                if 'monto_aprobado' in df_clean.columns:
                    try:
                        monto_aprobado = df_clean.at[idx, 'monto_aprobado']
                        if pd.notna(monto_aprobado) and str(monto_aprobado).strip() != '':
                            monto_str = str(monto_aprobado).replace(',', '').replace(' ', '')
                            if monto_str:  # Solo si no está vacío
                                monto = float(monto_str)
                                df_clean.at[idx, 'monto_aprobado'] = int(monto)
                            else:
                                df_clean.at[idx, 'monto_aprobado'] = ''
                        else:
                            df_clean.at[idx, 'monto_aprobado'] = ''
                    except Exception as e:
                        print(f"⚠️ Error procesando monto_aprobado en fila {idx}: {e}")
                        df_clean.at[idx, 'monto_aprobado'] = ''
            
            print("✅ Datos limpiados y normalizados")
            
        except Exception as clean_error:
            print(f"❌ Error limpiando datos: {str(clean_error)}")
            # Continuar con validación sin la limpieza
        
        # Validaciones por fila
        print("🔍 Iniciando validaciones por fila...")
        print(f"🔍 Validando duplicados en BD para {len(df_clean)} filas...")
        row_errors = []
        duplicate_checks = []  # Para verificar duplicados
        
        for idx, row in df_clean.iterrows():
            row_error = []
            
            # Validar campos obligatorios
            for field in required_columns:
                if pd.isna(row[field]) or str(row[field]).strip() == '':
                    row_error.append(f'Fila {idx + 2}: El campo {field} es obligatorio')
            
            # Validar número EDP
            try:
                n_edp = int(row['n_edp'])
                if n_edp <= 0:
                    row_error.append(f'Fila {idx + 2}: El número EDP debe ser positivo')
                else:
                    # Verificar duplicados dentro del mismo archivo
                    proyecto = str(row['proyecto']).strip()
                    edp_key = f"{n_edp}_{proyecto}"
                    if edp_key in duplicate_checks:
                        row_error.append(f'Fila {idx + 2}: EDP #{n_edp} duplicado para proyecto {proyecto}')
                    else:
                        duplicate_checks.append(edp_key)
                        # SIEMPRE verificar duplicados en BD, incluso en preview (súper rápido)
                        if check_duplicate_fast(n_edp, proyecto):
                            row_error.append(f'Fila {idx + 2}: Ya existe EDP #{n_edp} para proyecto {proyecto}')
            except (ValueError, TypeError):
                row_error.append(f'Fila {idx + 2}: El número EDP debe ser un número válido')
            
            # Validar montos
            try:
                monto_str = str(row['monto_propuesto']).replace(',', '').replace(' ', '')
                monto = float(monto_str)
                if monto <= 0:
                    row_error.append(f'Fila {idx + 2}: El monto propuesto debe ser mayor a 0')
            except (ValueError, TypeError):
                row_error.append(f'Fila {idx + 2}: El monto propuesto debe ser un número válido')
            
            # Validar fecha de emisión
            try:
                fecha_str = str(row['fecha_emision']).strip()
                # Intentar varios formatos de fecha
                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                fecha_parsed = None
                for fmt in date_formats:
                    try:
                        fecha_parsed = datetime.strptime(fecha_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if fecha_parsed is None:
                    row_error.append(f'Fila {idx + 2}: La fecha de emisión debe tener formato YYYY-MM-DD, DD/MM/YYYY o MM/DD/YYYY')
            except (ValueError, TypeError):
                row_error.append(f'Fila {idx + 2}: La fecha de emisión no es válida')
            
            row_errors.extend(row_error)
        
        print(f"📊 Total errores encontrados: {len(row_errors)}")
        errors.extend(row_errors)
        
        # En modo preview, limitar errores mostrados
        if preview_mode and len(errors) > 10:
            errors = errors[:10]
            warnings.append('Se muestran solo los primeros 10 errores. Corrija estos para ver más.')
        
        # Si hay errores de duplicados, generar sugerencias
        suggestions = None
        if len(errors) > 0 and any('Ya existe EDP' in str(error) for error in errors):
            print("🔍 Generando sugerencias para EDPs duplicados...")
            suggestions = get_duplicate_suggestions(df_clean)
        
        result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_rows': len(df_clean),
            'suggestions': suggestions
        }
        
        print(f"✅ Validación completada: valid={result['valid']}, errores={len(errors)}")
        if suggestions and suggestions['has_duplicates']:
            print(f"💡 Generadas sugerencias para {suggestions['total_duplicates']} duplicados")
        
        return result
        
    except Exception as e:
        print(f"💥 Error en validate_bulk_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'valid': False,
            'errors': [f'Error interno validando datos: {str(e)}'],
            'warnings': [],
            'total_rows': 0
        }

def prepare_edp_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Preparar datos del EDP para creación, agregando campos automáticos."""
    import pandas as pd
    
    print(f"🔧 Iniciando preparación de datos EDP...")
    print(f"📋 Form data recibido: {form_data}")
    
    # Procesar n_edp - convertir a string (como espera Supabase)
    n_edp_value = form_data.get('n_edp')
    if pd.isna(n_edp_value) if hasattr(pd, 'isna') else n_edp_value is None:
        raise ValueError("El número EDP no puede estar vacío")
    
    try:
        # Convertir a entero primero para validar, luego a string para Supabase
        n_edp_int = int(float(str(n_edp_value)))
        if n_edp_int <= 0:
            raise ValueError("El número EDP debe ser positivo")
        n_edp_final = str(n_edp_int)
        print(f"✅ n_edp procesado: {n_edp_value} → {n_edp_final}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"El número EDP debe ser un número válido: {e}")
    
    # Limpiar y convertir montos a float
    monto_propuesto = form_data.get('monto_propuesto', 0)
    if isinstance(monto_propuesto, str):
        monto_propuesto = monto_propuesto.replace(',', '').replace(' ', '')
    try:
        monto_propuesto = float(monto_propuesto) if monto_propuesto else 0.0
        if monto_propuesto <= 0:
            raise ValueError("El monto propuesto debe ser mayor a 0")
        print(f"✅ monto_propuesto procesado: {monto_propuesto}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Monto propuesto inválido: {e}")
    
    monto_aprobado = form_data.get('monto_aprobado')
    if monto_aprobado and str(monto_aprobado).strip() and str(monto_aprobado).strip().lower() != 'nan':
        if isinstance(monto_aprobado, str):
            monto_aprobado = monto_aprobado.replace(',', '').replace(' ', '')
        try:
            monto_aprobado = float(monto_aprobado)
            print(f"✅ monto_aprobado procesado: {monto_aprobado}")
        except (ValueError, TypeError):
            print("⚠️ monto_aprobado inválido, estableciendo como None")
            monto_aprobado = None
    else:
        monto_aprobado = None
        print("✅ monto_aprobado establecido como None (vacío)")
    
    # Procesar fecha de emisión y generar mes
    try:
        fecha_emision_str = str(form_data['fecha_emision'])
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
    
    # Procesar fecha de envío cliente
    fecha_envio_cliente = form_data.get('fecha_envio_cliente')
    if fecha_envio_cliente and str(fecha_envio_cliente).strip() and str(fecha_envio_cliente).strip().lower() != 'nan':
        try:
            # Validar formato de fecha
            datetime.strptime(str(fecha_envio_cliente), '%Y-%m-%d')
            fecha_envio_cliente_final = str(fecha_envio_cliente)
            print(f"✅ fecha_envio_cliente procesada: {fecha_envio_cliente_final}")
        except ValueError:
            print("⚠️ fecha_envio_cliente inválida, estableciendo como None")
            fecha_envio_cliente_final = None
    else:
        fecha_envio_cliente_final = None
        print("✅ fecha_envio_cliente establecida como None (vacía)")
    
    # Procesar campos de texto opcionales
    gestor = form_data.get('gestor')
    gestor_final = str(gestor).strip() if gestor and str(gestor).strip() != '' and str(gestor).strip().lower() != 'nan' else None
    
    observaciones = form_data.get('observaciones')
    observaciones_final = str(observaciones).strip() if observaciones and str(observaciones).strip() != '' and str(observaciones).strip().lower() != 'nan' else None
    
    # Procesar campo booleano conformidad_enviada
    conformidad_enviada = form_data.get('conformidad_enviada', False)
    if isinstance(conformidad_enviada, str):
        # Convertir string a booleano
        conformidad_enviada_final = conformidad_enviada.lower() in ['true', 'yes', 'si', 'sí', '1', 'on']
    elif isinstance(conformidad_enviada, (int, float)):
        conformidad_enviada_final = bool(conformidad_enviada)
    else:
        conformidad_enviada_final = bool(conformidad_enviada) if conformidad_enviada is not None else False
    
    print(f"✅ Campos opcionales procesados - gestor: {gestor_final}, observaciones: {observaciones_final}")
    print(f"✅ Campo booleano procesado - conformidad_enviada: {conformidad_enviada_final}")
    
    # Preparar datos finales
    edp_data = {
        # Campos obligatorios
        'n_edp': n_edp_final,
        'proyecto': str(form_data['proyecto']).strip(),
        'cliente': str(form_data['cliente']).strip(),
        'jefe_proyecto': str(form_data['jefe_proyecto']).strip(),
        'fecha_emision': fecha_emision_str,
        'monto_propuesto': monto_propuesto,
        
        # Campos automáticos
        'estado': 'revisión',  # Estado inicial más apropiado
        'mes': mes,
        'conformidad_enviada': conformidad_enviada_final,  # Booleano procesado
        
        # Campos opcionales
        'gestor': gestor_final,
        'fecha_envio_cliente': fecha_envio_cliente_final,
        'monto_aprobado': monto_aprobado,
        'fecha_estimada_pago': fecha_estimada_pago_final,
        'observaciones': observaciones_final,
        
        # Campos de seguimiento
        'registrado_por': form_data.get('registrado_por', 'admin'),
        'fecha_registro': datetime.now().isoformat(),
        
        # Campos adicionales para compatibilidad con Supabase
        'n_conformidad': '',
        'fecha_conformidad': None,
        'estado_detallado': '',
        'motivo_no_aprobado': '',
        'tipo_falla': ''
    }
    
    print(f"🎯 Datos finales preparados: {edp_data}")
    return edp_data




def validate_edp_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar datos de un EDP individual."""
    errors = []
    
    print(f"🔍 Iniciando validación de datos EDP...")
    print(f"📋 Datos a validar: {data}")
    
    # Validaciones obligatorias
    required_fields = ['n_edp', 'proyecto', 'cliente', 'jefe_proyecto', 'fecha_emision', 'monto_propuesto']
    
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == '':
            errors.append(f'El campo {field} es obligatorio')
            print(f"❌ Campo obligatorio faltante: {field}")
    
    # Validar número EDP
    if 'n_edp' in data and data['n_edp']:
        try:
            n_edp = int(float(str(data['n_edp'])))
            if n_edp <= 0:
                errors.append('El número EDP debe ser positivo')
                print(f"❌ n_edp debe ser positivo: {n_edp}")
            else:
                # Validar que no exista EDP con mismo número para el mismo proyecto
                if 'proyecto' in data and data['proyecto']:
                    print(f"🔍 Validando duplicado: EDP #{n_edp} para proyecto '{data['proyecto']}'")
                    try:
                        is_duplicate = check_duplicate_fast(n_edp, data['proyecto'])
                        if is_duplicate:
                            errors.append(f'Ya existe EDP #{n_edp} para el proyecto {data["proyecto"]}')
                            print(f"🚫 Duplicado encontrado: EDP #{n_edp} para proyecto {data['proyecto']}")
                        else:
                            print(f"✅ EDP #{n_edp} es único para proyecto {data['proyecto']}")
                    except Exception as dup_error:
                        print(f"⚠️ Error verificando duplicados: {str(dup_error)}")
                        # No bloquear si hay error en verificación
        except (ValueError, TypeError):
            errors.append('El número EDP debe ser un número válido')
            print(f"❌ n_edp formato inválido: {data.get('n_edp')}")
    
    # Validar fecha de emisión
    if 'fecha_emision' in data and data['fecha_emision']:
        try:
            fecha_str = str(data['fecha_emision']).strip()
            datetime.strptime(fecha_str, '%Y-%m-%d')
            print(f"✅ fecha_emision válida: {fecha_str}")
        except (ValueError, TypeError):
            errors.append('La fecha de emisión debe tener formato YYYY-MM-DD')
            print(f"❌ fecha_emision formato inválido: {data.get('fecha_emision')}")
    
    # Validar monto propuesto
    if 'monto_propuesto' in data and data['monto_propuesto']:
        try:
            monto_str = str(data['monto_propuesto']).replace(',', '').replace(' ', '')
            monto = float(monto_str)
            if monto <= 0:
                errors.append('El monto propuesto debe ser mayor a 0')
                print(f"❌ monto_propuesto debe ser positivo: {monto}")
            else:
                print(f"✅ monto_propuesto válido: {monto}")
        except (ValueError, TypeError):
            errors.append('El monto propuesto debe ser un número válido')
            print(f"❌ monto_propuesto formato inválido: {data.get('monto_propuesto')}")
    
    # Validar monto aprobado si está presente
    if 'monto_aprobado' in data and data['monto_aprobado'] and str(data['monto_aprobado']).strip() != '' and str(data['monto_aprobado']).strip().lower() != 'nan':
        try:
            monto_str = str(data['monto_aprobado']).replace(',', '').replace(' ', '')
            monto_aprobado = float(monto_str)
            if monto_aprobado <= 0:
                errors.append('El monto aprobado debe ser mayor a 0')
                print(f"❌ monto_aprobado debe ser positivo: {monto_aprobado}")
            else:
                print(f"✅ monto_aprobado válido: {monto_aprobado}")
        except (ValueError, TypeError):
            errors.append('El monto aprobado debe ser un número válido')
            print(f"❌ monto_aprobado formato inválido: {data.get('monto_aprobado')}")
    
    # Validar fechas opcionales (solo si tienen valor)
    date_fields = ['fecha_envio_cliente', 'fecha_estimada_pago']
    for field in date_fields:
        if field in data and data[field] and str(data[field]).strip() != '' and str(data[field]).strip().lower() != 'nan':
            try:
                fecha_str = str(data[field]).strip()
                # Intentar varios formatos de fecha
                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                fecha_parsed = None
                for fmt in date_formats:
                    try:
                        fecha_parsed = datetime.strptime(fecha_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if fecha_parsed is None:
                    errors.append(f'El campo {field} debe tener formato YYYY-MM-DD, DD/MM/YYYY o MM/DD/YYYY')
                    print(f"❌ {field} formato inválido: {fecha_str}")
                else:
                    print(f"✅ {field} válido: {fecha_str}")
            except (ValueError, TypeError):
                errors.append(f'El campo {field} no es una fecha válida')
                print(f"❌ {field} no es fecha válida: {data.get(field)}")
    
    # Validar campos de texto obligatorios
    text_fields = ['proyecto', 'cliente', 'jefe_proyecto']
    for field in text_fields:
        if field in data and data[field]:
            value = str(data[field]).strip()
            if len(value) < 2:
                errors.append(f'El campo {field} debe tener al menos 2 caracteres')
                print(f"❌ {field} muy corto: {value}")
            elif len(value) > 100:
                errors.append(f'El campo {field} no puede exceder 100 caracteres')
                print(f"❌ {field} muy largo: {len(value)} caracteres")
            else:
                print(f"✅ {field} válido: {value}")
    
    validation_result = {
        'valid': len(errors) == 0,
        'errors': errors
    }
    
    print(f"🎯 Resultado validación: valid={validation_result['valid']}, errores={len(errors)}")
    if errors:
        print(f"❌ Errores encontrados: {errors}")
    
    return validation_result


@edp_management_bp.route('/upload/apply-suggestions-and-process', methods=['POST'])
@login_required
def apply_suggestions_and_process():
    """Aplicar sugerencias automáticamente y procesar el archivo sin descarga."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No se encontró archivo'}), 400
        
        file = request.files['file']
        suggestions_data = request.form.get('suggestions')
        
        if not suggestions_data:
            return jsonify({'success': False, 'message': 'No se encontraron sugerencias'}), 400
        
        import json
        suggestions = json.loads(suggestions_data)
        
        print(f"🔧 Aplicando sugerencias automáticamente para {len(suggestions.get('duplicates', []))} duplicados")
        
        # Leer archivo original
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({'success': False, 'message': 'Formato de archivo no soportado'}), 400
        
        # Aplicar correcciones automáticamente
        corrections_applied = 0
        correction_details = []
        
        for suggestion in suggestions.get('duplicates', []):
            row_idx = suggestion['row'] - 2  # Convertir a índice 0-based
            if row_idx < len(df) and suggestion['suggested_numbers']:
                # Usar el primer número sugerido
                old_edp = suggestion['current_edp']
                new_edp = suggestion['suggested_numbers'][0]
                
                df.iloc[row_idx, df.columns.get_loc('n_edp')] = new_edp
                corrections_applied += 1
                
                correction_details.append({
                    'row': suggestion['row'],
                    'proyecto': suggestion['proyecto'],
                    'old_edp': old_edp,
                    'new_edp': new_edp
                })
                
                print(f"✅ Fila {suggestion['row']}: EDP #{old_edp} → #{new_edp} (Proyecto: {suggestion['proyecto']})")
        
        print(f"🔧 Total correcciones aplicadas: {corrections_applied}")
        
        # Procesar el archivo corregido directamente
        from flask_login import current_user
        user_email = current_user.email if current_user and hasattr(current_user, 'email') else 'sistema'
        
        print("🚀 Procesando archivo corregido automáticamente...")
        result = process_bulk_upload(df, user_email)
        
        # Agregar información de correcciones al resultado
        result['corrections_applied'] = corrections_applied
        result['correction_details'] = correction_details
        
        # Limpiar caché después del procesamiento exitoso
        if result.get('success') and result.get('stats', {}).get('success_count', 0) > 0:
            print("🧹 Limpiando caché de EDPs después del procesamiento exitoso...")
            global _GLOBAL_EDP_CACHE
            _GLOBAL_EDP_CACHE['data'] = {}
            _GLOBAL_EDP_CACHE['last_update'] = 0
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error aplicando sugerencias y procesando: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error aplicando sugerencias: {str(e)}'
        }), 500
        
@edp_management_bp.route('/upload/validate', methods=['POST'])
@login_required
def validate_file():
    """Validar archivo antes de la carga masiva."""
    try:
        print("🔍 Iniciando validación de archivo...")
        
        if 'file' not in request.files:
            print("❌ No se encontró archivo en la request")
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        file = request.files['file']
        print(f"📁 Archivo recibido: {file.filename}")
        
        if not allowed_file(file.filename):
            print(f"❌ Tipo de archivo no permitido: {file.filename}")
            return jsonify({
                'success': False,
                'message': 'Tipo de archivo no permitido. Use .xlsx, .xls o .csv'
            }), 400
        
        print(f"✅ Tipo de archivo válido: {file.filename}")
        
        # Leer archivo
        try:
            print("📖 Leyendo archivo...")
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
                print(f"📊 CSV leído exitosamente: {df.shape}")
            else:
                df = pd.read_excel(file)
                print(f"📊 Excel leído exitosamente: {df.shape}")
            
            print(f"📋 Columnas encontradas: {list(df.columns)}")
            
        except Exception as read_error:
            print(f"❌ Error leyendo archivo: {str(read_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error leyendo archivo: {str(read_error)}. Verifique que el archivo no esté corrupto y tenga el formato correcto.'
            }), 400
        
        # Validar estructura y datos
        try:
            print("🔍 Validando estructura y datos...")
            validation_result = validate_bulk_data(df, preview_mode=True)
            print(f"✅ Validación completada: {validation_result.get('valid', False)}")
            
        except Exception as validation_error:
            print(f"❌ Error en validación: {str(validation_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error validando datos: {str(validation_error)}'
            }), 400
        
        # Generar preview de los primeros 5 registros
        try:
            print("👀 Generando preview...")
            # Reemplazar NaN con None para JSON válido
            df_preview = df.head(5).fillna('')  # Reemplazar NaN con string vacío
            preview_data = df_preview.to_dict('records')
            print(f"📋 Preview generado con {len(preview_data)} registros")
            
        except Exception as preview_error:
            print(f"❌ Error generando preview: {str(preview_error)}")
            preview_data = []
        
        response_data = {
            'success': validation_result['valid'],
            'validation': validation_result,
            'preview': preview_data,
            'total_rows': len(df),
            'columns': list(df.columns),
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', []),
            'suggestions': validation_result.get('suggestions')
        }
        
        print(f"✅ Respuesta preparada: success={response_data['success']}")
        if validation_result.get('suggestions'):
            print(f"💡 Sugerencias incluidas: {validation_result['suggestions']['total_duplicates']} duplicados")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"💥 Error general en validate_file: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error inesperado validando archivo: {str(e)}'
        }), 500


def get_duplicate_suggestions(df: pd.DataFrame) -> Dict[str, Any]:
    """Analizar duplicados y generar sugerencias para números EDP disponibles."""
    duplicates_info = []
    cache_data = load_edps_cache()
    all_suggested_numbers = set()  # Evitar duplicados globales
    
    # Crear un conjunto de todos los números EDP que están en el archivo actual por proyecto
    current_file_edps = {}  # {proyecto: set(edps)}
    for idx, row in df.iterrows():
        try:
            n_edp = int(row['n_edp'])
            proyecto = str(row['proyecto']).strip().upper()
            
            if proyecto not in current_file_edps:
                current_file_edps[proyecto] = set()
            current_file_edps[proyecto].add(n_edp)
        except (ValueError, TypeError):
            continue
    
    print(f"🔍 EDPs en archivo actual por proyecto: {current_file_edps}")
    
    for idx, row in df.iterrows():
        try:
            n_edp = int(row['n_edp'])
            proyecto = str(row['proyecto']).strip()
            proyecto_upper = proyecto.upper()
            
            if check_duplicate_fast(n_edp, proyecto):
                print(f"🚫 Duplicado encontrado: EDP #{n_edp} para proyecto {proyecto}")
                
                # Encontrar números disponibles para este proyecto
                # Empezar desde el número actual + 1
                available_numbers = []
                current_num = n_edp + 1
                
                # Buscar 3 números únicos disponibles
                while len(available_numbers) < 3 and current_num < n_edp + 1000:
                    cache_key = f"{current_num}_{proyecto_upper}"
                    
                    # Verificar que el número no esté:
                    # 1. En la base de datos
                    # 2. Ya sugerido globalmente
                    # 3. En el archivo actual para el mismo proyecto
                    is_in_db = cache_data.get(cache_key, False)
                    is_already_suggested = current_num in all_suggested_numbers
                    is_in_current_file = current_num in current_file_edps.get(proyecto_upper, set())
                    
                    if not is_in_db and not is_already_suggested and not is_in_current_file:
                        available_numbers.append(current_num)
                        all_suggested_numbers.add(current_num)
                        print(f"✅ Número disponible encontrado: #{current_num} para {proyecto}")
                    else:
                        reasons = []
                        if is_in_db: reasons.append("en BD")
                        if is_already_suggested: reasons.append("ya sugerido")
                        if is_in_current_file: reasons.append("en archivo actual")
                        print(f"❌ Número #{current_num} no disponible ({', '.join(reasons)})")
                    
                    current_num += 1
                
                duplicates_info.append({
                    'row': idx + 2,
                    'current_edp': n_edp,
                    'proyecto': proyecto,
                    'suggested_numbers': available_numbers,
                    'cliente': str(row.get('cliente', '')),
                    'monto': row.get('monto_propuesto', 0)
                })
                
                print(f"🔧 Sugerencias para EDP #{n_edp}: {available_numbers}")
                
        except (ValueError, TypeError):
            continue
    
    print(f"📊 Total duplicados encontrados: {len(duplicates_info)}")
    print(f"📊 Números sugeridos globalmente: {sorted(all_suggested_numbers)}")
    
    return {
        'has_duplicates': len(duplicates_info) > 0,
        'duplicates': duplicates_info,
        'total_duplicates': len(duplicates_info)
    }