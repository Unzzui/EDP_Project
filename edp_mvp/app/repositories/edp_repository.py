"""
Repository for EDP (Estado de Pago) data access.
"""
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

from . import BaseRepository, SheetsRepository
from ..models import EDP
from ..utils.date_utils import parse_date_safe
from ..utils.format_utils import clean_numeric_value


class EDPRepository(BaseRepository):
    """Repository for EDP operations."""
    
    def __init__(self):
        super().__init__()
        self.sheets_repo = SheetsRepository()
        self.sheet_name = "edp"
        self.range_name = "edp!A:V"
    
    def find_all(self, apply_filters: bool = True) -> Dict[str, Any]:
        """Get all EDPs with optional transformations."""
        try:
            df = self._read_sheet_with_transformations()
            models = self._dataframe_to_models(df)
            
            return {
                'success': True,
                'data': models,
                'message': f"Successfully retrieved {len(models)} EDPs"
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'message': f"Error retrieving EDPs: {str(e)}"
            }
    
    def find_all_dataframe(self, apply_filters: bool = True) -> Dict[str, Any]:
        """Get all EDPs as DataFrame for analytics purposes."""
        try:
            df = self._read_sheet_with_transformations()
            
            return {
                'success': True,
                'data': df,
                'message': f"Successfully retrieved {len(df)} EDPs as DataFrame"
            }
        except Exception as e:
            return {
                'success': False,
                'data': pd.DataFrame(),
                'message': f"Error retrieving EDPs DataFrame: {str(e)}"
            }
    
    
    def find_by_id(self, edp_id: int) -> Optional[EDP]:
        """Find EDP by ID."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df['id'] == edp_id]
        
        if filtered_df.empty:
            return None
        
        models = self._dataframe_to_models(filtered_df)
        return models[0] if models else None
    
    def find_by_n_edp(self, n_edp: str) -> Optional[EDP]:
        """Find EDP by N° EDP."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df['n_edp'] == str(n_edp)]
        
        if filtered_df.empty:
            return None
        
        models = self._dataframe_to_models(filtered_df)
        return models[0] if models else None
    
    def find_by_filters(self, filters: Dict[str, Any]) -> List[EDP]:
        """Find EDPs by multiple filters."""
        df = self._read_sheet_with_transformations()
        
        # Apply filters
        for key, value in filters.items():
            if value is not None and value != "" and key in df.columns:
                if isinstance(value, list):
                    df = df[df[key].isin(value)]
                else:
                    df = df[df[key] == value]
        
        return self._dataframe_to_models(df)
    
    def create(self, edp: EDP) -> int:
        """Create new EDP and return the assigned ID."""
        # Get next ID
        next_id = self.sheets_repo.get_next_id(self.sheet_name)
        edp.id = next_id
        
        # Prepare row values
        row_values = self._model_to_row_values(edp)
        
        # Append to sheet
        if self.sheets_repo._append_rows(self.sheet_name, [row_values]):
            return next_id
        else:
            raise Exception("Failed to create EDP")
    
    def update(self, edp: EDP) -> bool:
        """Update existing EDP."""
        if not edp.id:
            raise ValueError("EDP ID is required for update")
        
        row_number = self.sheets_repo.find_row_by_id(self.sheet_name, str(edp.id))
        if not row_number:
            return False
        
        # Get headers and prepare values
        headers = self.sheets_repo._get_headers(self.sheet_name)
        row_values = self._model_to_row_values(edp, headers)
        
        # Update the entire row
        range_name = f"{self.sheet_name}!A{row_number}:{self._get_last_column(len(headers))}{row_number}"
        return self.sheets_repo._write_range(range_name, [row_values])
    
    def update_fields(self, edp_id: int, updates: Dict[str, Any]) -> bool:
        """Update specific fields of an EDP."""
        # Find the row
        row_number = self.sheets_repo.find_row_by_id(self.sheet_name, str(edp_id))
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
        """Read EDP sheet with all transformations applied."""
        values = self._read_range(self.range_name)
        df = self._values_to_dataframe(values)
        
        if df.empty:
            return df
        
        # Apply transformations
        df = self._apply_transformations(df)
        return df
    
    def _apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply EDP-specific transformations."""
        try:
            hoy = pd.to_datetime(datetime.today())
            
            # Ensure we have a proper DataFrame
            if df is None or df.empty:
                return df
            
            # Convert ID to numeric
            if 'id' in df.columns:
                df['id'] = pd.to_numeric(df['id'], errors='coerce')
            
            # Convert monetary amounts
            for col in ["monto_propuesto", "monto_aprobado"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Process categorical columns - fix the string operations
            categorical_cols = ['estado', 'estado_detallado', 'motivo_no_aprobado', 'tipo_falla']
            for col in categorical_cols:
                if col in df.columns and len(df) > 0:
                    # Ensure column exists and has data before applying string operations
                    # Fill NaN values with empty string first, then apply transformations
                    df[col] = df[col].fillna('').astype(str).str.strip().str.lower()
            
            # Process dates
            date_cols = [
                "fecha_emision", "fecha_envio_cliente", "fecha_estimada_pago",
                "fecha_conformidad", "fecha_registro"
            ]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            
            # Calculate derived fields
            if "estado" in df.columns and len(df) > 0:
                df["validado"] = df["estado"] == "validado"
            
            # Calculate waiting days
            if "fecha_envio_cliente" in df.columns and len(df) > 0:
                fecha_envio = pd.to_datetime(df["fecha_envio_cliente"], errors='coerce')
                if "fecha_conformidad" in df.columns:
                    fecha_conformidad = pd.to_datetime(df["fecha_conformidad"], errors='coerce')
                    df["dias_espera"] = (fecha_conformidad.fillna(hoy) - fecha_envio).dt.days
                else:
                    df["dias_espera"] = (hoy - fecha_envio).dt.days
            
            # Calculate critical status
            if "dias_espera" in df.columns and len(df) > 0:
                df["critico"] = (
                    (pd.to_numeric(df["dias_espera"], errors="coerce") > 30)
                    & (~df["estado"].isin(["validado", "pagado"]))
                )
            return df
    
        except Exception as e:
            print(f"Error in _apply_transformations: {e}")
            # Return the original DataFrame if transformations fail
            return df
    
    def _dataframe_to_models(self, df: pd.DataFrame) -> List[EDP]:
        """Convert DataFrame to list of EDP models."""
        models = []
        
        for _, row in df.iterrows():
            model_data = {
                'id': row.get('id'),
                'n_edp': row.get('n_edp'),
                'proyecto': row.get('proyecto'),
                'cliente': row.get('cliente'),
                'estado': row.get('estado'),
                'estado_detallado': row.get('estado_detallado'),
                'jefe_proyecto': row.get('jefe_proyecto'),
                'gestor': row.get('gestor'),
                'mes': row.get('mes'),
                'monto_propuesto': row.get('monto_propuesto'),
                'monto_aprobado': row.get('monto_aprobado'),
                'fecha_emision': row.get('fecha_emision'),
                'fecha_envio_cliente': row.get('fecha_envio_cliente'),
                'fecha_estimada_pago': row.get('fecha_estimada_pago'),
                'fecha_conformidad': row.get('fecha_conformidad'),
                'conformidad_enviada': row.get('conformidad_enviada'),
                'n_conformidad': row.get('n_conformidad'),
                'registrado_po': row.get('registrado_po'),
                'fecha_registro': row.get('fecha_registro'),
                'motivo_no_aprobado': row.get('motivo_no_aprobado'),
                'tipo_falla': row.get('tipo_falla'),
                'validado': row.get('validado'),
                'critico': row.get('critico'),
                'dias_espera': row.get('dias_espera'),
                'dias_habiles': row.get('dias_habiles'),
                'observaciones': row.get('observaciones')
            }
            
            # Clean None values and convert types
            cleaned_data = {}
            for k, v in model_data.items():
                if pd.isna(v):
                    cleaned_data[k] = None
                else:
                    cleaned_data[k] = v
            
            models.append(EDP.from_dict(cleaned_data))
        
        return models
    
    def _model_to_row_values(self, edp: EDP, headers: Optional[List[str]] = None) -> List[str]:
        """Convert EDP model to row values for Google Sheets."""
        if headers is None:
            headers = self.sheets_repo._get_headers(self.sheet_name)
        
        # Map model fields to sheet columns (now using lowercase names)
        field_mapping = {
            'id': edp.id,
            'n_edp': edp.n_edp,
            'proyecto': edp.proyecto,
            'cliente': edp.cliente,
            'estado': edp.estado,
            'estado_detallado': edp.estado_detallado,
            'jefe_proyecto': edp.jefe_proyecto,
            'gestor': edp.gestor,
            'mes': edp.mes,
            'monto_propuesto': edp.monto_propuesto,
            'monto_aprobado': edp.monto_aprobado,
            'fecha_emision': edp.fecha_emision.isoformat() if edp.fecha_emision else "",
            'fecha_envio_cliente': edp.fecha_envio_cliente.isoformat() if edp.fecha_envio_cliente else "",
            'fecha_estimada_pago': edp.fecha_estimada_pago.isoformat() if edp.fecha_estimada_pago else "",
            'fecha_conformidad': edp.fecha_conformidad.isoformat() if edp.fecha_conformidad else "",
            'conformidad_enviada': edp.conformidad_enviada,
            'n_conformidad': edp.n_conformidad,
            'registrado_po': edp.registrado_po,
            'fecha_registro': edp.fecha_registro.isoformat() if edp.fecha_registro else "",
            'motivo_no_aprobado': edp.motivo_no_aprobado,
            'tipo_falla': edp.tipo_falla,
            'observaciones': edp.observaciones
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
