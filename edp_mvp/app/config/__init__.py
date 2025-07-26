"""
Configuration management for the EDP application.
"""
import os
import json
import tempfile
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variables de entorno cargadas desde .env")
except ImportError:
    print("⚠️ python-dotenv no instalado, usando variables de entorno del sistema")

@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    # Supabase (anteriormente Google Sheets) configuration (for EDP data)
    credentials_file: str = "credentials.json"
    sheet_id: str = ""
    timeout: int = 30
    retry_attempts: int = 3
    
    # SQLite configuration (for users and auth)
    sqlite_db_path: str = ""
    sqlalchemy_database_uri: str = ""
    sqlalchemy_track_modifications: bool = False
    
    # Supabase configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    
    # NUEVO: Selector de backend de datos
    database_type: str = "supabase"  # Cambiado de "sqlite" a "supabase"
    data_backend: str = "supabase"   # NUEVO: "google_sheets" o "supabase"
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create DatabaseConfig from environment variables."""
        
        # Obtener tipo de base de datos desde variables de entorno
        database_type = os.getenv('DATABASE_TYPE', 'supabase')  # Cambio por defecto
        data_backend = os.getenv('DATA_BACKEND', 'supabase')    # NUEVO: backend de datos
        
        # SQLite configuration
        instance_dir = os.getenv('INSTANCE_PATH', 'edp_mvp/instance')
        sqlite_filename = os.getenv('SQLITE_DB_NAME', 'edp_mvp.db')
        sqlite_path = os.path.join(instance_dir, sqlite_filename)
        
        # Configurar URI de SQLAlchemy basado en el tipo de DB
        if database_type == 'postgresql':
            # PostgreSQL/Supabase para producción
            database_url = os.getenv('DATABASE_URL')
            if database_url and database_url.startswith('postgres://'):
                # Render/Heroku compatibility: replace postgres:// with postgresql://
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            sqlalchemy_uri = database_url or 'postgresql://localhost/edp_mvp'
        else:
            # SQLite por defecto
            sqlalchemy_uri = f'sqlite:///{sqlite_path}'
        
        # Supabase configuration
        supabase_url = os.getenv('SUPABASE_URL', '')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY', '')
        supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        
        print(f"🔧 Configuración de datos:")
        print(f"   📊 Backend de datos: {data_backend}")
        print(f"   🗄️ Base de datos: {database_type}")
        print(f"   🔗 Supabase: {'✅ Configurado' if supabase_url else '❌ No configurado'}")
        
        return cls(
            credentials_file=os.getenv('GOOGLE_CREDENTIALS_FILE', 'edp_mvp/app/keys/edp-control-system.json'),
            # Usar SHEET_ID que tienes en tu .env
            sheet_id=os.getenv('SHEET_ID', os.getenv('GOOGLE_SHEET_ID', '')),
            timeout=int(os.getenv('DB_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('DB_RETRY_ATTEMPTS', '3')),
            # SQLite config
            sqlite_db_path=sqlite_path,
            sqlalchemy_database_uri=sqlalchemy_uri,
            sqlalchemy_track_modifications=os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true',
            # Supabase config
            supabase_url=supabase_url,
            supabase_anon_key=supabase_anon_key,
            supabase_service_role_key=supabase_service_role_key,
            database_type=database_type,
            data_backend=data_backend  # NUEVO
        )

@dataclass
class AppConfig:
    """Application configuration."""
    
    # Basic app settings
    debug: bool = False
    testing: bool = False
    environment: str = "development"
    secret_key: str = "dev-secret-key"
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 5000
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "app.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Pagination settings
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Cache settings
    cache_timeout: int = 30  # 30 seconds default for faster refresh
    
    # File upload settings
    max_upload_size: int = 16 * 1024 * 1024  # 16MB
    allowed_extensions: tuple = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt', '.jpg', '.png')
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create config from environment variables."""
        return cls(
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            testing=os.getenv('TESTING', 'False').lower() == 'true',
            environment=os.getenv('ENVIRONMENT', 'development'),
            secret_key=os.getenv('SECRET_KEY', 'dev-secret-key'),
            host=os.getenv('HOST', '127.0.0.1'),
            port=int(os.getenv('PORT', '5000')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', 'app.log'),
            default_page_size=int(os.getenv('DEFAULT_PAGE_SIZE', '20')),
            max_page_size=int(os.getenv('MAX_PAGE_SIZE', '100')),
            cache_timeout=int(os.getenv('CACHE_TIMEOUT', '30')),
            max_upload_size=int(os.getenv('MAX_UPLOAD_SIZE', str(16 * 1024 * 1024)))
        )


@dataclass
class SecurityConfig:
    """Security configuration."""
    
    # Session settings
    session_timeout: int = 3600  # 1 hour
    csrf_protection: bool = True
    
    # Password settings
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Create config from environment variables."""
        return cls(
            session_timeout=int(os.getenv('SESSION_TIMEOUT', '3600')),
            csrf_protection=os.getenv('CSRF_PROTECTION', 'True').lower() == 'true',
            min_password_length=int(os.getenv('MIN_PASSWORD_LENGTH', '8')),
            require_uppercase=os.getenv('REQUIRE_UPPERCASE', 'True').lower() == 'true',
            require_lowercase=os.getenv('REQUIRE_LOWERCASE', 'True').lower() == 'true',
            require_numbers=os.getenv('REQUIRE_NUMBERS', 'True').lower() == 'true',
            require_special_chars=os.getenv('REQUIRE_SPECIAL_CHARS', 'True').lower() == 'true',
            rate_limit_enabled=os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true',
            rate_limit_requests=int(os.getenv('RATE_LIMIT_REQUESTS', '100')),
            rate_limit_window=int(os.getenv('RATE_LIMIT_WINDOW', '3600'))
        )


@dataclass
class EmailConfig:
    """Email configuration for notifications."""
    
    # SMTP settings
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587
    mail_use_tls: bool = True
    mail_use_ssl: bool = False
    mail_username: str = ""
    mail_password: str = ""
    
    # Email settings
    mail_default_sender: str = ""
    mail_max_emails: int = 100
    
    # Test email settings
    test_email_recipient: str = "diegobravobe@gmail.com"
    
    # Notification settings
    enable_critical_alerts: bool = True
    enable_weekly_summary: bool = True
    enable_payment_reminders: bool = True
    enable_system_alerts: bool = True
    
    # Alert thresholds
    critical_edp_days: int = 60
    payment_reminder_days: int = 30
    weekly_summary_day: str = "monday"  # day of week
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Create EmailConfig from environment variables."""
        return cls(
            mail_server=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
            mail_port=int(os.getenv('MAIL_PORT', '587')),
            mail_use_tls=os.getenv('MAIL_USE_TLS', 'True').lower() == 'true',
            mail_use_ssl=os.getenv('MAIL_USE_SSL', 'False').lower() == 'true',
            mail_username=os.getenv('MAIL_USERNAME', ''),
            mail_password=os.getenv('MAIL_PASSWORD', ''),
            mail_default_sender=os.getenv('MAIL_DEFAULT_SENDER', ''),
            mail_max_emails=int(os.getenv('MAIL_MAX_EMAILS', '100')),
            test_email_recipient=os.getenv('TEST_EMAIL_RECIPIENT', 'diegobravobe@gmail.com'),
            enable_critical_alerts=os.getenv('ENABLE_CRITICAL_ALERTS', 'True').lower() == 'true',
            enable_weekly_summary=os.getenv('ENABLE_WEEKLY_SUMMARY', 'True').lower() == 'true',
            enable_payment_reminders=os.getenv('ENABLE_PAYMENT_REMINDERS', 'True').lower() == 'true',
            enable_system_alerts=os.getenv('ENABLE_SYSTEM_ALERTS', 'True').lower() == 'true',
            critical_edp_days=int(os.getenv('CRITICAL_EDP_DAYS', '60')),
            payment_reminder_days=int(os.getenv('PAYMENT_REMINDER_DAYS', '30')),
            weekly_summary_day=os.getenv('WEEKLY_SUMMARY_DAY', 'monday')
        )


@dataclass
class KPIConfig:
    """KPI calculation configuration."""
    
    # Health score thresholds
    excellent_threshold: float = 90.0
    good_threshold: float = 70.0
    fair_threshold: float = 50.0
    
    # Risk calculation weights
    overdue_weight: float = 0.4
    status_weight: float = 0.3
    update_frequency_weight: float = 0.2
    priority_weight: float = 0.1
    
    # Alert thresholds
    overdue_alert_days: int = 1
    stale_alert_days: int = 30
    low_health_threshold: float = 50.0
    
    # Calculation intervals
    kpi_update_frequency: int = 3600  # 1 hour in seconds
    trend_data_retention_days: int = 90
    
    @classmethod
    def from_env(cls) -> 'KPIConfig':
        """Create config from environment variables."""
        return cls(
            excellent_threshold=float(os.getenv('EXCELLENT_THRESHOLD', '90.0')),
            good_threshold=float(os.getenv('GOOD_THRESHOLD', '70.0')),
            fair_threshold=float(os.getenv('FAIR_THRESHOLD', '50.0')),
            overdue_weight=float(os.getenv('OVERDUE_WEIGHT', '0.4')),
            status_weight=float(os.getenv('STATUS_WEIGHT', '0.3')),
            update_frequency_weight=float(os.getenv('UPDATE_FREQUENCY_WEIGHT', '0.2')),
            priority_weight=float(os.getenv('PRIORITY_WEIGHT', '0.1')),
            overdue_alert_days=int(os.getenv('OVERDUE_ALERT_DAYS', '1')),
            stale_alert_days=int(os.getenv('STALE_ALERT_DAYS', '30')),
            low_health_threshold=float(os.getenv('LOW_HEALTH_THRESHOLD', '50.0')),
            kpi_update_frequency=int(os.getenv('KPI_UPDATE_FREQUENCY', '3600')),
            trend_data_retention_days=int(os.getenv('TREND_DATA_RETENTION_DAYS', '90'))
        )


class Config:
    """Main configuration class that combines all configs."""
    
    def __init__(self):
        self.app = AppConfig.from_env()
        self.database = DatabaseConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.email = EmailConfig.from_env()
        self.kpi = KPIConfig.from_env()
        
        # NUEVO: Configurar backend de datos
        self.DATA_BACKEND = self.database.data_backend
        
        # Add compatibility attributes for legacy code
        if self.DATA_BACKEND == "google_sheets":
            print("📊 Usando Google Sheets como backend de datos")
            # SOLO usar variables de entorno - no archivos JSON
            self.GOOGLE_CREDENTIALS = "ENV_VARS"  # Siempre usar variables de entorno
            # Usar SHEET_ID de tu .env
            self.SHEET_ID = os.getenv('SHEET_ID', os.getenv('GOOGLE_SHEET_ID', ''))
            
            # Configurar servicio de Google Sheets desde aquí
            self.GOOGLE_SERVICE = self._setup_google_service()
        else:
            print("🗄️ Usando Supabase como backend de datos")
            self.GOOGLE_SERVICE = None
            self.SHEET_ID = ""
        
        self.SECRET_KEY = self.app.secret_key
        self.DEBUG = self.app.debug
        self.FLASK_ENV = self.app.environment
        
        # SQLAlchemy configuration for Flask
        self.SQLALCHEMY_DATABASE_URI = self.database.sqlalchemy_database_uri
        self.SQLALCHEMY_TRACK_MODIFICATIONS = self.database.sqlalchemy_track_modifications
        
        # Set environment-specific overrides
        if self.app.environment == 'production':
            self._apply_production_overrides()
        elif self.app.environment == 'testing':
            self._apply_testing_overrides()
    
    def _apply_production_overrides(self):
        """Apply production-specific settings."""
        self.app.debug = False
        self.app.testing = False
        self.app.log_level = "WARNING"
        
        # Stricter security in production
        self.security.csrf_protection = True
        self.security.rate_limit_enabled = True
        
        # More conservative timeouts
        self.database.timeout = 60
        self.database.retry_attempts = 5
        
    def _apply_testing_overrides(self):
        """Apply testing-specific settings."""
        self.app.testing = True
        self.app.debug = True
        self.app.log_level = "DEBUG"
        
        # Relaxed security for testing 
        self.security.csrf_protection = False
        self.security.rate_limit_enabled = False
        
        # Faster timeouts for tests
        self.database.timeout = 10
        self.database.retry_attempts = 1
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration from various sources."""
        redis_url = None
        
        # Try different environment variable names in order of preference
        redis_env_vars = ['REDIS_URL', 'REDISCLOUD_URL', 'REDISTOGO_URL']
        
        for var in redis_env_vars:
            redis_url = os.getenv(var)
            if redis_url:
                print(f"✅ Redis configurado desde {var}")
                break
        
        if not redis_url:
            # Try localhost default for development
            redis_url = "redis://localhost:6379/0"
            print("⚠️ Redis no configurado, usando localhost por defecto")
        
        return {
            'url': redis_url,
            'decode_responses': True,
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
            'health_check_interval': 30
        }
    
    def is_google_sheets_enabled(self) -> bool:
        """Supabase integration (migrated from Google Sheets)"""
        return (
            self.DATA_BACKEND == "google_sheets" and
            self.GOOGLE_SERVICE is not None and 
            bool(self.SHEET_ID)
        )
    
    def is_supabase_enabled(self) -> bool:
        """Check if Supabase integration is enabled and properly configured."""
        return (
            self.DATA_BACKEND == "supabase" and
            bool(self.database.supabase_url) and 
            bool(self.database.supabase_service_role_key)
        )
    
    def _setup_google_service(self):
        """
        Configurar servicio de Google Sheets usando archivo JSON.
        Simplificado para usar únicamente el archivo JSON en app/keys/
        
        Returns:
            Google Sheets service object o None si no se puede configurar
        """
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            import json
            
            print("🔑 Configurando servicio de Google Sheets...")
            
            # Usar archivo JSON directamente
            credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'edp_mvp/app/keys/edp-control-system.json')
            
            # Construir ruta absoluta
            if not os.path.isabs(credentials_file):
                # Si es relativa, usar la ruta del proyecto
                project_root = Path(__file__).parent.parent.parent.parent
                json_path = project_root / credentials_file
            else:
                json_path = Path(credentials_file)
            
            print(f"   📁 Buscando credenciales en: {json_path}")
            
            if not json_path.exists():
                print(f"   ❌ Archivo JSON no encontrado: {json_path}")
                print("🎭 Activando modo demo (sin Google Sheets)")
                return None
            
            print(f"   ✅ Archivo JSON encontrado: {json_path}")
            
            # Cargar credenciales desde JSON
            with open(json_path, 'r') as f:
                credentials_data = json.load(f)
            
            # Verificar que el JSON tiene los campos necesarios
            required_fields = ['project_id', 'client_email', 'private_key']
            missing_fields = [field for field in required_fields if field not in credentials_data]
            
            if missing_fields:
                print(f"   ❌ Archivo JSON incompleto. Campos faltantes: {missing_fields}")
                print("🎭 Activando modo demo")
                return None
            
            print(f"   📧 Client Email: {credentials_data['client_email']}")
            print(f"   🆔 Project ID: {credentials_data['project_id']}")
            print("   ✅ Archivo JSON válido")
            
            # Crear credenciales y servicio
            print("   🔧 Creando credenciales de Google...")
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_info(credentials_data, scopes=scopes)
            
            print("   🔧 Construyendo servicio de Google Sheets...")
            service = build('sheets', 'v4', credentials=creds)
            
            print("✅ Servicio de Google Sheets configurado exitosamente")
            return service
            
        except Exception as e:
            print(f"❌ Error configurando servicio de Google Sheets: {e}")
            print(f"🔍 Tipo de error: {type(e).__name__}")
            
            print("🔧 Posibles soluciones:")
            print("   1. Verifica el archivo JSON en app/keys/")
            print("   2. Regenera las credenciales de Google Cloud")
            print("   3. Verifica permisos del archivo JSON")
            
            print("🎭 Activando modo demo")
            return None
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration settings."""
        issues = []
        warnings = []
        
        # Check required settings
        if not self.database.sheet_id:
            issues.append("Google Sheet ID is not configured")
        
        if self.app.secret_key == "dev-secret-key" and self.app.environment == "production":
            issues.append("Secret key should be changed in production")
        
        # Check file paths
        creds_path = Path(self.database.credentials_file)
        if not creds_path.exists():
            warnings.append(f"Credentials file not found: {self.database.credentials_file}")
        
        # Check numeric values
        if self.app.port < 1 or self.app.port > 65535:
            issues.append("Invalid port number")
        
        if self.kpi.excellent_threshold <= self.kpi.good_threshold:
            issues.append("KPI thresholds are not properly ordered")
        
        # Security checks
        if not self.security.csrf_protection and self.app.environment == "production":
            warnings.append("CSRF protection is disabled in production")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    



# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def reload_config():
    """Reload configuration from environment."""
    global config
    config = Config()
    return config


# Environment-specific config loaders
def load_development_config() -> Config:
    """Load development configuration."""
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['DEBUG'] = 'true'
    return reload_config()


def load_production_config() -> Config:
    """Load production configuration."""
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['DEBUG'] = 'false'
    return reload_config()


def load_testing_config() -> Config:
    """Load testing configuration."""
    os.environ['ENVIRONMENT'] = 'testing'
    os.environ['TESTING'] = 'true'
    return reload_config()