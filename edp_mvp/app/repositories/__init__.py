"""
Base repository classes for data access layer.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from ..config import Config, get_config


class BaseRepository(ABC):
    """Abstract base repository class."""
    
    def __init__(self):
        self._service = None
    
    @property
    def service(self):
        """Get Google Sheets service instance."""
        if self._service is None:
            self._service = self._get_service()
        return self._service
    
    def _get_service(self):
        """Create Google Sheets service."""
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        config = get_config()
        creds = Credentials.from_service_account_file(
            config.GOOGLE_CREDENTIALS, 
            scopes=scopes
        )
        return build('sheets', 'v4', credentials=creds)
    
    def _read_range(self, range_name: str) -> List[List[str]]:
        """Read data from Google Sheets range."""
        try:
            config = get_config()
            result = self.service.spreadsheets().values().get(
                spreadsheetId=config.SHEET_ID,
                range=range_name
            ).execute()
            return result.get('values', [])
        except Exception as e:
            print(f"Error reading range {range_name}: {str(e)}")
            return []
    
    def _write_range(self, range_name: str, values: List[List[str]], 
                    value_input_option: str = "USER_ENTERED") -> bool:
        """Write data to Google Sheets range."""
        try:
            config = get_config()
            self.service.spreadsheets().values().update(
                spreadsheetId=config.SHEET_ID,
                range=range_name,
                valueInputOption=value_input_option,
                body={"values": values}
            ).execute()
            return True
        except Exception as e:
            print(f"Error writing to range {range_name}: {str(e)}")
            return False
    
    def _append_rows(self, sheet_name: str, values: List[List[str]]) -> bool:
        """Append rows to a sheet."""
        try:
            config = get_config()
            self.service.spreadsheets().values().append(
                spreadsheetId=config.SHEET_ID,
                range=sheet_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": values}
            ).execute()
            return True
        except Exception as e:
            print(f"Error appending to sheet {sheet_name}: {str(e)}")
            return False
    
    def _get_headers(self, sheet_name: str) -> List[str]:
        """Get headers from first row of sheet."""
        values = self._read_range(f"{sheet_name}!1:1")
        return values[0] if values else []
    
    def _values_to_dataframe(self, values: List[List[str]], 
                            apply_transformations: bool = True) -> pd.DataFrame:
        """Convert sheet values to pandas DataFrame."""
        if not values or len(values) < 2:
            return pd.DataFrame()
        
        headers = values[0]
        data = values[1:]
        
        # Ensure all rows have same length as headers
        normalized_data = []
        for row in data:
            normalized_row = row + [''] * (len(headers) - len(row))
            normalized_data.append(normalized_row[:len(headers)])
        
        df = pd.DataFrame(normalized_data, columns=headers)
        df = df.fillna("")
        
        return df


class SheetsRepository(BaseRepository):
    """Repository for basic Google Sheets operations."""
    
    def read_sheet_raw(self, range_name: str) -> pd.DataFrame:
        """Read sheet data without transformations."""
        values = self._read_range(range_name)
        return self._values_to_dataframe(values, apply_transformations=False)
    
    def get_next_id(self, sheet_name: str, id_column: str = "A") -> int:
        """Get the next available ID for a sheet."""
        values = self._read_range(f"{sheet_name}!{id_column}:{id_column}")
        if not values or len(values) < 2:
            return 1
        
        # Skip header and get existing IDs
        ids = []
        for row in values[1:]:
            if row and row[0].isdigit():
                ids.append(int(row[0]))
        
        return max(ids) + 1 if ids else 1
    
    def find_row_by_id(self, sheet_name: str, record_id: str, 
                      id_column: str = "A") -> Optional[int]:
        """Find row number by ID (1-based, including header)."""
        values = self._read_range(f"{sheet_name}!{id_column}:{id_column}")
        
        for i, row in enumerate(values):
            if row and str(row[0]) == str(record_id):
                return i + 1  # 1-based indexing
        
        return None
