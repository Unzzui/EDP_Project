"""
Service for managing progressive EDP alerts.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from flask import current_app
from ..extensions import db
from .email_service import EmailService
from .smart_alert_service import SmartAlertService, AlertAction
from ..config.alert_rules import (
    ALERT_RULES, CRITICAL_DAYS_THRESHOLD,
    get_alert_rules_for_days, get_recipients_by_type
)

logger = logging.getLogger(__name__)

class EDPAlertService:
    """Servicio para gestionar alertas progresivas de EDPs con lógica inteligente"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.smart_alert_service = SmartAlertService()
        
    def get_edps_for_alerts(self) -> List[Dict[str, Any]]:
        """Obtiene EDPs que requieren alertas desde la base de datos Supabase"""
        try:
            logger.info("🔍 Obteniendo datos de EDPs desde Supabase para análisis de alertas...")
            
            # Query directo a la tabla EDP en Supabase
            query = text("""
                SELECT 
                    n_edp,
                    cliente,
                    jefe_proyecto,
                    gestor,
                    monto_propuesto,
                    monto_aprobado,
                    estado,
                    estado_detallado,
                    updated_at,
                    created_at,
                    fecha_ultimo_seguimiento,
                    dso_actual,
                    dias_en_cliente,
                    COALESCE(
                        fecha_ultimo_seguimiento,
                        updated_at,
                        created_at
                    ) as fecha_ultima_actualizacion
                FROM edp 
                WHERE LOWER(estado) != 'pagado'
                AND LOWER(estado) != 'cancelado'
                AND LOWER(estado) != 'rechazado'
                ORDER BY fecha_ultima_actualizacion ASC
            """)
            
            result = db.session.execute(query).fetchall()
            db.session.commit()  # Commit para limpiar cualquier transacción pendiente
            
            if not result:
                logger.warning("No se encontraron EDPs en la base de datos")
                return []
            
            edps_with_alerts = []
            
            for row in result:
                # Convertir row a diccionario
                edp = {
                    'n_edp': str(row.n_edp),
                    'cliente': row.cliente or 'N/A',
                    'jefe_proyecto': row.jefe_proyecto or row.gestor or 'N/A',
                    'monto_propuesto': float(row.monto_propuesto or 0),
                    'monto_aprobado': float(row.monto_aprobado or 0),
                    'estado_edp': row.estado or 'N/A',
                    'estado_detallado': row.estado_detallado or 'N/A',
                    'fecha_ultima_actualizacion': row.fecha_ultima_actualizacion,
                    'dso_actual': row.dso_actual or 0,
                    'dias_en_cliente': row.dias_en_cliente or 0
                }
                
                # Calcular días sin movimiento
                dias_sin_movimiento = self._calculate_days_without_movement(edp)
                
                if dias_sin_movimiento >= 7:  # Solo alertas a partir de 7 días
                    edp_alert_data = {
                        'n_edp': edp['n_edp'],
                        'cliente': edp['cliente'],
                        'jefe_proyecto': edp['jefe_proyecto'],
                        'monto_propuesto': edp['monto_propuesto'],
                        'monto_aprobado': edp['monto_aprobado'],
                        'estado_edp': edp['estado_edp'],
                        'estado_detallado': edp['estado_detallado'],
                        'fecha_ultima_actualizacion': edp['fecha_ultima_actualizacion'],
                        'dias_sin_movimiento': dias_sin_movimiento,
                        'dias_restantes_critico': max(0, CRITICAL_DAYS_THRESHOLD - dias_sin_movimiento),
                        'is_critical': dias_sin_movimiento >= CRITICAL_DAYS_THRESHOLD,
                        'alert_rules_triggered': get_alert_rules_for_days(dias_sin_movimiento)
                    }
                    edps_with_alerts.append(edp_alert_data)
            
            logger.info(f"📊 Encontrados {len(edps_with_alerts)} EDPs que requieren alertas")
            return edps_with_alerts
            
        except Exception as e:
            logger.error(f"Error obteniendo EDPs para alertas desde Supabase: {e}")
            # Rollback en caso de error
            try:
                db.session.rollback()
            except:
                pass
            return []
    
    def _calculate_days_without_movement(self, edp: Dict[str, Any]) -> int:
        """Calcula días sin movimiento basado en fecha de última actualización"""
        try:
            fecha_ultima = edp.get('fecha_ultima_actualizacion')
            if not fecha_ultima:
                return 999  # Si no hay fecha, considerarlo muy antiguo
            
            # Si es un datetime object, usarlo directamente
            if isinstance(fecha_ultima, datetime):
                return (datetime.now() - fecha_ultima).days
            
            # Si es string, intentar parsearlo
            if isinstance(fecha_ultima, str):
                # Intentar varios formatos de fecha
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        fecha_dt = datetime.strptime(fecha_ultima, fmt)
                        return (datetime.now() - fecha_dt).days
                    except ValueError:
                        continue
                
                logger.warning(f"No se pudo parsear fecha: {fecha_ultima}")
                return 999
            
            return 999
            
        except Exception as e:
            logger.error(f"Error calculando días sin movimiento: {e}")
            return 999
    
    def should_send_alert(self, edp_data: Dict[str, Any], alert_rule: Dict[str, Any]) -> bool:
        """
        Determina si se debe enviar una alerta usando lógica inteligente de experiencia de usuario.
        
        La lógica incluye:
        - Cooldowns inteligentes basados en acciones del usuario
        - Límites diarios para evitar spam
        - Consideración de horarios laborales
        - Frecuencias adaptativas
        """
        try:
            # 1. Verificar la lógica inteligente primero
            should_send_smart = self.smart_alert_service.should_send_alert(edp_data, alert_rule)
            if not should_send_smart:
                return False
            
            # 2. Verificar frecuencia tradicional como respaldo
            last_alert = self._get_last_alert_time(
                edp_data['n_edp'], 
                alert_rule['day_threshold']
            )
            
            if not last_alert:
                return True  # Primera vez que se activa esta regla
            
            # Verificar si ha pasado el tiempo suficiente según la frecuencia
            hours_since_last = (datetime.now() - last_alert).total_seconds() / 3600
            frequency_allows = hours_since_last >= alert_rule['frequency_hours']
            
            # Aplicar lógica combinada
            return frequency_allows
            
        except Exception as e:
            logger.error(f"Error verificando si enviar alerta: {e}")
            # En caso de error, usar solo la lógica inteligente si está disponible
            try:
                return self.smart_alert_service.should_send_alert(edp_data, alert_rule)
            except:
                return True  # Último recurso: enviar alerta por seguridad
    
    def _get_last_alert_time(self, n_edp: str, day_threshold: int) -> Optional[datetime]:
        """Obtiene la última vez que se envió una alerta específica"""
        try:
            query = text("""
                SELECT MAX(sent_at) 
                FROM edp_alerts 
                WHERE n_edp = :n_edp 
                AND day_threshold = :day_threshold
            """)
            
            result = db.session.execute(query, {
                'n_edp': n_edp,
                'day_threshold': day_threshold
            }).scalar()
            
            db.session.commit()  # Commit para limpiar la transacción
            return result
            
        except Exception as e:
            logger.warning(f"Error obteniendo última alerta: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    def _record_alert_sent(self, edp_data: Dict[str, Any], alert_rule: Dict[str, Any], 
                          recipients: List[str]) -> None:
        """Registra que se envió una alerta tanto en BD como en el servicio inteligente"""
        try:
            # 1. Registrar en base de datos (comportamiento original)
            query = text("""
                INSERT INTO edp_alerts 
                (n_edp, day_threshold, alert_level, recipients, sent_at, dias_sin_movimiento)
                VALUES (:n_edp, :day_threshold, :alert_level, :recipients, :sent_at, :dias_sin_movimiento)
            """)
            
            db.session.execute(query, {
                'n_edp': edp_data['n_edp'],
                'day_threshold': alert_rule['day_threshold'],
                'alert_level': alert_rule['alert_level'],
                'recipients': ','.join(recipients),
                'sent_at': datetime.now(),
                'dias_sin_movimiento': edp_data['dias_sin_movimiento']
            })
            
            db.session.commit()
            
            # 2. Notificar al servicio inteligente para tracking de experiencia de usuario
            self.smart_alert_service.record_alert_sent(edp_data, alert_rule)
            
            logger.info(f"✅ Registrada alerta enviada para EDP {edp_data['n_edp']} (DB + Smart Service)")
            
        except Exception as e:
            logger.error(f"Error registrando alerta enviada: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def acknowledge_alert(self, edp_id: str, user_action: str = "acknowledged") -> Dict[str, Any]:
        """
        Permite a los usuarios reconocer alertas y pausar notificaciones temporalmente.
        
        Args:
            edp_id: ID del EDP
            user_action: Tipo de acción ('acknowledged', 'in_progress', 'paused', etc.)
        
        Returns:
            Dict con el resultado de la acción
        """
        try:
            # Mapear strings a enum
            action_map = {
                'acknowledged': AlertAction.ACKNOWLEDGED,
                'in_progress': AlertAction.IN_PROGRESS,
                'escalated': AlertAction.ESCALATED,
                'paused': AlertAction.PAUSED,
                'resolved': AlertAction.RESOLVED
            }
            
            action = action_map.get(user_action, AlertAction.ACKNOWLEDGED)
            
            # Registrar la acción en el servicio inteligente
            self.smart_alert_service.record_user_action(edp_id, action)
            
            # Determinar mensaje de respuesta
            messages = {
                AlertAction.ACKNOWLEDGED: "Alerta reconocida. Se reducirá la frecuencia de notificaciones.",
                AlertAction.IN_PROGRESS: "EDP marcado como 'en progreso'. Alertas pausadas por 48 horas.",
                AlertAction.ESCALATED: "EDP escalado. Se continuará con alertas en frecuencia normal.",
                AlertAction.PAUSED: "Alertas pausadas por 72 horas. Se reanudarán automáticamente.",
                AlertAction.RESOLVED: "EDP marcado como resuelto. Alertas pausadas hasta cambio de estado."
            }
            
            return {
                'success': True,
                'message': messages.get(action, "Acción registrada correctamente."),
                'action': user_action,
                'edp_id': edp_id,
                'cooldown_active': True
            }
            
        except Exception as e:
            logger.error(f"Error procesando acción de usuario para EDP {edp_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'edp_id': edp_id
            }
    
    def test_alert_system(self, test_email: str = None) -> Dict[str, Any]:
        """Prueba el sistema de alertas con datos simulados"""
        try:
            logger.info("🧪 Ejecutando prueba del sistema de alertas...")
            
            # Datos de prueba
            test_edp = {
                'n_edp': 'TEST-001',
                'cliente': 'Cliente Prueba',
                'jefe_proyecto': 'Test Manager',
                'monto_propuesto': 100000,
                'estado_edp': 'enviado',
                'fecha_ultima_actualizacion': '01/01/2024',
                'dias_sin_movimiento': 15,
                'dias_restantes_critico': 15,
                'is_critical': False,
                'alert_rules_triggered': get_alert_rules_for_days(15)
            }
            
            if test_email:
                # Enviar alerta de prueba
                alert_rule = test_edp['alert_rules_triggered'][0] if test_edp['alert_rules_triggered'] else {
                    'day_threshold': 15,
                    'alert_level': 'warning',
                    'frequency_hours': 72,
                    'subject_template': '🧪 PRUEBA: EDP {n_edp} - {dias} días sin movimiento',
                    'message_template': 'Esta es una alerta de prueba para el EDP {n_edp}',
                    'recipients_type': 'all'
                }
                
                success = self.email_service.send_progressive_alert(
                    test_edp, alert_rule, [test_email]
                )
                
                return {
                    'test_completed': True,
                    'email_sent': success,
                    'test_recipient': test_email,
                    'test_edp': test_edp['n_edp']
                }
            else:
                # Solo verificar configuración
                return {
                    'test_completed': True,
                    'email_service_enabled': self.email_service.is_enabled(),
                    'database_available': True,
                    'alert_rules_count': len(ALERT_RULES)
                }
                
        except Exception as e:
            logger.error(f"Error en prueba del sistema de alertas: {e}")
            return {'error': str(e)}
    
    def send_progressive_alerts(self) -> Dict[str, Any]:
        """Envía alertas progresivas según las reglas configuradas"""
        try:
            logger.info("🚨 Iniciando procesamiento de alertas progresivas...")
            
            edps_with_alerts = self.get_edps_for_alerts()
            
            results = {
                'total_edps_processed': len(edps_with_alerts),
                'alerts_sent': 0,
                'alerts_skipped': 0,
                'errors': 0,
                'details': []
            }
            
            for edp_data in edps_with_alerts:
                logger.info(f"📋 Procesando EDP {edp_data['n_edp']} ({edp_data['dias_sin_movimiento']} días)")
                edp_results = self._process_edp_alerts(edp_data)
                results['alerts_sent'] += edp_results['sent']
                results['alerts_skipped'] += edp_results['skipped']
                results['errors'] += edp_results['errors']
                results['details'].append({
                    'n_edp': edp_data['n_edp'],
                    'dias_sin_movimiento': edp_data['dias_sin_movimiento'],
                    'alerts_sent': edp_results['sent'],
                    'alerts_skipped': edp_results['skipped']
                })
            
            logger.info(f"✅ Alertas procesadas: {results['alerts_sent']} enviadas, {results['alerts_skipped']} omitidas, {results['errors']} errores")
            return results
            
        except Exception as e:
            logger.error(f"Error enviando alertas progresivas: {e}")
            return {'error': str(e)}
    
    def _process_edp_alerts(self, edp_data: Dict[str, Any]) -> Dict[str, int]:
        """Procesa las alertas para un EDP específico"""
        results = {'sent': 0, 'skipped': 0, 'errors': 0}
        
        for alert_rule in edp_data['alert_rules_triggered']:
            try:
                logger.info(f"  📧 Evaluando regla {alert_rule['day_threshold']} días ({alert_rule['alert_level']})")
                
                if self.should_send_alert(edp_data, alert_rule):
                    recipients = get_recipients_by_type(
                        alert_rule['recipients_type'], 
                        edp_data['jefe_proyecto']
                    )
                    
                    if recipients:
                        success = self.email_service.send_progressive_alert(
                            edp_data, alert_rule, recipients
                        )
                        if success:
                            self._record_alert_sent(edp_data, alert_rule, recipients)
                            results['sent'] += 1
                            logger.info(f"    ✅ Alerta enviada a {len(recipients)} destinatarios")
                        else:
                            results['errors'] += 1
                            logger.error(f"    ❌ Error enviando alerta")
                    else:
                        logger.warning(f"    ⚠️ No se encontraron destinatarios para EDP {edp_data['n_edp']}")
                        results['skipped'] += 1
                else:
                    results['skipped'] += 1
                    logger.info(f"    ⏭️ Alerta omitida (ya enviada reciente)")
                    
            except Exception as e:
                logger.error(f"Error procesando alerta para EDP {edp_data['n_edp']}: {e}")
                results['errors'] += 1
        
        return results
    
    def send_daily_critical_summary(self) -> Dict[str, Any]:
        """Envía resumen diario de EDPs críticos"""
        try:
            logger.info("📊 Enviando resumen diario de EDPs críticos...")
            
            edps_with_alerts = self.get_edps_for_alerts()
            critical_edps = [
                edp for edp in edps_with_alerts 
                if edp['is_critical']
            ]
            
            if critical_edps:
                # Enviar a gerencia
                manager_emails = get_recipients_by_type('all')
                success = self.email_service.send_bulk_critical_alerts(
                    critical_edps, manager_emails
                )
                
                result = {
                    'critical_edps_count': len(critical_edps),
                    'email_sent': success,
                    'recipients': manager_emails
                }
            else:
                result = {'critical_edps_count': 0, 'email_sent': False}
            
            logger.info(f"📊 Resumen crítico enviado: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en resumen crítico diario: {e}")
            return {'error': str(e)}
    
    def get_alert_history(self, n_edp: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene el historial de alertas enviadas"""
        try:
            if n_edp:
                query = text("""
                    SELECT * FROM edp_alerts 
                    WHERE n_edp = :n_edp 
                    ORDER BY sent_at DESC 
                    LIMIT :limit
                """)
                params = {'n_edp': n_edp, 'limit': limit}
            else:
                query = text("""
                    SELECT * FROM edp_alerts 
                    ORDER BY sent_at DESC 
                    LIMIT :limit
                """)
                params = {'limit': limit}
            
            result = db.session.execute(query, params).fetchall()
            db.session.commit()  # Commit para limpiar la transacción
            
            history = []
            for row in result:
                history.append({
                    'n_edp': row[1],
                    'day_threshold': row[2],
                    'alert_level': row[3],
                    'recipients': row[4].split(',') if row[4] else [],
                    'sent_at': row[5],
                    'dias_sin_movimiento': row[6]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de alertas: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return []
    
    def test_alert_system(self, test_email: str = None) -> Dict[str, Any]:
        """Prueba el sistema de alertas con datos simulados"""
        try:
            logger.info("🧪 Ejecutando prueba del sistema de alertas...")
            
            # Datos de prueba
            test_edp = {
                'n_edp': 'TEST-001',
                'cliente': 'Cliente Prueba',
                'jefe_proyecto': 'Test Manager',
                'monto_propuesto': 100000,
                'estado_edp': 'enviado',
                'fecha_ultima_actualizacion': '01/01/2024',
                'dias_sin_movimiento': 15,
                'dias_restantes_critico': 15,
                'is_critical': False,
                'alert_rules_triggered': get_alert_rules_for_days(15)
            }
            
            if test_email:
                # Enviar alerta de prueba
                alert_rule = test_edp['alert_rules_triggered'][0] if test_edp['alert_rules_triggered'] else {
                    'day_threshold': 15,
                    'alert_level': 'warning',
                    'frequency_hours': 72,
                    'subject_template': '🧪 PRUEBA: EDP {n_edp} - {dias} días sin movimiento',
                    'message_template': 'Esta es una alerta de prueba para el EDP {n_edp}',
                    'recipients_type': 'all'
                }
                
                success = self.email_service.send_progressive_alert(
                    test_edp, alert_rule, [test_email]
                )
                
                return {
                    'test_completed': True,
                    'email_sent': success,
                    'test_recipient': test_email,
                    'test_edp': test_edp['n_edp']
                }
            else:
                # Solo verificar configuración
                return {
                    'test_completed': True,
                    'email_service_enabled': self.email_service.is_enabled(),
                    'database_available': True,
                    'alert_rules_count': len(ALERT_RULES)
                }
                
        except Exception as e:
            logger.error(f"Error en prueba del sistema de alertas: {e}")
            return {'error': str(e)}
