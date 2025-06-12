"""
Refactored EDP Controller using the new layered architecture.
This demonstrates how the monolithic controller can be restructured.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from typing import Dict, Any, Optional
from datetime import datetime

from ..services.edp_service import EDPService
from ..services.controller_service import ControllerService
from ..services.kpi_service import KPIService
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils


# Create Blueprint
edp_controller_bp = Blueprint("edp_controller", __name__, url_prefix="/edp")

# Initialize services
edp_service = EDPService()
controller_service = ControllerService()
kpi_service = KPIService()


@edp_controller_bp.route("/")
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


@edp_controller_bp.route("/list")
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


@edp_controller_bp.route("/<edp_id>")
@login_required
def view_edp(edp_id: str):
    """View detailed information for a specific EDP."""
    try:
        # Get EDP details
        edp_response = edp_service.get_edp_by_id(edp_id)
        
        if not edp_response.success:
            flash(f"EDP not found: {edp_response.message}", "error")
            return redirect(url_for('edp_controller.list_edps'))
        
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
        return redirect(url_for('edp_controller.list_edps'))


@edp_controller_bp.route("/create", methods=["GET", "POST"])
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
                return redirect(url_for('edp_controller.view_edp', edp_id=create_response.data['id']))
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


@edp_controller_bp.route("/<edp_id>/edit", methods=["GET", "POST"])
@login_required
def edit_edp(edp_id: str):
    """Edit an existing EDP."""
    if request.method == "GET":
        # Get EDP for editing
        edp_response = edp_service.get_edp_by_id(edp_id)
        
        if not edp_response.success:
            flash(f"EDP not found: {edp_response.message}", "error")
            return redirect(url_for('edp_controller.list_edps'))
        
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
                return redirect(url_for('edp_controller.view_edp', edp_id=edp_id))
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
            return redirect(url_for('edp_controller.view_edp', edp_id=edp_id))


@edp_controller_bp.route("/<edp_id>/kpis", methods=["GET", "POST"])
@login_required
def manage_kpis(edp_id: str):
    """Manage KPIs for an EDP."""
    if request.method == "GET":
        # Get current KPIs
        kpi_response = kpi_service.calculate_edp_kpis(edp_id)
        
        if not kpi_response.success:
            flash(f"Error loading KPIs: {kpi_response.message}", "error")
            return redirect(url_for('edp_controller.view_edp', edp_id=edp_id))
        
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
        
        return redirect(url_for('edp_controller.manage_kpis', edp_id=edp_id))
    
    except Exception as e:
        error_message = f"Error updating KPI targets: {str(e)}"
        if request.is_json:
            return jsonify({'success': False, 'message': error_message}), 500
        else:
            flash(error_message, "error")
            return redirect(url_for('edp_controller.view_edp', edp_id=edp_id))


@edp_controller_bp.route("/statistics")
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
@edp_controller_bp.route("/api/health-scores")
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


@edp_controller_bp.route("/api/recent-activity")
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


@edp_controller_bp.route("/api/alerts")
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
@edp_controller_bp.app_template_filter('format_currency')
def format_currency_filter(amount):
    """Template filter to format currency."""
    return FormatUtils.format_currency(amount)


@edp_controller_bp.app_template_filter('format_percentage')
def format_percentage_filter(value):
    """Template filter to format percentage."""
    return FormatUtils.format_percentage(value)


@edp_controller_bp.app_template_filter('format_date')
def format_date_filter(date_value):
    """Template filter to format dates."""
    return DateUtils.format_date(date_value)


@edp_controller_bp.app_template_filter('relative_time')
def relative_time_filter(date_value):
    """Template filter to get relative time."""
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value)
        except ValueError:
            return date_value
    return DateUtils.get_relative_time_string(date_value)


@edp_controller_bp.app_template_filter('status_badge')
def status_badge_filter(status):
    """Template filter to format status badge."""
    return FormatUtils.format_status_badge(status)


@edp_controller_bp.app_template_filter('priority_badge')
def priority_badge_filter(priority):
    """Template filter to format priority badge."""
    return FormatUtils.format_priority_badge(priority)


@edp_controller_bp.app_template_filter('health_score')
def health_score_filter(score):
    """Template filter to format health score."""
    return FormatUtils.format_health_score(score)
