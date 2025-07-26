#!/usr/bin/env python3
"""
Worker de Celery independiente para tareas de email.
"""
import os
import sys
import logging
from celery import Celery
import time
# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Crear aplicación Celery independiente
celery_app = Celery(
    'email_worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    worker_send_task_events=False,
    worker_enable_remote_control=False,
    task_events=False,
    event_queue_expires=60
)

# Tareas independientes
@celery_app.task(bind=True)
def simple_test_task(self):
    """Tarea simple de prueba."""
    logger.info("🧪 Simple test task starting")
    
    result = {
        "message": "Hello from independent Celery worker!", 
        "timestamp": "2024-01-01 12:00:00",
        "task_id": self.request.id
    }
    
    logger.info("🧪 Simple test task completed")
    return result

@celery_app.task(bind=True)
def send_test_email(self):
    """Tarea para enviar email de prueba."""
    try:
        logger.info("📧 Test email task starting")
        
        # Importar configuración de email
        import smtplib
        import time
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Obtener configuración desde variables de entorno
        mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.getenv('MAIL_PORT', '587'))
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')
        mail_use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        test_recipient = os.getenv('TEST_EMAIL_RECIPIENT', 'diegobravobe@gmail.com')
        
        if not all([mail_username, mail_password, test_recipient]):
            logger.error("❌ Email configuration missing")
            return {"success": False, "reason": "missing_config"}
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email - Independent Celery Worker"
        msg['From'] = mail_username
        msg['To'] = test_recipient
        
        html_content = """
        <html>
        <body>
            <h2>Test Email from Independent Celery Worker</h2>
            <p>Este es un email de prueba enviado desde un worker de Celery independiente.</p>
            <p>Si recibes este email, significa que el sistema está funcionando correctamente.</p>
            <p><strong>Task ID:</strong> {task_id}</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
        </body>
        </html>
        """.format(
            task_id=self.request.id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Enviar email
        if mail_use_tls:
            server = smtplib.SMTP(mail_server, mail_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(mail_server, mail_port)
        
        server.login(mail_username, mail_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"📧 Test email sent successfully to {test_recipient}")
        return {
            "success": True,
            "recipient": test_recipient,
            "task_id": self.request.id,
            "message": "Test email sent successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in test email task: {str(e)}")
        raise

# Tareas de email para la aplicación Flask
@celery_app.task(bind=True)
def send_critical_edp_alerts_task(self, critical_edps, recipients):
    """Tarea para enviar alertas de EDPs críticos."""
    try:
        logger.info("📧 Critical EDP alerts task starting")
        
        # Enviar alertas
        sent_count = 0
        for edp in critical_edps:
            success = send_email_with_template(
                subject=f"🚨 ALERTA CRÍTICA: EDP {edp.get('n_edp', 'N/A')}",
                template_name="critical_edp_alert",
                template_data=edp,
                recipients=recipients
            )
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

@celery_app.task(bind=True)
def send_payment_reminders_task(self, reminder_edps, recipients):
    """Tarea para enviar recordatorios de pago."""
    try:
        logger.info("📧 Payment reminders task starting")
        
        # Enviar recordatorios
        sent_count = 0
        for edp in reminder_edps:
            success = send_email_with_template(
                subject=f"💰 Recordatorio de Pago: EDP {edp.get('n_edp', 'N/A')}",
                template_name="payment_reminder",
                template_data=edp,
                recipients=recipients
            )
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

@celery_app.task(bind=True)
def send_weekly_summary_task(self, kpis_data, recipients):
    """Tarea para enviar resumen semanal."""
    try:
        logger.info("📧 Weekly summary task starting")
        
        import time
        
        # Enviar resumen semanal
        success = send_email_with_template(
            subject=f"📊 Resumen Semanal - {time.strftime('%d/%m/%Y')}",
            template_name="weekly_summary",
            template_data=kpis_data,
            recipients=recipients
        )
        
        logger.info(f"📧 Weekly summary sent: {success}")
        return {
            "success": success,
            "recipients_count": len(recipients)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in weekly summary task: {str(e)}")
        raise

@celery_app.task(bind=True)
def send_edp_expiration_alerts_task(self, expiration_data, recipients):
    """Tarea para enviar alertas de vencimiento de EDPs por etapas."""
    try:
        logger.info("📧 EDP expiration alerts task starting")
        
        alert_type = expiration_data.get('alert_type', 'overdue')
        edps = expiration_data.get('edps', [])
        days_threshold = expiration_data.get('days_threshold', 0)
        
        if not edps:
            logger.info(f"📧 No EDPs found for {alert_type} alerts")
            return {
                "success": True,
                "alert_type": alert_type,
                "edps_count": 0
            }
        
        # Enviar alertas según el tipo
        subject_map = {
            'upcoming': f"⚠️ EDPs Vencen Pronto - {time.strftime('%d/%m/%Y')}",
            'imminent': f"🚨 EDPs Vencen en {days_threshold} Días - {time.strftime('%d/%m/%Y')}",
            'critical': f"🔥 EDPs Vencen Mañana - {time.strftime('%d/%m/%Y')}",
            'overdue': f"🚨 EDPs Vencidos - {time.strftime('%d/%m/%Y')}"
        }
        
        subject = subject_map.get(alert_type, f"Alerta de EDPs - {time.strftime('%d/%m/%Y')}")
        
        # Mapear nombres de plantillas
        template_map = {
            'upcoming': 'edp_expiration_upcoming',
            'imminent': 'edp_expiration_imminent', 
            'critical': 'edp_expiration_critical',
            'overdue': 'overdue_edp_alert'
        }
        
        template_name = template_map.get(alert_type, f"edp_expiration_{alert_type}")
        
        success = send_email_with_template(
            subject=subject,
            template_name=template_name,
            template_data=expiration_data,
            recipients=recipients
        )
        
        logger.info(f"📧 {alert_type} EDP alerts sent: {success}")
        return {
            "success": success,
            "recipients_count": len(recipients),
            "alert_type": alert_type,
            "edps_count": len(edps),
            "days_threshold": days_threshold
        }
        
    except Exception as e:
        logger.error(f"❌ Error in EDP expiration alerts task: {str(e)}")
        raise

@celery_app.task(bind=True)
def send_overdue_edp_alerts_task(self, overdue_edps, recipients):
    """Tarea para enviar alertas de EDPs vencidos."""
    try:
        logger.info("📧 Overdue EDP alerts task starting")
        
        if not overdue_edps:
            logger.info("📧 No overdue EDPs found")
            return {
                "success": True,
                "overdue_edps_count": 0
            }
        
        # Enviar alertas de EDPs vencidos
        success = send_email_with_template(
            subject=f"🚨 EDPs Vencidos - {time.strftime('%d/%m/%Y')}",
            template_name="overdue_edp_alert",
            template_data={"edps": overdue_edps},
            recipients=recipients
        )
        
        logger.info(f"📧 Overdue EDP alerts sent: {success}")
        return {
            "success": success,
            "recipients_count": len(recipients),
            "overdue_edps_count": len(overdue_edps)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in overdue EDP alerts task: {str(e)}")
        raise

@celery_app.task(bind=True)
def send_system_alert_task(self, alert_data, recipients):
    """Tarea para enviar alerta del sistema."""
    try:
        logger.info("📧 System alert task starting")
        
        # Enviar alerta del sistema
        success = send_email_with_template(
            subject=f"⚠️ Alerta del Sistema: {alert_data.get('title', 'Alerta')}",
            template_name="system_alert",
            template_data=alert_data,
            recipients=recipients
        )
        
        logger.info(f"📧 System alert sent: {success}")
        return {
            "success": success,
            "recipients_count": len(recipients)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in system alert task: {str(e)}")
        raise

@celery_app.task(bind=True)
def test_email_service_task(self, test_recipient):
    """Tarea para probar el servicio de email."""
    try:
        logger.info("📧 Email service test task starting")
        
        # Enviar email de prueba
        test_data = {
            "title": "Test del Sistema de Email - Pagora EDP",
            "description": "Este es un email de prueba para verificar que el sistema de notificaciones de Pagora está funcionando correctamente.",
            "severity": "low",
            "timestamp": time.strftime("%d/%m/%Y %H:%M:%S")
        }
        
        success = send_email_with_template(
            subject="🧪 Test del Sistema de Email - Pagora EDP",
            template_name="test_email",
            template_data=test_data,
            recipients=[test_recipient]
        )
        
        logger.info(f"📧 Test email sent: {success}")
        return {
            "success": success,
            "recipient": test_recipient
        }
        
    except Exception as e:
        logger.error(f"❌ Error in email service test task: {str(e)}")
        raise

@celery_app.task(bind=True)
def send_followup_reminders_task(self, followup_data, recipients):
    """Tarea para enviar recordatorios de seguimiento de EDPs sin movimiento."""
    try:
        logger.info("📧 Followup reminders task starting")
        
        jefe_proyecto = followup_data.get('jefe_proyecto', 'N/A')
        edps_sin_movimiento = followup_data.get('edps_sin_movimiento', [])
        dias_sin_movimiento = followup_data.get('dias_sin_movimiento', 0)
        
        if not edps_sin_movimiento:
            logger.info(f"📧 No EDPs without movement for {jefe_proyecto}")
            return {
                "success": True,
                "jefe_proyecto": jefe_proyecto,
                "edps_count": 0
            }
        
        # Enviar recordatorio de seguimiento
        success = send_email_with_template(
            subject=f"📋 Recordatorio de Seguimiento - {jefe_proyecto} ({time.strftime('%d/%m/%Y')})",
            template_name="followup_reminder",
            template_data=followup_data,
            recipients=recipients
        )
        
        logger.info(f"📧 Followup reminders sent for {jefe_proyecto}: {success}")
        return {
            "success": success,
            "recipients_count": len(recipients),
            "jefe_proyecto": jefe_proyecto,
            "edps_count": len(edps_sin_movimiento),
            "dias_sin_movimiento": dias_sin_movimiento
        }
        
    except Exception as e:
        logger.error(f"❌ Error in followup reminders task: {str(e)}")
        raise

@celery_app.task(bind=True)
def send_performance_report_task(self, performance_data, recipients):
    """Tarea para enviar reporte de performance del equipo."""
    try:
        logger.info("📧 Performance report task starting")
        
        jefe_proyecto = performance_data.get('jefe_proyecto', 'N/A')
        periodo = performance_data.get('periodo', 'semanal')
        
        # Enviar reporte de performance
        success = send_email_with_template(
            subject=f"📊 Reporte de Performance - {jefe_proyecto} ({periodo.title()})",
            template_name="performance_report",
            template_data=performance_data,
            recipients=recipients
        )
        
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

# Funciones de email para las tareas
def send_email_with_template(subject: str, template_name: str, template_data, recipients) -> bool:
    """Enviar email usando una plantilla específica."""
    try:
        # Obtener configuración desde variables de entorno
        mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.getenv('MAIL_PORT', '587'))
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')
        mail_use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        mail_default_sender = os.getenv('MAIL_DEFAULT_SENDER', mail_username)
        
        if not all([mail_username, mail_password, mail_default_sender]):
            logger.error("❌ Email configuration missing")
            return False
        
        # Importar librerías necesarias
        import smtplib
        import time
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Generar contenido HTML basado en la plantilla
        html_content = generate_email_template(template_name, template_data)
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_default_sender
        msg['To'] = ', '.join(recipients)
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Enviar email
        if mail_use_tls:
            server = smtplib.SMTP(mail_server, mail_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(mail_server, mail_port)
        
        server.login(mail_username, mail_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"📧 Email sent successfully to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return False

def generate_email_template(template_name: str, data) -> str:
    """Generar contenido HTML para diferentes tipos de email con diseño Executive Suite."""
    
    # CSS base para el diseño Executive Suite
    base_css = """
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background-color: #fafafa;
            margin: 0;
            padding: 0;
        }
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .email-header {
            background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
            color: white;
            padding: 32px;
            text-align: center;
        }
        .email-header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            letter-spacing: -0.025em;
        }
        .email-header .subtitle {
            margin: 8px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
            font-weight: 400;
        }
        .email-content {
            padding: 32px;
        }
        .metric-card {
            background-color: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 20px;
            margin: 16px 0;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }
        .metric-item {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 16px;
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 600;
            color: #0066cc;
            margin-bottom: 4px;
        }
        .metric-label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .alert-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .alert-critical {
            background-color: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }
        .alert-warning {
            background-color: #fffbeb;
            color: #d97706;
            border: 1px solid #fed7aa;
        }
        .alert-info {
            background-color: #eff6ff;
            color: #2563eb;
            border: 1px solid #bfdbfe;
        }
        .alert-success {
            background-color: #f0fdf4;
            color: #059669;
            border: 1px solid #bbf7d0;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        .data-table th {
            background-color: #f8fafc;
            font-weight: 600;
            color: #374151;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .data-table td {
            font-size: 14px;
        }
        .amount {
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            font-weight: 500;
        }
        .email-footer {
            background-color: #f8fafc;
            padding: 24px 32px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }
        .email-footer p {
            margin: 0;
            font-size: 12px;
            color: #6b7280;
        }
        .divider {
            height: 1px;
            background-color: #e5e7eb;
            margin: 24px 0;
        }
        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #374151;
            margin: 24px 0 16px 0;
        }
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-pending { background-color: #f59e0b; }
        .status-critical { background-color: #dc2626; }
        .status-completed { background-color: #059669; }
    </style>
    """
    
    if template_name == "critical_edp_alert":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Alerta Crítica de EDP</h1>
                    <div class="subtitle">Requiere atención inmediata</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-critical">CRÍTICO</div>
                    
                    <div class="metric-card">
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{data.get('n_edp', 'N/A')}</div>
                                <div class="metric-label">Número EDP</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value amount">${data.get('monto', 0):,.0f}</div>
                                <div class="metric-label">Monto</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{data.get('dso_actual', 0)} días</div>
                                <div class="metric-label">DSO Actual</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-title">Detalles del Proyecto</div>
                    <table class="data-table">
                        <tr>
                            <th>Cliente</th>
                            <td>{data.get('cliente', 'N/A')}</td>
                        </tr>
                        <tr>
                            <th>Proyecto</th>
                            <td>{data.get('proyecto', 'N/A')}</td>
                        </tr>
                        <tr>
                            <th>Último Movimiento</th>
                            <td>{data.get('ultimo_movimiento', 'N/A')}</td>
                        </tr>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #dc2626; font-weight: 500;">
                        ⚠️ Este EDP requiere atención inmediata. Por favor, revisa el estado del proyecto y toma las acciones necesarias.
                    </p>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "payment_reminder":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Recordatorio de Pago</h1>
                    <div class="subtitle">EDP próximo al estado crítico</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-warning">ATENCIÓN</div>
                    
                    <div class="metric-card">
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{data.get('n_edp', 'N/A')}</div>
                                <div class="metric-label">Número EDP</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value amount">${data.get('monto', 0):,.0f}</div>
                                <div class="metric-label">Monto</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{data.get('dso_actual', 0)} días</div>
                                <div class="metric-label">DSO Actual</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-title">Información del Cliente</div>
                    <table class="data-table">
                        <tr>
                            <th>Cliente</th>
                            <td>{data.get('cliente', 'N/A')}</td>
                        </tr>
                        <tr>
                            <th>Proyecto</th>
                            <td>{data.get('proyecto', 'N/A')}</td>
                        </tr>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #d97706; font-weight: 500;">
                        💰 Este EDP está próximo a alcanzar el estado crítico. Por favor, contacta al cliente para gestionar el pago.
                    </p>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "weekly_summary":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Resumen Semanal</h1>
                    <div class="subtitle">{time.strftime('%d/%m/%Y')} • Reporte de Gestión</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-info">INFORME</div>
                    
                    <div class="section-title">KPIs Principales</div>
                    <div class="metric-grid">
                        <div class="metric-item">
                            <div class="metric-value">{data.get('total_edps', 0)}</div>
                            <div class="metric-label">Total EDPs</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value amount">${data.get('total_monto', 0):,.0f}</div>
                            <div class="metric-label">Monto Total</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{data.get('dso_promedio', 0)} días</div>
                            <div class="metric-label">DSO Promedio</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{data.get('edps_criticos', 0)}</div>
                            <div class="metric-label">EDPs Críticos</div>
                        </div>
                    </div>
                    
                    <div class="section-title">Actividad de la Semana</div>
                    <div class="metric-grid">
                        <div class="metric-item">
                            <div class="metric-value">{data.get('edps_aprobados_semana', 0)}</div>
                            <div class="metric-label">EDPs Aprobados</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{data.get('edps_pagados_semana', 0)}</div>
                            <div class="metric-label">EDPs Pagados</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value amount">${data.get('monto_cobrado_semana', 0):,.0f}</div>
                            <div class="metric-label">Monto Cobrado</div>
                        </div>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #059669; font-weight: 500;">
                        📊 Resumen semanal generado automáticamente por el sistema de gestión Pagora EDP.
                    </p>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "system_alert":
        severity_colors = {
            'low': 'alert-info',
            'medium': 'alert-warning', 
            'high': 'alert-critical',
            'critical': 'alert-critical'
        }
        alert_class = severity_colors.get(data.get('severity', 'medium'), 'alert-info')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Alerta del Sistema</h1>
                    <div class="subtitle">{data.get('title', 'Notificación del Sistema')}</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge {alert_class}">{data.get('severity', 'medium').upper()}</div>
                    
                    <div class="metric-card">
                        <div class="section-title">Descripción</div>
                        <p style="margin: 0; color: #374151;">{data.get('description', 'N/A')}</p>
                    </div>
                    
                    <div class="section-title">Detalles Técnicos</div>
                    <table class="data-table">
                        <tr>
                            <th>Severidad</th>
                            <td>{data.get('severity', 'N/A').title()}</td>
                        </tr>
                        <tr>
                            <th>Timestamp</th>
                            <td>{data.get('timestamp', 'N/A')}</td>
                        </tr>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #6b7280; font-size: 14px;">
                        Esta alerta fue generada automáticamente por el sistema de monitoreo de Pagora EDP.
                    </p>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "edp_expiration_upcoming":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>EDPs Vencen Pronto</h1>
                    <div class="subtitle">Atención preventiva requerida</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-warning">PRÓXIMO VENCIMIENTO</div>
                    
                    <div class="metric-card">
                        <div class="section-title">Resumen de EDPs por Vencer</div>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{len(data.get('edps', []))}</div>
                                <div class="metric-label">EDPs por Vencer</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value amount">${sum(edp.get('monto', 0) for edp in data.get('edps', [])):,.0f}</div>
                                <div class="metric-label">Monto Total</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{data.get('days_threshold', 0)} días</div>
                                <div class="metric-label">Días Restantes</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-title">EDPs por Vencer</div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>EDP</th>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>DSO</th>
                                <th>Días Restantes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(f'''
                            <tr>
                                <td><strong>{edp.get('n_edp', 'N/A')}</strong></td>
                                <td>{edp.get('cliente', 'N/A')}</td>
                                <td>{edp.get('proyecto', 'N/A')}</td>
                                <td class="amount">${edp.get('monto', 0):,.0f}</td>
                                <td>{edp.get('dso_actual', 0)} días</td>
                                <td style="color: #d97706; font-weight: 600;">{data.get('days_threshold', 0) - edp.get('dso_actual', 0)} días</td>
                            </tr>
                            ''' for edp in data.get('edps', []))}
                        </tbody>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #d97706; font-weight: 500;">
                        ⚠️ Estos EDPs están próximos a vencer. Se recomienda contactar a los clientes para gestionar los pagos.
                    </p>
                    
                    <div class="metric-card" style="background-color: #fffbeb; border-color: #fed7aa;">
                        <div class="section-title" style="color: #d97706;">Acciones Recomendadas</div>
                        <ul style="margin: 0; padding-left: 20px; color: #374151;">
                            <li>Contactar a los clientes para recordar los pagos pendientes</li>
                            <li>Verificar la documentación de facturación</li>
                            <li>Establecer recordatorios de seguimiento</li>
                            <li>Preparar planes de contingencia si es necesario</li>
                        </ul>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "edp_expiration_imminent":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>EDPs Vencen en {data.get('days_threshold', 0)} Días</h1>
                    <div class="subtitle">Acción inmediata requerida</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-critical">VENCIMIENTO INMINENTE</div>
                    
                    <div class="metric-card">
                        <div class="section-title">Resumen de EDPs por Vencer</div>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{len(data.get('edps', []))}</div>
                                <div class="metric-label">EDPs Críticos</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value amount">${sum(edp.get('monto', 0) for edp in data.get('edps', [])):,.0f}</div>
                                <div class="metric-label">Monto Total</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{data.get('days_threshold', 0)} días</div>
                                <div class="metric-label">Días Restantes</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-title">EDPs por Vencer Inminentemente</div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>EDP</th>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>DSO</th>
                                <th>Días Restantes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(f'''
                            <tr>
                                <td><strong>{edp.get('n_edp', 'N/A')}</strong></td>
                                <td>{edp.get('cliente', 'N/A')}</td>
                                <td>{edp.get('proyecto', 'N/A')}</td>
                                <td class="amount">${edp.get('monto', 0):,.0f}</td>
                                <td>{edp.get('dso_actual', 0)} días</td>
                                <td style="color: #dc2626; font-weight: 600;">{data.get('days_threshold', 0) - edp.get('dso_actual', 0)} días</td>
                            </tr>
                            ''' for edp in data.get('edps', []))}
                        </tbody>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #dc2626; font-weight: 500;">
                        🚨 Estos EDPs vencen en {data.get('days_threshold', 0)} días. Se requiere acción inmediata para evitar el vencimiento.
                    </p>
                    
                    <div class="metric-card" style="background-color: #fef2f2; border-color: #fecaca;">
                        <div class="section-title" style="color: #dc2626;">Acciones Urgentes</div>
                        <ul style="margin: 0; padding-left: 20px; color: #374151;">
                            <li>Contactar inmediatamente a los clientes</li>
                            <li>Enviar recordatorios de pago urgentes</li>
                            <li>Verificar estado de facturación</li>
                            <li>Preparar documentación de cobranza</li>
                            <li>Establecer contacto con departamento financiero del cliente</li>
                        </ul>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "edp_expiration_critical":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>EDPs Vencen Mañana</h1>
                    <div class="subtitle">ÚLTIMA OPORTUNIDAD</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-critical">VENCIMIENTO MAÑANA</div>
                    
                    <div class="metric-card">
                        <div class="section-title">Resumen de EDPs que Vencen Mañana</div>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{len(data.get('edps', []))}</div>
                                <div class="metric-label">EDPs Críticos</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value amount">${sum(edp.get('monto', 0) for edp in data.get('edps', [])):,.0f}</div>
                                <div class="metric-label">Monto Total</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">MAÑANA</div>
                                <div class="metric-label">Vencimiento</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-title">EDPs que Vencen Mañana</div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>EDP</th>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>DSO</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(f'''
                            <tr>
                                <td><strong>{edp.get('n_edp', 'N/A')}</strong></td>
                                <td>{edp.get('cliente', 'N/A')}</td>
                                <td>{edp.get('proyecto', 'N/A')}</td>
                                <td class="amount">${edp.get('monto', 0):,.0f}</td>
                                <td>{edp.get('dso_actual', 0)} días</td>
                                <td>
                                    <span class="status-indicator status-critical"></span>
                                    ÚLTIMO DÍA
                                </td>
                            </tr>
                            ''' for edp in data.get('edps', []))}
                        </tbody>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #dc2626; font-weight: 500; font-size: 16px;">
                        🔥 ESTOS EDPs VENCEN MAÑANA. Es la última oportunidad para evitar el vencimiento.
                    </p>
                    
                    <div class="metric-card" style="background-color: #fef2f2; border-color: #fecaca;">
                        <div class="section-title" style="color: #dc2626;">Acciones de Emergencia</div>
                        <ul style="margin: 0; padding-left: 20px; color: #374151;">
                            <li>Llamar inmediatamente a los clientes</li>
                            <li>Enviar emails de urgencia máxima</li>
                            <li>Contactar gerentes financieros</li>
                            <li>Preparar documentación de cobranza legal</li>
                            <li>Notificar a dirección ejecutiva</li>
                        </ul>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "overdue_edp_alert":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>EDPs Vencidos</h1>
                    <div class="subtitle">Requieren acción inmediata</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-critical">VENCIDOS</div>
                    
                    <div class="metric-card">
                        <div class="section-title">Resumen de EDPs Vencidos</div>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{len(data.get('edps', []))}</div>
                                <div class="metric-label">EDPs Vencidos</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value amount">${sum(edp.get('monto', 0) for edp in data.get('edps', [])):,.0f}</div>
                                <div class="metric-label">Monto Total</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{max((edp.get('dso_actual', 0) for edp in data.get('edps', [])), default=0)} días</div>
                                <div class="metric-label">DSO Máximo</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-title">Lista de EDPs Vencidos</div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>EDP</th>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>DSO</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(f'''
                            <tr>
                                <td><strong>{edp.get('n_edp', 'N/A')}</strong></td>
                                <td>{edp.get('cliente', 'N/A')}</td>
                                <td>{edp.get('proyecto', 'N/A')}</td>
                                <td class="amount">${edp.get('monto', 0):,.0f}</td>
                                <td style="color: #dc2626; font-weight: 600;">{edp.get('dso_actual', 0)} días</td>
                                <td>
                                    <span class="status-indicator status-critical"></span>
                                    {edp.get('estado', 'N/A')}
                                </td>
                            </tr>
                            ''' for edp in data.get('edps', []))}
                        </tbody>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #dc2626; font-weight: 500;">
                        🚨 Estos EDPs han superado el límite de días establecido y requieren atención inmediata. 
                        Por favor, contacta a los clientes correspondientes para gestionar los pagos pendientes.
                    </p>
                    
                    <div class="metric-card" style="background-color: #fef2f2; border-color: #fecaca;">
                        <div class="section-title" style="color: #dc2626;">Acciones Recomendadas</div>
                        <ul style="margin: 0; padding-left: 20px; color: #374151;">
                            <li>Contactar inmediatamente a los clientes con EDPs vencidos</li>
                            <li>Revisar el estado de facturación y documentación</li>
                            <li>Establecer planes de pago si es necesario</li>
                            <li>Actualizar el estado en el sistema después de cada contacto</li>
                        </ul>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "test_email":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Test del Sistema</h1>
                    <div class="subtitle">Verificación de Notificaciones</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-success">TEST</div>
                    
                    <div class="metric-card">
                        <div class="section-title">Información del Test</div>
                        <table class="data-table">
                            <tr>
                                <th>Título</th>
                                <td>{data.get('title', 'N/A')}</td>
                            </tr>
                            <tr>
                                <th>Descripción</th>
                                <td>{data.get('description', 'N/A')}</td>
                            </tr>
                            <tr>
                                <th>Severidad</th>
                                <td>{data.get('severity', 'N/A').title()}</td>
                            </tr>
                            <tr>
                                <th>Timestamp</th>
                                <td>{data.get('timestamp', 'N/A')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #059669; font-weight: 500;">
                        ✅ Si recibes este email, significa que el sistema de notificaciones de Pagora está funcionando correctamente.
                    </p>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "followup_reminder":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Recordatorio de Seguimiento</h1>
                    <div class="subtitle">EDPs sin movimiento</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-warning">ATENCIÓN</div>
                    
                    <div class="metric-card">
                        <div class="section-title">Resumen de EDPs sin Movimiento</div>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{len(data.get('edps_sin_movimiento', []))}</div>
                                <div class="metric-label">EDPs sin Movimiento</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value amount">${sum(edp.get('monto', 0) for edp in data.get('edps_sin_movimiento', [])):,.0f}</div>
                                <div class="metric-label">Monto Total</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{data.get('dias_sin_movimiento', 0)} días</div>
                                <div class="metric-label">Días sin Movimiento</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-title">EDPs sin Movimiento</div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>EDP</th>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>DSO</th>
                                <th>Días sin Movimiento</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(f'''
                            <tr>
                                <td><strong>{edp.get('n_edp', 'N/A')}</strong></td>
                                <td>{edp.get('cliente', 'N/A')}</td>
                                <td>{edp.get('proyecto', 'N/A')}</td>
                                <td class="amount">${edp.get('monto', 0):,.0f}</td>
                                <td>{edp.get('dso_actual', 0)} días</td>
                                <td style="color: #d97706; font-weight: 600;">{data.get('dias_sin_movimiento', 0)} días</td>
                            </tr>
                            ''' for edp in data.get('edps_sin_movimiento', []))}
                        </tbody>
                    </table>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #d97706; font-weight: 500;">
                        ⚠️ Estos EDPs han superado el límite de días sin movimiento establecido. Por favor, revisa el estado de estos proyectos.
                    </p>
                    
                    <div class="metric-card" style="background-color: #fffbeb; border-color: #fed7aa;">
                        <div class="section-title" style="color: #d97706;">Acciones Recomendadas</div>
                        <ul style="margin: 0; padding-left: 20px; color: #374151;">
                            <li>Contactar a los clientes para recordar los pagos pendientes</li>
                            <li>Verificar la documentación de facturación</li>
                            <li>Establecer recordatorios de seguimiento</li>
                            <li>Preparar planes de contingencia si es necesario</li>
                        </ul>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif template_name == "performance_report":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Reporte de Performance</h1>
                    <div class="subtitle">{data.get('jefe_proyecto', 'N/A')} - {data.get('periodo', 'semanal')}</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-info">INFORME</div>
                    
                    <div class="section-title">KPIs Principales</div>
                    <div class="metric-grid">
                        <div class="metric-item">
                            <div class="metric-value">{data.get('total_edps', 0)}</div>
                            <div class="metric-label">Total EDPs</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value amount">${data.get('total_monto', 0):,.0f}</div>
                            <div class="metric-label">Monto Total</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{data.get('dso_promedio', 0)} días</div>
                            <div class="metric-label">DSO Promedio</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{data.get('edps_criticos', 0)}</div>
                            <div class="metric-label">EDPs Críticos</div>
                        </div>
                    </div>
                    
                    <div class="section-title">Actividad de la Semana</div>
                    <div class="metric-grid">
                        <div class="metric-item">
                            <div class="metric-value">{data.get('edps_aprobados_semana', 0)}</div>
                            <div class="metric-label">EDPs Aprobados</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{data.get('edps_pagados_semana', 0)}</div>
                            <div class="metric-label">EDPs Pagados</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value amount">${data.get('monto_cobrado_semana', 0):,.0f}</div>
                            <div class="metric-label">Monto Cobrado</div>
                        </div>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <p style="color: #059669; font-weight: 500;">
                        📊 Reporte de performance generado automáticamente por el sistema de gestión Pagora EDP.
                    </p>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    else:
        # Plantilla por defecto
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {base_css}
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Notificación del Sistema</h1>
                    <div class="subtitle">Pagora EDP Management</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge alert-info">INFO</div>
                    
                    <div class="metric-card">
                        <p style="margin: 0; color: #374151;">{str(data)}</p>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>Pagora EDP Management System • {time.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """

if __name__ == '__main__':
    # Ejecutar worker
    celery_app.start() 