"""
Base service classes and utilities for the services layer.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class BaseService(ABC):
    """Base class for all services."""
    
    def __init__(self):
        self.created_at = datetime.now()
    
    def generate_id(self) -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> bool:
        """Validate that all required fields are present and not empty."""
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        return True
    
    def sanitize_string(self, value: str) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return str(value)
        return value.strip()
    
    def format_currency(self, amount: float) -> str:
        """Format currency amount."""
        return f"${amount:,.2f}"
    
    def format_percentage(self, value: float) -> str:
        """Format percentage value."""
        return f"{value:.1f}%"


class ServiceResponse:
    """Standard response class for service operations."""
    
    def __init__(self, success: bool, data: Any = None, message: str = "", errors: Optional[Dict] = None):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'errors': self.errors,
            'timestamp': self.timestamp.isoformat()
        }


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Custom exception for business logic errors."""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)
