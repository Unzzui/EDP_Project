"""
Email service for sending notifications and alerts.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Mail, Message
from jinja2 import Template
from ..config import get_config

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self):
        self.config = get_config()
        self.email_config = self.config.email
        self.mail = Mail()
        self.mail.init_app(current_app)
    
    def _render_template_safe(self, template_name: str, **context) -> str:
        """
        Render template safely using Jinja2 directly to avoid Flask context issues.
        
        Args:
            template_name: Name of the template file
            **context: Template context variables
        
        Returns:
            str: Rendered template content
        """
        try:
            # Use Jinja2 directly to avoid Flask context issues
            from jinja2 import Environment, FileSystemLoader
            import os
            
            # Get the template directory path
            template_dir = os.path.join(current_app.root_path, 'templates')
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # Load and render template
            template = env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return f"Error rendering template: {str(e)}"
    
    def _render_text_template_safe(self, template_name: str, **context) -> str:
        """
        Render text template safely using Jinja2 directly to avoid Flask context issues.
        
        Args:
            template_name: Name of the text template file
            **context: Template context variables
        
        Returns:
            str: Rendered text template content
        """
        try:
            # Use Jinja2 directly to avoid Flask context issues
            from jinja2 import Environment, FileSystemLoader
            import os
            
            # Get the template directory path
            template_dir = os.path.join(current_app.root_path, 'templates')
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # Load and render template
            template = env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering text template {template_name}: {e}")
            return f"Error rendering text template: {str(e)}"
    
    def is_enabled(self) -> bool:
        """Check if email service is properly configured."""
        return (
            self.email_config.mail_username and 
            self.email_config.mail_password and
            self.email_config.mail_default_sender
        )
    
    def send_email(self, subject: str, recipients: List[str], 
                  html_body: str, text_body: str = None) -> bool:
        """
        Send an email with HTML and text content using direct SMTP.
        
        Args:
            subject: Email subject
            recipients: List of email addresses
            html_body: HTML content
            text_body: Plain text content (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not self.is_enabled():
                logger.warning("📧 Email service not configured, skipping email send")
                return False
            
            # Usar SMTP directamente en lugar de Flask-Mail
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config.mail_default_sender
            msg['To'] = ', '.join(recipients)
            
            # Agregar contenido
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Conectar y enviar
            if self.email_config.mail_use_tls:
                server = smtplib.SMTP(self.email_config.mail_server, self.email_config.mail_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.email_config.mail_server, self.email_config.mail_port)
            
            server.login(self.email_config.mail_username, self.email_config.mail_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"📧 Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {str(e)}")
            return False
    
    def send_critical_edp_alert(self, edp_data: Dict[str, Any], 
                               recipients: List[str]) -> bool:
        """
        Send critical EDP alert email.
        
        Args:
            edp_data: EDP data dictionary
            recipients: List of email addresses
        
        Returns:
            bool: True if email sent successfully
        """
        if not self.email_config.enable_critical_alerts:
            logger.info("📧 Critical alerts disabled, skipping email")
            return False
        
        subject = f"🚨 ALERTA CRÍTICA: EDP {edp_data.get('n_edp', 'N/A')} requiere atención inmediata"
        
        html_body = self._render_template_safe(
            'emails/critical_alert.html',
            edp_data=edp_data, 
            app_url=current_app.config.get('APP_URL', 'http://localhost:5000')
        )
        text_body = self._render_text_template_safe(
            'emails/text/critical_alert.txt',
            edp_data=edp_data
        )
        
        return self.send_email(subject, recipients, html_body, text_body)
    
    def send_payment_reminder(self, edp_data: Dict[str, Any], 
                             recipients: List[str]) -> bool:
        """
        Send payment reminder email.
        
        Args:
            edp_data: EDP data dictionary
            recipients: List of email addresses
        
        Returns:
            bool: True if email sent successfully
        """
        if not self.email_config.enable_payment_reminders:
            logger.info("📧 Payment reminders disabled, skipping email")
            return False
        
        subject = f"💰 Recordatorio de Pago: EDP {edp_data.get('n_edp', 'N/A')}"
        
        html_body = self._render_template_safe(
            'emails/payment_reminder.html',
            edp_data=edp_data, 
            app_url=current_app.config.get('APP_URL', 'http://localhost:5000')
        )
        text_body = self._render_text_template_safe(
            'emails/text/payment_reminder.txt',
            edp_data=edp_data
        )
        
        return self.send_email(subject, recipients, html_body, text_body)
    
    def send_weekly_summary(self, kpis_data: Dict[str, Any], 
                           recipients: List[str]) -> bool:
        """
        Send weekly summary email.
        
        Args:
            kpis_data: KPIs data dictionary
            recipients: List of email addresses
        
        Returns:
            bool: True if email sent successfully
        """
        if not self.email_config.enable_weekly_summary:
            logger.info("📧 Weekly summary disabled, skipping email")
            return False
        
        # Procesar y limpiar los datos de KPIs
        processed_kpis = self._process_kpis_data(kpis_data)
        
        # Debug: Log de los datos procesados
        logger.info(f"📊 Datos procesados para email: {list(processed_kpis.keys())}")
        if 'proyectos_por_jefe' in processed_kpis:
            logger.info(f"📊 Número de proyectos procesados: {len(processed_kpis['proyectos_por_jefe'])}")
        
        subject = f"📊 Resumen Semanal - {datetime.now().strftime('%d/%m/%Y')}"
        
        html_body = self._render_template_safe(
            'emails/weekly_summary.html',
            processed_kpis=processed_kpis, 
            date=datetime.now().strftime('%d/%m/%Y'), 
            app_url=current_app.config.get('APP_URL', 'http://localhost:5000')
        )
        
        text_body = self._render_text_template_safe(
            'emails/text/weekly_summary.txt',
            processed_kpis=processed_kpis, 
            date=datetime.now().strftime('%d/%m/%Y')
        )
        
        return self.send_email(subject, recipients, html_body, text_body)
    
    def send_system_alert(self, alert_data: Dict[str, Any], 
                         recipients: List[str]) -> bool:
        """
        Send system alert email.
        
        Args:
            alert_data: Alert data dictionary
            recipients: List of email addresses
        
        Returns:
            bool: True if email sent successfully
        """
        if not self.email_config.enable_system_alerts:
            logger.info("📧 System alerts disabled, skipping email")
            return False
        
        subject = f"⚠️ Alerta del Sistema: {alert_data.get('title', 'Alerta')}"
        
        html_body = self._render_template_safe(
            'emails/system_alert.html',
            alert_data=alert_data
        )
        text_body = self._render_text_template_safe(
            'emails/text/system_alert.txt',
            alert_data=alert_data
        )
        
        return self.send_email(subject, recipients, html_body, text_body)
    
    def send_performance_report(self, performance_data: Dict[str, Any], 
                               recipients: List[str]) -> bool:
        """
        Send performance report email.
        
        Args:
            performance_data: Performance data dictionary
            recipients: List of email addresses
        
        Returns:
            bool: True if email sent successfully
        """
        jefe_proyecto = performance_data.get('jefe_proyecto', 'N/A')
        periodo = performance_data.get('periodo', 'semanal')
        
        subject = f"📊 Reporte de Performance - {jefe_proyecto} ({periodo.title()})"
        
        html_body = self._render_template_safe(
            'emails/performance_report.html',
            performance_data=performance_data, 
            app_url=current_app.config.get('APP_URL', 'http://localhost:5000'), 
            jefe_proyecto=jefe_proyecto, 
            periodo=periodo
        )
        text_body = self._render_text_template_safe(
            'emails/text/performance_report.txt',
            performance_data=performance_data,
            jefe_proyecto=jefe_proyecto,
            periodo=periodo
        )
        
        return self.send_email(subject, recipients, html_body, text_body)
    
    def send_test_email(self, test_recipient: str) -> bool:
        """
        Send test email to verify email service configuration.
        
        Args:
            test_recipient: Email address to send test to
        
        Returns:
            bool: True if email sent successfully
        """
        test_data = {
            "title": "Test del Sistema de Email - Pagora EDP",
            "description": "Este es un email de prueba para verificar que el sistema de notificaciones de Pagora está funcionando correctamente.",
            "severity": "low",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        return self.send_system_alert(test_data, [test_recipient])
    
    def send_bulk_critical_alerts(self, critical_edps: List[Dict[str, Any]], 
                                 recipients: List[str]) -> bool:
        """
        Send bulk critical alerts email.
        
        Args:
            critical_edps: List of critical EDPs
            recipients: List of email addresses
        
        Returns:
            bool: True if email sent successfully
        """
        if not critical_edps:
            logger.info("📧 No critical EDPs to send alerts for")
            return True
        
        subject = f"🚨 {len(critical_edps)} EDPs Críticos Requieren Atención"
        
        html_body = self._render_template_safe(
            'emails/bulk_critical_alerts.html',
            critical_edps=critical_edps, 
            app_url=current_app.config.get('APP_URL', 'http://localhost:5000')
        )
        text_body = self._render_text_template_safe(
            'emails/text/bulk_critical_alerts.txt',
            critical_edps=critical_edps
        )
        
        return self.send_email(subject, recipients, html_body, text_body)

    def send_progressive_alert(self, edp_data: Dict[str, Any], alert_rule: Dict[str, Any], 
                              recipients: List[str]) -> bool:
        """
        Send progressive alert email based on alert rule.
        
        Args:
            edp_data: EDP data dictionary
            alert_rule: Alert rule configuration (dictionary)
            recipients: List of email addresses
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Formatear subject y mensaje - usando .get() para evitar KeyError
            subject = alert_rule['subject_template'].format(
                n_edp=edp_data.get('n_edp', 'N/A'),
                dias=edp_data.get('dias_sin_movimiento', 0),
                dias_restantes_critico=edp_data.get('dias_restantes_critico', 0)
            )
            
            # Preparar contexto para el template
            email_context = {
                **edp_data,  # Variables directas para compatibilidad
                'edp_data': edp_data,  # También como objeto para templates que lo esperan
                'alert_level': alert_rule['alert_level'],
                'alert_message': alert_rule['message_template'].format(
                    n_edp=edp_data.get('n_edp', 'N/A'),
                    dias=edp_data.get('dias_sin_movimiento', 0),
                    dias_restantes_critico=edp_data.get('dias_restantes_critico', 0),
                    cliente=edp_data.get('cliente', 'N/A')
                ),
                'app_url': current_app.config.get('APP_URL', 'http://localhost:5000')
            }
            
            # Determinar template según nivel de alerta
            template_map = {
                'info': 'emails/edp_alert_info.html',
                'warning': 'emails/edp_alert_warning.html',
                'urgent': 'emails/edp_alert_urgent.html',
                'critical': 'emails/critical_alert.html'
            }
            
            template_name = template_map.get(alert_rule['alert_level'], 'emails/edp_alert_info.html')
            
            # Renderizar templates
            html_body = self._render_template_safe(template_name, **email_context)
            
            # Generar nombre del template de texto correctamente
            if template_name.startswith('emails/'):
                text_template_name = template_name.replace('emails/', 'emails/text/').replace('.html', '.txt')
            else:
                text_template_name = f"emails/text/{template_name.replace('.html', '.txt')}"
            
            text_body = self._render_text_template_safe(text_template_name, **email_context)
            
            return self.send_email(subject, recipients, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error enviando alerta progresiva: {e}")
            return False
    
    def _process_kpis_data(self, kpis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and clean KPIs data for email templates.
        
        Args:
            kpis_data: Raw KPIs data dictionary
        
        Returns:
            Dict[str, Any]: Processed KPIs data with formatted strings and original data
        """
        try:
            processed = {}
            
            # Verificar si los datos vienen en el formato nuevo (con kpis_principales)
            if 'kpis_principales' in kpis_data:
                # Formato nuevo del manager service
                kpis_principales = kpis_data.get('kpis_principales', {})
                actividad_semanal = kpis_data.get('actividad_semanal', {})
                
                # Procesar datos básicos de KPIs
                processed['total_edps'] = str(kpis_principales.get('total_edps', 0))
                processed['total_monto'] = "{:,.0f}".format(kpis_principales.get('monto_total', 0))
                processed['dso_promedio'] = str(kpis_principales.get('dso_promedio', 0))
                processed['edps_criticos'] = str(kpis_principales.get('edps_criticos', 0))
                
                # Procesar datos semanales
                processed['edps_aprobados_semana'] = str(actividad_semanal.get('edps_aprobados', 0))
                processed['edps_pagados_semana'] = str(actividad_semanal.get('edps_pagados', 0))
                processed['monto_cobrado_semana'] = "{:,.0f}".format(actividad_semanal.get('monto_cobrado', 0))
                
                # Procesar proyectos activos
                processed['proyectos_activos'] = str(actividad_semanal.get('nuevos_edps', 0))
                
                # Si hay datos de proyectos críticos, usarlos para la tabla
                if 'edps_criticos' in kpis_data and kpis_data['edps_criticos']:
                    # Los datos ya vienen en el formato correcto del manager service
                    processed['proyectos_por_jefe'] = kpis_data['edps_criticos']
                else:
                    processed['proyectos_por_jefe'] = []
            
            else:
                # Formato original (directo)
                # Procesar datos básicos de KPIs
                processed['total_edps'] = str(kpis_data.get('total_edps', 0))
                processed['total_monto'] = "{:,.0f}".format(kpis_data.get('total_monto', 0))
                processed['dso_promedio'] = str(kpis_data.get('dso_promedio', 0))
                processed['edps_criticos'] = str(kpis_data.get('edps_criticos', 0))
                
                # Procesar datos semanales
                processed['edps_aprobados_semana'] = str(kpis_data.get('edps_aprobados_semana', 0))
                processed['edps_pagados_semana'] = str(kpis_data.get('edps_pagados_semana', 0))
                processed['monto_cobrado_semana'] = "{:,.0f}".format(kpis_data.get('monto_cobrado_semana', 0))
                
                # Procesar proyectos activos si existe la información
                if 'proyectos_por_jefe' in kpis_data:
                    proyectos_activos = len([p for p in kpis_data['proyectos_por_jefe'] if p.get('estado_proyecto') == 'activo'])
                    processed['proyectos_activos'] = str(proyectos_activos)
                    
                    # Incluir los datos de proyectos por jefe para la tabla
                    processed['proyectos_por_jefe'] = kpis_data['proyectos_por_jefe']
                else:
                    processed['proyectos_activos'] = '0'
                    processed['proyectos_por_jefe'] = []
                
                # Procesar información adicional si está disponible
                if 'proyectos_por_jefe' in kpis_data:
                    # Contar EDPs totales de todos los proyectos
                    total_edps_count = sum(len(p.get('edps', [])) for p in kpis_data['proyectos_por_jefe'])
                    if total_edps_count > 0:
                        processed['total_edps'] = str(total_edps_count)
                    
                    # Calcular monto total de todos los proyectos
                    total_monto = sum(p.get('total_monto', 0) for p in kpis_data['proyectos_por_jefe'])
                    if total_monto > 0:
                        processed['total_monto'] = "{:,.0f}".format(total_monto)
                    
                    # Calcular DSO promedio
                    dso_values = []
                    for proyecto in kpis_data['proyectos_por_jefe']:
                        for edp in proyecto.get('edps', []):
                            if edp.get('dias_sin_movimiento'):
                                dso_values.append(edp['dias_sin_movimiento'])
                    
                    if dso_values:
                        dso_promedio = sum(dso_values) / len(dso_values)
                        processed['dso_promedio'] = "{:.1f}".format(dso_promedio)
                    
                    # Contar EDPs críticos (más de 30 días)
                    edps_criticos = sum(1 for proyecto in kpis_data['proyectos_por_jefe'] 
                                      for edp in proyecto.get('edps', []) 
                                      if edp.get('dias_sin_movimiento', 0) > 30)
                    processed['edps_criticos'] = str(edps_criticos)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing KPIs data: {e}")
            # Retornar valores por defecto en caso de error
            return {
                'total_edps': '0',
                'total_monto': '0',
                'dso_promedio': '0',
                'edps_criticos': '0',
                'edps_aprobados_semana': '0',
                'edps_pagados_semana': '0',
                'monto_cobrado_semana': '0',
                'proyectos_activos': '0',
                'proyectos_por_jefe': []
            } 