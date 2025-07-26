#!/usr/bin/env python3
"""
Worker de Celery completamente standalone para pruebas de email.
"""
import os
import sys
import logging
from celery import Celery
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Celery completamente standalone
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Crear aplicación Celery completamente independiente
standalone_celery_app = Celery(
    'standalone_email_worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Configuración de Celery
standalone_celery_app.conf.update(
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
    event_queue_expires=60,
    imports=[]  # No importar módulos automáticamente
)

@standalone_celery_app.task(bind=True)
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
    """Generar contenido HTML para el reporte de performance."""
    
    if template_name == "performance_report":
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #1a1a1a;
                    background-color: #fafafa;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .email-header {{
                    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
                    color: white;
                    padding: 32px;
                    text-align: center;
                }}
                .email-header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                    letter-spacing: -0.025em;
                }}
                .email-header .subtitle {{
                    margin: 8px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                    font-weight: 400;
                }}
                .email-content {{
                    padding: 32px;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin: 24px 0;
                }}
                .metric-item {{
                    background-color: #f8fafc;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 16px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: 600;
                    color: #0066cc;
                    margin-bottom: 4px;
                }}
                .metric-label {{
                    font-size: 12px;
                    color: #6b7280;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }}
                .alert-badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    background-color: #eff6ff;
                    color: #2563eb;
                    border: 1px solid #bfdbfe;
                }}
                .email-footer {{
                    background-color: #f8fafc;
                    padding: 24px 32px;
                    text-align: center;
                    border-top: 1px solid #e5e7eb;
                }}
                .email-footer p {{
                    margin: 0;
                    font-size: 12px;
                    color: #6b7280;
                }}
                .amount {{
                    font-family: 'JetBrains Mono', 'Courier New', monospace;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Reporte de Performance</h1>
                    <div class="subtitle">{data.get('jefe_proyecto', 'N/A')} - {data.get('periodo', 'semanal')}</div>
                </div>
                
                <div class="email-content">
                    <div class="alert-badge">INFORME</div>
                    
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
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <h1>Notificación del Sistema</h1>
            <p>{str(data)}</p>
        </body>
        </html>
        """

if __name__ == '__main__':
    # Ejecutar worker
    standalone_celery_app.start() 