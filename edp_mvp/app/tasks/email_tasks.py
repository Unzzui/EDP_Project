"""
Celery tasks for email notifications.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .. import celery

logger = logging.getLogger(__name__)

def get_email_service():
    """Get email service instance."""
    from ..services.email_service import EmailService
    return EmailService()

def get_manager_service():
    """Get manager service instance."""
    from ..services.manager_service import ManagerService
    return ManagerService()

def get_recipients_for_role(role: str) -> List[str]:
    """
    Get email recipients for a specific role.
    
    Args:
        role: User role (manager, admin, controller, etc.)
    
    Returns:
        List of email addresses
    """
    try:
        from ..models.user import User
        from ..extensions import db
        
        users = User.query.filter_by(rol=role).all()
        recipients = []
        
        for user in users:
            if hasattr(user, 'email') and user.email:
                recipients.append(user.email)
            elif hasattr(user, 'username') and '@' in user.username:
                recipients.append(user.username)
        
        logger.info(f"📧 Found {len(recipients)} recipients for role {role}")
        return recipients
        
    except Exception as e:
        logger.error(f"❌ Error getting recipients for role {role}: {str(e)}")
        return []

def get_all_manager_recipients() -> List[str]:
    """Get all manager and admin email addresses."""
    recipients = []
    recipients.extend(get_recipients_for_role('manager'))
    recipients.extend(get_recipients_for_role('admin'))
    
    # Si no hay destinatarios, usar el email de prueba
    if not recipients:
        from ..config import get_config
        config = get_config()
        test_email = config.email.test_email_recipient
        if test_email:
            recipients.append(test_email)
            logger.info(f"📧 No se encontraron managers/admins, usando email de prueba: {test_email}")
    
    return list(set(recipients))  # Remove duplicates

@celery.task(bind=True, max_retries=3)
def send_critical_edp_alerts(self):
    """
    Send critical EDP alerts to managers and admins.
    Runs daily to check for EDPs that are critical.
    """
    try:
        logger.info("📧 Starting critical EDP alerts task")
        
        # Create Flask app context
        from .. import create_app
        app = create_app()
        
        with app.app_context():
            email_service = get_email_service()
            manager_service = get_manager_service()
            
            if not email_service.is_enabled():
                logger.warning("📧 Email service not configured, skipping critical alerts")
                return {"success": False, "reason": "email_not_configured"}
            
            # Get critical EDPs
            critical_response = manager_service.get_critical_projects_data({})
            if not critical_response.success:
                logger.error(f"❌ Error getting critical EDPs: {critical_response.message}")
                raise Exception(critical_response.message)
            
            critical_edps = critical_response.data.get("critical_projects", [])
            
            if not critical_edps:
                logger.info("📧 No critical EDPs found")
                return {"success": True, "critical_edps_count": 0}
            
            # Get recipients
            recipients = get_all_manager_recipients()
            if not recipients:
                logger.warning("📧 No recipients found for critical alerts")
                return {"success": False, "reason": "no_recipients"}
            
            # Send alerts
            sent_count = 0
            for edp in critical_edps:
                success = email_service.send_critical_edp_alert(edp, recipients)
                if success:
                    sent_count += 1
            
            logger.info(f"📧 Critical alerts sent: {sent_count}/{len(critical_edps)}")
            return {
                "success": True,
                "sent_count": sent_count,
                "total_count": len(critical_edps),
                "recipients_count": len(recipients)
            }
        
    except Exception as e:
        logger.error(f"❌ Error in critical EDP alerts task: {str(e)}")
        raise

@celery.task(bind=True, max_retries=3)
def send_payment_reminders(self):
    """
    Send payment reminders for EDPs that are approaching critical status.
    Runs daily to check for EDPs that need payment reminders.
    """
    try:
        logger.info("📧 Starting payment reminders task")
        
        # Create Flask app context
        from .. import create_app
        app = create_app()
        
        with app.app_context():
            email_service = get_email_service()
            manager_service = get_manager_service()
            
            if not email_service.is_enabled():
                logger.warning("📧 Email service not configured, skipping payment reminders")
                return {"success": False, "reason": "email_not_configured"}
            
            # Get EDPs that need payment reminders
            reminder_response = manager_service.get_payment_reminder_data({})
            if not reminder_response.success:
                logger.error(f"❌ Error getting payment reminder data: {reminder_response.message}")
                raise Exception(reminder_response.message)
            
            reminder_edps = reminder_response.data.get("reminder_edps", [])
            
            if not reminder_edps:
                logger.info("📧 No EDPs need payment reminders")
                return {"success": True, "reminder_edps_count": 0}
            
            # Get recipients
            recipients = get_all_manager_recipients()
            if not recipients:
                logger.warning("📧 No recipients found for payment reminders")
                return {"success": False, "reason": "no_recipients"}
            
            # Send reminders
            sent_count = 0
            for edp in reminder_edps:
                success = email_service.send_payment_reminder(edp, recipients)
                if success:
                    sent_count += 1
            
            logger.info(f"📧 Payment reminders sent: {sent_count}/{len(reminder_edps)}")
            return {
                "success": True,
                "sent_count": sent_count,
                "total_count": len(reminder_edps),
                "recipients_count": len(recipients)
            }
        
    except Exception as e:
        logger.error(f"❌ Error in payment reminders task: {str(e)}")
        raise

@celery.task(bind=True, max_retries=3)
def send_weekly_summary(self):
    """
    Send weekly summary of KPIs and metrics to managers and admins.
    Runs weekly to provide overview of system performance.
    """
    try:
        logger.info("📧 Starting weekly summary task")
        
        # Create Flask app context
        from .. import create_app
        app = create_app()
        
        with app.app_context():
            email_service = get_email_service()
            manager_service = get_manager_service()
            
            if not email_service.is_enabled():
                logger.warning("📧 Email service not configured, skipping weekly summary")
                return {"success": False, "reason": "email_not_configured"}
            
            # Get weekly KPIs data
            kpis_response = manager_service.get_weekly_kpis_data({})
            if not kpis_response.success:
                logger.error(f"❌ Error getting weekly KPIs: {kpis_response.message}")
                raise Exception(kpis_response.message)
            
            kpis_data = kpis_response.data
            
            # Get recipients
            recipients = get_all_manager_recipients()
            if not recipients:
                logger.warning("📧 No recipients found for weekly summary")
                return {"success": False, "reason": "no_recipients"}
            
            # Send weekly summary
            success = email_service.send_weekly_summary(kpis_data, recipients)
            
            logger.info(f"📧 Weekly summary sent: {success}")
            return {
                "success": success,
                "recipients_count": len(recipients)
            }
        
    except Exception as e:
        logger.error(f"❌ Error in weekly summary task: {str(e)}")
        raise

@celery.task(bind=True, max_retries=3)
def send_system_alert(self, alert_data: Dict[str, Any]):
    """
    Send system alert to managers and admins.
    Used for important system notifications.
    """
    try:
        logger.info("📧 Starting system alert task")
        
        email_service = get_email_service()
        
        if not email_service.is_enabled():
            logger.warning("📧 Email service not configured, skipping system alert")
            return {"success": False, "reason": "email_not_configured"}
        
        # Get recipients
        recipients = get_all_manager_recipients()
        if not recipients:
            logger.warning("📧 No recipients found for system alert")
            return {"success": False, "reason": "no_recipients"}
        
        # Send system alert
        success = email_service.send_system_alert(alert_data, recipients)
        
        logger.info(f"📧 System alert sent: {success}")
        return {
            "success": success,
            "recipients_count": len(recipients)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in system alert task: {str(e)}")
        raise

@celery.task(bind=True, max_retries=3)
def test_email_service(self):
    """
    Test email service functionality.
    Sends a test email to verify the email service is working.
    """
    try:
        logger.info("📧 Starting email service test task")
        
        email_service = get_email_service()
        
        if not email_service.is_enabled():
            logger.warning("📧 Email service not configured")
            return {"success": False, "reason": "email_not_configured"}
        
        # Get test recipient
        from ..config import get_config
        config = get_config()
        test_recipient = config.email.test_email_recipient
        
        if not test_recipient:
            logger.warning("📧 No test email recipient configured")
            return {"success": False, "reason": "no_test_recipient"}
        
        # Send test email
        success = email_service.send_test_email(test_recipient)
        
        logger.info(f"📧 Test email sent: {success}")
        return {
            "success": success,
            "recipient": test_recipient
        }
        
    except Exception as e:
        logger.error(f"❌ Error in email service test task: {str(e)}")
        raise

@celery.task(bind=True)
def simple_test_task(self):
    """Simple test task for debugging."""
    logger.info("🧪 Simple test task starting")
    
    result = {
        "message": "Hello from Flask Celery worker!", 
        "timestamp": datetime.now().isoformat(),
        "task_id": self.request.id
    }
    
    logger.info("🧪 Simple test task completed")
    return result

@celery.task(bind=True)
def flask_context_test_task(self):
    """Test task that requires Flask context."""
    logger.info("🧪 Flask context test task starting")
    
    try:
        from ..models.user import User
        from ..extensions import db
        
        # Try to access database
        user_count = User.query.count()
        
        result = {
            "message": "Flask context test successful!",
            "user_count": user_count,
            "timestamp": datetime.now().isoformat(),
            "task_id": self.request.id
        }
        
        logger.info("🧪 Flask context test task completed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Flask context test failed: {str(e)}")
        raise

@celery.task(bind=True, max_retries=3)
def send_performance_report_task(self, performance_data: Dict[str, Any], recipients: List[str]):
    """
    Send performance report for a specific project manager.
    Used to send detailed performance metrics to project managers.
    """
    try:
        logger.info("📧 Starting performance report task")
        
        email_service = get_email_service()
        
        if not email_service.is_enabled():
            logger.warning("📧 Email service not configured, skipping performance report")
            return {"success": False, "reason": "email_not_configured"}
        
        if not recipients:
            logger.warning("📧 No recipients provided for performance report")
            return {"success": False, "reason": "no_recipients"}
        
        jefe_proyecto = performance_data.get('jefe_proyecto', 'N/A')
        periodo = performance_data.get('periodo', 'semanal')
        
        # Send performance report
        success = email_service.send_performance_report(performance_data, recipients)
        
        logger.info(f"📧 Performance report sent for {jefe_proyecto}: {success}")
        return {
            "success": success,
            "recipients_count": len(recipients),
            "jefe_proyecto": jefe_proyecto,
            "periodo": periodo
        }
        
    except Exception as e:
        logger.error(f"❌ Error in performance report task: {str(e)}")
        raise 