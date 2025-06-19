# MIGRACIÓN A SUPABASE - GUÍA COMPLETA

## 📋 CHECKLIST DE MIGRACIÓN

### PASO 1: Configuración de Supabase

- [ ] Crear proyecto en Supabase
- [ ] Obtener credenciales de conexión
- [ ] Configurar variables de entorno
- [ ] Instalar dependencias adicionales

### PASO 2: Preparación del Código

- [ ] Actualizar configuración de base de datos
- [ ] Crear script de migración
- [ ] Adaptar modelos para PostgreSQL
- [ ] Actualizar archivos de configuración

### PASO 3: Migración de Datos

- [ ] Exportar datos de SQLite
- [ ] Crear esquema en PostgreSQL
- [ ] Importar datos a Supabase
- [ ] Verificar integridad de datos

### PASO 4: Testing y Deployment

- [ ] Probar en entorno local
- [ ] Actualizar configuración de producción
- [ ] Desplegar cambios
- [ ] Verificar funcionamiento

## 🔧 INSTRUCCIONES DETALLADAS

### 1. CREAR PROYECTO EN SUPABASE

1. Ve a https://supabase.com
2. Crea una cuenta o inicia sesión
3. Crea un nuevo proyecto
4. Guarda las credenciales que te proporcione

### 2. VARIABLES DE ENTORNO

Añade estas variables a tu archivo .env:

```env
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key

# Database URL para SQLAlchemy
DATABASE_URL=postgresql://postgres:tu_password@db.tu-proyecto.supabase.co:5432/postgres

# Backup de SQLite (para rollback si es necesario)
SQLITE_BACKUP_PATH=./backups/edp_database_backup.db
```

### 3. DEPENDENCIAS ADICIONALES

Ya tienes psycopg2-binary, pero podrías necesitar:

- supabase (cliente oficial de Python)
- alembic (para migraciones más avanzadas)

### 4. PASOS DE CÓDIGO

Los archivos que se han creado/modificado:
✅ config/**init**.py (configuración actualizada para Supabase)
✅ migration_sqlite_to_supabase.py (script de migración automática)
✅ verify_supabase_migration.py (script de verificación)
✅ rollback_to_sqlite.py (script de rollback)
✅ requirements.txt (dependencias añadidas)
✅ .env.supabase.example (template de configuración)

## 🚀 PASOS PARA EJECUTAR LA MIGRACIÓN

### PASO 1: Preparación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear proyecto en Supabase
# Ve a https://supabase.com y crea un proyecto

# 3. Configurar variables de entorno
cp .env.supabase.example .env
# Edita .env con tus credenciales reales de Supabase
```

### PASO 2: Ejecutar migración

```bash
# 1. Verificar configuración actual
python verify_supabase_migration.py

# 2. Ejecutar migración (crea backup automáticamente)
python migration_sqlite_to_supabase.py

# 3. Verificar migración
python verify_supabase_migration.py
```

### PASO 3: Testing

```bash
# 1. Probar la aplicación
python run.py

# 2. Verificar que funcionen las funcionalidades principales:
#    - Login de usuarios
#    - Carga de datos
#    - Dashboard
#    - Kanban
```

### PASO 4: En caso de problemas

```bash
# Rollback a SQLite
python rollback_to_sqlite.py
```

## 📝 NOTAS IMPORTANTES

### Configuración de Supabase

1. **Row Level Security (RLS)**: Desactívalo temporalmente para la migración
2. **Conexiones**: Supabase tiene límites de conexiones concurrentes
3. **Indexes**: Considera recrear los índices después de la migración

### Variables de entorno críticas

```env
DATABASE_URL=postgresql://postgres:password@db.proyecto.supabase.co:5432/postgres
DATABASE_TYPE=postgresql
SUPABASE_URL=https://proyecto.supabase.co
SUPABASE_ANON_KEY=tu_anon_key
```

### Verificaciones post-migración

- [ ] Todos los usuarios pueden hacer login
- [ ] Los datos de EDP se cargan correctamente
- [ ] El dashboard muestra métricas
- [ ] Las funciones de admin funcionan
- [ ] Los websockets (si los usas) funcionan
