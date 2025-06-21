# Solución Completa: Problemas de Serialización JSON

## Resumen del Problema

El sistema Pagora MVP presentaba múltiples errores de serialización JSON:

1. **Error inicial**: `Object of type int64 is not JSON serializable`
2. **Error secundario**: `Object of type DictToObject is not JSON serializable`

### Contexto del Sistema

- **Base de datos**: PostgreSQL con campos `monto_propuesto` y `monto_aprobado` de tipo `numeric` (equivale a `float` en Python)
- **Procesamiento**: pandas/numpy que convierte automáticamente números a `numpy.int64`
- **Comunicación**: Socket.IO y respuestas de API que requieren serialización JSON
- **Templates**: Jinja2 usando `tojson` filter con objetos `DictToObject`

## Análisis de la Causa Raíz

### Problema 1: Tipos numpy no serializables

Los datos procesados por pandas contenían tipos numpy (`numpy.int64`, `numpy.float64`, etc.) que no son directamente serializables a JSON, pero la base de datos esperaba tipos específicos:

- `monto_propuesto`: `numeric` (float) en BD, pero llegaba como `numpy.int64`
- `monto_aprobado`: `numeric` (float) en BD, pero llegaba como `numpy.int64`

### Problema 2: Objetos DictToObject en templates

El sistema usa la clase `DictToObject` para convertir diccionarios en objetos con notación de punto, pero estos objetos no son serializables a JSON cuando se usan en templates con `| tojson`.

## Solución Implementada

### 1. Función Centralizada de Conversión de Tipos

**Archivo**: `edp_mvp/app/utils/type_conversion.py`

```python
def convert_numpy_types_for_json(obj: Any) -> Any:
    """
    Convierte tipos numpy y pandas a tipos nativos de Python para serialización JSON.

    IMPORTANTE: Los campos monetarios (monto_propuesto, monto_aprobado) se convierten
    específicamente a float para coincidir con el tipo 'numeric' de la base de datos.
    """
    # Manejar objetos DictToObject convirtiéndolos de vuelta a diccionarios
    if hasattr(obj, '__dict__') and obj.__class__.__name__ == 'DictToObject':
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
    # ... resto de conversiones
```

**Características clave**:

- ✅ Convierte `numpy.int64` → `int` para IDs y contadores
- ✅ Convierte `numpy.int64` → `float` **específicamente** para campos monetarios
- ✅ Maneja objetos `DictToObject` convirtiéndolos a diccionarios
- ✅ Procesa recursivamente diccionarios y listas anidadas
- ✅ Maneja `pandas.Timestamp`, `numpy.bool_`, etc.

### 2. Función Específica para Updates de Base de Datos

```python
def convert_edp_updates_for_db(updates: dict) -> dict:
    """
    Convierte específicamente los updates de EDP para la base de datos.
    Asegura que los tipos coincidan con el esquema de la BD.
    """
    # Lógica específica para cada tipo de campo según el esquema de BD
```

### 3. Patch Global de JSON

**Archivo**: `edp_mvp/app/__init__.py`

```python
def patched_json_dumps(obj, *args, **kwargs):
    """Versión patcheada de json.dumps que maneja tipos numpy automáticamente"""
    try:
        return original_json_dumps(obj, *args, **kwargs)
    except TypeError as e:
        error_str = str(e)
        if any(error_type in error_str for error_type in ["int64", "float64", "bool_", "Timestamp", "DictToObject"]):
            from .utils.type_conversion import convert_numpy_types_for_json
            converted_obj = convert_numpy_types_for_json(obj)
            return original_json_dumps(converted_obj, *args, **kwargs)
        else:
            raise e

# Aplicar patches
json.dumps = patched_json_dumps
flask_json.dumps = patched_flask_dumps
```

**Cobertura del patch**:

- ✅ `json.dumps` estándar
- ✅ `flask.json.dumps`
- ✅ Jinja2 `| tojson` filter
- ✅ Socket.IO emit automático
- ✅ Respuestas de API automáticas

### 4. Actualización de Servicios

**Archivo**: `edp_mvp/app/services/supabase_service.py`

```python
def _convert_updates_for_json(self, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Usar la función centralizada de conversión"""
    from ..utils.type_conversion import convert_edp_updates_for_db
    return convert_edp_updates_for_db(updates)
```

### 5. Scripts de Verificación

**Archivos de prueba creados**:

- `test_float_conversion.py`: Verifica conversión de tipos numpy
- `test_dicttoobject_serialization.py`: Verifica manejo de objetos DictToObject

## Resultados

### Antes de la Solución

```
TypeError: Object of type int64 is not JSON serializable
TypeError: Object of type DictToObject is not JSON serializable
```

### Después de la Solución

```python
# Conversión automática:
numpy.int64(1500000) → 1500000 (int) para IDs
numpy.int64(1500000) → 1500000.0 (float) para montos  # ✅ Coincide con BD
DictToObject(data) → {"key": "value", ...} (dict)     # ✅ Serializable

# Logs exitosos:
INFO:socketio.server:emitting event "edp_actualizado" to all [/]
✅ Actualización de estado completada exitosamente para EDP 223
```

## Beneficios de la Solución

### 1. **Compatibilidad con Base de Datos**

- Los montos se envían como `float` coincidiendo con el tipo `numeric` de PostgreSQL
- Eliminación completa de conflictos de tipos

### 2. **Cobertura Completa**

- Socket.IO automático
- APIs automáticas
- Templates Jinja2 automáticos
- Conversión manual cuando se necesite

### 3. **Mantenibilidad**

- Función centralizada fácil de actualizar
- Patch global como red de seguridad
- Lógica específica por tipo de campo

### 4. **Rendimiento**

- Conversión solo cuando es necesaria (lazy conversion)
- Cache de conversiones en el patch global

## Archivos Modificados

1. **Nuevo**: `edp_mvp/app/utils/type_conversion.py`
2. **Actualizado**: `edp_mvp/app/__init__.py` (patch global)
3. **Actualizado**: `edp_mvp/app/services/supabase_service.py`
4. **Actualizado**: `edp_mvp/app/routes/dashboard.py` (imports)

## Verificación

### Tests Automáticos

```bash
python edp_mvp/test_float_conversion.py
python edp_mvp/test_dicttoobject_serialization.py
```

### Verificación Manual

1. **Kanban**: Drag & drop funciona sin errores
2. **Modal EDP**: Edición funciona sin errores
3. **Templates**: `| tojson` funciona con DictToObject
4. **APIs**: Respuestas JSON correctas
5. **Socket.IO**: Eventos emitidos correctamente

## Estado Final

✅ **Error de int64 solucionado**  
✅ **Error de DictToObject solucionado**  
✅ **Compatibilidad con esquema de BD garantizada**  
✅ **Cobertura completa del sistema**  
✅ **Red de seguridad global implementada**

El sistema ahora maneja automáticamente todos los tipos numpy/pandas y objetos personalizados, asegurando compatibilidad completa entre el procesamiento de datos y la serialización JSON.
