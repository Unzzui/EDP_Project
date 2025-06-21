"""
Adaptador de compatibilidad para migrar de Google Sheets a Supabase
Mantiene las mismas funciones que gsheet.py pero usando Supabase como backend
"""

import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
import re
import traceback
from time import time
import json
import numpy as np

# Importar el nuevo servicio de Supabase
from ..services.supabase_service import get_supabase_service, get_supabase_async_service

# Importar Flask-Login para obtener el usuario actual
try:
    from flask_login import current_user
    from flask import has_request_context
    HAS_FLASK_LOGIN = True
except ImportError:
    current_user = None
    has_request_context = None
    HAS_FLASK_LOGIN = False

# Constantes para compatibilidad
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Cache global para compatibilidad con el sistema anterior
_range_cache = {}

# Cache para evitar entradas duplicadas en logs
_recent_log_entries = {}

logger = logging.getLogger(__name__)

def clear_all_cache():
    """Limpia el cache de Supabase (equivalente a clear_all_cache de gsheet.py)"""
    global _range_cache
    try:
        service = get_supabase_service()
        service.clear_all_cache()
        _range_cache.clear()  # Also clear the compatibility cache
        print("🧹 Cache de Supabase limpiado")
    except Exception as e:
        print(f"⚠️ Error limpiando cache de Supabase: {e}")

def get_service():
    """
    Obtener servicio de Supabase (equivalente a get_service de gsheet.py).
    Para compatibilidad, retorna el servicio de Supabase.
    """
    return get_supabase_service()

def read_sheet(range_name: str, apply_transformations: bool = True) -> pd.DataFrame:
    """
    Lee datos de Supabase y los convierte en DataFrame de pandas.
    Reemplaza la función read_sheet original que leía de Google Sheets.
    
    Args:
        range_name (str): Rango/tabla a leer, ej: "edp!A1:Z", "cost_header!A1:Q", "projects!A1:I"
        apply_transformations (bool): Si se deben aplicar transformaciones específicas por tipo de tabla
    
    Returns:
        DataFrame: Datos solicitados
    """
    print(f"📊 Leyendo {range_name} desde Supabase...")
    
    try:
        service = get_supabase_service()
        
        # Convertir formato de Google Sheets a nombre de tabla
        table_name = _extract_table_name(range_name)
        
        # Mapear nombres de hojas a tablas de Supabase
        table_mapping = {
            'edp': 'edp',
            'projects': 'projects', 
            'cost_header': 'cost_header',
            'cost_lines': 'cost_lines',
            'log': 'edp_log',
            'logs': 'edp_log',
            'caja': 'caja'
        }
        
        supabase_table = table_mapping.get(table_name, table_name)
        
        # Obtener datos desde Supabase
        df = service.to_dataframe(supabase_table)
        
        if apply_transformations:
            df = _apply_transformations(df, table_name)
        
        print(f"✅ Obtenidos {len(df)} registros de {supabase_table}")
        return df
        
    except Exception as e:
        print(f"❌ Error leyendo {range_name} desde Supabase: {e}")
        print(f"🔍 Detalle del error: {traceback.format_exc()}")
        
        # Intentar datos demo si falla
        try:
            table_name = _extract_table_name(range_name)
            if table_name == 'edp':
                from ..utils.demo_data import get_demo_edp_data
                demo_df = get_demo_edp_data()
                if not demo_df.empty:
                    print(f"✅ Usando datos demo de EDP para {range_name}")
                    return demo_df
            elif table_name in ['log', 'logs']:
                from ..utils.demo_data import get_demo_logs_data
                demo_df = get_demo_logs_data()
                if not demo_df.empty:
                    print(f"✅ Usando datos demo de logs para {range_name}")
                    return demo_df
        except Exception as demo_error:
            print(f"❌ Error generando datos demo: {demo_error}")
        
        print(f"💥 No hay datos disponibles para {range_name}, retornando DataFrame vacío")
        return pd.DataFrame()

def batch_read_sheets(range_names: List[str], apply_transformations: bool = True) -> Dict[str, pd.DataFrame]:
    """Leer múltiples rangos/tablas de forma eficiente desde Supabase"""
    print(f"📊 Leyendo {len(range_names)} tablas desde Supabase...")
    
    dfs = {}
    service = get_supabase_service()
    
    for range_name in range_names:
        try:
            df = read_sheet(range_name, apply_transformations)
            dfs[range_name] = df
        except Exception as e:
            print(f"❌ Error leyendo {range_name}: {e}")
            dfs[range_name] = pd.DataFrame()
    
    return dfs

def append_row(row_values: List[Any], sheet_name: str = "edp") -> bool:
    """
    Inserta una fila en la tabla especificada de Supabase.
    Reemplaza la función append_row original de Google Sheets.
    """
    try:
        service = get_supabase_service()
        
        # Mapear nombre de hoja a tabla
        table_mapping = {
            'edp': 'edp',
            'projects': 'projects',
            'cost_header': 'cost_header', 
            'cost_lines': 'cost_lines',
            'log': 'edp_log',
            'logs': 'edp_log'
        }
        
        table_name = table_mapping.get(sheet_name, sheet_name)
        
        # Obtener esquema de la tabla para mapear valores
        sample_data = service.select(table_name, limit=1)
        if not sample_data:
            print(f"❌ No se pudo obtener esquema de {table_name}")
            return False
        
        columns = list(sample_data[0].keys())
        
        # Crear diccionario de datos
        data = {}
        for i, value in enumerate(row_values):
            if i < len(columns):
                column = columns[i]
                # Omitir columnas auto-generadas
                if column not in ['id', 'created_at', 'updated_at']:
                    data[column] = value if value != '' else None
        
        # Agregar timestamps
        if 'created_at' in columns:
            data['created_at'] = datetime.now().isoformat()
        if 'updated_at' in columns:
            data['updated_at'] = datetime.now().isoformat()
        
        # Insertar registro
        result = service.insert(table_name, data)
        
        print(f"✅ Fila insertada en {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error insertando fila en {sheet_name}: {e}")
        return False

def update_row(row_number: int, updates: Dict[str, Any], sheet_name: str = "edp", 
               usuario: str = None, force_update: bool = False) -> bool:
    """
    Actualiza un registro específico en Supabase.
    Reemplaza la función update_row original de Google Sheets.
    """
    try:
        service = get_supabase_service()
        
        # Mapear nombre de hoja a tabla
        table_mapping = {
            'edp': 'edp',
            'projects': 'projects',
            'cost_header': 'cost_header',
            'cost_lines': 'cost_lines',
            'log': 'logs',
            'logs': 'logs'
        }
        
        table_name = table_mapping.get(sheet_name, sheet_name)
        
        # En Supabase usamos ID en lugar de número de fila
        # Asumimos que row_number corresponde al ID del registro
        record_id = row_number
        
        # Obtener registro actual para comparación
        current_record = service.select(table_name, {"id": record_id})
        if not current_record:
            print(f"❌ Registro {record_id} no encontrado en {table_name}")
            return False
        
        current_data = current_record[0]
        
        # Preparar actualizaciones
        update_data = {}
        cambios_reales = []
        
        for column, new_value in updates.items():
            # Convertir nombre de columna si es necesario
            db_column = _map_column_name(column)
            
            old_value = current_data.get(db_column)
            
            # Convertir tipos para serialización JSON
            new_value_converted = _convert_for_json_serialization(new_value)
            old_value_converted = _convert_for_json_serialization(old_value)
            
            # Conversiones específicas para campos EDP
            if db_column == 'conformidad_enviada' and isinstance(new_value_converted, str):
                new_value_converted = new_value_converted.lower() in ['sí', 'si', 'yes', 'true', '1']
            
            # Comparar valores
            if old_value_converted != new_value_converted or force_update:
                update_data[db_column] = new_value_converted
                cambios_reales.append({
                    'campo': db_column,
                    'valor_anterior': old_value_converted,
                    'valor_nuevo': new_value_converted
                })
        
        if not update_data and not force_update:
            print(f"🔍 No hay cambios reales para actualizar en {table_name}")
            return True
        
        # Agregar timestamp de actualización
        update_data['updated_at'] = datetime.now().isoformat()
        if usuario:
            update_data['last_modified_by'] = usuario
        
        # Realizar actualización
        result = service.update(table_name, {"id": record_id}, update_data)
        
        # Registrar en log si hay cambios (opcional - no bloquear si falla)
        if cambios_reales and table_name == 'edp':
            try:
                log_message = f"EDP {record_id} actualizado por {usuario or 'sistema'}"
                service.create_log({
                    "edp_id": str(record_id),
                    "log_type": "update",
                    "message": log_message,
                    "user": usuario or "sistema",
                    "details": json.dumps(cambios_reales)
                })
            except Exception as log_error:
                print(f"⚠️ No se pudo registrar log para EDP {record_id}: {log_error}")
                # Continuar sin bloquear la actualización
        
        print(f"✅ Registro {record_id} actualizado en {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando registro en {sheet_name}: {e}")
        return False

def append_edp(edp_data: Dict[str, Any]) -> int:
    """
    Inserta un nuevo EDP en Supabase.
    Reemplaza la función append_edp original.
    """
    try:
        service = get_supabase_service()
        
        # Crear el EDP
        result = service.create_edp(edp_data)
        
        # Obtener el ID del nuevo registro
        edp_id = result.get('id')
        print(f"✅ EDP creado con ID: {edp_id}")
        
        return edp_id
        
    except Exception as e:
        print(f"❌ Error creando EDP: {e}")
        return None

def update_edp_by_id(edp_id: int, updates: Dict[str, Any], usuario: str = None) -> bool:
    """
    Actualiza un EDP específico por ID.
    Reemplaza la función update_edp_by_id original.
    """
    try:
        print(f"🔍 update_edp_by_id - ID: {edp_id}, Updates: {updates}, Usuario: {usuario}")
        
        service = get_supabase_service()
        
        # Verificar que el EDP existe antes de actualizar
        existing_edp = service.get_edp_by_id(edp_id)
        if not existing_edp:
            print(f"❌ EDP {edp_id} no encontrado en la base de datos")
            return False
        
        print(f"✅ EDP {edp_id} encontrado, procediendo con actualización...")
        
        result = service.update_edp(edp_id, updates, usuario)
        print(f"🔍 Resultado de actualización: {result}")
        
        if result:
            print(f"✅ EDP {edp_id} actualizado exitosamente")
            return True
        else:
            print(f"❌ No se pudo actualizar EDP {edp_id} - resultado vacío")
            return False
        
    except Exception as e:
        import traceback
        print(f"❌ Error actualizando EDP {edp_id}: {e}")
        print(f"❌ Traceback completo:")
        print(traceback.format_exc())
        return False

def append_project(project_data: Dict[str, Any], sheet_name: str = "projects") -> int:
    """
    Inserta un nuevo proyecto en Supabase.
    Reemplaza la función append_project original.
    """
    try:
        service = get_supabase_service()
        
        result = service.create_project(project_data)
        project_id = result.get('id')
        
        print(f"✅ Proyecto creado con ID: {project_id}")
        return project_id
        
    except Exception as e:
        print(f"❌ Error creando proyecto: {e}")
        return None

def _extract_table_name(range_name: str) -> str:
    """Extraer nombre de tabla desde formato de Google Sheets"""
    if '!' in range_name:
        return range_name.split('!')[0]
    return range_name

def _map_column_name(column_name: str) -> str:
    """Mapear nombres de columnas de Google Sheets a Supabase"""
    # Mapeo básico de nombres de columnas
    column_mapping = {
        'N° EDP': 'n_edp',
        'Nº EDP': 'n_edp', 
        'Cliente': 'cliente',
        'Proyecto': 'proyecto',
        'Gestor': 'gestor',
        'Jefe de Proyecto': 'jefe_proyecto',
        'Fecha Inicio': 'fecha_inicio',
        'Fecha Fin Prevista': 'fecha_fin_prevista',
        'Monto Contrato': 'monto_contrato',
        'Moneda': 'moneda',
        'Estado': 'estado',
        'Observaciones': 'observaciones'
    }
    
    return column_mapping.get(column_name, column_name.lower().replace(' ', '_'))

def _convert_for_json_serialization(value: Any) -> Any:
    """Convertir tipos de pandas a tipos nativos de Python para serialización JSON"""
    import numpy as np
    import pandas as pd
    
    if value is None:
        return None
    
    # Handle pandas/numpy types
    if isinstance(value, (np.integer, pd.Int64Dtype)):
        return int(value)
    elif isinstance(value, (np.floating, pd.Float64Dtype)):
        return float(value)
    elif isinstance(value, (np.bool_, pd.BooleanDtype)):
        return bool(value)
    elif isinstance(value, pd.Timestamp):
        return value.isoformat()
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif hasattr(value, 'item'):  # For numpy scalars
        return value.item()
    elif pd.isna(value):
        return None
    else:
        return value

def _apply_transformations(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Aplicar transformaciones específicas por tipo de tabla"""
    if df.empty:
        return df
    
    try:
        if table_name == 'edp':
            # Transformaciones específicas para EDP (migradas desde EDPRepository)
            import numpy as np
            
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
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

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
                    ).dt.days.fillna(0)
                else:
                    df["dias_espera"] = ((hoy - fecha_envio).dt.days).fillna(0)
            else:
                # Si no hay fecha_envio_cliente, poner 0 días de espera
                df["dias_espera"] = 0

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
                
                # Asegurar que dias_habiles no sea None
                if "dias_habiles" not in df.columns:
                    df["dias_habiles"] = 0
                else:
                    df["dias_habiles"] = df["dias_habiles"].fillna(0)

            # Calculate critical status (comentado - campo no existe en BD Supabase)
            # if "dias_espera" in df.columns and len(df) > 0:
            #     dias_espera_numeric = pd.to_numeric(df["dias_espera"], errors="coerce").fillna(0)
            #     estado_not_final = ~df["estado"].isin(["validado", "pagado"])
            #     df["critico"] = (dias_espera_numeric > 30) & estado_not_final
            # else:
            #     df["critico"] = False

            # Calculate validation status
            if (
                "estado" in df.columns
                and "conformidad_enviada" in df.columns
                and len(df) > 0
            ):
                df["validado"] = (df["estado"].isin(["validado", "pagado"])) & (
                    df["conformidad_enviada"] == "Sí"
                )
            else:
                df["validado"] = False
            
            # Ensure text fields are not None (convert None to empty string)
            text_fields = [
                "proyecto", "cliente", "gestor", "jefe_proyecto", "mes",
                "n_conformidad", "registrado_por", "motivo_no_aprobado", 
                "tipo_falla", "observaciones", "estado_detallado"
            ]
            for field in text_fields:
                if field in df.columns:
                    df[field] = df[field].fillna("")
        
        elif table_name == 'cost_header':
            # Transformaciones para encabezados de costos
            date_columns = ['fecha_factura', 'fecha_recepcion', 'fecha_vencimiento', 'fecha_pago']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            numeric_columns = ['importe_bruto', 'importe_neto']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        elif table_name == 'projects':
            # Transformaciones para proyectos
            if 'fecha_inicio' in df.columns:
                df['fecha_inicio'] = pd.to_datetime(df['fecha_inicio'], errors='coerce')
            if 'fecha_fin_prevista' in df.columns:
                df['fecha_fin_prevista'] = pd.to_datetime(df['fecha_fin_prevista'], errors='coerce')
            if 'monto_contrato' in df.columns:
                df['monto_contrato'] = pd.to_numeric(df['monto_contrato'], errors='coerce')
        
        elif table_name in ['log', 'logs']:
            # Transformaciones para logs
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
    except Exception as e:
        print(f"⚠️ Error aplicando transformaciones a {table_name}: {e}")
        import traceback
        print(traceback.format_exc())
        # Return the original DataFrame if transformations fail
    
    return df

# === FUNCIONES DE UTILIDAD ===

def idx_to_a1(idx: int) -> str:
    """Convertir índice de columna a notación A1 (para compatibilidad)"""
    # Esta función no es necesaria para Supabase, pero se mantiene para compatibilidad
    result = ""
    while idx >= 0:
        result = chr(65 + (idx % 26)) + result
        idx = idx // 26 - 1
    return result

def format_currency(value: Any, currency: str = "CLP") -> str:
    """Formatear valores monetarios"""
    try:
        if pd.isna(value) or value == '':
            return ''
        
        num_value = float(value)
        if currency == "CLP":
            return f"${num_value:,.0f}"
        else:
            return f"{currency} {num_value:,.2f}"
    except:
        return str(value)

def clean_numeric_value(value: Any) -> Optional[float]:
    """Limpiar y convertir valores numéricos"""
    if value is None or value == '':
        return None
    
    try:
        if isinstance(value, str):
            # Limpiar formato de moneda
            cleaned = value.replace('$', '').replace(',', '').replace('.', '').strip()
            return float(cleaned)
        return float(value)
    except:
        return None

def clean_date_value(value: Any) -> Optional[str]:
    """Limpiar y normalizar valores de fecha"""
    if value is None or value == '':
        return None
    
    try:
        if isinstance(value, str):
            # Intentar parsear fecha
            parsed_date = pd.to_datetime(value, errors='coerce')
            if not pd.isna(parsed_date):
                return parsed_date.isoformat()[:10]  # Solo fecha YYYY-MM-DD
        elif hasattr(value, 'isoformat'):
            return value.isoformat()[:10]
    except:
        pass
    
    return str(value) if value else None

# === COMPATIBILIDAD CON CÓDIGO EXISTENTE ===

# Aliases para mantener compatibilidad con código existente
read_range = read_sheet
batch_read_ranges = batch_read_sheets 

# === FUNCIONES ADICIONALES MIGRADAS ===

# Cache para evitar entradas duplicadas en el log (como en Google Sheets)
_recent_log_entries = {}

def normalizar_valor_log(valor: Any) -> str:
    """Normalizar valores para el log (función auxiliar)"""
    if valor is None or valor == '':
        return ''
    
    if isinstance(valor, (int, float)):
        return str(valor)
    
    if isinstance(valor, str):
        # Limpiar espacios y convertir a minúsculas para comparación
        return valor.strip()
    
    return str(valor)

def log_cambio_edp(n_edp: str, proyecto: str, campo: str, antes: str, despues: str, usuario: str = None) -> bool:
    """
    Registra un cambio en la tabla logs de Supabase.
    Equivalente a log_cambio_edp de Google Sheets.
    
    Args:
        n_edp (str): Número de EDP
        proyecto (str): Nombre del proyecto  
        campo (str): Campo que cambió
        antes (str): Valor anterior
        despues (str): Valor nuevo
        usuario (str): Usuario que hizo el cambio
    
    Returns:
        bool: True si se registró exitosamente
    """
    try:
        service = get_supabase_service()
        
        # Obtener el usuario real si no se especifica
        if usuario is None:
            try:
                # Verificar si estamos en un contexto de request de Flask y Flask-Login está disponible
                if HAS_FLASK_LOGIN and has_request_context and has_request_context() and current_user and current_user.is_authenticated:
                    # Intentar obtener el nombre completo, email o username del usuario
                    if hasattr(current_user, 'nombre_completo') and current_user.nombre_completo:
                        usuario = current_user.nombre_completo
                    elif hasattr(current_user, 'email') and current_user.email:
                        usuario = current_user.email
                    elif hasattr(current_user, 'username') and current_user.username:
                        usuario = current_user.username
                    else:
                        usuario = f"Usuario ID: {current_user.id}"
                else:
                    usuario = "Sistema"
            except Exception as e:
                print(f"Error obteniendo usuario actual: {e}")
                usuario = "Sistema"
        
        # Normalizar valores para el log
        antes_normalizado = normalizar_valor_log(antes)
        despues_normalizado = normalizar_valor_log(despues)
        
        # No registrar si son iguales después de normalizar
        if antes_normalizado == despues_normalizado:
            return True
            
        # Convert n_edp to string first for deduplication
        n_edp_str = str(n_edp)
            
        # DEDUPLICACIÓN con proyecto incluido en la clave
        entry_key = f"{n_edp_str}:{proyecto}:{campo}:{antes_normalizado}:{despues_normalizado}"
        
        # Verificar si hemos registrado este cambio recientemente (últimos 30 segundos)
        current_time = datetime.now()
        if entry_key in _recent_log_entries:
            last_time = _recent_log_entries[entry_key]
            if (current_time - last_time).total_seconds() < 30:
                # Ya registramos este mismo cambio hace menos de 30 segundos, no duplicar
                return True
        
        # Actualizar el caché de entradas recientes
        _recent_log_entries[entry_key] = current_time
        
        # Limpiar entradas antiguas del caché (más de 5 minutos)
        for k in list(_recent_log_entries.keys()):
            if (current_time - _recent_log_entries[k]).total_seconds() > 300:
                del _recent_log_entries[k]
        
        # Crear entrada de log usando la estructura de la tabla edp_log
        # n_edp_str ya está definido arriba
        log_data = {
            "fecha_hora": current_time.isoformat(),
            "n_edp": int(n_edp_str) if n_edp_str.isdigit() else None,
            "edp_id": int(n_edp_str) if n_edp_str.isdigit() else None,
            "proyecto": proyecto,
            "campo": campo,
            "antes": antes_normalizado,
            "despues": despues_normalizado,
            "usuario": usuario
        }
        
        # Insertar en Supabase (intentar diferentes tablas si es necesario)
        try:
            service.insert('edp_log', log_data)
        except Exception as table_error:
            print(f"⚠️ Tabla edp_log no disponible, intentando con logs: {table_error}")
            try:
                service.insert('logs', log_data)
            except Exception as logs_error:
                print(f"⚠️ Tabla logs tampoco disponible: {logs_error}")
                print(f"⚠️ Log no registrado - continuando operación")
                return True  # No fallar la operación principal por un problema de logging
        
        print(f"✅ Log registrado: EDP {n_edp} - {campo}")
        return True
        
    except Exception as e:
        print(f"⚠️ Error registrando log para EDP {n_edp} (no crítico): {e}")
        return True  # No fallar la operación principal por problemas de logging

def read_log(n_edp: str = None, proyecto: str = None, usuario: str = None, range_name: str = "log!A1:G") -> pd.DataFrame:
    """
    Lee el historial de cambios desde Supabase.
    Equivalente a read_log de Google Sheets.
    
    Args:
        n_edp (str, optional): Filtrar por número de EDP
        proyecto (str, optional): Filtrar por proyecto 
        usuario (str, optional): Filtrar por usuario
        range_name (str): Parámetro para compatibilidad, no se usa en Supabase
    
    Returns:
        DataFrame: Historial de cambios filtrado
    """
    try:
        service = get_supabase_service()
        
        # Construir filtros para Supabase
        filters = {}
        if n_edp:
            n_edp_str = str(n_edp)
            filters["n_edp"] = int(n_edp_str) if n_edp_str.isdigit() else n_edp
        
        # Obtener datos de logs
        logs_data = service.select('edp_log', filters, limit=1000)  # Límite ajustable
        
        if not logs_data:
            # Devolver DataFrame vacío con columnas esperadas
            return pd.DataFrame(columns=['fecha_hora', 'n_edp', 'proyecto', 'campo', 'antes', 'despues', 'usuario'])
        
        # Convertir a DataFrame compatible (la tabla edp_log ya tiene la estructura correcta)
        processed_logs = []
        for log in logs_data:
            try:
                processed_logs.append({
                    'fecha_hora': log.get('fecha_hora'),
                    'n_edp': str(log.get('n_edp', '')),
                    'proyecto': log.get('proyecto', ''),
                    'campo': log.get('campo', ''),
                    'antes': log.get('antes', ''),
                    'despues': log.get('despues', ''),
                    'usuario': log.get('usuario', '')
                })
            except Exception as e:
                print(f"⚠️ Error procesando log: {e}")
                continue
        
        df = pd.DataFrame(processed_logs)
        
        if df.empty:
            return pd.DataFrame(columns=['fecha_hora', 'n_edp', 'proyecto', 'campo', 'antes', 'despues', 'usuario'])
        
        # Convertir fecha-hora
        if "fecha_hora" in df.columns:
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
        
        # Aplicar filtros adicionales
        if proyecto:
            df = df[df["proyecto"] == str(proyecto)]
        if usuario:
            df = df[df["usuario"].str.lower() == usuario.lower()]
        
        # Orden descendente por fecha
        if "fecha_hora" in df.columns:
            df = df.sort_values("fecha_hora", ascending=False)
        
        print(f"📊 Obtenidos {len(df)} registros de log")
        return df
        
    except Exception as e:
        print(f"❌ Error leyendo logs: {e}")
        return pd.DataFrame(columns=['fecha_hora', 'n_edp', 'proyecto', 'campo', 'antes', 'despues', 'usuario'])

def read_cost_header(filtros: Dict = None) -> pd.DataFrame:
    """
    Lee la tabla cost_header con filtros opcionales.
    Equivalente a read_cost_header de Google Sheets.
    
    Args:
        filtros (dict, optional): Filtros como:
            - project_id: ID del proyecto
            - estado_costo: Estado del costo
            - proveedor: Nombre del proveedor
            - vencidos_only: True para solo vencidos
            
    Returns:
        DataFrame: Costos que cumplen los filtros
    """
    try:
        service = get_supabase_service()
        
        # Construir filtros para Supabase
        supabase_filters = {}
        if filtros:
            if 'project_id' in filtros and filtros['project_id']:
                supabase_filters['project_id'] = filtros['project_id']
            if 'estado_costo' in filtros and filtros['estado_costo']:
                supabase_filters['estado_costo'] = filtros['estado_costo'].lower()
        
        # Obtener datos
        df = service.to_dataframe('cost_header', supabase_filters)
        
        if df.empty:
            return pd.DataFrame()
        
        # Aplicar filtros adicionales que requieren operaciones complejas
        if filtros:
            if 'proveedor' in filtros and filtros['proveedor']:
                df = df[df['proveedor'].str.contains(filtros['proveedor'], case=False, na=False)]
            
            # Para vencidos, necesitamos calcular estado_vencimiento
            if 'vencidos_only' in filtros and filtros['vencidos_only']:
                # Calcular vencimientos si la columna no existe
                if 'fecha_vencimiento' in df.columns:
                    today = pd.Timestamp.now().normalize()
                    df['estado_vencimiento'] = df['fecha_vencimiento'].apply(
                        lambda x: 'vencido' if pd.notna(x) and pd.to_datetime(x) < today else 'vigente'
                    )
                    df = df[df['estado_vencimiento'] == 'vencido']
        
        return df
        
    except Exception as e:
        print(f"❌ Error leyendo cost_header: {e}")
        return pd.DataFrame()

def read_projects(filtros: Dict = None) -> pd.DataFrame:
    """
    Lee la tabla projects con filtros opcionales.
    Equivalente a read_projects de Google Sheets.
    
    Args:
        filtros (dict, optional): Filtros como:
            - cliente: Nombre del cliente
            - jefe_proyecto: Jefe de proyecto
            - estado_proyecto: Estado del proyecto
            - activos_only: True para solo proyectos activos
            
    Returns:
        DataFrame: Proyectos que cumplen los filtros
    """
    try:
        service = get_supabase_service()
        
        # Construir filtros para Supabase
        supabase_filters = {}
        if filtros:
            if 'jefe_proyecto' in filtros and filtros['jefe_proyecto']:
                supabase_filters['jefe_proyecto'] = filtros['jefe_proyecto']
            if 'estado_proyecto' in filtros and filtros['estado_proyecto']:
                supabase_filters['estado_proyecto'] = filtros['estado_proyecto']
        
        # Obtener datos
        df = service.to_dataframe('projects', supabase_filters)
        
        if df.empty:
            return pd.DataFrame()
        
        # Aplicar filtros adicionales
        if filtros:
            if 'cliente' in filtros and filtros['cliente']:
                df = df[df['cliente'].str.contains(filtros['cliente'], case=False, na=False)]
            if 'activos_only' in filtros and filtros['activos_only']:
                df = df[df['estado_proyecto'].isin(['en_curso', 'no_iniciado'])]
        
        return df
        
    except Exception as e:
        print(f"❌ Error leyendo projects: {e}")
        return pd.DataFrame()

def append_cost(cost_data: Dict[str, Any], sheet_name: str = "cost_header") -> Optional[int]:
    """
    Inserta un nuevo registro de costo en Supabase.
    Equivalente a append_cost de Google Sheets.
    
    Args:
        cost_data (dict): Datos del costo con las columnas requeridas
        sheet_name (str): Nombre de la tabla (para compatibilidad)
    
    Returns:
        int: ID del nuevo registro o None si falló
    """
    try:
        service = get_supabase_service()
        
        # Crear el registro de costo
        result = service.create_cost_header(cost_data)
        cost_id = result.get('cost_id')
        
        print(f"✅ Costo creado con ID: {cost_id}")
        return cost_id
        
    except Exception as e:
        print(f"❌ Error creando costo: {e}")
        return None

def son_diferentes(v1: Any, v2: Any) -> bool:
    """Función auxiliar para comparar valores (para compatibilidad)"""
    # Normalizar valores
    val1 = normalizar_valor_log(v1)
    val2 = normalizar_valor_log(v2)
    
    # Comparar strings normalizados
    return val1 != val2

def generate_unique_id() -> str:
    """Generar ID único para compatibilidad"""
    return f"id_{int(datetime.now().timestamp() * 1000)}"

def validar_transicion(estado_actual: str, nuevo_estado: str) -> bool:
    """Validar transición de estados (función auxiliar)"""
    # Implementación básica - puedes expandir según tus reglas de negocio
    transiciones_validas = {
        'no_iniciado': ['en_curso', 'cancelado'],
        'en_curso': ['completado', 'pausado', 'cancelado'],
        'pausado': ['en_curso', 'cancelado'],
        'completado': [],  # No se puede cambiar desde completado
        'cancelado': ['no_iniciado']  # Se puede reactivar
    }
    
    return nuevo_estado in transiciones_validas.get(estado_actual, [])

def validar_edp(edp_original: Dict, updates: Dict) -> Dict[str, Any]:
    """Validar actualizaciones de EDP (función auxiliar)"""
    errores = []
    
    # Validaciones básicas
    if 'estado' in updates:
        estado_actual = edp_original.get('estado', 'no_iniciado')
        nuevo_estado = updates['estado']
        
        if not validar_transicion(estado_actual, nuevo_estado):
            errores.append(f"Transición de estado no válida: {estado_actual} → {nuevo_estado}")
    
    # Validar fechas
    if 'fecha_inicio' in updates and 'fecha_fin_prevista' in updates:
        try:
            fecha_inicio = pd.to_datetime(updates['fecha_inicio'])
            fecha_fin = pd.to_datetime(updates['fecha_fin_prevista'])
            
            if fecha_fin <= fecha_inicio:
                errores.append("La fecha de fin debe ser posterior a la fecha de inicio")
        except:
            errores.append("Formato de fecha inválido")
    
    return {
        'valido': len(errores) == 0,
        'errores': errores
    } 