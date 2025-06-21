# 🔧 CORRECCIÓN: Error JSON Serialization con tipos int64
# 
# Este script corrige el problema "Object of type int64 is not JSON serializable"
# que ocurre cuando se actualizan EDPs desde el modal

import numpy as np
import pandas as pd
import json
from typing import Any, Dict

def convert_numpy_types_to_native(obj: Any) -> Any:
    """
    Convierte tipos de NumPy/Pandas a tipos nativos de Python
    para que sean serializables a JSON.
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types_to_native(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif hasattr(obj, 'item'):  # numpy scalars
        return obj.item()
    elif pd.isna(obj) or str(obj) == 'NaT':
        return None
    else:
        return obj

# PARCHE PARA LAS RUTAS DE DASHBOARD
def patch_dashboard_routes():
    """
    Aplica el parche a las rutas de dashboard que tienen problemas
    de serialización JSON.
    """
    
    # Contenido del parche para dashboard.py
    dashboard_patch = '''
# 🔧 PARCHE: Agregar conversión de tipos antes de JSON
def convert_edp_data_for_json(edp_data):
    """Convierte datos EDP para serialización JSON segura"""
    import numpy as np
    import pandas as pd
    
    converted = {}
    for key, value in edp_data.items():
        if pd.isna(value):
            converted[key] = None
        elif isinstance(value, (np.integer, np.int64, np.int32)):
            converted[key] = int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            if np.isnan(value):
                converted[key] = None
            else:
                converted[key] = float(value)
        elif isinstance(value, (np.bool_, np.bool8)):
            converted[key] = bool(value)
        elif isinstance(value, pd.Timestamp):
            converted[key] = value.isoformat()
        elif hasattr(value, 'item'):  # numpy scalars
            converted[key] = value.item()
        else:
            converted[key] = value
    
    return converted

# Aplicar en get_edp_data y get_edp_data_by_internal_id
'''
    
    print("📋 Parche para serialización JSON:")
    print("1. Agregar función convert_edp_data_for_json a dashboard.py")
    print("2. Usar en get_edp_data() antes de return jsonify(edp_data)")
    print("3. Usar en get_edp_data_by_internal_id() antes de return jsonify(edp_data)")
    
    return dashboard_patch

# PARCHE ESPECÍFICO PARA EL PROBLEMA
def create_fixed_get_edp_functions():
    """
    Crea las versiones corregidas de las funciones get_edp_data
    """
    
    fixed_get_edp_data = '''
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
'''

    fixed_get_edp_data_by_id = '''
@dashboard_bp.route("api/get-edp-by-id/<int:internal_id>", methods=["GET"])
@login_required
def get_edp_data_by_internal_id(internal_id):
    """API endpoint to get EDP data by internal ID."""
    try:
        df = controller_service.load_related_data()
        datos_relacionados = df.data
        df = pd.DataFrame(datos_relacionados.get("edps", []))
        edp = df[df["id"] == internal_id]

        if edp.empty:
            return jsonify({"error": f"EDP con ID {internal_id} no encontrado"}), 404

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
        print(f"❌ Error en get_edp_data_by_internal_id: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
'''
    
    return {
        'get_edp_data': fixed_get_edp_data,
        'get_edp_data_by_internal_id': fixed_get_edp_data_by_id
    }

if __name__ == "__main__":
    print("🔧 CORRECCIÓN PARA ERROR JSON SERIALIZATION")
    print("=" * 50)
    
    print("\n📋 PROBLEMA:")
    print("   ❌ Object of type int64 is not JSON serializable")
    print("   ❌ Ocurre al editar EDPs desde el modal")
    print("   ❌ Los datos de pandas contienen tipos numpy no serializables")
    
    print("\n🔧 SOLUCIÓN:")
    print("   ✅ Convertir tipos numpy a tipos nativos Python")
    print("   ✅ Aplicar conversión en get_edp_data() y get_edp_data_by_internal_id()")
    print("   ✅ Manejar valores NaN/NaT correctamente")
    
    print("\n📁 ARCHIVOS A MODIFICAR:")
    print("   • edp_mvp/app/routes/dashboard.py")
    print("     - Función get_edp_data()")
    print("     - Función get_edp_data_by_internal_id()")
    
    print("\n🚀 IMPLEMENTACIÓN:")
    print("   1. Agregar conversión de tipos antes de jsonify()")
    print("   2. Manejar tipos numpy específicamente")
    print("   3. Preservar formateo de fechas")
    
    print("\n" + "=" * 50)
    print("✅ Script de corrección creado exitosamente")
    print("💡 Aplica los cambios mostrados en dashboard.py") 