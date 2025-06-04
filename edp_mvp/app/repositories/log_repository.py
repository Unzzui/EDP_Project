"""
Log Repository for handling log entries data operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models import LogEntry
from . import BaseRepository, SheetsRepository
import pandas as pd

class LogRepository(BaseRepository):
    """Repository for managing log entries."""
    
    def __init__(self):
        super().__init__()
        self.sheets_repo = SheetsRepository()
        self.sheet_name = "log"
        self.range_name = "log!A:G"
    
    def find_all(self) -> List[LogEntry]:
        """Get all log entries."""
        try:
            df = self._read_sheet_with_transformations()
            models = self._dataframe_to_models(df)
            
            return {
                'success': True,
                'data': models,
                'message': f"Successfully retrieved {len(models)} Log entries."
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'message': f"Error retrieving Logs: {str(e)}"
            }
    
    

    def _read_sheet_with_transformations(self) -> pd.DataFrame:
        """Read EDP sheet with all transformations applied."""
        values = self._read_range(self.range_name)
        df = self._values_to_dataframe(values)
        
        if df.empty:
            return df
        
        # Apply transformations
        df = self._apply_transformations(df)
        
        return df
    
    def _apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply necessary transformations to the DataFrame."""
        # Convert timestamp to datetime
        # df['fecha_hora'] = pd.to_datetime(df['fecha_hora'], errors='coerce')
        
        # # Convert details from string to dictionary if needed
        # if 'campo' in df.columns:
        #     df['campo'] = df['campo'].apply(lambda x: eval(x) if isinstance(x, str) else x)
        
        return df
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

    def _dataframe_to_models(self, df: pd.DataFrame) -> List[LogEntry]:
        """Convert DataFrame to list of EDP models."""
        models = []
        
        for _, row in df.iterrows():
            model_data = {
                'id': row.get('id'),
                'fecha_hora': row.get('fecha_hora'),
                'n_edp': row.get('n_edp'),
                'proyecto': row.get('proyecto'),
                'campo': row.get('campo'),
                'antes': row.get('antes'),
                'despues': row.get('despues'),
                'usuario': row.get('usuario', {})
            }
            
            # Clean None values and convert types
            cleaned_data = {}
            for k, v in model_data.items():
                if pd.isna(v):
                    cleaned_data[k] = None
                else:
                    cleaned_data[k] = v
            
            models.append(LogEntry.from_dict(cleaned_data))
        
        return models
    
    def _model_to_row_values(self, log: LogEntry, headers: Optional[List[str]] = None) -> List[str]:
        """Convert EDP model to row values for Google Sheets."""
        if headers is None:
            headers = self.sheets_repo._get_headers(self.sheet_name)
        
        # Map model fields to sheet columns (now using lowercase names)
        field_mapping = {
            'id': log.id,
            'fecha_hora': log.timestamp.isoformat() if log.timestamp else None,
            'n_edp': log.edp_id,
            'proyecto': log.proyecto,
            'campo': str(log.details) if log.details else None,
            'antes': str(log.before) if log.before else None,
            'despues': str(log.after) if log.after else None,
            'usuario': log.user
        }
        
        # Build row values according to headers
        row_values = []
        for header in headers:
            value = field_mapping.get(header, "")
            row_values.append(str(value) if value is not None else "")
        
        return row_values
    
    def _get_last_column(self, num_cols: int) -> str:
        """Convert column number to Excel column letter."""
        result = ""
        while num_cols > 0:
            num_cols -= 1
            result = chr(65 + (num_cols % 26)) + result
            num_cols //= 26
        return result
