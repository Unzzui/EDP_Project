"""
Database Manager for Multi-Tenant Architecture.
Handles database creation and management for each tenant.
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import current_app
import logging
from typing import Optional, Dict


class TenantDatabaseManager:
    """Manages database operations for multi-tenant architecture."""
    
    def __init__(self, master_db_url: str):
        """
        Initialize the database manager.
        
        Args:
            master_db_url: URL for the master database (contains tenant info)
        """
        self.master_db_url = master_db_url
        self.logger = logging.getLogger(__name__)
        self._tenant_engines = {}  # Cache for tenant database engines
    
    def create_tenant_database(self, tenant) -> bool:
        """
        Create a new database for a tenant.
        
        Args:
            tenant: Tenant model instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Parse master DB URL to get connection info
            master_engine = create_engine(self.master_db_url)
            connection_parts = str(master_engine.url).split('/')
            base_url = '/'.join(connection_parts[:-1])
            
            # Connect to PostgreSQL server (not specific database)
            server_url = base_url + '/postgres'
            
            # Create database
            engine = create_engine(server_url, isolation_level='AUTOCOMMIT')
            with engine.connect() as conn:
                # Check if database already exists
                result = conn.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (tenant.database_name,)
                )
                
                if result.fetchone():
                    self.logger.warning(f"Database {tenant.database_name} already exists")
                    return True
                
                # Create the database
                conn.execute(f'CREATE DATABASE "{tenant.database_name}"')
                self.logger.info(f"Created database: {tenant.database_name}")
            
            # Initialize schema in the new database
            self._initialize_tenant_schema(tenant)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create database for tenant {tenant.company_name}: {e}")
            return False
    
    def _initialize_tenant_schema(self, tenant):
        """Initialize the database schema for a tenant."""
        try:
            tenant_db_url = self._get_tenant_db_url(tenant)
            engine = create_engine(tenant_db_url)
            
            # Import your models here to create tables
            from ..models import db
            from ..models.user import User
            # Add other models as needed
            
            # Create all tables
            with engine.connect() as conn:
                # Create schema if needed
                db.metadata.create_all(engine)
                
                # Create default admin user for the tenant
                self._create_default_admin_user(tenant, engine)
                
            self.logger.info(f"Initialized schema for tenant: {tenant.company_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize schema for tenant {tenant.company_name}: {e}")
            raise
    
    def _create_default_admin_user(self, tenant, engine):
        """Create a default admin user for the tenant."""
        try:
            from ..models.user import User
            
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Check if admin already exists
            existing_admin = session.query(User).filter_by(
                username='admin',
                rol='admin'
            ).first()
            
            if not existing_admin:
                admin_user = User(
                    nombre_completo=f"Admin - {tenant.company_name}",
                    username='admin',
                    password='admin123',  # Should be changed on first login
                    rol='admin',
                    email=tenant.contact_email
                )
                session.add(admin_user)
                session.commit()
                self.logger.info(f"Created admin user for tenant: {tenant.company_name}")
            
            session.close()
            
        except Exception as e:
            self.logger.error(f"Failed to create admin user for tenant {tenant.company_name}: {e}")
            raise
    
    def get_tenant_engine(self, tenant):
        """
        Get SQLAlchemy engine for a specific tenant.
        Uses caching for performance.
        """
        if tenant.id not in self._tenant_engines:
            tenant_db_url = self._get_tenant_db_url(tenant)
            engine = create_engine(
                tenant_db_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self._tenant_engines[tenant.id] = engine
        
        return self._tenant_engines[tenant.id]
    
    def _get_tenant_db_url(self, tenant) -> str:
        """Generate database URL for a specific tenant."""
        # Parse master DB URL
        master_engine = create_engine(self.master_db_url)
        url_parts = str(master_engine.url).split('/')
        base_url = '/'.join(url_parts[:-1])
        
        return f"{base_url}/{tenant.database_name}"
    
    def delete_tenant_database(self, tenant) -> bool:
        """
        Delete tenant database (use with extreme caution!).
        
        Args:
            tenant: Tenant model instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First, close any existing connections
            if tenant.id in self._tenant_engines:
                self._tenant_engines[tenant.id].dispose()
                del self._tenant_engines[tenant.id]
            
            # Connect to PostgreSQL server
            master_engine = create_engine(self.master_db_url)
            connection_parts = str(master_engine.url).split('/')
            base_url = '/'.join(connection_parts[:-1])
            server_url = base_url + '/postgres'
            
            engine = create_engine(server_url, isolation_level='AUTOCOMMIT')
            with engine.connect() as conn:
                # Terminate existing connections to the database
                conn.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{tenant.database_name}' AND pid <> pg_backend_pid()
                """)
                
                # Drop the database
                conn.execute(f'DROP DATABASE IF EXISTS "{tenant.database_name}"')
                self.logger.info(f"Deleted database: {tenant.database_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete database for tenant {tenant.company_name}: {e}")
            return False
    
    def backup_tenant_database(self, tenant, backup_path: str) -> bool:
        """
        Create a backup of tenant database.
        
        Args:
            tenant: Tenant model instance
            backup_path: Path where backup should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import subprocess
            from urllib.parse import urlparse
            
            # Parse database URL
            url = urlparse(self._get_tenant_db_url(tenant))
            
            # Construct pg_dump command
            cmd = [
                'pg_dump',
                f'--host={url.hostname}',
                f'--port={url.port or 5432}',
                f'--username={url.username}',
                f'--dbname={tenant.database_name}',
                '--verbose',
                '--no-password',  # Use .pgpass or environment variables
                f'--file={backup_path}'
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = url.password
            
            # Execute backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Backup created for tenant {tenant.company_name}: {backup_path}")
                return True
            else:
                self.logger.error(f"Backup failed for tenant {tenant.company_name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to backup database for tenant {tenant.company_name}: {e}")
            return False
    
    def get_tenant_stats(self, tenant) -> Dict[str, any]:
        """
        Get statistics for a tenant database.
        
        Args:
            tenant: Tenant model instance
            
        Returns:
            dict: Database statistics
        """
        try:
            engine = self.get_tenant_engine(tenant)
            
            with engine.connect() as conn:
                # Get basic stats
                stats = {}
                
                # Database size
                size_result = conn.execute(f"""
                    SELECT pg_size_pretty(pg_database_size('{tenant.database_name}')) as size
                """)
                stats['database_size'] = size_result.fetchone()[0]
                
                # Table count
                table_result = conn.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                stats['table_count'] = table_result.fetchone()[0]
                
                # Add more specific stats based on your models
                # Example: EDP count, User count, etc.
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for tenant {tenant.company_name}: {e}")
            return {}
    
    def migrate_tenant_database(self, tenant, migration_script: str) -> bool:
        """
        Execute migration script on tenant database.
        
        Args:
            tenant: Tenant model instance
            migration_script: SQL migration script
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            engine = self.get_tenant_engine(tenant)
            
            with engine.connect() as conn:
                # Execute migration in a transaction
                trans = conn.begin()
                try:
                    conn.execute(migration_script)
                    trans.commit()
                    self.logger.info(f"Migration completed for tenant: {tenant.company_name}")
                    return True
                except Exception as e:
                    trans.rollback()
                    self.logger.error(f"Migration failed for tenant {tenant.company_name}: {e}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to migrate database for tenant {tenant.company_name}: {e}")
            return False
