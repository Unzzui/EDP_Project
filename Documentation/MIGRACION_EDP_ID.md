# 🚀 GUÍA COMPLETA: Migración con columna edp_id

## Resumen del problema

La tabla `edp_log` necesitaba una columna `edp_id` para relacionarse con la ID única de la tabla `edp` (no solo con `n_edp`).

## ✅ Cambios realizados

### 1. Estructura de Base de Datos

- **Archivo**: `update_edp_log_structure.sql`
- **Cambio**: Script para agregar columna `edp_id` a la tabla `edp_log`
- **Incluye**: Índice y constraint de clave foránea

### 2. Script de Migración

- **Archivo**: `migrate_google_sheets_to_supabase.py`
- **Cambios**:
  - Nuevo método `get_edp_id_mapping()` para obtener mapeo n_edp → id
  - Modificado `migrate_log_data()` para incluir `edp_id` en los registros
  - La migración ahora relaciona automáticamente los logs con los EDPs

### 3. Scripts de Ayuda

- **`verify_migration_prerequisites.py`**: Verifica que todo esté listo
- **`run_migration_step_by_step.sh`**: Guía paso a paso para la migración

## 📋 PASOS A SEGUIR

### Paso 1: Verificar prerequisitos

```bash
python3 verify_migration_prerequisites.py
```

### Paso 2: Actualizar estructura de tabla (si es necesario)

En el SQL Editor de Supabase, ejecuta:

```sql
-- Contenido de update_edp_log_structure.sql
ALTER TABLE edp_log ADD COLUMN IF NOT EXISTS edp_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_edp_log_edp_id ON edp_log(edp_id);
```

### Paso 3: Ejecutar migración

Opción A - Script guiado:

```bash
./run_migration_step_by_step.sh
```

Opción B - Directo:

```bash
python3 migrate_google_sheets_to_supabase.py
```

## 🔄 Orden de migración

1. **projects** (tablas de referencia)
2. **edp** (tabla principal)
3. **cost_header**
4. **edp_log** (ahora con `edp_id` automático)
5. **issues**

## ✅ Qué hace la nueva migración

- Migra `edp` primero para tener las IDs disponibles
- Obtiene mapeo de `n_edp` → `id` desde la tabla `edp`
- Al migrar `edp_log`, asigna automáticamente `edp_id` basado en `n_edp`
- Mantiene `n_edp` para compatibilidad y también agrega `edp_id` para relaciones

## 🔍 Verificación post-migración

```bash
python3 verify_supabase_migration.py
```

## 🎯 Resultado esperado

- Tabla `edp_log` con columna `edp_id` correctamente poblada
- Relación directa entre logs y EDPs usando ID único
- Mejor integridad referencial y performance en consultas

## ⚠️ Notas importantes

- Si ya hay datos en `edp_log`, la actualización SQL los relacionará automáticamente
- La migración maneja casos donde no hay coincidencia (`edp_id` será NULL)
- Se mantiene retrocompatibilidad con `n_edp`
