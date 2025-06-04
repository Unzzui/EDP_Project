"""
Date utilities for handling date operations and formatting.
"""
from datetime import datetime, timedelta, date
from typing import Optional, Union, Tuple
import calendar


# Standalone utility functions for backward compatibility
def parse_date_safe(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[datetime]:
    """Parse date string to datetime object safely."""
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None


class DateUtils:
    """Utility class for date operations."""
    
    # Common date formats
    ISO_FORMAT = "%Y-%m-%d"
    DISPLAY_FORMAT = "%B %d, %Y"
    SHORT_FORMAT = "%m/%d/%Y"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    @staticmethod
    def now() -> datetime:
        """Get current datetime."""
        return datetime.now()
    
    @staticmethod
    def today() -> date:
        """Get current date."""
        return date.today()
    
    @staticmethod
    def parse_date(date_str: str, format_str: str = ISO_FORMAT) -> Optional[datetime]:
        """Parse date string to datetime object."""
        try:
            return datetime.strptime(date_str, format_str)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def format_date(dt: Union[datetime, date], format_str: str = DISPLAY_FORMAT) -> str:
        """Format datetime/date object to string."""
        try:
            if isinstance(dt, datetime):
                return dt.strftime(format_str)
            elif isinstance(dt, date):
                return dt.strftime(format_str)
            else:
                return str(dt)
        except (ValueError, AttributeError):
            return str(dt)
    
    @staticmethod
    def days_between(start_date: Union[datetime, date], end_date: Union[datetime, date]) -> int:
        """Calculate days between two dates."""
        try:
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()
            
            return (end_date - start_date).days
        except (AttributeError, TypeError):
            return 0
    
    @staticmethod
    def add_days(dt: Union[datetime, date], days: int) -> Union[datetime, date]:
        """Add days to a date."""
        try:
            return dt + timedelta(days=days)
        except (TypeError, AttributeError):
            return dt
    
    @staticmethod
    def subtract_days(dt: Union[datetime, date], days: int) -> Union[datetime, date]:
        """Subtract days from a date."""
        try:
            return dt - timedelta(days=days)
        except (TypeError, AttributeError):
            return dt
    
    @staticmethod
    def get_week_range(dt: Union[datetime, date] = None) -> Tuple[date, date]:
        """Get the start and end of the week for a given date."""
        if dt is None:
            dt = date.today()
        elif isinstance(dt, datetime):
            dt = dt.date()
        
        # Monday is 0, Sunday is 6
        days_since_monday = dt.weekday()
        start_of_week = dt - timedelta(days=days_since_monday)
        end_of_week = start_of_week + timedelta(days=6)
        
        return start_of_week, end_of_week
    
    @staticmethod
    def get_month_range(dt: Union[datetime, date] = None) -> Tuple[date, date]:
        """Get the start and end of the month for a given date."""
        if dt is None:
            dt = date.today()
        elif isinstance(dt, datetime):
            dt = dt.date()
        
        start_of_month = dt.replace(day=1)
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        end_of_month = dt.replace(day=last_day)
        
        return start_of_month, end_of_month
    
    @staticmethod
    def get_quarter_range(dt: Union[datetime, date] = None) -> Tuple[date, date]:
        """Get the start and end of the quarter for a given date."""
        if dt is None:
            dt = date.today()
        elif isinstance(dt, datetime):
            dt = dt.date()
        
        quarter = (dt.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        
        start_of_quarter = dt.replace(month=start_month, day=1)
        
        # Get last day of the quarter
        if end_month == 12:
            end_of_quarter = dt.replace(month=12, day=31)
        else:
            # Get last day of end_month
            last_day = calendar.monthrange(dt.year, end_month)[1]
            end_of_quarter = dt.replace(month=end_month, day=last_day)
        
        return start_of_quarter, end_of_quarter
    
    @staticmethod
    def get_year_range(dt: Union[datetime, date] = None) -> Tuple[date, date]:
        """Get the start and end of the year for a given date."""
        if dt is None:
            dt = date.today()
        elif isinstance(dt, datetime):
            dt = dt.date()
        
        start_of_year = dt.replace(month=1, day=1)
        end_of_year = dt.replace(month=12, day=31)
        
        return start_of_year, end_of_year
    
    @staticmethod
    def is_weekend(dt: Union[datetime, date]) -> bool:
        """Check if a date is a weekend."""
        try:
            if isinstance(dt, datetime):
                dt = dt.date()
            return dt.weekday() >= 5  # Saturday is 5, Sunday is 6
        except AttributeError:
            return False
    
    @staticmethod
    def is_business_day(dt: Union[datetime, date]) -> bool:
        """Check if a date is a business day (Monday-Friday)."""
        return not DateUtils.is_weekend(dt)
    
    @staticmethod
    def get_business_days_between(start_date: Union[datetime, date], end_date: Union[datetime, date]) -> int:
        """Calculate business days between two dates."""
        try:
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()
            
            if start_date > end_date:
                start_date, end_date = end_date, start_date
            
            business_days = 0
            current_date = start_date
            
            while current_date <= end_date:
                if DateUtils.is_business_day(current_date):
                    business_days += 1
                current_date += timedelta(days=1)
            
            return business_days
        except (AttributeError, TypeError):
            return 0
    
    @staticmethod
    def get_relative_time_string(dt: datetime) -> str:
        """Get a relative time string (e.g., '2 hours ago', 'in 3 days')."""
        try:
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                if diff.days == 1:
                    return "1 day ago"
                else:
                    return f"{diff.days} days ago"
            elif diff.days < 0:
                future_days = abs(diff.days)
                if future_days == 1:
                    return "in 1 day"
                else:
                    return f"in {future_days} days"
            else:
                # Same day
                seconds = diff.seconds
                if seconds < 60:
                    return "just now"
                elif seconds < 3600:
                    minutes = seconds // 60
                    return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                else:
                    hours = seconds // 3600
                    return f"{hours} hour{'s' if hours > 1 else ''} ago"
        except (AttributeError, TypeError):
            return str(dt)
    
    @staticmethod
    def is_overdue(target_date: Union[datetime, date], current_date: Union[datetime, date] = None) -> bool:
        """Check if a target date is overdue."""
        if current_date is None:
            current_date = datetime.now() if isinstance(target_date, datetime) else date.today()
        
        try:
            # Convert to same type for comparison
            if isinstance(target_date, datetime) and isinstance(current_date, date):
                current_date = datetime.combine(current_date, datetime.min.time())
            elif isinstance(target_date, date) and isinstance(current_date, datetime):
                target_date = datetime.combine(target_date, datetime.min.time())
            
            return current_date > target_date
        except (AttributeError, TypeError):
            return False
    
    @staticmethod
    def get_age_in_days(birth_date: Union[datetime, date]) -> int:
        """Get age in days from a birth date."""
        try:
            today = date.today() if isinstance(birth_date, date) else datetime.now()
            if isinstance(birth_date, datetime) and isinstance(today, date):
                today = datetime.combine(today, datetime.min.time())
            elif isinstance(birth_date, date) and isinstance(today, datetime):
                birth_date = datetime.combine(birth_date, datetime.min.time())
            
            return (today - birth_date).days
        except (AttributeError, TypeError):
            return 0
    
    @staticmethod
    def validate_date_range(start_date: Union[datetime, date], end_date: Union[datetime, date]) -> bool:
        """Validate that start_date is before or equal to end_date."""
        try:
            # Convert to same type for comparison
            if isinstance(start_date, datetime) and isinstance(end_date, date):
                end_date = datetime.combine(end_date, datetime.max.time())
            elif isinstance(start_date, date) and isinstance(end_date, datetime):
                start_date = datetime.combine(start_date, datetime.min.time())
            
            return start_date <= end_date
        except (AttributeError, TypeError):
            return False
