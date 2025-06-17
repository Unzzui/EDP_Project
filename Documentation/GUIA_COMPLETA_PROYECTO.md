# 🗺️ GUÍA COMPLETA DEL PROYECTO EDP MVP

## 📋 ÍNDICE

1. [Estructura General](#estructura-general)
2. [Archivos de Configuración](#archivos-de-configuración)
3. [Aplicación Principal](#aplicación-principal)
4. [Controladores y Rutas](#controladores-y-rutas)
5. [Servicios de Negocio](#servicios-de-negocio)
6. [Repositorios de Datos](#repositorios-de-datos)
7. [Plantillas y Frontend](#plantillas-y-frontend)
8. [Utilidades y Herramientas](#utilidades-y-herramientas)
9. [Dashboard y Análisis](#dashboard-y-análisis)
10. [APIs y Endpoints](#apis-y-endpoints)
11. [Comandos Útiles](#comandos-útiles)
12. [Solución de Problemas](#solución-de-problemas)

---

## 🏗️ ESTRUCTURA GENERAL

```
EDP_Project/
├── 🚀 run.py                    # Ejecutar app en desarrollo
├── 🚀 run_production.py         # Ejecutar app en producción
├── 📋 requirements.txt          # Dependencias Python
├── 🔧 status_check.py           # Verificar estado del sistema
├── 🧪 test_services.py          # Pruebas de servicios
└── edp_mvp/                     # Aplicación principal
    ├── app/                     # Código de la aplicación
    └── test_architecture.py     # Pruebas de arquitectura
```

---

## ⚙️ ARCHIVOS DE CONFIGURACIÓN

### 📍 Ubicación: `/edp_mvp/app/`

| Archivo         | Propósito               | Ubicación                    |
| --------------- | ----------------------- | ---------------------------- |
| `__init__.py`   | Inicialización de Flask | `/edp_mvp/app/__init__.py`   |
| `config.py`     | Configuración de la app | `/edp_mvp/app/config.py`     |
| `extensions.py` | Extensiones de Flask    | `/edp_mvp/app/extensions.py` |

### 🔑 Configuraciones Importantes:

```python
# config.py - Configuración principal
SECRET_KEY = "dev-secret-key-change-in-production"
GOOGLE_SHEETS_CREDENTIALS = "keys/edp-control-system-f3cfafc0093a.json"
```

---

## 🎯 APLICACIÓN PRINCIPAL

### 📍 Estructura del Core: `/edp_mvp/app/`

```
app/
├── 🔐 auth/                     # Sistema de autenticación
│   ├── forms.py                 # Formularios de login
│   └── routes.py                # Rutas de autenticación
├── 🎛️ controllers/              # Controladores de API
├── 📊 dashboard/                # Dashboards especializados
├── 📝 edp/                      # Módulo de EDPs
├── 🏛️ models/                   # Modelos de datos
├── 💾 repositories/             # Acceso a datos
├── ⚙️ services/                 # Lógica de negocio
├── 🎨 static/                   # Archivos estáticos
├── 📄 templates/                # Plantillas HTML
└── 🛠️ utils/                    # Utilidades
```

---

## 🎛️ CONTROLADORES Y RUTAS

### 📍 Ubicación: `/edp_mvp/app/controllers/`

| Controlador                  | Responsabilidad       | Endpoints           |
| ---------------------------- | --------------------- | ------------------- |
| **edp_controller.py**        | Gestión de EDPs       | `/api/edp/*`        |
| **manager_controller.py**    | Dashboard gerencial   | `/api/manager/*`    |
| **controller_controller.py** | Dashboard controlador | `/api/controller/*` |

### 🔗 Endpoints Principales:

#### 📊 Manager Dashboard (`/api/manager/`)

```
GET  /api/manager/related-data        # Datos relacionados
GET  /api/manager/selector-lists      # Listas para selectores
POST /api/manager/executive-kpis      # KPIs ejecutivos
POST /api/manager/executive-charts    # Gráficos ejecutivos
POST /api/manager/profitability       # Análisis de rentabilidad
GET  /api/manager/top-edps           # Top EDPs por monto
POST /api/manager/critical-projects   # Proyectos críticos
```

#### 📋 EDP Management (`/api/edp/`)

```
GET  /api/edp/                       # Listar EDPs
POST /api/edp/                       # Crear EDP
GET  /api/edp/<id>                   # Obtener EDP específico
PUT  /api/edp/<id>                   # Actualizar EDP
```

---

## ⚙️ SERVICIOS DE NEGOCIO

### 📍 Ubicación: `/edp_mvp/app/services/`

| Servicio             | Función                 | Archivo                |
| -------------------- | ----------------------- | ---------------------- |
| **ManagerService**   | Lógica gerencial y KPIs | `manager_service.py`   |
| **EDPService**       | Gestión de EDPs         | `edp_service.py`       |
| **CostService**      | Gestión de costos       | `cost_service.py`      |
| **AnalyticsService** | Análisis y métricas     | `analytics_service.py` |
| **DashboardService** | Datos de dashboard      | `dashboard_service.py` |
| **KanbanService**    | Tablero Kanban          | `kanban_service.py`    |
| **CashflowService**  | Flujo de caja           | `cashflow_service.py`  |
| **KPIService**       | Indicadores clave       | `kpi_service.py`       |

### 🎯 Manager Service - Métodos Principales:

```python
# manager_service.py
load_related_data()                    # Cargar datos relacionados
calculate_executive_kpis()             # Calcular KPIs ejecutivos
generate_executive_charts()            # Generar gráficos
analyze_profitability()                # Análisis de rentabilidad
get_top_edps()                        # Top EDPs
generate_executive_alerts()            # Alertas ejecutivas
```

---

## 💾 REPOSITORIOS DE DATOS

### 📍 Ubicación: `/edp_mvp/app/repositories/`

| Repositorio           | Datos                | Archivo                 |
| --------------------- | -------------------- | ----------------------- |
| **EDPRepository**     | EDPs (Google Sheets) | `edp_repository.py`     |
| **CostRepository**    | Costos               | `cost_repository.py`    |
| **ProjectRepository** | Proyectos            | `project_repository.py` |
| **LogRepository**     | Logs del sistema     | `log_repository.py`     |

### 🔑 Configuración Google Sheets:

```
Credenciales: /edp_mvp/app/keys/tu-credencial.json
```

---

## 📄 PLANTILLAS Y FRONTEND

### 📍 Estructura: `/edp_mvp/app/templates/`

```
templates/
├── 📄 base.html                     # Plantilla base
├── 🧭 navbar.html                   # Barra de navegación
├── 📝 edp_form.html                 # Formulario EDP
├── 📋 edp_list.html                 # Lista de EDPs
├── 🔐 login.html                    # Página de login
├── 🧩 components/                   # Componentes reutilizables
├── 🎛️ controller/                   # Dashboard controlador
├── 📊 dashboard/                    # Dashboards generales
├── 🏗️ layouts/                     # Layouts base
├── 👨‍💼 manager/                      # Dashboard gerencial
└── 📄 pages/                       # Páginas específicas
```

### 🎨 Archivos Estáticos: `/edp_mvp/app/static/`

```
static/
├── 🎨 css/                         # Estilos CSS
├── 🖼️ img/                         # Imágenes
└── ⚡ js/                          # JavaScript
```

---

## 🛠️ UTILIDADES Y HERRAMIENTAS

### 📍 Ubicación: `/edp_mvp/app/utils/`

| Utilidad            | Función                | Archivo               |
| ------------------- | ---------------------- | --------------------- |
| **FormatUtils**     | Formateo de datos      | `format_utils.py`     |
| **DateUtils**       | Manejo de fechas       | `date_utils.py`       |
| **ValidationUtils** | Validaciones           | `validation_utils.py` |
| **GoogleSheets**    | Conexión Google Sheets | `gsheet.py`           |
| **Calc**            | Cálculos matemáticos   | `calc.py`             |

---

## 📊 DASHBOARD Y ANÁLISIS

### 📍 Ubicación: `/edp_mvp/app/dashboard/`

| Dashboard                | Usuario       | Archivo         |
| ------------------------ | ------------- | --------------- |
| **Manager Dashboard**    | Gerentes      | `manager.py`    |
| **Controller Dashboard** | Controladores | `controller.py` |

### 🎯 Rutas de Dashboard:

```
/dashboard/manager                    # Dashboard gerencial
/dashboard/controller                 # Dashboard controlador
```

---

## 🔌 APIs Y ENDPOINTS

### 📡 URLs Base:

```
Desarrollo:  http://localhost:5000
Producción:  [Configurar en config.py]
```

### 🎯 Endpoints por Módulo:

#### 👨‍💼 Manager APIs:

```bash
# Datos relacionados
GET /api/manager/related-data

# KPIs ejecutivos
POST /api/manager/executive-kpis
Content-Type: application/json
{
  "jefe_proyecto": "opcional",
  "cliente": "opcional",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD"
}

# Gráficos ejecutivos
POST /api/manager/executive-charts

# Análisis de rentabilidad
POST /api/manager/profitability

# Top EDPs
GET /api/manager/top-edps?limit=10

# Proyectos críticos
POST /api/manager/critical-projects
```

#### 📋 EDP APIs:

```bash
# Listar EDPs
GET /api/edp/

# Crear EDP
POST /api/edp/
Content-Type: application/json
{
  "proyecto": "Nombre del proyecto",
  "cliente": "Cliente",
  "monto_propuesto": 1000000,
  "descripcion": "Descripción"
}
```

---

## 🚀 COMANDOS ÚTILES

### 🖥️ Desarrollo:

```bash
# Ejecutar en desarrollo
cd /home/unzzui/Documents/coding/EDP_Project
python run.py

# Ejecutar en producción
python run_production.py

# Verificar estado del sistema
python status_check.py

# Ejecutar pruebas
python test_services.py
```

### 📦 Dependencias:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Actualizar dependencias
pip freeze > requirements.txt
```

### 🔍 Debugging:

```bash
# Ver logs de la aplicación
tail -f logs/app.log

# Verificar estructura
python edp_mvp/test_architecture.py
```

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### ❌ Errores Comunes:

#### 1. **Error de Google Sheets**

```
Problema: No se pueden cargar datos
Solución: Verificar credenciales en /edp_mvp/app/keys/
```

#### 2. **Error de Flask SECRET_KEY**

```
Problema: RuntimeError sobre SECRET_KEY
Solución: Verificar config.py está activado
```

#### 3. **Error de importación pandas**

```
Problema: ModuleNotFoundError: pandas
Solución: pip install pandas
```

#### 4. **Error en manager_controller.py**

```
Problema: SyntaxError en critical_projects
Solución: Verificar sintaxis de try/except
```

### 🩺 Diagnóstico Rápido:

```bash
# Verificar configuración
python -c "from edp_mvp.app import create_app; print('OK')"

# Verificar servicios
python test_services.py

# Verificar estructura
python edp_mvp/test_architecture.py
```

---

## 📝 NOTAS IMPORTANTES

### 🔐 Seguridad:

- Credenciales Google Sheets en `/edp_mvp/app/keys/`
- SECRET_KEY configurado en `config.py`
- No subir credenciales al repositorio

### 📊 Datos:

- Datos principales en Google Sheets
- Cache en memoria para performance
- Validación de datos en servicios

### 🎯 Performance:

- Servicios optimizados para grandes volúmenes
- Caching de datos frecuentes
- Paginación en APIs

---

## 🆘 CONTACTO Y SOPORTE

### 📧 Para problemas técnicos:

1. Verificar logs en consola
2. Ejecutar `python status_check.py`
3. Revisar esta guía
4. Consultar código en `/edp_mvp/app/`

### 📚 Documentación adicional:

- Comentarios en código
- Docstrings en métodos
- Tests en archivos `test_*.py`

---

_Última actualización: Junio 2025_
_Versión: MVP 1.0_
