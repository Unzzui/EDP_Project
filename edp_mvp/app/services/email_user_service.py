"""
Email User Service for managing email users and their configurations.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.email_user import EmailUser, EmailUserProject, EmailUserClient, EmailUserPreference
from ..extensions import db

logger = logging.getLogger(__name__)

class EmailUserService:
    """Service for managing email users and their configurations."""
    
    def create_user(self, email: str, name: str, role: str, 
                   email_config: Optional[Dict[str, Any]] = None) -> EmailUser:
        """
        Create a new email user with configuration.
        
        Args:
            email: User email address
            name: User name
            role: User role (executive, manager, project_manager, controller, finance, client)
            email_config: Email configuration dictionary
            
        Returns:
            EmailUser: Created user
        """
        try:
            # Verificar si el usuario ya existe
            existing_user = EmailUser.query.filter_by(email=email).first()
            if existing_user:
                raise ValueError(f"User with email {email} already exists")
            
            # Crear usuario
            user = EmailUser(
                email=email,
                name=name,
                role=role
            )
            
            # Aplicar configuración de correo si se proporciona
            if email_config:
                user.mail_server = email_config.get('mail_server')
                user.mail_port = email_config.get('mail_port', 587)
                user.mail_use_tls = email_config.get('mail_use_tls', True)
                user.mail_username = email_config.get('mail_username')
                user.mail_password = email_config.get('mail_password')
                user.mail_default_sender = email_config.get('mail_default_sender')
                user.enable_critical_alerts = email_config.get('enable_critical_alerts', True)
                user.enable_payment_reminders = email_config.get('enable_payment_reminders', True)
                user.enable_weekly_summary = email_config.get('enable_weekly_summary', True)
                user.enable_system_alerts = email_config.get('enable_system_alerts', True)
            
            db.session.add(user)
            db.session.commit()
            
            # Crear preferencias por defecto
            preferences = EmailUserPreference(user_id=user.id)
            db.session.add(preferences)
            db.session.commit()
            
            logger.info(f"✅ Created email user: {email} with role: {role}")
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating email user {email}: {e}")
            raise
    
    def update_user_email_config(self, user_id: int, email_config: Dict[str, Any]) -> bool:
        """
        Update user's email configuration.
        
        Args:
            user_id: User ID
            email_config: Email configuration dictionary
            
        Returns:
            bool: True if updated successfully
        """
        try:
            user = EmailUser.query.get(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Actualizar configuración
            if 'mail_server' in email_config:
                user.mail_server = email_config['mail_server']
            if 'mail_port' in email_config:
                user.mail_port = email_config['mail_port']
            if 'mail_use_tls' in email_config:
                user.mail_use_tls = email_config['mail_use_tls']
            if 'mail_username' in email_config:
                user.mail_username = email_config['mail_username']
            if 'mail_password' in email_config:
                user.mail_password = email_config['mail_password']
            if 'mail_default_sender' in email_config:
                user.mail_default_sender = email_config['mail_default_sender']
            if 'enable_critical_alerts' in email_config:
                user.enable_critical_alerts = email_config['enable_critical_alerts']
            if 'enable_payment_reminders' in email_config:
                user.enable_payment_reminders = email_config['enable_payment_reminders']
            if 'enable_weekly_summary' in email_config:
                user.enable_weekly_summary = email_config['enable_weekly_summary']
            if 'enable_system_alerts' in email_config:
                user.enable_system_alerts = email_config['enable_system_alerts']
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Updated email config for user: {user.email}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error updating email config for user {user_id}: {e}")
            return False
    
    def assign_projects_to_user(self, user_id: int, projects: List[Dict[str, str]]) -> bool:
        """
        Assign projects to a user.
        
        Args:
            user_id: User ID
            projects: List of project dictionaries with 'project_name' and 'project_manager'
            
        Returns:
            bool: True if assigned successfully
        """
        try:
            user = EmailUser.query.get(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Eliminar asignaciones existentes
            EmailUserProject.query.filter_by(user_id=user_id).delete()
            
            # Crear nuevas asignaciones
            for project_data in projects:
                project = EmailUserProject(
                    user_id=user_id,
                    project_name=project_data['project_name'],
                    project_manager=project_data['project_manager']
                )
                db.session.add(project)
            
            db.session.commit()
            logger.info(f"✅ Assigned {len(projects)} projects to user: {user.email}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error assigning projects to user {user_id}: {e}")
            return False
    
    def assign_clients_to_user(self, user_id: int, clients: List[str]) -> bool:
        """
        Assign clients to a user.
        
        Args:
            user_id: User ID
            clients: List of client names
            
        Returns:
            bool: True if assigned successfully
        """
        try:
            user = EmailUser.query.get(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Eliminar asignaciones existentes
            EmailUserClient.query.filter_by(user_id=user_id).delete()
            
            # Crear nuevas asignaciones
            for client_name in clients:
                client = EmailUserClient(
                    user_id=user_id,
                    client_name=client_name
                )
                db.session.add(client)
            
            db.session.commit()
            logger.info(f"✅ Assigned {len(clients)} clients to user: {user.email}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error assigning clients to user {user_id}: {e}")
            return False
    
    def get_user_by_email(self, email: str) -> Optional[EmailUser]:
        """Get user by email address."""
        return EmailUser.query.filter_by(email=email, is_active=True).first()
    
    def get_all_active_users(self) -> List[EmailUser]:
        """Get all active users."""
        return EmailUser.query.filter_by(is_active=True).all()
    
    def get_users_by_role(self, role: str) -> List[EmailUser]:
        """Get all users with a specific role."""
        return EmailUser.query.filter_by(role=role, is_active=True).all()
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user."""
        try:
            user = EmailUser.query.get(user_id)
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Deactivated user: {user.email}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error deactivating user {user_id}: {e}")
            return False
    
    def get_user_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: User summary with all related data
        """
        try:
            user = EmailUser.query.get(user_id)
            if not user:
                return {}
            
            return {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_active': user.is_active,
                'email_configured': user.is_email_configured(),
                'email_config': user.get_email_config(),
                'assigned_projects': user.get_assigned_projects(),
                'assigned_clients': user.get_assigned_clients(),
                'permissions': user.permissions,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user summary for {user_id}: {e}")
            return {}
    
    def test_user_email_config(self, user_id: int) -> Dict[str, Any]:
        """
        Test user's email configuration.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: Test results
        """
        try:
            user = EmailUser.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if not user.is_email_configured():
                return {'success': False, 'error': 'Email not configured'}
            
            # Importar EmailService para probar configuración
            from .email_service import EmailService
            
            # Crear configuración temporal para el test
            test_config = {
                'mail_server': user.mail_server,
                'mail_port': user.mail_port,
                'mail_use_tls': user.mail_use_tls,
                'mail_username': user.mail_username,
                'mail_password': user.mail_password,
                'mail_default_sender': user.mail_default_sender
            }
            
            # Crear EmailService temporal con la configuración del usuario
            email_service = EmailService()
            email_service.email_config = type('Config', (), test_config)()
            
            # Probar envío de email de prueba
            test_data = {
                "title": "Test de Configuración de Email",
                "description": "Este es un email de prueba para verificar la configuración.",
                "severity": "low",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            
            success = email_service.send_system_alert(test_data, [user.email])
            
            return {
                'success': success,
                'message': 'Email test completed',
                'user_email': user.email
            }
            
        except Exception as e:
            logger.error(f"❌ Error testing email config for user {user_id}: {e}")
            return {'success': False, 'error': str(e)} 