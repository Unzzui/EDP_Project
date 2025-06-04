"""
Log Repository for handling log entries data operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models import LogEntry
from . import BaseRepository


class LogRepository(BaseRepository):
    """Repository for managing log entries."""
    
    def __init__(self):
        super().__init__()
        self.sheet_name = "Logs"
    
    def find_all(self) -> List[LogEntry]:
        """Get all log entries."""
        try:
            sheet = self.get_sheet(self.sheet_name)
            if not sheet:
                return []
            
            records = sheet.get_all_records()
            return [self._dict_to_log_entry(record) for record in records]
        except Exception as e:
            print(f"Error fetching all logs: {e}")
            return []
    
    def find_by_edp_id(self, edp_id: str) -> List[LogEntry]:
        """Get all log entries for a specific EDP."""
        try:
            all_logs = self.find_all()
            return [log for log in all_logs if log.edp_id == edp_id]
        except Exception as e:
            print(f"Error fetching logs for EDP {edp_id}: {e}")
            return []
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[LogEntry]:
        """Get log entries within a date range."""
        try:
            all_logs = self.find_all()
            return [
                log for log in all_logs 
                if start_date <= log.timestamp <= end_date
            ]
        except Exception as e:
            print(f"Error fetching logs by date range: {e}")
            return []
    
    def find_by_type(self, log_type: str) -> List[LogEntry]:
        """Get log entries by type."""
        try:
            all_logs = self.find_all()
            return [log for log in all_logs if log.log_type == log_type]
        except Exception as e:
            print(f"Error fetching logs by type {log_type}: {e}")
            return []
    
    def create(self, log_entry: LogEntry) -> bool:
        """Create a new log entry."""
        try:
            sheet = self.get_sheet(self.sheet_name)
            if not sheet:
                return False
            
            row_data = self._log_entry_to_list(log_entry)
            sheet.append_row(row_data)
            return True
        except Exception as e:
            print(f"Error creating log entry: {e}")
            return False
    
    def create_bulk(self, log_entries: List[LogEntry]) -> bool:
        """Create multiple log entries at once."""
        try:
            sheet = self.get_sheet(self.sheet_name)
            if not sheet:
                return False
            
            rows_data = [self._log_entry_to_list(log) for log in log_entries]
            sheet.append_rows(rows_data)
            return True
        except Exception as e:
            print(f"Error creating bulk log entries: {e}")
            return False
    
    def delete_old_logs(self, days_old: int = 90) -> bool:
        """Delete log entries older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            sheet = self.get_sheet(self.sheet_name)
            if not sheet:
                return False
            
            records = sheet.get_all_records()
            rows_to_delete = []
            
            for i, record in enumerate(records, start=2):  # Start at 2 (header is row 1)
                log_date = datetime.fromisoformat(record.get('timestamp', ''))
                if log_date < cutoff_date:
                    rows_to_delete.append(i)
            
            # Delete from bottom to top to maintain row indices
            for row_num in reversed(rows_to_delete):
                sheet.delete_rows(row_num)
            
            return True
        except Exception as e:
            print(f"Error deleting old logs: {e}")
            return False
    
    def _dict_to_log_entry(self, record: Dict[str, Any]) -> LogEntry:
        """Convert dictionary from Google Sheets to LogEntry object."""
        return LogEntry(
            id=record.get('id', ''),
            edp_id=record.get('edp_id', ''),
            timestamp=datetime.fromisoformat(record.get('timestamp', '')),
            log_type=record.get('log_type', ''),
            message=record.get('message', ''),
            user=record.get('user', ''),
            details=record.get('details', {})
        )
    
    def _log_entry_to_list(self, log_entry: LogEntry) -> List[Any]:
        """Convert LogEntry object to list for Google Sheets."""
        return [
            log_entry.id,
            log_entry.edp_id,
            log_entry.timestamp.isoformat(),
            log_entry.log_type,
            log_entry.message,
            log_entry.user,
            str(log_entry.details) if log_entry.details else ''
        ]
