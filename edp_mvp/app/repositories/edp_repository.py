"""
Repository for EDP (Estado de Pago) data access.
"""

from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime
import logging
import traceback

from . import BaseRepository
from ..models import EDP
from ..utils.date_utils import parse_date_safe
from ..utils.format_utils import clean_numeric_value
from ..utils.supabase_adapter import read_sheet, update_row, log_cambio_edp, append_row
from ..services.supabase_service import get_supabase_service
from ..config import get_config
import numpy as np
from ..services.cache_invalidation_service import invalidate_cache_on_change

logger = logging.getLogger(__name__)


class EDPRepository(BaseRepository):
    """Repository for EDP operations."""

    def __init__(self):
        super().__init__()
        self.table_name = "edp"
        self.range_name = "edp!A:V"  # Para compatibilidad

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
        try:
            service = get_supabase_service()
            
            # Preparar datos del EDP
            edp_data = {
                'n_edp': int(edp.n_edp) if edp.n_edp else None,  # Convertir a INTEGER
                'proyecto': edp.proyecto,
                'cliente': edp.cliente,
                'gestor': edp.gestor,
                'jefe_proyecto': edp.jefe_proyecto,
                'mes': edp.mes,
                'fecha_emision': edp.fecha_emision.isoformat() if edp.fecha_emision else None,
                'fecha_envio_cliente': edp.fecha_envio_cliente.isoformat() if edp.fecha_envio_cliente else None,
                'monto_propuesto': int(edp.monto_propuesto) if edp.monto_propuesto else None,  # Convertir a BIGINT
                'monto_aprobado': int(edp.monto_aprobado) if edp.monto_aprobado else None,  # Convertir a BIGINT
                'fecha_estimada_pago': edp.fecha_estimada_pago.isoformat() if edp.fecha_estimada_pago else None,
                'conformidad_enviada': bool(edp.conformidad_enviada) if edp.conformidad_enviada is not None else False,
                'n_conformidad': edp.n_conformidad,
                'fecha_conformidad': edp.fecha_conformidad.isoformat() if edp.fecha_conformidad else None,
                'estado': edp.estado,
                'observaciones': edp.observaciones,
                'registrado_por': edp.registrado_por,
                'estado_detallado': edp.estado_detallado,
                'fecha_registro': edp.fecha_registro.isoformat() if edp.fecha_registro else None,
                'motivo_no_aprobado': edp.motivo_no_aprobado,
                'tipo_falla': edp.tipo_falla
            }
            
            # Insertar en Supabase
            result = service.insert(self.table_name, edp_data)
            
            # El servicio insert() devuelve una lista, necesitamos el primer elemento
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get('id')
            elif result and isinstance(result, dict):
                return result.get('id')
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error creating EDP: {e}")
            raise Exception(f"Failed to create EDP: {e}")
    
    def create_bulk(self, edps: List[EDP]) -> Dict[str, Any]:
        """Create multiple EDPs in bulk for better performance."""
        try:
            if not edps:
                return {"success": True, "created_ids": [], "message": "No EDPs to create"}
            
            service = get_supabase_service()
            created_ids = []
            
            # Preparar datos de todos los EDPs
            edps_data = []
            for edp in edps:
                edp_data = {
                    'n_edp': int(edp.n_edp) if edp.n_edp else None,  # Convertir a INTEGER
                    'proyecto': edp.proyecto,
                    'cliente': edp.cliente,
                    'gestor': edp.gestor,
                    'jefe_proyecto': edp.jefe_proyecto,
                    'mes': edp.mes,
                    'fecha_emision': edp.fecha_emision.isoformat() if edp.fecha_emision else None,
                    'fecha_envio_cliente': edp.fecha_envio_cliente.isoformat() if edp.fecha_envio_cliente else None,
                    'monto_propuesto': int(edp.monto_propuesto) if edp.monto_propuesto else None,  # Convertir a BIGINT
                    'monto_aprobado': int(edp.monto_aprobado) if edp.monto_aprobado else None,  # Convertir a BIGINT
                    'fecha_estimada_pago': edp.fecha_estimada_pago.isoformat() if edp.fecha_estimada_pago else None,
                    'conformidad_enviada': bool(edp.conformidad_enviada) if edp.conformidad_enviada is not None else False,
                    'n_conformidad': edp.n_conformidad,
                    'fecha_conformidad': edp.fecha_conformidad.isoformat() if edp.fecha_conformidad else None,
                    'estado': edp.estado,
                    'observaciones': edp.observaciones,
                    'registrado_por': edp.registrado_por,
                    'estado_detallado': edp.estado_detallado,
                    'fecha_registro': edp.fecha_registro.isoformat() if edp.fecha_registro else None,
                    'motivo_no_aprobado': edp.motivo_no_aprobado,
                    'tipo_falla': edp.tipo_falla
                }
                edps_data.append(edp_data)
            
            # Bulk insert en Supabase usando insert normal (que maneja listas)
            results = service.insert(self.table_name, edps_data)
            
            # El servicio insert() devuelve una lista cuando se pasa una lista
            created_ids = []
            if results and isinstance(results, list):
                created_ids = [result.get('id') for result in results if result and result.get('id')]
            
            return {
                "success": True,
                "created_ids": created_ids,
                "message": f"Successfully created {len(created_ids)} EDPs"
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

        try:
            service = get_supabase_service()
            
            # Preparar datos actualizados
            edp_data = {
                'n_edp': int(edp.n_edp) if edp.n_edp else None,  # Convertir a INTEGER
                'proyecto': edp.proyecto,
                'cliente': edp.cliente,
                'gestor': edp.gestor,
                'jefe_proyecto': edp.jefe_proyecto,
                'mes': edp.mes,
                'fecha_emision': edp.fecha_emision.isoformat() if edp.fecha_emision else None,
                'fecha_envio_cliente': edp.fecha_envio_cliente.isoformat() if edp.fecha_envio_cliente else None,
                'monto_propuesto': int(edp.monto_propuesto) if edp.monto_propuesto else None,  # Convertir a BIGINT
                'monto_aprobado': int(edp.monto_aprobado) if edp.monto_aprobado else None,  # Convertir a BIGINT
                'fecha_estimada_pago': edp.fecha_estimada_pago.isoformat() if edp.fecha_estimada_pago else None,
                'conformidad_enviada': bool(edp.conformidad_enviada) if edp.conformidad_enviada is not None else False,
                'n_conformidad': edp.n_conformidad,
                'fecha_conformidad': edp.fecha_conformidad.isoformat() if edp.fecha_conformidad else None,
                'estado': edp.estado,
                'observaciones': edp.observaciones,
                'registrado_por': edp.registrado_por,
                'estado_detallado': edp.estado_detallado,
                'fecha_registro': edp.fecha_registro.isoformat() if edp.fecha_registro else None,
                'motivo_no_aprobado': edp.motivo_no_aprobado,
                'tipo_falla': edp.tipo_falla
            }
            
            # Actualizar en Supabase por ID
            result = service.update(self.table_name, {'id': edp.id}, edp_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating EDP {edp.id}: {e}")
            return False

    @invalidate_cache_on_change('edp_deleted', ['edps'])
    def delete(self, edp_id: int) -> Dict[str, Any]:
        """Delete EDP by internal ID."""
        try:
            print(f"🗑️ Eliminando EDP con ID: {edp_id}")
            
            service = get_supabase_service()
            
            # Primero verificar que el EDP existe
            existing_edp = service.select(self.table_name, {"id": edp_id}, limit=1)
            
            if not existing_edp:
                print(f"❌ EDP no encontrado con ID: {edp_id}")
                return {
                    "success": False,
                    "message": f"EDP con ID {edp_id} no encontrado"
                }
            
            edp_record = existing_edp[0]
            n_edp = edp_record.get('n_edp', 'N/A')
            proyecto = edp_record.get('proyecto', 'N/A')
            
            print(f"📋 EDP encontrado: #{n_edp} - Proyecto: {proyecto}")
            
            # Eliminar el EDP
            result = service.delete(self.table_name, {"id": edp_id})
            
            if result:
                print(f"✅ EDP #{n_edp} eliminado exitosamente")
                
                # Limpiar caché (si está disponible)
                try:
                    from ..controllers.edp_upload_controller import _GLOBAL_EDP_CACHE
                    _GLOBAL_EDP_CACHE['data'] = {}
                    _GLOBAL_EDP_CACHE['last_update'] = 0
                    print("🧹 Caché global limpiado")
                except ImportError:
                    print("ℹ️ Caché global no disponible")
                    pass
                
                return {
                    "success": True,
                    "message": f"EDP #{n_edp} (Proyecto: {proyecto}) eliminado exitosamente",
                    "deleted_edp": {
                        "id": edp_id,
                        "n_edp": n_edp,
                        "proyecto": proyecto
                    }
                }
            else:
                print(f"❌ Error eliminando EDP #{n_edp}")
                return {
                    "success": False,
                    "message": f"Error eliminando EDP #{n_edp}"
                }
                
        except Exception as e:
            print(f"💥 Error en delete: {str(e)}")
            logger.error(f"Error deleting EDP {edp_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error eliminando EDP: {str(e)}"
            }

    def delete_by_n_edp(self, n_edp: str, proyecto: str = None) -> Dict[str, Any]:
        """Delete EDP by n_edp and optionally proyecto."""
        try:
            print(f"🗑️ Eliminando EDP #{n_edp} (Proyecto: {proyecto or 'cualquiera'})")
            
            service = get_supabase_service()
            
            # Buscar EDP por n_edp (y proyecto si se especifica)
            filters = {"n_edp": str(n_edp)}
            if proyecto:
                filters["proyecto"] = str(proyecto)
            
            existing_edps = service.select(self.table_name, filters)
            
            if not existing_edps:
                return {
                    "success": False,
                    "message": f"EDP #{n_edp}" + (f" para proyecto {proyecto}" if proyecto else "") + " no encontrado"
                }
            
            if len(existing_edps) > 1 and not proyecto:
                # Múltiples EDPs con el mismo número pero diferentes proyectos
                projects = [edp.get('proyecto', 'N/A') for edp in existing_edps]
                return {
                    "success": False,
                    "message": f"Múltiples EDPs #{n_edp} encontrados en proyectos: {', '.join(projects)}. Especifique el proyecto."
                }
            
            # Eliminar el EDP encontrado
            edp_to_delete = existing_edps[0]
            edp_id = edp_to_delete.get('id')
            
            return self.delete(edp_id)
            
        except Exception as e:
            print(f"💥 Error en delete_by_n_edp: {str(e)}")
            logger.error(f"Error deleting EDP by n_edp {n_edp}: {e}")
            return {
                "success": False,
                "message": f"Error eliminando EDP: {str(e)}"
            }

    @invalidate_cache_on_change('edp_updated', ['edps'])
    def update_fields(self, edp_id: int, updates: Dict[str, Any]) -> bool:
        """Update specific fields of an EDP."""
        try:
            print(f"🔍 update_fields called with:")
            print(f"   - edp_id: {edp_id} (type: {type(edp_id)})")
            print(f"   - updates: {updates}")
            
            service = get_supabase_service()
            
            # Buscar EDP por n_edp en Supabase
            filters = {'n_edp': int(edp_id) if str(edp_id).isdigit() else edp_id}
            existing_edp = service.select(self.table_name, filters, limit=1)
            
            if not existing_edp:
                print(f"❌ EDP not found for n_edp: {edp_id}")
                return False
            
            edp_record = existing_edp[0]
            print(f"   - Found EDP with ID: {edp_record.get('id')}")
            
            # Convert string boolean values to actual booleans for Supabase
            cleaned_updates = {}
            for key, value in updates.items():
                if key == 'conformidad_enviada':
                    # Convert "Sí"/"No" to boolean
                    if value == "Sí":
                        cleaned_updates[key] = True
                    elif value == "No":
                        cleaned_updates[key] = False
                    else:
                        cleaned_updates[key] = value
                else:
                    cleaned_updates[key] = value
            
            print(f"   - Cleaned updates: {cleaned_updates}")
            
            # Actualizar solo los campos especificados
            result = service.update(self.table_name, {'id': edp_record['id']}, cleaned_updates)
            
            if result:
                print(f"✅ Successfully updated EDP {edp_id}")
                return True
            else:
                print(f"❌ Failed to update EDP {edp_id}")
                return False
            
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
            
            # Convert pandas/numpy types to native Python types before passing to adapter
            clean_updates = {}
            for key, value in updates.items():
                if value is None or pd.isna(value):
                    clean_updates[key] = None
                elif hasattr(value, 'item'):  # numpy scalars
                    clean_updates[key] = value.item()
                elif hasattr(value, 'tolist'):  # numpy arrays
                    clean_updates[key] = value.tolist()
                # Conversiones específicas para campos EDP
                elif key == 'conformidad_enviada' and isinstance(value, str):
                    clean_updates[key] = value.lower() in ['sí', 'si', 'yes', 'true', '1']
                else:
                    clean_updates[key] = value
            
            # Update using Supabase adapter with cleaned data - usar ID interno, no row_number
            # Necesitamos obtener el ID interno del EDP encontrado
            edp_internal_id = current_edp.get("id")
            if not edp_internal_id:
                return {
                    "success": False,
                    "message": f"EDP {n_edp} sin ID interno válido"
                }
            
            from ..utils.supabase_adapter import update_edp_by_id
            success = update_edp_by_id(int(edp_internal_id), clean_updates)
            
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
                    "message": "Failed to update EDP in Supabase"
                }
                
        except Exception as e:
            import traceback
            print(f"Error in update_by_edp_id: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "message": f"Error updating EDP: {str(e)}"
            }

    @invalidate_cache_on_change('edp_updated', ['edps'])
    def update_by_internal_id(self, internal_id: int, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update EDP by internal ID using form data and log changes."""
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
            
            # Find EDP by internal ID
            edp_found = df_edps[df_edps["id"] == int(internal_id)]
            
            if edp_found.empty:
                return {
                    "success": False,
                    "message": f"EDP with internal ID {internal_id} not found"
                }
            
            # Get row number (add 2 for header and 0-based indexing)
            row_index = edp_found.index[0]
            row_number = row_index + 2
            
            # Get current EDP data
            current_edp = edp_found.iloc[0].to_dict()
            n_edp = current_edp.get('n_edp', str(internal_id))
            
            print(f"🔍 update_by_internal_id - Found EDP: n_edp={n_edp}, internal_id={internal_id}")
            
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
            
            print(f"🔍 update_by_internal_id - Applying updates: {updates}")
            
            # Convert pandas/numpy types to native Python types before passing to adapter
            clean_updates = {}
            for key, value in updates.items():
                if value is None or pd.isna(value):
                    clean_updates[key] = None
                elif hasattr(value, 'item'):  # numpy scalars
                    clean_updates[key] = value.item()
                elif hasattr(value, 'tolist'):  # numpy arrays
                    clean_updates[key] = value.tolist()
                # Conversiones específicas para campos EDP
                elif key == 'conformidad_enviada' and isinstance(value, str):
                    clean_updates[key] = value.lower() in ['sí', 'si', 'yes', 'true', '1']
                else:
                    clean_updates[key] = value
            
            print(f"🔍 update_by_internal_id - Clean updates: {clean_updates} (types: {[(k, type(v)) for k, v in clean_updates.items()]})")
            
            # Update using Supabase adapter with cleaned data - usar ID interno, no row_number
            from ..utils.supabase_adapter import update_edp_by_id
            success = update_edp_by_id(int(internal_id), clean_updates)
            
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
                    "message": f"EDP {n_edp} (ID: {internal_id}) updated successfully",
                    "data": {
                        "updated_fields": list(updates.keys()),
                        "changes_count": len(changes)
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update EDP in Supabase"
                }
                
        except Exception as e:
            import traceback
            print(f"❌ Error in update_by_internal_id: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "message": f"Error updating EDP: {str(e)}"
            }

    def _read_sheet_with_transformations(self) -> pd.DataFrame:
        """Read EDP data from Supabase with all transformations applied."""
        df = read_sheet(self.range_name, apply_transformations=True)
        return df

    # Método _apply_transformations movido al adaptador de Supabase
    # Las transformaciones ahora se aplican automáticamente en read_sheet()

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
                "dso_actual": row.get("dso_actual"),
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

    # Métodos auxiliares removidos - ya no necesarios con Supabase
    # _model_to_row_values y _get_last_column eran específicos de Google Sheets
