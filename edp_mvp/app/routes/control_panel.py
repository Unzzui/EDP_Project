"""
Controlador unificado para la vista Kanban con control de acceso por roles.
Permite que admin y manager vean todos los EDPs, mientras que JP solo ve los suyos.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
import logging
import json
import pandas as pd

from ..services.dashboard_service import ControllerService
from ..services.manager_service import ManagerService
from ..services.control_panel_service import KanbanService
from ..services.project_service import ProjectManagerService
from ..utils.auth_utils import require_controller_or_above, require_project_manager_or_above
from ..utils.format_utils import FormatUtils
from ..utils.supabase_adapter import update_row, log_cambio_edp

# Create blueprint
control_panel_bp = Blueprint('control_panel', __name__, url_prefix='/control')

# Initialize services
controller_service = ControllerService()
manager_service = ManagerService()
kanban_service = KanbanService()
pm_service = ProjectManagerService()

logger = logging.getLogger(__name__)

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

def _get_manager_name_for_filtering() -> Optional[str]:
    """Obtiene el nombre del manager para filtrar, solo si el usuario es JP."""
    access_level = _get_user_access_level()
    
    if access_level != 'restricted':
        return None  # No filtrar por manager
    
    # Para usuarios restringidos, determinar el nombre del manager
    if hasattr(current_user, 'jefe_asignado') and current_user.jefe_asignado:
        return current_user.jefe_asignado
    elif hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
        return current_user.nombre_completo
    elif hasattr(current_user, 'username') and current_user.username:
        return current_user.username
    else:
        return None

def _apply_role_based_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Aplica filtros basados en el rol del usuario."""
    access_level = _get_user_access_level()
    
    if access_level == 'restricted':
        manager_name = _get_manager_name_for_filtering()
        if manager_name:
            filters['jefe_proyecto'] = manager_name
            logger.info(f"Aplicando filtro por jefe_proyecto: {manager_name}")
    
    return filters

def _parse_filters(request) -> Dict[str, Any]:
    """Parse filters from request."""
    filters = {
        'mes': request.args.get('mes', ''),
        'proyecto': request.args.get('proyecto', ''),
        'cliente': request.args.get('cliente', ''),
        'estado_detallado': request.args.get('estado_detallado', ''),
        'jefe_proyecto': request.args.get('jefe_proyecto', ''),
        'monto_min': request.args.get('monto_min', ''),
        'monto_max': request.args.get('monto_max', ''),
        'dias_min': request.args.get('dias_min', ''),
        'dias_max': request.args.get('dias_max', ''),
        'buscar': request.args.get('buscar', '').strip(),
        'mostrar_validados_antiguos': request.args.get('mostrar_validados_antiguos', 'false') == 'true'
    }
    
    # Aplicar filtros basados en rol
    filters = _apply_role_based_filters(filters)
    
    return filters

def _get_empty_kanban_data() -> Dict[str, Any]:
    """Retorna datos vacíos para casos de error."""
    return {
        'columnas': {},
        'estadisticas': {},
        'registros': [],
        'filtros': {},
        'meses': [],
        'jefe_proyectos': [],
        'clientes': [],
        'estados_detallados': [],
        'dso_global': 0,
        'now': datetime.now()
    }

@control_panel_bp.route('/')
@login_required
@require_project_manager_or_above
def vista_kanban():
    """Vista Kanban unificada con control de acceso por roles."""
    try:
        access_level = _get_user_access_level()
        
        if access_level == 'none':
            flash('No tienes permisos para acceder a esta vista.', 'error')
            return redirect(url_for('landing.index'))
        
        # Parse filters
        filters = _parse_filters(request)
        manager_name = _get_manager_name_for_filtering()
        
        logger.info(f"Usuario {current_user.username} accediendo a Kanban - Nivel: {access_level}, Manager: {manager_name}")
        
        # ===== CARGAR DATOS RELACIONADOS =====
        # Usar siempre controller_service pero con filtros aplicados
        datos_response = controller_service.load_related_data()
        
        if not datos_response.success:
            logger.error(f"Error cargando datos relacionados: {datos_response.message}")
            flash('Error al cargar datos. Inténtalo de nuevo.', 'error')
            return render_template('controller/controller_kanban.html', **_get_empty_kanban_data())

        datos_relacionados = datos_response.data
        logger.info(f"Datos cargados: {len(datos_relacionados.get('edps', []))} EDPs")

        # Extract raw DataFrames
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        df_log_raw = pd.DataFrame(datos_relacionados.get("logs", []))

        # ===== OBTENER DATOS DEL KANBAN =====
        kanban_response = kanban_service.get_kanban_board_data(df_edp_raw, filters)
        
        if not kanban_response.success:
            logger.error(f"Error en kanban service: {kanban_response.message}")
            flash('Error al cargar el tablero Kanban.', 'error')
            return render_template('controller/controller_kanban.html', **_get_empty_kanban_data())

        kanban_data = kanban_response.data

        # ===== OBTENER DATOS PROCESADOS PARA LA TABLA =====
        dashboard_response = controller_service.get_processed_dashboard_context(
            df_edp_raw, df_log_raw, filters
        )

        if dashboard_response and dashboard_response.success:
            dashboard_context = dashboard_response.data
            registros = dashboard_context.get('registros', [])
        else:
            registros = []
            dashboard_context = {}

        # ===== PREPARAR DATOS PARA EL TEMPLATE =====
        template_context = {
            # Datos del Kanban
            "columnas": kanban_data.get("columnas", {}),
            "estadisticas": kanban_data.get("estadisticas", {}),
            
            # Datos para la tabla
            "registros": registros,
            
            # Filtros y opciones
            "filtros": filters,
            "meses": kanban_data.get("filter_options", {}).get("meses", []),
            "jefe_proyectos": kanban_data.get("filter_options", {}).get("jefe_proyectos", []),
            "clientes": kanban_data.get("filter_options", {}).get("clientes", []),
            "estados_detallados": kanban_data.get("filter_options", {}).get("estados_detallados", []),
            
            # Contexto de usuario para JavaScript
            "user_access_level": access_level,
            "manager_name": manager_name,
            "current_user_role": getattr(current_user, 'rol', ''),
            "is_restricted_user": access_level == 'restricted',
            
            # Datos adicionales
            "now": datetime.now(),
            "dso_global": dashboard_context.get('dso_global', 0),
        }
        
        # Agregar datos adicionales del dashboard si están disponibles
        if dashboard_context:
            for key in ['kpis', 'charts', 'alertas', 'dso_var']:
                if key in dashboard_context:
                    template_context[key] = dashboard_context[key]

        logger.info(f"Vista kanban cargada exitosamente - Acceso: {access_level}, Registros: {len(registros)}")
        
        # Usar el template existente del controller
        return render_template('controller/controller_kanban.html', **template_context)

    except Exception as e:
        logger.error(f"Error en vista_kanban: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error al cargar el tablero Kanban: {str(e)}", "error")
        return redirect(url_for('landing.index'))

@control_panel_bp.route('/update_estado', methods=['POST'])
@login_required
def update_edp_status():
    """Actualizar estado de EDP desde el kanban board con control de acceso."""
    try:
        access_level = _get_user_access_level()
        
        if access_level == 'none':
            return jsonify({"error": "Sin permisos"}), 403
        
        data = request.get_json()
        edp_id = data.get("edp_id")
        nuevo_estado = data.get("nuevo_estado", "").lower()
        estado_anterior = data.get("estado_anterior", "").lower()
        conformidad_enviada = data.get("conformidad_enviada", False)
        proyecto = data.get("proyecto", None)

        if not edp_id or not nuevo_estado:
            return jsonify({"error": "Datos incompletos"}), 400

        # Verificar permisos para usuarios restringidos
        if access_level == 'restricted':
            manager_name = _get_manager_name_for_filtering()
            if manager_name and proyecto:
                # Para usuarios restringidos, verificar que pueden actualizar este EDP
                # Esto se podría implementar con una verificación adicional si es necesario
                pass

        # Obtener el usuario real desde Flask-Login
        usuario = "Sistema"
        if current_user.is_authenticated:
            if hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
                usuario = current_user.nombre_completo
            elif hasattr(current_user, 'email') and current_user.email:
                usuario = current_user.email
            elif hasattr(current_user, 'username') and current_user.username:
                usuario = current_user.username
            else:
                usuario = f"User ID: {current_user.id}"

        # Procesar actualización en background con socketio
        from .. import socketio
        socketio.start_background_task(
            _procesar_actualizacion_estado,
            edp_id,
            nuevo_estado,
            conformidad_enviada,
            usuario,
            estado_anterior,
            proyecto,
        )

        return jsonify({"success": True, "queued": True}), 202
        
    except Exception as e:
        logger.error(f"Error en update_edp_status: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


def _procesar_actualizacion_estado(edp_id: str, nuevo_estado: str, conformidad: bool, usuario: str, estado_anterior: str = None, proyecto: str = None):
    """Tarea en segundo plano para persistir el cambio de estado."""
    try:
        from ..services.cache_invalidation_service import CacheInvalidationService
        from .. import socketio
        
        logger.info(f"🔄 Procesando actualización de estado para EDP {edp_id}:")
        logger.info(f"   - Nuevo estado: {nuevo_estado}")
        logger.info(f"   - Estado anterior: {estado_anterior}")
        logger.info(f"   - Conformidad: {conformidad}")
        logger.info(f"   - Usuario: {usuario}")

        # Obtener proyecto por id del edp
        controller_service = ControllerService()
        df = controller_service.load_related_data().data
        df_edps = pd.DataFrame(df.get("edps", []))
        if not proyecto:
            proyecto = df_edps[df_edps["n_edp"] == edp_id]["proyecto"].values[0] if not df_edps[df_edps["n_edp"] == edp_id].empty else None
      
        logger.info(f"   - Proyecto asociado: {proyecto}")
        
        # Usar kanban service para actualizar
        additional = {"conformidad_enviada": "Sí"} if conformidad else None
        resp = kanban_service.update_edp_status(edp_id, nuevo_estado, additional)

        logger.info(f"🔍 Respuesta del servicio kanban:")
        logger.info(f"   - Success: {resp.success}")
        logger.info(f"   - Message: {resp.message}")
        if hasattr(resp, 'data'):
            logger.info(f"   - Data: {resp.data}")
        
        if resp.success:
            # Registrar TODOS los cambios en el log con el usuario detectado
            try:
                # Obtener los cambios reales desde la respuesta del servicio
                updates_realizados = resp.data.get("updates", {})
                logger.info(f"🔍 Cambios realizados: {updates_realizados}")
                
                # Obtener valores anteriores del EDP
                edp_anterior = df_edps[df_edps["n_edp"] == edp_id]
                valores_anteriores = {}
                if not edp_anterior.empty:
                    valores_anteriores = {
                        "estado": estado_anterior or edp_anterior.iloc[0]["estado"],
                        "conformidad_enviada": edp_anterior.iloc[0]["conformidad_enviada"],
                        "n_conformidad": edp_anterior.iloc[0]["n_conformidad"],
                        "fecha_conformidad": edp_anterior.iloc[0]["fecha_conformidad"],
                        "fecha_estimada_pago": edp_anterior.iloc[0]["fecha_estimada_pago"],
                    }
                
                # Registrar cada campo que cambió
                for campo, nuevo_valor in updates_realizados.items():
                    valor_anterior = valores_anteriores.get(campo, "")
                    
                    # Solo registrar si realmente cambió
                    if str(nuevo_valor) != str(valor_anterior):
                        log_cambio_edp(
                            n_edp=edp_id,
                            proyecto=proyecto,
                            campo=campo,
                            antes=valor_anterior,
                            despues=nuevo_valor,
                            usuario=usuario
                        )
                        logger.info(f"📝 Cambio registrado en log: EDP {edp_id} {campo} {valor_anterior} → {nuevo_valor} por {usuario}")
                        
            except Exception as log_error:
                logger.error(f"⚠️ Error al registrar cambios en log: {log_error}")
                logger.error(traceback.format_exc())
            
            # Invalidar cache automáticamente
            cache_invalidation = CacheInvalidationService()
            updated_fields = list(resp.data.get("updates", {}).keys())
            cache_invalidation.register_data_change('edp_state_changed', [edp_id], 
                                                  {'updated_fields': updated_fields})
            
            # Convertir tipos numpy a tipos nativos antes de emitir
            def convert_numpy_types_for_emit(obj):
                """Convierte tipos numpy a tipos nativos de Python para serialización JSON"""
                if isinstance(obj, dict):
                    return {key: convert_numpy_types_for_emit(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types_for_emit(item) for item in obj]
                elif hasattr(obj, 'item'):  # numpy types
                    return obj.item()
                elif hasattr(obj, 'tolist'):  # numpy arrays
                    return obj.tolist()
                elif pd.isna(obj):  # pandas NaT/NaN
                    return None
                else:
                    return obj
            
            # Convertir datos antes de emitir
            updates_data = {"estado": nuevo_estado, **resp.data.get("updates", {})}
            updates_serializable = convert_numpy_types_for_emit(updates_data)
            cambios_serializable = convert_numpy_types_for_emit(resp.data.get("updates", {}))
            
            # Emit events for both manager dashboard and kanban board
            socketio.emit("edp_actualizado", {
                "edp_id": str(edp_id), 
                "updates": updates_serializable,
                "usuario": str(usuario),
                "timestamp": datetime.now().isoformat()
            })
            socketio.emit("estado_actualizado", {
                "edp_id": str(edp_id), 
                "nuevo_estado": str(nuevo_estado), 
                "cambios": cambios_serializable
            })
            socketio.emit("cache_invalidated", {
                "type": "edp_state_changed",
                "affected_ids": [str(edp_id)],
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"✅ Actualización de estado completada exitosamente para EDP {edp_id}")
        else:
            logger.error(f"❌ Error en actualización de estado: {resp.message}")
            
    except Exception as exc:
        logger.error(f"💥 Excepción en _procesar_actualizacion_estado: {exc}")
        logger.error(traceback.format_exc())


def _procesar_actualizacion_estado_by_id(internal_id: int, edp_id: str, nuevo_estado: str, conformidad: bool, usuario: str, estado_anterior: str = None, proyecto: str = None):
    """Tarea en segundo plano para persistir el cambio de estado usando ID interno."""
    try:
        from ..services.cache_invalidation_service import CacheInvalidationService
        from .. import socketio
        
        logger.info(f"🔄 Procesando actualización de estado por ID interno {internal_id} (EDP {edp_id}):")
        logger.info(f"   - Nuevo estado: {nuevo_estado}")
        logger.info(f"   - Estado anterior: {estado_anterior}")
        logger.info(f"   - Conformidad: {conformidad}")
        logger.info(f"   - Usuario: {usuario}")
        logger.info(f"   - Proyecto asociado: {proyecto}")
        
        # Usar kanban service para actualizar (sigue usando n_edp internamente)
        additional = {"conformidad_enviada": "Sí"} if conformidad else None
        resp = kanban_service.update_edp_status(edp_id, nuevo_estado, additional)

        logger.info(f"🔍 Respuesta del servicio kanban:")
        logger.info(f"   - Success: {resp.success}")
        logger.info(f"   - Message: {resp.message}")
        if hasattr(resp, 'data'):
            logger.info(f"   - Data: {resp.data}")
        
        if resp.success:
            # Registrar TODOS los cambios en el log con el usuario detectado
            try:
                # Obtener los cambios reales desde la respuesta del servicio
                updates_realizados = resp.data.get("updates", {})
                logger.info(f"🔍 Cambios realizados: {updates_realizados}")
                
                # Obtener valores anteriores del EDP usando el ID interno
                controller_service = ControllerService()
                df = controller_service.load_related_data().data
                df_edps = pd.DataFrame(df.get("edps", []))
                edp_anterior = df_edps[df_edps["id"] == internal_id]
                
                valores_anteriores = {}
                if not edp_anterior.empty:
                    valores_anteriores = {
                        "estado": estado_anterior or edp_anterior.iloc[0]["estado"],
                        "conformidad_enviada": edp_anterior.iloc[0]["conformidad_enviada"],
                        "n_conformidad": edp_anterior.iloc[0]["n_conformidad"],
                        "fecha_conformidad": edp_anterior.iloc[0]["fecha_conformidad"],
                        "fecha_estimada_pago": edp_anterior.iloc[0]["fecha_estimada_pago"],
                    }
                
                # Registrar cada campo que cambió
                for campo, nuevo_valor in updates_realizados.items():
                    valor_anterior = valores_anteriores.get(campo, "")
                    
                    # Solo registrar si realmente cambió
                    if str(nuevo_valor) != str(valor_anterior):
                        log_cambio_edp(
                            n_edp=edp_id,
                            proyecto=proyecto,
                            campo=campo,
                            antes=valor_anterior,
                            despues=nuevo_valor,
                            usuario=usuario
                        )
                        logger.info(f"📝 Cambio registrado en log: EDP {edp_id} (ID {internal_id}) {campo} {valor_anterior} → {nuevo_valor} por {usuario}")
                        
            except Exception as log_error:
                logger.error(f"⚠️ Error al registrar cambios en log: {log_error}")
                logger.error(traceback.format_exc())
            
            # Invalidar cache automáticamente
            cache_invalidation = CacheInvalidationService()
            updated_fields = list(resp.data.get("updates", {}).keys())
            cache_invalidation.register_data_change('edp_state_changed', [edp_id], 
                                                  {'updated_fields': updated_fields})
            
            # Convertir tipos numpy a tipos nativos antes de emitir
            def convert_numpy_types_for_emit(obj):
                """Convierte tipos numpy a tipos nativos de Python para serialización JSON"""
                if isinstance(obj, dict):
                    return {key: convert_numpy_types_for_emit(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types_for_emit(item) for item in obj]
                elif hasattr(obj, 'item'):  # numpy types
                    return obj.item()
                elif hasattr(obj, 'tolist'):  # numpy arrays
                    return obj.tolist()
                elif pd.isna(obj):  # pandas NaT/NaN
                    return None
                else:
                    return obj
            
            # Convertir datos antes de emitir
            updates_data = {"estado": nuevo_estado, **resp.data.get("updates", {})}
            updates_serializable = convert_numpy_types_for_emit(updates_data)
            cambios_serializable = convert_numpy_types_for_emit(resp.data.get("updates", {}))
            
            # Emit events for both manager dashboard and kanban board
            socketio.emit("edp_actualizado", {
                "edp_id": str(edp_id),
                "internal_id": int(internal_id),
                "updates": updates_serializable,
                "usuario": str(usuario),
                "timestamp": datetime.now().isoformat()
            })
            socketio.emit("estado_actualizado", {
                "edp_id": str(edp_id),
                "internal_id": int(internal_id),
                "nuevo_estado": str(nuevo_estado), 
                "cambios": cambios_serializable
            })
            socketio.emit("cache_invalidated", {
                "type": "edp_state_changed",
                "affected_ids": [str(edp_id)],
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"✅ Actualización de estado completada exitosamente para EDP {edp_id} (ID interno {internal_id})")
        else:
            logger.error(f"❌ Error en actualización de estado: {resp.message}")
            
    except Exception as exc:
        logger.error(f"💥 Excepción en _procesar_actualizacion_estado_by_id: {exc}")
        logger.error(traceback.format_exc())

@control_panel_bp.route('/api/get-edp/<edp_id>')
@login_required
def get_edp_data(edp_id):
    """Obtener datos de un EDP específico con control de acceso."""
    try:
        access_level = _get_user_access_level()
        
        if access_level == 'none':
            return jsonify({"error": "Sin permisos"}), 403
        
        # Usar el servicio para obtener los datos
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            return jsonify({"error": "Error cargando datos"}), 500
            
        datos_relacionados = datos_response.data
        df_edp = pd.DataFrame(datos_relacionados.get("edps", []))
        
        if not df_edp.empty:
            edp_row = df_edp[df_edp['n_edp'].astype(str) == str(edp_id)]
            
            if not edp_row.empty:
                edp_data = edp_row.iloc[0].to_dict()
                
                # Verificar permisos para usuarios restringidos
                if access_level == 'restricted':
                    manager_name = _get_manager_name_for_filtering()
                    if manager_name and edp_data.get('jefe_proyecto') != manager_name:
                        return jsonify({"error": "Sin permisos para este EDP"}), 403
                
                # Limpiar valores NaN
                for key, value in edp_data.items():
                    if pd.isna(value):
                        edp_data[key] = None
                
                return jsonify(edp_data)
            else:
                return jsonify({"error": "EDP no encontrado"}), 404
        else:
            return jsonify({"error": "No hay datos disponibles"}), 500
            
    except Exception as e:
        logger.error(f"Error obteniendo datos del EDP {edp_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
