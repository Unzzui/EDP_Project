"""
Repository for EDP (Estado de Pago) data access.
"""

from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import logging
import traceback

from . import BaseRepository, SheetsRepository
from ..models import EDP
from ..utils.date_utils import parse_date_safe
from ..utils.format_utils import clean_numeric_value
from ..utils.gsheet import update_row, log_cambio_edp
from ..config import get_config
import numpy as np
from ..services.cache_invalidation_service import invalidate_cache_on_change

logger = logging.getLogger(__name__)


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
                "success": True,
                "data": models,
                "message": f"Successfully retrieved {len(models)} EDPs",
            }
        except Exception as e:
            return {
                "success": False,
                "data": [],
                "message": f"Error retrieving EDPs: {str(e)}",
            }

    def find_all_dataframe(self, apply_filters: bool = True) -> Dict[str, Any]:
        """Get all EDPs as DataFrame for analytics purposes."""
        try:
            df = self._read_sheet_with_transformations()

            return {
                "success": True,
                "data": df,
                "message": f"Successfully retrieved {len(df)} EDPs as DataFrame",
            }
        except Exception as e:
            return {
                "success": False,
                "data": pd.DataFrame(),
                "message": f"Error retrieving EDPs DataFrame: {str(e)}",
            }

    def find_by_id(self, edp_id: int) -> Optional[EDP]:
        """Find EDP by ID."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df["id"] == edp_id]

        if filtered_df.empty:
            return None

        models = self._dataframe_to_models(filtered_df)
        return models[0] if models else None

    def find_by_n_edp(self, n_edp: str) -> Optional[EDP]:
        """Find EDP by N° EDP."""
        df = self._read_sheet_with_transformations()
        filtered_df = df[df["n_edp"] == str(n_edp)]

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
    
    def create_bulk(self, edps: List[EDP]) -> Dict[str, Any]:
        """Create multiple EDPs in bulk for better performance."""
        try:
            if not edps:
                return {"success": True, "created_ids": [], "message": "No EDPs to create"}
            
            # Get starting ID
            next_id = self.sheets_repo.get_next_id(self.sheet_name)
            created_ids = []
            
            # Prepare all rows
            rows = []
            for i, edp in enumerate(edps):
                edp.id = next_id + i
                row_values = self._model_to_row_values(edp)
                rows.append(row_values)
                created_ids.append(edp.id)
            
            # Bulk insert
            if self.sheets_repo._append_rows(self.sheet_name, rows):
                return {
                    "success": True,
                    "created_ids": created_ids,
                    "message": f"Successfully created {len(created_ids)} EDPs"
                }
            else:
                return {
                    "success": False,
                    "created_ids": [],
                    "message": "Failed to create EDPs in bulk"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk create: {e}")
            return {
                "success": False,
                "created_ids": [],
                "message": f"Error creating EDPs: {str(e)}"
            }

    @invalidate_cache_on_change('edp_updated', ['edps'])
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

    @invalidate_cache_on_change('edp_updated', ['edps'])
    def update_fields(self, edp_id: int, updates: Dict[str, Any]) -> bool:
        """Update specific fields of an EDP."""
        try:
            print(f"🔍 update_fields called with:")
            print(f"   - edp_id: {edp_id} (type: {type(edp_id)})")
            print(f"   - updates: {updates}")
            
            # Convert edp_id to string for comparison with n_edp
            edp_id_str = str(edp_id)
            
            # Find the row by n_edp (column B) instead of id (column A)
            row_number = self.sheets_repo.find_row_by_id(self.sheet_name, edp_id_str, id_column="B")
            print(f"   - row_number found (searching n_edp in column B): {row_number}")
            
            if not row_number:
                print(f"❌ Row not found for n_edp: {edp_id_str}")
                return False

            # Get current data
            headers = self.sheets_repo._get_headers(self.sheet_name)
            print(f"   - headers count: {len(headers)}")
            
            if not headers:
                print(f"❌ No headers found for sheet: {self.sheet_name}")
                return False

            # Read the specific row directly using Google Sheets API (bypass read_sheet function)
            range_name = f"{self.sheet_name}!A{row_number}:{self._get_last_column(len(headers))}{row_number}"
            print(f"   - range_name: {range_name}")
            
            try:
                config = get_config()
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=config.SHEET_ID,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                print(f"   - direct API values: {values}")
                
                if not values or not values[0]:
                    print(f"❌ No current values found for range: {range_name}")
                    return False

                row_values = values[0]
                
                # Ensure row_values has same length as headers
                while len(row_values) < len(headers):
                    row_values.append('')
                    
            except Exception as api_error:
                print(f"❌ Error reading row directly from API: {api_error}")
                return False

            # Apply updates
            for field_name, new_value in updates.items():
                if field_name in headers:
                    col_index = headers.index(field_name)
                    if col_index < len(row_values):
                        old_value = row_values[col_index]
                        row_values[col_index] = (
                            str(new_value) if new_value is not None else ""
                        )
                        print(f"   - Updated {field_name}: '{old_value}' → '{new_value}'")
                    else:
                        print(f"⚠️  Column index {col_index} out of range for {field_name}")
                else:
                    print(f"⚠️  Field '{field_name}' not found in headers")

            # Write back
            result = self.sheets_repo._write_range(range_name, [row_values])
            print(f"   - Write result: {result}")
            return result
            
        except Exception as e:
            print(f"💥 Exception in update_fields: {e}")
            print(traceback.format_exc())
            return False

    @invalidate_cache_on_change('edp_updated', ['edps'])
    def update_by_edp_id(self, n_edp: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update EDP by n_edp using form data and log changes."""
        try:
            
            # Get all EDPs to find the specific one
            edps_response = self.find_all_dataframe()
            
            if not edps_response.get("success", True):
                return {
                    "success": False,
                    "message": f"Error retrieving EDPs: {edps_response.get('message', 'Unknown error')}"
                }
            
            df_edps = edps_response.get("data", pd.DataFrame())
            
            if df_edps.empty:
                return {
                    "success": False,
                    "message": "No EDPs found in the system"
                }
            
            # Find EDP by n_edp
            edp_found = df_edps[df_edps["n_edp"] == str(n_edp)]
            
            if edp_found.empty:
                return {
                    "success": False,
                    "message": f"EDP with ID {n_edp} not found"
                }
            
            # Get row number (add 2 for header and 0-based indexing)
            row_index = edp_found.index[0]
            row_number = row_index + 2
            
            # Get current EDP data
            current_edp = edp_found.iloc[0].to_dict()
        
            
            # Prepare updates dictionary
            updates = {}
            
            # Map form fields to database fields
            field_mapping = {
                'estado': 'estado',
                'estado_detallado': 'estado_detallado',
                'conformidad_enviada': 'conformidad_enviada',
                'fecha_conformidad': 'fecha_conformidad',
                'motivo_no_aprobado': 'motivo_no_aprobado',
                'tipo_falla': 'tipo_falla',
                'observaciones': 'observaciones',
                'monto_propuesto': 'monto_propuesto',
                'monto_aprobado': 'monto_aprobado',
                'n_conformidad': 'n_conformidad',
                'fecha_estimada_pago': 'fecha_estimada_pago',
                'fecha_emision': 'fecha_emision'
            }
            
            # Process form data and track changes
            changes = []
            
            for form_field, db_field in field_mapping.items():
                if form_field in form_data:
                    new_value = form_data[form_field]
                    
                    # Clean and format the new value
                    if new_value == "":
                        new_value = None
                    
                    # Get current value
                    current_value = current_edp.get(db_field)
                    
                    # Convert current value for comparison
                    if pd.isna(current_value):
                        current_value = None
                    elif isinstance(current_value, str):
                        current_value = current_value.strip()
                    

                    
                    # Improved comparison logic
                    values_different = False
                    
                    # Handle None values
                    if current_value is None and new_value is None:
                        values_different = False
                    elif current_value is None or new_value is None:
                        values_different = True
                    else:
                        # Both values are not None, compare as strings
                        current_str = str(current_value).strip()
                        new_str = str(new_value).strip()
                        values_different = current_str != new_str
                    
                    if values_different:
                        updates[db_field] = new_value
                        changes.append({
                            'campo': db_field,
                            'antes': current_value,
                            'despues': new_value
                        })
            
            # If there are no changes, return success
            if not updates:
                return {
                    "success": True,
                    "message": "No changes detected"
                }
            
            # Update the sheet using gsheet utility
            success = update_row(row_number, updates, sheet_name="edp")
            
            if success:
                # Log changes
                for change in changes:
                    log_cambio_edp(
                        n_edp=n_edp,
                        proyecto=current_edp.get('proyecto', ''),
                        campo=change['campo'],
                        antes=change['antes'],
                        despues=change['despues']
                    )
                
                return {
                    "success": True,
                    "message": f"EDP {n_edp} updated successfully",
                    "data": {
                        "updated_fields": list(updates.keys()),
                        "changes_count": len(changes)
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update EDP in Google Sheets"
                }
                
        except Exception as e:
            import traceback
            print(f"Error in update_by_edp_id: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "message": f"Error updating EDP: {str(e)}"
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
        """Apply EDP-specific transformations."""
        try:
            hoy = pd.to_datetime(datetime.today())

            # Ensure we have a proper DataFrame
            if df is None or df.empty:
                return df

            # Convert ID to numeric
            if "id" in df.columns:
                df["id"] = pd.to_numeric(df["id"], errors="coerce")

            # Convert monetary amounts
            for col in ["monto_propuesto", "monto_aprobado"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Process categorical columns - fix the string operations
            categorical_cols = [
                "estado",
                "estado_detallado",
                "motivo_no_aprobado",
                "tipo_falla",
            ]
            for col in categorical_cols:
                if col in df.columns and len(df) > 0:
                    # Ensure column exists and has data before applying string operations
                    # Fill NaN values with empty string first, then apply transformations
                    df[col] = df[col].fillna("").astype(str).str.strip().str.lower()

            # Process dates
            date_cols = [
                "fecha_emision",
                "fecha_envio_cliente",
                "fecha_estimada_pago",
                "fecha_conformidad",
                "fecha_registro",
            ]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Calculate waiting days
            if "fecha_envio_cliente" in df.columns and len(df) > 0:
                fecha_envio = pd.to_datetime(df["fecha_envio_cliente"], errors="coerce")
                if "fecha_conformidad" in df.columns:
                    fecha_conformidad = pd.to_datetime(
                        df["fecha_conformidad"], errors="coerce"
                    )
                    df["dias_espera"] = (
                        fecha_conformidad.fillna(hoy) - fecha_envio
                    ).dt.days
                else:
                    df["dias_espera"] = (hoy - fecha_envio).dt.days

            if "fecha_envio_cliente" in df.columns and len(df) > 0:
                df["fecha_envio_cliente"] = pd.to_datetime(
                    df["fecha_envio_cliente"], errors="coerce"
                )
                df["fecha_conformidad"] = pd.to_datetime(
                    df.get("fecha_conformidad", pd.NaT), errors="coerce"
                )
                hoy = pd.Timestamp.today()

                df["fecha_final"] = df["fecha_conformidad"].fillna(hoy)

                # Asegúrate de que ambas fechas no sean NaT
                mask_validas = (~df["fecha_envio_cliente"].isna()) & (
                    ~df["fecha_final"].isna()
                )

                df.loc[mask_validas, "dias_habiles"] = df.loc[mask_validas].apply(
                    lambda row: np.busday_count(
                        row["fecha_envio_cliente"].date(), row["fecha_final"].date()
                    ),
                    axis=1,
                )

            # Calculate critical status
            if "dias_espera" in df.columns and len(df) > 0:
                dias_espera_numeric = pd.to_numeric(df["dias_espera"], errors="coerce")
                estado_not_final = ~df["estado"].isin(["validado", "pagado"])
                df["critico"] = (dias_espera_numeric > 30) & estado_not_final

            # Calculate validation status
            if (
                "estado" in df.columns
                and "conformidad_enviada" in df.columns
                and len(df) > 0
            ):
                df["validado"] = (df["estado"].isin(["validado", "pagado"])) & (
                    df["conformidad_enviada"] == "Sí"
                )

            return df

        except Exception as e:
            logger.error(f"Error in _apply_transformations: {e}")
            # Return the original DataFrame if transformations fail
            return df

    def _dataframe_to_models(self, df: pd.DataFrame) -> List[EDP]:
        """Convert DataFrame to list of EDP models."""
        models = []

        for i, row in df.iterrows():
            model_data = {
                "id": row.get("id"),
                "n_edp": row.get("n_edp"),
                "proyecto": row.get("proyecto"),
                "cliente": row.get("cliente"),
                "estado": row.get("estado"),
                "estado_detallado": row.get("estado_detallado"),
                "jefe_proyecto": row.get("jefe_proyecto"),
                "gestor": row.get("gestor"),
                "mes": row.get("mes"),
                "monto_propuesto": row.get("monto_propuesto"),
                "monto_aprobado": row.get("monto_aprobado"),
                "fecha_emision": row.get("fecha_emision"),
                "fecha_envio_cliente": row.get("fecha_envio_cliente"),
                "fecha_estimada_pago": row.get("fecha_estimada_pago"),
                "fecha_conformidad": row.get("fecha_conformidad"),
                "conformidad_enviada": row.get("conformidad_enviada"),
                "n_conformidad": row.get("n_conformidad"),
                "registrado_por": row.get("registrado_por"),
                "fecha_registro": row.get("fecha_registro"),
                "motivo_no_aprobado": row.get("motivo_no_aprobado"),
                "tipo_falla": row.get("tipo_falla"),
                "critico": row.get("critico"),
                "dias_espera": row.get("dias_espera"),
                "dias_habiles": row.get("dias_habiles"),
                "observaciones": row.get("observaciones"),
            }

            # Clean None values and convert types properly
            cleaned_data = {}
            for k, v in model_data.items():
                if pd.isna(v) or v is None:
                    cleaned_data[k] = None
                elif isinstance(v, pd.Series):
                    # Handle pandas Series objects
                    if v.empty:
                        cleaned_data[k] = None
                    else:
                        val = v.iloc[0] if len(v) > 0 else None
                        cleaned_data[k] = None if pd.isna(val) else val
                else:
                    # Convert scalar values, handle boolean conversion properly
                    if k in ["critico"] and v is not None:
                        # Handle different data types for boolean fields
                        if isinstance(v, bool):
                            cleaned_data[k] = v
                        elif isinstance(v, (int, float)):
                            cleaned_data[k] = bool(v)
                        elif isinstance(v, str):
                            cleaned_data[k] = str(v).lower() in [
                                "true",
                                "1",
                                "yes",
                                "sí",
                                "si",
                                "verdadero",
                            ]
                        else:
                            # For any other type, try to convert to string first
                            try:
                                str_val = str(v)
                                cleaned_data[k] = str_val.lower() in [
                                    "true",
                                    "1",
                                    "yes",
                                    "sí",
                                    "si",
                                    "verdadero",
                                ]
                            except:
                                cleaned_data[k] = bool(v) if v is not None else False
                    else:
                        cleaned_data[k] = v

            logger.debug(f"Row {i} cleaned_data keys: {list(cleaned_data.keys())}")
            logger.debug(
                f"Row {i} cleaned_data sample: {dict(list(cleaned_data.items())[:5])}"
            )

            try:
                model = EDP.from_dict(cleaned_data)
                models.append(model)
                logger.debug(f"Successfully created model for row {i}")
            except Exception as e:
                logger.debug(f"Error creating model for row {i}: {e}")
                logger.debug(f"Problematic data: {cleaned_data}")
                # Print detailed type information to debug further
                for key, value in cleaned_data.items():
                    logger.debug(f"{key}: {type(value)} = {value}")

        logger.debug(f"Total models created: {len(models)}")
        return models

    def _model_to_row_values(
        self, edp: EDP, headers: Optional[List[str]] = None
    ) -> List[str]:
        """Convert EDP model to row values for Google Sheets."""
        if headers is None:
            headers = self.sheets_repo._get_headers(self.sheet_name)

        # Map model fields to sheet columns (now using lowercase names)
        field_mapping = {
            "id": edp.id,
            "n_edp": edp.n_edp,
            "proyecto": edp.proyecto,
            "cliente": edp.cliente,
            "estado": edp.estado,
            "estado_detallado": edp.estado_detallado,
            "jefe_proyecto": edp.jefe_proyecto,
            "gestor": edp.gestor,
            "mes": edp.mes,
            "monto_propuesto": edp.monto_propuesto,
            "monto_aprobado": edp.monto_aprobado,
            "fecha_emision": edp.fecha_emision.isoformat() if edp.fecha_emision else "",
            "fecha_envio_cliente": (
                edp.fecha_envio_cliente.isoformat() if edp.fecha_envio_cliente else ""
            ),
            "fecha_estimada_pago": (
                edp.fecha_estimada_pago.isoformat() if edp.fecha_estimada_pago else ""
            ),
            "fecha_conformidad": (
                edp.fecha_conformidad.isoformat() if edp.fecha_conformidad else ""
            ),
            "conformidad_enviada": edp.conformidad_enviada,
            "n_conformidad": edp.n_conformidad,
            "registrado_por": edp.registrado_por,
            "fecha_registro": (
                edp.fecha_registro.isoformat() if edp.fecha_registro else ""
            ),
            "motivo_no_aprobado": edp.motivo_no_aprobado,
            "tipo_falla": edp.tipo_falla,
            "observaciones": edp.observaciones,
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
