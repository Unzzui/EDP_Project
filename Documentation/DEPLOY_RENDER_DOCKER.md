# 🐳 Deploy en Render con Docker

## 📋 **RESUMEN DE CAMBIOS RECIENTES**

**✅ RESUELTO:** Problema con `su-exec` no disponible en Debian Bookworm

- Removido `su-exec` del Dockerfile
- Implementada estrategia simplificada de permisos compatible con Render
- Mejorado el entrypoint script para verificación de Secret Files
- Actualizada configuración de Gunicorn para mejor rendimiento en Render

## ⚠️ IMPORTANTE: Variables de Entorno

### El problema de "port" en DATABASE_URL

Si ves este error:

```
ValueError: invalid literal for int() with base 10: 'port'
```

Significa que `DATABASE_URL` tiene un placeholder en lugar de valores reales.

### ✅ **SOLUCIÓN: Configurar servicios en el ORDEN CORRECTO**

**1. Crear PostgreSQL Database PRIMERO:**

- Dashboard Render → New → PostgreSQL
- Name: `edp-database`
- Database Name: `edp_mvp_db`
- Plan: Starter
- **¡ESPERAR A QUE ESTÉ COMPLETAMENTE ACTIVO!**

**2. Crear Redis SEGUNDO:**

- Dashboard Render → New → Redis
- Name: `edp-redis`
- Plan: Starter
- **¡ESPERAR A QUE ESTÉ COMPLETAMENTE ACTIVO!**

**3. Crear Web Service ÚLTIMO:**

- Dashboard Render → New → Web Service
- Connect GitHub repo
- **Environment**: Docker
- **Dockerfile Path**: `./Dockerfile`

### 🔧 **Variables de entorno en Web Service:**

#### Configurar manualmente:

```bash
FLASK_ENV=production
SECRET_KEY=una-clave-muy-segura-de-32-caracteres-cambiar-esto
DEBUG=False
SHEET_ID=tu-google-sheet-id-aqui
```

#### 🔐 **Secret Files (para Google Sheets):**

1. **En el Web Service → Settings → Secret Files**
2. **Add Secret File**:
   - **Filename**: `edp-control-system-f3cfafc0093a.json`
   - **File Content**: Pegar el contenido del archivo JSON de credenciales
3. **Save Secret File**

**⚠️ IMPORTANTE**: El archivo estará disponible en `/etc/secrets/edp-control-system-f3cfafc0093a.json`

#### Conectar servicios:

1. **DATABASE_URL**:

   - Add Environment Variable
   - Key: `DATABASE_URL`
   - Value: "From Database" → Select `edp-database` → Connection String

2. **REDIS_URL**:
   - Add Environment Variable
   - Key: `REDIS_URL`
   - Value: "From Service" → Select `edp-redis` → Connection String

### 🔍 **Verificar en los logs:**

✅ **Logs correctos:**

```
✅ Usando PostgreSQL: postgresql://...
✅ Base de datos inicializada correctamente
✅ Redis conectado correctamente (o fallback a SQLite)
[INFO] Starting gunicorn
[INFO] Listening at: http://0.0.0.0:5000
```

❌ **Logs con errores:**

```
⚠️ DATABASE_URL parece tener placeholders: postgresql://user:password@host:port/db
ValueError: invalid literal for int() with base 10: 'port'
```

### 🚨 **Si sigue fallando:**

1. **Verifica que los servicios estén activos**:

   - PostgreSQL debe mostrar "Available"
   - Redis debe mostrar "Available"

2. **Rebuild del Web Service**:

   - En el dashboard del Web Service
   - Manual Deploy → Clear cache → Deploy

3. **Verifica las variables**:
   - Environment tab del Web Service
   - DATABASE_URL debe ser una URL real, no placeholder
   - REDIS_URL debe ser una URL real, no placeholder

### 🔄 **Si necesitas debug:**

Temporalmente agrega esta variable para ver más información:

```bash
DEBUG=True
```

Luego revisa los logs y vuelve a poner `DEBUG=False` cuando funcione.

## 📦 **El Docker build incluye:**

1. ✅ PostgreSQL driver (psycopg2-binary)
2. ✅ Gunicorn con threading
3. ✅ Inicialización automática de DB
4. ✅ Fallback a SQLite si PostgreSQL falla
5. ✅ Manejo robusto de errores
6. ✅ Usuario no-root para seguridad
7. ✅ Modo demo sin Google Sheets
8. ✅ Manejo de template errors

## 🎭 **Modo Demo (sin Google Sheets):**

Si no configuras Google Sheets, la aplicación funcionará con datos demo:

- ✅ 50 proyectos EDP de ejemplo
- ✅ 100 entradas de log simuladas
- ✅ KPIs calculados con datos demo
- ✅ Dashboard funcional completo

### 📊 Para habilitar Google Sheets en producción:

**Opción A: Usando Secret Files (RECOMENDADO):**

1. **Obtener credenciales Google:**

   - Ve a Google Cloud Console
   - Crea/selecciona un proyecto
   - Habilita Google Sheets API
   - Crea credenciales de Service Account
   - Descarga el archivo JSON

2. **En Render Web Service:**

   - Settings → Secret Files → Add Secret File
   - Filename: `edp-control-system-f3cfafc0093a.json`
   - Content: Pegar el JSON completo
   - La app lo buscará automáticamente en `/etc/secrets/`

3. **Configurar variables:**
   ```bash
   SHEET_ID=1ABC123def456GHI789jkl0MNO1pqr2STU3vwx4YZ5
   ```

**Opción B: Modo Demo (sin configuración):**

- No hagas nada, la app usará datos simulados
- Perfecto para testing o demostración

## 🔐 **SOLUCIÓN PROBLEMAS SECRET FILES**

### ❌ Error común: "Permission denied" al leer Secret Files

Si ves este error:
```
❌ Error de permisos leyendo credenciales: [Errno 13] Permission denied: '/etc/secrets/edp-control-system-f3cfafc0093a.json'
```

**✅ SOLUCIÓN IMPLEMENTADA:**

1. **Script automático de corrección**: `fix_render_secrets.py`
   - Se ejecuta como root en el entrypoint
   - Copia Secret Files de `/etc/secrets/` a `/app/secrets/`
   - Ajusta permisos para que sean legibles por `appuser`

2. **Búsqueda inteligente de credenciales**: 
   - La app busca credenciales en múltiples ubicaciones
   - Prioriza archivos copiados en `/app/secrets/`
   - Fallback a ubicaciones originales si es posible

3. **Modo demo robusto**:
   - Si no se pueden leer las credenciales, la app funciona en modo demo
   - Datos demo para EDP y logs incluidos
   - No falla el deploy por problemas de permisos

### 🔧 **Archivos involucrados en la solución:**

- `fix_render_secrets.py`: Copia Secret Files con permisos correctos
- `entrypoint.sh`: Ejecuta corrección como root, luego cambia a appuser  
- `edp_mvp/app/config/__init__.py`: Búsqueda inteligente de credenciales
- `edp_mvp/app/utils/gsheet.py`: Manejo robusto de errores de permisos
- `edp_mvp/app/utils/demo_data.py`: Datos demo cuando no hay acceso a Google Sheets
