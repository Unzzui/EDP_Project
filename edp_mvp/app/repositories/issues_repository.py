"""
Repository for issues data access.
"""


from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import logging

from . import BaseRepository, SheetsRepository
from ..models import Cost
from ..utils.date_utils import parse_date_safe
from ..utils.format_utils import clean_numeric_value

logger = logging.getLogger(__name__)



class IssuesRepository(BaseRepository):
    """Repository for issues data access."""

    def __init__(self):
        super().__init__()
        self.sheets_repo = SheetsRepository()
        self.sheet_name = "issues"
        self.range_name = "issues!A:R"  # A to R 
        
    def find_all_dataframe(self, apply_filters: bool = True) -> Dict[str, Any]:
            """Get all costs as DataFrame for analytics purposes."""
            try:
                df = self._read_sheet_with_transformations()

                return {
                    "success": True,
                    "data": df,
                    "message": f"Successfully retrieved {len(df)} costs as DataFrame",
                }
            except Exception as e:
                return {
                    "success": False,
                    "data": pd.DataFrame(),
                    "message": f"Error retrieving costs DataFrame: {str(e)}",
                }
            
    def _read_sheet_with_transformations(self) -> pd.DataFrame:
        values = self._read_range(self.range_name)
        df = self._values_to_dataframe(values)

        if df.empty:
            return df

        # Apply transformations
        df = self._apply_transformations(df)
        return df
    
    def _apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply transformations to the dataframe."""
        return df
    
