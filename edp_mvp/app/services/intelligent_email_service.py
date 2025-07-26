"""
Intelligent Email Service with role-based filtering.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .email_service import EmailService
from .email_permissions_service import EmailPermissionsService, EmailPermission, EmailRole

logger = logging.getLogger(__name__)

class IntelligentEmailService:
    """Intelligent email service with role-based data filtering."""
    
    def __init__(self):
        self.email_service = EmailService()
        self.permissions_service = EmailPermissionsService()
    
    def send_weekly_summary_intelligent(self, kpis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send weekly summary with intelligent filtering based on user roles.
        
        Args:
            kpis_data: Raw KPIs data
            
        Returns:
            Dict[str, Any]: Results of email sending
        """
        try:
            # Obtener todos los destinatarios que pueden recibir resumen semanal
            recipients = self.permissions_service.get_recipients_for_permission(
                EmailPermission.WEEKLY_SUMMARY
            )
            
            results = {
                "total_recipients": len(recipients),
                "successful_sends": 0,
                "failed_sends": 0,
                "per_recipient_results": {}
            }
            
            for recipient in recipients:
                try:
                    # Filtrar datos según el rol del usuario
                    filtered_data = self.permissions_service.filter_data_by_role(
                        kpis_data, recipient, "weekly_summary"
                    )
                    
                    # Enviar email personalizado
                    success = self.email_service.send_weekly_summary(
                        filtered_data, [recipient]
                    )
                    
                    if success:
                        results["successful_sends"] += 1
                        results["per_recipient_results"][recipient] = {
                            "status": "success",
                            "role": self.permissions_service.get_user_role(recipient).value,
                            "data_filtered": True
                        }
                    else:
                        results["failed_sends"] += 1
                        results["per_recipient_results"][recipient] = {
                            "status": "failed",
                            "role": self.permissions_service.get_user_role(recipient).value,
                            "data_filtered": True
                        }
                
                except Exception as e:
                    logger.error(f"Error sending weekly summary to {recipient}: {e}")
                    results["failed_sends"] += 1
                    results["per_recipient_results"][recipient] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            logger.info(f"📧 Weekly summary sent: {results['successful_sends']} successful, {results['failed_sends']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in intelligent weekly summary: {e}")
            return {
                "total_recipients": 0,
                "successful_sends": 0,
                "failed_sends": 0,
                "error": str(e)
            }
    
    def send_critical_alerts_intelligent(self, critical_edps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send critical alerts with intelligent filtering.
        
        Args:
            critical_edps: List of critical EDPs
            
        Returns:
            Dict[str, Any]: Results of email sending
        """
        try:
            # Obtener destinatarios para alertas críticas
            recipients = self.permissions_service.get_recipients_for_permission(
                EmailPermission.CRITICAL_ALERTS
            )
            
            results = {
                "total_recipients": len(recipients),
                "successful_sends": 0,
                "failed_sends": 0,
                "per_recipient_results": {}
            }
            
            for recipient in recipients:
                try:
                    # Filtrar alertas según el rol
                    filtered_alerts = self.permissions_service.filter_data_by_role(
                        critical_edps, recipient, "critical_alerts"
                    )
                    
                    if filtered_alerts:  # Solo enviar si hay alertas para este usuario
                        success = self.email_service.send_bulk_critical_alerts(
                            filtered_alerts, [recipient]
                        )
                        
                        if success:
                            results["successful_sends"] += 1
                            results["per_recipient_results"][recipient] = {
                                "status": "success",
                                "role": self.permissions_service.get_user_role(recipient).value,
                                "alerts_count": len(filtered_alerts)
                            }
                        else:
                            results["failed_sends"] += 1
                            results["per_recipient_results"][recipient] = {
                                "status": "failed",
                                "role": self.permissions_service.get_user_role(recipient).value,
                                "alerts_count": len(filtered_alerts)
                            }
                    else:
                        # No hay alertas para este usuario
                        results["per_recipient_results"][recipient] = {
                            "status": "skipped",
                            "role": self.permissions_service.get_user_role(recipient).value,
                            "reason": "no_alerts_for_user"
                        }
                
                except Exception as e:
                    logger.error(f"Error sending critical alerts to {recipient}: {e}")
                    results["failed_sends"] += 1
                    results["per_recipient_results"][recipient] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            logger.info(f"🚨 Critical alerts sent: {results['successful_sends']} successful, {results['failed_sends']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in intelligent critical alerts: {e}")
            return {
                "total_recipients": 0,
                "successful_sends": 0,
                "failed_sends": 0,
                "error": str(e)
            }
    
    def send_payment_reminders_intelligent(self, reminder_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send payment reminders with intelligent filtering.
        
        Args:
            reminder_data: List of payment reminders
            
        Returns:
            Dict[str, Any]: Results of email sending
        """
        try:
            # Obtener destinatarios para recordatorios de pago
            recipients = self.permissions_service.get_recipients_for_permission(
                EmailPermission.PAYMENT_REMINDERS
            )
            
            results = {
                "total_recipients": len(recipients),
                "successful_sends": 0,
                "failed_sends": 0,
                "per_recipient_results": {}
            }
            
            for recipient in recipients:
                try:
                    # Filtrar recordatorios según el rol
                    filtered_reminders = self.permissions_service.filter_data_by_role(
                        reminder_data, recipient, "payment_reminders"
                    )
                    
                    if filtered_reminders:
                        # Enviar recordatorios individuales o en bulk según el caso
                        success = self._send_payment_reminders_to_user(
                            filtered_reminders, recipient
                        )
                        
                        if success:
                            results["successful_sends"] += 1
                            results["per_recipient_results"][recipient] = {
                                "status": "success",
                                "role": self.permissions_service.get_user_role(recipient).value,
                                "reminders_count": len(filtered_reminders)
                            }
                        else:
                            results["failed_sends"] += 1
                            results["per_recipient_results"][recipient] = {
                                "status": "failed",
                                "role": self.permissions_service.get_user_role(recipient).value,
                                "reminders_count": len(filtered_reminders)
                            }
                    else:
                        results["per_recipient_results"][recipient] = {
                            "status": "skipped",
                            "role": self.permissions_service.get_user_role(recipient).value,
                            "reason": "no_reminders_for_user"
                        }
                
                except Exception as e:
                    logger.error(f"Error sending payment reminders to {recipient}: {e}")
                    results["failed_sends"] += 1
                    results["per_recipient_results"][recipient] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            logger.info(f"💰 Payment reminders sent: {results['successful_sends']} successful, {results['failed_sends']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in intelligent payment reminders: {e}")
            return {
                "total_recipients": 0,
                "successful_sends": 0,
                "failed_sends": 0,
                "error": str(e)
            }
    
    def _send_payment_reminders_to_user(self, reminders: List[Dict[str, Any]], 
                                       recipient: str) -> bool:
        """Send payment reminders to a specific user."""
        try:
            # Para controllers y finance, enviar todos los recordatorios en un email
            user_role = self.permissions_service.get_user_role(recipient)
            
            if user_role in [EmailRole.CONTROLLER, EmailRole.FINANCE]:
                # Enviar resumen de todos los recordatorios
                return self.email_service.send_bulk_critical_alerts(
                    reminders, [recipient]
                )
            else:
                # Para clientes, enviar recordatorios individuales
                success_count = 0
                for reminder in reminders:
                    success = self.email_service.send_payment_reminder(
                        reminder, [recipient]
                    )
                    if success:
                        success_count += 1
                
                return success_count == len(reminders)
        
        except Exception as e:
            logger.error(f"Error sending payment reminders to {recipient}: {e}")
            return False
    
    def send_custom_email_intelligent(self, email_type: str, data: Dict[str, Any], 
                                     custom_recipients: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send custom email with intelligent filtering.
        
        Args:
            email_type: Type of email (weekly_summary, critical_alerts, etc.)
            data: Email data
            custom_recipients: Optional custom recipient list
            
        Returns:
            Dict[str, Any]: Results of email sending
        """
        try:
            if custom_recipients:
                recipients = custom_recipients
            else:
                # Obtener destinatarios basados en el tipo de email
                permission_map = {
                    "weekly_summary": EmailPermission.WEEKLY_SUMMARY,
                    "critical_alerts": EmailPermission.CRITICAL_ALERTS,
                    "payment_reminders": EmailPermission.PAYMENT_REMINDERS
                }
                
                permission = permission_map.get(email_type, EmailPermission.ALL_DATA)
                recipients = self.permissions_service.get_recipients_for_permission(permission)
            
            results = {
                "total_recipients": len(recipients),
                "successful_sends": 0,
                "failed_sends": 0,
                "per_recipient_results": {}
            }
            
            for recipient in recipients:
                try:
                    # Filtrar datos según el rol
                    filtered_data = self.permissions_service.filter_data_by_role(
                        data, recipient, email_type
                    )
                    
                    # Enviar email según el tipo
                    success = self._send_email_by_type(email_type, filtered_data, [recipient])
                    
                    if success:
                        results["successful_sends"] += 1
                        results["per_recipient_results"][recipient] = {
                            "status": "success",
                            "role": self.permissions_service.get_user_role(recipient).value
                        }
                    else:
                        results["failed_sends"] += 1
                        results["per_recipient_results"][recipient] = {
                            "status": "failed",
                            "role": self.permissions_service.get_user_role(recipient).value
                        }
                
                except Exception as e:
                    logger.error(f"Error sending {email_type} to {recipient}: {e}")
                    results["failed_sends"] += 1
                    results["per_recipient_results"][recipient] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in custom intelligent email: {e}")
            return {
                "total_recipients": 0,
                "successful_sends": 0,
                "failed_sends": 0,
                "error": str(e)
            }
    
    def _send_email_by_type(self, email_type: str, data: Dict[str, Any], 
                           recipients: List[str]) -> bool:
        """Send email based on type."""
        try:
            if email_type == "weekly_summary":
                return self.email_service.send_weekly_summary(data, recipients)
            elif email_type == "critical_alerts":
                return self.email_service.send_bulk_critical_alerts(data, recipients)
            elif email_type == "payment_reminders":
                return self.email_service.send_bulk_critical_alerts(data, recipients)
            elif email_type == "system_alert":
                return self.email_service.send_system_alert(data, recipients)
            elif email_type == "performance_report":
                return self.email_service.send_performance_report(data, recipients)
            else:
                logger.warning(f"Unknown email type: {email_type}")
                return False
        except Exception as e:
            logger.error(f"Error sending {email_type} email: {e}")
            return False 