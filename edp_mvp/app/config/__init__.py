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
    
    # Google Sheets configuration (for EDP data)
    credentials_file: str = "credentials.json"
    sheet_id: str = ""
    timeout: int = 30
    retry_attempts: int = 3
    
    # SQLite configuration (for users and auth)
    sqlite_db_path: str = ""
    sqlalchemy_database_uri: str = ""
    sqlalchemy_track_modifications: bool = False
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables."""
        # Default SQLite database path
        base_dir = Path(__file__).parent.parent.parent.parent  # Go to project root
        default_db_path = str(base_dir / "edp_mvp" / "instance" / "edp_database.db")
        
        sqlite_path = os.getenv('SQLITE_DB_PATH', default_db_path)
        
        # Fix DATABASE_URL handling for production
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url != "":
            print(f"🔍 DATABASE_URL detectado: {database_url[:50]}...")
            
            # Detectar placeholders comunes en DATABASE_URL
            placeholders = ['username', 'password', 'hostname', 'port', 'database', 'host']
            has_placeholder = any(placeholder in database_url.lower() for placeholder in placeholders)
            
            if has_placeholder:
                print(f"⚠️ DATABASE_URL contiene placeholders, usando SQLite")
                sqlalchemy_uri = f"sqlite:///{sqlite_path}"
            else:
                # Fix for PostgreSQL URLs that start with postgres:// (Render uses this)
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
                sqlalchemy_uri = database_url
                print(f"✅ Usando PostgreSQL validado")
        else:
            sqlalchemy_uri = f"sqlite:///{sqlite_path}"
            print(f"⚠️ DATABASE_URL no configurado, usando SQLite: {sqlite_path}")
        
        return cls(
            credentials_file="",  # No usar archivos JSON
            # Usar SHEET_ID que tienes en tu .env
            sheet_id=os.getenv('SHEET_ID', os.getenv('GOOGLE_SHEET_ID', '')),
            timeout=int(os.getenv('DB_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('DB_RETRY_ATTEMPTS', '3')),
            # SQLite config
            sqlite_db_path=sqlite_path,
            sqlalchemy_database_uri=sqlalchemy_uri,
            sqlalchemy_track_modifications=os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true'
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
        self.kpi = KPIConfig.from_env()
        
        # Add compatibility attributes for legacy code
        # SOLO usar variables de entorno - no archivos JSON
        self.GOOGLE_CREDENTIALS = "ENV_VARS"  # Siempre usar variables de entorno
        # Usar SHEET_ID de tu .env
        self.SHEET_ID = os.getenv('SHEET_ID', os.getenv('GOOGLE_SHEET_ID', ''))
        
        # Configurar servicio de Google Sheets desde aquí
        self.GOOGLE_SERVICE = self._setup_google_service()
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
        self.app.debug = True
        self.app.testing = True
        self.app.log_level = "DEBUG"
        
        # Relaxed settings for testing
        self.security.csrf_protection = False
        self.security.rate_limit_enabled = False
        
        # Faster timeouts for tests
        self.database.timeout = 10
        self.cache_timeout = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all configurations to dictionary."""
        return {
            'app': self.app.__dict__,
            'database': self.database.__dict__,
            'security': self.security.__dict__,
            'kpi': self.kpi.__dict__
        }
    
    def get_app_info(self) -> Dict[str, Any]:
        """Get basic app information."""
        return {
            'environment': self.app.environment,
            'debug': self.app.debug,
            'version': self.get_version(),
            'config_loaded_at': self._config_loaded_at.isoformat() if hasattr(self, '_config_loaded_at') else None
        }
    
    def get_version(self) -> str:
        """Get application version."""
        try:
            # Try to read from version file
            version_file = Path(__file__).parent.parent / 'version.txt'
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass
        
        return "1.0.0"  # Default version
    
    def _setup_google_service(self):
        """
        Configurar servicio de Google Sheets usando variables de entorno o archivo JSON.
        Centraliza toda la lógica de autenticación en la configuración.
        
        Returns:
            Google Sheets service object o None si no se puede configurar
        """
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            import json
            
            # 1. Cargar variables de entorno
            print("🔑 Configurando servicio de Google Sheets...")
            google_project_id = os.getenv('GOOGLE_PROJECT_ID')
            google_client_email = os.getenv('GOOGLE_CLIENT_EMAIL')
            google_private_key = os.getenv('GOOGLE_PRIVATE_KEY')
            google_key_id = os.getenv('GOOGLE_PRIVATE_KEY_ID', 'auto-generated-from-env')
            google_client_id = os.getenv('GOOGLE_CLIENT_ID', 'auto-generated-from-env')
            
            print(f"   📧 Client Email: {google_client_email}")
            print(f"   🆔 Project ID: {google_project_id}")
            print(f"   🔐 Private Key ID: {google_key_id}")
            print(f"   👤 Client ID: {google_client_id}")
            
            # 2. Verificar si tenemos todas las variables de entorno
            env_vars_complete = all([google_project_id, google_client_email, google_private_key])
            
            if env_vars_complete:
                print(f"   🔍 Private Key Length: {len(google_private_key)} caracteres")
                
                # Si la clave privada es muy corta, probablemente está truncada
                if len(google_private_key) < 100:
                    print(f"   ⚠️ Clave privada parece estar truncada ({len(google_private_key)} chars)")
                    print("   🔄 Intentando cargar desde archivo JSON...")
                    env_vars_complete = False
                else:
                    print("   ✅ Variables de entorno parecen completas")
            else:
                missing_vars = []
                if not google_project_id:
                    missing_vars.append('GOOGLE_PROJECT_ID')
                if not google_client_email:
                    missing_vars.append('GOOGLE_CLIENT_EMAIL')
                if not google_private_key:
                    missing_vars.append('GOOGLE_PRIVATE_KEY')
                
                print(f"   ⚠️ Variables de entorno faltantes: {', '.join(missing_vars)}")
                print("   🔄 Intentando cargar desde archivo JSON...")
            
            # 3. Si las variables de entorno no están completas, usar archivo JSON
            if not env_vars_complete:
                json_path = os.path.join(os.path.dirname(__file__), '..', 'keys', 'edp-control-system.json')
                if os.path.exists(json_path):
                    print(f"   📁 Cargando credenciales desde: {json_path}")
                    with open(json_path, 'r') as f:
                        credentials_data = json.load(f)
                    
                    # Verificar que el JSON tiene los campos necesarios
                    required_fields = ['project_id', 'client_email', 'private_key']
                    if all(field in credentials_data for field in required_fields):
                        print("   ✅ Archivo JSON válido encontrado")
                    else:
                        print(f"   ❌ Archivo JSON incompleto. Campos faltantes: {[f for f in required_fields if f not in credentials_data]}")
                        print("🎭 Activando modo demo")
                        return None
                else:
                    print(f"   ❌ Archivo JSON no encontrado: {json_path}")
                    print("🎭 Activando modo demo (sin Google Sheets)")
                    return None
            else:
                # 4. Usar variables de entorno para crear las credenciales
                print("   � Procesando clave privada desde variables de entorno...")
                processed_private_key = google_private_key.strip()
                
                # Remover comillas externas si existen
                if processed_private_key.startswith('"') and processed_private_key.endswith('"'):
                    processed_private_key = processed_private_key[1:-1]
                    print("   🔧 Removiendo comillas externas")
                
                # Si la clave contiene \n literales, convertirlos a saltos de línea reales
                if '\\n' in processed_private_key:
                    processed_private_key = processed_private_key.replace('\\n', '\n')
                    print("   🔧 Procesando \\n literales")
                
                # Verificar formato
                if not processed_private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                    print(f"   ❌ ERROR: Clave privada no tiene formato correcto")
                    print("   � Intentando cargar desde archivo JSON...")
                    # Fallback a JSON
                    json_path = os.path.join(os.path.dirname(__file__), '..', 'keys', 'edp-control-system-f3cfafc0093a.json')
                    if os.path.exists(json_path):
                        with open(json_path, 'r') as f:
                            credentials_data = json.load(f)
                    else:
                        print("🎭 Activando modo demo")
                        return None
                else:
                    # Crear credenciales desde variables de entorno
                    credentials_data = {
                        "type": "service_account",
                        "project_id": google_project_id,
                        "private_key_id": google_key_id,
                        "private_key": processed_private_key,
                        "client_email": google_client_email,
                        "client_id": google_client_id,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{google_client_email.replace('@', '%40')}"
                    }
            
            # 5. Crear credenciales y servicio
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
            
            # Debugging específico para diferentes tipos de errores
            if "seekable bit stream" in str(e):
                print("🔧 Error específico: problema con formato de private key")
                
            elif "Invalid" in str(e) and "private" in str(e).lower():
                print("🔧 Error específico: clave privada inválida")
                
            elif "JSON" in str(e):
                print("🔧 Error específico: problema con credenciales JSON")
            
            print("� Posibles soluciones:")
            print("   1. Verifica el archivo JSON en app/keys/")
            print("   2. Regenera las credenciales de Google Cloud")
            print("   3. Verifica permisos del archivo JSON")
            
            import traceback
            traceback.print_exc()
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