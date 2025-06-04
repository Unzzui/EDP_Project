# 📋 Guía del Proyecto EDP MVP

## 🎯 Resumen del Proyecto

Sistema de gestión y control de EDPs (Expedientes de Pago) con dashboard ejecutivo, análisis de rentabilidad y gestión de costos.

---

## 📁 Estructura del Proyecto

### 🏠 Directorio Raíz: `/home/unzzui/Documents/coding/EDP_Project/`

```
EDP_Project/
├── 🚀 ARCHIVOS DE EJECUCIÓN
│   ├── run.py                    # Servidor desarrollo
│   ├── run_production.py         # Servidor producción
│   ├── requirements.txt          # Dependencias Python
│   └── status_check.py          # Verificación estado
│
├── 🧪 ARCHIVOS DE TESTING
│   ├── test_services.py         # Tests servicios
│   ├── import_test.py           # Tests importación
│   └── iniciar_ngrok.sh         # Script ngrok
│
└── 📦 edp_mvp/                  # APLICACIÓN PRINCIPAL
    ├── app/                     # Código fuente
    └── test_architecture.py    # Test arquitectura
```

---

## 🏗️ Arquitectura de la Aplicación (`edp_mvp/app/`)

### 🔧 Configuración

```
app/
├── __init__.py              # Inicialización Flask
├── config.py               # Configuración (SECRET_KEY, etc.)
└── extensions.py           # Extensiones Flask
```

### 🛡️ Autenticación (`app/auth/`)

```
auth/
├── __init__.py
├── forms.py                # Formularios login
└── routes.py               # Rutas autenticación
```

### 🎮 Controladores (`app/controllers/`)

```
controllers/
├── __init__.py
├── edp_controller.py       # API endpoints EDPs
├── manager_controller.py   # API endpoints dashboard gerencial
└── controller_controller.py # API endpoints controlador
```

### 📊 Dashboard (`app/dashboard/`)

```
dashboard/
├── __init__.py
├── controller.py           # Dashboard controlador
└── manager.py             # Dashboard gerencial
```

### 📋 Módulo EDP (`app/edp/`)

```
edp/
├── __init__.py
├── forms.py               # Formularios EDP
└── routes.py              # Rutas web EDP
```

---

## 🔄 Capa de Datos

### 📚 Repositorios (`app/repositories/`)

```
repositories/
├── __init__.py
├── edp_repository.py      # CRUD EDPs
├── cost_repository.py    # CRUD costos
├── project_repository.py # CRUD proyectos
└── log_repository.py     # CRUD logs
```

### 🧠 Servicios (`app/services/`)

```
services/
├── __init__.py
├── manager_service.py     # 🎯 SERVICIO PRINCIPAL GERENCIAL
├── edp_service.py         # Lógica negocio EDPs
├── cost_service.py        # Gestión costos
├── dashboard_service.py   # Dashboard general
├── analytics_service.py   # Análisis datos
├── cashflow_service.py    # Flujo caja
├── kanban_service.py      # Vista kanban
└── kpi_service.py         # Indicadores
```

---

## 🎨 Interfaz de Usuario

### 🌐 Templates (`app/templates/`)

```
templates/
├── base.html              # Template base
├── navbar.html            # Barra navegación
├── login.html             # Página login
├── edp_form.html          # Formulario EDP
├── edp_list.html          # Lista EDPs
│
├── components/            # Componentes reutilizables
├── layouts/               # Layouts base
├── pages/                 # Páginas estáticas
│
├── controller/            # Templates controlador
│   ├── dashboard.html
│   └── ...
│
└── manager/               # 🎯 TEMPLATES GERENCIALES
    ├── dashboard.html     # Dashboard principal
    ├── profitability.html # Análisis rentabilidad
    └── ...
```

### 🎨 Recursos Estáticos (`app/static/`)

```
static/
├── css/                   # Estilos CSS
├── js/                    # JavaScript
└── img/                   # Imágenes
```

---

## 🔧 Utilidades (`app/utils/`)

```
utils/
├── __init__.py
├── format_utils.py        # Formateo datos
├── date_utils.py          # Manejo fechas
├── validation_utils.py    # Validaciones
├── calc.py                # Cálculos
├── gsheet.py              # Google Sheets
└── fill_edp_ids.py        # Llenar IDs EDP
```

---

## 🛣️ Rutas Principales

### 🌐 Rutas Web

```
/                          # Login
/dashboard/manager         # Dashboard gerencial
/dashboard/controller      # Dashboard controlador
/edp/list                 # Lista EDPs
/edp/create               # Crear EDP
/edp/edit/<id>            # Editar EDP
```

### 🔌 API Endpoints

#### 📊 API Gerencial (`/api/manager/`)

```
GET  /api/manager/data                    # Datos relacionados
GET  /api/manager/kpis                    # KPIs ejecutivos
GET  /api/manager/charts                  # Gráficos
GET  /api/manager/profitability           # Análisis rentabilidad
GET  /api/manager/top-edps               # Top EDPs
GET  /api/manager/alerts                 # Alertas ejecutivas
GET  /api/manager/critical-projects      # Proyectos críticos
```

#### 📝 API EDPs (`/api/edp/`)

```
GET  /api/edp/                           # Listar EDPs
POST /api/edp/                           # Crear EDP
GET  /api/edp/<id>                       # Obtener EDP
PUT  /api/edp/<id>                       # Actualizar EDP
DELETE /api/edp/<id>                     # Eliminar EDP
```

---

## 📊 Funcionalidades Clave

### 🎯 Dashboard Gerencial

**Ubicación**: `app/services/manager_service.py`

#### 🔢 KPIs Ejecutivos

```python
# Método principal
_calculate_executive_kpis()

# Submétodos organizados:
_prepare_kpi_data()           # Preparación datos
_calculate_financial_kpis()   # KPIs financieros
_calculate_operational_kpis() # KPIs operacionales
_calculate_profitability_kpis() # KPIs rentabilidad
_calculate_aging_kpis()       # Buckets antigüedad
_calculate_efficiency_kpis()  # KPIs eficiencia
```

#### 📈 Análisis de Rentabilidad

```python
# Método principal
analyze_profitability()

# Análisis por dimensión:
_analyze_profitability_by_projects()  # Por proyectos
_analyze_profitability_by_clients()   # Por clientes
_analyze_profitability_by_managers()  # Por gestores
```

#### 📊 Generación de Gráficos

```python
_generate_chart_data()              # Datos gráficos
_build_monthly_trend_chart()        # Tendencias mensuales
_build_aging_buckets_chart()        # Buckets antigüedad
_build_manager_performance_chart()  # Performance gestores
_build_opex_capex_chart()          # OPEX/CAPEX
```

### 💰 Gestión de Costos

**Ubicación**: `app/services/cost_service.py`

- Integración con datos de costos reales
- Cálculo de rentabilidad con costos reales
- Fallback a costos estimados (65% de ingresos)

---

## 🔍 Archivos Importantes Modificados Recientemente

### ✅ Completamente Implementados

1. **`app/services/manager_service.py`** - ⭐ ARCHIVO PRINCIPAL

   - ✅ Análisis de rentabilidad completo
   - ✅ KPIs refactorizados en subfunciones
   - ✅ Integración con datos de costos reales
   - ✅ Generación de gráficos mejorada

2. **`app/config.py`**
   - ✅ Configuración SECRET_KEY activada
   - ✅ Variables de entorno configuradas

### 🔧 Necesita Corrección

3. **`app/controllers/manager_controller.py`**
   - ❌ Error de sintaxis en `api_critical_projects`
   - ❌ Falta import de pandas
   - ❌ Verificar creación de `df_edp`

---

## 🚀 Cómo Ejecutar

### 🔧 Desarrollo

```bash
cd /home/unzzui/Documents/coding/EDP_Project
python run.py
```

### 🌐 Producción

```bash
cd /home/unzzui/Documents/coding/EDP_Project
python run_production.py
```

### 🧪 Tests

```bash
cd /home/unzzui/Documents/coding/EDP_Project
python test_services.py
python status_check.py
```

---

## 🔗 Integraciones

### 📊 Google Sheets

- **Archivo**: `app/utils/gsheet.py`
- **Credenciales**: `app/keys/edp-control-system-f3cfafc0093a.json`

### 🌐 Ngrok (Desarrollo)

- **Script**: `iniciar_ngrok.sh`
- Para exposición externa durante desarrollo

---

## 📝 Próximos Pasos

### 🔥 Crítico

1. **Corregir `manager_controller.py`**
   - Arreglar error de sintaxis en línea del `try:`
   - Añadir import de pandas
   - Verificar funcionalidad de proyectos críticos

### 🚀 Mejoras

2. **Testing End-to-End**

   - Probar carga completa del dashboard
   - Verificar todos los endpoints API
   - Validar renderizado de templates

3. **Documentación Técnica**
   - Documentar APIs en detalle
   - Crear ejemplos de uso
   - Guías de troubleshooting

---

## 🆘 Troubleshooting

### 🐛 Errores Comunes

#### Error de Flask SECRET_KEY

- **Archivo**: `app/config.py`
- **Solución**: Ya está configurado ✅

#### Error en manager_service

- **Archivo**: `app/services/manager_service.py`
- **Estado**: Completamente refactorizado ✅

#### Error en API endpoints

- **Archivo**: `app/controllers/manager_controller.py`
- **Estado**: Necesita corrección ❌

### 📞 Contacto para Soporte

Si encuentras problemas:

1. Revisa los logs en la consola
2. Verifica que todas las dependencias estén instaladas
3. Confirma que la configuración esté correcta

---

**Última actualización**: Junio 4, 2025
**Versión**: MVP 1.0
**Estado**: En desarrollo activo
