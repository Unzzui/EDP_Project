"""
Servicio para integrar el worker independiente de email con la aplicación Flask.
"""
import os
import sys
import logging
from typing import Dict, Any, List
from pathlib import Path

# Agregar el directorio raíz al path para importar el worker independiente
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class EmailWorkerService:
    """Servicio para manejar emails usando el worker independiente."""
    
    def __init__(self):
        try:
            # Importar el adaptador del worker independiente
            from email_worker_adapter import email_adapter
            self.adapter = email_adapter
            self.available = True
            logger.info("✅ Email worker service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing email worker service: {str(e)}")
            self.available = False
    
    def is_available(self) -> bool:
        """Verificar si el servicio está disponible."""
        return self.available
    
    def send_test_email(self, test_recipient: str = None) -> Dict[str, Any]:
        """Enviar email de prueba usando el worker independiente."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        
        try:
            if not test_recipient:
                test_recipient = os.getenv('TEST_EMAIL_RECIPIENT', 'diegobravobe@gmail.com')
            
            result = self.adapter.test_email_service(test_recipient)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending test email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_critical_alerts(self, critical_edps: List[Dict], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alertas de EDPs críticos usando el worker independiente."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        
        try:
            result = self.adapter.send_critical_edp_alerts(critical_edps, recipients)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending critical alerts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_payment_reminders(self, reminder_edps: List[Dict], recipients: List[str]) -> Dict[str, Any]:
        """Enviar recordatorios de pago usando el worker independiente."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        
        try:
            result = self.adapter.send_payment_reminders(reminder_edps, recipients)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending payment reminders: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_edp_expiration_alerts(self, expiration_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alertas de vencimiento de EDPs por etapas usando el worker independiente."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        
        try:
            result = self.adapter.send_edp_expiration_alerts(expiration_data, recipients)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending EDP expiration alerts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_overdue_edp_alerts(self, overdue_edps: List[Dict], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alertas de EDPs vencidos."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        try:
            return self.adapter.send_overdue_edp_alerts(overdue_edps, recipients)
        except Exception as e:
            logger.error(f"❌ Error en send_overdue_edp_alerts: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_followup_reminders(self, followup_data: Dict, recipients: List[str]) -> Dict[str, Any]:
        """Enviar recordatorios de seguimiento de EDPs sin movimiento."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        try:
            return self.adapter.send_followup_reminders(followup_data, recipients)
        except Exception as e:
            logger.error(f"❌ Error en send_followup_reminders: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_performance_report(self, performance_data: Dict, recipients: List[str]) -> Dict[str, Any]:
        """Enviar reporte de performance del equipo."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        try:
            return self.adapter.send_performance_report(performance_data, recipients)
        except Exception as e:
            logger.error(f"❌ Error en send_performance_report: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_weekly_summary(self, kpis_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """Enviar resumen semanal usando el worker independiente."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        
        try:
            result = self.adapter.send_weekly_summary(kpis_data, recipients)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending weekly summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_system_alert(self, alert_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alerta del sistema usando el worker independiente."""
        if not self.is_available():
            return {
                "success": False,
                "error": "Email worker service not available"
            }
        
        try:
            result = self.adapter.send_system_alert(alert_data, recipients)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending system alert: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtener el estado de una tarea."""
        if not self.is_available():
            return {
                "state": "ERROR",
                "status": "Email worker service not available"
            }
        
        try:
            result = self.adapter.get_task_status(task_id)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting task status: {str(e)}")
            return {
                "state": "ERROR",
                "status": f"Error getting task status: {str(e)}"
            }

# Instancia global del servicio
email_worker_service = EmailWorkerService() 