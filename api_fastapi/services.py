import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import Flask services and functions
from edp_mvp.app.config import get_config
from edp_mvp.app.utils.gsheet import (
    read_sheet, 
    get_service, 
    clear_all_cache,
    read_log,
    read_cost_header,
    read_projects,
    update_edp_by_id,
    append_edp,
    append_cost,
    append_project
)
from edp_mvp.app.repositories.edp_repository import EDPRepository

from fastapi import HTTPException
from models import (
    EDP, EDPFilters, EDPResponse, EDPStats,
    Project, ProjectFilters, ProjectResponse,
    CostHeader, CostLine, CostFilters, CostResponse,
    LogEntry, LogFilters, LogResponse,
    MovimientoCaja, CajaData, CajaResponse, ResumenCaja,
    KPIDashboard, DashboardData, CacheStats
)

logger = logging.getLogger(__name__)

# Simple in-memory cache for the API
_api_cache = {}
_cache_timestamps = {}

def _get_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from parameters"""
    key_data = {k: v for k, v in kwargs.items() if v is not None}
    key_str = json.dumps(key_data, sort_keys=True)
    return f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"

def _is_cache_valid(key: str, ttl_seconds: int = 300) -> bool:
    """Check if cache entry is still valid"""
    if key not in _cache_timestamps:
        return False
    age = datetime.now().timestamp() - _cache_timestamps[key]
    return age < ttl_seconds

def _set_cache(key: str, data: Any) -> None:
    """Set cache entry"""
    _api_cache[key] = data
    _cache_timestamps[key] = datetime.now().timestamp()

def _get_cache(key: str) -> Optional[Any]:
    """Get cache entry if valid"""
    if key in _api_cache and _is_cache_valid(key):
        return _api_cache[key]
    return None

def _clean_numeric_value(value) -> Optional[float]:
    """Clean and convert numeric values from sheets"""
    if pd.isna(value) or value == '' or value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Remove currency symbols and separators
        cleaned = value.replace('$', '').replace(',', '').replace('.', '').strip()
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    
    return None

def _clean_date_value(value) -> Optional[str]:
    """Clean and convert date values from sheets"""
    if pd.isna(value) or value == '' or value is None:
        return None
    
    if isinstance(value, str):
        # Handle different date formats
        try:
            # Try to parse and return in ISO format
            if len(value) == 10 and '-' in value:  # YYYY-MM-DD
                return value
            # Add more date format handling as needed
            return value
        except:
            return None
    
    return str(value)

class GoogleSheetsServiceAsync:
    """Async wrapper for Google Sheets operations"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.config = get_config()
        
    async def get_edp_data(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get EDP data asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: read_sheet("edp!A1:V", apply_transformations=True)
        )
    
    async def get_projects_data(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get Projects data asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: read_sheet("projects!A1:I", apply_transformations=True)
        )
    
    async def get_cost_header_data(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get Cost Header data asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: read_sheet("cost_header!A1:Q", apply_transformations=True)
        )
    
    async def get_cost_lines_data(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get Cost Lines data asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: read_sheet("cost_lines!A1:H", apply_transformations=True)
        )
    
    async def get_log_data(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get Log data asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: read_sheet("log!A1:G", apply_transformations=True)
        )
    
    async def get_caja_data(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get Caja data asynchronously (if exists)"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                self.executor, 
                lambda: read_sheet("caja!A1:Z", apply_transformations=True)
            )
        except:
            # Return empty DataFrame if caja sheet doesn't exist
            return pd.DataFrame()
    
    def _process_edp_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process EDP DataFrame and convert to list of dictionaries"""
        if df.empty:
            return []
        
        processed_data = []
        for _, row in df.iterrows():
            # Handle ID - always convert to string for consistency
            id_value = row.get('id')
            if pd.notna(id_value):
                id_value = str(id_value)
            else:
                id_value = None
            
            # Handle n_edp - can be string or int
            n_edp_value = row.get('n_edp')
            if pd.notna(n_edp_value):
                try:
                    n_edp_value = int(n_edp_value)
                except (ValueError, TypeError):
                    # If it's a string, try to extract number or keep as string
                    n_edp_str = str(n_edp_value)
                    import re
                    numbers = re.findall(r'\d+', n_edp_str)
                    n_edp_value = int(numbers[0]) if numbers else None
            else:
                n_edp_value = None
            
            edp_dict = {
                'id': id_value,
                'n_edp': n_edp_value,
                'proyecto': str(row.get('proyecto', '')) if pd.notna(row.get('proyecto')) else None,
                'cliente': str(row.get('cliente', '')) if pd.notna(row.get('cliente')) else None,
                'gestor': str(row.get('gestor', '')) if pd.notna(row.get('gestor')) else None,
                'jefe_proyecto': str(row.get('jefe_proyecto', '')) if pd.notna(row.get('jefe_proyecto')) else None,
                'mes': str(row.get('mes', '')) if pd.notna(row.get('mes')) else None,
                'fecha_emision': _clean_date_value(row.get('fecha_emision')),
                'fecha_envio_cliente': _clean_date_value(row.get('fecha_envio_cliente')),
                'monto_propuesto': _clean_numeric_value(row.get('monto_propuesto')),
                'monto_aprobado': _clean_numeric_value(row.get('monto_aprobado')),
                'fecha_estimada_pago': _clean_date_value(row.get('fecha_estimada_pago')),
                'conformidad_enviada': str(row.get('conformidad_enviada', '')) if pd.notna(row.get('conformidad_enviada')) else None,
                'n_conformidad': str(row.get('n_conformidad', '')) if pd.notna(row.get('n_conformidad')) else None,
                'fecha_conformidad': _clean_date_value(row.get('fecha_conformidad')),
                'estado': str(row.get('estado', '')) if pd.notna(row.get('estado')) else None,
                'observaciones': str(row.get('observaciones', '')) if pd.notna(row.get('observaciones')) else None,
                'registrado_por': str(row.get('registrado_por', '')) if pd.notna(row.get('registrado_por')) else None,
                'estado_detallado': str(row.get('estado_detallado', '')) if pd.notna(row.get('estado_detallado')) else None,
                'fecha_registro': _clean_date_value(row.get('fecha_registro')),
                'motivo_no_aprobado': str(row.get('motivo_no_aprobado', '')) if pd.notna(row.get('motivo_no_aprobado')) else None,
                'tipo_falla': str(row.get('tipo_falla', '')) if pd.notna(row.get('tipo_falla')) else None,
            }
            processed_data.append(edp_dict)
        
        return processed_data
    
    def _process_projects_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process Projects DataFrame and convert to list of dictionaries"""
        if df.empty:
            return []
        
        processed_data = []
        for _, row in df.iterrows():
            project_dict = {
                'project_id': str(row.get('project_id', '')) if pd.notna(row.get('project_id')) else None,
                'proyecto': str(row.get('proyecto', '')) if pd.notna(row.get('proyecto')) else None,
                'cliente': str(row.get('cliente', '')) if pd.notna(row.get('cliente')) else None,
                'gestor': str(row.get('gestor', '')) if pd.notna(row.get('gestor')) else None,
                'jefe_proyecto': str(row.get('jefe_proyecto', '')) if pd.notna(row.get('jefe_proyecto')) else None,
                'fecha_inicio': _clean_date_value(row.get('fecha_inicio')),
                'fecha_fin_prevista': _clean_date_value(row.get('fecha_fin_prevista')),
                'monto_contrato': _clean_numeric_value(row.get('monto_contrato')),
                'moneda': str(row.get('moneda', 'CLP')) if pd.notna(row.get('moneda')) else 'CLP',
            }
            processed_data.append(project_dict)
        
        return processed_data
    
    def _process_cost_header_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process Cost Header DataFrame and convert to list of dictionaries"""
        if df.empty:
            return []
        
        processed_data = []
        for _, row in df.iterrows():
            cost_dict = {
                'cost_id': int(row.get('cost_id', 0)) if pd.notna(row.get('cost_id')) else None,
                'project_id': str(row.get('project_id', '')) if pd.notna(row.get('project_id')) else None,
                'proveedor': str(row.get('proveedor', '')) if pd.notna(row.get('proveedor')) else None,
                'factura': str(row.get('factura', '')) if pd.notna(row.get('factura')) else None,
                'fecha_factura': _clean_date_value(row.get('fecha_factura')),
                'fecha_recepcion': _clean_date_value(row.get('fecha_recepcion')),
                'fecha_vencimiento': _clean_date_value(row.get('fecha_vencimiento')),
                'fecha_pago': _clean_date_value(row.get('fecha_pago')),
                'importe_bruto': _clean_numeric_value(row.get('importe_bruto')),
                'importe_neto': _clean_numeric_value(row.get('importe_neto')),
                'moneda': str(row.get('moneda', 'CLP')) if pd.notna(row.get('moneda')) else 'CLP',
                'estado_costo': str(row.get('estado_costo', '')) if pd.notna(row.get('estado_costo')) else None,
                'tipo_costo': str(row.get('tipo_costo', '')) if pd.notna(row.get('tipo_costo')) else None,
                'detalle_costo': str(row.get('detalle_costo', '')) if pd.notna(row.get('detalle_costo')) else None,
                'detalle_especifico_costo': str(row.get('detalle_especifico_costo', '')) if pd.notna(row.get('detalle_especifico_costo')) else None,
                'responsable_registro': str(row.get('responsable_registro', '')) if pd.notna(row.get('responsable_registro')) else None,
                'url_respaldo': str(row.get('url_respaldo', '')) if pd.notna(row.get('url_respaldo')) else None,
            }
            processed_data.append(cost_dict)
        
        return processed_data
    
    def _process_log_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process Log DataFrame and convert to list of dictionaries"""
        if df.empty:
            return []
        
        processed_data = []
        for _, row in df.iterrows():
            # Handle n_edp - can be string or int
            n_edp_value = row.get('n_edp')
            if pd.notna(n_edp_value):
                try:
                    n_edp_value = int(n_edp_value)
                except (ValueError, TypeError):
                    # If it's a string like 'TEST-001', try to extract number or keep as string
                    n_edp_str = str(n_edp_value)
                    import re
                    numbers = re.findall(r'\d+', n_edp_str)
                    if numbers:
                        n_edp_value = int(numbers[0])
                    else:
                        # Keep as string if no numbers found
                        n_edp_value = n_edp_str
            else:
                n_edp_value = None
            
            log_dict = {
                'fecha_hora': str(row.get('fecha_hora', '')) if pd.notna(row.get('fecha_hora')) else None,
                'n_edp': n_edp_value,
                'proyecto': str(row.get('proyecto', '')) if pd.notna(row.get('proyecto')) else None,
                'campo': str(row.get('campo', '')) if pd.notna(row.get('campo')) else None,
                'antes': str(row.get('antes', '')) if pd.notna(row.get('antes')) else None,
                'despues': str(row.get('despues', '')) if pd.notna(row.get('despues')) else None,
                'usuario': str(row.get('usuario', '')) if pd.notna(row.get('usuario')) else None,
            }
            processed_data.append(log_dict)
        
        return processed_data
    
    async def update_edp(self, edp_id: int, updates: Dict[str, Any], usuario: str = None) -> bool:
        """Update EDP asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: update_edp_by_id(edp_id, updates, usuario)
        )
    
    async def create_edp(self, edp_data: Dict[str, Any]) -> int:
        """Create new EDP asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: append_edp(edp_data)
        )
    
    async def clear_cache(self) -> bool:
        """Clear all caches asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            clear_all_cache
        )

class APIService:
    """Main API service that coordinates between different data sources"""
    
    def __init__(self):
        self.edp_repository = EDPRepository()
        self.sheets_service = GoogleSheetsServiceAsync()
        
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Check cache first
            cache_key = _get_cache_key("dashboard")
            cached_data = _get_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Get data from multiple sources concurrently
            edps_data, projects_data, costs_data = await asyncio.gather(
                self.get_filtered_edps({}),
                self.get_all_projects({}),
                self.get_all_costs({}),
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(edps_data, Exception):
                edps_data = []
            if isinstance(projects_data, Exception):
                projects_data = []
            if isinstance(costs_data, Exception):
                costs_data = {"headers": [], "summary": {}}
            
            # Calculate EDP metrics
            total_edps = len(edps_data)
            edps_aprobados = len([edp for edp in edps_data if edp.get('estado') == 'aprobado'])
            edps_pendientes = len([edp for edp in edps_data if edp.get('estado') in ['enviado', 'revisión cliente', 'creado']])
            
            monto_total_propuesto = sum(edp.get('monto_propuesto', 0) or 0 for edp in edps_data)
            monto_total_aprobado = sum(edp.get('monto_aprobado', 0) or 0 for edp in edps_data)
            
            tasa_aprobacion = (edps_aprobados / total_edps * 100) if total_edps > 0 else 0
            
            # Calculate project metrics
            total_projects = len(projects_data)
            proyectos_activos = len([p for p in projects_data if p.get('fecha_fin_prevista')])
            
            # Calculate cost metrics
            cost_headers = costs_data.get("headers", [])
            total_costs = len(cost_headers)
            costos_pendientes = len([c for c in cost_headers if c.get('estado_costo') == 'pendiente'])
            costos_pagados = len([c for c in cost_headers if c.get('estado_costo') == 'pagado'])
            
            # Group data for charts
            edp_by_status = {}
            for edp in edps_data:
                status = edp.get('estado', 'unknown')
                edp_by_status[status] = edp_by_status.get(status, 0) + 1
            
            projects_by_client = {}
            for project in projects_data:
                client = project.get('cliente', 'unknown')
                projects_by_client[client] = projects_by_client.get(client, 0) + 1
            
            costs_by_type = costs_data.get("summary", {}).get("by_type", {})
            
            # Recent activity (last 7 days)
            recent_activity = []
            for edp in edps_data[:10]:  # Last 10 EDPs as recent activity
                recent_activity.append({
                    "type": "EDP",
                    "description": f"EDP {edp.get('n_edp')} - {edp.get('proyecto')}",
                    "status": edp.get('estado'),
                    "date": edp.get('fecha_registro')
                })
            
            # Create KPIs
            kpis = {
                "total_edps": total_edps,
                "total_projects": total_projects,
                "total_costs": total_costs,
                "edps_aprobados": edps_aprobados,
                "edps_pendientes": edps_pendientes,
                "monto_total_aprobado": monto_total_aprobado,
                "monto_total_propuesto": monto_total_propuesto,
                "tasa_aprobacion": round(tasa_aprobacion, 2),
                "proyectos_activos": proyectos_activos,
                "costos_pendientes": costos_pendientes,
                "costos_pagados": costos_pagados
            }
            
            # Alerts (basic implementation)
            alerts = []
            if edps_pendientes > total_edps * 0.7:  # More than 70% pending
                alerts.append({
                    "type": "warning",
                    "message": f"Alto número de EDPs pendientes: {edps_pendientes}",
                    "priority": "medium"
                })
            
            if costos_pendientes > 0:
                alerts.append({
                    "type": "info",
                    "message": f"{costos_pendientes} costos pendientes de pago",
                    "priority": "low"
                })
            
            dashboard_data = {
                "kpis": kpis,
                "edp_by_status": edp_by_status,
                "projects_by_status": projects_by_client,
                "costs_by_type": costs_by_type,
                "recent_activity": recent_activity,
                "alerts": alerts,
                "charts": {
                    "edp_status_distribution": edp_by_status,
                    "project_client_distribution": projects_by_client,
                    "cost_type_distribution": costs_by_type
                },
                "last_updated": datetime.now()
            }
            
            result = {
                "success": True,
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            _set_cache(cache_key, result)
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_filtered_edps(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get filtered EDP data"""
        try:
            cache_key = _get_cache_key("edps", **filters)
            cached_data = _get_cache(cache_key)
            if cached_data:
                return cached_data
            
            edp_data = await self.sheets_service.get_edp_data(filters)
            
            if edp_data.empty:
                return []
            
            # Process the DataFrame to clean data
            try:
                processed_data = self.sheets_service._process_edp_dataframe(edp_data)
            except Exception as processing_error:
                logger.error(f"Error processing EDP dataframe: {processing_error}")
                # Return raw data if processing fails
                processed_data = edp_data.to_dict('records') if not edp_data.empty else []
            
            # Apply filters if provided
            if filters and processed_data:
                filtered_data = []
                for edp in processed_data:
                    try:
                        include = True
                        
                        if filters.get('estado') and edp.get('estado') != filters['estado']:
                            include = False
                        if filters.get('cliente') and filters['cliente'].lower() not in (edp.get('cliente') or '').lower():
                            include = False
                        if filters.get('jefe_proyecto') and filters['jefe_proyecto'].lower() not in (edp.get('jefe_proyecto') or '').lower():
                            include = False
                        if filters.get('proyecto') and filters['proyecto'].lower() not in (edp.get('proyecto') or '').lower():
                            include = False
                        if filters.get('mes') and edp.get('mes') != filters['mes']:
                            include = False
                        
                        if include:
                            filtered_data.append(edp)
                    except Exception as filter_error:
                        logger.warning(f"Error filtering EDP {edp}: {filter_error}")
                        # Include the item if filtering fails
                        filtered_data.append(edp)
                
                processed_data = filtered_data
            
            _set_cache(cache_key, processed_data)
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in get_filtered_edps: {e}")
            # Return empty list instead of raising exception
            return []

    async def get_all_projects(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all projects data"""
        try:
            cache_key = _get_cache_key("projects", **(filters or {}))
            cached_data = _get_cache(cache_key)
            if cached_data:
                return cached_data
            
            projects_data = await self.sheets_service.get_projects_data(filters)
            
            if projects_data.empty:
                return []
            
            # Process the DataFrame to clean data
            processed_data = self.sheets_service._process_projects_dataframe(projects_data)
            
            # Apply filters if provided
            if filters:
                filtered_data = []
                for project in processed_data:
                    include = True
                    
                    if filters.get('cliente') and filters['cliente'].lower() not in (project.get('cliente') or '').lower():
                        include = False
                    if filters.get('jefe_proyecto') and filters['jefe_proyecto'].lower() not in (project.get('jefe_proyecto') or '').lower():
                        include = False
                    if filters.get('gestor') and filters['gestor'].lower() not in (project.get('gestor') or '').lower():
                        include = False
                    
                    if include:
                        filtered_data.append(project)
                
                processed_data = filtered_data
            
            _set_cache(cache_key, processed_data)
            return processed_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting projects data: {str(e)}")

    async def get_all_costs(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get all costs data (headers and lines)"""
        try:
            cache_key = _get_cache_key("costs", **(filters or {}))
            cached_data = _get_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Get both headers and lines
            cost_headers_data, cost_lines_data = await asyncio.gather(
                self.sheets_service.get_cost_header_data(filters),
                self.sheets_service.get_cost_lines_data(filters),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(cost_headers_data, Exception):
                cost_headers_data = pd.DataFrame()
            if isinstance(cost_lines_data, Exception):
                cost_lines_data = pd.DataFrame()
            
            # Process the DataFrames
            processed_headers = self.sheets_service._process_cost_header_dataframe(cost_headers_data)
            processed_lines = cost_lines_data.to_dict('records') if not cost_lines_data.empty else []
            
            # Apply filters to headers if provided
            if filters and processed_headers:
                filtered_headers = []
                for cost in processed_headers:
                    include = True
                    
                    if filters.get('project_id') and cost.get('project_id') != filters['project_id']:
                        include = False
                    if filters.get('estado_costo') and cost.get('estado_costo') != filters['estado_costo']:
                        include = False
                    if filters.get('tipo_costo') and cost.get('tipo_costo') != filters['tipo_costo']:
                        include = False
                    if filters.get('proveedor') and filters['proveedor'].lower() not in (cost.get('proveedor') or '').lower():
                        include = False
                    
                    if include:
                        filtered_headers.append(cost)
                
                processed_headers = filtered_headers
            
            result = {
                "headers": processed_headers,
                "lines": processed_lines,
                "total_headers": len(processed_headers),
                "total_lines": len(processed_lines),
                "summary": self._calculate_cost_summary(processed_headers)
            }
            
            _set_cache(cache_key, result)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting costs data: {str(e)}")

    async def get_all_logs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all log entries"""
        try:
            cache_key = _get_cache_key("logs", **(filters or {}))
            cached_data = _get_cache(cache_key)
            if cached_data:
                return cached_data
            
            log_data = await self.sheets_service.get_log_data(filters)
            
            if log_data.empty:
                return []
            
            # Process the DataFrame
            processed_data = self.sheets_service._process_log_dataframe(log_data)
            
            # Apply filters if provided
            if filters:
                filtered_data = []
                for log_entry in processed_data:
                    include = True
                    
                    if filters.get('n_edp') and log_entry.get('n_edp') != filters['n_edp']:
                        include = False
                    if filters.get('proyecto') and filters['proyecto'].lower() not in (log_entry.get('proyecto') or '').lower():
                        include = False
                    if filters.get('usuario') and filters['usuario'].lower() not in (log_entry.get('usuario') or '').lower():
                        include = False
                    if filters.get('campo') and filters['campo'].lower() not in (log_entry.get('campo') or '').lower():
                        include = False
                    
                    if include:
                        filtered_data.append(log_entry)
                
                processed_data = filtered_data
            
            _set_cache(cache_key, processed_data)
            return processed_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting logs data: {str(e)}")

    def _calculate_cost_summary(self, cost_headers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for costs"""
        if not cost_headers:
            return {"total_amount": 0, "by_status": {}, "by_type": {}, "by_currency": {}}
        
        total_amount = sum(cost.get('importe_neto', 0) or 0 for cost in cost_headers)
        
        # Group by status
        by_status = {}
        for cost in cost_headers:
            status = cost.get('estado_costo', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        # Group by type
        by_type = {}
        for cost in cost_headers:
            tipo = cost.get('tipo_costo', 'unknown')
            by_type[tipo] = by_type.get(tipo, 0) + (cost.get('importe_neto', 0) or 0)
        
        # Group by currency
        by_currency = {}
        for cost in cost_headers:
            currency = cost.get('moneda', 'CLP')
            by_currency[currency] = by_currency.get(currency, 0) + (cost.get('importe_neto', 0) or 0)
        
        return {
            "total_amount": total_amount,
            "by_status": by_status,
            "by_type": by_type,
            "by_currency": by_currency
        }
    
    async def get_caja_summary(self) -> Dict[str, Any]:
        """Get cash flow summary"""
        try:
            cache_key = _get_cache_key("caja_summary")
            cached_data = _get_cache(cache_key)
            if cached_data:
                return cached_data
            
            caja_data = await self.sheets_service.get_caja_data()
            
            if caja_data.empty:
                return {"total_ingresos": 0, "total_egresos": 0, "balance": 0, "items": []}
            
            # Calculate summary metrics
            total_ingresos = caja_data[caja_data['tipo'] == 'Ingreso']['monto'].sum() if 'tipo' in caja_data.columns else 0
            total_egresos = caja_data[caja_data['tipo'] == 'Egreso']['monto'].sum() if 'tipo' in caja_data.columns else 0
            balance = total_ingresos - total_egresos
            
            result = {
                "total_ingresos": float(total_ingresos) if pd.notna(total_ingresos) else 0,
                "total_egresos": float(total_egresos) if pd.notna(total_egresos) else 0,
                "balance": float(balance) if pd.notna(balance) else 0,
                "items": caja_data.to_dict('records')
            }
            
            _set_cache(cache_key, result)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting caja data: {str(e)}")

    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    async def clear_all_caches(self) -> Dict[str, Any]:
        """Clear all caches"""
        try:
            # Clear local cache
            _api_cache.clear()
            _cache_timestamps.clear()
            
            # Clear Google Sheets cache
            await self.sheets_service.clear_cache()
            
            return {
                "success": True,
                "message": "All caches cleared",
                "timestamp": self.get_current_timestamp()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": self.get_current_timestamp()
            }

    async def check_cache_health(self) -> Dict[str, Any]:
        """Check cache health status"""
        try:
            return {
                "status": "healthy",
                "local_cache_entries": len(_api_cache),
                "oldest_entry": min(_cache_timestamps.values()) if _cache_timestamps else None,
                "newest_entry": max(_cache_timestamps.values()) if _cache_timestamps else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def check_sheets_health(self) -> Dict[str, Any]:
        """Check Google Sheets service health"""
        try:
            # Try to get service
            service = get_service()
            if service is None:
                return {
                    "status": "error",
                    "message": "Google Sheets service not available"
                }
            
            return {
                "status": "healthy",
                "message": "Google Sheets service available"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_edps_with_cache(self, filters, limit: int = 100, offset: int = 0, force_refresh: bool = False):
        """Get EDPs with cache support"""
        try:
            cache_key = _get_cache_key("edps_with_cache", 
                                     estado=filters.estado,
                                     cliente=filters.cliente,
                                     jefe_proyecto=filters.jefe_proyecto,
                                     mes=filters.mes,
                                     limit=limit,
                                     offset=offset)
            
            if not force_refresh:
                cached_data = _get_cache(cache_key)
                if cached_data:
                    return cached_data
            
            # Get filtered data
            edps_data = await self.get_filtered_edps({
                'estado': filters.estado,
                'cliente': filters.cliente,
                'jefe_proyecto': filters.jefe_proyecto,
                'mes': filters.mes
            })
            
            # Apply pagination
            total = len(edps_data)
            paginated_edps = edps_data[offset:offset + limit]
            
            result = {
                "data": paginated_edps,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
            
            _set_cache(cache_key, result)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting EDPs with cache: {str(e)}")

    async def get_edp_by_id(self, edp_id: str, force_refresh: bool = False):
        """Get single EDP by ID"""
        try:
            cache_key = _get_cache_key("edp_by_id", edp_id=edp_id)
            
            if not force_refresh:
                cached_data = _get_cache(cache_key)
                if cached_data:
                    return cached_data
            
            # Get all EDPs and find the one with matching ID
            all_edps = await self.get_filtered_edps({})
            
            for edp in all_edps:
                if str(edp.get('id')) == str(edp_id) or str(edp.get('n_edp')) == str(edp_id):
                    _set_cache(cache_key, edp)
                    return edp
            
            return None
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting EDP by ID: {str(e)}")

    async def get_edp_stats(self, force_refresh: bool = False):
        """Get EDP statistics"""
        try:
            cache_key = _get_cache_key("edp_stats")
            
            if not force_refresh:
                cached_data = _get_cache(cache_key)
                if cached_data:
                    return cached_data
            
            # Get all EDPs
            all_edps = await self.get_filtered_edps({})
            
            if not all_edps:
                return {"total": 0, "by_status": {}, "by_client": {}}
            
            # Calculate statistics
            df = pd.DataFrame(all_edps)
            
            stats = {
                "total": len(df),
                "by_status": df.groupby('estado_detallado').size().to_dict() if 'estado_detallado' in df.columns else {},
                "by_client": df.groupby('cliente').size().to_dict() if 'cliente' in df.columns else {},
                "total_amount": df['monto_aprobado'].sum() if 'monto_aprobado' in df.columns else 0,
                "last_updated": self.get_current_timestamp()
            }
            
            _set_cache(cache_key, stats)
            return stats
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting EDP stats: {str(e)}")

    async def update_edp(self, edp_id: str, updates: Dict[str, Any]) -> bool:
        """Update EDP and invalidate cache"""
        try:
            # Use the sheets service to update
            success = await self.sheets_service.update_edp(int(edp_id), updates)
            
            if success:
                # Invalidate related cache entries
                keys_to_remove = [k for k in _api_cache.keys() if 'edp' in k.lower()]
                for key in keys_to_remove:
                    _api_cache.pop(key, None)
                    _cache_timestamps.pop(key, None)
            
            return success
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating EDP: {str(e)}")

    async def get_caja_data(self, fecha_desde: str = None, fecha_hasta: str = None, 
                           categoria: str = None, force_refresh: bool = False):
        """Get caja data with filters"""
        try:
            cache_key = _get_cache_key("caja_data", 
                                     fecha_desde=fecha_desde,
                                     fecha_hasta=fecha_hasta,
                                     categoria=categoria)
            
            if not force_refresh:
                cached_data = _get_cache(cache_key)
                if cached_data:
                    return cached_data
            
            # Get caja data
            caja_data = await self.sheets_service.get_caja_data()
            
            if caja_data.empty:
                return {"data": [], "total": 0, "summary": {}}
            
            # Apply filters
            filtered_data = caja_data
            if fecha_desde and 'fecha' in caja_data.columns:
                filtered_data = filtered_data[filtered_data['fecha'] >= fecha_desde]
            if fecha_hasta and 'fecha' in caja_data.columns:
                filtered_data = filtered_data[filtered_data['fecha'] <= fecha_hasta]
            if categoria and 'categoria' in caja_data.columns:
                filtered_data = filtered_data[filtered_data['categoria'].str.contains(categoria, case=False, na=False)]
            
            result = {
                "data": filtered_data.to_dict('records'),
                "total": len(filtered_data),
                "summary": await self.get_caja_summary()
            }
            
            _set_cache(cache_key, result)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting caja data: {str(e)}")

    async def get_caja_resumen(self, force_refresh: bool = False):
        """Get caja summary"""
        return await self.get_caja_summary()

    async def get_cache_stats(self):
        """Get cache statistics"""
        try:
            return {
                "total_entries": len(_api_cache),
                "cache_keys": list(_api_cache.keys()),
                "oldest_entry": min(_cache_timestamps.values()) if _cache_timestamps else None,
                "newest_entry": max(_cache_timestamps.values()) if _cache_timestamps else None,
                "timestamp": self.get_current_timestamp()
            }
        except Exception as e:
            return {"error": str(e)}

    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        try:
            import fnmatch
            
            keys_to_remove = []
            for key in _api_cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                _api_cache.pop(key, None)
                _cache_timestamps.pop(key, None)
            
            return len(keys_to_remove)
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0

    async def refresh_all_cache(self):
        """Refresh all cached data"""
        try:
            # Clear current cache
            await self.clear_all_caches()
            
            # Pre-load commonly used data
            await self.get_dashboard_data()
            await self.get_edp_stats(force_refresh=True)
            await self.get_caja_summary()
            
            return {
                "success": True,
                "message": "All cache refreshed successfully",
                "timestamp": self.get_current_timestamp()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": self.get_current_timestamp()
            }

    async def handle_sheets_update(self, webhook_data: Dict[str, Any]):
        """Handle webhook notification of sheets update"""
        try:
            # Clear all cache when sheets are updated
            await self.clear_all_caches()
            
            # Log the update
            logger.info(f"Sheets updated via webhook: {webhook_data}")
            
            return {
                "success": True,
                "message": "Webhook processed successfully",
                "timestamp": self.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error handling sheets webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": self.get_current_timestamp()
            } 