"""
Repository for Cost data access.
"""
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

from . import BaseRepository, SheetsRepository
from ..models import Cost
from ..utils.date_utils import parse_date_safe
from ..utils.format_utils import clean_numeric_value


class CostRepository(BaseRepository):
    """Repository for Cost operations."""
    
    def __init__(self):
        super().__init__()
        self.sheets_repo = SheetsRepository()
        self.sheet_name = "cost_header"
        self.range_name = "cost_header!A:Q"  # A to Q for 17 columns
    
    def find_all(self, apply_filters: bool = True) -> Dict[str, Any]:
        """Get all costs with optional transformations."""
        try:
            df = self._read_sheet_with_transformations()
            models = self._dataframe_to_models(df)
            
            return {
                'success': True,
                'data': models,
                'message': f"Successfully retrieved {len(models)} costs"
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'message': f"Error retrieving costs: {str(e)}"
            }
    
    def find_all_dataframe(self, apply_filters: bool = True) -> Dict[str, Any]:
        """Get all costs as DataFrame for analytics purposes."""
        try:
            df = self._read_sheet_with_transformations()
            
            return {
                'success': True,
                'data': df,
                'message': f"Successfully retrieved {len(df)} costs as DataFrame"
            }
        except Exception as e:
            return {
                'success': False,
                'data': pd.DataFrame(),
                'message': f"Error retrieving costs DataFrame: {str(e)}"
            }
    
    def find_by_id(self, cost_id: int) -> Optional[Cost]:
        """Find cost by ID."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df['cost_id'] == cost_id]
        
        if filtered_df.empty:
            return None
        
        models = self._dataframe_to_models(filtered_df)
        return models[0] if models else None
    
    def find_by_project_id(self, project_id: str) -> List[Cost]:
        """Find costs by project ID."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df['project_id'] == str(project_id)]
        
        return self._dataframe_to_models(filtered_df)
    
    def find_by_proveedor(self, proveedor: str) -> List[Cost]:
        """Find costs by provider."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df['proveedor'].str.contains(proveedor, case=False, na=False)]
        
        return self._dataframe_to_models(filtered_df)
    
    def find_by_estado(self, estado: str) -> List[Cost]:
        """Find costs by status."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df['estado_costo'] == str(estado).lower()]
        
        return self._dataframe_to_models(filtered_df)
    
    def find_overdue(self) -> List[Cost]:
        """Find overdue costs."""
        df = self._read_sheet_with_transformations()
        today = pd.to_datetime(datetime.today())
        
        # Filter unpaid costs that are past due date
        overdue_df = df[
            (df['estado_costo'] != 'pagado') & 
            (pd.to_datetime(df['fecha_vencimiento'], errors='coerce') < today)
        ]
        
        return self._dataframe_to_models(overdue_df)
    
    def find_by_filters(self, filters: Dict[str, Any]) -> List[Cost]:
        """Find costs by multiple filters."""
        df = self._read_sheet_with_transformations()
        
        # Apply filters
        for key, value in filters.items():
            if value is not None and value != "" and key in df.columns:
                if isinstance(value, list):
                    df = df[df[key].isin(value)]
                else:
                    df = df[df[key] == value]
        
        return self._dataframe_to_models(df)
    
    def create(self, cost: Cost) -> int:
        """Create new cost and return the assigned ID."""
        # Get next ID
        next_id = self.sheets_repo.get_next_id(self.sheet_name)
        cost.cost_id = next_id
        
        # Prepare row values
        row_values = self._model_to_row_values(cost)
        
        # Append to sheet
        if self.sheets_repo._append_rows(self.sheet_name, [row_values]):
            return next_id
        else:
            raise Exception("Failed to create cost")
    
    def update(self, cost: Cost) -> bool:
        """Update existing cost."""
        if not cost.cost_id:
            raise ValueError("Cost ID is required for update")
        
        row_number = self.sheets_repo.find_row_by_id(self.sheet_name, str(cost.cost_id))
        if not row_number:
            return False
        
        # Get headers and prepare values
        headers = self.sheets_repo._get_headers(self.sheet_name)
        row_values = self._model_to_row_values(cost, headers)
        
        # Update the entire row
        range_name = f"{self.sheet_name}!A{row_number}:{self._get_last_column(len(headers))}{row_number}"
        return self.sheets_repo._write_range(range_name, [row_values])
    
    def update_fields(self, cost_id: int, updates: Dict[str, Any]) -> bool:
        """Update specific fields of a cost."""
        # Find the row
        row_number = self.sheets_repo.find_row_by_id(self.sheet_name, str(cost_id))
        if not row_number:
            return False
        
        # Get current data
        headers = self.sheets_repo._get_headers(self.sheet_name)
        range_name = f"{self.sheet_name}!A{row_number}:{self._get_last_column(len(headers))}{row_number}"
        current_values = self.sheets_repo._read_range(range_name)
        
        if not current_values:
            return False
        
        row_values = current_values[0]
        
        # Apply updates
        for field_name, new_value in updates.items():
            if field_name in headers:
                col_index = headers.index(field_name)
                if col_index < len(row_values):
                    row_values[col_index] = str(new_value) if new_value is not None else ""
        
        # Write back
        return self.sheets_repo._write_range(range_name, [row_values])
    
    def _read_sheet_with_transformations(self) -> pd.DataFrame:
        """Read costs sheet with all transformations applied."""
        values = self._read_range(self.range_name)
        df = self._values_to_dataframe(values)
        
        if df.empty:
            return df
        
        # Apply transformations
        df = self._apply_transformations(df)
        return df
    
    def _apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply cost-specific transformations."""
        try:
            # Ensure we have a proper DataFrame
            if df is None or df.empty:
                return df
            
            # Make a copy to avoid modifying the original
            df = df.copy()
            
            
            # Calculate derived fields safely
            if "estado_costo" in df.columns and len(df) > 0:
                df["is_paid"] = (df["estado_costo"] == "pagado")
            
            # Convert monetary amounts
            for col in ["importe_bruto", "importe_neto"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    
                    
                    # Process categorical columns - fix the string operations
            categorical_cols = ['estado_costo', 'tipo_costo', 'detalle_costo', 'moneda', 'proveedor' ]
            for col in categorical_cols:
                if col in df.columns and len(df) > 0:
                    # Ensure column exists and has data before applying string operations
                    # Fill NaN values with empty string first, then apply transformations
                    df[col] = df[col].fillna('').astype(str).str.strip().str.lower()
            
          
            
            return df
            
        except Exception as e:
            print(f"Error in _apply_transformations: {e}")
            import traceback
            traceback.print_exc()
            # Return the original DataFrame if transformations fail
            return df
    
    def _dataframe_to_models(self, df: pd.DataFrame) -> List[Cost]:
        """Convert DataFrame to list of Cost models."""
        models = []
        
        for _, row in df.iterrows():
            model_data = {
                'cost_id': row.get('cost_id'),
                'project_id': row.get('project_id'),
                'proveedor': row.get('proveedor'),
                'factura': row.get('factura'),
                'fecha_factura': row.get('fecha_factura'),
                'fecha_recepcion': row.get('fecha_recepcion'),
                'fecha_vencimiento': row.get('fecha_vencimiento'),
                'fecha_pago': row.get('fecha_pago'),
                'importe_bruto': row.get('importe_bruto'),
                'importe_neto': row.get('importe_neto'),
                'moneda': row.get('moneda'),
                'estado_costo': row.get('estado_costo'),
                'tipo_costo': row.get('tipo_costo'),
                'detalle_costo': row.get('detalle_costo'),
                'responsable_registro': row.get('responsable_registro'),
                'observaciones': row.get('observaciones'),
                'url_respaldo': row.get('url_respaldo')
            }
            
            # Clean None values and convert types
            cleaned_data = {}
            for k, v in model_data.items():
                if pd.isna(v):
                    cleaned_data[k] = None
                else:
                    cleaned_data[k] = v
            
            models.append(Cost.from_dict(cleaned_data))
        
        return models
    
    def _model_to_row_values(self, cost: Cost, headers: Optional[List[str]] = None) -> List[str]:
        """Convert Cost model to row values for Google Sheets."""
        if headers is None:
            headers = self.sheets_repo._get_headers(self.sheet_name)
        
        # Map model fields to sheet columns
        field_mapping = {
            'cost_id': cost.cost_id,
            'project_id': cost.project_id,
            'proveedor': cost.proveedor,
            'factura': cost.factura,
            'fecha_factura': cost.fecha_factura.isoformat() if cost.fecha_factura else "",
            'fecha_recepcion': cost.fecha_recepcion.isoformat() if cost.fecha_recepcion else "",
            'fecha_vencimiento': cost.fecha_vencimiento.isoformat() if cost.fecha_vencimiento else "",
            'fecha_pago': cost.fecha_pago.isoformat() if cost.fecha_pago else "",
            'importe_bruto': cost.importe_bruto,
            'importe_neto': cost.importe_neto,
            'moneda': cost.moneda,
            'estado_costo': cost.estado_costo,
            'tipo_costo': cost.tipo_costo,
            'detalle_costo': cost.detalle_costo,
            'responsable_registro': cost.responsable_registro,
            'observaciones': cost.observaciones,
            'url_respaldo': cost.url_respaldo
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
    
    def get_costs_summary(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get costs summary for analytics."""
        try:
            df = self._read_sheet_with_transformations()
            
            if project_id:
                df = df[df['project_id'] == project_id]
            
            if df.empty:
                return {
                    'total_costs': 0,
                    'paid_costs': 0,
                    'pending_costs': 0,
                    'overdue_costs': 0,
                    'total_amount': 0,
                    'paid_amount': 0,
                    'pending_amount': 0
                }
            
            total_costs = len(df)
            paid_costs = len(df[df['estado_costo'] == 'pagado'])
            pending_costs = len(df[df['estado_costo'] != 'pagado'])
            overdue_costs = len(df[df.get('days_overdue', 0) > 0])
            
            total_amount = df['importe_neto'].sum()
            paid_amount = df[df['estado_costo'] == 'pagado']['importe_neto'].sum()
            pending_amount = df[df['estado_costo'] != 'pagado']['importe_neto'].sum()
            
            return {
                'total_costs': total_costs,
                'paid_costs': paid_costs,
                'pending_costs': pending_costs,
                'overdue_costs': overdue_costs,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'pending_amount': pending_amount
            }
            
        except Exception as e:
            print(f"Error getting costs summary: {e}")
            return {
                'total_costs': 0,
                'paid_costs': 0,
                'pending_costs': 0,
                'overdue_costs': 0,
                'total_amount': 0,
                'paid_amount': 0,
                'pending_amount': 0
            }