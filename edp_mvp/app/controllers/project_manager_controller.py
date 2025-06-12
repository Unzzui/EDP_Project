"""
Controller for Project Manager (Jefe de Proyecto) views and API endpoints.
Handles all project manager related routes and data processing.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    make_response,
    abort
)
from flask_login import login_required, current_user
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import traceback
import logging
import json

from ..services.project_manager_service import ProjectManagerService
from ..services.edp_service import EDPService
from ..services.analytics_service import AnalyticsService
from ..utils.auth_utils import require_project_manager_or_above
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils

# Create blueprint
project_manager_bp = Blueprint('project_manager', __name__, url_prefix='/jefe-proyecto')

# Initialize services
pm_service = ProjectManagerService()
edp_service = EDPService()
analytics_service = AnalyticsService()

logger = logging.getLogger(__name__)

@project_manager_bp.route('/')
@login_required
@require_project_manager_or_above
def dashboard():
    """Main dashboard for project manager."""
    try:
        # Determine the manager name based on user role
        try:
            manager_name = _get_manager_name()
        except ValueError as e:
            flash(str(e) + '. Contacte al administrador.', 'error')
            return redirect(url_for('main.index'))
        
        # Validate user has appropriate role
        if not hasattr(current_user, 'rol') or current_user.rol not in ['jefe_proyecto', 'miembro_equipo_proyecto', 'director_operaciones', 'administrador']:
            flash('No tiene permisos para acceder a esta sección', 'error')
            return redirect(url_for('main.index'))
        
        # Get comprehensive dashboard data
        dashboard_data = pm_service.get_dashboard_data(manager_name)
        
        if not dashboard_data:
            flash(f'No se encontraron datos para el jefe de proyecto: {manager_name}', 'warning')
            return redirect(url_for('main.index'))
        
        # Add additional template variables
        template_data = {
            **dashboard_data,
            'current_date': datetime.now(),
            'manager_name': manager_name,
            'is_team_member': current_user.rol == 'miembro_equipo_proyecto',
            'format_currency': FormatUtils.format_currency,
            'format_number': FormatUtils.format_number,
            'calculate_percentage': lambda x, y: round((x/y*100) if y > 0 else 0, 1)
        }
        
        return render_template('JP/dashboard.html', **template_data)
        
    except Exception as e:
        logger.error(f"Error in project manager dashboard for {current_user.username}: {str(e)}")
        logger.error(traceback.format_exc())
        flash('Error al cargar el dashboard del jefe de proyecto', 'error')
        return redirect(url_for('main.index'))

@project_manager_bp.route('/proyecto/<project_name>')
@login_required
@require_project_manager_or_above
def project_detail(project_name: str):
    """Detailed view for a specific project."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        # Get project details
        project_data = pm_service.get_project_detail(manager_name, project_name)
        
        if not project_data:
            flash(f'Proyecto no encontrado: {project_name}', 'warning')
            return redirect(url_for('project_manager.dashboard'))
        
        # Get additional project analytics
        project_analytics = analytics_service.analyze_project_performance(project_name)
        
        template_data = {
            'manager_name': manager_name,
            'project_data': project_data,
            'project_analytics': project_analytics,
            'format_currency': FormatUtils.format_currency,
            'format_number': FormatUtils.format_number,
            'current_date': datetime.now()
        }
        
        return render_template('JP/project_detail.html', **template_data)
        
    except Exception as e:
        logger.error(f"Error in project detail for {project_name}: {str(e)}")
        flash('Error al cargar los detalles del proyecto', 'error')
        return redirect(url_for('project_manager.dashboard'))

@project_manager_bp.route('/equipo')
@login_required
@require_project_manager_or_above
def team_dashboard():
    """Team performance dashboard."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        # Get team dashboard data
        team_data = pm_service.get_team_dashboard(manager_name)
        
        template_data = {
            'manager_name': manager_name,
            **team_data,
            'format_currency': FormatUtils.format_currency,
            'format_number': FormatUtils.format_number,
            'current_date': datetime.now()
        }
        
        return render_template('JP/team_dashboard.html', **template_data)
        
    except Exception as e:
        logger.error(f"Error in team dashboard for {current_user.username}: {str(e)}")
        flash('Error al cargar el dashboard del equipo', 'error')
        return redirect(url_for('project_manager.dashboard'))

@project_manager_bp.route('/reportes')
@login_required
@require_project_manager_or_above
def reports():
    """Reports and analytics view."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        # Get dashboard data for reports
        dashboard_data = pm_service.get_dashboard_data(manager_name)
        
        # Add report-specific calculations
        report_data = {
            'summary_charts': _generate_summary_charts(dashboard_data),
            'performance_metrics': _calculate_performance_metrics(dashboard_data),
            'trend_analysis': _generate_trend_analysis(dashboard_data)
        }
        
        template_data = {
            'manager_name': manager_name,
            'dashboard_data': dashboard_data,
            'report_data': report_data,
            'format_currency': FormatUtils.format_currency,
            'current_date': datetime.now()
        }
        
        return render_template('JP/reports.html', **template_data)
        
    except Exception as e:
        logger.error(f"Error in reports for {current_user.username}: {str(e)}")
        flash('Error al cargar los reportes', 'error')
        return redirect(url_for('project_manager.dashboard'))

# API Endpoints

@project_manager_bp.route('/api/kpis')
@login_required
@require_project_manager_or_above
def api_get_kpis():
    """API endpoint to get KPIs for the current project manager."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        dashboard_data = pm_service.get_dashboard_data(manager_name)
        
        return jsonify({
            'success': True,
            'data': dashboard_data.get('kpis', {}),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in API KPIs for {current_user.username}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener KPIs',
            'message': str(e)
        }), 500

@project_manager_bp.route('/api/projects')
@login_required
@require_project_manager_or_above
def api_get_projects():
    """API endpoint to get projects for the current project manager."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        dashboard_data = pm_service.get_dashboard_data(manager_name)
        
        return jsonify({
            'success': True,
            'data': dashboard_data.get('project_performance', []),
            'total': len(dashboard_data.get('project_performance', [])),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in API projects for {current_user.username}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener proyectos',
            'message': str(e)
        }), 500

@project_manager_bp.route('/api/team')
@login_required
@require_project_manager_or_above
def api_get_team():
    """API endpoint to get team performance data."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        team_data = pm_service.get_team_dashboard(manager_name)
        
        return jsonify({
            'success': True,
            'data': team_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in API team for {current_user.username}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener datos del equipo',
            'message': str(e)
        }), 500

@project_manager_bp.route('/api/alerts')
@login_required
@require_project_manager_or_above
def api_get_alerts():
    """API endpoint to get alerts for the current project manager."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        dashboard_data = pm_service.get_dashboard_data(manager_name)
        
        return jsonify({
            'success': True,
            'data': dashboard_data.get('alerts', []),
            'count': len(dashboard_data.get('alerts', [])),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in API alerts for {current_user.username}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener alertas',
            'message': str(e)
        }), 500

@project_manager_bp.route('/api/export', methods=['POST'])
@login_required
@require_project_manager_or_above
def api_export_report():
    """API endpoint to export manager report for the current user."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        data = request.get_json() or {}
        format_type = data.get('format', 'excel')
        
        # Generate report
        report_path = pm_service.export_manager_report(manager_name, format_type)
        
        return jsonify({
            'success': True,
            'data': {
                'report_path': report_path,
                'download_url': f'/downloads/{report_path}'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in API export for {current_user.username}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al exportar reporte',
            'message': str(e)
        }), 500

@project_manager_bp.route('/api/charts')
@login_required
@require_project_manager_or_above
def api_get_charts():
    """API endpoint to get chart data for the current project manager dashboard."""
    try:
        # Use current authenticated user's name as the manager
        manager_name = _get_manager_name()
        
        dashboard_data = pm_service.get_dashboard_data(manager_name)
        
        # Generate chart data
        charts = {
            'project_status': _generate_project_status_chart(dashboard_data),
            'financial_trends': _generate_financial_trends_chart(dashboard_data),
            'team_performance': _generate_team_performance_chart(dashboard_data),
            'kpi_radar': _generate_kpi_radar_chart(dashboard_data)
        }
        
        return jsonify({
            'success': True,
            'data': charts,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in API charts for {current_user.username}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al generar gráficos',
            'message': str(e)
        }), 500



# Helper functions for chart generation

def _generate_project_status_chart(dashboard_data: Dict) -> Dict:
    """Generate project status distribution chart."""
    projects_by_status = dashboard_data.get('projects_by_status', {})
    
    return {
        'type': 'doughnut',
        'data': {
            'labels': ['Pendientes', 'En Progreso', 'Completados', 'Vencidos'],
            'datasets': [{
                'data': [
                    len(projects_by_status.get('pending', [])),
                    len(projects_by_status.get('in_progress', [])),
                    len(projects_by_status.get('completed', [])),
                    len(projects_by_status.get('overdue', []))
                ],
                'backgroundColor': ['#fbbf24', '#3b82f6', '#10b981', '#ef4444']
            }]
        },
        'options': {
            'responsive': True,
            'plugins': {
                'legend': {'position': 'bottom'}
            }
        }
    }

def _generate_financial_trends_chart(dashboard_data: Dict) -> Dict:
    """Generate financial trends chart."""
    trends = dashboard_data.get('trends', {}).get('monthly_trends', [])
    
    return {
        'type': 'line',
        'data': {
            'labels': [trend['month'] for trend in trends],
            'datasets': [
                {
                    'label': 'Propuesto',
                    'data': [trend['amount_proposed'] for trend in trends],
                    'borderColor': '#8b5cf6',
                    'backgroundColor': '#8b5cf6'
                },
                {
                    'label': 'Aprobado',
                    'data': [trend['amount_approved'] for trend in trends],
                    'borderColor': '#3b82f6',
                    'backgroundColor': '#3b82f6'
                },
                {
                    'label': 'Pagado',
                    'data': [trend['amount_paid'] for trend in trends],
                    'borderColor': '#10b981',
                    'backgroundColor': '#10b981'
                }
            ]
        },
        'options': {
            'responsive': True,
            'scales': {
                'y': {'beginAtZero': True}
            }
        }
    }

def _generate_team_performance_chart(dashboard_data: Dict) -> Dict:
    """Generate team performance chart."""
    team_performance = dashboard_data.get('team_performance', {})
    
    if not team_performance:
        return {'type': 'bar', 'data': {'labels': [], 'datasets': []}}
    
    return {
        'type': 'bar',
        'data': {
            'labels': list(team_performance.keys()),
            'datasets': [{
                'label': 'Eficiencia (%)',
                'data': [member['efficiency_score'] for member in team_performance.values()],
                'backgroundColor': '#3b82f6'
            }]
        },
        'options': {
            'responsive': True,
            'scales': {
                'y': {'beginAtZero': True, 'max': 100}
            }
        }
    }

def _generate_kpi_radar_chart(dashboard_data: Dict) -> Dict:
    """Generate KPI radar chart."""
    kpis = dashboard_data.get('kpis', {})
    
    return {
        'type': 'radar',
        'data': {
            'labels': ['Eficiencia', 'Presupuesto', 'Tiempo', 'Calidad'],
            'datasets': [{
                'label': 'Rendimiento',
                'data': [
                    kpis.get('project_efficiency', 0),
                    kpis.get('budget_performance', 0),
                    kpis.get('time_performance', 0),
                    kpis.get('quality_score', 0)
                ],
                'backgroundColor': 'rgba(59, 130, 246, 0.2)',
                'borderColor': '#3b82f6',
                'pointBackgroundColor': '#3b82f6'
            }]
        },
        'options': {
            'responsive': True,
            'scales': {
                'r': {'beginAtZero': True, 'max': 100}
            }
        }
    }

def _generate_summary_charts(dashboard_data: Dict) -> Dict:
    """Generate summary charts for reports."""
    return {
        'project_distribution': _generate_project_status_chart(dashboard_data),
        'financial_overview': _generate_financial_trends_chart(dashboard_data)
    }

def _calculate_performance_metrics(dashboard_data: Dict) -> Dict:
    """Calculate additional performance metrics for reports."""
    summary = dashboard_data.get('summary', {})
    kpis = dashboard_data.get('kpis', {})
    
    return {
        'efficiency_rating': _get_rating(kpis.get('project_efficiency', 0)),
        'budget_rating': _get_rating(kpis.get('budget_performance', 0)),
        'time_rating': _get_rating(kpis.get('time_performance', 0)),
        'overall_rating': _get_rating(kpis.get('overall_score', 0)),
        'improvement_areas': _identify_improvement_areas(kpis)
    }

def _generate_trend_analysis(dashboard_data: Dict) -> Dict:
    """Generate trend analysis for reports."""
    trends = dashboard_data.get('trends', {}).get('monthly_trends', [])
    
    if len(trends) < 2:
        return {'growth_rate': 0, 'trend_direction': 'stable'}
    
    # Calculate growth rate between last two months
    current = trends[-1]['amount_paid'] if trends else 0
    previous = trends[-2]['amount_paid'] if len(trends) > 1 else current
    
    growth_rate = ((current - previous) / previous * 100) if previous > 0 else 0
    
    trend_direction = 'up' if growth_rate > 5 else 'down' if growth_rate < -5 else 'stable'
    
    return {
        'growth_rate': round(growth_rate, 1),
        'trend_direction': trend_direction
    }

def _get_rating(score: float) -> str:
    """Get performance rating based on score."""
    if score >= 90:
        return 'excellent'
    elif score >= 80:
        return 'good'
    elif score >= 70:
        return 'fair'
    else:
        return 'poor'

def _identify_improvement_areas(kpis: Dict) -> List[str]:
    """Identify areas needing improvement based on KPIs."""
    areas = []
    
    if kpis.get('project_efficiency', 0) < 70:
        areas.append('Eficiencia de Proyectos')
    
    if kpis.get('budget_performance', 0) < 80:
        areas.append('Gestión de Presupuesto')
    
    if kpis.get('time_performance', 0) < 70:
        areas.append('Gestión de Tiempo')
    
    if kpis.get('quality_score', 0) < 75:
        areas.append('Control de Calidad')
    
    return areas

def _get_manager_name():
    """Helper function to get the manager name based on current user role."""
    if current_user.rol == 'jefe_proyecto':
        return current_user.nombre_completo or current_user.username
    elif current_user.rol == 'miembro_equipo_proyecto':
        manager_name = current_user.jefe_asignado
        if not manager_name:
            raise ValueError('No tiene un jefe de proyecto asignado')
        return manager_name
    else:
        # For higher roles (director, admin), use their own name
        return current_user.nombre_completo or current_user.username
