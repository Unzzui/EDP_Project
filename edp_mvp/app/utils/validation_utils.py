"""
Validation utilities for data validation and business rules.
"""
from typing import Any, Dict, List, Optional, Union, Callable
import re
from datetime import datetime, date
from email_validator import validate_email, EmailNotValidError


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(self.message)


class Validator:
    """Base validator class."""
    
    def __init__(self, message: str = None):
        self.message = message
    
    def __call__(self, value: Any) -> bool:
        """Make validator callable."""
        return self.validate(value)
    
    def validate(self, value: Any) -> bool:
        """Override in subclasses."""
        raise NotImplementedError


class RequiredValidator(Validator):
    """Validates that a value is not None or empty."""
    
    def __init__(self, message: str = "This field is required"):
        super().__init__(message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True


class LengthValidator(Validator):
    """Validates string length."""
    
    def __init__(self, min_length: int = None, max_length: int = None, 
                 message: str = None):
        self.min_length = min_length
        self.max_length = max_length
        if not message:
            if min_length and max_length:
                message = f"Length must be between {min_length} and {max_length} characters"
            elif min_length:
                message = f"Length must be at least {min_length} characters"
            elif max_length:
                message = f"Length must be no more than {max_length} characters"
        super().__init__(message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True  # Let RequiredValidator handle None
        
        length = len(str(value))
        
        if self.min_length and length < self.min_length:
            return False
        if self.max_length and length > self.max_length:
            return False
        
        return True


class EmailValidator(Validator):
    """Validates email format."""
    
    def __init__(self, message: str = "Invalid email format"):
        super().__init__(message)
    
    def validate(self, value: Any) -> bool:
        if value is None or value == "":
            return True  # Let RequiredValidator handle empty values
        
        try:
            validate_email(str(value))
            return True
        except EmailNotValidError:
            return False


class RegexValidator(Validator):
    """Validates against a regular expression pattern."""
    
    def __init__(self, pattern: str, message: str = "Invalid format"):
        self.pattern = re.compile(pattern)
        super().__init__(message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        return bool(self.pattern.match(str(value)))


class RangeValidator(Validator):
    """Validates numeric range."""
    
    def __init__(self, min_value: Union[int, float] = None, 
                 max_value: Union[int, float] = None, 
                 message: str = None):
        self.min_value = min_value
        self.max_value = max_value
        if not message:
            if min_value is not None and max_value is not None:
                message = f"Value must be between {min_value} and {max_value}"
            elif min_value is not None:
                message = f"Value must be at least {min_value}"
            elif max_value is not None:
                message = f"Value must be no more than {max_value}"
        super().__init__(message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        try:
            num_value = float(value)
            
            if self.min_value is not None and num_value < self.min_value:
                return False
            if self.max_value is not None and num_value > self.max_value:
                return False
            
            return True
        except (ValueError, TypeError):
            return False


class DateValidator(Validator):
    """Validates date format and range."""
    
    def __init__(self, min_date: Union[datetime, date] = None,
                 max_date: Union[datetime, date] = None,
                 message: str = "Invalid date"):
        self.min_date = min_date
        self.max_date = max_date
        super().__init__(message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        try:
            # Handle different input types
            if isinstance(value, str):
                # Try to parse ISO format
                parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif isinstance(value, datetime):
                parsed_date = value
            elif isinstance(value, date):
                parsed_date = datetime.combine(value, datetime.min.time())
            else:
                return False
            
            # Check range
            if self.min_date:
                min_dt = self.min_date if isinstance(self.min_date, datetime) else datetime.combine(self.min_date, datetime.min.time())
                if parsed_date < min_dt:
                    return False
            
            if self.max_date:
                max_dt = self.max_date if isinstance(self.max_date, datetime) else datetime.combine(self.max_date, datetime.max.time())
                if parsed_date > max_dt:
                    return False
            
            return True
        except (ValueError, TypeError):
            return False


class ChoiceValidator(Validator):
    """Validates that value is in a list of choices."""
    
    def __init__(self, choices: List[Any], message: str = None):
        self.choices = choices
        if not message:
            message = f"Value must be one of: {', '.join(str(c) for c in choices)}"
        super().__init__(message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        return value in self.choices


class ValidationUtils:
    """Utility class for validation operations."""
    
    # Common validators
    REQUIRED = RequiredValidator()
    EMAIL = EmailValidator()
    
    # Regex patterns
    PHONE_PATTERN = r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
    URL_PATTERN = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    ALPHA_PATTERN = r'^[a-zA-Z]+$'
    ALPHANUMERIC_PATTERN = r'^[a-zA-Z0-9]+$'
    
    @staticmethod
    def validate_field(value: Any, validators: List[Validator], field_name: str = None) -> Dict[str, Any]:
        """Validate a single field with multiple validators."""
        result = {
            'valid': True,
            'errors': []
        }
        
        for validator in validators:
            if not validator.validate(value):
                result['valid'] = False
                error = {
                    'message': validator.message,
                    'field': field_name,
                    'validator': validator.__class__.__name__
                }
                result['errors'].append(error)
        
        return result
    
    @staticmethod
    def validate_dict(data: Dict[str, Any], rules: Dict[str, List[Validator]]) -> Dict[str, Any]:
        """Validate a dictionary of data against rules."""
        result = {
            'valid': True,
            'errors': {},
            'field_errors': {}
        }
        
        for field_name, validators in rules.items():
            value = data.get(field_name)
            field_result = ValidationUtils.validate_field(value, validators, field_name)
            
            if not field_result['valid']:
                result['valid'] = False
                result['field_errors'][field_name] = field_result['errors']
                result['errors'][field_name] = [error['message'] for error in field_result['errors']]
        
        return result
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Quick email validation."""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        return bool(re.match(ValidationUtils.PHONE_PATTERN, phone))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format."""
        if not url:
            return False
        return bool(re.match(ValidationUtils.URL_PATTERN, url))
    
    @staticmethod
    def is_strong_password(password: str) -> Dict[str, Any]:
        """Check password strength."""
        if not password:
            return {'strong': False, 'score': 0, 'issues': ['Password is required']}
        
        issues = []
        score = 0
        
        # Length check
        if len(password) < 8:
            issues.append('Password must be at least 8 characters long')
        else:
            score += 1
        
        # Character type checks
        if not re.search(r'[a-z]', password):
            issues.append('Password must contain lowercase letters')
        else:
            score += 1
        
        if not re.search(r'[A-Z]', password):
            issues.append('Password must contain uppercase letters')
        else:
            score += 1
        
        if not re.search(r'[0-9]', password):
            issues.append('Password must contain numbers')
        else:
            score += 1
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append('Password must contain special characters')
        else:
            score += 1
        
        # Common password check
        common_passwords = ['password', '123456', 'password123', 'admin', 'qwerty']
        if password.lower() in common_passwords:
            issues.append('Password is too common')
            score = max(0, score - 2)
        
        strength_levels = {
            0: 'Very Weak',
            1: 'Weak', 
            2: 'Fair',
            3: 'Good',
            4: 'Strong',
            5: 'Very Strong'
        }
        
        return {
            'strong': score >= 4,
            'score': score,
            'strength': strength_levels.get(score, 'Unknown'),
            'issues': issues
        }
    
    @staticmethod
    def sanitize_input(value: str, max_length: int = None, allowed_chars: str = None) -> str:
        """Sanitize user input."""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove leading/trailing whitespace
        value = value.strip()
        
        # Limit length
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        # Filter allowed characters
        if allowed_chars:
            value = ''.join(c for c in value if c in allowed_chars)
        
        return value
    
    @staticmethod
    def validate_edp_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate EDP-specific data."""
        rules = {
            'name': [
                RequiredValidator(),
                LengthValidator(min_length=3, max_length=100)
            ],
            'responsible': [
                RequiredValidator(),
                LengthValidator(min_length=2, max_length=50)
            ],
            'status': [
                RequiredValidator(),
                ChoiceValidator(['planning', 'active', 'on_hold', 'completed', 'cancelled'])
            ],
            'priority': [
                ChoiceValidator(['low', 'medium', 'high', 'critical'])
            ],
            'budget': [
                RangeValidator(min_value=0)
            ]
        }
        
        result = ValidationUtils.validate_dict(data, rules)
        
        # Custom business logic validation
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] and data['end_date']:
                try:
                    start = datetime.fromisoformat(data['start_date']) if isinstance(data['start_date'], str) else data['start_date']
                    end = datetime.fromisoformat(data['end_date']) if isinstance(data['end_date'], str) else data['end_date']
                    
                    if start > end:
                        result['valid'] = False
                        result['errors']['date_range'] = ['Start date cannot be after end date']
                except (ValueError, TypeError):
                    result['valid'] = False
                    result['errors']['date_format'] = ['Invalid date format']
        
        return result
    
    @staticmethod
    def validate_project_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Project-specific data."""
        rules = {
            'name': [
                RequiredValidator(),
                LengthValidator(min_length=3, max_length=100)
            ],
            'edp_id': [
                RequiredValidator()
            ],
            'status': [
                RequiredValidator(),
                ChoiceValidator(['planning', 'in_progress', 'on_hold', 'review', 'completed', 'cancelled'])
            ],
            'priority': [
                ChoiceValidator(['low', 'medium', 'high', 'critical'])
            ],
            'progress': [
                RangeValidator(min_value=0, max_value=100)
            ],
            'budget': [
                RangeValidator(min_value=0)
            ]
        }
        
        return ValidationUtils.validate_dict(data, rules)
    
    @staticmethod
    def validate_log_entry_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate LogEntry-specific data."""
        rules = {
            'edp_id': [
                RequiredValidator()
            ],
            'log_type': [
                RequiredValidator(),
                ChoiceValidator(['created', 'updated', 'status_change', 'kpi_update', 'comment', 'system'])
            ],
            'message': [
                RequiredValidator(),
                LengthValidator(min_length=1, max_length=500)
            ],
            'user': [
                RequiredValidator(),
                LengthValidator(min_length=1, max_length=50)
            ]
        }
        
        return ValidationUtils.validate_dict(data, rules)
