"""
Utilidades para conversión de tipos numpy/pandas para serialización JSON
Maneja específicamente el caso donde los montos deben ser float en lugar de int
"""

import numpy as np
import pandas as pd
from typing import Any


def convert_numpy_types_for_json(obj: Any) -> Any:
    """
    Convierte tipos numpy y pandas a tipos nativos de Python para serialización JSON.
    
    IMPORTANTE: Los campos monetarios (monto_propuesto, monto_aprobado) se convierten 
    específicamente a float para coincidir con el tipo 'numeric' de la base de datos.
    """
    # Manejar objetos DictToObject convirtiéndolos de vuelta a diccionarios
    if hasattr(obj, '__dict__') and obj.__class__.__name__ == 'DictToObject':
        # Convertir DictToObject de vuelta a diccionario
        dict_obj = {}
        for key, value in obj.__dict__.items():
            dict_obj[key] = convert_numpy_types_for_json(value)
        return dict_obj
    elif isinstance(obj, dict):
        converted = {}
        for key, value in obj.items():
            # Campos monetarios siempre como float
            if key in ['monto_propuesto', 'monto_aprobado'] and value is not None:
                if pd.isna(value):
                    converted[key] = None
                else:
                    try:
                        converted[key] = float(value)
                    except (ValueError, TypeError):
                        converted[key] = 0.0
            else:
                converted[key] = convert_numpy_types_for_json(value)
        return converted
    elif isinstance(obj, list):
        return [convert_numpy_types_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif hasattr(obj, 'item'):  # numpy scalars
        return obj.item()
    elif hasattr(obj, 'tolist'):  # numpy arrays
        return obj.tolist()
    elif pd.isna(obj):  # pandas NaT/NaN
        return None
    else:
        return obj


def convert_edp_updates_for_db(updates: dict) -> dict:
    """
    Convierte específicamente los updates de EDP para la base de datos.
    Asegura que los tipos coincidan con el esquema de la BD.
    """
    converted = {}
    
    for key, value in updates.items():
        if value is None or (isinstance(value, str) and value.strip() == ""):
            converted[key] = None
        elif key in ['monto_propuesto', 'monto_aprobado']:
            # Montos siempre como float (numeric en BD)
            if pd.isna(value):
                converted[key] = None
            else:
                try:
                    converted[key] = float(value)
                except (ValueError, TypeError):
                    converted[key] = 0.0
        elif key in ['n_edp', 'id', 'dias_en_cliente', 'dso_actual']:
            # IDs y contadores como int
            if pd.isna(value):
                converted[key] = None
            else:
                try:
                    converted[key] = int(value)
                except (ValueError, TypeError):
                    converted[key] = None
        elif key in ['conformidad_enviada', 'esta_vencido']:
            # Booleanos
            if pd.isna(value):
                converted[key] = None
            elif isinstance(value, str):
                converted[key] = value.lower() in ['sí', 'si', 'yes', 'true', '1']
            else:
                converted[key] = bool(value)
        elif key in ['fecha_emision', 'fecha_envio_cliente', 'fecha_estimada_pago', 
                     'fecha_conformidad', 'fecha_registro', 'fecha_ultimo_seguimiento',
                     'created_at', 'updated_at']:
            # Fechas
            if pd.isna(value) or value == "":
                converted[key] = None
            elif isinstance(value, pd.Timestamp):
                converted[key] = value.isoformat()
            elif isinstance(value, str):
                converted[key] = value
            else:
                converted[key] = str(value) if value else None
        else:
            # Strings y otros tipos
            if pd.isna(value):
                converted[key] = None
            elif hasattr(value, 'item'):  # numpy types
                converted[key] = value.item()
            else:
                converted[key] = value
    
    return converted


def safe_json_serialize(obj: Any) -> Any:
    """
    Función segura para serializar cualquier objeto a JSON.
    Maneja automáticamente tipos numpy/pandas.
    """
    try:
        import json
        return json.dumps(convert_numpy_types_for_json(obj))
    except TypeError as e:
        # Si aún falla, aplicar conversión más agresiva
        print(f"⚠️ Error en serialización JSON: {e}")
        print(f"⚠️ Aplicando conversión agresiva...")
        
        def aggressive_convert(obj):
            if isinstance(obj, dict):
                return {str(k): aggressive_convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [aggressive_convert(item) for item in obj]
            elif hasattr(obj, 'item'):
                return obj.item()
            elif hasattr(obj, '__dict__'):
                return str(obj)
            else:
                return str(obj)
        
        converted = aggressive_convert(obj)
        return json.dumps(converted)


def debug_object_types(obj: Any, path: str = "") -> None:
    """
    Función de depuración para mostrar todos los tipos en un objeto.
    Útil para encontrar tipos numpy problemáticos.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            debug_object_types(value, current_path)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            current_path = f"{path}[{i}]"
            debug_object_types(value, current_path)
    else:
        type_name = type(obj).__name__
        if 'numpy' in str(type(obj)) or 'pandas' in str(type(obj)):
            print(f"🚨 {path}: {obj} (tipo problemático: {type_name})")
        elif path:  # Solo mostrar tipos no básicos
            print(f"✅ {path}: {obj} (tipo: {type_name})") 