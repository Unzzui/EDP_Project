"""
Tenant Context Manager for handling multi-tenancy in Flask.
This middleware manages tenant identification and database switching.
"""
from flask import g, request, abort, current_app
from functools import wraps
from typing import Optional
import re


class TenantContext:
    """Manages tenant context throughout the request lifecycle."""
    
    def __init__(self, app=None):
        self.app = app if app else current_app
        self.tenant_db_manager = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the tenant context with Flask app."""
        self.app = app
        
        # Initialize database manager
        from .tenant_database_manager import TenantDatabaseManager
        master_db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        self.tenant_db_manager = TenantDatabaseManager(master_db_url)
        
        # Register request handlers
        app.before_request(self.before_request)
        app.teardown_request(self.teardown_request)
        
        # Store instance in app
        app.tenant_context = self
    
    def before_request(self):
        """
        Called before each request to identify and set tenant context.
        Tenant can be identified by:
        1. Subdomain (preferred): tenant.pagora.com
        2. API Key header: X-Tenant-API-Key
        3. URL path: /tenant/company-slug/
        """
        tenant = None
        
        # Method 1: Subdomain-based tenant identification
        tenant = self._identify_by_subdomain()
        
        # Method 2: API Key (for API requests)
        if not tenant:
            tenant = self._identify_by_api_key()
        
        # Method 3: URL path (fallback)
        if not tenant:
            tenant = self._identify_by_path()
        
        # Store tenant in request context
        g.current_tenant = tenant
        
        # Skip tenant requirement for certain routes
        if self._is_tenant_exempt_route():
            return
        
        # Require tenant for protected routes
        if not tenant and self._requires_tenant():
            abort(404, description="Tenant not found")
        
        # Set up tenant database connection
        if tenant:
            self._setup_tenant_database(tenant)
    
    def teardown_request(self, exception=None):
        """Clean up tenant context after request."""
        # Clean up any tenant-specific resources
        if hasattr(g, 'tenant_db_session'):
            g.tenant_db_session.close()
    
    def _identify_by_subdomain(self) -> Optional['Tenant']:
        """Identify tenant by subdomain."""
        try:
            host = request.host.lower()
            
            # Skip if localhost or IP
            if 'localhost' in host or self._is_ip_address(host):
                return None
            
            # Extract subdomain
            parts = host.split('.')
            if len(parts) >= 3:  # subdomain.domain.com
                subdomain = parts[0]
                
                # Skip www
                if subdomain == 'www':
                    return None
                
                return self._get_tenant_by_slug(subdomain)
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error identifying tenant by subdomain: {e}")
            return None
    
    def _identify_by_api_key(self) -> Optional['Tenant']:
        """Identify tenant by API key header."""
        try:
            api_key = request.headers.get('X-Tenant-API-Key')
            if not api_key:
                return None
            
            from ..models.tenant import Tenant
            return Tenant.query.filter_by(
                api_key=api_key,
                is_active=True
            ).first()
            
        except Exception as e:
            current_app.logger.error(f"Error identifying tenant by API key: {e}")
            return None
    
    def _identify_by_path(self) -> Optional['Tenant']:
        """Identify tenant by URL path."""
        try:
            path = request.path
            
            # Look for pattern: /tenant/{slug}/...
            match = re.match(r'^/tenant/([^/]+)/', path)
            if match:
                tenant_slug = match.group(1)
                return self._get_tenant_by_slug(tenant_slug)
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error identifying tenant by path: {e}")
            return None
    
    def _get_tenant_by_slug(self, slug: str) -> Optional['Tenant']:
        """Get tenant by slug."""
        try:
            from ..models.tenant import Tenant
            return Tenant.query.filter_by(
                company_slug=slug,
                is_active=True
            ).first()
            
        except Exception as e:
            current_app.logger.error(f"Error getting tenant by slug {slug}: {e}")
            return None
    
    def _is_ip_address(self, host: str) -> bool:
        """Check if host is an IP address."""
        import re
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(ip_pattern, host.split(':')[0]))
    
    def _is_tenant_exempt_route(self) -> bool:
        """Check if current route is exempt from tenant requirement."""
        exempt_routes = [
            '/',  # Landing page
            '/health',
            '/api/health',
            '/auth/login',
            '/auth/register',
            '/auth/logout',
            '/api/auth/',
            '/static/',
            '/favicon.ico',
            '/api/tenant/create',  # Tenant creation endpoint
            '/api/contact',  # Contact form
            '/api/access-request',  # Access request
        ]
        
        path = request.path
        return any(path.startswith(route) for route in exempt_routes)
    
    def _requires_tenant(self) -> bool:
        """Check if current route requires a tenant."""
        # Most routes require tenant except landing and auth
        return not self._is_tenant_exempt_route()
    
    def _setup_tenant_database(self, tenant):
        """Set up database connection for the tenant."""
        try:
            # Get tenant-specific database engine
            engine = self.tenant_db_manager.get_tenant_engine(tenant)
            
            # Create session for this tenant
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            g.tenant_db_session = Session()
            
            # Store engine for direct access if needed
            g.tenant_db_engine = engine
            
        except Exception as e:
            current_app.logger.error(f"Failed to setup tenant database for {tenant.company_name}: {e}")
            abort(500, description="Database connection failed")
    
    @staticmethod
    def get_current_tenant():
        """Get the current tenant from request context."""
        return getattr(g, 'current_tenant', None)
    
    @staticmethod
    def get_tenant_db_session():
        """Get the current tenant database session."""
        return getattr(g, 'tenant_db_session', None)
    
    @staticmethod
    def get_tenant_db_engine():
        """Get the current tenant database engine."""
        return getattr(g, 'tenant_db_engine', None)


def require_tenant(f):
    """Decorator to require tenant context for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            abort(404, description="Tenant not found")
        return f(*args, **kwargs)
    return decorated_function


def tenant_admin_required(f):
    """Decorator to require tenant admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            abort(404, description="Tenant not found")
        
        # Check if user is admin for this tenant
        if not current_user.is_authenticated:
            abort(401, description="Authentication required")
        
        # Check if user has admin role in this tenant
        from ..models.tenant import TenantUser
        tenant_user = TenantUser.query.filter_by(
            tenant_id=tenant.id,
            user_id=current_user.id
        ).first()
        
        if not tenant_user or (not current_user.is_admin and not tenant_user.is_owner):
            abort(403, description="Tenant admin privileges required")
        
        return f(*args, **kwargs)
    return decorated_function


def api_key_auth(f):
    """Decorator for API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            abort(401, description="Invalid API key")
        return f(*args, **kwargs)
    return decorated_function
