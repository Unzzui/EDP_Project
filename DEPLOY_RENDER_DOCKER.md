# 🐳 Deploy en Render con Docker

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
```

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
