"""
Configuration management for the EDP application.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

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
        
        return cls(
            credentials_file=os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
            # Cambiado para usar SHEET_ID que es lo que tienes en tu .env
            sheet_id=os.getenv('SHEET_ID', os.getenv('GOOGLE_SHEET_ID', '')),
            timeout=int(os.getenv('DB_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('DB_RETRY_ATTEMPTS', '3')),
            # SQLite config
            sqlite_db_path=sqlite_path,
            sqlalchemy_database_uri=os.getenv('DATABASE_URL', f"sqlite:///{sqlite_path}"),
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
        self.GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
        # Usar SHEET_ID de tu .env
        self.SHEET_ID = os.getenv('SHEET_ID', os.getenv('GOOGLE_SHEET_ID', ''))
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
