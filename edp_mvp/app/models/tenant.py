"""
Tenant (Company) model for multi-tenancy support.
"""
from flask_login import UserMixin
from datetime import datetime
from ..extensions import db
import secrets
import string


class Tenant(db.Model):
    """Tenant/Company model for multi-tenancy."""
    
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False, index=True)
    company_slug = db.Column(db.String(50), unique=True, nullable=False, index=True)  # URL-friendly identifier
    database_name = db.Column(db.String(100), unique=True, nullable=False)  # Specific DB name
    
    # Contact Information
    contact_email = db.Column(db.String(255), nullable=False, index=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    contact_name = db.Column(db.String(100), nullable=False)
    
    # Subscription Information
    plan_type = db.Column(db.String(50), nullable=False, default='starter')  # starter, professional, enterprise
    max_users = db.Column(db.Integer, nullable=False, default=2)
    max_edps_monthly = db.Column(db.Integer, nullable=False, default=100)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_trial = db.Column(db.Boolean, default=True, nullable=False)
    trial_ends_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Database Configuration
    db_host = db.Column(db.String(255), default='localhost')
    db_port = db.Column(db.Integer, default=5432)
    
    # API Key for tenant
    api_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    def __init__(self, company_name, contact_email, contact_name, plan_type='starter', **kwargs):
        self.company_name = company_name
        self.contact_email = contact_email
        self.contact_name = contact_name
        self.plan_type = plan_type
        
        # Generate URL-friendly slug
        self.company_slug = self._generate_slug(company_name)
        
        # Generate unique database name
        self.database_name = f"pagora_{self.company_slug}_{secrets.token_hex(8)}"
        
        # Generate API key
        self.api_key = self._generate_api_key()
        
        # Set plan limits
        self._set_plan_limits(plan_type)
        
        # Set trial period (30 days)
        from datetime import timedelta
        self.trial_ends_at = datetime.utcnow() + timedelta(days=30)
        
        # Set other attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _generate_slug(self, company_name):
        """Generate URL-friendly slug from company name."""
        import re
        slug = re.sub(r'[^\w\s-]', '', company_name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:50]  # Limit length
    
    def _generate_api_key(self):
        """Generate secure API key."""
        return secrets.token_urlsafe(48)
    
    def _set_plan_limits(self, plan_type):
        """Set limits based on plan type."""
        plan_configs = {
            'starter': {
                'max_users': 2,
                'max_edps_monthly': 100
            },
            'professional': {
                'max_users': 10,
                'max_edps_monthly': 500
            },
            'enterprise': {
                'max_users': -1,  # Unlimited
                'max_edps_monthly': -1  # Unlimited
            }
        }
        
        config = plan_configs.get(plan_type, plan_configs['starter'])
        self.max_users = config['max_users']
        self.max_edps_monthly = config['max_edps_monthly']
    
    @property
    def is_trial_expired(self):
        """Check if trial period has expired."""
        if not self.is_trial or not self.trial_ends_at:
            return False
        return datetime.utcnow() > self.trial_ends_at
    
    @property
    def days_left_in_trial(self):
        """Get days left in trial."""
        if not self.is_trial or not self.trial_ends_at:
            return 0
        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)
    
    def get_database_url(self, base_url="postgresql://user:pass@localhost"):
        """Get database URL for this tenant."""
        return f"{base_url}/{self.database_name}"
    
    def upgrade_plan(self, new_plan_type):
        """Upgrade tenant to new plan."""
        self.plan_type = new_plan_type
        self._set_plan_limits(new_plan_type)
        self.updated_at = datetime.utcnow()
    
    def activate_subscription(self):
        """Activate paid subscription (end trial)."""
        self.is_trial = False
        self.trial_ends_at = None
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate tenant."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'company_slug': self.company_slug,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'contact_name': self.contact_name,
            'plan_type': self.plan_type,
            'max_users': self.max_users,
            'max_edps_monthly': self.max_edps_monthly,
            'is_active': self.is_active,
            'is_trial': self.is_trial,
            'days_left_in_trial': self.days_left_in_trial,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Tenant {self.company_name} ({self.company_slug})>'


class TenantUser(db.Model):
    """Association between tenants and users."""
    
    __tablename__ = 'tenant_users'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    is_owner = db.Column(db.Boolean, default=False, nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='tenant_users')
    user = db.relationship('User', backref='tenant_associations')
    
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'user_id', name='unique_tenant_user'),
    )
    
    def __repr__(self):
        return f'<TenantUser tenant_id={self.tenant_id} user_id={self.user_id}>'
