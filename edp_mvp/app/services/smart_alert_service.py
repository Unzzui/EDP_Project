"""
Smart Alert Service - Sistema inteligente de alertas que considera la experiencia del usuario.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertAction(Enum):
    """Acciones que puede tomar el usuario en respuesta a una alerta"""
    ACKNOWLEDGED = "acknowledged"  # Usuario vio y reconoció la alerta
    IN_PROGRESS = "in_progress"    # Usuario está trabajando en el EDP
    ESCALATED = "escalated"        # Usuario escaló el problema
    PAUSED = "paused"             # Usuario pidió pausar alertas temporalmente
    RESOLVED = "resolved"         # EDP fue resuelto/actualizado

@dataclass
class AlertCooldown:
    """Configuración de cooldown inteligente para alertas"""
    edp_id: str
    last_alert_sent: datetime
    user_action: Optional[AlertAction]
    action_timestamp: Optional[datetime]
    cooldown_until: Optional[datetime]
    escalation_count: int = 0
    total_alerts_sent: int = 0

class SmartAlertService:
    """
    Servicio de alertas inteligente que considera:
    - Acciones del usuario
    - Historial de alertas
    - Contexto del negocio
    - Experiencia del usuario
    """
    
    def __init__(self):
        self.cooldowns: Dict[str, AlertCooldown] = {}
        self.business_hours = (9, 18)  # 9 AM a 6 PM
        self.max_daily_alerts = 3      # Máximo 3 alertas por EDP por día
        
    def should_send_alert(self, edp_data: Dict[str, Any], alert_rule: Dict[str, Any]) -> bool:
        """
        Determina si se debe enviar una alerta considerando el contexto inteligente.
        
        Args:
            edp_data: Datos del EDP
            alert_rule: Regla de alerta
            
        Returns:
            bool: True si se debe enviar la alerta
        """
        edp_id = edp_data.get('id') or edp_data.get('n_edp')
        if not edp_id:
            return True  # Sin ID, enviar por defecto
        
        # Verificar cooldown activo
        if self._is_in_cooldown(edp_id):
            logger.info(f"📴 EDP {edp_id} en cooldown, omitiendo alerta")
            return False
        
        # Verificar límite diario
        if self._exceeds_daily_limit(edp_id):
            logger.info(f"📵 EDP {edp_id} alcanzó límite diario de alertas")
            return False
        
        # Verificar horario laboral para alertas no críticas
        if alert_rule['alert_level'] != 'critical' and not self._is_business_hours():
            logger.info(f"🌙 Fuera de horario laboral, posponiendo alerta no crítica")
            return False
        
        # Aplicar lógica de frecuencia inteligente
        intelligent_frequency = self._calculate_intelligent_frequency(edp_id, alert_rule)
        if not self._frequency_allows_alert(edp_id, intelligent_frequency):
            return False
        
        return True
    
    def record_alert_sent(self, edp_data: Dict[str, Any], alert_rule: Dict[str, Any]):
        """Registra que se envió una alerta"""
        edp_id = edp_data.get('id') or edp_data.get('n_edp')
        if not edp_id:
            return
        
        now = datetime.now()
        if edp_id not in self.cooldowns:
            self.cooldowns[edp_id] = AlertCooldown(
                edp_id=edp_id,
                last_alert_sent=now,
                user_action=None,
                action_timestamp=None,
                cooldown_until=None
            )
        else:
            self.cooldowns[edp_id].last_alert_sent = now
        
        self.cooldowns[edp_id].total_alerts_sent += 1
        logger.info(f"📤 Alerta registrada para EDP {edp_id} (total: {self.cooldowns[edp_id].total_alerts_sent})")
    
    def record_user_action(self, edp_id: str, action: AlertAction, cooldown_hours: int = None):
        """
        Registra una acción del usuario y ajusta el cooldown.
        
        Args:
            edp_id: ID del EDP
            action: Acción tomada por el usuario
            cooldown_hours: Horas de cooldown personalizadas
        """
        now = datetime.now()
        
        if edp_id not in self.cooldowns:
            self.cooldowns[edp_id] = AlertCooldown(
                edp_id=edp_id,
                last_alert_sent=now,
                user_action=action,
                action_timestamp=now,
                cooldown_until=None
            )
        
        cooldown = self.cooldowns[edp_id]
        cooldown.user_action = action
        cooldown.action_timestamp = now
        
        # Determinar cooldown según la acción
        if cooldown_hours:
            cooldown_duration = cooldown_hours
        else:
            cooldown_duration = self._get_cooldown_for_action(action)
        
        cooldown.cooldown_until = now + timedelta(hours=cooldown_duration)
        
        logger.info(f"✅ Acción '{action.value}' registrada para EDP {edp_id}, cooldown hasta {cooldown.cooldown_until}")
    
    def _is_in_cooldown(self, edp_id: str) -> bool:
        """Verifica si un EDP está en período de cooldown"""
        if edp_id not in self.cooldowns:
            return False
        
        cooldown = self.cooldowns[edp_id]
        if not cooldown.cooldown_until:
            return False
        
        return datetime.now() < cooldown.cooldown_until
    
    def _exceeds_daily_limit(self, edp_id: str) -> bool:
        """Verifica si se excedió el límite diario de alertas"""
        if edp_id not in self.cooldowns:
            return False
        
        cooldown = self.cooldowns[edp_id]
        today = datetime.now().date()
        last_alert_date = cooldown.last_alert_sent.date() if cooldown.last_alert_sent else None
        
        # Si la última alerta fue hoy, verificar el contador
        if last_alert_date == today:
            return cooldown.total_alerts_sent >= self.max_daily_alerts
        
        # Si fue otro día, resetear contador
        if last_alert_date != today:
            cooldown.total_alerts_sent = 0
        
        return False
    
    def _is_business_hours(self) -> bool:
        """Verifica si estamos en horario laboral"""
        now = datetime.now()
        current_hour = now.hour
        # Solo lunes a viernes
        if now.weekday() >= 5:  # 5 = sábado, 6 = domingo
            return False
        
        return self.business_hours[0] <= current_hour < self.business_hours[1]
    
    def _calculate_intelligent_frequency(self, edp_id: str, alert_rule: Dict[str, Any]) -> int:
        """
        Calcula frecuencia inteligente basada en el historial y contexto.
        
        Returns:
            int: Horas entre alertas
        """
        base_frequency = alert_rule['frequency_hours']
        
        if edp_id not in self.cooldowns:
            return base_frequency
        
        cooldown = self.cooldowns[edp_id]
        
        # Si el usuario ya reconoció o está trabajando, aumentar frecuencia
        if cooldown.user_action in [AlertAction.ACKNOWLEDGED, AlertAction.IN_PROGRESS]:
            return base_frequency * 2  # Duplicar el tiempo
        
        # Si hay muchas alertas sin respuesta, aumentar progresivamente
        if cooldown.total_alerts_sent > 5:
            multiplier = min(cooldown.total_alerts_sent / 5, 3)  # Máximo 3x
            return int(base_frequency * multiplier)
        
        return base_frequency
    
    def _frequency_allows_alert(self, edp_id: str, frequency_hours: int) -> bool:
        """Verifica si ha pasado suficiente tiempo desde la última alerta"""
        if edp_id not in self.cooldowns:
            return True
        
        cooldown = self.cooldowns[edp_id]
        if not cooldown.last_alert_sent:
            return True
        
        time_since_last = datetime.now() - cooldown.last_alert_sent
        return time_since_last >= timedelta(hours=frequency_hours)
    
    def _get_cooldown_for_action(self, action: AlertAction) -> int:
        """
        Obtiene las horas de cooldown según la acción del usuario.
        
        Returns:
            int: Horas de cooldown
        """
        action_cooldowns = {
            AlertAction.ACKNOWLEDGED: 24,    # 1 día
            AlertAction.IN_PROGRESS: 48,     # 2 días
            AlertAction.ESCALATED: 12,       # 12 horas (menos porque se escaló)
            AlertAction.PAUSED: 72,          # 3 días
            AlertAction.RESOLVED: 9999       # Prácticamente infinito hasta que cambie el estado
        }
        
        return action_cooldowns.get(action, 24)  # Default 24 horas
    
    def get_alert_suggestions(self, edp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene sugerencias inteligentes para el manejo de alertas.
        
        Returns:
            Dict con sugerencias y estadísticas
        """
        edp_id = edp_data.get('id') or edp_data.get('n_edp')
        dias_sin_movimiento = edp_data.get('dias_sin_movimiento', 0)
        
        suggestions = {
            'recommended_actions': [],
            'alert_history': {},
            'smart_insights': []
        }
        
        if edp_id in self.cooldowns:
            cooldown = self.cooldowns[edp_id]
            suggestions['alert_history'] = {
                'total_alerts_sent': cooldown.total_alerts_sent,
                'last_alert': cooldown.last_alert_sent.isoformat() if cooldown.last_alert_sent else None,
                'last_user_action': cooldown.user_action.value if cooldown.user_action else None,
                'in_cooldown': self._is_in_cooldown(edp_id)
            }
        
        # Sugerencias basadas en días sin movimiento
        if dias_sin_movimiento >= 30:
            suggestions['recommended_actions'].extend([
                'Contactar directamente al cliente por teléfono',
                'Programar reunión urgente con el jefe de proyecto',
                'Considerar escalación a gerencia'
            ])
            suggestions['smart_insights'].append(
                'EDP en estado crítico - se recomienda contacto directo sobre alertas automáticas'
            )
        elif dias_sin_movimiento >= 21:
            suggestions['recommended_actions'].extend([
                'Revisar últimas comunicaciones con el cliente',
                'Verificar documentos pendientes',
                'Coordinar seguimiento con el jefe de proyecto'
            ])
            suggestions['smart_insights'].append(
                'EDP cerca del estado crítico - momento ideal para acción proactiva'
            )
        
        return suggestions
