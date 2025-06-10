"""
EDP Service for business logic related to EDP operations.
Compatible with Google Sheets architecture.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from ..repositories.edp_repository import EDPRepository
from ..repositories.log_repository import LogRepository
from . import BaseService, ServiceResponse, ValidationError, BusinessLogicError
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils


class EDPService(BaseService):
    """Service for managing EDP business logic using Google Sheets."""
    
    def __init__(self):
        super().__init__()
        self.edp_repository = EDPRepository()
        self.log_repository = LogRepository()
        self.date_utils = DateUtils()
        self.format_utils = FormatUtils()
    
    def get_all_edps(self) -> ServiceResponse:
        """Get all EDPs with enriched data."""
        try:
            edps_response = self.edp_repository.find_all_dataframe()
            
            if not edps_response.get("success", True):
                return ServiceResponse(
                    success=False,
                    message=f"Error retrieving EDPs: {edps_response.get('message', 'Unknown error')}"
                )
            
            df_edps = edps_response.get("data", pd.DataFrame())
            
            if df_edps.empty:
                return ServiceResponse(
                    success=True,
                    data=[],
                    message="No EDPs found"
                )
            
            # Convert to list of dictionaries
            edps_list = df_edps.to_dict('records')
            
            # Clean NaT values for JSON serialization
            edps_list = self._clean_nat_values(edps_list)
            
            return ServiceResponse(
                success=True,
                data=edps_list,
                message=f"Retrieved {len(edps_list)} EDPs successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving EDPs: {str(e)}"
            )
    
    def get_edp_by_id(self, edp_id: str) -> ServiceResponse:
        """Get a specific EDP with detailed information."""
        try:
            # Get all EDPs from repository
            edps_response = self.edp_repository.find_all_dataframe()
            
            if not edps_response.get("success", True):
                return ServiceResponse(
                    success=False,
                    message=f"Error retrieving EDPs: {edps_response.get('message', 'Unknown error')}"
                )
            
            df_edps = edps_response.get("data", pd.DataFrame())
            
            if df_edps.empty:
                return ServiceResponse(
                    success=False,
                    message="No EDPs found in the system"
                )
            
            # Filter by EDP ID
            edp_found = df_edps[df_edps["n_edp"] == str(edp_id)]
            
            if edp_found.empty:
                return ServiceResponse(
                    success=False,
                    message=f"EDP with ID {edp_id} not found"
                )
            
            # Get the first match and convert to dict
            edp_data = edp_found.iloc[0].to_dict()
            
            # Clean NaT values and format dates
            edp_data = self._clean_nat_values(edp_data)
            edp_data = self._format_edp_dates(edp_data)
            
            # Add calculated fields
            edp_data['row_index'] = edp_found.index[0] + 2  # +2 for header and 0-indexing
            
            return ServiceResponse(
                success=True,
                data=edp_data,
                message="EDP retrieved successfully"
            )
        except Exception as e:
            import traceback
            print(f"Error in get_edp_by_id: {str(e)}")
            print(traceback.format_exc())
            return ServiceResponse(
                success=False,
                message=f"Error retrieving EDP: {str(e)}"
            )
    
    def update_edp(self, edp_id: str, edp_data: Dict[str, Any], user: str = "Sistema") -> ServiceResponse:
        """Update an existing EDP using the repository."""
        try:
            # Use the repository's update method
            update_response = self.edp_repository.update_by_edp_id(edp_id, edp_data, user)
            
            if update_response.get("success", False):
                return ServiceResponse(
                    success=True,
                    data=update_response.get("data", {}),
                    message=update_response.get("message", "EDP updated successfully")
                )
            else:
                return ServiceResponse(
                    success=False,
                    message=update_response.get("message", "Failed to update EDP")
                )
        except Exception as e:
            import traceback
            print(f"Error in update_edp: {str(e)}")
            print(traceback.format_exc())
            return ServiceResponse(
                success=False,
                message=f"Error updating EDP: {str(e)}"
            )
    
    def get_edp_statistics(self) -> ServiceResponse:
        """Get overall EDP statistics."""
        try:
            edps_response = self.edp_repository.find_all_dataframe()
            
            if not edps_response.get("success", True):
                return ServiceResponse(
                    success=False,
                    message=f"Error retrieving EDPs for statistics: {edps_response.get('message', 'Unknown error')}"
                )
            
            df_edps = edps_response.get("data", pd.DataFrame())
            
            if df_edps.empty:
                statistics = {
                    'total_edps': 0,
                    'status_distribution': {},
                    'by_responsible': {},
                    'by_month': {},
                    'total_amount': 0
                }
            else:
                statistics = {
                    'total_edps': len(df_edps),
                    'status_distribution': df_edps['estado'].value_counts().to_dict() if 'estado' in df_edps.columns else {},
                    'by_responsible': df_edps['jefe_proyecto'].value_counts().to_dict() if 'jefe_proyecto' in df_edps.columns else {},
                    'by_month': df_edps['mes'].value_counts().to_dict() if 'mes' in df_edps.columns else {},
                    'total_amount': df_edps['monto_aprobado'].sum() if 'monto_aprobado' in df_edps.columns else 0
                }
            
            return ServiceResponse(
                success=True,
                data=statistics,
                message="Statistics retrieved successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving statistics: {str(e)}"
            )
    
    def _clean_nat_values(self, data):
        """
        Limpia valores NaT (Not a Time) de pandas convirtiéndolos en None
        para que puedan ser serializados a JSON.
        """
        if isinstance(data, list):
            return [self._clean_nat_values(item) for item in data]
        
        if not isinstance(data, dict):
            if pd.isna(data) or str(data) == "NaT":
                return None
            return data
        
        result = {}
        for key, value in data.items():
            if pd.isna(value) or str(value) == "NaT":
                result[key] = None
            elif isinstance(value, dict):
                result[key] = self._clean_nat_values(value)
            elif isinstance(value, list):
                result[key] = [
                    self._clean_nat_values(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    def _format_edp_dates(self, edp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format date fields for template display."""
        date_fields = [
            'fecha_emision', 'fecha_envio_cliente', 'fecha_estimada_pago', 
            'fecha_conformidad', 'fecha_registro'
        ]
        
        for field in date_fields:
            if field in edp_data and edp_data[field] is not None:
                try:
                    # If it's already a string in the right format, keep it
                    if isinstance(edp_data[field], str) and len(edp_data[field]) == 10:
                        edp_data[f"{field}_str"] = edp_data[field]
                    # If it's a pandas Timestamp or datetime, format it
                    elif hasattr(edp_data[field], 'strftime'):
                        edp_data[f"{field}_str"] = edp_data[field].strftime('%Y-%m-%d')
                    else:
                        # Try to parse and format
                        parsed_date = pd.to_datetime(edp_data[field], errors='coerce')
                        if pd.notna(parsed_date):
                            edp_data[f"{field}_str"] = parsed_date.strftime('%Y-%m-%d')
                        else:
                            edp_data[f"{field}_str"] = ""
                except Exception:
                    edp_data[f"{field}_str"] = ""
            else:
                edp_data[f"{field}_str"] = ""
        
        return edp_data
