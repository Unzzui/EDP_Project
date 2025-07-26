# 🗄️ Scripts de Reset de Base de Datos - EDP Project

## 📋 Descripción

Scripts para hacer un reset completo de todos los datos de la base de datos excepto los usuarios. Estos scripts eliminan todos los datos de EDP, proyectos, costos, logs, etc., pero preservan la tabla de usuarios y sus datos de autenticación.

## 🚨 ADVERTENCIA IMPORTANTE

**⚠️ ESTOS SCRIPTS ELIMINAN TODOS LOS DATOS DE LA BASE DE DATOS EXCEPTO USUARIOS**

- ✅ **Se preservan**: Tabla de usuarios, datos de autenticación, configuraciones del sistema
- ❌ **Se eliminan**: Todos los datos de EDP, proyectos, costos, logs, issues, etc.

## 📁 Scripts Disponibles

### 1. `reset_database.py` - Script Completo con Confirmación

**Características:**

- ✅ Confirmación del usuario antes de ejecutar
- ✅ Backup automático antes del reset
- ✅ Logging detallado
- ✅ Verificación post-reset
- ✅ Limpieza de cache Redis
- ✅ Soporte para SQLite y Supabase

**Uso:**

```bash
python reset_database.py
```

**Salida:**

```
🗄️ Script de Reset de Base de Datos - EDP Project
============================================================

⚠️  ADVERTENCIA: RESET DE BASE DE DATOS
============================================================
Este script eliminará TODOS los datos de:
  • EDP (proyectos)
  • Projects
  • Cost Header y Cost Lines
  • Logs
  • Caja
  • Issues
  • Historial de estados
  • Perfiles de clientes

✅ PERO PRESERVARÁ:
  • Tabla de usuarios
  • Datos de autenticación
  • Configuraciones del sistema

¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): SI

💾 Creando backup antes del reset...
🗄️ Ejecutando reset en SQLite...
🗄️ Ejecutando reset en Supabase...
🗑️ Limpiando cache...
🔍 Verificando reset...

✅ RESET COMPLETADO EXITOSAMENTE
============================================================
📋 Se han eliminado todos los datos de:
   • edp
   • projects
   • cost_header
   • cost_lines
   • logs
   • caja
   • edp_log
   • issues
   • edp_status_history
   • client_profiles

✅ Se han preservado:
   • Tabla de usuarios
   • Datos de autenticación
   • Configuraciones del sistema

💾 Se ha creado un backup antes del reset
🗑️ Se ha limpiado el cache del sistema
============================================================
```

### 2. `quick_reset.py` - Script Rápido sin Confirmación

**Características:**

- ⚡ Ejecución rápida sin confirmaciones
- 🗑️ Reset directo de todas las tablas
- 🧹 Limpieza de cache
- 📝 Salida simple y directa

**Uso:**

```bash
python quick_reset.py
```

**Salida:**

```
🗄️ Reset rápido de base de datos...
🗄️ Reseteando SQLite: edp_mvp/instance/edp_database.db
   ✅ edp reseteada
   ✅ projects reseteada
   ✅ cost_header reseteada
   ✅ cost_lines reseteada
   📋 logs no existe
   📋 caja no existe
   ✅ edp_log reseteada
   ✅ issues reseteada
   📋 edp_status_history no existe
   📋 client_profiles no existe
✅ SQLite reseteado
🗄️ Reseteando Supabase...
   ✅ edp reseteada
   ✅ projects reseteada
   ✅ cost_header reseteada
   ✅ cost_lines reseteada
   📋 logs no existe o error
   📋 caja no existe o error
   ✅ edp_log reseteada
   ✅ issues reseteada
   📋 edp_status_history no existe o error
   📋 client_profiles no existe o error
✅ Supabase reseteado
🗑️ Cache limpiado: 15 claves
✅ Reset completado
```

## 🔧 Configuración Requerida

### Variables de Entorno

Los scripts leen las siguientes variables de entorno:

```bash
# Backend de datos (sqlite, supabase, o ambos)
DATA_BACKEND=supabase

# Configuración SQLite
SQLITE_DB_PATH=edp_mvp/instance/edp_database.db

# Configuración Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key

# Configuración Redis (opcional)
REDIS_URL=redis://localhost:6379/0
```

### Archivo .env

Crea un archivo `.env` en la raíz del proyecto:

```env
# Backend de datos
DATA_BACKEND=supabase

# SQLite
SQLITE_DB_PATH=edp_mvp/instance/edp_database.db

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0
```

## 📊 Tablas que se Resetean

Los scripts eliminan datos de las siguientes tablas:

| Tabla                | Descripción                    |
| -------------------- | ------------------------------ |
| `edp`                | Datos principales de EDP       |
| `projects`           | Información de proyectos       |
| `cost_header`        | Encabezados de costos          |
| `cost_lines`         | Líneas de detalle de costos    |
| `logs`               | Registro de actividades        |
| `caja`               | Movimientos de caja            |
| `edp_log`            | Log específico de EDP          |
| `issues`             | Problemas y incidencias        |
| `edp_status_history` | Historial de cambios de estado |
| `client_profiles`    | Perfiles de clientes           |

## 🔒 Tablas que se Preservan

| Tabla                    | Descripción                       |
| ------------------------ | --------------------------------- |
| `usuarios`               | Datos de usuarios y autenticación |
| `sqlite_sequence`        | Secuencias de auto-increment      |
| Otras tablas del sistema | Configuraciones y metadatos       |

## 📁 Archivos Generados

### Logs

- `reset_database.log` - Log detallado del proceso de reset

### Backups

- `backups/edp_database_backup_YYYYMMDD_HHMMSS.db` - Backup de SQLite
- `backups/supabase_backup_YYYYMMDD_HHMMSS.json` - Backup de Supabase

## 🚀 Casos de Uso

### 1. Reset Completo con Seguridad

```bash
# Usar el script completo con confirmación y backup
python reset_database.py
```

### 2. Reset Rápido para Desarrollo

```bash
# Usar el script rápido para limpiar datos de desarrollo
python quick_reset.py
```

### 3. Reset Solo SQLite

```bash
# Configurar solo SQLite
export DATA_BACKEND=sqlite
python reset_database.py
```

### 4. Reset Solo Supabase

```bash
# Configurar solo Supabase
export DATA_BACKEND=supabase
python reset_database.py
```

## 🔍 Verificación Post-Reset

### Verificar SQLite

```bash
sqlite3 edp_mvp/instance/edp_database.db
.tables
SELECT COUNT(*) FROM usuarios;  -- Debe tener usuarios
SELECT COUNT(*) FROM edp;       -- Debe estar vacía
SELECT COUNT(*) FROM projects;  -- Debe estar vacía
.quit
```

### Verificar Supabase

```bash
# Usar el SQL Editor de Supabase
SELECT COUNT(*) FROM usuarios;  -- Debe tener usuarios
SELECT COUNT(*) FROM edp;       -- Debe estar vacía
SELECT COUNT(*) FROM projects;  -- Debe estar vacía
```

## 🛠️ Solución de Problemas

### Error: "Base de datos no encontrada"

```bash
# Verificar que la ruta de SQLite sea correcta
ls -la edp_mvp/instance/edp_database.db
```

### Error: "Supabase no configurado"

```bash
# Verificar variables de entorno
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY
```

### Error: "No tienes permisos"

```bash
# Verificar que el script tenga permisos de ejecución
chmod +x reset_database.py
chmod +x quick_reset.py
```

### Error: "Redis no disponible"

```bash
# El script continuará sin limpiar cache
# Verificar configuración de Redis
echo $REDIS_URL
```

## 🔄 Restaurar desde Backup

### Restaurar SQLite

```bash
# Detener la aplicación
# Copiar el backup
cp backups/edp_database_backup_YYYYMMDD_HHMMSS.db edp_mvp/instance/edp_database.db
# Reiniciar la aplicación
```

### Restaurar Supabase

```bash
# Usar el archivo JSON de backup para restaurar datos
# Ejecutar las consultas INSERT en el SQL Editor de Supabase
```

## 📝 Notas Importantes

1. **Siempre hacer backup** antes de ejecutar un reset
2. **Verificar la configuración** de variables de entorno
3. **Detener la aplicación** antes de ejecutar el reset
4. **Revisar los logs** si hay errores
5. **Verificar el resultado** después del reset

## 🎯 Recomendaciones

- **Desarrollo**: Usar `quick_reset.py` para limpiar datos rápidamente
- **Producción**: Usar `reset_database.py` con confirmación y backup
- **Testing**: Verificar siempre que los usuarios se preserven
- **Backup**: Mantener copias de seguridad regulares

---

## 🎉 ¡Scripts Listos!

Con estos scripts puedes hacer un reset completo y seguro de tu base de datos, preservando siempre los datos de usuarios y autenticación.

¡Úsalos con responsabilidad! 🚀
