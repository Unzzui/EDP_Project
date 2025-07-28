"""
Alert rules configuration for EDP progressive alerts.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any

class AlertLevel(Enum):
    """Niveles de alerta progresiva"""
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    """Regla de alerta para EDPs"""
    day_threshold: int
    alert_level: AlertLevel
    frequency_hours: int  # Cada cuántas horas enviar la alerta
    subject_template: str
    message_template: str
    recipients_type: str  # 'project_manager', 'controller', 'all'

# Configuración de alertas progresivas CON EXPERIENCIA DE USUARIO MEJORADA
ALERT_RULES = [
    # Alerta informativa a los 7 días
    AlertRule(
        day_threshold=7,
        alert_level=AlertLevel.INFO,
        frequency_hours=168,  # Una vez por semana
        subject_template="EDP {n_edp}: 1 semana sin movimiento",
        message_template="El EDP {n_edp} del cliente {cliente} lleva {dias} días sin movimiento",
        recipients_type="project_manager"
    ),
    
    # Alerta de advertencia a los 14 días
    AlertRule(
        day_threshold=14,
        alert_level=AlertLevel.WARNING,
        frequency_hours=96,  # Cada 4 días (reducido de 3)
        subject_template="ALERTA EDP {n_edp}: 2 semanas sin movimiento",
        message_template="El EDP {n_edp} lleva {dias} días sin movimiento. Quedan {dias_restantes_critico} días para ser crítico",
        recipients_type="project_manager"
    ),
    
    # Alerta urgente a los 21 días
    AlertRule(
        day_threshold=21,
        alert_level=AlertLevel.URGENT,
        frequency_hours=72,  # Cada 3 días (aumentado de 2)
        subject_template="EDP {n_edp}: 3 SEMANAS - ACCIÓN REQUERIDA",
        message_template="URGENTE: El EDP {n_edp} lleva {dias} días sin movimiento. Quedan solo {dias_restantes_critico} días para ser crítico",
        recipients_type="controller"
    ),
    
    # Alerta pre-crítica a los 28 días
    AlertRule(
        day_threshold=28,
        alert_level=AlertLevel.URGENT,
        frequency_hours=48,  # Cada 2 días (aumentado de diario)
        subject_template="EDP {n_edp}: QUEDAN {dias_restantes_critico} DÍAS PARA SER CRÍTICO",
        message_template="URGENTE: El EDP {n_edp} lleva {dias} días sin movimiento. Quedan solo {dias_restantes_critico} días para ser crítico",
        recipients_type="all"
    ),
    
    # Alerta crítica a los 30+ días - FRECUENCIA INTELIGENTE
    AlertRule(
        day_threshold=30,
        alert_level=AlertLevel.CRITICAL,
        frequency_hours=24,  # Diario inicialmente (era cada 12 horas)
        subject_template="EDP {n_edp}: CRÍTICO - ACCIÓN INMEDIATA REQUERIDA",
        message_template="CRÍTICO: El EDP {n_edp} lleva {dias} días sin movimiento y es oficialmente CRÍTICO. Si ya está gestionando este caso, puede pausar las alertas respondiendo a este email con 'PAUSAR ALERTAS'",
        recipients_type="all"
    )
]

# Configuración global
CRITICAL_DAYS_THRESHOLD = 30

# Mapeo de jefes de proyecto a emails (PRUEBAS - solo diegobravobe@gmail.com)
PROJECT_MANAGER_EMAILS = {
    'Juan Pérez': 'diegobravobe@gmail.com',
    'María González': 'diegobravobe@gmail.com',
    'Carlos Rodriguez': 'diegobravobe@gmail.com',
    'Ana Martinez': 'diegobravobe@gmail.com',
    'Luis Silva': 'diegobravobe@gmail.com',
    'Patricia Lopez': 'diegobravobe@gmail.com',
    'Roberto Chen': 'diegobravobe@gmail.com',
    'Sofia Morales': 'diegobravobe@gmail.com',
    # Todos mapeados a diegobravobe@gmail.com para pruebas
}

# Emails de controladores (PRUEBAS - solo diegobravobe@gmail.com)
CONTROLLER_EMAILS = [
    'diegobravobe@gmail.com'
]

# Emails de gerencia (PRUEBAS - solo diegobravobe@gmail.com)  
MANAGER_EMAILS = [
    'diegobravobe@gmail.com'
]

def get_alert_rules_for_days(dias_sin_movimiento: int) -> List[Dict[str, Any]]:
    """
    Obtiene las reglas de alerta que se activan para los días dados.
    
    Args:
        dias_sin_movimiento: Días sin movimiento del EDP
        
    Returns:
        List[Dict]: Lista de reglas activadas
    """
    triggered_rules = []
    
    for rule in ALERT_RULES:
        if dias_sin_movimiento >= rule.day_threshold:
            triggered_rules.append({
                'day_threshold': rule.day_threshold,
                'alert_level': rule.alert_level.value,
                'frequency_hours': rule.frequency_hours,
                'subject_template': rule.subject_template,
                'message_template': rule.message_template,
                'recipients_type': rule.recipients_type
            })
    
    return triggered_rules

def get_recipients_by_type(recipients_type: str, jefe_proyecto: str = None) -> List[str]:
    """
    Obtiene la lista de destinatarios según el tipo.
    
    Args:
        recipients_type: Tipo de destinatarios ('project_manager', 'controller', 'all')
        jefe_proyecto: Nombre del jefe de proyecto (opcional)
        
    Returns:
        List[str]: Lista de emails
    """
    recipients = []
    
    try:
        if recipients_type in ['project_manager', 'all']:
            # Obtener email del jefe de proyecto
            if jefe_proyecto and jefe_proyecto in PROJECT_MANAGER_EMAILS:
                recipients.append(PROJECT_MANAGER_EMAILS[jefe_proyecto])
        
        if recipients_type in ['controller', 'all']:
            # Agregar emails de controladores
            recipients.extend(CONTROLLER_EMAILS)
        
        if recipients_type == 'all':
            # Agregar emails de gerencia
            recipients.extend(MANAGER_EMAILS)
        
        # Remover duplicados y emails vacíos
        return list(set(filter(None, recipients)))
        
    except Exception as e:
        print(f"Error obteniendo destinatarios: {e}")
        return []
