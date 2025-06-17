# 🚀 Guía de Deploy en Render para EDP MVP

## Problemas Resueltos

### ❌ Problemas Originales:

1. **Redis no disponible**: `Error 111 connecting to localhost:6379. Connection refused.`
2. **Werkzeug en producción**: `RuntimeError: The Werkzeug web server is not designed to run in production`

### ✅ Soluciones Implementadas:

1. **Servidor de producción**: Gunicorn con eventlet para SocketIO
2. **Redis externo**: Configuración para usar Redis de Render
3. **Variables de entorno**: Configuración flexible para desarrollo y producción

## 📁 Archivos Creados/Modificados

- `gunicorn_config.py` - Configuración del servidor Gunicorn
- `wsgi.py` - Entry point para WSGI
- `Procfile` - Comandos de inicio para Render
- `render.yaml` - Configuración completa de servicios
- `start_production.sh` - Script de inicio con verificaciones
- `env.production.example` - Variables de entorno ejemplo

## 🔧 Configuración en Render

### Opción 1: Deploy Manual Simple

1. **Conecta tu repositorio** en Render
2. **Configura las variables de entorno**:

   ```
   FLASK_ENV=production
   SECRET_KEY=tu-clave-secreta-aqui
   ```

3. **Configura los servicios**:
   - **Web Service**:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn --config gunicorn_config.py wsgi:application`
   - **Redis**: Agrega un servicio Redis desde el dashboard de Render

### Opción 2: Deploy con render.yaml (Recomendado)

1. Sube el archivo `render.yaml` a tu repositorio
2. En Render, selecciona "New" > "Blueprint"
3. Conecta tu repositorio y Render detectará el `render.yaml`
4. Configura las variables de entorno sensibles manualmente

### Variables de Entorno Requeridas en Render:

```bash
# Obligatorias
FLASK_ENV=production
SECRET_KEY=una-clave-muy-segura-de-32-caracteres-minimo

# Automáticas (Render las proporciona)
REDIS_URL=redis://...
DATABASE_URL=postgresql://...
PORT=5000
```

## 🔄 Verificación de Deploy

1. **Verifica que Redis esté conectado**:

   - Los logs deben mostrar "✅ Redis conectado correctamente"
   - Sin "⚠️ Redis no disponible"

2. **Verifica que Gunicorn esté ejecutándose**:

   - Los logs deben mostrar "Server is ready. Spawning workers"
   - No debe aparecer RuntimeError de Werkzeug

3. **Verifica funcionalidades**:
   - Login/logout funciona
   - Dashboard carga correctamente
   - WebSocket funciona (tiempo real)

## 🐛 Troubleshooting

### Si Redis sigue fallando:

```bash
# Verifica la variable REDIS_URL en Render
echo $REDIS_URL
# Debe ser algo como: redis://red-xxxxx:6379
```

### Si Gunicorn no inicia:

```bash
# Verifica que eventlet esté instalado
pip list | grep eventlet
# Debe mostrar: eventlet==0.36.1
```

### Logs útiles:

```bash
# En Render, revisa los logs del servicio web
# Busca estos mensajes:
# ✅ Redis conectado correctamente
# 🌐 Iniciando servidor web con Gunicorn
# Server is ready. Spawning workers
```

## 📈 Optimizaciones de Producción

1. **Workers de Gunicorn**: Ajusta según el plan de Render
2. **Redis Memory**: Configurado con límite de 256MB y política LRU
3. **SocketIO**: Configurado con eventlet para mejor rendimiento
4. **Celery**: Worker separado para tareas asíncronas

## 🔐 Seguridad

- ✅ Debug desactivado en producción
- ✅ Secret key configurable
- ✅ CORS configurado correctamente
- ✅ Variables sensibles en entorno, no en código

## 🆘 Si necesitas ayuda

1. Revisa los logs en el dashboard de Render
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que el servicio Redis esté activo y conectado
4. Considera usar el plan básico de Redis si el gratuito no funciona
