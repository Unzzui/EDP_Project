"""
Endpoint de diagnóstico para verificar estado de Google Sheets en Render
Añadir este código a uno de tus controladores o crear una nueva ruta
"""
from flask import Blueprint, render_template_string
import os
import json

# Blueprint para diagnóstico (opcional)
diag_bp = Blueprint('diagnostic', __name__)

@diag_bp.route('/diagnostic/google-sheets')
def google_sheets_diagnostic():
    """Endpoint para diagnosticar Google Sheets en producción"""
    
    # Template HTML simple para mostrar el diagnóstico
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Diagnóstico Google Sheets</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .warning { background: #fff3cd; color: #856404; }
            .error { background: #f8d7da; color: #721c24; }
            .info { background: #d1ecf1; color: #0c5460; }
            pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🔍 Diagnóstico de Google Sheets</h1>
        
        <h2>📋 Variables de Entorno</h2>
        <div class="info status">
            <strong>GOOGLE_APPLICATION_CREDENTIALS:</strong> {{ google_app_creds }}<br>
            <strong>GOOGLE_CREDENTIALS:</strong> {{ google_creds }}<br>
            <strong>SHEET_ID:</strong> {{ sheet_id }}<br>
            <strong>FLASK_ENV:</strong> {{ flask_env }}
        </div>
        
        <h2>📁 Estado de Archivos</h2>
        {% for file_info in files_status %}
            <div class="{{ file_info.class }} status">
                <strong>{{ file_info.path }}:</strong> {{ file_info.status }}
                {% if file_info.details %}
                    <br><small>{{ file_info.details }}</small>
                {% endif %}
            </div>
        {% endfor %}
        
        <h2>🔧 Estado de Configuración</h2>
        <div class="{{ config_status.class }} status">
            <strong>Configuración:</strong> {{ config_status.message }}
        </div>
        
        <h2>🚀 Estado del Servicio</h2>
        <div class="{{ service_status.class }} status">
            <strong>Google Sheets Service:</strong> {{ service_status.message }}
        </div>
        
        <h2>📊 Test de Datos</h2>
        <div class="{{ data_status.class }} status">
            <strong>Lectura de datos:</strong> {{ data_status.message }}
        </div>
        
        <h2>🕒 Información del Sistema</h2>
        <pre>{{ system_info }}</pre>
        
        <p><small>Generado en: {{ timestamp }}</small></p>
    </body>
    </html>
    """
    
    from datetime import datetime
    import sys
    
    # Obtener información de variables de entorno
    google_app_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'NOT SET')
    google_creds = os.getenv('GOOGLE_CREDENTIALS', 'NOT SET') 
    sheet_id = os.getenv('SHEET_ID', 'NOT SET')
    flask_env = os.getenv('FLASK_ENV', 'NOT SET')
    
    # Verificar estado de archivos
    files_status = []
    credential_paths = [google_app_creds, google_creds]
    
    for path in credential_paths:
        if path != 'NOT SET':
            if os.path.exists(path):
                try:
                    file_size = os.path.getsize(path)
                    
                    # Intentar leer JSON
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    client_email = data.get('client_email', 'N/A')
                    project_id = data.get('project_id', 'N/A')
                    
                    files_status.append({
                        'path': path,
                        'status': f'✅ OK ({file_size} bytes)',
                        'details': f'Client: {client_email}, Project: {project_id}',
                        'class': 'success'
                    })
                except PermissionError:
                    files_status.append({
                        'path': path,
                        'status': '❌ Sin permisos de lectura',
                        'details': 'El archivo existe pero no se puede leer',
                        'class': 'error'
                    })
                except json.JSONDecodeError:
                    files_status.append({
                        'path': path,
                        'status': '❌ JSON inválido',
                        'details': 'El archivo no contiene JSON válido',
                        'class': 'error'
                    })
                except Exception as e:
                    files_status.append({
                        'path': path,
                        'status': f'❌ Error: {e}',
                        'details': None,
                        'class': 'error'
                    })
            else:
                files_status.append({
                    'path': path,
                    'status': '❌ Archivo no existe',
                    'details': None,
                    'class': 'error'
                })
        else:
            files_status.append({
                'path': 'Variable no configurada',
                'status': '⚠️ Variable de entorno vacía',
                'details': None,
                'class': 'warning'
            })
    
    # Test de configuración
    try:
        sys.path.insert(0, '/app')
        from edp_mvp.app.config import get_config
        config = get_config()
        
        google_creds_path = config.GOOGLE_CREDENTIALS
        
        if google_creds_path and os.path.exists(google_creds_path):
            config_status = {
                'message': f'✅ OK - Usando: {google_creds_path}',
                'class': 'success'
            }
        else:
            config_status = {
                'message': f'❌ GOOGLE_CREDENTIALS no válido: {google_creds_path}',
                'class': 'error'
            }
    except Exception as e:
        config_status = {
            'message': f'❌ Error cargando config: {e}',
            'class': 'error'
        }
    
    # Test del servicio
    try:
        from edp_mvp.app.utils.gsheet import get_service
        service = get_service()
        
        if service:
            service_status = {
                'message': '✅ Servicio inicializado correctamente',
                'class': 'success'
            }
        else:
            service_status = {
                'message': '❌ No se pudo inicializar el servicio',
                'class': 'error'
            }
    except Exception as e:
        service_status = {
            'message': f'❌ Error: {e}',
            'class': 'error'
        }
    
    # Test de datos
    try:
        from edp_mvp.app.utils.gsheet import read_sheet
        edp_data = read_sheet("edp!A:V")
        
        if not edp_data.empty:
            data_status = {
                'message': f'✅ Datos leídos correctamente ({len(edp_data)} registros)',
                'class': 'success'
            }
        else:
            data_status = {
                'message': '⚠️ Datos vacíos (modo demo activo)',
                'class': 'warning'
            }
    except Exception as e:
        data_status = {
            'message': f'❌ Error: {e}',
            'class': 'error'
        }
    
    # Información del sistema
    system_info = f"""Usuario: {os.getenv('USER', 'unknown')}
Directorio: {os.getcwd()}
Python: {sys.version}
Variables de entorno importantes:
  RENDER: {os.getenv('RENDER', 'NO')}
  PORT: {os.getenv('PORT', 'NOT SET')}
  DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}
  REDIS_URL: {'SET' if os.getenv('REDIS_URL') else 'NOT SET'}

Directorios relevantes:
  /etc/secrets existe: {os.path.exists('/etc/secrets')}
  /app/secrets existe: {os.path.exists('/app/secrets')}
"""
    
    return render_template_string(template,
        google_app_creds=google_app_creds,
        google_creds=google_creds,
        sheet_id=sheet_id,
        flask_env=flask_env,
        files_status=files_status,
        config_status=config_status,
        service_status=service_status,
        data_status=data_status,
        system_info=system_info,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

# Para añadir a tu aplicación principal:
# app.register_blueprint(diag_bp)
