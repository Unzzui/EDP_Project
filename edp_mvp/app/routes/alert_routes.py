"""
API endpoints for alert management.
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from ..services.alert_service import EDPAlertService
from ..config.alert_rules import ALERT_RULES, PROJECT_MANAGER_EMAILS, CONTROLLER_EMAILS, MANAGER_EMAILS

logger = logging.getLogger(__name__)

# Create blueprint
alert_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alert_bp.route('/status', methods=['GET'])
def get_alert_status():
    """
    Obtiene el estado del sistema de alertas.
    """
    try:
        alert_service = EDPAlertService()
        
        # Obtener EDPs que requieren alertas
        edps_with_alerts = alert_service.get_edps_for_alerts()
        
        # Calcular estadísticas
        total_edps = len(edps_with_alerts)
        critical_edps = len([e for e in edps_with_alerts if e['is_critical']])
        urgent_edps = len([e for e in edps_with_alerts if e['dias_sin_movimiento'] >= 21 and not e['is_critical']])
        warning_edps = len([e for e in edps_with_alerts if e['dias_sin_movimiento'] >= 14 and e['dias_sin_movimiento'] < 21])
        
        status = {
            'system_enabled': alert_service.email_service.is_enabled(),
            'total_edps_with_alerts': total_edps,
            'critical_edps': critical_edps,
            'urgent_edps': urgent_edps,
            'warning_edps': warning_edps,
            'last_check': datetime.now().isoformat(),
            'alert_rules_count': len(ALERT_RULES),
            'email_config': {
                'service_enabled': alert_service.email_service.is_enabled(),
                'google_sheets_available': bool(alert_service.gsheet_service.get_data())
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de alertas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@alert_bp.route('/trigger', methods=['POST'])
def trigger_alerts():
    """
    Dispara manualmente el envío de alertas progresivas.
    """
    try:
        alert_service = EDPAlertService()
        results = alert_service.send_progressive_alerts()
        
        return jsonify({
            'status': 'success',
            'message': 'Alertas procesadas exitosamente',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error disparando alertas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@alert_bp.route('/critical-summary', methods=['POST'])
def send_critical_summary():
    """
    Envía manualmente el resumen de EDPs críticos.
    """
    try:
        alert_service = EDPAlertService()
        results = alert_service.send_daily_critical_summary()
        
        return jsonify({
            'status': 'success',
            'message': 'Resumen crítico enviado',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error enviando resumen crítico: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@alert_bp.route('/history', methods=['GET'])
def get_alert_history():
    """
    Obtiene el historial de alertas enviadas.
    """
    try:
        n_edp = request.args.get('n_edp')
        limit = int(request.args.get('limit', 50))
        
        alert_service = EDPAlertService()
        history = alert_service.get_alert_history(n_edp, limit)
        
        return jsonify({
            'status': 'success',
            'data': {
                'alerts': history,
                'total': len(history),
                'filter': {'n_edp': n_edp, 'limit': limit}
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo historial de alertas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@alert_bp.route('/test', methods=['POST'])
def test_alert_system():
    """
    Prueba el sistema de alertas.
    """
    try:
        data = request.json or {}
        test_email = data.get('test_email')
        
        alert_service = EDPAlertService()
        results = alert_service.test_alert_system(test_email)
        
        return jsonify({
            'status': 'success',
            'message': 'Prueba del sistema completada',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error en prueba del sistema: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@alert_bp.route('/rules', methods=['GET'])
def get_alert_rules():
    """
    Obtiene las reglas de alertas configuradas.
    """
    try:
        rules_data = []
        
        for rule in ALERT_RULES:
            rules_data.append({
                'day_threshold': rule.day_threshold,
                'alert_level': rule.alert_level.value,
                'frequency_hours': rule.frequency_hours,
                'subject_template': rule.subject_template,
                'message_template': rule.message_template,
                'recipients_type': rule.recipients_type
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'rules': rules_data,
                'total_rules': len(rules_data),
                'recipients_config': {
                    'project_managers': len(PROJECT_MANAGER_EMAILS),
                    'controllers': len(CONTROLLER_EMAILS),
                    'managers': len(MANAGER_EMAILS)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo reglas de alertas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@alert_bp.route('/edps-with-alerts', methods=['GET'])
def get_edps_with_alerts():
    """
    Obtiene la lista de EDPs que requieren alertas.
    """
    try:
        alert_service = EDPAlertService()
        edps_with_alerts = alert_service.get_edps_for_alerts()
        
        # Filtrar por parámetros de consulta
        alert_level = request.args.get('alert_level')
        min_days = request.args.get('min_days', type=int)
        max_days = request.args.get('max_days', type=int)
        
        filtered_edps = edps_with_alerts
        
        if alert_level:
            filtered_edps = [
                edp for edp in filtered_edps 
                if any(rule['alert_level'] == alert_level for rule in edp['alert_rules_triggered'])
            ]
        
        if min_days is not None:
            filtered_edps = [
                edp for edp in filtered_edps 
                if edp['dias_sin_movimiento'] >= min_days
            ]
        
        if max_days is not None:
            filtered_edps = [
                edp for edp in filtered_edps 
                if edp['dias_sin_movimiento'] <= max_days
            ]
        
        return jsonify({
            'status': 'success',
            'data': {
                'edps': filtered_edps,
                'total': len(filtered_edps),
                'total_unfiltered': len(edps_with_alerts),
                'filters': {
                    'alert_level': alert_level,
                    'min_days': min_days,
                    'max_days': max_days
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo EDPs con alertas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@alert_bp.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """
    Obtiene datos para el dashboard de alertas.
    """
    try:
        alert_service = EDPAlertService()
        edps_with_alerts = alert_service.get_edps_for_alerts()
        
        # Agrupar por nivel de alerta
        alert_levels = {'info': 0, 'warning': 0, 'urgent': 0, 'critical': 0}
        edps_by_project_manager = {}
        edps_by_client = {}
        
        for edp in edps_with_alerts:
            # Contar por nivel de alerta (usar el más alto)
            highest_level = 'info'
            for rule in edp['alert_rules_triggered']:
                if rule['alert_level'] == 'critical':
                    highest_level = 'critical'
                elif rule['alert_level'] == 'urgent' and highest_level != 'critical':
                    highest_level = 'urgent'
                elif rule['alert_level'] == 'warning' and highest_level not in ['critical', 'urgent']:
                    highest_level = 'warning'
            
            alert_levels[highest_level] += 1
            
            # Agrupar por jefe de proyecto
            jefe = edp['jefe_proyecto']
            if jefe not in edps_by_project_manager:
                edps_by_project_manager[jefe] = {'total': 0, 'critical': 0, 'urgent': 0}
            
            edps_by_project_manager[jefe]['total'] += 1
            if edp['is_critical']:
                edps_by_project_manager[jefe]['critical'] += 1
            elif edp['dias_sin_movimiento'] >= 21:
                edps_by_project_manager[jefe]['urgent'] += 1
            
            # Agrupar por cliente
            cliente = edp['cliente']
            if cliente not in edps_by_client:
                edps_by_client[cliente] = {'total': 0, 'monto_total': 0}
            
            edps_by_client[cliente]['total'] += 1
            edps_by_client[cliente]['monto_total'] += edp['monto_propuesto']
        
        # Obtener historial reciente
        recent_history = alert_service.get_alert_history(limit=10)
        
        dashboard_data = {
            'summary': {
                'total_edps': len(edps_with_alerts),
                'alert_levels': alert_levels,
                'system_status': alert_service.email_service.is_enabled()
            },
            'by_project_manager': edps_by_project_manager,
            'by_client': dict(list(edps_by_client.items())[:10]),  # Top 10 clientes
            'recent_alerts': recent_history,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo datos del dashboard: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
