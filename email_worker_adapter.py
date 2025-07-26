#!/usr/bin/env python3
"""
Adaptador para conectar las tareas de email de Flask con el worker independiente.
"""
import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar el worker independiente
from celery_worker import celery_app

class EmailWorkerAdapter:
    """Adaptador para enviar tareas de email al worker independiente."""
    
    def __init__(self):
        self.worker_app = celery_app
    
    def send_critical_edp_alerts(self, critical_edps: List[Dict], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alertas de EDPs críticos usando el worker independiente."""
        try:
            logger.info("📧 Enviando alertas críticas via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_critical_edp_alerts_task',
                args=[critical_edps, recipients]
            )
            
            return {
                "success": True,
                "task_id": task.id,
                "message": "Critical alerts queued successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando alertas críticas: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_payment_reminders(self, reminder_edps: List[Dict], recipients: List[str]) -> Dict[str, Any]:
        """Enviar recordatorios de pago usando el worker independiente."""
        try:
            logger.info("📧 Enviando recordatorios de pago via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_payment_reminders_task',
                args=[reminder_edps, recipients]
            )
            
            return {
                "success": True,
                "task_id": task.id,
                "message": "Payment reminders queued successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando recordatorios de pago: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_edp_expiration_alerts(self, expiration_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alertas de vencimiento de EDPs por etapas usando el worker independiente."""
        try:
            logger.info(f"📧 Enviando alertas de vencimiento {expiration_data.get('alert_type', 'unknown')} via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_edp_expiration_alerts_task',
                args=[expiration_data, recipients]
            )
            
            return {
                "success": True,
                "task_id": task.id,
                "message": f"EDP expiration alerts ({expiration_data.get('alert_type', 'unknown')}) queued successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando alertas de vencimiento: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_overdue_edp_alerts(self, overdue_edps: List[Dict], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alertas de EDPs vencidos."""
        try:
            logger.info("📧 Enviando alertas de EDPs vencidos via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_overdue_edp_alerts_task',
                args=[overdue_edps, recipients]
            )
            
            return {
                'success': True,
                'task_id': task.id,
                'message': 'Alertas de EDPs vencidos encoladas'
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando alertas de EDPs vencidos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_followup_reminders(self, followup_data: Dict, recipients: List[str]) -> Dict[str, Any]:
        """Enviar recordatorios de seguimiento de EDPs sin movimiento."""
        try:
            logger.info(f"📧 Enviando recordatorios de seguimiento para {followup_data.get('jefe_proyecto', 'N/A')} via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_followup_reminders_task',
                args=[followup_data, recipients]
            )
            
            return {
                'success': True,
                'task_id': task.id,
                'message': 'Recordatorios de seguimiento encolados'
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando recordatorios de seguimiento: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_performance_report(self, performance_data: Dict, recipients: List[str]) -> Dict[str, Any]:
        """Enviar reporte de performance del equipo."""
        try:
            logger.info(f"📧 Enviando reporte de performance para {performance_data.get('jefe_proyecto', 'N/A')} via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_performance_report_task',
                args=[performance_data, recipients]
            )
            
            return {
                'success': True,
                'task_id': task.id,
                'message': 'Reporte de performance encolado'
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando reporte de performance: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_weekly_summary(self, kpis_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """Enviar resumen semanal usando el worker independiente."""
        try:
            logger.info("📧 Enviando resumen semanal via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_weekly_summary_task',
                args=[kpis_data, recipients]
            )
            
            return {
                "success": True,
                "task_id": task.id,
                "message": "Weekly summary queued successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando resumen semanal: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_system_alert(self, alert_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """Enviar alerta del sistema usando el worker independiente."""
        try:
            logger.info("📧 Enviando alerta del sistema via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.send_system_alert_task',
                args=[alert_data, recipients]
            )
            
            return {
                "success": True,
                "task_id": task.id,
                "message": "System alert queued successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando alerta del sistema: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_email_service(self, test_recipient: str) -> Dict[str, Any]:
        """Probar el servicio de email usando el worker independiente."""
        try:
            logger.info("📧 Probando servicio de email via worker independiente")
            
            task = self.worker_app.send_task(
                'celery_worker.test_email_service_task',
                args=[test_recipient]
            )
            
            return {
                "success": True,
                "task_id": task.id,
                "message": "Test email queued successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error probando servicio de email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtener el estado de una tarea."""
        try:
            task = self.worker_app.AsyncResult(task_id)
            
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
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error checking task status: {str(e)}")
            return {
                "state": "ERROR",
                "status": f"Error checking task status: {str(e)}"
            }

# Instancia global del adaptador
email_adapter = EmailWorkerAdapter()

def send_email_with_template(subject: str, template_name: str, template_data: Dict[str, Any], recipients: List[str]) -> bool:
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

def generate_email_template(template_name: str, data: Dict[str, Any]) -> str:
    """Generar contenido HTML para diferentes tipos de email."""
    
    if template_name == "critical_edp_alert":
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #d32f2f;">🚨 ALERTA CRÍTICA: EDP {data.get('n_edp', 'N/A')}</h2>
            <p><strong>Cliente:</strong> {data.get('cliente', 'N/A')}</p>
            <p><strong>Proyecto:</strong> {data.get('proyecto', 'N/A')}</p>
            <p><strong>Monto:</strong> ${data.get('monto', 0):,.2f}</p>
            <p><strong>DSO Actual:</strong> {data.get('dso_actual', 0)} días</p>
            <p><strong>Último Movimiento:</strong> {data.get('ultimo_movimiento', 'N/A')}</p>
            <hr>
            <p>Este EDP requiere atención inmediata. Por favor, revisa el estado del proyecto y toma las acciones necesarias.</p>
        </body>
        </html>
        """
    
    elif template_name == "payment_reminder":
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #f57c00;">💰 Recordatorio de Pago: EDP {data.get('n_edp', 'N/A')}</h2>
            <p><strong>Cliente:</strong> {data.get('cliente', 'N/A')}</p>
            <p><strong>Proyecto:</strong> {data.get('proyecto', 'N/A')}</p>
            <p><strong>Monto:</strong> ${data.get('monto', 0):,.2f}</p>
            <p><strong>DSO Actual:</strong> {data.get('dso_actual', 0)} días</p>
            <hr>
            <p>Este EDP está próximo a alcanzar el estado crítico. Por favor, contacta al cliente para gestionar el pago.</p>
        </body>
        </html>
        """
    
    elif template_name == "weekly_summary":
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1976d2;">📊 Resumen Semanal - {time.strftime('%d/%m/%Y')}</h2>
            <h3>KPIs Principales</h3>
            <ul>
                <li><strong>Total EDPs:</strong> {data.get('total_edps', 0)}</li>
                <li><strong>Monto Total:</strong> ${data.get('total_monto', 0):,.2f}</li>
                <li><strong>DSO Promedio:</strong> {data.get('dso_promedio', 0)} días</li>
                <li><strong>EDPs Críticos:</strong> {data.get('edps_criticos', 0)}</li>
            </ul>
            <h3>Actividad de la Semana</h3>
            <ul>
                <li><strong>EDPs Aprobados:</strong> {data.get('edps_aprobados_semana', 0)}</li>
                <li><strong>EDPs Pagados:</strong> {data.get('edps_pagados_semana', 0)}</li>
                <li><strong>Monto Cobrado:</strong> ${data.get('monto_cobrado_semana', 0):,.2f}</li>
            </ul>
        </body>
        </html>
        """
    
    elif template_name == "system_alert":
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #f57c00;">⚠️ Alerta del Sistema: {data.get('title', 'Alerta')}</h2>
            <p><strong>Descripción:</strong> {data.get('description', 'N/A')}</p>
            <p><strong>Severidad:</strong> {data.get('severity', 'N/A')}</p>
            <p><strong>Timestamp:</strong> {data.get('timestamp', 'N/A')}</p>
        </body>
        </html>
        """
    
    elif template_name == "test_email":
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #4caf50;">🧪 Test del Sistema de Email - Pagora EDP</h2>
            <p><strong>Título:</strong> {data.get('title', 'N/A')}</p>
            <p><strong>Descripción:</strong> {data.get('description', 'N/A')}</p>
            <p><strong>Severidad:</strong> {data.get('severity', 'N/A')}</p>
            <p><strong>Timestamp:</strong> {data.get('timestamp', 'N/A')}</p>
            <hr>
            <p>Si recibes este email, significa que el sistema de notificaciones de Pagora está funcionando correctamente.</p>
        </body>
        </html>
        """
    
    else:
        # Plantilla por defecto
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Notificación del Sistema</h2>
            <p>Contenido: {str(data)}</p>
        </body>
        </html>
        """ 