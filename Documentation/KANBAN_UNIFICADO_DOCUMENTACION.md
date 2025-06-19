# Implementación del Sistema Kanban Unificado con Control de Acceso por Roles

## Resumen

Se ha implementado una vista Kanban unificada que permite diferentes niveles de acceso según el rol del usuario:

### Niveles de Acceso

1. **Acceso Completo (`full`)** - Admin, Manager, Controller

   - Ve todos los EDPs del sistema
   - Puede usar todos los filtros disponibles
   - Acceso a funcionalidades avanzadas

2. **Acceso Restringido (`restricted`)** - Jefe de Proyecto, Miembro de Equipo

   - Solo ve los EDPs de sus proyectos asignados
   - Filtro automático por `jefe_proyecto`
   - Interfaz simplificada

3. **Sin Acceso (`none`)** - Usuarios sin rol o roles no autorizados
   - Redirigidos a la página principal

## Arquitectura

### Controlador Unificado

- **Archivo**: `edp_mvp/app/controllers/kanban_controller.py`
- **Blueprint**: `kanban_bp` con prefijo `/kanban`
- **Rutas principales**:
  - `GET /kanban/` - Vista principal
  - `POST /kanban/update_estado` - Actualizar estado de EDP
  - `GET /kanban/api/get-edp/<edp_id>` - Obtener datos de EDP específico

### Funciones Clave

#### `_get_user_access_level()`

Determina el nivel de acceso basado en el rol del usuario:

```python
def _get_user_access_level() -> str:
    role = getattr(current_user, 'rol', '')
    if role in ['admin', 'administrador']:
        return 'full'
    elif role in ['manager', 'controller']:
        return 'full'
    elif role in ['jefe_proyecto', 'miembro_equipo_proyecto']:
        return 'restricted'
    else:
        return 'none'
```

#### `_apply_role_based_filters()`

Aplica filtros automáticos para usuarios restringidos:

```python
def _apply_role_based_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    access_level = _get_user_access_level()
    if access_level == 'restricted':
        manager_name = _get_manager_name_for_filtering()
        if manager_name:
            filters['jefe_proyecto'] = manager_name
    return filters
```

### Template Unificado

- **Archivo**: `edp_mvp/app/templates/kanban/kanban_unified.html`
- Adaptable basado en `user_access_level`
- Muestra/oculta campos según permisos
- Interface responsive y moderna

## Navegación Actualizada

Se han actualizado todos los enlaces en la navegación para usar la nueva ruta unificada:

### Antes

```html
href="{{ url_for('controller.vista_kanban') }}" href="{{
url_for('project_manager.kanban_view') }}"
```

### Después

```html
href="{{ url_for('kanban.vista_kanban') }}"
```

### Archivos Actualizados

- `templates/components/navbar.html`
- `templates/main/landing.html`
- `templates/base/_navigation_simple.html`

## Flujo de Funcionamiento

1. **Usuario accede a `/kanban/`**
2. **Se determina el nivel de acceso** basado en `current_user.rol`
3. **Se aplican filtros automáticos** si es usuario restringido
4. **Se cargan datos** usando el servicio apropiado
5. **Se procesan datos del Kanban** con filtros aplicados
6. **Se renderiza template unificado** con contexto apropiado

## Beneficios

### Para Administradores y Managers

- Vista completa del sistema
- Acceso a todos los filtros
- Funcionalidades avanzadas de gestión

### Para Jefes de Proyecto

- Vista enfocada en sus proyectos
- Menos complejidad visual
- Datos relevantes para su rol

### Para el Sistema

- Una sola vista de Kanban que mantener
- Control de acceso centralizado
- Código más limpio y mantenible

## Seguridad

### Control de Acceso

- Verificación de rol en cada request
- Filtrado automático de datos sensibles
- Validación de permisos en APIs

### Ejemplo de Verificación

```python
# Verificar permisos para usuarios restringidos
if access_level == 'restricted':
    manager_name = _get_manager_name_for_filtering()
    if manager_name and edp_data.get('jefe_proyecto') != manager_name:
        return jsonify({"error": "Sin permisos para este EDP"}), 403
```

## Próximos Pasos

1. **Testing** - Probar con diferentes roles de usuario
2. **Funcionalidad Drag & Drop** - Implementar arrastrar y soltar EDPs
3. **Modales de Detalle** - Agregar modales para edición de EDPs
4. **Notificaciones en Tiempo Real** - WebSocket para actualizaciones
5. **Métricas Personalizadas** - KPIs específicos por rol

## Estructura de Archivos

```
edp_mvp/app/
├── controllers/
│   ├── kanban_controller.py          # Controlador unificado (NUEVO)
│   ├── controller_controller.py      # Mantiene otras funciones
│   └── project_manager_controller.py # Mantiene otras funciones
├── templates/
│   ├── kanban/
│   │   └── kanban_unified.html       # Template unificado (NUEVO)
│   ├── controller/
│   │   └── controller_kanban.html    # Puede deprecarse
│   └── JP/
│       └── kanban.html               # Puede deprecarse
└── services/
    ├── kanban_service.py             # Lógica de negocio del Kanban
    ├── controller_service.py         # Para usuarios con acceso completo
    └── manager_service.py            # Para servicios generales
```

Esta implementación proporciona una base sólida para el sistema de control de acceso optimizado que solicitaste, con la vista Kanban como componente principal del apartado de control.
