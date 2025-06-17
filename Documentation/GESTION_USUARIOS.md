# 👥 Gestión de Usuarios - Sistema EDP

## 📋 Descripción

Sistema completo de gestión de usuarios para el proyecto EDP que permite a los administradores crear, listar y gestionar usuarios desde una interfaz web profesional.

## 🎯 Características Implementadas

### ✅ Backend (Flask)

- **Rutas protegidas** con decoradores `@login_required` y `@role_required("admin")`
- **Repositorio de usuarios** con conexión a Google Sheets
- **Validaciones completas** de formularios
- **Hash de contraseñas** con `werkzeug.security`
- **Sistema de roles** (admin, controller, manager, jefe_proyecto)
- **Manejo de errores** y mensajes flash

### ✅ Frontend (HTML/CSS)

- **Interfaz moderna** con Tailwind CSS
- **Formulario de creación** responsivo y accesible
- **Lista de usuarios** con tabla profesional
- **Mensajes de éxito/error** con iconos
- **Estadísticas de usuarios** por rol
- **Navegación intuitiva** entre vistas

### ✅ Base de Datos (SQLite)

- **Tabla "usuarios"** con estructura SQLAlchemy
- **Script de inicialización** automática
- **Usuario admin por defecto**
- **Validación de username único**
- **Migraciones automáticas** con Flask-SQLAlchemy

## 🚀 Instalación y Configuración

### 1. Ejecutar Script de Inicialización

```bash
python init_system.py
```

Este script:

- ✅ Crea la base de datos SQLite si no existe
- ✅ Configura las tablas correctas
- ✅ Crea un usuario administrador por defecto

### 2. Credenciales por Defecto

```
Username: admin
Password: admin123
```

⚠️ **¡IMPORTANTE!** Cambie esta contraseña después del primer login.

## 🔗 Rutas Disponibles

### Autenticación

- `GET/POST /login` - Inicio de sesión
- `GET /logout` - Cerrar sesión

### Administración de Usuarios (Solo Admin)

- `GET /admin/usuarios` - Lista de usuarios
- `GET/POST /admin/usuarios/nuevo` - Crear nuevo usuario

## 📊 Estructura de la Tabla "usuarios"

| Campo           | Tipo                | Descripción                  | Ejemplo                                           |
| --------------- | ------------------- | ---------------------------- | ------------------------------------------------- |
| id              | INTEGER PRIMARY KEY | Identificador único auto-inc | 1, 2, 3...                                        |
| nombre_completo | VARCHAR(100)        | Nombre completo del usuario  | "Juan Pérez González"                             |
| username        | VARCHAR(80) UNIQUE  | Nombre de usuario único      | "jperez"                                          |
| password_hash   | VARCHAR(120)        | Contraseña hasheada          | "pbkdf2:sha256:..."                               |
| rol             | VARCHAR(20)         | Rol del usuario              | "admin", "controller", "manager", "jefe_proyecto" |
| activo          | BOOLEAN             | Estado del usuario           | True/False                                        |
| fecha_creacion  | DATETIME            | Fecha de creación            | "2024-01-15 10:30:00"                             |
| ultimo_acceso   | DATETIME            | Último acceso al sistema     | "2024-01-20 14:25:30"                             |

## 🎨 Interfaz de Usuario

### Lista de Usuarios (`/admin/usuarios`)

- 📊 **Tabla de usuarios** con información completa
- 🏷️ **Badges de roles** con colores diferenciados
- 📈 **Estadísticas** por tipo de rol
- ➕ **Botón "Nuevo Usuario"** destacado
- 🔍 **Estado visual** de cada usuario

### Crear Usuario (`/admin/usuarios/nuevo`)

- 📝 **Formulario completo** con validación
- ✅ **Validación en tiempo real**
- 🔒 **Campo de contraseña** con requisitos
- 🎯 **Dropdown de roles** predefinidos
- 🔙 **Navegación** de retorno a la lista

## 🔐 Sistema de Roles

### Roles Disponibles

1. **admin** - Administrador del sistema

   - ✅ Acceso a gestión de usuarios
   - ✅ Acceso completo a todas las funciones

2. **controller** - Controlador

   - ✅ Acceso al dashboard de controller
   - ❌ Sin acceso a administración

3. **manager** - Manager

   - ✅ Acceso al dashboard de manager
   - ❌ Sin acceso a administración

4. **jefe_proyecto** - Jefe de Proyecto
   - ✅ Acceso a funciones de proyecto
   - ❌ Sin acceso a administración

## 🛡️ Seguridad Implementada

### Autenticación

- ✅ **Contraseñas hasheadas** con salt
- ✅ **Validación de credenciales** en base de datos
- ✅ **Sesiones seguras** con Flask-Login
- ✅ **Redirección por rol** después del login

### Autorización

- ✅ **Decorador `@role_required`** para rutas protegidas
- ✅ **Validación de permisos** en cada request
- ✅ **Mensajes de error** informativos
- ✅ **Redirección automática** a login si no autorizado

### Validaciones

- ✅ **Username único** verificado en base de datos
- ✅ **Campos requeridos** validados
- ✅ **Longitud mínima** de contraseña (6 caracteres)
- ✅ **Roles válidos** de lista predefinida

## 🎯 Casos de Uso

### Para Administradores

1. **Crear nuevo usuario**

   - Ir a `/admin/usuarios/nuevo`
   - Completar formulario
   - Seleccionar rol apropiado
   - Guardar usuario

2. **Ver lista de usuarios**
   - Ir a `/admin/usuarios`
   - Revisar usuarios existentes
   - Ver estadísticas por rol

### Para Usuarios

1. **Iniciar sesión**
   - Ir a `/login`
   - Ingresar username y contraseña
   - Ser redirigido según rol

## 🔧 Personalización

### Agregar Nuevos Roles

1. Editar lista `valid_roles` en `admin_controller.py`
2. Actualizar template `nuevo.html` con nueva opción
3. Agregar lógica de redirección en `auth/routes.py`

### Modificar Campos de Usuario

1. Actualizar modelo `User` en SQLAlchemy
2. Crear migración de base de datos
3. Actualizar templates HTML

## 🐛 Solución de Problemas

### Error: "Base de datos no encontrada"

```bash
python init_system.py
```

### Error: "No tienes permisos"

- Verificar que el usuario tenga rol "admin"
- Revisar implementación de `@role_required`

### Error: "Usuario ya existe"

- Verificar que el username sea único
- Revisar tabla "usuarios" en SQLite

## 📝 Próximas Mejoras

- [ ] Edición de usuarios existentes
- [ ] Desactivar/activar usuarios
- [ ] Cambio de contraseñas
- [ ] Auditoria de accesos
- [ ] Recuperación de contraseñas
- [ ] Validación de complejidad de contraseñas

## 🏗️ Arquitectura

```
📁 edp_mvp/app/
├── 📁 controllers/
│   └── 📄 admin_controller.py      # Rutas y lógica de admin
├── 📁 models/
│   └── 📄 user.py                  # Modelo SQLAlchemy User
├── 📁 templates/admin/usuarios/
│   ├── 📄 index.html               # Lista de usuarios
│   └── 📄 nuevo.html               # Crear usuario
├── 📁 auth/
│   └── 📄 routes.py                # Autenticación actualizada
├── 📁 utils/
│   └── 📄 init_users_db.py         # Inicialización de BD SQLite
├── 📄 extensions.py                # Flask-SQLAlchemy config
└── 📄 config.py                    # Configuración SQLite

📄 init_system.py                   # Script de configuración
📄 edp_database.db                  # Base de datos SQLite
```

---

## 🎉 ¡Sistema Listo!

Con esta implementación, el sistema EDP cuenta con un sistema completo de gestión de usuarios que cumple con todos los requisitos solicitados:

✅ **Funcional** - Crear usuarios desde el navegador  
✅ **Seguro** - Autenticación y autorización robusta  
✅ **Profesional** - Interfaz moderna y limpia  
✅ **Completo** - Validaciones y manejo de errores

¡El administrador ya puede gestionar usuarios de manera eficiente! 🚀
