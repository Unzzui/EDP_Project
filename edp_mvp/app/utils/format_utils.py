"""
Formatting utilities for consistent data presentation.
"""
from typing import Any, Optional, List, Dict, Union
from decimal import Decimal, ROUND_HALF_UP
import re


# Standalone utility functions for backward compatibility
def clean_numeric_value(value: Any) -> Optional[float]:
    """Clean and convert value to numeric format, handling various input types."""
    if value is None or value == '':
        return None
    
    try:
        # If already a number
        if isinstance(value, (int, float, Decimal)):
            return float(value)
        
        # If string, clean it up
        if isinstance(value, str):
            # Remove currency symbols, commas, spaces
            cleaned = re.sub(r'[^\d.-]', '', value.strip())
            if cleaned == '' or cleaned == '-':
                return None
            return float(cleaned)
            
        # Try direct conversion for other types
        return float(value)
        
    except (ValueError, TypeError, AttributeError):
        return None


class FormatUtils:
    """Utility class for formatting data."""
    
    @staticmethod
    def format_currency(amount: Union[float, int, Decimal], currency_symbol: str = "$", decimal_places: int = 2) -> str:
        """Format number as currency with periods as thousands separator."""
        try:
            if amount is None:
                return f"{currency_symbol}0.00"
            
            amount = float(amount)
            formatted = f"{amount:,.{decimal_places}f}"
            # Replace commas with periods for thousands separator
            formatted = formatted.replace(",", ".")
            return f"{currency_symbol}{formatted}"
        except (ValueError, TypeError):
            return f"{currency_symbol}0.00"
    
    @staticmethod
    def format_percentage(value: Union[float, int], decimal_places: int = 1, include_symbol: bool = True) -> str:
        """Format number as percentage."""
        try:
            if value is None:
                return "0.0%" if include_symbol else "0.0"
            
            value = float(value)
            formatted = f"{value:.{decimal_places}f}"
            return f"{formatted}%" if include_symbol else formatted
        except (ValueError, TypeError):
            return "0.0%" if include_symbol else "0.0"
    
    @staticmethod
    def format_number(value: Union[float, int], decimal_places: int = 2, thousands_separator: bool = True) -> str:
        """Format number with periods as thousands separator and decimal places."""
        try:
            if value is None:
                return "0"
            
            value = float(value)
            if thousands_separator:
                formatted = f"{value:,.{decimal_places}f}"
                # Replace commas with periods for thousands separator
                formatted = formatted.replace(",", ".")
                return formatted
            else:
                return f"{value:.{decimal_places}f}"
        except (ValueError, TypeError):
            return "0"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format."""
        try:
            if size_bytes == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
            
            return f"{size_bytes:.1f} {size_names[i]}"
        except (ValueError, TypeError):
            return "0 B"
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to specified length with suffix."""
        try:
            if not text or len(text) <= max_length:
                return text
            
            return text[:max_length - len(suffix)] + suffix
        except (TypeError, AttributeError):
            return str(text)
    
    @staticmethod
    def format_phone_number(phone: str, format_type: str = "US") -> str:
        """Format phone number."""
        try:
            # Remove all non-digit characters
            digits = re.sub(r'\D', '', phone)
            
            if format_type.upper() == "US" and len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif format_type.upper() == "US" and len(digits) == 11 and digits[0] == '1':
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            else:
                return phone  # Return original if can't format
        except (TypeError, AttributeError):
            return str(phone)
    
    @staticmethod
    def format_list_to_string(items: List[Any], separator: str = ", ", last_separator: str = " and ") -> str:
        """Format list items into a readable string."""
        try:
            if not items:
                return ""
            
            str_items = [str(item) for item in items]
            
            if len(str_items) == 1:
                return str_items[0]
            elif len(str_items) == 2:
                return f"{str_items[0]}{last_separator}{str_items[1]}"
            else:
                return f"{separator.join(str_items[:-1])}{last_separator}{str_items[-1]}"
        except (TypeError, AttributeError):
            return str(items)
    
    @staticmethod
    def format_title_case(text: str) -> str:
        """Format text to title case with smart handling."""
        try:
            if not text:
                return text
            
            # Words that should not be capitalized (unless they're the first word)
            small_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 
                          'nor', 'of', 'on', 'or', 'so', 'the', 'to', 'up', 'yet'}
            
            words = text.lower().split()
            formatted_words = []
            
            for i, word in enumerate(words):
                if i == 0 or word not in small_words:
                    formatted_words.append(word.capitalize())
                else:
                    formatted_words.append(word)
            
            return ' '.join(formatted_words)
        except (TypeError, AttributeError):
            return str(text)
    
    @staticmethod
    def format_camel_to_readable(camel_case: str) -> str:
        """Convert camelCase or PascalCase to readable format."""
        try:
            # Add space before uppercase letters
            result = re.sub(r'([a-z])([A-Z])', r'\1 \2', camel_case)
            # Capitalize first letter
            return result.capitalize()
        except (TypeError, AttributeError):
            return str(camel_case)
    
    @staticmethod
    def format_snake_to_readable(snake_case: str) -> str:
        """Convert snake_case to readable format."""
        try:
            return snake_case.replace('_', ' ').title()
        except (TypeError, AttributeError):
            return str(snake_case)
    
    @staticmethod
    def format_status_badge(status: str) -> Dict[str, str]:
        """Format status for badge display with color and text."""
        try:
            status_lower = status.lower()
            
            status_config = {
                'active': {'text': 'Active', 'color': 'success', 'bg_color': '#28a745'},
                'inactive': {'text': 'Inactive', 'color': 'secondary', 'bg_color': '#6c757d'},
                'pending': {'text': 'Pending', 'color': 'warning', 'bg_color': '#ffc107'},
                'completed': {'text': 'Completed', 'color': 'primary', 'bg_color': '#007bff'},
                'cancelled': {'text': 'Cancelled', 'color': 'danger', 'bg_color': '#dc3545'},
                'on_hold': {'text': 'On Hold', 'color': 'warning', 'bg_color': '#ffc107'},
                'planning': {'text': 'Planning', 'color': 'info', 'bg_color': '#17a2b8'},
                'in_progress': {'text': 'In Progress', 'color': 'primary', 'bg_color': '#007bff'},
                'review': {'text': 'Review', 'color': 'warning', 'bg_color': '#ffc107'},
                'draft': {'text': 'Draft', 'color': 'secondary', 'bg_color': '#6c757d'}
            }
            
            return status_config.get(status_lower, {
                'text': FormatUtils.format_title_case(status),
                'color': 'secondary',
                'bg_color': '#6c757d'
            })
        except (TypeError, AttributeError):
            return {'text': str(status), 'color': 'secondary', 'bg_color': '#6c757d'}
    
    @staticmethod
    def format_priority_badge(priority: str) -> Dict[str, str]:
        """Format priority for badge display with color and text."""
        try:
            priority_lower = priority.lower()
            
            priority_config = {
                'low': {'text': 'Low', 'color': 'success', 'bg_color': '#28a745'},
                'medium': {'text': 'Medium', 'color': 'warning', 'bg_color': '#ffc107'},
                'high': {'text': 'High', 'color': 'danger', 'bg_color': '#dc3545'},
                'critical': {'text': 'Critical', 'color': 'danger', 'bg_color': '#dc3545', 'pulse': True},
                'urgent': {'text': 'Urgent', 'color': 'danger', 'bg_color': '#dc3545'}
            }
            
            return priority_config.get(priority_lower, {
                'text': FormatUtils.format_title_case(priority),
                'color': 'secondary',
                'bg_color': '#6c757d'
            })
        except (TypeError, AttributeError):
            return {'text': str(priority), 'color': 'secondary', 'bg_color': '#6c757d'}
    
    @staticmethod
    def format_health_score(score: Union[float, int]) -> Dict[str, Any]:
        """Format health score with color coding and description."""
        try:
            score = float(score)
            
            if score >= 90:
                return {
                    'score': score,
                    'label': 'Excellent',
                    'color': 'success',
                    'bg_color': '#28a745',
                    'description': 'Project is performing excellently'
                }
            elif score >= 70:
                return {
                    'score': score,
                    'label': 'Good',
                    'color': 'primary',
                    'bg_color': '#007bff',
                    'description': 'Project is performing well'
                }
            elif score >= 50:
                return {
                    'score': score,
                    'label': 'Fair',
                    'color': 'warning',
                    'bg_color': '#ffc107',
                    'description': 'Project needs attention'
                }
            else:
                return {
                    'score': score,
                    'label': 'Poor',
                    'color': 'danger',
                    'bg_color': '#dc3545',
                    'description': 'Project requires immediate attention'
                }
        except (ValueError, TypeError):
            return {
                'score': 0,
                'label': 'Unknown',
                'color': 'secondary',
                'bg_color': '#6c757d',
                'description': 'Score unavailable'
            }
    
    @staticmethod
    def format_tags(tags: List[str], max_display: int = 3) -> Dict[str, Any]:
        """Format tags for display with overflow handling."""
        try:
            if not tags:
                return {'visible': [], 'hidden': [], 'overflow_count': 0}
            
            visible = tags[:max_display]
            hidden = tags[max_display:]
            overflow_count = len(hidden)
            
            return {
                'visible': visible,
                'hidden': hidden,
                'overflow_count': overflow_count
            }
        except (TypeError, AttributeError):
            return {'visible': [], 'hidden': [], 'overflow_count': 0}
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Basic HTML sanitization by escaping HTML characters."""
        try:
            if not text:
                return text
            
            html_escape_table = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }
            
            return "".join(html_escape_table.get(c, c) for c in text)
        except (TypeError, AttributeError):
            return str(text)
    
    @staticmethod
    def format_json_pretty(data: Dict[str, Any], indent: int = 2) -> str:
        """Format dictionary as pretty JSON string."""
        try:
            import json
            return json.dumps(data, indent=indent, sort_keys=True, default=str)
        except (TypeError, AttributeError, ValueError):
            return str(data)
            
    @staticmethod
    def to_json_safe(data: Any) -> str:
        """Convert any data structure to a JSON string safely, handling non-serializable types."""
        try:
            import json
            from datetime import datetime, date
            
            def json_serial(obj):
                """JSON serializer for objects not serializable by default json code"""
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                if isinstance(obj, Decimal):
                    return float(obj)
                if hasattr(obj, '__dict__'):
                    return obj.__dict__
                return str(obj)
                
            return json.dumps(data, default=json_serial)
        except Exception as e:
            # Fallback to basic string representation if JSON conversion fails
            print(f"JSON serialization error: {e}")
            return "{}"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to human readable format."""
        try:
            if seconds < 60:
                return f"{seconds} second{'s' if seconds != 1 else ''}"
            elif seconds < 3600:
                minutes = seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
            elif seconds < 86400:
                hours = seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                days = seconds // 86400
                return f"{days} day{'s' if days != 1 else ''}"
        except (ValueError, TypeError):
            return "0 seconds"
    
    @staticmethod
    def clean_numeric_value(value: Any) -> Optional[float]:
        """Clean and convert value to numeric format, handling various input types."""
        if value is None or value == '':
            return None
        
        try:
            # If already a number
            if isinstance(value, (int, float, Decimal)):
                return float(value)
            
            # If string, clean it up
            if isinstance(value, str):
                # Remove currency symbols, commas, spaces
                cleaned = re.sub(r'[^\d.-]', '', value.strip())
                if cleaned == '' or cleaned == '-':
                    return None
                return float(cleaned)
                
            # Try direct conversion for other types
            return float(value)
            
        except (ValueError, TypeError, AttributeError):
            return None
