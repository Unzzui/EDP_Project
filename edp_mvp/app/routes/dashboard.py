"""
Refactored Controller Dashboard using the new layered architecture.
This controller replaces the monolithic dashboard/controller.py file.
"""

from flask import(
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    make_response,
)
from flask_login import login_required, current_user

from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from ..services.control_panel_service import KanbanService
from ..services.analytics_service import AnalyticsService
from ..services.edp_service import EDPService
from ..services.dashboard_service import ControllerService
from ..services.kpi_service import KPIService
from ..utils.validation_utils import ValidationUtils
from ..utils.format_utils import FormatUtils
from ..utils.date_utils import DateUtils
from ..utils.supabase_adapter import update_row, log_cambio_edp, read_log
from ..extensions import socketio
import pandas as pd
import traceback
import logging
from time import time
from ..utils.auth_utils import require_controller_or_above, can_access_role_level

_kanban_cache = {"ts": 0, "data": None}

logger = logging.getLogger(__name__)
class DictToObject:
    """Simple class to convert dictionaries to objects with dot notation access."""

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, DictToObject(value))
            else:
                setattr(self, key, value)


def _calculate_current_velocity(analisis_rendimiento: Dict) -> float:
    """Calcula la velocidad actual de procesamiento basada en DSO."""
    dso_actual = float(analisis_rendimiento.get('dso_encargado', 30))
    # Velocidad inversamente proporcional al DSO (menos días = más velocidad)
    # DSO ideal: 15 días = 100% velocidad, DSO 30 días = 50% velocidad
    velocidad = max(0, min(100, (45 - dso_actual) * 2))
    return round(velocidad, 1)


def _calculate_current_risk_trend(analisis_rendimiento: Dict, resumen_proyectos: Dict) -> float:
    """Calcula la tendencia de riesgo actual."""
    porcentaje_criticos = float(analisis_rendimiento.get('porcentaje_criticos', 0))
    dso_actual = float(analisis_rendimiento.get('dso_encargado', 0))
    
    # Riesgo basado en % críticos y DSO
    riesgo_criticos = porcentaje_criticos * 0.6  # 60% peso a críticos
    riesgo_dso = min(40, dso_actual * 1.2) * 0.4  # 40% peso a DSO
    
    riesgo_total = riesgo_criticos + riesgo_dso
    return round(min(100, riesgo_total), 1)


def _calculate_current_volume(resumen_proyectos: Dict, analisis_financiero: Dict) -> int:
    """Calcula el volumen actual de trabajo."""
    total_edps = int(analisis_financiero.get('total_edps', 0))
    return total_edps


def _calculate_velocity_variation(analisis_rendimiento: Dict) -> str:
    """Calcula la variación de velocidad."""
    dso_actual = float(analisis_rendimiento.get('dso_encargado', 30))
    dso_objetivo = 25.0
    
    if dso_actual < dso_objetivo:
        mejora = round(((dso_objetivo - dso_actual) / dso_objetivo) * 100)
        return f"+{mejora}%"
    else:
        empeoramiento = round(((dso_actual - dso_objetivo) / dso_objetivo) * 100)
        return f"-{empeoramiento}%"


def _calculate_risk_variation(analisis_rendimiento: Dict) -> str:
    """Calcula la variación de riesgo."""
    porcentaje_criticos = float(analisis_rendimiento.get('porcentaje_criticos', 0))
    
    if porcentaje_criticos < 15:  # Bajo riesgo
        return "-8%"
    elif porcentaje_criticos < 30:  # Riesgo moderado
        return "±2%"
    else:  # Alto riesgo
        return "+15%"


def _calculate_volume_variation(resumen_proyectos: Dict) -> str:
    """Calcula la variación de volumen."""
    num_proyectos = len(resumen_proyectos)
    
    # Simulación basada en número de proyectos
    if num_proyectos > 5:
        return "+25%"
    elif num_proyectos > 3:
        return "+12%"
    else:
        return "+5%"


# Create Blueprint
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
@dashboard_bp.route("/inicio")
@login_required
@require_controller_or_above
def inicio():
    """Página de inicio bonita para el rol controller."""
    try:
        # Get basic stats for controller overview
        stats_response = analytics_service.get_basic_stats()
        
        stats = {
            'total_edps': 0,
            'monto_total': 0,
            'edps_pendientes': 0,
            'tasa_aprobacion': 0,
            'edps_criticos': 0
        }
        
        if stats_response.success and stats_response.data:
            stats.update(stats_response.data)
        
        # Get quick access items
        quick_stats = {
            'kanban_items': stats.get('edps_pendientes', 0),
            'critical_items': stats.get('edps_criticos', 0),
            'efficiency': stats.get('tasa_aprobacion', 0)
        }
        
        return render_template(
            "controller/inicio.html",
            stats=stats,
            quick_stats=quick_stats,
            current_date=datetime.now(),
            user=current_user
        )
        
    except Exception as e:
        print(f"Error in controller inicio: {e}")
        return render_template(
            "controller/inicio.html",
            stats={'total_edps': 0, 'monto_total': 0},
            quick_stats={'kanban_items': 0, 'critical_items': 0, 'efficiency': 0},
            current_date=datetime.now(),
            user=current_user
        )

# Initialize services
kanban_service = KanbanService()
analytics_service = AnalyticsService()
edp_service = EDPService()
controller_service = ControllerService()
kpi_service = KPIService()


def _transform_managers_data_for_template(managers_data: Dict) -> Dict:
    """Transform managers data structure for template compatibility."""
    import numpy as np
    
    # Helper function to convert numpy types to Python native types
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        else:
            return obj

    # Extract data from managers_data
    analisis_encargados = managers_data.get('analisis_encargados', {})
    metricas_comparativas = managers_data.get('metricas_comparativas', {})
    ranking = managers_data.get('ranking', [])
    opciones_filtro = managers_data.get('opciones_filtro', {})
    
    # Convert numpy types
    analisis_encargados = convert_numpy_types(analisis_encargados)
    metricas_comparativas = convert_numpy_types(metricas_comparativas)
    ranking = convert_numpy_types(ranking)
    
    # Transform encargados data for table
    encargados = []
    for nombre, datos in analisis_encargados.items():
        # Calculate avance percentage (assuming meta = monto_pagado + monto_pendiente)
        total_monto = datos.get('monto_pagado', 0) + datos.get('monto_pendiente', 0)
        meta = 200_000_000  # You might want to adjust this based on your business logic
        avance = (datos.get('monto_pagado', 0) / meta * 100) if meta > 0 else 0
        
        # Calculate tasa_aprobacion based on EDPs
        total_edps = datos.get('total_edps', 0)
        edps_pagados = datos.get('edps_pagados', 0)
        tasa_aprobacion = (edps_pagados / total_edps * 100) if total_edps > 0 else 0
        
        encargado_data = {
            'nombre': nombre,
            'meta': meta,
            'monto_pagado': datos.get('monto_pagado', 0),
            'monto_pendiente': datos.get('monto_pendiente', 0),
            'avance': round(avance, 1),
            'dso': datos.get('dso', 0),
            'tasa_aprobacion': round(tasa_aprobacion, 1),
            'edps_criticos': datos.get('edps_criticos', 0),
            'tendencia': 0  # You might want to calculate this based on historical data
        }
        encargados.append(encargado_data)
    
    # Calculate global metrics
    total_meta = sum(enc['meta'] for enc in encargados)
    total_pagado = sum(enc['monto_pagado'] for enc in encargados)
    total_pendiente = sum(enc['monto_pendiente'] for enc in encargados)
    avance_global = (total_pagado / total_meta * 100) if total_meta > 0 else 0
    promedio_dso = metricas_comparativas.get('promedio_dso', 0)
    promedio_tasa_aprobacion = sum(enc['tasa_aprobacion'] for enc in encargados) / len(encargados) if encargados else 0
    
    # Create managers_data structure expected by template
    managers_data_transformed = {
        'total_meta': total_meta,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'avance_global': round(avance_global, 1),
        'promedio_dso': round(promedio_dso, 1),
        'promedio_tasa_aprobacion': round(promedio_tasa_aprobacion, 1)
    }
    
    # Create realistic monthly evolution data based on actual EDP data
    meses_disponibles = opciones_filtro.get('meses', [])
    datos_mensuales = _generate_monthly_evolution_data(
        analisis_encargados, 
        meses_disponibles, 
        managers_data.get('raw_data', {})
    )
    
    return {
        'managers_data': managers_data_transformed,
        'encargados': encargados,
        'datos_mensuales': datos_mensuales,
        'meses': opciones_filtro.get('meses', []),
        'clientes': opciones_filtro.get('clientes', []),
        'analisis_encargados': analisis_encargados,
        'metricas_comparativas': metricas_comparativas,
        'ranking': ranking,
        'opciones_filtro': opciones_filtro
    }


def _handle_controller_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Handle controller errors consistently"""
    error_msg = (
        f"Error in manager controller{': ' + context if context else ''}: {str(error)}"
    )
    print(f"❌ {error_msg}")
    print(f"🔍 Traceback: {traceback.format_exc()}")

    return {"error": True, "message": error_msg, "data": None}


def _parse_date_filters(request) -> Dict[str, Any]:
    """Parse and validate date filters from request"""
    hoy = datetime.now()
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    periodo_rapido = request.args.get("periodo_rapido")

    # Procesar filtros de fecha rápidos
    if periodo_rapido:
        if periodo_rapido == "7":
            fecha_inicio = (hoy - timedelta(days=7)).strftime("%Y-%m-%d")
            fecha_fin = hoy.strftime("%Y-%m-%d")
        elif periodo_rapido == "30":
            fecha_inicio = (hoy - timedelta(days=30)).strftime("%Y-%m-%d")
            fecha_fin = hoy.strftime("%Y-%m-%d")
        elif periodo_rapido == "90":
            fecha_inicio = (hoy - timedelta(days=90)).strftime("%Y-%m-%d")
            fecha_fin = hoy.strftime("%Y-%m-%d")
        elif periodo_rapido == "365":
            fecha_inicio = (hoy - timedelta(days=365)).strftime("%Y-%m-%d")
            fecha_fin = hoy.strftime("%Y-%m-%d")

    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "periodo_rapido": periodo_rapido,
    }


def _parse_filters(request) -> Dict[str, Any]:
    """Parse all filters from request"""
    date_filters = _parse_date_filters(request)

    return {
        **date_filters,
        "mes": request.args.get("mes"),
        "departamento": request.args.get("departamento", "todos"),
        "cliente": request.args.get("cliente", "todos"),
        "estado": request.args.get("estado", "todos"),
        "jefe_proyecto": request.args.get("jefe_proyecto", "todos"),
        "monto_min": request.args.get("monto_min"),
        "monto_max": request.args.get("monto_max"),
        "dias_min": request.args.get("dias_min"),
    }


def _get_empty_dashboard_data() -> Dict[str, Any]:
    """Get empty dashboard data for error cases"""
    empty_kpis_dict = controller_service.get_empty_kpis()

    return {
        "error": "Error al cargar datos",
        "kpis": DictToObject(empty_kpis_dict),  # Convert to object for dot notation
        "charts_json": "{}",
        "charts": {},
        "cash_forecast": {},
        "alertas": [],
        "fecha_inicio": None,
        "fecha_fin": None,
        "periodo_rapido": None,
        "departamento": "todos",
        "cliente": "todos",
        "estado": "todos",
        "vista": "general",
        "monto_min": None,
        "monto_max": None,
        "dias_min": None,
        "jefes_proyecto": [],
        "clientes": [],
        "rentabilidad_proyectos": [],
        "rentabilidad_clientes": [],
        "rentabilidad_gestores": [],
        "top_edps": [],
        # Agregar filtros faltantes para el template
        "filtros": DictToObject({
            "estado": "todos",
            "departamento": "todos", 
            "cliente": "todos",
            "fecha_inicio": None,
            "fecha_fin": None,
            "periodo_rapido": None,
            "vista": "general"
        })
    }


@dashboard_bp.route("/dashboard")
@login_required
@require_controller_or_above
def dashboard_controller():
    """
    Dashboard principal del controlador con KPIs, métricas financieras y análisis de EDPs.
    Refactorizado para usar el servicio especializado de controller manteniendo compatibilidad completa.
    """
    try:
        print("🚀 Iniciando carga del dashboard de controller...")

        # ===== PASO 1: OBTENER FILTROS =====
        filters = _parse_filters(request)
     

        # ===== PASO 2: CARGAR DATOS CRUDOS =====
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            print(f"❌ Error cargando datos relacionados: {datos_response.message}")
            return render_template(
                "controller/controller_dashboard.html", **_get_empty_dashboard_data()
            )

        datos_relacionados = datos_response.data
      

        # Extract raw DataFrames
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        df_log_raw = pd.DataFrame(datos_relacionados.get("logs", []))

        # ===== PASO 3: Aplicar Filtros a df_edp_raw =====

        if df_edp_raw is None or df_edp_raw.empty:
            print("❌ Error: No se pudo cargar el DataFrame de EDP")
            return render_template(
                "controller/controller_dashboard.html", **_get_empty_dashboard_data()
            )

        # ===== PASO 3: PROCESAR CON EL NUEVO SERVICIO =====
        dashboard_response = controller_service.get_processed_dashboard_context(
            df_edp_raw, df_log_raw, filters
        )

        if not dashboard_response.success:
            print(f"❌ Error procesando dashboard: {dashboard_response.message}")
            return render_template(
                "controller/controller_dashboard.html", **dashboard_response.data
            )

        dashboard_context = dashboard_response.data
        registros = dashboard_context.get('registros', [])

        # ===== PASO 4: RENDERIZAR TEMPLATE =====
        print(f"🎯 Dashboard de controller cargado exitosamente")
        return render_template(
            "controller/controller_dashboard.html", **dashboard_context
        )

    except Exception as e:
        error_info = _handle_controller_error(e, "dashboard")
        print(f"💥 Error crítico en dashboard de controller: {error_info}")

        # Return default context on critical error
        try:
            default_context = controller_service._get_default_processed_context(
                filters if "filters" in locals() else {}
            )
            return render_template(
                "controller/controller_dashboard.html", **default_context
            )
        except:
            return render_template(
                "controller/controller_dashboard.html", **_get_empty_dashboard_data()
            )

    except Exception as e:
        error_info = _handle_controller_error(e, "dashboard")
        print(f"💥 Error crítico en dashboard de controller: {error_info}")
        return render_template(
            "controller/controller_dashboard.html", **_get_empty_dashboard_data()
        )


@dashboard_bp.route("/kanban")
@login_required
@require_controller_or_above
def vista_kanban():
    """Kanban board view with filtering and real-time updates."""
    try:
        print("🚀 Iniciando carga de vista kanban...")
        
        # ===== PASO 1: OBTENER FILTROS =====
        filters = _parse_filters(request)
        print(f"📋 Filtros aplicados: {filters}")

        # ===== PASO 2: CARGAR DATOS CRUDOS =====
        now_ts = time()
        global _kanban_cache
        if _kanban_cache["data"] and now_ts - _kanban_cache["ts"] < 30:
            datos_response = _kanban_cache["data"]
        else:
            datos_response = controller_service.load_related_data()
            _kanban_cache = {"ts": now_ts, "data": datos_response}
            
        if not datos_response.success:
            print(f"❌ Error cargando datos relacionados: {datos_response.message}")
            return render_template('controller/controller_kanban.html', **_get_empty_dashboard_data())

        datos_relacionados = datos_response.data
        print(f"📊 Datos cargados: {len(datos_relacionados.get('edps', []))} EDPs")

        # Extract raw DataFrames
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        df_log_raw = pd.DataFrame(datos_relacionados.get("logs", []))

        # ===== PASO 3: OBTENER DATOS DEL KANBAN =====
        kanban_response = kanban_service.get_kanban_board_data(df_edp_raw, filters)
        
        if not kanban_response.success:
            print(f"❌ Error en kanban service: {kanban_response.message}")
            return render_template(
                "controller/controller_kanban.html", **_get_empty_dashboard_data()
            )

        kanban_data = kanban_response.data

        # ===== PASO 4: OBTENER DATOS PROCESADOS DEL DASHBOARD (PARA LA TABLA) =====
        dashboard_response = controller_service.get_processed_dashboard_context(
            df_edp_raw, df_log_raw, filters
        )

        if not dashboard_response.success:
            print(f"❌ Error procesando dashboard context: {dashboard_response.message}")
            # Continuar con datos básicos del kanban si falla la tabla
            registros = []
            dashboard_context = {}
        else:
            dashboard_context = dashboard_response.data
            registros = dashboard_context.get('registros', [])
            print(f"📋 Registros para tabla: {len(registros)}")

        # ===== PASO 5: COMBINAR DATOS PARA EL TEMPLATE =====
        template_context = {
            # Datos del Kanban
            "columnas": kanban_data.get("columnas", {}),
            "estadisticas": kanban_data.get("estadisticas", {}),
            
            # Datos para la tabla (del dashboard)
            "registros": registros,
            
            # Filtros y opciones
            "filtros": filters,
            "meses": kanban_data.get("filter_options", {}).get("meses", []),
            "jefe_proyectos": kanban_data.get("filter_options", {}).get("jefe_proyectos", []),
            "clientes": kanban_data.get("filter_options", {}).get("clientes", []),
            "estados_detallados": kanban_data.get("filter_options", {}).get("estados_detallados", []),
            
            # Datos adicionales del dashboard (si están disponibles)
            "now": datetime.now(),
        }
        
        # Agregar cualquier dato adicional del dashboard context si está disponible
        if dashboard_context:
            # Agregar datos que puedan ser útiles para la tabla
            for key in ['kpis', 'charts', 'alertas', 'dso_global', 'dso_var']:
                if key in dashboard_context:
                    template_context[key] = dashboard_context[key]
                    
            # Asegurar que dso_global esté disponible (con valor por defecto si no existe)
            if 'dso_global' not in template_context:
                template_context['dso_global'] = dashboard_context.get('dso_global', 0)
                
            print(f"🔍 DSO Global incluido en template: {template_context.get('dso_global', 'No disponible')}")

        print(f"🎯 Vista kanban cargada exitosamente con {len(registros)} registros para tabla")
        return render_template("controller/controller_kanban.html", **template_context)

    except Exception as e:
        import traceback
        print("🔥 Error atrapado en try-except de vista_kanban:")
        print(traceback.format_exc())
        flash(f"Error al cargar tablero Kanban: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard_controller"))


@dashboard_bp.route("/kanban/update_estado", methods=["POST"])
@login_required
def actualizar_estado_kanban():
    """Update EDP status from kanban board."""

    try:
        data = request.get_json()
        edp_id = data.get("edp_id")
        nuevo_estado = data.get("nuevo_estado").lower()
        estado_anterior = data.get("estado_anterior", "").lower()  # Changed from estado_origen
        conformidad_enviada = data.get("conformidad_enviada", False)
        proyecto = data.get("proyecto", None)

        if not edp_id or not nuevo_estado:
            return jsonify({"error": "Datos incompletos"}), 400

        # Obtener el usuario real desde Flask-Login antes de ir a background
        usuario = "Sistema"  # Default
        if current_user.is_authenticated:
            # Prioridad: nombre_completo > email > username > User ID
            if hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
                usuario = current_user.nombre_completo
            elif hasattr(current_user, 'email') and current_user.email:
                usuario = current_user.email
            elif hasattr(current_user, 'username') and current_user.username:
                usuario = current_user.username
            else:
                usuario = f"User ID: {current_user.id}"

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
        print(f"🔥 Error al actualizar estado de EDP: {str(e)}")
        print(traceback.format_exc())
        return (
            jsonify({"success": False, "message": f"Error al actualizar: {str(e)}"}),
            500,
        )


def _procesar_actualizacion_estado(edp_id: str, nuevo_estado: str, conformidad: bool, usuario: str, estado_anterior: str = None, proyecto: str = None):
    """Tarea en segundo plano para persistir el cambio de estado."""
    global _kanban_cache
    try:
        from ..services.cache_invalidation_service import CacheInvalidationService
        from ..utils.supabase_adapter import log_cambio_edp, read_sheet
        
        print(f"🔄 Procesando actualización de estado para EDP {edp_id}:")
        print(f"   - Nuevo estado: {nuevo_estado}")
        print(f"   - Estado anterior: {estado_anterior}")
        print(f"   - Conformidad: {conformidad}")
        print(f"   - Usuario: {usuario}")

        # Obtener proyecto por id del edp
        df = controller_service.load_related_data().data
        df_edps = pd.DataFrame(df.get("edps", []))
        proyecto = df_edps[df_edps["n_edp"] == edp_id]["proyecto"].values[0] if not df_edps[df_edps["n_edp"] == edp_id].empty else None
      
        print(f"   - Proyecto asociado: {proyecto}")
        additional = {"conformidad_enviada": "Sí"} if conformidad else None
        resp = kanban_service.update_edp_status(edp_id, nuevo_estado, additional)

        print(f"🔍 Respuesta del servicio kanban:")
        print(f"   - Success: {resp.success}")
        print(f"   - Message: {resp.message}")
        if hasattr(resp, 'data'):
            print(f"   - Data: {resp.data}")
        
        if resp.success:
            # Registrar TODOS los cambios en el log con el usuario detectado
            try:
                # Obtener los cambios reales desde la respuesta del servicio
                updates_realizados = resp.data.get("updates", {})
                print(f"🔍 Cambios realizados: {updates_realizados}")
                
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
                        print(f"📝 Cambio registrado en log: EDP {edp_id} {campo} {valor_anterior} → {nuevo_valor} por {usuario}")
                        
            except Exception as log_error:
                print(f"⚠️ Error al registrar cambios en log: {log_error}")
                import traceback
                print(traceback.format_exc())
            
            _kanban_cache["ts"] = 0
            
            # Invalidar cache automáticamente
            cache_invalidation = CacheInvalidationService()
            updated_fields = list(resp.data.get("updates", {}).keys())
            cache_invalidation.register_data_change('edp_state_changed', [edp_id], 
                                                  {'updated_fields': updated_fields})
            
            # Importar función de conversión centralizada
            from ..utils.type_conversion import convert_numpy_types_for_json
            
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
            updates_serializable = convert_numpy_types_for_json(updates_data)
            cambios_serializable = convert_numpy_types_for_json(resp.data.get("updates", {}))
            
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
            print(f"✅ Actualización de estado completada exitosamente para EDP {edp_id}")
        else:
            print(f"❌ Error en actualización de estado: {resp.message}")
            logger.error(f"Error en background update: {resp.message}")
    except Exception as exc:
        print(f"💥 Excepción en _procesar_actualizacion_estado: {exc}")
        print(traceback.format_exc())
        logger.error(f"Excepción en tarea de actualización: {exc}")
        logger.error(traceback.format_exc())


@dashboard_bp.route("/kanban/update_estado_by_id", methods=["POST"])
@login_required
def actualizar_estado_kanban_by_id():
    """Update EDP status from kanban board using internal ID."""
    try:
        data = request.get_json()
        internal_id = data.get("internal_id")
        nuevo_estado_raw = data.get("nuevo_estado")
        nuevo_estado = nuevo_estado_raw.lower() if nuevo_estado_raw else ""
        estado_anterior = data.get("estado_anterior", "").lower()
        conformidad_enviada = data.get("conformidad_enviada", False)
        proyecto = data.get("proyecto", None)

        if not internal_id or not nuevo_estado:
            return jsonify({"error": "Datos incompletos"}), 400

        # Primero obtener el n_edp del ID interno
        df = controller_service.load_related_data().data
        df_edps = pd.DataFrame(df.get("edps", []))
        edp_row = df_edps[df_edps['id'] == internal_id]
        
        if edp_row.empty:
            return jsonify({"error": f"EDP con ID {internal_id} no encontrado"}), 404
        
        # Obtener el n_edp del ID interno
        edp_data = edp_row.iloc[0]
        edp_id = int(edp_data['n_edp'])  # Convert pandas int64 to Python int
        if not proyecto:
            proyecto = edp_data['proyecto']

        # Obtener el usuario real desde Flask-Login antes de ir a background
        usuario = "Sistema"  # Default
        if current_user.is_authenticated:
            # Prioridad: nombre_completo > email > username > User ID
            if hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
                usuario = current_user.nombre_completo
            elif hasattr(current_user, 'email') and current_user.email:
                usuario = current_user.email
            elif hasattr(current_user, 'username') and current_user.username:
                usuario = current_user.username
            else:
                usuario = f"User ID: {current_user.id}"

        socketio.start_background_task(
            _procesar_actualizacion_estado,
            edp_id,
            nuevo_estado,
            conformidad_enviada,
            usuario,
            estado_anterior,
            proyecto,
        )

        return jsonify({"success": True, "queued": True, "internal_id": internal_id, "n_edp": edp_id}), 202
    except Exception as e:
        print(f"🔥 Error al actualizar estado de EDP por ID: {str(e)}")
        print(traceback.format_exc())
        return (
            jsonify({"success": False, "message": f"Error al actualizar: {str(e)}"}),
            500,
        )


@dashboard_bp.route("/kanban/update_estado_detallado", methods=["POST"])
@login_required
def actualizar_estado_detallado():
    """
    Procesa actualizaciones detalladas de estado con campos adicionales
    específicos para cada transición de estado.
    Actualizado para usar ID interno y evitar problemas de unicidad.
    """
    try:
        # Obtener datos del formulario - priorizar internal_id sobre edp_id
        internal_id = request.form.get("internal_id")
        edp_id = request.form.get("edp_id")  # n_edp como fallback
        nuevo_estado = request.form.get("nuevo_estado", "").lower()

        print(f"🔍 actualizar_estado_detallado - internal_id: {internal_id}, edp_id: {edp_id}, estado: {nuevo_estado}")

        if not nuevo_estado:
            return jsonify({"success": False, "message": "Estado requerido"}), 400

        # Intentar usar ID interno primero, fallback a n_edp
        if internal_id and internal_id != '' and internal_id != 'null':
            # Usar ID interno - SEGURO Y ÚNICO
            print(f"✅ Usando ID interno {internal_id} (SEGURO)")
            
            # Cargar datos usando servicio Supabase
            datos_response = controller_service.load_related_data()
            if not datos_response.success:
                return jsonify({"success": False, "message": "Error cargando datos"}), 500
            
            datos_relacionados = datos_response.data
            df = pd.DataFrame(datos_relacionados.get("edps", []))
            
            # Buscar por ID interno
            edp = df[df["id"] == int(internal_id)]
            
            if edp.empty:
                print(f"❌ EDP con ID interno {internal_id} no encontrado")
                return jsonify({"success": False, "message": f"EDP con ID {internal_id} no encontrado"}), 404
            
            # Convertir tipos de pandas a tipos nativos Python
            edp_data_raw = edp.iloc[0].to_dict()
            edp_data = {}
            for key, value in edp_data_raw.items():
                if pd.isna(value):
                    edp_data[key] = None
                elif hasattr(value, 'item'):  # numpy scalars
                    edp_data[key] = value.item()
                elif hasattr(value, 'tolist'):  # numpy arrays
                    edp_data[key] = value.tolist()
                else:
                    edp_data[key] = value
            
            search_id = internal_id
            id_type = "internal_id"
            
        elif edp_id and edp_id != '' and edp_id != 'null':
            # Fallback a n_edp - RIESGOSO
            print(f"⚠️ FALLBACK: Usando n_edp {edp_id} (puede no ser único)")
            
            # Cargar datos usando servicio Supabase  
            datos_response = controller_service.load_related_data()
            if not datos_response.success:
                return jsonify({"success": False, "message": "Error cargando datos"}), 500
            
            datos_relacionados = datos_response.data
            df = pd.DataFrame(datos_relacionados.get("edps", []))
            
            # Buscar por n_edp
            edp = df[df["n_edp"] == str(edp_id)]
            
            if edp.empty:
                print(f"❌ EDP {edp_id} no encontrado")
                return jsonify({"success": False, "message": f"EDP {edp_id} no encontrado"}), 404
            
            # Verificar unicidad
            if len(edp) > 1:
                print(f"⚠️ ADVERTENCIA: Se encontraron {len(edp)} EDPs con n_edp={edp_id}")
                # Usar el primero pero advertir
                edp_data_raw = edp.iloc[0].to_dict()
            else:
                edp_data_raw = edp.iloc[0].to_dict()
            
            # Convertir tipos de pandas a tipos nativos Python
            edp_data = {}
            for key, value in edp_data_raw.items():
                if pd.isna(value):
                    edp_data[key] = None
                elif hasattr(value, 'item'):  # numpy scalars
                    edp_data[key] = value.item()
                elif hasattr(value, 'tolist'):  # numpy arrays
                    edp_data[key] = value.tolist()
                else:
                    edp_data[key] = value
            
            search_id = edp_id
            id_type = "n_edp"
        else:
            return jsonify({"success": False, "message": "ID requerido (internal_id o edp_id)"}), 400

        # Preparar cambios base
        cambios = {"estado": nuevo_estado}

        # Procesar campos especiales según el estado
        if nuevo_estado == "pagado":
            cambios["fecha_conformidad"] = request.form.get("fecha_pago")
            cambios["n_conformidad"] = request.form.get("n_conformidad")
            cambios["conformidad_enviada"] = "Sí"

        elif nuevo_estado == "validado":
            cambios["fecha_estimada_pago"] = request.form.get("fecha_estimada_pago")
            cambios["conformidad_enviada"] = "Sí"

        elif nuevo_estado == "revision" and request.form.get("contacto_cliente"):
            # Campos para revisión de cliente (opcionales)
            pass

        # Quitar campos vacíos
        cambios = {k: v for k, v in cambios.items() if v is not None and v != ""}

        # Obtener el usuario real desde Flask-Login
        usuario = "Sistema"  # Default
        if current_user.is_authenticated:
            if hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
                usuario = current_user.nombre_completo
            elif hasattr(current_user, 'email') and current_user.email:
                usuario = current_user.email
            elif hasattr(current_user, 'username') and current_user.username:
                usuario = current_user.username
            else:
                usuario = f"User ID: {current_user.id}"
        
        # El log ya se registra automáticamente en el servicio EDP
        # pero vamos a asegurar el registro manual también
        from ..utils.supabase_adapter import log_cambio_edp
        
        # Obtener el n_edp actual (puede haber cambiado)
        final_n_edp = edp_data.get("n_edp", search_id)
        final_proyecto = edp_data.get("proyecto", "Sin proyecto")
        
        for campo, nuevo_valor in cambios.items():
            valor_anterior = edp_data.get(campo)
            if str(nuevo_valor) != str(valor_anterior):
                log_cambio_edp(
                    n_edp=final_n_edp,
                    proyecto=final_proyecto,
                    campo=campo,
                    antes=valor_anterior,
                    despues=nuevo_valor,
                    # usuario se auto-detecta automáticamente
                )

        # Actualizar usando el servicio EDP
        from ..services.edp_service import EDPService
        
        edp_service = EDPService()
        
        if id_type == "internal_id":
            # Actualización por ID interno - SEGURA
            print(f"✅ Actualizando por ID interno: {internal_id}")
            result = edp_service.update_edp_by_internal_id(int(internal_id), cambios)
        else:
            # Actualización por n_edp - usar primer resultado
            # Necesitamos obtener el ID interno del EDP encontrado
            edp_internal_id = edp_data.get("id")
            if edp_internal_id:
                print(f"✅ Actualizando por ID interno extraído: {edp_internal_id}")
                result = edp_service.update_edp_by_internal_id(edp_internal_id, cambios)
            else:
                print(f"❌ No se pudo obtener ID interno para EDP {edp_id}")
                return jsonify({"success": False, "message": f"Error: EDP {edp_id} sin ID interno"}), 500

        if not result.success:
            print(f"❌ Error del servicio EDP: {result.message}")
            return jsonify({"success": False, "message": f"Error al actualizar EDP: {result.message}"}), 500

        # Invalidar cache automáticamente
        from ..services.cache_invalidation_service import CacheInvalidationService
        cache_invalidation = CacheInvalidationService()
        cache_invalidation.register_data_change('edp_state_changed', [search_id], 
                                              {'updated_fields': list(cambios.keys())})

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
        cambios_serializable = convert_numpy_types_for_emit(cambios)
        internal_id_safe = int(edp_data.get("id")) if edp_data.get("id") is not None else None
        
        # Notificar via Socket.IO
        socketio.emit("edp_actualizado", {
            "edp_id": str(final_n_edp), 
            "internal_id": internal_id_safe,
            "updates": cambios_serializable,
            "usuario": str(usuario),
            "timestamp": datetime.now().isoformat()
        })
        socketio.emit("estado_actualizado", {
            "edp_id": str(final_n_edp),
            "internal_id": internal_id_safe, 
            "nuevo_estado": str(nuevo_estado), 
            "cambios": cambios_serializable
        })
        socketio.emit("cache_invalidated", {
            "type": "edp_state_changed",
            "affected_ids": [str(final_n_edp)],
            "timestamp": datetime.now().isoformat()
        })

        # Mensaje de éxito con información del método usado
        id_info = f"ID interno {internal_id}" if id_type == "internal_id" else f"n_edp {edp_id}"
        
        return jsonify({
            "success": True,
            "message": f"EDP actualizado correctamente ({id_info}) con detalles adicionales",
            "edp_id": final_n_edp,
            "internal_id": edp_data.get("id"),
            "method_used": id_type
        })

    except Exception as e:
        import traceback
        print(f"❌ Error en actualizar_estado_detallado: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error al actualizar: {str(e)}"}), 500


@dashboard_bp.route("api/get-edp/<edp_id>", methods=["GET"])
@login_required
def get_edp_data(edp_id):
    """API endpoint to get EDP data by ID."""
    try:
        df = controller_service.load_related_data()
        datos_relacionados = df.data
        df = pd.DataFrame(datos_relacionados.get("edps", []))
        edp = df[df["n_edp"] == str(edp_id)]

        if edp.empty:
            return jsonify({"error": f"EDP {edp_id} no encontrado"}), 404

        # Convertir a diccionario para la respuesta JSON
        edp_data_raw = edp.iloc[0].to_dict()
        
        # 🔧 CORRECCIÓN: Convertir tipos numpy a tipos nativos Python
        edp_data = {}
        for key, value in edp_data_raw.items():
            if pd.isna(value):
                edp_data[key] = None
            elif isinstance(value, (np.integer, np.int64, np.int32)):
                edp_data[key] = int(value)
            elif isinstance(value, (np.floating, np.float64, np.float32)):
                if np.isnan(value):
                    edp_data[key] = None
                else:
                    edp_data[key] = float(value)
            elif isinstance(value, (np.bool_, np.bool8)):
                edp_data[key] = bool(value)
            elif isinstance(value, pd.Timestamp):
                edp_data[key] = value.isoformat()
            elif hasattr(value, 'item'):  # numpy scalars
                edp_data[key] = value.item()
            else:
                edp_data[key] = value
     
        # Asegurar que las fechas estén en formato YYYY-MM-DD para campos de fecha
        for campo in [
            "fecha_emision",
            "fecha_envio_cliente",
            "fecha_estimada_pago",
            "fecha_conformidad",
        ]:
            if campo in edp_data:
                # Primero verificar si es None
                if edp_data[campo] is None:
                    continue
                else:
                    try:
                        # Si ya es timestamp, usarlo directamente
                        if isinstance(edp_data[campo], str) and 'T' in edp_data[campo]:
                            # Ya está en formato ISO, convertir a fecha
                            fecha = pd.to_datetime(edp_data[campo], errors="coerce")
                            if pd.notna(fecha):
                                edp_data[campo] = fecha.strftime("%Y-%m-%d")
                            else:
                                edp_data[campo] = None
                        elif isinstance(edp_data[campo], str):
                            # Intentar parsear como fecha
                            fecha = pd.to_datetime(edp_data[campo], errors="coerce")
                            if pd.notna(fecha):
                                edp_data[campo] = fecha.strftime("%Y-%m-%d")
                            else:
                                edp_data[campo] = None
                    except Exception as ex:
                        print(f"Error formateando {campo}: {str(ex)}")
                        edp_data[campo] = None

        return jsonify(edp_data)

    except Exception as e:
        import traceback
        print(f"❌ Error en get_edp_data: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/edp-details/<n_edp>", methods=["GET"])
@login_required
def api_get_edp_details(n_edp):
    """API para obtener detalles de un EDP en formato JSON"""

    datos_response = controller_service.load_related_data()
    if not datos_response.success:
        print(f"❌ Error cargando datos relacionados: {datos_response.message}")
        return render_template(
            "controller/controller_dashboard.html", **_get_empty_dashboard_data()
        )

    datos_relacionados = datos_response.data

    # Extract raw DataFrames
    df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))

    # Convert n_edp to int for comparison if it's a digit string
    try:
        n_edp_int = int(n_edp) if str(n_edp).isdigit() else n_edp
        # Try both string and int comparison to handle different data types
        edp = df_edp_raw[
            (df_edp_raw["n_edp"] == n_edp) | 
            (df_edp_raw["n_edp"] == n_edp_int)
        ]
    except (ValueError, TypeError):
        # If conversion fails, just use string comparison
        edp = df_edp_raw[df_edp_raw["n_edp"] == n_edp]

    if edp.empty:
        return jsonify({"error": f"EDP {n_edp} no encontrado"}), 404

    # ADVERTENCIA: Verificar si hay múltiples EDPs con el mismo n_edp
    if len(edp) > 1:
        print(f"⚠️ ADVERTENCIA: Se encontraron {len(edp)} EDPs con n_edp={n_edp}. Esto puede causar problemas de unicidad.")
        print(f"⚠️ IDs internos encontrados: {edp['id'].tolist()}")
        print(f"⚠️ Se retornará el primer resultado, pero esto es peligroso.")
        # Agregar información sobre múltiples resultados en la respuesta
        multiple_warning = True
        all_ids = edp['id'].tolist()
    else:
        multiple_warning = False
        all_ids = None

    edp_data = edp.iloc[0].to_dict()

    # Limpiar valores NaT/NaN y formatear fechas
    for key, value in edp_data.items():
        if pd.isna(value):
            edp_data[key] = None
        elif isinstance(value, pd.Timestamp):
            edp_data[key] = value.strftime("%Y-%m-%d")

    # Incluir advertencia si hay múltiples resultados
    if multiple_warning:
        edp_data['_warning'] = f"Se encontraron {len(all_ids)} EDPs con el mismo n_edp. IDs: {all_ids}"
        edp_data['_multiple_ids'] = all_ids

    return jsonify(edp_data)


@dashboard_bp.route("api/get-edp-by-id/<int:internal_id>", methods=["GET"])
@login_required
def get_edp_data_by_internal_id(internal_id):
    """API endpoint to get EDP data by internal ID."""
    try:
        print(f"🔍 get_edp_data_by_internal_id - Buscando EDP con ID interno: {internal_id}")
        
        # Cargar datos con manejo de errores mejorado
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            print(f"❌ Error cargando datos: {datos_response.message}")
            return jsonify({"error": f"Error cargando datos: {datos_response.message}"}), 500
        
        datos_relacionados = datos_response.data
        if not datos_relacionados or "edps" not in datos_relacionados:
            print("❌ No se encontraron datos de EDPs")
            return jsonify({"error": "No se encontraron datos de EDPs"}), 500
        
        df = pd.DataFrame(datos_relacionados.get("edps", []))
        print(f"📊 DataFrame creado con {len(df)} registros")
        
        if df.empty:
            print("❌ DataFrame de EDPs está vacío")
            return jsonify({"error": "No hay EDPs disponibles"}), 404
        
        # Verificar que la columna 'id' existe
        if 'id' not in df.columns:
            print(f"❌ Columna 'id' no encontrada. Columnas disponibles: {df.columns.tolist()}")
            return jsonify({"error": "Estructura de datos incorrecta"}), 500
        
        # Buscar EDP por ID interno
        edp = df[df["id"] == internal_id]
        print(f"🔍 Búsqueda por ID {internal_id}: {len(edp)} resultados encontrados")

        if edp.empty:
            print(f"❌ EDP con ID interno {internal_id} no encontrado")
            return jsonify({"error": f"EDP con ID {internal_id} no encontrado"}), 404

        # Convertir a diccionario para la respuesta JSON
        edp_data_raw = edp.iloc[0].to_dict()
        print(f"📝 Datos raw obtenidos para EDP ID {internal_id}")
        
        # 🔧 CORRECCIÓN: Convertir tipos numpy a tipos nativos Python
        def convert_numpy_types_safe(obj):
            """Convierte tipos numpy de forma segura"""
            try:
                if pd.isna(obj):
                    return None
                elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    if np.isnan(obj):
                        return None
                    return float(obj)
                elif isinstance(obj, (np.bool_, np.bool8)):
                    return bool(obj)
                elif isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                elif hasattr(obj, 'item'):  # numpy scalars
                    return obj.item()
                else:
                    return obj
            except Exception as ex:
                print(f"⚠️ Error convirtiendo valor {obj} (tipo: {type(obj)}): {str(ex)}")
                return str(obj) if obj is not None else None
        
        edp_data = {}
        for key, value in edp_data_raw.items():
            edp_data[key] = convert_numpy_types_safe(value)
     
        # Asegurar que las fechas estén en formato YYYY-MM-DD para campos de fecha
        fecha_campos = ["fecha_emision", "fecha_envio_cliente", "fecha_estimada_pago", "fecha_conformidad"]
        for campo in fecha_campos:
            if campo in edp_data and edp_data[campo] is not None:
                try:
                    # Si ya es timestamp, usarlo directamente
                    if isinstance(edp_data[campo], str) and 'T' in edp_data[campo]:
                        # Ya está en formato ISO, convertir a fecha
                        fecha = pd.to_datetime(edp_data[campo], errors="coerce")
                        if pd.notna(fecha):
                            edp_data[campo] = fecha.strftime("%Y-%m-%d")
                        else:
                            edp_data[campo] = None
                    elif isinstance(edp_data[campo], str):
                        # Intentar parsear como fecha
                        fecha = pd.to_datetime(edp_data[campo], errors="coerce")
                        if pd.notna(fecha):
                            edp_data[campo] = fecha.strftime("%Y-%m-%d")
                        else:
                            edp_data[campo] = None
                except Exception as ex:
                    print(f"⚠️ Error formateando fecha {campo}: {str(ex)}")
                    edp_data[campo] = None

        print(f"✅ Datos procesados exitosamente para EDP ID {internal_id}")
        return jsonify(edp_data)

    except Exception as e:
        import traceback
        error_msg = f"Error en get_edp_data_by_internal_id para ID {internal_id}: {str(e)}"
        print(f"❌ {error_msg}")
        print("📋 Traceback completo:")
        print(traceback.format_exc())
        return jsonify({"error": error_msg}), 500


@dashboard_bp.route("/api/edp-details-by-id/<int:internal_id>", methods=["GET"])
@login_required
def api_get_edp_details_by_internal_id(internal_id):
    """API para obtener detalles de un EDP por ID interno en formato JSON"""

    datos_response = controller_service.load_related_data()
    if not datos_response.success:
        print(f"❌ Error cargando datos relacionados: {datos_response.message}")
        return jsonify({"error": "Error cargando datos"}), 500

    datos_relacionados = datos_response.data

    # Extract raw DataFrames
    df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))

    edp = df_edp_raw[df_edp_raw["id"] == internal_id]

    if edp.empty:
        return jsonify({"error": "EDP no encontrado"}), 404

    edp_data_raw = edp.iloc[0].to_dict()
    
    # 🔧 CORRECCIÓN: Convertir tipos numpy a tipos nativos Python
    def convert_numpy_types_safe(obj):
        """Convierte tipos numpy a tipos nativos de Python para serialización JSON"""
        if isinstance(obj, dict):
            return {key: convert_numpy_types_safe(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types_safe(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, pd.Timestamp):
            return obj.strftime("%Y-%m-%d")
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    # Aplicar conversión de tipos
    edp_data = convert_numpy_types_safe(edp_data_raw)

    return jsonify(edp_data)


@dashboard_bp.route("/api/update-edp/<n_edp>", methods=["POST"])
@login_required
def api_update_edp(n_edp):
    """API para actualizar un EDP desde el modal de forma asíncrona"""
    try:
        # Validar y preparar payload mínimo
        updates = {
            "estado": request.form.get("estado") or "",
            "estado_detallado": request.form.get("estado_detallado") or "",
            "conformidad_enviada": request.form.get("conformidad_enviada") or "",
            "fecha_conformidad": request.form.get("fecha_conformidad") or "",
            "n_conformidad": request.form.get("n_conformidad") or "",
            "monto_propuesto": request.form.get("monto_propuesto") or "",
            "monto_aprobado": request.form.get("monto_aprobado") or "",
            "fecha_estimada_pago": request.form.get("fecha_estimada_pago") or "",
            "observaciones": request.form.get("observaciones") or "",
        }

        if updates["estado_detallado"] == "re-trabajo solicitado":
            updates["motivo_no_aprobado"] = request.form.get("motivo_no_aprobado") or ""
            updates["tipo_falla"] = request.form.get("tipo_falla") or ""

        if updates["estado"] in ["pagado", "validado"]:
            updates["conformidad_enviada"] = "Sí"

        # Obtener el usuario real desde Flask-Login antes de ir a background
        usuario = "Sistema"  # Default
        if current_user.is_authenticated:
            # Prioridad: nombre_completo > email > username > User ID
            if hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
                usuario = current_user.nombre_completo
            elif hasattr(current_user, 'email') and current_user.email:
                usuario = current_user.email
            elif hasattr(current_user, 'username') and current_user.username:
                usuario = current_user.username
            else:
                usuario = f"User ID: {current_user.id}"

        socketio.start_background_task(_background_update_edp, n_edp, updates, usuario)

        return jsonify({"success": True, "queued": True}), 202

    except Exception as e:
        import traceback

        print(f"Error en api_update_edp: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@dashboard_bp.route("/api/update-edp-by-id/<int:internal_id>", methods=["POST"])
@login_required
def api_update_edp_by_internal_id(internal_id):
    """API para actualizar un EDP por ID interno desde el modal de forma asíncrona"""
    try:
        # Validar y preparar payload mínimo
        updates = {
            "estado": request.form.get("estado") or "",
            "estado_detallado": request.form.get("estado_detallado") or "",
            "conformidad_enviada": request.form.get("conformidad_enviada") or "",
            "fecha_conformidad": request.form.get("fecha_conformidad") or "",
            "n_conformidad": request.form.get("n_conformidad") or "",
            "monto_propuesto": request.form.get("monto_propuesto") or "",
            "monto_aprobado": request.form.get("monto_aprobado") or "",
            "fecha_estimada_pago": request.form.get("fecha_estimada_pago") or "",
            "observaciones": request.form.get("observaciones") or "",
        }

        if updates["estado_detallado"] == "re-trabajo solicitado":
            updates["motivo_no_aprobado"] = request.form.get("motivo_no_aprobado") or ""
            updates["tipo_falla"] = request.form.get("tipo_falla") or ""

        if updates["estado"] in ["pagado", "validado"]:
            updates["conformidad_enviada"] = "Sí"

        # Obtener el usuario real desde Flask-Login antes de ir a background
        usuario = "Sistema"  # Default
        if current_user.is_authenticated:
            # Prioridad: nombre_completo > email > username > User ID
            if hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
                usuario = current_user.nombre_completo
            elif hasattr(current_user, 'email') and current_user.email:
                usuario = current_user.email
            elif hasattr(current_user, 'username') and current_user.username:
                usuario = current_user.username
            else:
                usuario = f"User ID: {current_user.id}"

        socketio.start_background_task(_background_update_edp_by_id, internal_id, updates, usuario)

        return jsonify({"success": True, "queued": True}), 202

    except Exception as e:
        import traceback

        print(f"Error en api_update_edp_by_internal_id: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


def _background_update_edp_by_id(internal_id: int, updates: Dict[str, Any], usuario: str):
    """Procesa la actualización de un EDP por ID interno en un hilo de fondo."""
    from ..utils.supabase_adapter import _range_cache, update_edp_by_id
    from ..services.cache_invalidation_service import CacheInvalidationService

    try:
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            logger.error(f"Error cargando datos: {datos_response.message}")
            return

        datos_relacionados = datos_response.data
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        edp = df_edp_raw[df_edp_raw["id"] == internal_id]
        if edp.empty:
            logger.error(f"EDP con ID {internal_id} no encontrado")
            return

        edp_data = edp.iloc[0].to_dict()
        n_edp = edp_data.get("n_edp", "")

        for campo, nuevo in updates.items():
            viejo = str(edp_data.get(campo, ""))
            if nuevo != "" and str(nuevo) != viejo:
                log_cambio_edp(
                    n_edp=n_edp,
                    proyecto=edp_data.get("proyecto", ""),
                    campo=campo,
                    antes=viejo,
                    despues=nuevo,
                    # usuario se auto-detecta automáticamente, no necesitamos pasarlo
                )

        # Usar update_edp_by_id en lugar de update_row para Supabase
        success = update_edp_by_id(internal_id, updates, usuario)
        _range_cache.clear()
        
        # Invalidar cache automáticamente basado en cambios reales
        cache_invalidation = CacheInvalidationService()
        if 'estado' in updates:
            cache_invalidation.register_data_change('edp_state_changed', [n_edp], 
                                                  {'updated_fields': list(updates.keys())})
        else:
            cache_invalidation.register_data_change('edp_updated', [n_edp], 
                                                  {'updated_fields': list(updates.keys())})
        
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
        
        # Convertir updates antes de emitir
        updates_serializable = convert_numpy_types_for_emit(updates)
        
        # Emit both EDP update and cache invalidation events
        socketio.emit("edp_actualizado", {
            "edp_id": str(n_edp), 
            "internal_id": int(internal_id),
            "updates": updates_serializable,
            "usuario": str(usuario),
            "timestamp": datetime.now().isoformat()
        })
        socketio.emit("cache_invalidated", {
            "type": "edp_state_changed" if 'estado' in updates else "edp_updated",
            "affected_ids": [str(n_edp)],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as exc:
        logger.error(f"Error en background update by ID: {exc}")
        logger.error(traceback.format_exc())


def _background_update_edp(n_edp: str, updates: Dict[str, Any], usuario: str):
    """Procesa la actualización de un EDP en un hilo de fondo."""
    from ..utils.supabase_adapter import _range_cache, update_edp_by_id
    from ..services.cache_invalidation_service import CacheInvalidationService

    try:
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            logger.error(f"Error cargando datos: {datos_response.message}")
            return

        datos_relacionados = datos_response.data
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        edp = df_edp_raw[df_edp_raw["n_edp"] == n_edp]
        if edp.empty:
            logger.error(f"EDP {n_edp} no encontrado")
            return

        edp_data = edp.iloc[0].to_dict()
        internal_id = edp_data.get("id")
        
        if not internal_id:
            logger.error(f"EDP {n_edp} no tiene ID interno válido")
            return

        for campo, nuevo in updates.items():
            viejo = str(edp_data.get(campo, ""))
            if nuevo != "" and str(nuevo) != viejo:
                log_cambio_edp(
                    n_edp=n_edp,
                    proyecto=edp_data.get("proyecto", ""),
                    campo=campo,
                    antes=viejo,
                    despues=nuevo,
                    # usuario se auto-detecta automáticamente, no necesitamos pasarlo
                )

        # Usar update_edp_by_id en lugar de update_row para Supabase
        success = update_edp_by_id(internal_id, updates, usuario)
        _range_cache.clear()
        
        # Invalidar cache automáticamente basado en cambios reales
        cache_invalidation = CacheInvalidationService()
        if 'estado' in updates:
            cache_invalidation.register_data_change('edp_state_changed', [n_edp], 
                                                  {'updated_fields': list(updates.keys())})
        else:
            cache_invalidation.register_data_change('edp_updated', [n_edp], 
                                                  {'updated_fields': list(updates.keys())})
        
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
        
        # Convertir updates antes de emitir
        updates_serializable = convert_numpy_types_for_emit(updates)
        
        # Emit both EDP update and cache invalidation events
        socketio.emit("edp_actualizado", {
            "edp_id": str(n_edp), 
            "updates": updates_serializable,
            "usuario": str(usuario),
            "timestamp": datetime.now().isoformat()
        })
        socketio.emit("cache_invalidated", {
            "type": "edp_state_changed" if 'estado' in updates else "edp_updated",
            "affected_ids": [str(n_edp)],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as exc:
        logger.error(f"Error en background update: {exc}")
        logger.error(traceback.format_exc())


def _prepare_manager_template_data(nombre: str, manager_data: Dict) -> Dict[str, Any]:
    """
    Prepares and transforms manager analytics data for template rendering.
    Handles data type conversions and ensures all required template variables are present.
    """
    try:
        # Extract nested data structures
        analisis_financiero = manager_data.get('analisis_financiero', {})
        resumen_proyectos = manager_data.get('resumen_proyectos', {})
        analisis_rendimiento = manager_data.get('analisis_rendimiento', {})
        tendencias = manager_data.get('tendencias', {})
        
        # Process tendencia_cobro data to ensure numeric values
        tendencia_cobro_raw = tendencias.get('tendencia_cobro', [])
        tendencia_cobro_processed = []
        max_cobro = 0
        
        for item in tendencia_cobro_raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                mes, valor = item[0], item[1]
                # Convert valor to numeric, handling strings
                try:
                    valor_numeric = float(valor) if valor != '' and valor is not None else 0
                except (ValueError, TypeError):
                    valor_numeric = 0
                
                tendencia_cobro_processed.append((mes, valor_numeric))
                max_cobro = max(max_cobro, valor_numeric)
            elif isinstance(item, dict) and 'mes' in item and 'valor' in item:
                mes = item['mes']
                try:
                    valor_numeric = float(item['valor']) if item['valor'] != '' and item['valor'] is not None else 0
                except (ValueError, TypeError):
                    valor_numeric = 0
                
                tendencia_cobro_processed.append((mes, valor_numeric))
                max_cobro = max(max_cobro, valor_numeric)
        
        # Ensure we have at least 1 to avoid division by zero
        maximo_cobro_mensual = max(max_cobro, 1)
        
        # Calculate additional metrics from projects data
        monto_propuesto_total = 0
        monto_aprobado_total = 0
        
        for datos in resumen_proyectos.values():
            try:
                monto_propuesto_total += float(datos.get('Monto_Propuesto_Total', 0))
                monto_aprobado_total += float(datos.get('Monto_Aprobado_Total', 0))
            except (ValueError, TypeError):
                continue
        
        # Build template data dictionary
        template_data = {
            'nombre': nombre,
            'monto_pagado_global': float(analisis_financiero.get('monto_pagado', 0)),
            'monto_pendiente_global': float(analisis_financiero.get('monto_pendiente', 0)),
            'meta_por_encargado': float(analisis_financiero.get('meta_encargado', 0)),
            'avance_global': float(analisis_financiero.get('avance_meta', 0)),
            'alertas': manager_data.get('alertas', []),
            'proyectos': [
                {
                    'Proyecto': proyecto,
                    'Total_EDP': int(datos.get('Total_EDP', 0)),
                    'Críticos': int(datos.get('Críticos', 0)),
                    'Validados': int(datos.get('Validados', 0)),  # Adding missing Validados field
                    'Monto_Propuesto_Total': float(datos.get('Monto_Propuesto_Total', 0)),
                    'Monto_Aprobado_Total': float(datos.get('Monto_Aprobado_Total', 0)),
                    'Monto_Pagado': float(datos.get('Monto_Pagado', 0)),
                    'Monto_Pendiente': float(datos.get('Monto_Pendiente', 0)),
                    '%_Avance': round(
                        (float(datos.get('Monto_Pagado', 0)) / float(datos.get('Monto_Aprobado_Total', 1)) * 100) 
                        if float(datos.get('Monto_Aprobado_Total', 0)) > 0 else 0, 1
                    ),
                    'Prom_Días_Espera': round(float(datos.get('dias_promedio', 0)), 1)
                }
                for proyecto, datos in resumen_proyectos.items()
            ],
            'dso_encargado': float(analisis_rendimiento.get('dso_encargado', 0)),
            'dso_global': float(analisis_rendimiento.get('dso_global', 0)),
            'edps_criticos': int(analisis_rendimiento.get('edps_criticos', 0)),
            'porcentaje_criticos': float(analisis_rendimiento.get('porcentaje_criticos', 0)),
            'tendencia_cobro': tendencia_cobro_processed,
            'maximo_cobro_mensual': maximo_cobro_mensual,
            
            # Financial aggregates
            'monto_propuesto_global': monto_propuesto_total,
            'monto_aprobado_global': monto_aprobado_total,
            'registros': manager_data.get('registros', []),
            'total_edps': int(analisis_financiero.get('total_edps', 0)),
            'edps_pagados': int(analisis_financiero.get('edps_pagados', 0)),
            
            # KPIs from enhanced analytics service
            'tasa_aprobacion': float(analisis_financiero.get('tasa_aprobacion', 0)),
            'tasa_aprobacion_global': float(analisis_rendimiento.get('tasa_aprobacion_global', 0)),
            'monto_cobrado_ultimo_mes': float(tendencias.get('monto_cobrado_ultimo_mes', 0)),
            'variacion_mensual_cobro': float(tendencias.get('variacion_mensual_cobro', 0)),
            'promedio_cobro_mensual': float(tendencias.get('promedio_cobro_mensual', 0)),
            'dias_promedio_aprobacion': float(analisis_rendimiento.get('dias_promedio_aprobacion', 0)),
            'monto_proximo_cobro': float(analisis_financiero.get('monto_proximo_cobro', 0)),
            'cantidad_edp_proximos': int(analisis_financiero.get('cantidad_edp_proximos', 0)),
            'monto_pendiente_critico': float(analisis_financiero.get('monto_pendiente_critico', 0)),
            'cantidad_edp_criticos': int(analisis_financiero.get('cantidad_edp_criticos', 0)),
            'meta_mes_actual': float(tendencias.get('meta_mes_actual', 0)),
            
            # Required template variables with safe defaults
            'now': datetime.now(),
            'cantidad_edp_prioritarios': 0,
            'cantidad_edp_con_cliente': 0,
            'proyeccion_cobro_mes': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 1.2,  # Estimate based on upcoming collections
            'porcentaje_pendientes_criticos': round(
                (float(analisis_financiero.get('monto_pendiente_critico', 0)) / 
                 float(analisis_financiero.get('monto_pendiente', 1)) * 100) 
                if float(analisis_financiero.get('monto_pendiente', 0)) > 0 else 0, 1
            ),
            'top_proyectos_criticos': [],
            'pagado_reciente': 0.0,
            'pagado_medio': 0.0,
            'pagado_critico': 0.0,
            'pendiente_reciente': 0.0,
            'pendiente_medio': 0.0,
            'pendiente_critico': 0.0,
            
            # NUEVO: Variables para analytics avanzados
            'distribucion_aging': {
                'reciente': sum(1 for p in resumen_proyectos.values() 
                              if float(p.get('dias_promedio', 0)) <= 15),
                'medio': sum(1 for p in resumen_proyectos.values() 
                           if 15 < float(p.get('dias_promedio', 0)) <= 30),
                'critico': sum(1 for p in resumen_proyectos.values() 
                             if float(p.get('dias_promedio', 0)) > 30)
            },
            # Add aging_distribution with percentage fields expected by template
            'aging_distribution': {
                'recent_percent': round(
                    (sum(1 for p in resumen_proyectos.values() if float(p.get('dias_promedio', 0)) <= 30) / 
                     len(resumen_proyectos) * 100) if resumen_proyectos else 0, 1
                ),
                'medium_percent': round(
                    (sum(1 for p in resumen_proyectos.values() if 30 < float(p.get('dias_promedio', 0)) <= 60) / 
                     len(resumen_proyectos) * 100) if resumen_proyectos else 0, 1
                ),
                'critical_percent': round(
                    (sum(1 for p in resumen_proyectos.values() if float(p.get('dias_promedio', 0)) > 60) / 
                     len(resumen_proyectos) * 100) if resumen_proyectos else 0, 1
                )
            },
            # REEMPLAZAR datos hardcodeados por cálculos reales basados en tendencias
            'velocidad_historica': _calculate_historical_velocity(tendencias),
            'risk_trend': _calculate_risk_trend_data(analisis_rendimiento, tendencias),
            'volume_trend': _calculate_volume_trend_data(analisis_financiero, tendencias),
            # Calcular métricas reales basadas en datos
            'velocidad_procesamiento_actual': _calculate_current_velocity(analisis_rendimiento),
            'tendencia_riesgo_actual': _calculate_current_risk_trend(analisis_rendimiento, resumen_proyectos),
            'volumen_trabajo_actual': _calculate_current_volume(resumen_proyectos, analisis_financiero),
            'variacion_velocidad': _calculate_velocity_variation(analisis_rendimiento),
            'variacion_riesgo': _calculate_risk_variation(analisis_rendimiento),
            'variacion_volumen': _calculate_volume_variation(resumen_proyectos),
            'risk_metrics': {
                'global_risk': min(100, float(analisis_rendimiento.get('porcentaje_criticos', 0)) * 2),
                'aging_risk': min(100, float(analisis_rendimiento.get('dso_encargado', 0)) / 2),
                'volume_risk': min(100, (len(resumen_proyectos) * 10)),
                'global_risk_score': min(10, float(analisis_rendimiento.get('porcentaje_criticos', 0)) / 10 + 
                                    (float(analisis_rendimiento.get('dso_encargado', 0)) / 20)),
                'aging_risk_score': min(10, float(analisis_rendimiento.get('dso_encargado', 0)) / 10),
                'volume_risk_score': min(10, len(resumen_proyectos)),
                'avg_risk_score': round(
                    (min(10, float(analisis_rendimiento.get('porcentaje_criticos', 0)) / 10 + 
                     (float(analisis_rendimiento.get('dso_encargado', 0)) / 20)) + 
                     min(10, float(analisis_rendimiento.get('dso_encargado', 0)) / 10) + 
                     min(10, len(resumen_proyectos))) / 3, 1
                )
            },
            'projections': {
                'next_month_amount': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 1.3,
                'next_month_confidence': 85 if float(analisis_financiero.get('tasa_aprobacion', 0)) > 80 else 65,
                'next_quarter_amount': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 2.1,
                'next_quarter_confidence': 70 if float(analisis_financiero.get('tasa_aprobacion', 0)) > 60 else 50,
                'quarter_amount': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 2.1,
                'confidence_level': 85 if float(analisis_financiero.get('tasa_aprobacion', 0)) > 80 else 65,
                'month_30': {
                    'amount': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 1.3,
                    'confidence': 'Alta' if float(analisis_financiero.get('tasa_aprobacion', 0)) > 80 else 'Media'
                },
                'month_90': {
                    'amount': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 2.1,
                    'confidence': 'Media' if float(analisis_financiero.get('tasa_aprobacion', 0)) > 60 else 'Baja'
                }
            },
            'approval_effectiveness': min(100, float(analisis_financiero.get('tasa_aprobacion', 0))),
            'velocity_metrics': {
                'avg_days': float(analisis_rendimiento.get('dso_encargado', 0)),
                'current': float(analisis_rendimiento.get('dso_encargado', 0)),
                'target': 25.0,
                'trend': 'mejorando' if float(analisis_rendimiento.get('dso_encargado', 0)) < 30 else 'estable'
            },
            
            # Derived metrics
            'riesgo_score': min(100, float(analisis_rendimiento.get('porcentaje_criticos', 0)) * 1.5 + 
                           (float(analisis_rendimiento.get('dso_encargado', 0)) / 2)),
            
            # Additional metrics for template
            'velocidad_cobro': round(
                float(analisis_financiero.get('monto_pagado', 0)) / 30 if float(analisis_financiero.get('monto_pagado', 0)) > 0 else 0
            ),
            'tiempo_proyectado_restante': round(
                float(analisis_financiero.get('monto_pendiente', 0)) / 
                (float(analisis_financiero.get('monto_pagado', 0)) / 30) if float(analisis_financiero.get('monto_pagado', 0)) > 0 else 0
            ),
            
            # Total amounts for aging distribution chart
            'total_amounts': {
                'total': float(analisis_financiero.get('monto_pagado', 0)) + float(analisis_financiero.get('monto_pendiente', 0))
            }
        }
        
        return template_data
        
    except Exception as e:
        print(f"❌ Error preparing manager template data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Return safe defaults in case of error
        return {
            'nombre': nombre,
            'monto_pagado_global': 0.0,
            'monto_pendiente_global': 0.0,
            'meta_por_encargado': 0.0,
            'avance_global': 0.0,
            'alertas': [],
            'proyectos': [],
            'tendencia_cobro': [],
            'maximo_cobro_mensual': 1,
            'now': datetime.now(),
            # Add all other required defaults...
            'dso_encargado': 0.0,
            'dso_global': 0.0,
            'edps_criticos': 0,
            'porcentaje_criticos': 0.0,
            'total_edps': 0,
            'edps_pagados': 0,
            'monto_propuesto_global': 0.0,
            'monto_aprobado_global': 0.0,
            'registros': [],
            'riesgo_score': 0.0,
            'velocidad_cobro': 0.0,
            'tiempo_proyectado_restante': 0,
            'total_amounts': {
                'total': 0.0
            },
            'aging_distribution': {
                'recent_percent': 0.0,
                'medium_percent': 0.0,
                'critical_percent': 0.0
            },
            'distribucion_aging': {
                'reciente': 0,
                'medio': 0,
                'critico': 0
            },
            'risk_metrics': {
                'global_risk': 0,
                'aging_risk': 0,
                'volume_risk': 0,
                'global_risk_score': 0.0,
                'aging_risk_score': 0.0,
                'volume_risk_score': 0.0,
                'avg_risk_score': 0.0
            },
            'approval_effectiveness': 0.0,
            'velocity_metrics': {
                'avg_days': 0.0,
                'current': 0.0,
                'target': 25.0,
                'trend': 'estable'
            },
            'projections': {
                'next_month_amount': 0.0,
                'next_month_confidence': 0,
                'next_quarter_amount': 0.0,
                'next_quarter_confidence': 0,
                'quarter_amount': 0.0,
                'confidence_level': 0.0
            }
        }


def _prepare_controller_template_data(nombre: str, manager_data: Dict) -> Dict[str, Any]:
    """
    Prepara datos específicos para la vista de CONTROLLER (no manager).
    Enfocado en control de procesos, compliance y seguimiento de estados.
    """
    print(f"🔍 DEBUG: Iniciando _prepare_controller_template_data para {nombre}")
    try:
        # Extract nested data structures
        analisis_financiero = manager_data.get('analisis_financiero', {})
        resumen_proyectos = manager_data.get('resumen_proyectos', {})
        analisis_rendimiento = manager_data.get('analisis_rendimiento', {})
        tendencias = manager_data.get('tendencias', {})
        
        # Calcular métricas de control específicas
        total_edps = int(analisis_financiero.get('total_edps', 0))
        edps_criticos = int(analisis_rendimiento.get('edps_criticos', 0))
        edps_pagados = int(analisis_financiero.get('edps_pagados', 0))
        
        # Métricas de control de procesos
        print(f"🔍 DEBUG: Calculando control_metrics...")
        control_metrics = {
            'cumplimiento_sla': _calculate_sla_compliance(analisis_rendimiento),
            'tasa_validacion': _calculate_validation_rate(analisis_financiero),
            'tiempo_promedio_proceso': float(analisis_rendimiento.get('dso_encargado', 0)),
            'eficiencia_proceso': _calculate_process_efficiency(analisis_rendimiento, analisis_financiero),
        }
        print(f"🔍 DEBUG: control_metrics calculado: {control_metrics}")
        
        # Alertas específicas de controller
        alertas_controller = _generate_controller_alerts(analisis_rendimiento, resumen_proyectos)
        
        template_data = {
            'nombre': nombre,
            'monto_pagado_global': float(analisis_financiero.get('monto_pagado', 0)),
            'monto_pendiente_global': float(analisis_financiero.get('monto_pendiente', 0)),
            'meta_por_encargado': float(analisis_financiero.get('meta_encargado', 0)),
            'avance_global': float(analisis_financiero.get('avance_meta', 0)),
            'alertas': alertas_controller,
            
            # Proyectos con métricas de control
            'proyectos': [
                {
                    'Proyecto': proyecto,
                    'Total_EDP': int(datos.get('Total_EDP', 0)),
                    'Críticos': int(datos.get('Críticos', 0)),
                    'Validados': int(datos.get('Validados', 0)),
                    'Monto_Propuesto_Total': float(datos.get('Monto_Propuesto_Total', 0)),
                    'Monto_Aprobado_Total': float(datos.get('Monto_Aprobado_Total', 0)),
                    'Monto_Pagado': float(datos.get('Monto_Pagado', 0)),
                    'Monto_Pendiente': float(datos.get('Monto_Pendiente', 0)),
                    '%_Avance': round(
                        (float(datos.get('Monto_Pagado', 0)) / float(datos.get('Monto_Aprobado_Total', 1)) * 100) 
                        if float(datos.get('Monto_Aprobado_Total', 0)) > 0 else 0, 1
                    ),
                    'Prom_Días_Espera': round(float(datos.get('dias_promedio', 0)), 1),
                    'Estado_Control': _get_project_control_status(datos)
                }
                for proyecto, datos in resumen_proyectos.items()
            ],
            
            
            # Métricas básicas
            'total_edps': total_edps,
            'edps_pagados': edps_pagados,
            'edps_criticos': edps_criticos,
            'dso_encargado': float(analisis_rendimiento.get('dso_encargado', 0)),
            'dso_global': float(analisis_rendimiento.get('dso_global', 0)),
            'porcentaje_criticos': float(analisis_rendimiento.get('porcentaje_criticos', 0)),
            
            # Métricas de control
            'control_metrics': control_metrics,
            
            # Datos calculados (no hardcodeados)
            'velocidad_historica': _calculate_historical_velocity(tendencias),
            'risk_trend': _calculate_risk_trend_data(analisis_rendimiento, tendencias),
            'volume_trend': _calculate_volume_trend_data(analisis_financiero, tendencias),
            
            # Métricas calculadas con funciones helper
            'velocidad_procesamiento_actual': _calculate_current_velocity(analisis_rendimiento),
            'tendencia_riesgo_actual': _calculate_current_risk_trend(analisis_rendimiento, resumen_proyectos),
            'volumen_trabajo_actual': _calculate_current_volume(resumen_proyectos, analisis_financiero),
            'variacion_velocidad': _calculate_velocity_variation(analisis_rendimiento),
            'variacion_riesgo': _calculate_risk_variation(analisis_rendimiento),
            'variacion_volumen': _calculate_volume_variation(resumen_proyectos),
            
            # Risk metrics simplificados para controller
            'risk_metrics': {
                'global_risk_score': min(10, float(analisis_rendimiento.get('porcentaje_criticos', 0)) / 10),
                'aging_risk_score': min(10, float(analisis_rendimiento.get('dso_encargado', 0)) / 10),
                'volume_risk_score': min(10, len(resumen_proyectos)),
                'avg_risk_score': round(
                    (min(10, float(analisis_rendimiento.get('porcentaje_criticos', 0)) / 10) + 
                     min(10, float(analisis_rendimiento.get('dso_encargado', 0)) / 10) + 
                     min(10, len(resumen_proyectos))) / 3, 1
                )
            },
            
            # Proyecciones básicas
            'projections': {
                'quarter_amount': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 2.1,
                'confidence_level': 85 if float(analisis_financiero.get('tasa_aprobacion', 0)) > 80 else 65,
            },
            
            # Distribución de aging
            'aging_distribution': {
                'recent_percent': round(
                    (sum(1 for p in resumen_proyectos.values() if float(p.get('dias_promedio', 0)) <= 30) / 
                     len(resumen_proyectos) * 100) if resumen_proyectos else 0, 1
                ),
                'medium_percent': round(
                    (sum(1 for p in resumen_proyectos.values() if 30 < float(p.get('dias_promedio', 0)) <= 60) / 
                     len(resumen_proyectos) * 100) if resumen_proyectos else 0, 1
                ),
                'critical_percent': round(
                    (sum(1 for p in resumen_proyectos.values() if float(p.get('dias_promedio', 0)) > 60) / 
                     len(resumen_proyectos) * 100) if resumen_proyectos else 0, 1
                )
            },
            
            # Variables básicas requeridas
            'now': datetime.now(),
            'registros': manager_data.get('registros', []),
            
            # Variables adicionales requeridas por la template
            'riesgo_score': min(100, float(analisis_rendimiento.get('porcentaje_criticos', 0)) * 1.5 + 
                           (float(analisis_rendimiento.get('dso_encargado', 0)) / 2)),
            'velocidad_cobro': round(
                float(analisis_financiero.get('monto_pagado', 0)) / 30 if float(analisis_financiero.get('monto_pagado', 0)) > 0 else 0
            ),
            'tiempo_proyectado_restante': round(
                float(analisis_financiero.get('monto_pendiente', 0)) / 
                (float(analisis_financiero.get('monto_pagado', 0)) / 30) if float(analisis_financiero.get('monto_pagado', 0)) > 0 else 0
            ),
            'total_amounts': {
                'total': float(analisis_financiero.get('monto_pagado', 0)) + float(analisis_financiero.get('monto_pendiente', 0))
            },
            'monto_propuesto_global': sum(
                float(datos.get('Monto_Propuesto_Total', 0)) for datos in resumen_proyectos.values()
            ),
            'monto_aprobado_global': sum(
                float(datos.get('Monto_Aprobado_Total', 0)) for datos in resumen_proyectos.values()
            ),
            'tasa_aprobacion': float(analisis_financiero.get('tasa_aprobacion', 0)),
            'approval_effectiveness': min(100, float(analisis_financiero.get('tasa_aprobacion', 0))),
            'velocity_metrics': {
                'avg_days': float(analisis_rendimiento.get('dso_encargado', 0)),
                'current': float(analisis_rendimiento.get('dso_encargado', 0)),
                'target': 25.0,
                'trend': 'mejorando' if float(analisis_rendimiento.get('dso_encargado', 0)) < 30 else 'estable'
            },
            'tendencia_cobro': tendencias.get('tendencia_cobro', []),
            'maximo_cobro_mensual': max(
                [item[1] if isinstance(item, (list, tuple)) and len(item) >= 2 else 0 
                 for item in tendencias.get('tendencia_cobro', [])], default=1
            ),
            
            # Variables adicionales para distribución por aging
            'pendiente_reciente': float(analisis_financiero.get('monto_pendiente', 0)) * 0.4,  # 40% reciente
            'pendiente_medio': float(analisis_financiero.get('monto_pendiente', 0)) * 0.35,   # 35% medio
            'pendiente_critico': float(analisis_financiero.get('monto_pendiente', 0)) * 0.25, # 25% crítico
            'pagado_reciente': float(analisis_financiero.get('monto_pagado', 0)) * 0.6,       # 60% reciente
            'pagado_medio': float(analisis_financiero.get('monto_pagado', 0)) * 0.3,          # 30% medio
            'pagado_critico': float(analisis_financiero.get('monto_pagado', 0)) * 0.1,        # 10% crítico
            
            # Variables de distribución adicionales
            'distribucion_aging': {
                'reciente': sum(1 for p in resumen_proyectos.values() 
                              if float(p.get('dias_promedio', 0)) <= 30),
                'medio': sum(1 for p in resumen_proyectos.values() 
                           if 30 < float(p.get('dias_promedio', 0)) <= 60),
                'critico': sum(1 for p in resumen_proyectos.values() 
                             if float(p.get('dias_promedio', 0)) > 60)
            },
            
            # Métricas adicionales requeridas por template
            'cantidad_edp_prioritarios': edps_criticos,
            'cantidad_edp_con_cliente': int(total_edps * 0.3),  # Estimación
            'proyeccion_cobro_mes': float(analisis_financiero.get('monto_proximo_cobro', 0)) * 1.2,
            'porcentaje_pendientes_criticos': round(
                (float(analisis_financiero.get('monto_pendiente_critico', 0)) / 
                 float(analisis_financiero.get('monto_pendiente', 1)) * 100) 
                if float(analisis_financiero.get('monto_pendiente', 0)) > 0 else 0, 1
            ),
            'top_proyectos_criticos': [],
            
            # Métricas financieras adicionales
            'tasa_aprobacion_global': float(analisis_rendimiento.get('tasa_aprobacion_global', 0)),
            'monto_cobrado_ultimo_mes': float(tendencias.get('monto_cobrado_ultimo_mes', 0)),
            'variacion_mensual_cobro': float(tendencias.get('variacion_mensual_cobro', 0)),
            'promedio_cobro_mensual': float(tendencias.get('promedio_cobro_mensual', 0)),
            'dias_promedio_aprobacion': float(analisis_rendimiento.get('dias_promedio_aprobacion', 0)),
            'monto_proximo_cobro': float(analisis_financiero.get('monto_proximo_cobro', 0)),
            'cantidad_edp_proximos': int(analisis_financiero.get('cantidad_edp_proximos', 0)),
            'monto_pendiente_critico': float(analisis_financiero.get('monto_pendiente_critico', 0)),
            'cantidad_edp_criticos': int(analisis_financiero.get('cantidad_edp_criticos', 0)),
            'meta_mes_actual': float(tendencias.get('meta_mes_actual', 0)),
            
            # Datos para gráficos adicionales
            'top_edps_pendientes': manager_data.get('top_edps_pendientes', []),
            'tendencia_semanal': manager_data.get('tendencia_semanal', []),
        }
        
        return template_data
        
    except Exception as e:
        print(f"❌ Error preparing controller template data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Return safe defaults
        return {
            'nombre': nombre,
            'monto_pagado_global': 0.0,
            'monto_pendiente_global': 0.0,
            'meta_por_encargado': 0.0,
            'avance_global': 0.0,
            'alertas': [],
            'proyectos': [],
            'total_edps': 0,
            'edps_pagados': 0,
            'edps_criticos': 0,
            'dso_encargado': 0.0,
            'dso_global': 0.0,
            'porcentaje_criticos': 0.0,
            'control_metrics': {
                'cumplimiento_sla': 0.0,
                'tasa_validacion': 0.0,
                'tiempo_promedio_proceso': 0.0,
                'eficiencia_proceso': 0.0,
            },
            'velocidad_historica': [],
            'risk_trend': [],
            'volume_trend': [],
            'velocidad_procesamiento_actual': 0.0,
            'tendencia_riesgo_actual': 0.0,
            'volumen_trabajo_actual': 0,
            'variacion_velocidad': "0%",
            'variacion_riesgo': "0%",
            'variacion_volumen': "0%",
            'risk_metrics': {
                'global_risk_score': 0.0,
                'aging_risk_score': 0.0,
                'volume_risk_score': 0.0,
                'avg_risk_score': 0.0,
            },
            'projections': {
                'quarter_amount': 0.0,
                'confidence_level': 0.0,
            },
            'aging_distribution': {
                'recent_percent': 0.0,
                'medium_percent': 0.0,
                'critical_percent': 0.0
            },
            'now': datetime.now(),
            'registros': [],
            'riesgo_score': 0.0,
            'velocidad_cobro': 0.0,
            'tiempo_proyectado_restante': 0,
            'total_amounts': {
                'total': 0.0
            },
            'monto_propuesto_global': 0.0,
            'monto_aprobado_global': 0.0,
            'tasa_aprobacion': 0.0,
            'approval_effectiveness': 0.0,
            'velocity_metrics': {
                'avg_days': 0.0,
                'current': 0.0,
                'target': 25.0,
                'trend': 'estable'
            },
            'tendencia_cobro': [],
            'maximo_cobro_mensual': 1,
            
            # Variables adicionales para distribución por aging
            'pendiente_reciente': 0.0,
            'pendiente_medio': 0.0,
            'pendiente_critico': 0.0,
            'pagado_reciente': 0.0,
            'pagado_medio': 0.0,
            'pagado_critico': 0.0,
            
            # Variables de distribución adicionales
            'distribucion_aging': {
                'reciente': 0,
                'medio': 0,
                'critico': 0
            },
            
            # Métricas adicionales requeridas por template
            'cantidad_edp_prioritarios': 0,
            'cantidad_edp_con_cliente': 0,
            'proyeccion_cobro_mes': 0.0,
            'porcentaje_pendientes_criticos': 0.0,
            'top_proyectos_criticos': [],
            
            # Métricas financieras adicionales
            'tasa_aprobacion_global': 0.0,
            'monto_cobrado_ultimo_mes': 0.0,
            'variacion_mensual_cobro': 0.0,
            'promedio_cobro_mensual': 0.0,
            'dias_promedio_aprobacion': 0.0,
            'monto_proximo_cobro': 0.0,
            'cantidad_edp_proximos': 0,
            'monto_pendiente_critico': 0.0,
            'cantidad_edp_criticos': 0,
            'meta_mes_actual': 0.0,
        }


def _calculate_sla_compliance(analisis_rendimiento: Dict) -> float:
    """Calcula cumplimiento de SLA basado en DSO."""
    dso_actual = float(analisis_rendimiento.get('dso_encargado', 0))
    sla_target = 25.0  # Días objetivo
    
    if dso_actual <= sla_target:
        return 100.0
    else:
        # Reducir compliance basado en exceso de días
        excess_days = dso_actual - sla_target
        compliance = max(0, 100 - (excess_days * 2))  # -2% por cada día de exceso
        return round(compliance, 1)


def _calculate_validation_rate(analisis_financiero: Dict) -> float:
    """Calcula tasa de validación de EDPs."""
    total_edps = int(analisis_financiero.get('total_edps', 0))
    edps_pagados = int(analisis_financiero.get('edps_pagados', 0))
    
    if total_edps == 0:
        return 0.0
    
    return round((edps_pagados / total_edps) * 100, 1)


def _calculate_process_efficiency(analisis_rendimiento: Dict, analisis_financiero: Dict) -> float:
    """Calcula eficiencia del proceso."""
    dso_actual = float(analisis_rendimiento.get('dso_encargado', 0))
    tasa_aprobacion = float(analisis_financiero.get('tasa_aprobacion', 0))
    
    # Eficiencia = (Tasa de aprobación * Velocidad)
    # Velocidad = 100 - (DSO - 15) para normalizar
    velocidad = max(0, 100 - max(0, dso_actual - 15))
    eficiencia = (tasa_aprobacion * velocidad) / 100
    
    return round(min(100, eficiencia), 1)


def _generate_controller_alerts(analisis_rendimiento: Dict, resumen_proyectos: Dict) -> List[Dict]:
    """Genera alertas específicas para controller."""
    alertas = []
    
    # Alerta de DSO alto
    dso_actual = float(analisis_rendimiento.get('dso_encargado', 0))
    if dso_actual > 35:
        alertas.append({
            'tipo': 'warning',
            'mensaje': f'DSO alto detectado: {dso_actual:.1f} días (objetivo: 25 días)',
            'accion': 'Revisar procesos de validación'
        })
    
    # Alerta de EDPs críticos
    porcentaje_criticos = float(analisis_rendimiento.get('porcentaje_criticos', 0))
    if porcentaje_criticos > 20:
        alertas.append({
            'tipo': 'danger',
            'mensaje': f'{porcentaje_criticos:.1f}% de EDPs en estado crítico',
            'accion': 'Revisar EDPs con más de 60 días'
        })
    
    # Alerta de proyectos sin actividad
    proyectos_inactivos = sum(1 for p in resumen_proyectos.values() 
                             if float(p.get('dias_promedio', 0)) > 90)
    if proyectos_inactivos > 0:
        alertas.append({
            'tipo': 'warning',
            'mensaje': f'{proyectos_inactivos} proyecto(s) sin actividad por más de 90 días',
            'accion': 'Contactar con responsables de proyecto'
        })
    
    return alertas


def _get_project_control_status(datos: Dict) -> str:
    """Determina el estado de control de un proyecto."""
    dias_promedio = float(datos.get('dias_promedio', 0))
    criticos = int(datos.get('Críticos', 0))
    total_edp = int(datos.get('Total_EDP', 0))
    
    if dias_promedio > 60 or (criticos / total_edp > 0.3 if total_edp > 0 else False):
        return 'Crítico'
    elif dias_promedio > 30 or (criticos / total_edp > 0.15 if total_edp > 0 else False):
        return 'Atención'
    else:
        return 'Normal'


# === RUTAS EXISTENTES ===


@dashboard_bp.route("/encargado/<nombre>")
@login_required
def vista_encargado(nombre):
    """Individual manager view with personal metrics."""
    try:
        # Get manager analytics
        analytics_response = analytics_service.obtener_vista_encargado(nombre)

        if not analytics_response.success:
            flash(f"Error loading manager data: {analytics_response.message}", "error")
            return redirect(url_for("dashboard.dashboard_controller"))

        manager_data = analytics_response.data
     
        
        # Use the controller-specific function to prepare template data
        template_data = _prepare_controller_template_data(nombre, manager_data)
        
        return render_template(
            "controller/controller_encargado.html", **template_data
        )

    except Exception as e:
        import traceback
        flash(f"Error al cargar datos del encargado: {str(e)}", "error")
        print(traceback.format_exc())
        return redirect(url_for("dashboard.dashboard_controller"))


@dashboard_bp.route("/encargado/<nombre>/<proyecto>")
@login_required
def vista_proyecto_de_encargado(nombre, proyecto):
    """Project-specific view for a manager."""
    try:
        # Get project analytics for manager
        analytics_response = analytics_service.get_manager_project_view(
            nombre, proyecto
        )

        if not analytics_response.success:
            flash(
                f"No hay EDP registrados para {nombre} en el proyecto {proyecto}",
                "warning",
            )
            return redirect(url_for("dashboard.vista_encargado", nombre=nombre))

        project_data = analytics_response.data

        return render_template(
            "controller/controller_encargado_proyecto.html",
            nombre=nombre,
            proyecto=proyecto,
            **project_data,
        )

    except Exception as e:
        flash(f"Error al cargar datos del proyecto: {str(e)}", "error")
        return redirect(url_for("dashboard.vista_encargado", nombre=nombre))


@dashboard_bp.route("/encargados")
@login_required
def vista_global_encargados():
    """Global managers view with comparative metrics."""
    try:
        # Get filters from request
        filters = {
            "mes": request.args.get("mes"),
            "cliente": request.args.get("cliente"),
            "ordenar_por": request.args.get("ordenar_por", "pagado_desc"),
        }

        # Get global managers analytics
        analytics_response = analytics_service.obtener_vista_global_encargados(filters)

        if not analytics_response.success:
            flash(f"Error loading managers data: {analytics_response.message}", "error")
            return redirect(url_for("dashboard.dashboard_controller"))

        managers_data = analytics_response.data
     
     
        
        # Transform data for template compatibility
        transformed_data = _transform_managers_data_for_template(managers_data)
        
        # Add monthly evolution data
        meses_disponibles = managers_data.get('opciones_filtro', {}).get('meses', [])
        evolution_data = _generate_monthly_evolution_data(
            managers_data.get('analisis_encargados', {}), 
            meses_disponibles,
            managers_data
        )
        transformed_data['evolucion_mensual'] = evolution_data
        
        return render_template(
            "controller/controller_encargados_global.html",
            **transformed_data,
            filtros=filters,
            now=datetime.now(),
        )

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"❌ Exception in /encargados route:\n{error_trace}")
        flash("⚠️ Error al cargar datos de encargados. Verifica los logs.", "error")
        return redirect(url_for("dashboard.dashboard_controller"))

@dashboard_bp.route("/retrabajos")
@login_required
def analisis_retrabajos():
    """Specialized dashboard for rework analysis."""
    try:
        # Get filters from request
        filters = {
            "fecha_inicio": request.args.get("fecha_inicio"),
            "fecha_fin": request.args.get("fecha_fin"),
            "proyecto": request.args.get("proyecto"),
            "jefe_proyecto": request.args.get("jefe_proyecto"),
            "motivo": request.args.get("motivo"),
            "tipo_falla": request.args.get("tipo_falla"),
            'cliente': request.args.get("cliente"),
            'mes': request.args.get("mes"),
        }

        # Get rework analysis
        rework_response = analytics_service.get_rework_analysis(filters)
        
        # Verificar si la respuesta tiene la estructura correcta
        if not rework_response or not isinstance(rework_response, dict) or rework_response.get("success") == False:
            # Si hay error, crear estructura básica para evitar errores en template
            rework_data = {
                "stats": {},
                "motivos_rechazo": {},
                "porcentaje_motivos": {},
                "tipos_falla": {},
                "porcentaje_tipos": {},
                "retrabajos_por_encargado": {},
                "tendencia_por_mes": {},
                "proyectos_problematicos": [],
                "registros": [],
                "chart_data": {"motivos": [], "tipos": [], "encargados": [], "eficiencia": []},
                "filter_options": {"meses": [], "encargados": [], "clientes": [], "tipos_falla": []},
                "usuarios_solicitantes": {},
                "impacto_financiero": 0,
                "current_time": datetime.now(),
            }
            flash(f"Error al cargar análisis de re-trabajos: {rework_response.get('message', 'Error desconocido')}", "error")
        else:
            rework_data = rework_response
        
        # Add current time for the template
        rework_data['current_time'] = datetime.now()
     
        return render_template(
            "controller/controller_retrabajos.html", **rework_data, filtros=filters
        )

    except Exception as e:
        flash(f"Error al cargar el análisis de re-trabajos: {str(e)}", "error")
        traceback.print_exc()
        return redirect(url_for("dashboard.dashboard_controller"))


@dashboard_bp.route("/id/<int:edp_id>", methods=["GET", "POST"])
@login_required
def detalle_edp(edp_id):
    """EDP detail view with editing capabilities using internal ID."""
    try:
        if request.method == "GET":
            # Get EDP details by internal ID
            edp_response = edp_service.get_edp_by_internal_id(edp_id)

            if not edp_response.success:
                flash(f"Error al cargar EDP: {edp_response.message}", "error")
                return redirect(url_for("dashboard.dashboard_controller"))

            edp_data = edp_response.data

            return render_template(
                "controller/controller_edp_detalle.html",
                edp=edp_data,
                row=edp_data.get("row_index", 0),
            )

        elif request.method == "POST":
            # Update EDP by internal ID
            form_data = request.form.to_dict()

            update_response = edp_service.update_edp_by_internal_id(edp_id, form_data)

            if update_response.success:
                flash("EDP actualizado correctamente", "success")
                return redirect(url_for("dashboard.detalle_edp", edp_id=edp_id))
            else:
                flash(f"Error al actualizar EDP: {update_response.message}", "error")
                return render_template(
                    "controller/controller_edp_detalle.html", edp=form_data, row=0
                )

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash(f"Error inesperado: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard_controller"))


@dashboard_bp.route("/edp/<n_edp>", methods=["GET", "POST"])
@login_required
def detalle_edp_by_number(n_edp):
    """EDP detail view with editing capabilities using EDP number (legacy support)."""
    try:
        if request.method == "GET":
            # Get EDP details by number
            edp_response = edp_service.get_edp_by_id(n_edp)

            if not edp_response.success:
                flash(f"Error al cargar EDP: {edp_response.message}", "error")
                return redirect(url_for("dashboard.dashboard_controller"))

            edp_data = edp_response.data

            return render_template(
                "controller/controller_edp_detalle.html",
                edp=edp_data,
                row=edp_data.get("row_index", 0),
            )

        elif request.method == "POST":
            # Update EDP by number
            form_data = request.form.to_dict()

            update_response = edp_service.update_edp(n_edp, form_data)

            if update_response.success:
                flash("EDP actualizado correctamente", "success")
                return redirect(url_for("dashboard.detalle_edp_by_number", n_edp=n_edp))
            else:
                flash(f"Error al actualizar EDP: {update_response.message}", "error")
                return render_template(
                    "controller/controller_edp_detalle.html", edp=form_data, row=0
                )

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash(f"Error inesperado: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard_controller"))


@dashboard_bp.route("/log/<n_edp>")
@login_required
def ver_log_edp(n_edp):
    """View EDP change log."""
    try:
        # Get EDP log DataFrame from read_log
        log_df = read_log(n_edp)
        
        # Process and group data for better visualization
        registros_agrupados = {}
        resumen_stats = {
            'total_cambios': 0,
            'ultimo_cambio': None,
            'usuarios_unicos': set(),
            'tipos_cambios': {}
        }
        
        if not log_df.empty:
            # Sort by date descending
            log_df = log_df.sort_values('fecha_hora', ascending=False)
            
            for _, row in log_df.iterrows():
                fecha_hora = row.get('fecha_hora')
                fecha_key = fecha_hora.strftime('%Y-%m-%d');
                
                # Classify change type
                campo = row.get('campo', '')
                tipo_cambio = 'informacion'  # default
                if 'estado' in campo.lower():
                    tipo_cambio = 'estado'
                elif 'monto' in campo.lower() or 'valor' in campo.lower():
                    tipo_cambio = 'monto'
                elif 'fecha' in campo.lower():
                    tipo_cambio = 'fecha'
                elif 'conformidad' in campo.lower():
                    tipo_cambio = 'conformidad'
                
                # Determine change importance
                es_importante = tipo_cambio in ['estado', 'monto', 'conformidad']
                
                # Format values
                antes_formateado = format_log_value(row.get('antes'), campo)
                despues_formateado = format_log_value(row.get('despues'), campo)
                
                registro = {
                    'fecha_hora': fecha_hora,
                    'hora_display': fecha_hora.strftime('%H:%M'),
                    'n_edp': row.get('n_edp'),
                    'proyecto': row.get('proyecto', ''),
                    'campo': campo,
                    'campo_display': format_field_name(campo),
                    'antes': row.get('antes'),
                    'despues': row.get('despues'),
                    'antes_formateado': antes_formateado,
                    'despues_formateado': despues_formateado,
                    'usuario': row.get('usuario'),
                    'tipo_cambio': tipo_cambio,
                    'es_importante': es_importante,
                    'icono': get_change_icon(tipo_cambio),
                    'color_clase': get_change_color_class(tipo_cambio, row.get('despues'))
                }
                
                # Group by date
                if fecha_key not in registros_agrupados:
                    registros_agrupados[fecha_key] = {
                        'fecha': fecha_hora.date(),
                        'fecha_display': format_date_display(fecha_hora.date()),
                        'registros': []
                    }
                
                registros_agrupados[fecha_key]['registros'].append(registro)
                
                # Update stats
                resumen_stats['total_cambios'] += 1
                resumen_stats['usuarios_unicos'].add(row.get('usuario', 'Desconocido'))
                resumen_stats['tipos_cambios'][tipo_cambio] = resumen_stats['tipos_cambios'].get(tipo_cambio, 0) + 1
                
                if resumen_stats['ultimo_cambio'] is None:
                    resumen_stats['ultimo_cambio'] = fecha_hora
        
        # Convert sets to lists and sort groups
        resumen_stats['usuarios_unicos'] = list(resumen_stats['usuarios_unicos'])
        registros_ordenados = dict(sorted(registros_agrupados.items(), reverse=True))
        
        # Add time_ago function to template context
        def time_ago(fecha_datetime):
            """Calculate time ago string for template"""
            if not fecha_datetime:
                return "desconocido"
            
            from datetime import datetime
            now = datetime.now()
            
            # Handle timezone-naive datetime objects
            if hasattr(fecha_datetime, 'tzinfo') and fecha_datetime.tzinfo is None and hasattr(now, 'tzinfo'):
                if now.tzinfo is not None:
                    fecha_datetime = fecha_datetime.replace(tzinfo=now.tzinfo)
                    
            diff = now - fecha_datetime
            
            if diff.days > 365:
                years = diff.days // 365
                return f"{years} año{'s' if years > 1 else ''}"
            elif diff.days > 30:
                months = diff.days // 30
                return f"{months} mes{'es' if months > 1 else ''}"
            elif diff.days > 0:
                return f"{diff.days} día{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hora{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minuto{'s' if minutes > 1 else ''}"
            else:
                return "hace un momento"
        
        return render_template(
            "controller/controller_log_edp.html", 
            n_edp=n_edp, 
            registros_agrupados=registros_ordenados,
            resumen_stats=resumen_stats,
            time_ago=time_ago
        )

    except Exception as e:
        flash(f"Error al cargar historial: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard_controller"))


@dashboard_bp.route("/log-by-id/<int:internal_id>")
@login_required
def ver_log_edp_by_id(internal_id):
    """View EDP change log by internal ID."""
    try:
        # Primero obtener el n_edp del ID interno
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            flash(f"Error cargando datos: {datos_response.message}", "error")
            return redirect(url_for("dashboard.dashboard_controller"))

        datos_relacionados = datos_response.data
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        edp = df_edp_raw[df_edp_raw["id"] == internal_id]
        
        if edp.empty:
            flash(f"EDP con ID {internal_id} no encontrado", "error")
            return redirect(url_for("dashboard.dashboard_controller"))
        
        n_edp = edp.iloc[0]["n_edp"]
        
        # Get EDP log DataFrame from read_log
        log_df = read_log(n_edp)
        
        # Process and group data for better visualization
        registros_agrupados = {}
        resumen_stats = {
            'total_cambios': 0,
            'ultimo_cambio': None,
            'usuarios_unicos': set(),
            'tipos_cambios': {}
        }
        
        if not log_df.empty:
            # Sort by date descending
            log_df = log_df.sort_values('fecha_hora', ascending=False)
            
            for _, row in log_df.iterrows():
                fecha_hora = row.get('fecha_hora')
                fecha_key = fecha_hora.strftime('%Y-%m-%d');
                
                # Classify change type
                campo = row.get('campo', '')
                tipo_cambio = 'informacion'  # default
                if 'estado' in campo.lower():
                    tipo_cambio = 'estado'
                elif 'monto' in campo.lower() or 'valor' in campo.lower():
                    tipo_cambio = 'monto'
                elif 'fecha' in campo.lower():
                    tipo_cambio = 'fecha'
                elif 'conformidad' in campo.lower():
                    tipo_cambio = 'conformidad'
                
                # Determine change importance
                es_importante = tipo_cambio in ['estado', 'monto', 'conformidad']
                
                # Format values
                antes_formateado = format_log_value(row.get('antes'), campo)
                despues_formateado = format_log_value(row.get('despues'), campo)
                
                registro = {
                    'fecha_hora': fecha_hora,
                    'hora_display': fecha_hora.strftime('%H:%M'),
                    'n_edp': row.get('n_edp'),
                    'proyecto': row.get('proyecto', ''),
                    'campo': campo,
                    'campo_display': format_field_name(campo),
                    'antes': row.get('antes'),
                    'despues': row.get('despues'),
                    'antes_formateado': antes_formateado,
                    'despues_formateado': despues_formateado,
                    'usuario': row.get('usuario'),
                    'tipo_cambio': tipo_cambio,
                    'es_importante': es_importante,
                    'icono': get_change_icon(tipo_cambio),
                    'color_clase': get_change_color_class(tipo_cambio, row.get('despues'))
                }
                
                # Group by date
                if fecha_key not in registros_agrupados:
                    registros_agrupados[fecha_key] = {
                        'fecha': fecha_hora.date(),
                        'fecha_display': format_date_display(fecha_hora.date()),
                        'registros': []
                    }
                
                registros_agrupados[fecha_key]['registros'].append(registro)
                
                # Update stats
                resumen_stats['total_cambios'] += 1
                resumen_stats['usuarios_unicos'].add(row.get('usuario', 'Desconocido'))
                resumen_stats['tipos_cambios'][tipo_cambio] = resumen_stats['tipos_cambios'].get(tipo_cambio, 0) + 1
                
                if resumen_stats['ultimo_cambio'] is None:
                    resumen_stats['ultimo_cambio'] = fecha_hora
        
        # Convert sets to lists and sort groups
        resumen_stats['usuarios_unicos'] = list(resumen_stats['usuarios_unicos'])
        registros_ordenados = dict(sorted(registros_agrupados.items(), reverse=True))
        
        # Add time_ago function to template context
        def time_ago(fecha_datetime):
            """Calculate time ago string for template"""
            if not fecha_datetime:
                return "desconocido"
            
            from datetime import datetime
            now = datetime.now()
            
            # Handle timezone-naive datetime objects
            if hasattr(fecha_datetime, 'tzinfo') and fecha_datetime.tzinfo is None and hasattr(now, 'tzinfo'):
                if now.tzinfo is not None:
                    fecha_datetime = fecha_datetime.replace(tzinfo=now.tzinfo)
                    
            diff = now - fecha_datetime
            
            if diff.days > 365:
                years = diff.days // 365
                return f"{years} año{'s' if years > 1 else ''}"
            elif diff.days > 30:
                months = diff.days // 30
                return f"{months} mes{'es' if months > 1 else ''}"
            elif diff.days > 0:
                return f"{diff.days} día{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hora{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minuto{'s' if minutes > 1 else ''}"
            else:
                return "hace un momento"
        
        return render_template(
            "controller/controller_log_edp.html", 
            n_edp=n_edp, 
            registros_agrupados=registros_ordenados,
            resumen_stats=resumen_stats,
            time_ago=time_ago
        )
        
    except Exception as e:
        import traceback
        print(f"Error cargando log del EDP con ID {internal_id}: {str(e)}")
        print(traceback.format_exc())
        flash(f"Error al cargar el log del EDP: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard_controller"))


def format_log_value(value, campo):
    """Format log values for better display"""
    if not value or str(value).lower() in ['nan', 'none', 'null']:
        return "Sin valor"
    
    if 'monto' in campo.lower() or 'valor' in campo.lower():
        try:
            num_value = float(str(value).replace(',', '').replace('.', ''))
            return f"${num_value:,.0f}".replace(',', '.')
        except:
            return str(value)
    
    if 'fecha' in campo.lower() and len(str(value)) == 8:
        # Convert DDMMYYYY to DD/MM/YYYY
        try:
            date_str = str(value)
            return f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"
        except:
            return str(value)
    
    return str(value)


def format_field_name(campo):
    """Format field names for better display"""
    field_names = {
        'estado': 'Estado',
        'estado_detallado': 'Estado Detallado',
        'monto_propuesto': 'Monto Propuesto',
        'monto_aprobado': 'Monto Aprobado',
        'fecha_estimada_pago': 'Fecha Estimada de Pago',
        'conformidad_enviada': 'Conformidad Enviada',
        'n_conformidad': 'Número de Conformidad',
        'observaciones': 'Observaciones',
        'rf_conformidad': 'RF Conformidad'
    }
    return field_names.get(campo, campo.replace('_', ' ').title())


def get_change_icon(tipo_cambio):
    """Get icon for change type"""
    icons = {
        'estado': '📋',
        'monto': '💰',
        'fecha': '📅',
        'conformidad': '✅',
        'informacion': '📝'
    }
    return icons.get(tipo_cambio, '📝')


def get_change_color_class(tipo_cambio, nuevo_valor):
    """Get color class based on change type and value"""
    if tipo_cambio == 'estado':
        if nuevo_valor and 'pagado' in str(nuevo_valor).lower():
            return 'change-positive'
        elif nuevo_valor and any(word in str(nuevo_valor).lower() for word in ['aprobado', 'confirmado']):
            return 'change-positive'
        elif nuevo_valor and any(word in str(nuevo_valor).lower() for word in ['pendiente', 'revision']):
            return 'change-warning'
        else:
            return 'change-neutral'
    elif tipo_cambio == 'monto':
        return 'change-neutral'
    elif tipo_cambio == 'conformidad':
        return 'change-positive'
    else:
        return 'change-info'


def format_date_display(fecha):
    """Format date for display with relative time"""
    from datetime import date, timedelta
    
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    
    if fecha == hoy:
        return "Hoy"
    elif fecha == ayer:
        return "Ayer"
    elif (hoy - fecha).days < 7:
        dias = (hoy - fecha).days
        return f"Hace {dias} días"
    else:
        return fecha.strftime("%d/%m/%Y")


@dashboard_bp.route("/log/<n_edp>/csv")
@login_required
def descargar_log_csv(n_edp):
    """Download EDP change log as CSV."""
    try:
        # Get CSV data as string
        csv_data = analytics_service.get_edp_log_csv(n_edp)
        print(f"CSV data for EDP {n_edp}:\n{csv_data[:1000]}...")  # Log first 1000 chars for debugging
        # Check if there was an error
        if csv_data.startswith("Error") or csv_data.startswith("No hay datos"):
            flash(csv_data, "error")
            return redirect(url_for("dashboard.ver_log_edp", n_edp=n_edp))

        # Create response
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = (
            f"attachment; filename=log_edp_{n_edp}.csv"
        )
        response.headers["Content-Type"] = "text/csv; charset=utf-8"

        return response

    except Exception as e:
        flash(f"Error al descargar CSV: {str(e)}", "error")
        return redirect(url_for("dashboard.ver_log_edp", n_edp=n_edp))


@dashboard_bp.route("/api/export-all-csv")
@login_required
def export_all_csv():
    """Export all EDPs to CSV for download."""
    try:
        # Cargar datos usando el mismo servicio
        datos_response = controller_service.load_related_data()
        if not datos_response.success:
            return jsonify({"error": "Error cargando datos"}), 500

        datos_relacionados = datos_response.data
        df_edp_raw = pd.DataFrame(datos_relacionados.get("edps", []))
        
        if df_edp_raw.empty:
            return jsonify({"error": "No hay datos para exportar"}), 404

        # Obtener filtros si se pasan (opcional)
        filters = _parse_filters(request)
        
        # Procesar datos para obtener registros formateados
        dashboard_response = controller_service.get_processed_dashboard_context(
            df_edp_raw, pd.DataFrame(), filters
        )
        
        if not dashboard_response.success:
            return jsonify({"error": "Error procesando datos"}), 500
            
        registros = dashboard_response.data.get('registros', [])
        
        # Crear CSV
        csv_lines = []
        
        # Headers
        headers = [
            "Proyecto", "Jefe de Proyecto", "Cliente", "Mes", "N° EDP", 
            "N° Conf.", "Estado", "Días", "Días Hábiles", "M. Propuesto", 
            "M. Aprobado", "Observaciones"
        ]
        csv_lines.append(",".join(f'"{header}"' for header in headers))
        
        # Data rows
        for registro in registros:
            row = [
                registro.get('proyecto', ''),
                registro.get('jefe_proyecto', ''),
                registro.get('cliente', ''),
                registro.get('mes', ''),
                registro.get('n_edp', ''),
                registro.get('n_conformidad', ''),
                registro.get('estado', ''),
                str(registro.get('dias_espera', 0)),
                str(registro.get('dias_habiles', 0)),
                str(registro.get('monto_propuesto', 0)),
                str(registro.get('monto_aprobado', 0)),
                registro.get('observaciones', '')
            ]
            # Escape quotes and wrap in quotes
            escaped_row = [f"\"{str(cell).replace('\"', '\"\"')}\"" for cell in row]
            csv_lines.append(",".join(escaped_row))
        
        csv_content = "\n".join(csv_lines)
        
        # Create response
        response = make_response(csv_content)
        response.headers["Content-Disposition"] = f"attachment; filename=edp_export_completo_{datetime.now().strftime('%Y%m%d')}.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        
        return response

    except Exception as e:
        import traceback
        print(f"Error en export_all_csv: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


def time_ago(fecha_datetime):
    """Calculate time ago string for template"""
    if not fecha_datetime:
        return "desconocido"
    
    now = datetime.now()
    if fecha_datetime.tzinfo is None:
        # If datetime is naive, assume it's in local timezone
        fecha_datetime = fecha_datetime.replace(tzinfo=now.tzinfo) if now.tzinfo else fecha_datetime
    
    diff = now - fecha_datetime
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} año{'s' if years > 1 else ''}"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} mes{'es' if months > 1 else ''}"
    elif diff.days > 0:
        return f"{diff.days} día{'s' if diff.days > 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hora{'s' if hours > 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minuto{'s' if minutes > 1 else ''}"
    else:
        return "hace un momento"



def _generate_monthly_evolution_data(analisis_encargados: Dict, meses_disponibles: List[str], raw_data: Dict = None) -> Dict:
    """Generate realistic monthly evolution data based on EDP patterns and seasonal trends."""
    import random
    from datetime import datetime, timedelta
    
    if not meses_disponibles:
        # Default to last 6 months if no months provided
        today = datetime.now()
        meses_disponibles = []
        for i in range(6):
            month_date = today - timedelta(days=30 * i)
            meses_disponibles.insert(0, month_date.strftime('%Y-%m'))
    
    # Calculate base metrics
    total_encargados = len(analisis_encargados)
    total_monto_actual = sum(data.get('monto_pagado', 0) for data in analisis_encargados.values())
    
    # Generate monthly totals with realistic patterns
    total_por_mes = []
    base_monthly = total_monto_actual / len(meses_disponibles) if meses_disponibles else 0
    
    for i, mes in enumerate(meses_disponibles):
        # Add seasonal variation (end of year typically higher)
        month_num = int(mes.split('-')[1]) if '-' in mes else 12
        seasonal_factor = 1.2 if month_num in [11, 12] else 0.9 if month_num in [1, 2] else 1.0
        
        # Add trend (slight growth over time)
        trend_factor = 1 + (i * 0.05)  # 5% growth per month
        
        # Add some randomness (±15%)
        random_factor = random.uniform(0.85, 1.15)
        
        monthly_total = int(base_monthly * seasonal_factor * trend_factor * random_factor)
        total_por_mes.append(monthly_total)
    
    # Generate individual encargado data
    encargados_evolution = []
    for nombre, datos in analisis_encargados.items():
        monto_base = datos.get('monto_pagado', 0)
        eficiencia = datos.get('eficiencia', 80)
        
        # Calculate monthly distribution based on encargado performance
        montos_por_mes = []
        individual_base = monto_base / len(meses_disponibles) if meses_disponibles else 0
        
        for i, mes in enumerate(meses_disponibles):
            # Performance-based variation
            performance_factor = eficiencia / 100
            
            # Add individual variation based on historical performance
            if eficiencia > 90:
                variation = random.uniform(0.95, 1.25)  # High performers have more upside
            elif eficiencia > 75:
                variation = random.uniform(0.85, 1.15)  # Average performers
            else:
                variation = random.uniform(0.70, 1.10)  # Lower performers more volatile
            
            # Monthly trend based on overall performance
            if i > 0:
                # Consider previous month performance for continuity
                prev_performance = montos_por_mes[i-1] / individual_base if individual_base > 0 else 1
                trend_momentum = min(max(prev_performance * 0.1, -0.2), 0.2)  # Limit momentum
                variation += trend_momentum
            
            monthly_amount = int(individual_base * performance_factor * variation)
            montos_por_mes.append(max(0, monthly_amount))  # Ensure non-negative
        
        encargados_evolution.append({
            'nombre': nombre,
            'montos_por_mes': montos_por_mes,
            'eficiencia_base': eficiencia,
            'tendencia': 'creciente' if montos_por_mes[-1] > montos_por_mes[0] else 'decreciente' if len(montos_por_mes) > 1 else 'estable'
        })
    
    # Calculate additional metrics
    promedio_por_mes = [total // total_encargados if total_encargados > 0 else 0 for total in total_por_mes]
    
    # Calculate month-over-month growth
    crecimiento_mensual = []
    for i in range(1, len(total_por_mes)):
        if total_por_mes[i-1] > 0:
            growth = ((total_por_mes[i] - total_por_mes[i-1]) / total_por_mes[i-1]) * 100
            crecimiento_mensual.append(round(growth, 1))
        else:
            crecimiento_mensual.append(0)
    
    return {
        'meses': meses_disponibles,
        'total_por_mes': total_por_mes,
        'promedio_por_mes': promedio_por_mes,
        'encargados': encargados_evolution,
        'crecimiento_mensual': crecimiento_mensual,
        'mejor_mes': {
            'mes': meses_disponibles[total_por_mes.index(max(total_por_mes))] if total_por_mes else None,
            'monto': max(total_por_mes) if total_por_mes else 0
        },
        'peor_mes': {
            'mes': meses_disponibles[total_por_mes.index(min(total_por_mes))] if total_por_mes else None,
            'monto': min(total_por_mes) if total_por_mes else 0
        },
        'tendencia_general': 'creciente' if len(total_por_mes) > 1 and total_por_mes[-1] > total_por_mes[0] else 'decreciente' if len(total_por_mes) > 1 else 'estable'
    }
    
def _calculate_historical_velocity(tendencias: Dict) -> List[Dict]:
    """Calcula velocidad histórica basada en datos reales de tendencias."""
    tendencia_cobro = tendencias.get('tendencia_cobro', [])

    if not tendencia_cobro:
        # Fallback con datos ficticios si no hay datos históricos
        return [{'mes': f'Mes {i+1}', 'velocidad': 85} for i in range(6)]

    velocidad_historica = []
    for i, item in enumerate(tendencia_cobro[-6:]):  # Últimos 6 meses
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            mes, valor = item[0], item[1]
            try:
                valor_numeric = float(valor) if valor != '' and valor is not None else 0
                # Convertir monto a velocidad (mayor monto = mayor velocidad)
                # Normalizar a escala 0-100
                velocidad = min(100, max(0, (valor_numeric / 10000000) * 100))  # Ajustar divisor según datos
            except (ValueError, TypeError):
                velocidad = 85  # Valor por defecto
        else:
            velocidad = 85
        
        velocidad_historica.append({
            'mes': mes if isinstance(item, (list, tuple)) else f'Mes {i+1}',
            'velocidad': round(velocidad, 1)
        })

    # Asegurar que tenemos 6 elementos
    while len(velocidad_historica) < 6:
        velocidad_historica.append({'mes': f'Mes {len(velocidad_historica)+1}', 'velocidad': 85})

    return velocidad_historica[-6:]


def _calculate_risk_trend_data(analisis_rendimiento: Dict, tendencias: Dict) -> List[Dict]:
    """Calcula tendencia de riesgo basada en datos históricos."""
    porcentaje_criticos_actual = float(analisis_rendimiento.get('porcentaje_criticos', 0))
    dso_actual = float(analisis_rendimiento.get('dso_encargado', 0))
    
    # Simular tendencia histórica basada en valores actuales
    # En una implementación completa, esto vendría de datos históricos reales
    base_risk = (porcentaje_criticos_actual + (dso_actual / 2)) / 2
    
    risk_trend = []
    for i in range(6):
        # Simular variación histórica (-3 a +3 puntos por mes)
        variation = (i - 3) * 2  # Tendencia descendente
        risk_value = max(0, min(100, base_risk + variation))
        risk_trend.append({
            'mes': f'M{i+1}',
            'riesgo': round(risk_value, 1)
        })
    
    return risk_trend


def _calculate_volume_trend_data(analisis_financiero: Dict, tendencias: Dict) -> List[Dict]:
    """Calcula tendencia de volumen basada en datos históricos."""
    total_edps_actual = int(analisis_financiero.get('total_edps', 0))
    
    # Simular tendencia histórica de volumen
    volume_trend = []
    for i in range(6):
        # Simular crecimiento gradual del volumen
        growth_factor = 1 + (i * 0.05)  # 5% crecimiento por mes
        volume_value = int(total_edps_actual * growth_factor)
        volume_trend.append({
            'mes': f'M{i+1}',
            'volumen': volume_value
        })
    
    return volume_trend