"""
Kanban Service for managing board operations and data processing.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from . import BaseService, ServiceResponse, ValidationError
from ..models import EDP
from ..repositories.edp_repository import EDPRepository
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils
from ..utils.validation_utils import ValidationUtils


class KanbanService(BaseService):
    """Service for handling Kanban board operations."""
    
    def __init__(self):
        super().__init__()
        self.edp_repo = EDPRepository()
        
    def get_kanban_data(self, filters: Dict[str, Any] = None) -> ServiceResponse:
        """Get data for Kanban board view."""
        try:
            # Get EDPs data
            edps_response = self.edp_repo.get_all()
            if not edps_response.success:
                return ServiceResponse(
                    success=False,
                    message="Failed to load EDPs data",
                    data=None
                )
            
            df = edps_response.data
            original_count = len(df)
            
            # Apply filters
            df = self._apply_kanban_filters(df, filters or {})
            
            # Remove old validated EDPs unless explicitly requested
            if not filters.get('mostrar_validados_antiguos', False):
                df = self._filter_old_validated_edps(df)
            
            # Group EDPs by status
            columns = self._group_edps_by_status(df)
            
            # Generate statistics
            statistics = self._calculate_kanban_statistics(df, original_count)
            
            # Get filter options
            filter_options = self._get_filter_options(df)
            
            return ServiceResponse(
                success=True,
                data={
                    'columns': columns,
                    'statistics': statistics,
                    'filter_options': filter_options,
                    'filters': filters or {}
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error loading Kanban data: {str(e)}",
                data=None
            )
    
    def update_edp_status(self, edp_id: str, new_status: str, 
                         additional_data: Dict[str, Any] = None) -> ServiceResponse:
        """Update EDP status in Kanban board."""
        try:
            # Validate input
            if not edp_id or not new_status:
                return ServiceResponse(
                    success=False,
                    message="EDP ID and new status are required",
                    data=None
                )
            
            # Get current EDP data
            edp_response = self.edp_repo.get_by_id(edp_id)
            if not edp_response.success:
                return ServiceResponse(
                    success=False,
                    message=f"EDP {edp_id} not found",
                    data=None
                )
            
            current_edp = edp_response.data
            
            # Prepare updates
            updates = {"Estado": new_status}
            
            # Apply business rules
            if new_status.lower() in ["pagado", "validado"]:
                updates["Conformidad Enviada"] = "Sí"
            
            # Add additional data if provided
            if additional_data:
                updates.update(additional_data)
            
            # Validate updates
            validation_result = ValidationUtils.validate_edp_update(updates)
            if not validation_result['valid']:
                return ServiceResponse(
                    success=False,
                    message=f"Validation failed: {', '.join(validation_result['errors'])}",
                    data=None
                )
            
            # Update EDP
            update_response = self.edp_repo.update(edp_id, updates)
            if not update_response.success:
                return ServiceResponse(
                    success=False,
                    message=f"Failed to update EDP: {update_response.message}",
                    data=None
                )
            
            return ServiceResponse(
                success=True,
                message=f"EDP {edp_id} updated successfully",
                data={
                    'edp_id': edp_id,
                    'old_status': current_edp.estado,
                    'new_status': new_status,
                    'updates': updates
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error updating EDP status: {str(e)}",
                data=None
            )
    
    def _apply_kanban_filters(self, df: pd.DataFrame, 
                            filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to DataFrame."""
        filtered_df = df.copy()
        
        if filters.get('mes'):
            filtered_df = filtered_df[filtered_df['Mes'] == filters['mes']]
        
        if filters.get('encargado'):
            filtered_df = filtered_df[filtered_df['Jefe de Proyecto'] == filters['encargado']]
        
        if filters.get('cliente'):
            filtered_df = filtered_df[filtered_df['Cliente'] == filters['cliente']]
        
        if filters.get('estado_detallado'):
            filtered_df = filtered_df[filtered_df['Estado Detallado'] == filters['estado_detallado']]
        
        return filtered_df
    
    def _filter_old_validated_edps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out old validated EDPs (>10 days)."""
        cutoff_date = datetime.now() - timedelta(days=10)
        
        # Create mask for old validated EDPs
        old_validated_mask = (
            (df['Estado'] == 'validado') & 
            (pd.notna(df['Fecha Conformidad'])) & 
            (pd.to_datetime(df['Fecha Conformidad'], errors='coerce') < cutoff_date)
        )
        
        # Return DataFrame without old validated EDPs
        return df[~old_validated_mask]
    
    def _group_edps_by_status(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Group EDPs by status for Kanban columns."""
        status_columns = ["revisión", "enviado", "pagado", "validado"]
        columns = {status: [] for status in status_columns}
        
        # Convert numeric columns
        for col in ["Monto Propuesto", "Monto Aprobado"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        for _, row in df.iterrows():
            status = row.get("Estado", "").lower()
            if status in columns:
                item = self._prepare_kanban_item(row)
                columns[status].append(item)
        
        return columns
    
    def _prepare_kanban_item(self, row: pd.Series) -> Dict[str, Any]:
        """Prepare a single EDP item for Kanban display."""
        item = row.to_dict()
        
        # Calculate days until payment
        try:
            if pd.notna(row.get("Fecha Estimada de Pago")):
                payment_date = pd.to_datetime(row["Fecha Estimada de Pago"])
                item["dias_para_pago"] = (payment_date - datetime.now()).days
            else:
                item["dias_para_pago"] = None
        except Exception:
            item["dias_para_pago"] = None
        
        # Calculate amount difference
        try:
            proposed = row.get("Monto Propuesto", 0) or 0
            approved = row.get("Monto Aprobado", 0) or 0
            
            if proposed > 0 and approved > 0:
                item["diferencia_montos"] = approved - proposed
                item["porcentaje_diferencia"] = (item["diferencia_montos"] / proposed * 100)
            else:
                item["diferencia_montos"] = 0
                item["porcentaje_diferencia"] = 0
        except Exception:
            item["diferencia_montos"] = 0
            item["porcentaje_diferencia"] = 0
        
        # Check if critical
        item["es_critico"] = bool(row.get("Crítico", False))
        
        # Check if old validated
        if row.get("Estado") == "validado" and pd.notna(row.get("Fecha Conformidad")):
            try:
                conformity_date = pd.to_datetime(row["Fecha Conformidad"])
                days_since_conformity = (datetime.now() - conformity_date).days
                item["antiguedad_validado"] = "antiguo" if days_since_conformity > 10 else "reciente"
            except Exception:
                item["antiguedad_validado"] = "reciente"
        
        # Clean NaT values
        item = self._clean_nat_values(item)
        
        return item
    
    def _clean_nat_values(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean NaT and NaN values from item dictionary."""
        cleaned = {}
        for key, value in item.items():
            if pd.isna(value) or (isinstance(value, str) and value.lower() == 'nat'):
                cleaned[key] = None
            else:
                cleaned[key] = value
        return cleaned
    
    def _calculate_kanban_statistics(self, df: pd.DataFrame, 
                                   original_count: int) -> Dict[str, Any]:
        """Calculate statistics for Kanban board."""
        filtered_count = len(df)
        reduction_percentage = 0
        if original_count > 0:
            reduction_percentage = ((original_count - filtered_count) / original_count * 100)
        
        # Distribution by status
        distribution = df['Estado'].value_counts().to_dict()
        
        # Critical EDPs count
        critical_count = len(df[df.get('Crítico', False) == True])
        
        # Average days waiting
        avg_days_waiting = df['Días Espera'].mean() if 'Días Espera' in df.columns else 0
        
        return {
            'total_registros': original_count,
            'registros_filtrados': filtered_count,
            'porcentaje_reduccion': round(reduction_percentage, 1),
            'distribucion_cards': distribution,
            'edps_criticos': critical_count,
            'promedio_dias_espera': round(avg_days_waiting or 0, 1)
        }
    
    def _get_filter_options(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Get available options for filters."""
        return {
            'meses': sorted(df['Mes'].dropna().unique().tolist()) if 'Mes' in df.columns else [],
            'encargados': sorted(df['Jefe de Proyecto'].dropna().unique().tolist()) if 'Jefe de Proyecto' in df.columns else [],
            'clientes': sorted(df['Cliente'].dropna().unique().tolist()) if 'Cliente' in df.columns else [],
            'estados_detallados': sorted(df['Estado Detallado'].dropna().unique().tolist()) if 'Estado Detallado' in df.columns else []
        }
