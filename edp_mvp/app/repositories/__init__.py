"""
Base repository classes for data access layer.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from time import time
import os
import json

from ..config import Config, get_config
from ..utils.gsheet import read_sheet, clear_all_cache


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
        """Create Google Sheets service using ONLY environment variables."""
        # Use the centralized get_service function from gsheet.py
        # This ensures consistent behavior across the application
        from ..utils.gsheet import get_service
        return get_service()
    
    def _read_range(self, range_name: str) -> List[List[str]]:
        """Read data from Google Sheets range using optimized cache from gsheet.py."""
        try:
            # Use the optimized read_sheet function which handles multi-level caching
            df = read_sheet(range_name)
            
            # Convert DataFrame back to list of lists format
            if df.empty:
                return []
            
            # Get headers and data
            headers = df.columns.tolist()
            data = df.values.tolist()
            
            # Convert all values to strings (as expected by Google Sheets API)
            result = [headers]
            for row in data:
                result.append([str(cell) if cell is not None else '' for cell in row])
            
            return result
        except Exception as e:
            print(f"Error reading range {range_name}: {str(e)}")
            return []

    def _read_ranges(self, range_names: List[str]) -> Dict[str, List[List[str]]]:
        """Batch read multiple ranges using optimized cache."""
        result_dict: Dict[str, List[List[str]]] = {}
        try:
            # Use individual reads with optimized cache - the cache layer will handle efficiency
            for range_name in range_names:
                result_dict[range_name] = self._read_range(range_name)
            return result_dict
        except Exception as e:
            print(f"Error reading ranges {range_names}: {str(e)}")
            return result_dict
    
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
            # Invalidate all caches after write
            clear_all_cache()
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
            # Invalidate all caches after append
            clear_all_cache()
            return True
        except Exception as e:
            print(f"Error appending to sheet {sheet_name}: {str(e)}")
            return False
    
    def _get_headers(self, sheet_name: str) -> List[str]:
        """Get headers from first row of sheet."""
        try:
            # Read headers directly using read_sheet to get the DataFrame
            df = read_sheet(f"{sheet_name}!1:1", apply_transformations=False)
            if not df.empty:
                return df.columns.tolist()
            
            # Fallback: try reading a larger range to get headers
            df_full = read_sheet(f"{sheet_name}!A:Z", apply_transformations=False)
            if not df_full.empty:
                return df_full.columns.tolist()
            
            return []
        except Exception as e:
            print(f"Error getting headers for {sheet_name}: {str(e)}")
            return []
    
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
