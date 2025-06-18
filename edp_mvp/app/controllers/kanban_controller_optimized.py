#!/usr/bin/env python3
"""
Versión optimizada del Kanban Controller
Aplica estrategias de cache y carga asíncrona para mejorar performance
"""

import asyncio
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import logging

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

# Importar servicios originales
from ..services.controller_service import ControllerService
from ..services.kanban_service import KanbanService
from ..utils.auth_utils import require_project_manager_or_above

logger = logging.getLogger(__name__)

# ================================
# 🚀 CACHE Y OPTIMIZACIÓN
# ================================

# Cache simple en memoria para Flask
_flask_cache = {}
_cache_timestamps = {}
_executor = ThreadPoolExecutor(max_workers=2)

# TTL por tipo de datos
CACHE_TTL = {
    "quick_dashboard": 300,    # 5 min - Dashboard básico
    "kanban_data": 180,        # 3 min - Datos Kanban
    "filter_options": 600,     # 10 min - Opciones de filtros
    "full_dashboard": 1800,    # 30 min - Dashboard completo
}

def get_cache_key(prefix: str, user_id: str, **kwargs) -> str:
    """Generar clave de cache única por usuario y filtros"""
    clean_params = {k: v for k, v in kwargs.items() if v is not None}
    clean_params["user_id"] = user_id
    key_str = json.dumps(clean_params, sort_keys=True)
    hash_key = hashlib.md5(key_str.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_key}"

def get_from_flask_cache(key: str, ttl: int = 300) -> Optional[Any]:
    """Obtener del cache en memoria"""
    if key in _flask_cache:
        timestamp = _cache_timestamps.get(key, 0)
        if time.time() - timestamp < ttl:
            return _flask_cache[key]
        else:
            # Limpiar cache expirado
            del _flask_cache[key]
            del _cache_timestamps[key]
    return None

def set_in_flask_cache(key: str, data: Any):
    """Guardar en cache en memoria"""
    _flask_cache[key] = data
    _cache_timestamps[key] = time.time()

def run_async_in_flask(async_func, *args, **kwargs):
    """Ejecutar función asíncrona en Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_func(*args, **kwargs))
    finally:
        loop.close()

# ================================
# 🎯 FUNCIONES OPTIMIZADAS
# ================================

async def get_quick_dashboard_data_async(df_edp_raw: pd.DataFrame, df_log_raw: pd.DataFrame, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Obtener solo datos esenciales del dashboard de forma asíncrona"""
    loop = asyncio.get_event_loop()
    
    def calculate_quick_metrics():
        """Calcular solo métricas esenciales"""
        try:
            # Verificar que el DataFrame no esté vacío
            if df_edp_raw.empty:
                return {
                    "total_edps": 0, "total_pagados": 0, "total_pendientes": 0,
                    "monto_total": 0, "monto_pagado": 0, "dias_promedio": 0,
                    "criticos": 0, "registros": [], "dso_global": 0,
                    "calculation_time": 0, "data_source": "quick_calculation"
                }
            
            # Aplicar filtros básicos
            df = df_edp_raw.copy()
            
            # Asegurar que las columnas críticas existan
            required_columns = ["estado", "monto_aprobado", "dias_espera"]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 0 if col in ["monto_aprobado", "dias_espera"] else "pendiente"
            
            # Aplicar filtros si las columnas existen
            if "mes" in df.columns and filters.get("mes"):
                df = df[df["mes"] == filters["mes"]]
            if "jefe_proyecto" in df.columns and filters.get("jefe_proyecto") and filters["jefe_proyecto"] != "todos":
                df = df[df["jefe_proyecto"] == filters["jefe_proyecto"]]
            if "cliente" in df.columns and filters.get("cliente") and filters["cliente"] != "todos":
                df = df[df["cliente"] == filters["cliente"]]
            if filters.get("estado") == "pendientes":
                df = df[df["estado"].isin(["revisión", "enviado"])]
            elif filters.get("estado") and filters["estado"] != "todos":
                df = df[df["estado"] == filters["estado"]]
            
            # Calcular métricas básicas
            total_edps = len(df)
            total_pagados = len(df[df["estado"] == "pagado"])
            total_pendientes = len(df[df["estado"].isin(["enviado", "revisión"])])
            
            # Montos (asegurar que son numéricos)
            df["monto_aprobado"] = pd.to_numeric(df["monto_aprobado"], errors="coerce").fillna(0)
            monto_total = float(df["monto_aprobado"].sum())
            monto_pagado = float(df[df["estado"] == "pagado"]["monto_aprobado"].sum())
            
            # Días promedio
            df["dias_espera"] = pd.to_numeric(df["dias_espera"], errors="coerce").fillna(0)
            dias_promedio = float(df["dias_espera"].mean()) if not df["dias_espera"].isna().all() else 0
            
            # Críticos
            criticos = len(df[df.get("critico", False) == True])
            
            # Limpiar registros de valores NaT/NaN para serialización
            registros_limpios = []
            for record in df.to_dict('records'):
                record_limpio = {}
                for key, value in record.items():
                    if pd.isna(value) or str(value) == 'NaT':
                        record_limpio[key] = None
                    elif hasattr(value, 'isoformat'):  # datetime objects
                        try:
                            record_limpio[key] = value.isoformat()
                        except:
                            record_limpio[key] = str(value) if value is not None else None
                    else:
                        record_limpio[key] = value
                registros_limpios.append(record_limpio)
            
            return {
                "total_edps": total_edps,
                "total_pagados": total_pagados, 
                "total_pendientes": total_pendientes,
                "monto_total": monto_total,
                "monto_pagado": monto_pagado,
                "dias_promedio": round(dias_promedio, 1),
                "criticos": criticos,
                "registros": registros_limpios,  # Registros limpios para la tabla
                "dso_global": round(dias_promedio, 1),  # DSO simplificado
                "calculation_time": 0,
                "data_source": "quick_calculation"
            }
            
        except Exception as e:
            logger.error(f"Error en quick metrics: {e}")
            return {
                "total_edps": 0,
                "total_pagados": 0,
                "total_pendientes": 0,
                "monto_total": 0,
                "monto_pagado": 0,
                "dias_promedio": 0,
                "criticos": 0,
                "registros": [],
                "dso_global": 0,
                "error": str(e)
            }
    
    return await loop.run_in_executor(_executor, calculate_quick_metrics)

def get_full_dashboard_data_sync(df_edp_raw: pd.DataFrame, df_log_raw: pd.DataFrame, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Obtener datos completos del dashboard (función original)"""
    try:
        controller_service = ControllerService()
        dashboard_response = controller_service.get_processed_dashboard_context(
            df_edp_raw, df_log_raw, filters
        )
        
        if dashboard_response and dashboard_response.success:
            return dashboard_response.data
        else:
            return {}
            
    except Exception as e:
        logger.error(f"Error en full dashboard: {e}")
        return {}

# ================================
# 🎯 CONTROLADOR OPTIMIZADO
# ================================

# Funciones auxiliares simplificadas
def _get_user_access_level() -> str:
    """Determina el nivel de acceso del usuario actual."""
    if not current_user.is_authenticated:
        return 'none'
    
    role = getattr(current_user, 'rol', '')
    
    if role in ['admin', 'administrador']:
        return 'full'  # Ve todo
    elif role in ['manager', 'controller']:
        return 'full'  # Ve todo
    elif role in ['jefe_proyecto', 'miembro_equipo_proyecto']:
        return 'restricted'  # Solo ve sus proyectos
    else:
        return 'none'

def _parse_filters(request) -> Dict[str, Any]:
    """Parse filters from request."""
    return {
        'mes': request.args.get('mes', ''),
        'jefe_proyecto': request.args.get('jefe_proyecto', ''),
        'cliente': request.args.get('cliente', ''),
        'estado': request.args.get('estado', '')
    }

kanban_opt_bp = Blueprint('kanban_optimized', __name__, url_prefix='/kanban-opt')

@kanban_opt_bp.route('/')
@login_required
@require_project_manager_or_above
def vista_kanban_optimizada():
    """Vista Kanban OPTIMIZADA con cache y carga rápida."""
    try:
        start_time = time.time()
        
        access_level = _get_user_access_level()
        
        if access_level == 'none':
            flash('No tienes permisos para acceder a esta vista.', 'error')
            return redirect(url_for('main.index'))
        
        # Parse filters
        filters = _parse_filters(request)
        user_id = str(current_user.id) if current_user.is_authenticated else "anonymous"
        
        logger.info(f"Usuario {current_user.username} accediendo a Kanban OPTIMIZADO - Nivel: {access_level}")
        
        # ===== VERIFICAR CACHE PRIMERO =====
        cache_key = get_cache_key("quick_dashboard", user_id, **filters)
        cached_data = get_from_flask_cache(cache_key, CACHE_TTL["quick_dashboard"])
        
        if cached_data:
            logger.info(f"✅ Cache HIT para usuario {user_id} - Tiempo: {round(time.time() - start_time, 3)}s")
            
            # Agregar metadata de cache
            cached_data["from_cache"] = True
            cached_data["cache_time"] = round(time.time() - start_time, 3)
            
            return render_template('controller/controller_kanban.html', **cached_data)
        
        # ===== CARGAR DATOS BASE =====
        controller_service = ControllerService()
        kanban_service = KanbanService()
        
        datos_response = controller_service.load_related_data()
        
        if not datos_response.success:
            logger.error(f"Error cargando datos relacionados: {datos_response.message}")
            flash('Error al cargar datos. Inténtalo de nuevo.', 'error')
            return render_template('controller/controller_kanban.html', 
                                 registros=[], columnas={}, estadisticas={})

        datos_relacionados = datos_response.data
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        df_log_raw = pd.DataFrame(datos_relacionados.get("logs", []))
        
        # ===== OBTENER DATOS KANBAN (RÁPIDO) =====
        kanban_response = kanban_service.get_kanban_board_data(df_edp_raw, filters)
        kanban_data = kanban_response.data if kanban_response.success else {}
        
        # ===== OBTENER DASHBOARD RÁPIDO =====
        dashboard_data = run_async_in_flask(get_quick_dashboard_data_async, df_edp_raw, df_log_raw, filters)
        
        # ===== PREPARAR TEMPLATE CONTEXT =====
        template_context = {
            # Datos del Kanban
            "columnas": kanban_data.get("columnas", {}),
            "estadisticas": kanban_data.get("estadisticas", {}),
            
            # Datos rápidos del dashboard
            "registros": dashboard_data.get("registros", []),
            "total_edps": dashboard_data.get("total_edps", 0),
            "total_pagados": dashboard_data.get("total_pagados", 0),
            "total_pendientes": dashboard_data.get("total_pendientes", 0),
            "monto_total": dashboard_data.get("monto_total", 0),
            "monto_pagado": dashboard_data.get("monto_pagado", 0),
            "dias_promedio": dashboard_data.get("dias_promedio", 0),
            "criticos": dashboard_data.get("criticos", 0),
            "dso_global": dashboard_data.get("dso_global", 0),
            
            # Filtros y opciones
            "filtros": filters,
            "meses": kanban_data.get("filter_options", {}).get("meses", []),
            "jefe_proyectos": kanban_data.get("filter_options", {}).get("jefe_proyectos", []),
            "clientes": kanban_data.get("filter_options", {}).get("clientes", []),
            "estados_detallados": kanban_data.get("filter_options", {}).get("estados_detallados", []),
            
            # Contexto de usuario
            "user_access_level": access_level,
            "current_user_role": getattr(current_user, 'rol', ''),
            "is_restricted_user": access_level == 'restricted',
            
            # Metadata de performance
            "from_cache": False,
            "load_time": round(time.time() - start_time, 3),
            "data_source": dashboard_data.get("data_source", "quick_calculation"),
            "now": datetime.now(),
            
            # Configuración para carga completa en background
            "enable_background_loading": True,
        }
        
        # ===== GUARDAR EN CACHE =====
        set_in_flask_cache(cache_key, template_context)
        
        logger.info(f"✅ Kanban optimizado cargado en {template_context['load_time']}s - Registros: {len(template_context['registros'])}")
        
        return render_template('controller/controller_kanban.html', **template_context)

    except Exception as e:
        logger.error(f"Error en vista_kanban_optimizada: {str(e)}")
        flash(f"Error al cargar el tablero Kanban: {str(e)}", "error")
        return redirect(url_for('main.index'))

@kanban_opt_bp.route('/api/full-dashboard-data')
@login_required
def get_full_dashboard_data():
    """API endpoint para cargar datos completos en background"""
    try:
        start_time = time.time()
        
        filters = _parse_filters(request)
        user_id = str(current_user.id)
        
        # Verificar cache completo
        cache_key = get_cache_key("full_dashboard", user_id, **filters)
        cached_data = get_from_flask_cache(cache_key, CACHE_TTL["full_dashboard"])
        
        if cached_data:
            return jsonify({
                "success": True,
                "data": cached_data,
                "from_cache": True,
                "load_time": round(time.time() - start_time, 3)
            })
        
        # Cargar datos completos
        controller_service = ControllerService()
        datos_response = controller_service.load_related_data()
        
        if not datos_response.success:
            return jsonify({"success": False, "error": "Error cargando datos"}), 500
        
        datos_relacionados = datos_response.data
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        df_log_raw = pd.DataFrame(datos_relacionados.get("logs", []))
        
        # Obtener dashboard completo (función original)
        full_dashboard_data = get_full_dashboard_data_sync(df_edp_raw, df_log_raw, filters)
        
        # Preparar respuesta
        response_data = {
            "registros": full_dashboard_data.get("registros", []),
            "kpis_completos": {
                "dso_global": full_dashboard_data.get("dso_global", 0),
                "dso_var": full_dashboard_data.get("dso_var", 0),
                "top_dso_proyectos": full_dashboard_data.get("top_dso_proyectos", []),
                "total_edp_global": full_dashboard_data.get("total_edp_global", 0),
                "total_validados_global": full_dashboard_data.get("total_validados_global", 0),
                # Agregar más KPIs según necesidad
            },
            "charts": full_dashboard_data.get("charts", {}),
            "alertas": full_dashboard_data.get("alertas", []),
            "load_time": round(time.time() - start_time, 3),
            "from_cache": False
        }
        
        # Guardar en cache
        set_in_flask_cache(cache_key, response_data)
        
        return jsonify({
            "success": True,
            "data": response_data,
            "from_cache": False
        })
        
    except Exception as e:
        logger.error(f"Error en get_full_dashboard_data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@kanban_opt_bp.route('/api/cache-status')
@login_required
def get_cache_status():
    """Obtener estado del cache"""
    try:
        return jsonify({
            "cache_items": len(_flask_cache),
            "cache_keys": list(_flask_cache.keys())[:10],  # Primeras 10
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@kanban_opt_bp.route('/api/clear-cache', methods=['POST'])
@login_required
def clear_cache():
    """Limpiar cache manualmente"""
    try:
        cleared_count = len(_flask_cache)
        _flask_cache.clear()
        _cache_timestamps.clear()
        
        return jsonify({
            "success": True,
            "cleared_items": cleared_count,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Importar funciones de actualización del controlador original
from .kanban_controller import update_edp_status, _procesar_actualizacion_estado

# Re-exportar con el mismo nombre para compatibilidad
kanban_opt_bp.add_url_rule('/update_estado', 'update_edp_status', update_edp_status, methods=['POST']) 