"""
Email Permissions Service for role-based email filtering.
"""
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class EmailRole(Enum):
    """Email recipient roles - using existing system roles."""
    ADMIN = "admin"                   # Administradores - toda la información
    MANAGER = "manager"               # Gerentes - información general
    CONTROLLER = "controller"         # Controllers - toda la información operacional
    JEFE_PROYECTO = "jefe_proyecto"   # Jefes de proyecto - solo sus proyectos
    MIEMBRO_EQUIPO = "miembro_equipo_proyecto"  # Miembros de equipo - información limitada
    CLIENT = "client"                 # Clientes - solo información de sus proyectos

class EmailPermission(Enum):
    """Email permissions for different data types."""
    ALL_DATA = "all_data"                    # Acceso a toda la información
    PROJECT_DATA = "project_data"            # Solo datos de proyectos asignados
    FINANCIAL_DATA = "financial_data"        # Solo datos financieros
    OPERATIONAL_DATA = "operational_data"    # Solo datos operacionales
    CLIENT_DATA = "client_data"              # Solo datos del cliente
    CRITICAL_ALERTS = "critical_alerts"      # Alertas críticas
    WEEKLY_SUMMARY = "weekly_summary"        # Resumen semanal
    PAYMENT_REMINDERS = "payment_reminders"  # Recordatorios de pago

class EmailPermissionsService:
    """Service for managing email permissions and data filtering."""
    
    def __init__(self):
        # Definir permisos por rol - usando roles existentes del sistema
        self.role_permissions = {
            EmailRole.ADMIN: [
                EmailPermission.ALL_DATA,
                EmailPermission.CRITICAL_ALERTS,
                EmailPermission.WEEKLY_SUMMARY,
                EmailPermission.FINANCIAL_DATA,
                EmailPermission.OPERATIONAL_DATA,
                EmailPermission.PAYMENT_REMINDERS
            ],
            EmailRole.MANAGER: [
                EmailPermission.ALL_DATA,
                EmailPermission.CRITICAL_ALERTS,
                EmailPermission.WEEKLY_SUMMARY,
                EmailPermission.FINANCIAL_DATA,
                EmailPermission.OPERATIONAL_DATA
            ],
            EmailRole.CONTROLLER: [
                EmailPermission.ALL_DATA,
                EmailPermission.CRITICAL_ALERTS,
                EmailPermission.WEEKLY_SUMMARY,
                EmailPermission.OPERATIONAL_DATA,
                EmailPermission.PAYMENT_REMINDERS
            ],
            EmailRole.JEFE_PROYECTO: [
                EmailPermission.PROJECT_DATA,
                EmailPermission.CRITICAL_ALERTS,
                EmailPermission.WEEKLY_SUMMARY
            ],
            EmailRole.MIEMBRO_EQUIPO: [
                EmailPermission.PROJECT_DATA,
                EmailPermission.CRITICAL_ALERTS
            ],
            EmailRole.CLIENT: [
                EmailPermission.CLIENT_DATA,
                EmailPermission.PAYMENT_REMINDERS
            ]
        }
    
    def get_user_role(self, email: str) -> EmailRole:
        """
        Get user role based on email address using existing User system.
        
        Args:
            email: User email address
            
        Returns:
            EmailRole: User role
        """
        try:
            from ..models.user import User
            
            # Buscar usuario en el sistema existente
            user = User.query.filter_by(username=email, activo=True).first()
            
            if user:
                # Mapear rol del sistema existente a EmailRole
                role_mapping = {
                    'admin': EmailRole.ADMIN,
                    'manager': EmailRole.MANAGER,
                    'controller': EmailRole.CONTROLLER,
                    'jefe_proyecto': EmailRole.JEFE_PROYECTO,
                    'miembro_equipo_proyecto': EmailRole.MIEMBRO_EQUIPO
                }
                return role_mapping.get(user.rol, EmailRole.MIEMBRO_EQUIPO)
            else:
                # Fallback a lógica simple si no está en la base de datos
                if "diegobravobe@gmail.com" in email:
                    return EmailRole.ADMIN  # Para testing
                elif "controller" in email.lower():
                    return EmailRole.CONTROLLER
                elif "manager" in email.lower():
                    return EmailRole.MANAGER
                else:
                    return EmailRole.JEFE_PROYECTO  # Default
                    
        except Exception as e:
            logger.error(f"Error getting user role for {email}: {e}")
            # Fallback a lógica simple
            if "diegobravobe@gmail.com" in email:
                return EmailRole.ADMIN
            else:
                return EmailRole.JEFE_PROYECTO
    
    def can_access_data(self, user_email: str, permission: EmailPermission) -> bool:
        """
        Check if user can access specific data type.
        
        Args:
            user_email: User email address
            permission: Required permission
            
        Returns:
            bool: True if user has permission
        """
        user_role = self.get_user_role(user_email)
        user_permissions = self.role_permissions.get(user_role, [])
        
        return permission in user_permissions
    
    def filter_data_by_role(self, data: Any, user_email: str, 
                           data_type: str) -> Any:
        """
        Filter data based on user role and data type.
        
        Args:
            data: Raw data to filter (Dict or List)
            user_email: User email address
            data_type: Type of data being filtered
            
        Returns:
            Any: Filtered data
        """
        user_role = self.get_user_role(user_email)
        
        if data_type == "weekly_summary":
            return self._filter_weekly_summary(data, user_role, user_email)
        elif data_type == "critical_alerts":
            return self._filter_critical_alerts(data, user_role, user_email)
        elif data_type == "payment_reminders":
            return self._filter_payment_reminders(data, user_role, user_email)
        else:
            return data
    
    def _filter_weekly_summary(self, data: Dict[str, Any], user_role: EmailRole, 
                              user_email: str) -> Dict[str, Any]:
        """Filter weekly summary data based on user role."""
        filtered_data = data.copy()
        
        if user_role in [EmailRole.ADMIN, EmailRole.MANAGER, EmailRole.CONTROLLER]:
            # Acceso completo - mantener todos los proyectos
            return filtered_data
        
        elif user_role == EmailRole.JEFE_PROYECTO:
            # Solo proyectos asignados al jefe
            if 'proyectos_por_jefe' in filtered_data:
                user_projects = self._get_user_projects(user_email)
                filtered_data['proyectos_por_jefe'] = [
                    p for p in filtered_data['proyectos_por_jefe']
                    if p.get('jefe_proyecto') in user_projects
                ]
            
            # Recalcular KPIs basados en proyectos filtrados
            filtered_data = self._recalculate_kpis_for_filtered_projects(filtered_data)
        
        elif user_role == EmailRole.MIEMBRO_EQUIPO:
            # Solo proyectos asignados al miembro
            if 'proyectos_por_jefe' in filtered_data:
                user_projects = self._get_user_projects(user_email)
                filtered_data['proyectos_por_jefe'] = [
                    p for p in filtered_data['proyectos_por_jefe']
                    if p.get('jefe_proyecto') in user_projects
                ]
            
            # Recalcular KPIs basados en proyectos filtrados
            filtered_data = self._recalculate_kpis_for_filtered_projects(filtered_data)
        
        elif user_role == EmailRole.CLIENT:
            # Solo información del cliente
            if 'proyectos_por_jefe' in filtered_data:
                user_clients = self._get_user_clients(user_email)
                filtered_data['proyectos_por_jefe'] = [
                    p for p in filtered_data['proyectos_por_jefe']
                    if p.get('cliente') in user_clients
                ]
                filtered_data = self._recalculate_kpis_for_filtered_projects(filtered_data)
        
        return filtered_data
    
    def _filter_critical_alerts(self, data: List[Dict[str, Any]], user_role: EmailRole, 
                               user_email: str) -> List[Dict[str, Any]]:
        """Filter critical alerts based on user role."""
        if user_role in [EmailRole.ADMIN, EmailRole.MANAGER, EmailRole.CONTROLLER]:
            return data
        
        elif user_role == EmailRole.JEFE_PROYECTO:
            user_projects = self._get_user_projects(user_email)
            return [proyecto for proyecto in data if proyecto.get('jefe_proyecto') in user_projects]
        
        elif user_role == EmailRole.MIEMBRO_EQUIPO:
            user_projects = self._get_user_projects(user_email)
            return [proyecto for proyecto in data if proyecto.get('jefe_proyecto') in user_projects]
        
        elif user_role == EmailRole.CLIENT:
            user_clients = self._get_user_clients(user_email)
            return [proyecto for proyecto in data if proyecto.get('cliente') in user_clients]
        
        return data
    
    def _filter_payment_reminders(self, data: Dict[str, Any], user_role: EmailRole, 
                                 user_email: str) -> Dict[str, Any]:
        """Filter payment reminders based on user role."""
        if user_role in [EmailRole.CONTROLLER, EmailRole.ADMIN]:
            return data
        
        elif user_role == EmailRole.CLIENT:
            user_clients = self._get_user_clients(user_email)
            if isinstance(data, list):
                return [reminder for reminder in data if reminder.get('cliente') in user_clients]
            else:
                return data
        
        return data
    
    def _get_user_projects(self, user_email: str) -> List[str]:
        """Get projects assigned to user using existing User system."""
        try:
            from ..models.user import User
            
            # Buscar usuario en el sistema existente
            user = User.query.filter_by(username=user_email, activo=True).first()
            
            if user:
                # Para jefes de proyecto, usar su nombre como proyecto asignado
                if user.rol == 'jefe_proyecto':
                    return [user.nombre_completo]
                # Para miembros de equipo, usar su jefe asignado
                elif user.rol == 'miembro_equipo_proyecto' and user.jefe_asignado:
                    return [user.jefe_asignado]
                # Para otros roles, acceso completo
                else:
                    return ["Diego Bravo", "Pedro Rojas", "Carolina López"]
            else:
                # Fallback a configuración hardcodeada
                user_projects = {
                    "diegobravobe@gmail.com": ["Diego Bravo", "Pedro Rojas", "Carolina López"],
                    "pedro.rojas@empresa.com": ["Pedro Rojas"],
                    "carolina.lopez@empresa.com": ["Carolina López"]
                }
                return user_projects.get(user_email, [])
                
        except Exception as e:
            logger.error(f"Error getting user projects for {user_email}: {e}")
            # Fallback a configuración hardcodeada
            user_projects = {
                "diegobravobe@gmail.com": ["Diego Bravo", "Pedro Rojas", "Carolina López"],
                "pedro.rojas@empresa.com": ["Pedro Rojas"],
                "carolina.lopez@empresa.com": ["Carolina López"]
            }
            return user_projects.get(user_email, [])
    
    def _get_user_clients(self, user_email: str) -> List[str]:
        """Get clients associated with user."""
        try:
            from ..models.email_user import EmailUser
            
            # Buscar usuario en la base de datos
            user = EmailUser.query.filter_by(email=user_email, is_active=True).first()
            
            if user:
                # Obtener clientes asignados desde la base de datos
                return user.get_assigned_clients()
            else:
                # Fallback a configuración hardcodeada
                user_clients = {
                    "cliente.arauco@arauco.com": ["Arauco"],
                    "cliente.enel@enel.com": ["Enel"],
                    "cliente.minera@minera.com": ["Minera Escondida"]
                }
                return user_clients.get(user_email, [])
                
        except Exception as e:
            logger.error(f"Error getting user clients for {user_email}: {e}")
            # Fallback a configuración hardcodeada
            user_clients = {
                "cliente.arauco@arauco.com": ["Arauco"],
                "cliente.enel@enel.com": ["Enel"],
                "cliente.minera@minera.com": ["Minera Escondida"]
            }
            return user_clients.get(user_email, [])
    
    def _recalculate_kpis_for_filtered_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate KPIs based on filtered projects."""
        if 'proyectos_por_jefe' in data:
            projects = data['proyectos_por_jefe']
            
            # Recalcular totales
            total_edps = sum(len(p.get('edps', [])) for p in projects)
            total_monto = sum(p.get('total_monto', 0) for p in projects)
            
            # Actualizar KPIs principales
            if 'kpis_principales' in data:
                data['kpis_principales']['total_edps'] = total_edps
                data['kpis_principales']['monto_total'] = total_monto
            
            # Actualizar KPIs directos
            data['total_edps'] = total_edps
            data['total_monto'] = total_monto
        
        return data
    
    def get_recipients_by_role(self, role: EmailRole) -> List[str]:
        """
        Get all recipients for a specific role using existing User system.
        
        Args:
            role: Email role
            
        Returns:
            List[str]: List of email addresses
        """
        try:
            from ..models.user import User
            
            # Mapear EmailRole a string para consulta
            role_mapping = {
                EmailRole.ADMIN: 'admin',
                EmailRole.MANAGER: 'manager',
                EmailRole.CONTROLLER: 'controller',
                EmailRole.JEFE_PROYECTO: 'jefe_proyecto',
                EmailRole.MIEMBRO_EQUIPO: 'miembro_equipo_proyecto'
            }
            
            role_string = role_mapping.get(role)
            if role_string:
                # Buscar usuarios activos con ese rol
                users = User.query.filter_by(
                    rol=role_string, 
                    activo=True
                ).all()
                return [user.username for user in users]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting recipients for role {role}: {e}")
            # Fallback a configuración hardcodeada
            role_recipients = {
                EmailRole.ADMIN: ["diegobravobe@gmail.com"],
                EmailRole.MANAGER: ["gerente@empresa.com"],
                EmailRole.CONTROLLER: ["controller@empresa.com"],
                EmailRole.JEFE_PROYECTO: ["pedro.rojas@empresa.com", "carolina.lopez@empresa.com"],
                EmailRole.MIEMBRO_EQUIPO: ["miembro@empresa.com"],
                EmailRole.CLIENT: ["cliente.arauco@arauco.com", "cliente.enel@enel.com"]
            }
            return role_recipients.get(role, [])
    
    def get_recipients_for_permission(self, permission: EmailPermission) -> List[str]:
        """
        Get all recipients that have a specific permission.
        
        Args:
            permission: Required permission
            
        Returns:
            List[str]: List of email addresses
        """
        # Por ahora, solo permitir diegobravobe@gmail.com para pruebas
        return ["diegobravobe@gmail.com"] 