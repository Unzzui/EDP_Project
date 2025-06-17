# Sistema de Invalidación de Cache Automático

## Descripción

El sistema de invalidación de cache automático ha sido implementado para resolver el problema de actualizaciones basadas en tiempo en lugar de cambios reales en los datos. Este sistema:

- ✅ **Invalida cache solo cuando hay cambios reales** en los datos
- ✅ **Detecta automáticamente** qué tipos de cache necesitan actualizarse
- ✅ **Integra con operaciones existentes** a través de decoradores
- ✅ **Proporciona webhooks** para sistemas externos
- ✅ **Monitorea la salud** del sistema de cache
- ✅ **Incluye herramientas CLI** para administración

## Arquitectura del Sistema

### 1. Servicio de Invalidación (CacheInvalidationService)

- **Ubicación**: `app/services/cache_invalidation_service.py`
- **Función**: Coordina la invalidación basada en eventos
- **Dependencias de Cache**: Define qué cache depende de qué datos

### 2. Decoradores Automáticos

- **`@invalidate_cache_on_change`**: Decorador que se aplica a funciones que modifican datos
- **Integración**: Aplicado automáticamente en repositorios y servicios

### 3. Webhooks para Sistemas Externos

- **Endpoint**: `/manager/webhook/data-changed`
- **Función**: Permite que Google Sheets y otros sistemas notifiquen cambios
- **Seguridad**: Requiere webhook key para autenticación

### 4. Tareas de Monitoreo (Celery)

- **`monitor_cache_system`**: Monitorea salud del sistema
- **`cleanup_cache_events`**: Limpia eventos antiguos
- **`auto_warm_cache`**: Pre-calienta cache con consultas comunes

## Componentes Implementados

### A. Integración en Repositorios

```python
@invalidate_cache_on_change('edp_updated', ['edps'])
def update_by_edp_id(self, n_edp: str, form_data: Dict[str, Any], user: str = "Sistema"):
    # Automáticamente invalida cache cuando se actualiza un EDP
```

### B. Hooks en Controladores

```python
# En controller_controller.py - _background_update_edp
cache_invalidation = CacheInvalidationService()
if 'estado' in updates:
    cache_invalidation.register_data_change('edp_state_changed', [n_edp])
```

### C. Script de Google Apps Script

- **Archivo**: `google_apps_script_webhook.js`
- **Función**: Detecta cambios en Google Sheets y envía webhooks
- **Configuración**: Instalar en Google Apps Script con triggers

### D. CLI de Administración

- **Archivo**: `cache_cli.py`
- **Uso**: `./cache_cli.py health` para verificar estado

## APIs Disponibles

### 1. Estado de Salud del Cache

```bash
GET /manager/api/cache/health
```

### 2. Invalidación Manual

```bash
POST /manager/api/cache/invalidate
{
  "change_type": "edp_update",
  "filters": {}
}
```

### 3. Invalidación Automática

```bash
POST /manager/api/cache/auto-invalidate
{
  "operation": "edp_updated",
  "affected_ids": ["EDP-001", "EDP-002"],
  "metadata": {}
}
```

### 4. Webhook para Sistemas Externos

```bash
POST /manager/webhook/data-changed
{
  "webhook_key": "default_key_123",
  "change_type": "edp_updated",
  "affected_records": ["EDP-001"],
  "source_system": "google_sheets"
}
```

## Uso del CLI

### Verificar Estado del Sistema

```bash
./cache_cli.py health
./cache_cli.py health --json  # Output JSON
```

### Invalidar Cache Manualmente

```bash
./cache_cli.py invalidate --type all
./cache_cli.py invalidate --type dashboard
./cache_cli.py invalidate --operation edp_updated --ids EDP-001 EDP-002
```

### Monitorear Eventos

```bash
./cache_cli.py monitor
./cache_cli.py monitor --count 20
```

### Pre-calentar Cache

```bash
./cache_cli.py warm
./cache_cli.py warm --all
```

### Ver Estadísticas

```bash
./cache_cli.py stats
./cache_cli.py stats --detailed
```

## Configuración de Google Sheets

### 1. Instalar Script en Google Apps Script

1. Abrir Google Apps Script: `script.google.com`
2. Crear nuevo proyecto
3. Copiar contenido de `google_apps_script_webhook.js`
4. Configurar `WEBHOOK_URL` con la URL de tu aplicación Flask
5. Guardar y ejecutar `setupTriggers()`

### 2. Configurar Variables de Entorno

```bash
# En tu aplicación Flask
export CACHE_WEBHOOK_KEY="tu_clave_secreta_aqui"
```

### 3. Validar Configuración

Ejecutar en Google Apps Script:

```javascript
validateSetup();
```

## Variables de Entorno

```bash
# Redis (requerido)
REDIS_URL=redis://localhost:6379

# Webhook security (opcional)
CACHE_WEBHOOK_KEY=default_key_123
```

## Mapeo de Operaciones

El sistema mapea automáticamente operaciones a tipos de datos:

```python
operation_mapping = {
    'edp_created': ['edps'],
    'edp_updated': ['edps'],
    'edp_deleted': ['edps'],
    'edp_state_changed': ['edps'],
    'project_updated': ['projects'],
    'cost_updated': ['costs'],
    'bulk_edp_update': ['edps'],
    'data_import': ['edps', 'projects', 'costs']
}
```

## Dependencias de Cache

```python
cache_dependencies = {
    'manager_dashboard': ['edps', 'projects', 'costs'],
    'kpis': ['edps', 'projects'],
    'charts': ['edps', 'projects', 'costs'],
    'financials': ['edps', 'costs'],
    'analytics': ['edps', 'projects'],
    'kanban': ['edps'],
    'cashflow': ['edps', 'costs']
}
```

## Monitoreo y Logs

### Eventos Registrados

- Cada invalidación genera un evento con timestamp
- Eventos se almacenan en Redis con TTL de 1 hora
- CLI puede mostrar eventos recientes

### Logs de Aplicación

```python
logger.info("✅ Data change registered: edp_updated -> invalidated 15 cache entries")
```

### Métricas Disponibles

- Total de keys en cache
- Eventos de invalidación recientes
- Estado de conectividad de Redis
- Breakdown por tipo de cache

## Beneficios del Sistema

### ✅ Antes (Problemático)

- Cache se actualizaba cada X minutos independientemente de si había cambios
- Datos podían estar obsoletos entre actualizaciones
- Desperdicio de recursos computacionales
- Usuario veía datos inconsistentes

### ✅ Después (Optimizado)

- Cache se invalida solo cuando hay cambios reales
- Datos siempre frescos y consistentes
- Uso eficiente de recursos
- Mejor experiencia de usuario
- Sistema proactivo vs reactivo

## Próximos Pasos

1. **Monitoring Dashboard**: Crear interfaz web para monitorear el sistema
2. **Métricas Avanzadas**: Implementar Prometheus/Grafana para métricas
3. **Alertas**: Configurar alertas cuando el sistema no funciona correctamente
4. **Optimizaciones**: Implementar cache warming inteligente
5. **Testing**: Crear tests automatizados para el sistema de invalidación

## Troubleshooting

### Problema: Cache no se invalida

- Verificar que Redis esté funcionando: `./cache_cli.py health`
- Verificar logs de aplicación para errores
- Verificar que los decoradores estén aplicados correctamente

### Problema: Webhook no funciona

- Verificar `CACHE_WEBHOOK_KEY` en variables de entorno
- Verificar connectivity desde Google Sheets
- Revisar logs del endpoint webhook

### Problema: Demasiadas keys en cache

- Ejecutar cleanup: `./cache_cli.py invalidate --type all`
- Verificar TTL de las keys
- Considerar ajustar estrategia de cache

### Debugging

```bash
# Ver estado completo
./cache_cli.py health --json

# Ver eventos recientes
./cache_cli.py monitor --count 50

# Forzar limpieza completa
./cache_cli.py invalidate --type all
```
