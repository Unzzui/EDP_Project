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
import redis

# Simple in-memory cache with optional Redis backend
_range_cache: Dict[str, tuple] = {}
_redis_client = None
try:  # pragma: no cover - optional dependency

    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        print(f"🔗 Conectando a Redis en {redis_url}")
        _redis_client = redis.from_url(redis_url)
        print("✅ Conexión a Redis exitosa")
except Exception as e:
    print(f"⚠️ Error conectando a Redis: {e}")
    _redis_client = None

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
        """Read data from Google Sheets range with caching (Redis if available)."""
        try:
            config = get_config()
            timeout = getattr(config.app, "cache_timeout", 0)
            now = time()

            # Redis cache
            if _redis_client:
                cached = _redis_client.get(range_name)
                if cached:
                    return json.loads(cached)

            if range_name in _range_cache:
                ts, values = _range_cache[range_name]
                if now - ts < timeout:
                    return values

            result = self.service.spreadsheets().values().get(
                spreadsheetId=config.SHEET_ID,
                range=range_name
            ).execute()
            values = result.get("values", [])
            _range_cache[range_name] = (now, values)
            if _redis_client:
                _redis_client.setex(range_name, timeout, json.dumps(values))
            return values
        except Exception as e:
            print(f"Error reading range {range_name}: {str(e)}")
            return []

    def _read_ranges(self, range_names: List[str]) -> Dict[str, List[List[str]]]:
        """Batch read multiple ranges using Google Sheets batchGet."""
        result_dict: Dict[str, List[List[str]]] = {}
        try:
            config = get_config()
            timeout = getattr(config.app, "cache_timeout", 0)
            now = time()

            to_fetch = []
            for r in range_names:
                if _redis_client:
                    cached = _redis_client.get(r)
                    if cached:
                        result_dict[r] = json.loads(cached)
                        continue
                if r in _range_cache:
                    ts, values = _range_cache[r]
                    if now - ts < timeout:
                        result_dict[r] = values
                        continue
                to_fetch.append(r)

            if to_fetch:
                response = (
                    self.service.spreadsheets()
                    .values()
                    .batchGet(spreadsheetId=config.SHEET_ID, ranges=to_fetch)
                    .execute()
                )
                for item in response.get("valueRanges", []):
                    values = item.get("values", [])
                    r = item.get("range", to_fetch[0])
                    _range_cache[r] = (now, values)
                    if _redis_client:
                        _redis_client.setex(r, timeout, json.dumps(values))
                    result_dict[r] = values

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
            _range_cache.clear()  # invalidate cache after write
            if _redis_client:
                _redis_client.flushdb()
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
            _range_cache.clear()  # invalidate cache after append
            if _redis_client:
                _redis_client.flushdb()
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
