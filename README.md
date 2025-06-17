# 🚀 **Pagora - Sistema de Gestión Empresarial**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Flask-3.1+-green.svg" alt="Flask 3.1+">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Status-Production-brightgreen.svg" alt="Production Ready">
</p>

**Pagora** es un **sistema integral de gestión empresarial** especializado en el control, seguimiento y análisis de **EDPs (Estados de Pago)** y **conformidades** en proyectos empresariales. Más que un simple gestor de documentos, es una **plataforma de inteligencia de negocios** que optimiza el flujo de caja y la rentabilidad empresarial.

## 🎯 **¿Para qué sirve Pagora?**

Pagora está diseñado para empresas que necesitan:

- **Control financiero riguroso** de proyectos y facturación
- **Seguimiento detallado** de estados de pago (EDPs)
- **Análisis de rentabilidad** por proyecto, cliente y gestor
- **Optimización del cash flow** empresarial
- **KPIs ejecutivos** para toma de decisiones estratégicas

### 🏢 **Sectores ideales:**

- Empresas de consultoría (IT, ingeniería, legal)
- Contratistas y subcontratistas
- Empresas de servicios profesionales
- Organizaciones que trabajan por proyectos

## ✨ **Características Principales**

### 📊 **Dashboard Ejecutivo Avanzado**

- **KPIs financieros en tiempo real**: Ingresos, DSO, tasa de aprobación
- **Análisis de rentabilidad** por proyecto/cliente/gestor
- **Proyecciones de flujo de caja** y alertas de riesgo
- **Gráficos interactivos** con análisis predictivo

### 🎛️ **Gestión Completa de EDPs**

- **Tablero Kanban** para visualización del proceso
- **Seguimiento automático** del estado (revisión → enviado → aprobado → pagado)
- **Alertas inteligentes** para EDPs críticos o vencidos
- **Gestión de conformidades** con documentos de aprobación

### 📈 **Análisis Avanzados**

- **DSO (Days Sales Outstanding)** - métrica crítica de eficiencia
- **Aging de cuentas por cobrar** (0-30, 31-60, 61-90, +90 días)
- **Análisis OPEX vs CAPEX** por proyecto
- **Identificación automática** de proyectos críticos

### 👥 **Sistema de Roles Empresariales**

- **🎯 Manager/Gerente**: Vista ejecutiva con análisis financiero completo
- **📋 Controller**: Gestión operativa y seguimiento detallado
- **👨‍💼 Jefe de Proyecto**: Vista específica de sus proyectos
- **👤 Usuario**: Registro y consulta básica

### 🔗 **Integraciones**

- **Google Sheets API** para sincronización automática
- **Celery + Redis** para procesamiento asíncrono
- **Flask-Profiler** para monitoreo de rendimiento
- **Flower** para supervisión de colas de trabajo

## 🛠️ **Tecnologías**

- **Backend**: Flask 3.1+ (Python 3.11+)
- **Base de datos**: SQLite/PostgreSQL
- **Cache**: Redis 7+
- **Cola de tareas**: Celery 5.3+
- **Frontend**: HTML5, CSS3, JavaScript moderno
- **UI Framework**: TailwindCSS + DaisyUI
- **Gráficos**: Chart.js
- **API**: Google Sheets API

## 🚀 **Instalación Rápida**

### **Opción 1: Script Automatizado (Recomendado)**

```bash
# Clonar repositorio
git clone https://github.com/Unzzui/EDP_Project.git
cd EDP_Project

# Hacer ejecutable el script
chmod +x start_app.sh

# Iniciar todo automáticamente
./start_app.sh
```

### **Opción 2: Con Docker (Producción)**

```bash
# Iniciar todos los servicios
docker-compose up -d

# URLs disponibles:
# • Pagora: http://localhost:5000
# • Flower: http://localhost:5555
```

### **Opción 3: Con Makefile (Desarrollo)**

```bash
# Setup inicial
make setup

# Iniciar desarrollo
make dev

# Ver todas las opciones
make help
```

### **Opción 4: Manual**

```bash
# 1. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 4. Iniciar Redis
redis-server --daemonize yes

# 5. Iniciar servicios Celery
celery -A edp_mvp.app.celery worker --detach
celery -A edp_mvp.app.celery beat --detach
celery -A edp_mvp.app.celery flower &

# 6. Iniciar Pagora
python run.py
```

## 🔧 **Configuración**

### **Variables de Entorno (.env)**

```bash
# Configuración Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu-clave-secreta-super-segura

# Configuración Redis
REDIS_URL=redis://localhost:6379/0

# Configuración Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Configuración Google Sheets (Opcional)
GOOGLE_CREDENTIALS=/ruta/a/credenciales.json
SHEET_ID=tu_spreadsheet_id

# Base de datos
DATABASE_URL=sqlite:///pagora.db
```

### **Configuración Google Sheets (Opcional)**

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar Google Sheets API
3. Crear credenciales de "Cuenta de servicio"
4. Descargar archivo JSON de credenciales
5. Configurar ruta en `GOOGLE_CREDENTIALS`

## 📊 **URLs de la Aplicación**

Una vez iniciada la aplicación:

| Servicio                 | URL                                     | Descripción                        |
| ------------------------ | --------------------------------------- | ---------------------------------- |
| **Pagora Principal**     | http://localhost:5000                   | Aplicación principal               |
| **Dashboard Manager**    | http://localhost:5000/manager           | Vista ejecutiva                    |
| **Dashboard Controller** | http://localhost:5000/controller        | Vista operativa                    |
| **Kanban Board**         | http://localhost:5000/controller/kanban | Tablero visual                     |
| **Flower (Monitor)**     | http://localhost:5555                   | Monitor de tareas (admin/admin123) |
| **Profiler**             | http://localhost:5000/flask-profiler    | Monitor de rendimiento             |

## 📈 **KPIs y Métricas Principales**

Pagora calcula automáticamente:

- **💰 Ingresos totales** y proyecciones mensuales
- **📅 DSO (Days Sales Outstanding)** - eficiencia de cobros
- **✅ Tasa de aprobación** de EDPs
- **⏰ Aging de cuentas** por cobrar (0-30, 31-60, 61-90, +90 días)
- **💹 Rentabilidad** por proyecto, cliente y gestor
- **🚨 Proyectos críticos** con alta antigüedad
- **💸 Costo financiero** de retrasos en pagos
- **⚡ Eficiencia operacional** del equipo

## 🏗️ **Arquitectura del Sistema**

### **Estructura del Proyecto**

```
pagora/
├── edp_mvp/                 # Código fuente principal
│   ├── app/                 # Aplicación Flask
│   │   ├── controllers/     # Controladores de API
│   │   ├── services/        # Lógica de negocio
│   │   ├── repositories/    # Acceso a datos
│   │   ├── models/          # Modelos de datos
│   │   ├── templates/       # Plantillas HTML
│   │   │   ├── manager/     # Dashboard gerencial
│   │   │   ├── controller/  # Dashboard operativo
│   │   │   └── components/  # Componentes
│   │   └── static/          # CSS, JS, images
│   └── test/                # Tests unitarios
├── requirements.txt         # Dependencias Python
├── docker-compose.yml       # Orquestación Docker
├── Dockerfile              # Imagen Docker
├── Makefile                # Comandos de desarrollo
├── start_app.sh            # Script de inicio
└── README.md               # Esta documentación
```

### **APIs Principales**

#### **API Gerencial**

```
GET  /api/manager/data                    # Datos ejecutivos
GET  /api/manager/kpis                    # KPIs financieros
GET  /api/manager/charts                  # Gráficos de análisis
GET  /api/manager/profitability           # Análisis de rentabilidad
GET  /api/manager/alerts                  # Alertas ejecutivas
```

#### **API Operativa**

```
GET  /api/controller/data                 # Datos operativos
GET  /api/controller/kanban               # Datos del tablero
GET  /api/controller/filters              # Filtros disponibles
POST /api/controller/update-edp           # Actualizar EDP
```

## 🧪 **Testing y Desarrollo**

```bash
# Ejecutar tests
make test

# Linting de código
make lint

# Formatear código
make format

# Verificar estado de servicios
make status

# Limpiar archivos temporales
make clean
```

## 📱 **Capturas de Pantalla**

### Dashboard Ejecutivo

- Vista completa de KPIs financieros
- Gráficos de tendencias y análisis
- Alertas y proyectos críticos

### Tablero Kanban

- Visualización del flujo de EDPs
- Drag & drop para cambios de estado
- Métricas en tiempo real

### Análisis de Rentabilidad

- Rentabilidad por proyecto/cliente
- Análisis OPEX vs CAPEX
- Proyecciones financieras

## 🚀 **Despliegue en Producción**

### **Con Docker (Recomendado)**

```bash
# Configurar variables de producción
cp .env.example .env.production

# Iniciar en producción
docker-compose -f docker-compose.prod.yml up -d
```

### **Servidor tradicional**

```bash
# Usar Gunicorn como servidor WSGI
pip install gunicorn

# Iniciar aplicación
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 🤝 **Contribuir**

1. Fork del repositorio
2. Crear rama para nueva funcionalidad (`git checkout -b feature/nueva-funcion`)
3. Commit de cambios (`git commit -m 'Añadir nueva función'`)
4. Push a la rama (`git push origin feature/nueva-funcion`)
5. Crear Pull Request

## 📝 **Documentación Adicional**

- [📖 Guía Completa del Proyecto](GUIA_COMPLETA_PROYECTO.md)
- [🎯 Contexto Detallado](CONTEXT.md)
- [💰 Guía de Optimización KPI](GUIA_OPTIMIZACION_KPI.md)
- [👥 Gestión de Usuarios](GESTION_USUARIOS.md)
- [🔄 Sistema de Cache](SISTEMA_CACHE_INVALIDACION.md)

## 🆘 **Solución de Problemas**

### **Problemas Comunes**

```bash
# Redis no inicia
sudo systemctl start redis

# Permisos del script
chmod +x start_app.sh

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall

# Limpiar cache
make clean
```

### **Logs de Depuración**

```bash
# Logs de Celery
tail -f /tmp/edp_mvp_*/celery_worker.log

# Logs de Redis
redis-cli monitor

# Estado de servicios
make status
```

## 💼 **Casos de Uso Empresariales**

1. **Director Financiero**: Dashboard ejecutivo para decisiones estratégicas
2. **Controller**: Gestión diaria de EDPs y seguimiento de conformidades
3. **Jefe de Proyecto**: Monitoreo del estado de pago de proyectos específicos
4. **Gerente Comercial**: Análisis de rentabilidad y comportamiento de clientes

## 📊 **Beneficios Empresariales**

- **🔍 Visibilidad total** del flujo de caja
- **⚡ Reducción de EDPs perdidos** o mal gestionados
- **📈 Optimización de la rentabilidad** por proyecto
- **🚨 Alertas proactivas** de riesgos financieros
- **📋 Reportes automáticos** para stakeholders
- **💰 Mejora del DSO** y eficiencia de cobros

## 📄 **Licencia**

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

## 📞 **Soporte y Contacto**

- **Email**: diegobravobe@gmail.com
- **GitHub**: [Unzzui/EDP_Project](https://github.com/Unzzui/EDP_Project)
- **Issues**: [Reportar problemas](https://github.com/Unzzui/EDP_Project/issues)

---

<p align="center">
  <strong>🚀 Desarrollado con ❤️ para optimizar la gestión empresarial</strong>
</p>
