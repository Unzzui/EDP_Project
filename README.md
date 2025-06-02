# ConformiTrack MVP

## Descripción

ConformiTrack MVP es una aplicación web diseñada para el control y trazabilidad de EDPs (Estados de Pago) y conformidades. Esta versión mínima viable (MVP) proporciona las funcionalidades esenciales para gestionar el seguimiento de conformidades y EDPs en un entorno empresarial.

## Características principales

- Gestión de inventario de EDPs
- Seguimiento de conformidades
- Reportes y estadísticas
- Autenticación de usuarios
- Integración con Google Sheets

## Prerrequisitos

- Python 3.7+
- Pip (gestor de paquetes de Python)
- Cuenta de Google con acceso a Google Sheets API
- Credenciales de Google Cloud Platform

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Unzzui/EDP_Project.git
cd edp_mvp
```

### 2. Crear y activar entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Linux/MacOS
export SECRET_KEY="tu-clave-secreta"
export GOOGLE_CREDENTIALS="/ruta/a/tus/credenciales.json"
export SHEET_ID="tu_spreadsheet_id"

# Windows (CMD)
set SECRET_KEY=tu-clave-secreta
set GOOGLE_CREDENTIALS=C:\ruta\a\tus\credenciales.json
set SHEET_ID=tu_spreadsheet_id
```

También puedes crear un archivo `.env` en la raíz del proyecto:

```
SECRET_KEY=tu-clave-secreta
GOOGLE_CREDENTIALS=/ruta/a/tus/credenciales.json
SHEET_ID=tu_spreadsheet_id
```

## Ejecución

```bash
python run.py
```

La aplicación estará disponible en `http://127.0.0.1:5000/login`

## Estructura del proyecto

```
edp_mvp/
│
├── app/                # Módulos principales de Flask
│   ├── __init__.py     # Inicialización de la aplicación
│   ├── models/         # Modelos de datos
│   ├── routes/         # Rutas y controladores
│   ├── services/       # Servicios y lógica de negocio
│   └── templates/      # Plantillas HTML
│
├── static/             # Archivos estáticos
│   ├── css/            # Hojas de estilo
│   ├── js/             # Scripts de JavaScript
│   └── images/         # Imágenes
│
├── tests/              # Pruebas unitarias y de integración
│
├── .env.example        # Ejemplo de variables de entorno
├── .gitignore          # Archivos ignorados por Git
├── requirements.txt    # Dependencias del proyecto
└── run.py              # Punto de entrada de la aplicación
```

## Configuración de Google Sheets

1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilita la API de Google Sheets
3. Crea credenciales de tipo "Cuenta de servicio"
4. Descarga el archivo JSON de credenciales
5. Configura la ruta al archivo de credenciales en las variables de entorno

## Desarrollo

Para contribuir al proyecto:

1. Crea un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commit (`git commit -m 'Añade nueva funcionalidad'`)
4. Sube tu rama (`git push origin feature/nueva-funcionalidad`)
5. Crea una Pull Request

## Licencia

Este proyecto está licenciado bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.

## Contacto

Para soporte o consultas, contacta a [diegobravobe@gmail.com]
