"""
Email notification routes for managing email alerts and notifications.
"""
import logging
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from ..services.email_service import EmailService
from ..tasks.email_tasks import (
    send_critical_edp_alerts, 
    send_payment_reminders, 
    send_weekly_summary,
    send_system_alert,
    test_email_service
)
from ..utils.auth_utils import require_manager_or_above

logger = logging.getLogger(__name__)

email_bp = Blueprint('email_notifications', __name__)

@email_bp.route("/api/email/status")
@login_required
@require_manager_or_above
def email_status():
    """
    Get email service status and configuration.
    """
    try:
        email_service = EmailService()
        
        status = {
            "enabled": email_service.is_enabled(),
            "configured": bool(email_service.email_config.mail_username),
            "server": email_service.email_config.mail_server,
            "port": email_service.email_config.mail_port,
            "use_tls": email_service.email_config.mail_use_tls,
            "default_sender": email_service.email_config.mail_default_sender,
            "features": {
                "critical_alerts": email_service.email_config.enable_critical_alerts,
                "payment_reminders": email_service.email_config.enable_payment_reminders,
                "weekly_summary": email_service.email_config.enable_weekly_summary,
                "system_alerts": email_service.email_config.enable_system_alerts
            },
            "thresholds": {
                "critical_edp_days": email_service.email_config.critical_edp_days,
                "payment_reminder_days": email_service.email_config.payment_reminder_days,
                "weekly_summary_day": email_service.email_config.weekly_summary_day
            }
        }
        
        return jsonify({
            "success": True,
            "data": status
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting email status: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting email status: {str(e)}"
        }), 500

@email_bp.route("/api/email/test", methods=["POST"])
@login_required
@require_manager_or_above
def test_email():
    """
    Send a test email to verify the configuration.
    """
    try:
        # Usar el worker independiente
        from ..services.email_worker_service import email_worker_service
        
        result = email_worker_service.send_test_email()
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Test email queued successfully",
                "task_id": result['task_id']
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Error queuing test email: {result.get('error', 'Unknown error')}"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error queuing test email: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error queuing test email: {str(e)}"
        }), 500

@email_bp.route("/api/email/test/status/<task_id>")
@login_required
@require_manager_or_above
def test_email_status(task_id):
    """
    Check the status of a test email task.
    """
    try:
        from .. import celery
        
        task = celery.AsyncResult(task_id)
        
        if task.state == "PENDING":
            response = {"state": task.state, "status": "Task is waiting..."}
        elif task.state == "PROGRESS":
            response = {
                "state": task.state,
                "status": task.info.get("status", ""),
                "current": task.info.get("current", 0),
                "total": task.info.get("total", 1),
            }
        elif task.state == "SUCCESS":
            response = {
                "state": task.state,
                "status": "Test email sent successfully!",
                "result": task.result,
            }
        else:
            response = {
                "state": task.state,
                "status": str(task.info),
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error checking test email status: {str(e)}")
        return jsonify({
            "state": "ERROR",
            "status": f"Error checking task status: {str(e)}"
        }), 500

@email_bp.route("/api/email/send-critical-alerts")
@login_required
@require_manager_or_above
def send_critical_alerts_manual():
    """
    Manually trigger critical EDP alerts.
    """
    try:
        # Usar el worker independiente con datos reales
        from ..services.email_worker_service import email_worker_service
        from ..services.manager_service import ManagerService
        
        # Obtener datos reales de EDPs críticos
        manager_service = ManagerService()
        critical_response = manager_service.get_critical_projects_data({})
        
        if not critical_response.success:
            return jsonify({
                "success": False,
                "message": f"Error getting critical EDPs: {critical_response.message}"
            }), 500
        
        critical_edps = critical_response.data.get("critical_projects", [])
        
        if not critical_edps:
            return jsonify({
                "success": True,
                "message": "No critical EDPs found",
                "critical_edps_count": 0
            })
        
        # Obtener destinatarios
        from ..utils.auth_utils import get_all_manager_recipients
        recipients = get_all_manager_recipients()
        
        if not recipients:
            return jsonify({
                "success": False,
                "message": "No recipients found for critical alerts"
            }), 500
        
        # Enviar alertas usando el worker independiente
        result = email_worker_service.send_critical_alerts(critical_edps, recipients)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Critical alerts queued successfully",
                "task_id": result['task_id'],
                "critical_edps_count": len(critical_edps),
                "recipients_count": len(recipients)
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Error queuing critical alerts: {result.get('error', 'Unknown error')}"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error queuing critical alerts: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error queuing critical alerts: {str(e)}"
        }), 500

@email_bp.route("/api/email/send-payment-reminders")
@login_required
@require_manager_or_above
def send_payment_reminders_manual():
    """
    Manually trigger payment reminders.
    """
    try:
        # Queue the payment reminders task
        task = send_payment_reminders.delay()
        
        return jsonify({
            "success": True,
            "message": "Payment reminders queued successfully",
            "task_id": task.id
        })
        
    except Exception as e:
        logger.error(f"❌ Error queuing payment reminders: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error queuing payment reminders: {str(e)}"
        }), 500

@email_bp.route("/api/email/send-weekly-summary")
@login_required
@require_manager_or_above
def send_weekly_summary_manual():
    """
    Manually trigger weekly summary.
    """
    try:
        # Usar el worker independiente con datos reales
        from ..services.email_worker_service import email_worker_service
        from ..services.manager_service import ManagerService
        
        # Obtener datos reales de KPIs
        manager_service = ManagerService()
        dashboard_response = manager_service.get_manager_dashboard_data_sync()
        
        if not dashboard_response.success:
            return jsonify({
                "success": False,
                "message": f"Error getting KPIs data: {dashboard_response.message}"
            }), 500
        
        kpis_data = dashboard_response.data.get("executive_kpis", {})
        
        # Preparar datos del resumen semanal
        weekly_data = {
            "total_edps": kpis_data.get("total_edps", 0),
            "total_monto": kpis_data.get("total_monto", 0),
            "dso_promedio": kpis_data.get("dso_promedio", 0),
            "edps_criticos": kpis_data.get("edps_criticos", 0),
            "edps_aprobados_semana": kpis_data.get("edps_aprobados_semana", 0),
            "edps_pagados_semana": kpis_data.get("edps_pagados_semana", 0),
            "monto_cobrado_semana": kpis_data.get("monto_cobrado_semana", 0)
        }
        
        # Obtener destinatarios
        from ..utils.auth_utils import get_all_manager_recipients
        recipients = get_all_manager_recipients()
        
        if not recipients:
            return jsonify({
                "success": False,
                "message": "No recipients found for weekly summary"
            }), 500
        
        # Enviar resumen semanal usando el worker independiente
        result = email_worker_service.send_weekly_summary(weekly_data, recipients)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Weekly summary queued successfully",
                "task_id": result['task_id'],
                "recipients_count": len(recipients)
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Error queuing weekly summary: {result.get('error', 'Unknown error')}"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error queuing weekly summary: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error queuing weekly summary: {str(e)}"
        }), 500

@email_bp.route("/api/email/send-system-alert", methods=["POST"])
@login_required
@require_manager_or_above
def send_system_alert_manual():
    """
    Manually send a system alert email.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        # Validate required fields
        required_fields = ["title", "description"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Prepare alert data
        alert_data = {
            "title": data["title"],
            "description": data["description"],
            "severity": data.get("severity", "medium"),
            "timestamp": data.get("timestamp")
        }
        
        # Queue the system alert task
        task = send_system_alert.delay(alert_data)
        
        return jsonify({
            "success": True,
            "message": "System alert queued successfully",
            "task_id": task.id
        })
        
    except Exception as e:
        logger.error(f"❌ Error queuing system alert: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error queuing system alert: {str(e)}"
        }), 500

@email_bp.route("/api/email/task-status/<task_id>")
@login_required
@require_manager_or_above
def email_task_status(task_id):
    """
    Check the status of any email task.
    """
    try:
        # Usar el worker independiente
        from ..services.email_worker_service import email_worker_service
        
        response = email_worker_service.get_task_status(task_id)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error checking task status: {str(e)}")
        return jsonify({
            "state": "ERROR",
            "status": f"Error checking task status: {str(e)}"
        }), 500

@email_bp.route("/api/email/recipients")
@login_required
@require_manager_or_above
def get_email_recipients():
    """
    Get list of email recipients by role.
    """
    try:
        from ..models.user import User
        from ..extensions import db
        
        # Get all users with email addresses
        users = User.query.all()
        recipients_by_role = {}
        
        for user in users:
            email = None
            if hasattr(user, 'email') and user.email:
                email = user.email
            elif hasattr(user, 'username') and '@' in user.username:
                email = user.username
            
            if email:
                role = getattr(user, 'rol', 'user')
                if role not in recipients_by_role:
                    recipients_by_role[role] = []
                recipients_by_role[role].append({
                    "email": email,
                    "username": getattr(user, 'username', ''),
                    "nombre_completo": getattr(user, 'nombre_completo', '')
                })
        
        return jsonify({
            "success": True,
            "data": recipients_by_role
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting email recipients: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting email recipients: {str(e)}"
        }), 500

# ========================================
# ENDPOINTS DE PRUEBA SIN AUTENTICACIÓN
# ========================================

@email_bp.route("/api/email/test/status")
def email_status_test():
    """
    Get email service status and configuration (NO AUTH REQUIRED).
    """
    try:
        email_service = EmailService()
        
        status = {
            "enabled": email_service.is_enabled(),
            "configured": bool(email_service.email_config.mail_username),
            "server": email_service.email_config.mail_server,
            "port": email_service.email_config.mail_port,
            "use_tls": email_service.email_config.mail_use_tls,
            "default_sender": email_service.email_config.mail_default_sender,
            "test_recipient": email_service.email_config.test_email_recipient,
            "features": {
                "critical_alerts": email_service.email_config.enable_critical_alerts,
                "payment_reminders": email_service.email_config.enable_payment_reminders,
                "weekly_summary": email_service.email_config.enable_weekly_summary,
                "system_alerts": email_service.email_config.enable_system_alerts
            },
            "thresholds": {
                "critical_edp_days": email_service.email_config.critical_edp_days,
                "payment_reminder_days": email_service.email_config.payment_reminder_days,
                "weekly_summary_day": email_service.email_config.weekly_summary_day
            }
        }
        
        return jsonify({
            "success": True,
            "data": status
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting email status: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting email status: {str(e)}"
        }), 500

@email_bp.route("/api/email/test/send", methods=["POST"])
def test_email_no_auth():
    """
    Send a test email to verify the configuration (NO AUTH REQUIRED).
    """
    try:
        # Queue the test email task
        task = test_email_service.delay()
        
        return jsonify({
            "success": True,
            "message": "Test email queued successfully",
            "task_id": task.id
        })
        
    except Exception as e:
        logger.error(f"❌ Error queuing test email: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error queuing test email: {str(e)}"
        }), 500

@email_bp.route("/api/email/test/recipients")
def get_email_recipients_test():
    """
    Get list of email recipients by role (NO AUTH REQUIRED).
    """
    try:
        from ..models.user import User
        from ..extensions import db
        
        # Get all users with email addresses
        users = User.query.all()
        recipients_by_role = {}
        
        for user in users:
            email = None
            if hasattr(user, 'email') and user.email:
                email = user.email
            elif hasattr(user, 'username') and '@' in user.username:
                email = user.username
            
            if email:
                role = getattr(user, 'rol', 'user')
                if role not in recipients_by_role:
                    recipients_by_role[role] = []
                recipients_by_role[role].append({
                    "email": email,
                    "username": getattr(user, 'username', ''),
                    "nombre_completo": getattr(user, 'nombre_completo', '')
                })
        
        # Add test email if no recipients found
        if not any(recipients_by_role.values()):
            from ..config import get_config
            config = get_config()
            test_email = config.email.test_email_recipient
            if test_email:
                recipients_by_role["test"] = [{
                    "email": test_email,
                    "username": "test",
                    "nombre_completo": "Email de Prueba"
                }]
        
        return jsonify({
            "success": True,
            "data": recipients_by_role
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting email recipients: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting email recipients: {str(e)}"
        }), 500

@email_bp.route("/api/email/test/task-status/<task_id>")
def email_task_status_test(task_id):
    """
    Check the status of any email task (NO AUTH REQUIRED).
    """
    try:
        from .. import celery
        
        task = celery.AsyncResult(task_id)
        
        if task.state == "PENDING":
            response = {"state": task.state, "status": "Task is waiting..."}
        elif task.state == "PROGRESS":
            response = {
                "state": task.state,
                "status": task.info.get("status", ""),
                "current": task.info.get("current", 0),
                "total": task.info.get("total", 1),
            }
        elif task.state == "SUCCESS":
            response = {
                "state": task.state,
                "status": "Task completed successfully!",
                "result": task.result,
            }
        else:
            response = {
                "state": task.state,
                "status": str(task.info),
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error checking task status: {str(e)}")
        return jsonify({
            "state": "ERROR",
            "status": f"Error checking task status: {str(e)}"
        }), 500

@email_bp.route('/api/email/send-overdue-alerts', methods=['POST'])
@login_required
@require_manager_or_above
def send_overdue_alerts_manual():
    """Enviar alertas de EDPs vencidos manualmente."""
    try:
        from ..services.manager_service import ManagerService
        from ..services.email_worker_service import email_worker_service
        
        # Obtener datos de EDPs vencidos
        manager_service = ManagerService()
        edps_response = manager_service.edp_repo.find_all_dataframe()
        
        if isinstance(edps_response, dict) and not edps_response.get("success", False):
            return jsonify({
                "success": False,
                "message": f"Error obteniendo EDPs: {edps_response.get('message', 'Unknown error')}"
            }), 500
        
        df_edp = edps_response.get("data", [])
        
        # Configurar umbral de días (puede venir del request)
        overdue_days_threshold = request.json.get('overdue_days', 60) if request.is_json else 60
        
        # Filtrar EDPs vencidos
        overdue_edps = []
        for _, edp in df_edp.iterrows():
            dso_actual = edp.get('dso_actual', 0)
            if dso_actual and dso_actual > overdue_days_threshold:
                overdue_edps.append({
                    'n_edp': edp.get('n_edp', 'N/A'),
                    'cliente': edp.get('cliente', 'N/A'),
                    'proyecto': edp.get('proyecto', 'N/A'),
                    'monto': float(edp.get('monto_aprobado', 0)),
                    'dso_actual': int(dso_actual),
                    'estado': edp.get('estado', 'N/A'),
                    'fecha_emision': edp.get('fecha_emision', 'N/A')
                })
        
        # Obtener destinatarios
        from ..tasks.email_tasks import get_all_manager_recipients
        recipients = get_all_manager_recipients()
        
        if not recipients:
            return jsonify({
                "success": False,
                "message": "No se encontraron destinatarios para las alertas"
            }), 400
        
        # Enviar alertas
        result = email_worker_service.send_overdue_edp_alerts(overdue_edps, recipients)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Alertas de EDPs vencidos enviadas",
                "task_id": result['task_id'],
                "overdue_edps_count": len(overdue_edps),
                "recipients_count": len(recipients),
                "overdue_days_threshold": overdue_days_threshold
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Error enviando alertas: {result.get('error', 'Unknown error')}"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error sending overdue alerts: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error interno: {str(e)}"
        }), 500 