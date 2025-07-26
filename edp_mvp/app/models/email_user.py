"""
Email User Model for role-based email permissions.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..extensions import db

class EmailUser(db.Model):
    """Email user with role-based permissions."""
    
    __tablename__ = 'email_users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='project_manager')  # executive, manager, project_manager, controller, finance, client
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    assigned_projects = relationship('EmailUserProject', back_populates='user', cascade='all, delete-orphan')
    assigned_clients = relationship('EmailUserClient', back_populates='user', cascade='all, delete-orphan')
    email_preferences = relationship('EmailUserPreference', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EmailUser {self.email} ({self.role})>'
    
    @property
    def permissions(self):
        """Get user permissions based on role."""
        from ..services.email_permissions_service import EmailRole, EmailPermission
        
        role_permissions = {
            'executive': [
                'all_data', 'critical_alerts', 'weekly_summary', 
                'financial_data', 'operational_data'
            ],
            'manager': [
                'all_data', 'critical_alerts', 'weekly_summary', 
                'financial_data', 'operational_data'
            ],
            'project_manager': [
                'project_data', 'critical_alerts', 'weekly_summary'
            ],
            'controller': [
                'all_data', 'critical_alerts', 'weekly_summary', 
                'operational_data', 'payment_reminders'
            ],
            'finance': [
                'financial_data', 'critical_alerts', 'weekly_summary', 
                'payment_reminders'
            ],
            'client': [
                'client_data', 'payment_reminders'
            ]
        }
        
        return role_permissions.get(self.role, [])
    
    def can_access(self, permission: str) -> bool:
        """Check if user can access specific permission."""
        return permission in self.permissions
    
    def get_assigned_projects(self) -> list:
        """Get list of assigned project names."""
        return [ap.project_name for ap in self.assigned_projects if ap.is_active]
    
    def get_assigned_clients(self) -> list:
        """Get list of assigned client names."""
        return [ac.client_name for ac in self.assigned_clients if ac.is_active]

class EmailUserProject(db.Model):
    """Association table for email users and their assigned projects."""
    
    __tablename__ = 'email_user_projects'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('email_users.id'), nullable=False)
    project_name = Column(String(255), nullable=False)  # Nombre del proyecto (ej: "OT2467")
    project_manager = Column(String(255), nullable=False)  # Nombre del jefe de proyecto
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    user = relationship('EmailUser', back_populates='assigned_projects')
    
    def __repr__(self):
        return f'<EmailUserProject {self.user.email} -> {self.project_name}>'

class EmailUserClient(db.Model):
    """Association table for email users and their assigned clients."""
    
    __tablename__ = 'email_user_clients'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('email_users.id'), nullable=False)
    client_name = Column(String(255), nullable=False)  # Nombre del cliente
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    user = relationship('EmailUser', back_populates='assigned_clients')
    
    def __repr__(self):
        return f'<EmailUserClient {self.user.email} -> {self.client_name}>'

class EmailUserPreference(db.Model):
    """Email preferences for users."""
    
    __tablename__ = 'email_user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('email_users.id'), nullable=False, unique=True)
    
    # Preferencias de email
    receive_weekly_summary = Column(Boolean, default=True)
    receive_critical_alerts = Column(Boolean, default=True)
    receive_payment_reminders = Column(Boolean, default=True)
    receive_system_alerts = Column(Boolean, default=True)
    receive_performance_reports = Column(Boolean, default=True)
    
    # Frecuencia de emails
    weekly_summary_frequency = Column(String(20), default='weekly')  # daily, weekly, monthly
    critical_alerts_frequency = Column(String(20), default='immediate')  # immediate, daily, weekly
    
    # Horarios preferidos
    preferred_send_time = Column(String(10), default='09:00')  # HH:MM format
    timezone = Column(String(50), default='America/Santiago')
    
    # Configuración adicional
    email_format = Column(String(20), default='html')  # html, text, both
    language = Column(String(10), default='es')  # es, en
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación
    user = relationship('EmailUser', back_populates='email_preferences')
    
    def __repr__(self):
        return f'<EmailUserPreference {self.user.email}>'
    
    @property
    def active_preferences(self) -> dict:
        """Get active email preferences."""
        return {
            'weekly_summary': self.receive_weekly_summary,
            'critical_alerts': self.receive_critical_alerts,
            'payment_reminders': self.receive_payment_reminders,
            'system_alerts': self.receive_system_alerts,
            'performance_reports': self.receive_performance_reports
        } 