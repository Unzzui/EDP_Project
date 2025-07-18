"""
EDP Upload Controller - Maneja la carga masiva y manual de EDPs
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, send_file
from flask_login import login_required
from werkzeug.utils import secure_filename
import pandas as pd
import os
import tempfile
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import traceback
import io

from ..services.edp_service import EDPService
from ..repositories.edp_repository import EDPRepository
from ..utils.validation_utils import ValidationUtils
from ..models import EDP
from edp_mvp.app.repositories.project_repository import ProjectRepository
from edp_mvp.app.services.manager_service import ManagerService

# Blueprint
edp_upload_bp = Blueprint('edp_upload', __name__, url_prefix='/upload')

# Services
edp_service = EDPService()
edp_repository = EDPRepository()
project_repository = ProjectRepository()
manager_service = ManagerService()

# Configuración de archivos permitidos
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Caché global para optimizar validación de duplicados
_GLOBAL_EDP_CACHE = {
    'data': {},  # {f"{n_edp}_{proyecto}": True/False}
    'last_update': 0,
    'cache_duration': 300  # 5 minutos
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_edps_cache() -> Dict[str, bool]:
    """Cargar todos los EDPs en caché para validación rápida de duplicados."""
    global _GLOBAL_EDP_CACHE
    current_time = time.time()
    
    # Si el caché es reciente, devolverlo
    if (current_time - _GLOBAL_EDP_CACHE['last_update']) < _GLOBAL_EDP_CACHE['cache_duration']:
        return _GLOBAL_EDP_CACHE['data']
    
    print("🔄 Actualizando caché global de EDPs...")
    start_time = time.time()
    
    try:
        # Obtener todos los EDPs de una vez
        edps_response = edp_repository.find_all()
        if not edps_response.get('success', False):
            print(f"❌ Error obteniendo EDPs: {edps_response.get('message', 'Unknown error')}")
            return {}
        
        edps_list = edps_response.get('data', [])
        cache_data = {}
        
        # Procesar todos los EDPs y crear el caché
        for edp in edps_list:
            try:
                n_edp = str(getattr(edp, 'n_edp', '')).strip()
                proyecto = str(getattr(edp, 'proyecto', '')).strip().upper()
                
                if n_edp and proyecto:
                    cache_key = f"{n_edp}_{proyecto}"
                    cache_data[cache_key] = True
                    
            except Exception as e:
                print(f"⚠️ Error procesando EDP en caché: {str(e)}")
                continue
        
        # Actualizar caché global
        _GLOBAL_EDP_CACHE['data'] = cache_data
        _GLOBAL_EDP_CACHE['last_update'] = current_time
        
        load_time = time.time() - start_time
        print(f"✅ Caché actualizado: {len(cache_data)} EDPs en {load_time:.2f}s")
        
        return cache_data
        
    except Exception as e:
        print(f"❌ Error cargando caché de EDPs: {str(e)}")
        return {}

def check_duplicate_fast(n_edp: int, proyecto: str) -> bool:
    """Verificar duplicados usando caché global (súper rápido)."""
    cache_data = load_edps_cache()
    cache_key = f"{str(n_edp).strip()}_{str(proyecto).strip().upper()}"
    return cache_data.get(cache_key, False)

def find_available_edp_numbers(proyecto: str, start_from: int = None, count: int = 3) -> List[int]:
    """Encontrar números EDP disponibles para un proyecto específico."""
    cache_data = load_edps_cache()
    proyecto_upper = str(proyecto).strip().upper()
    
    # Si no se especifica desde dónde empezar, usar el número más alto + 1
    if start_from is None:
        max_edp = 0
        for cache_key in cache_data.keys():
            if cache_key.endswith(f"_{proyecto_upper}"):
                try:
                    edp_num = int(cache_key.split("_")[0])
                    max_edp = max(max_edp, edp_num)
                except (ValueError, IndexError):
                    continue
        start_from = max_edp + 1
    
    available_numbers = []
    current_num = start_from
    used_in_suggestions = set()  # Evitar duplicados en las sugerencias
    
    # Buscar números disponibles
    while len(available_numbers) < count and current_num < start_from + 1000:  # Límite de seguridad
        cache_key = f"{current_num}_{proyecto_upper}"
        # Verificar que no esté en BD ni ya sugerido
        if not cache_data.get(cache_key, False) and current_num not in used_in_suggestions:
            available_numbers.append(current_num)
            used_in_suggestions.add(current_num)
        current_num += 1
    
    return available_numbers

def get_duplicate_suggestions(df: pd.DataFrame) -> Dict[str, Any]:
    """Analizar duplicados y generar sugerencias para números EDP disponibles."""
    duplicates_info = []
    cache_data = load_edps_cache()
    all_suggested_numbers = set()  # Evitar duplicados globales
    
    # Crear un conjunto de todos los números EDP que están en el archivo actual por proyecto
    current_file_edps = {}  # {proyecto: set(edps)}
    for idx, row in df.iterrows():
        try:
            n_edp = int(row['n_edp'])
            proyecto = str(row['proyecto']).strip().upper()
            
            if proyecto not in current_file_edps:
                current_file_edps[proyecto] = set()
            current_file_edps[proyecto].add(n_edp)
        except (ValueError, TypeError):
            continue
    
    print(f"🔍 EDPs en archivo actual por proyecto: {current_file_edps}")
    
    for idx, row in df.iterrows():
        try:
            n_edp = int(row['n_edp'])
            proyecto = str(row['proyecto']).strip()
            proyecto_upper = proyecto.upper()
            
            if check_duplicate_fast(n_edp, proyecto):
                print(f"🚫 Duplicado encontrado: EDP #{n_edp} para proyecto {proyecto}")
                
                # Encontrar números disponibles para este proyecto
                # Empezar desde el número actual + 1
                available_numbers = []
                current_num = n_edp + 1
                
                # Buscar 3 números únicos disponibles
                while len(available_numbers) < 3 and current_num < n_edp + 1000:
                    cache_key = f"{current_num}_{proyecto_upper}"
                    
                    # Verificar que el número no esté:
                    # 1. En la base de datos
                    # 2. Ya sugerido globalmente
                    # 3. En el archivo actual para el mismo proyecto
                    is_in_db = cache_data.get(cache_key, False)
                    is_already_suggested = current_num in all_suggested_numbers
                    is_in_current_file = current_num in current_file_edps.get(proyecto_upper, set())
                    
                    if not is_in_db and not is_already_suggested and not is_in_current_file:
                        available_numbers.append(current_num)
                        all_suggested_numbers.add(current_num)
                        print(f"✅ Número disponible encontrado: #{current_num} para {proyecto}")
                    else:
                        reasons = []
                        if is_in_db: reasons.append("en BD")
                        if is_already_suggested: reasons.append("ya sugerido")
                        if is_in_current_file: reasons.append("en archivo actual")
                        print(f"❌ Número #{current_num} no disponible ({', '.join(reasons)})")
                    
                    current_num += 1
                
                duplicates_info.append({
                    'row': idx + 2,
                    'current_edp': n_edp,
                    'proyecto': proyecto,
                    'suggested_numbers': available_numbers,
                    'cliente': str(row.get('cliente', '')),
                    'monto': row.get('monto_propuesto', 0)
                })
                
                print(f"🔧 Sugerencias para EDP #{n_edp}: {available_numbers}")
                
        except (ValueError, TypeError):
            continue
    
    print(f"📊 Total duplicados encontrados: {len(duplicates_info)}")
    print(f"📊 Números sugeridos globalmente: {sorted(all_suggested_numbers)}")
    
    return {
        'has_duplicates': len(duplicates_info) > 0,
        'duplicates': duplicates_info,
        'total_duplicates': len(duplicates_info)
    }

@edp_upload_bp.route('/')
@login_required
def upload_page():
    """Página principal de carga de EDPs."""
    return render_template('edp/upload.html')



@edp_upload_bp.route('/template')
@login_required
def download_template():
    """Generar y descargar plantilla de Excel para carga masiva."""
    try:
        # Fechas automáticas
        today = datetime.now()
        fecha_pago = today + timedelta(days=30)
        
        # Crear plantilla con las columnas correctas (campos obligatorios y opcionales)
        template_data = {
            # CAMPOS OBLIGATORIOS
            'n_edp': [1001, 1002],
            'proyecto': ['OT7286', 'OT7287'],
            'cliente': ['Arauco', 'CMPC'],
            'jefe_proyecto': ['Carolina López', 'Juan Pérez'],
            'fecha_emision': [today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')],
            'monto_propuesto': [15491100, 12000000],
            
            # CAMPOS OPCIONALES
            'gestor': ['Juan Pérez', 'María García'],
            'fecha_envio_cliente': ['', ''],  # Se completa cuando se envía
            'monto_aprobado': ['', ''],  # Se completa después de aprobación
            'fecha_estimada_pago': [fecha_pago.strftime('%Y-%m-%d'), fecha_pago.strftime('%Y-%m-%d')],
            'observaciones': ['Proyecto prioritario', 'Pendiente documentación']
        }
        
        df = pd.DataFrame(template_data)
        
        # Asegurar que los montos sean enteros sin decimales
        df['monto_propuesto'] = df['monto_propuesto'].astype(int)
        
        # Crear archivo en memoria
        output = io.BytesIO()
        
        # Usar ExcelWriter para mejor compatibilidad
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Plantilla_EDPs', index=False)
            
            # Obtener el workbook para agregar formato
            workbook = writer.book
            worksheet = writer.sheets['Plantilla_EDPs']
            
            # Formatear columnas de montos como números enteros
            from openpyxl.styles import NamedStyle
            number_style = NamedStyle(name='integer')
            number_style.number_format = '0'
            
            # Aplicar formato a columnas de montos
            for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, 
                                         min_col=6, max_col=6):  # monto_propuesto
                for cell in row:
                    cell.style = number_style
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Crear respuesta con el archivo
        filename = f'plantilla_edp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"Error generando plantilla: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Si falla Excel, intentar CSV como fallback
        try:
            today = datetime.now()
            fecha_pago = today + timedelta(days=30)
            
            template_data = {
                # CAMPOS OBLIGATORIOS
                'n_edp': [1001, 1002],
                'proyecto': ['OT7286', 'OT7287'],
                'cliente': ['Arauco', 'CMPC'],
                'jefe_proyecto': ['Carolina López', 'Juan Pérez'],
                'fecha_emision': [today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')],
                'monto_propuesto': [15491100, 12000000],
                
                # CAMPOS OPCIONALES
                'gestor': ['Juan Pérez', 'María García'],
                'fecha_envio_cliente': ['', ''],  # Se completa cuando se envía
                'monto_aprobado': ['', ''],  # Se completa después de aprobación
                'fecha_estimada_pago': [fecha_pago.strftime('%Y-%m-%d'), fecha_pago.strftime('%Y-%m-%d')],
                'observaciones': ['Proyecto prioritario', 'Pendiente documentación']
            }
            
            df = pd.DataFrame(template_data)
            # Asegurar que los montos sean enteros
            df['monto_propuesto'] = df['monto_propuesto'].astype(int)
            
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            
            filename = f'plantilla_edp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
            
        except Exception as csv_error:
            print(f"Error generando CSV: {str(csv_error)}")
            flash(f'Error generando plantilla: {str(e)}. Detalles: {str(csv_error)}', 'error')
            return redirect(url_for('edp_upload.upload_page'))

@edp_upload_bp.route('/manual', methods=['GET', 'POST'])
@login_required
def manual_upload():
    """Carga manual de un EDP individual."""
    if request.method == 'GET':
        return render_template('edp/manual_upload.html')
    
    try:
        print("🔍 Iniciando carga manual de EDP...")
        
        # Obtener datos del formulario
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        print(f"📋 Datos recibidos: {form_data}")
        
        # Agregar usuario actual
        form_data['registrado_por'] = session.get('user', 'admin')
        form_data['fecha_registro'] = datetime.now().isoformat()
        
        # Validar datos básicos primero
        print("🔍 Validando datos del EDP...")
        validation_result = validate_edp_data(form_data)
        if not validation_result['valid']:
            print(f"❌ Validación fallida: {validation_result['errors']}")
            return jsonify({
                'success': False,
                'errors': validation_result['errors']
            }), 400
        
        print("✅ Validación exitosa")
        
        # Preparar datos del EDP
        print("🔧 Preparando datos del EDP...")
        edp_data = prepare_edp_data(form_data)
        print(f"📋 Datos preparados: {edp_data}")
        
        # Crear modelo EDP
        print("🏗️ Creando modelo EDP...")
        edp = EDP.from_dict(edp_data)
        print(f"✅ Modelo EDP creado: n_edp={edp.n_edp}, proyecto={edp.proyecto}")
        
        # Guardar en repositorio
        print("💾 Guardando en repositorio...")
        edp_id = edp_repository.create(edp)
        print(f"✅ EDP guardado con ID: {edp_id}")
        
        # Limpiar caché de EDPs para que la próxima validación sea actualizada
        print("🧹 Limpiando caché...")
        global _GLOBAL_EDP_CACHE
        _GLOBAL_EDP_CACHE['data'] = {}
        _GLOBAL_EDP_CACHE['last_update'] = 0
        
        response_data = {
            'success': True,
            'message': f'EDP {edp.n_edp} creado exitosamente',
            'edp_id': edp_id
        }
        print(f"✅ Respuesta exitosa: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error en manual_upload: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error creando EDP: {str(e)}',
            'details': str(e)  # Agregar detalles para debug
        }), 500

@edp_upload_bp.route('/bulk', methods=['POST'])
@login_required
def bulk_upload():
    """Carga masiva de EDPs desde archivo Excel/CSV."""
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        # Verificar extensión y tamaño
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Tipo de archivo no permitido. Use .xlsx, .xls o .csv'
            }), 400
        
        # Leer archivo
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error leyendo archivo: {str(e)}'
            }), 400
        
        # Validar estructura del archivo
        validation_result = validate_bulk_data(df)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'message': 'Estructura de archivo inválida',
                'errors': validation_result['errors']
            }), 400
        
        # Procesar datos en lotes para mejor rendimiento
        results = process_bulk_upload(df, session.get('user', 'admin'))
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error procesando archivo: {str(e)}'
        }), 500

@edp_upload_bp.route('/validate-progress/<validation_id>')
@login_required
def get_validation_progress(validation_id):
    """Obtener progreso de validación en tiempo real."""
    # Esto sería para implementar validación asíncrona con progreso
    # Por ahora, devolvemos progreso simulado
    return jsonify({
        'success': True,
        'progress': 100,
        'message': 'Validación completada',
        'status': 'completed'
    })

@edp_upload_bp.route('/validate', methods=['POST'])
@login_required
def validate_file():
    """Validar archivo antes de la carga masiva."""
    try:
        print("🔍 Iniciando validación de archivo...")
        
        if 'file' not in request.files:
            print("❌ No se encontró archivo en la request")
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        file = request.files['file']
        print(f"📁 Archivo recibido: {file.filename}")
        
        if not allowed_file(file.filename):
            print(f"❌ Tipo de archivo no permitido: {file.filename}")
            return jsonify({
                'success': False,
                'message': 'Tipo de archivo no permitido. Use .xlsx, .xls o .csv'
            }), 400
        
        print(f"✅ Tipo de archivo válido: {file.filename}")
        
        # Leer archivo
        try:
            print("📖 Leyendo archivo...")
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
                print(f"📊 CSV leído exitosamente: {df.shape}")
            else:
                df = pd.read_excel(file)
                print(f"📊 Excel leído exitosamente: {df.shape}")
            
            print(f"📋 Columnas encontradas: {list(df.columns)}")
            
        except Exception as read_error:
            print(f"❌ Error leyendo archivo: {str(read_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error leyendo archivo: {str(read_error)}. Verifique que el archivo no esté corrupto y tenga el formato correcto.'
            }), 400
        
        # Validar estructura y datos
        try:
            print("🔍 Validando estructura y datos...")
            validation_result = validate_bulk_data(df, preview_mode=True)
            print(f"✅ Validación completada: {validation_result.get('valid', False)}")
            
        except Exception as validation_error:
            print(f"❌ Error en validación: {str(validation_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error validando datos: {str(validation_error)}'
            }), 400
        
        # Generar preview de los primeros 5 registros
        try:
            print("👀 Generando preview...")
            # Reemplazar NaN con None para JSON válido
            df_preview = df.head(5).fillna('')  # Reemplazar NaN con string vacío
            preview_data = df_preview.to_dict('records')
            print(f"📋 Preview generado con {len(preview_data)} registros")
            
        except Exception as preview_error:
            print(f"❌ Error generando preview: {str(preview_error)}")
            preview_data = []
        
        response_data = {
            'success': validation_result['valid'],
            'validation': validation_result,
            'preview': preview_data,
            'total_rows': len(df),
            'columns': list(df.columns),
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', []),
            'suggestions': validation_result.get('suggestions')
        }
        
        print(f"✅ Respuesta preparada: success={response_data['success']}")
        if validation_result.get('suggestions'):
            print(f"💡 Sugerencias incluidas: {validation_result['suggestions']['total_duplicates']} duplicados")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"💥 Error general en validate_file: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error inesperado validando archivo: {str(e)}'
        }), 500


@edp_upload_bp.route('/debug/check-edps', methods=['GET'])
@login_required
def debug_check_edps():
    """Endpoint de debug para verificar el estado actual de los EDPs en la BD."""
    try:
        print("🔍 DEBUG: Verificando estado actual de EDPs en BD...")
        
        # Obtener todos los EDPs
        edps_response = edp_repository.find_all()
        if not edps_response.get('success', False):
            return jsonify({
                'success': False,
                'message': f'Error obteniendo EDPs: {edps_response.get("message", "Unknown error")}'
            }), 500
        
        edps_list = edps_response.get('data', [])
        
        # Procesar información de EDPs
        edps_info = []
        for edp in edps_list:
            try:
                edp_info = {
                    'edp_id': getattr(edp, 'edp_id', 'N/A'),
                    'n_edp': getattr(edp, 'n_edp', 'N/A'),
                    'proyecto': getattr(edp, 'proyecto', 'N/A'),
                    'cliente': getattr(edp, 'cliente', 'N/A'),
                    'estado': getattr(edp, 'estado', 'N/A'),
                    'fecha_registro': getattr(edp, 'fecha_registro', 'N/A')
                }
                edps_info.append(edp_info)
            except Exception as e:
                print(f"⚠️ Error procesando EDP: {str(e)}")
                continue
        
        # Buscar duplicados potenciales
        duplicates = {}
        for edp in edps_info:
            key = f"{edp['n_edp']}_{edp['proyecto']}"
            if key in duplicates:
                duplicates[key].append(edp)
            else:
                duplicates[key] = [edp]
        
        # Filtrar solo los que tienen duplicados
        actual_duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}
        
        return jsonify({
            'success': True,
            'total_edps': len(edps_list),
            'edps_info': edps_info,
            'duplicates_found': actual_duplicates,
            'duplicates_count': len(actual_duplicates)
        })
        
    except Exception as e:
        print(f"❌ Error en debug_check_edps: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@edp_upload_bp.route('/apply-suggestions', methods=['POST'])
@login_required
def apply_suggestions():
    """Aplicar sugerencias de números EDP y generar archivo corregido."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No se encontró archivo'}), 400
        
        file = request.files['file']
        suggestions_data = request.form.get('suggestions')
        
        if not suggestions_data:
            return jsonify({'success': False, 'message': 'No se encontraron sugerencias'}), 400
        
        import json
        suggestions = json.loads(suggestions_data)
        
        # Leer archivo original
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({'success': False, 'message': 'Formato de archivo no soportado'}), 400
        
        # Aplicar correcciones
        corrections_applied = 0
        for suggestion in suggestions.get('duplicates', []):
            row_idx = suggestion['row'] - 2  # Convertir a índice 0-based
            if row_idx < len(df) and suggestion['suggested_numbers']:
                # Usar el primer número sugerido
                new_edp = suggestion['suggested_numbers'][0]
                df.iloc[row_idx, df.columns.get_loc('n_edp')] = new_edp
                corrections_applied += 1
        
        # Generar archivo corregido
        output = io.BytesIO()
        if file.filename.endswith('.xlsx'):
            df.to_excel(output, index=False, engine='openpyxl')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension = '.xlsx'
        else:
            df.to_csv(output, index=False)
            mimetype = 'text/csv'
            extension = '.csv'
        
        output.seek(0)
        
        # Generar nombre de archivo
        original_name = file.filename.rsplit('.', 1)[0]
        corrected_filename = f"{original_name}_corregido{extension}"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=corrected_filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        print(f"Error aplicando sugerencias: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error aplicando sugerencias: {str(e)}'
        }), 500

@edp_upload_bp.route('/apply-suggestions-and-process', methods=['POST'])
@login_required
def apply_suggestions_and_process():
    """Aplicar sugerencias automáticamente y procesar el archivo sin descarga."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No se encontró archivo'}), 400
        
        file = request.files['file']
        suggestions_data = request.form.get('suggestions')
        
        if not suggestions_data:
            return jsonify({'success': False, 'message': 'No se encontraron sugerencias'}), 400
        
        import json
        suggestions = json.loads(suggestions_data)
        
        print(f"🔧 Aplicando sugerencias automáticamente para {len(suggestions.get('duplicates', []))} duplicados")
        
        # Leer archivo original
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({'success': False, 'message': 'Formato de archivo no soportado'}), 400
        
        # Aplicar correcciones automáticamente
        corrections_applied = 0
        correction_details = []
        
        for suggestion in suggestions.get('duplicates', []):
            row_idx = suggestion['row'] - 2  # Convertir a índice 0-based
            if row_idx < len(df) and suggestion['suggested_numbers']:
                # Usar el primer número sugerido
                old_edp = suggestion['current_edp']
                new_edp = suggestion['suggested_numbers'][0]
                
                df.iloc[row_idx, df.columns.get_loc('n_edp')] = new_edp
                corrections_applied += 1
                
                correction_details.append({
                    'row': suggestion['row'],
                    'proyecto': suggestion['proyecto'],
                    'old_edp': old_edp,
                    'new_edp': new_edp
                })
                
                print(f"✅ Fila {suggestion['row']}: EDP #{old_edp} → #{new_edp} (Proyecto: {suggestion['proyecto']})")
        
        print(f"🔧 Total correcciones aplicadas: {corrections_applied}")
        
        # Procesar el archivo corregido directamente
        from flask_login import current_user
        user_email = current_user.email if current_user and hasattr(current_user, 'email') else 'sistema'
        
        print("🚀 Procesando archivo corregido automáticamente...")
        result = process_bulk_upload(df, user_email)
        
        # Agregar información de correcciones al resultado
        result['corrections_applied'] = corrections_applied
        result['correction_details'] = correction_details
        
        # Limpiar caché después del procesamiento exitoso
        if result.get('success') and result.get('stats', {}).get('success_count', 0) > 0:
            print("🧹 Limpiando caché de EDPs después del procesamiento exitoso...")
            global _GLOBAL_EDP_CACHE
            _GLOBAL_EDP_CACHE['data'] = {}
            _GLOBAL_EDP_CACHE['last_update'] = 0
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error aplicando sugerencias y procesando: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error aplicando sugerencias: {str(e)}'
        }), 500

@edp_upload_bp.route('/clear-edp-cache', methods=['POST'])
@login_required
def clear_edp_cache():
    """Limpiar caché de EDPs para forzar actualización."""
    global _GLOBAL_EDP_CACHE
    _GLOBAL_EDP_CACHE['data'] = {}
    _GLOBAL_EDP_CACHE['last_update'] = 0
    
    return jsonify({
        'success': True,
        'message': 'Caché de EDPs limpiado exitosamente'
    })

@edp_upload_bp.route('/debug/clear-cache', methods=['POST'])
@login_required
def clear_cache():
    """Endpoint para limpiar el caché y forzar recarga desde BD."""
    try:
        print("🧹 DEBUG: Limpiando caché...")
        
        # Importar y usar el servicio de invalidación de caché
        from ..services.cache_invalidation_service import CacheInvalidationService
        
        cache_service = CacheInvalidationService()
        
        # Invalidar todo el caché
        result = cache_service.force_invalidate_all()
        
        if result.get('success'):
            print(f"✅ Caché limpiado exitosamente: {result.get('total_invalidated', 0)} entradas eliminadas")
            return jsonify({
                'success': True,
                'message': f'Caché limpiado exitosamente: {result.get("total_invalidated", 0)} entradas eliminadas',
                'details': result
            })
        else:
            print(f"⚠️ Error limpiando caché: {result.get('message', 'Unknown error')}")
            return jsonify({
                'success': False,
                'message': f'Error limpiando caché: {result.get("message", "Unknown error")}',
                'details': result
            }), 500
        
    except Exception as e:
        print(f"❌ Error limpiando caché: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



# === FUNCIONES AUXILIARES ===

def validate_edp_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar datos de un EDP individual."""
    errors = []
    
    print(f"🔍 Iniciando validación de datos EDP...")
    print(f"📋 Datos a validar: {data}")
    
    # Validaciones obligatorias
    required_fields = ['n_edp', 'proyecto', 'cliente', 'jefe_proyecto', 'fecha_emision', 'monto_propuesto']
    
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == '':
            errors.append(f'El campo {field} es obligatorio')
            print(f"❌ Campo obligatorio faltante: {field}")
    
    # Validar número EDP
    if 'n_edp' in data and data['n_edp']:
        try:
            n_edp = int(float(str(data['n_edp'])))
            if n_edp <= 0:
                errors.append('El número EDP debe ser positivo')
                print(f"❌ n_edp debe ser positivo: {n_edp}")
            else:
                # Validar que no exista EDP con mismo número para el mismo proyecto
                if 'proyecto' in data and data['proyecto']:
                    print(f"🔍 Validando duplicado: EDP #{n_edp} para proyecto '{data['proyecto']}'")
                    try:
                        is_duplicate = check_duplicate_fast(n_edp, data['proyecto'])
                        if is_duplicate:
                            errors.append(f'Ya existe EDP #{n_edp} para el proyecto {data["proyecto"]}')
                            print(f"🚫 Duplicado encontrado: EDP #{n_edp} para proyecto {data['proyecto']}")
                        else:
                            print(f"✅ EDP #{n_edp} es único para proyecto {data['proyecto']}")
                    except Exception as dup_error:
                        print(f"⚠️ Error verificando duplicados: {str(dup_error)}")
                        # No bloquear si hay error en verificación
        except (ValueError, TypeError):
            errors.append('El número EDP debe ser un número válido')
            print(f"❌ n_edp formato inválido: {data.get('n_edp')}")
    
    # Validar fecha de emisión
    if 'fecha_emision' in data and data['fecha_emision']:
        try:
            fecha_str = str(data['fecha_emision']).strip()
            datetime.strptime(fecha_str, '%Y-%m-%d')
            print(f"✅ fecha_emision válida: {fecha_str}")
        except (ValueError, TypeError):
            errors.append('La fecha de emisión debe tener formato YYYY-MM-DD')
            print(f"❌ fecha_emision formato inválido: {data.get('fecha_emision')}")
    
    # Validar monto propuesto
    if 'monto_propuesto' in data and data['monto_propuesto']:
        try:
            monto_str = str(data['monto_propuesto']).replace(',', '').replace(' ', '')
            monto = float(monto_str)
            if monto <= 0:
                errors.append('El monto propuesto debe ser mayor a 0')
                print(f"❌ monto_propuesto debe ser positivo: {monto}")
            else:
                print(f"✅ monto_propuesto válido: {monto}")
        except (ValueError, TypeError):
            errors.append('El monto propuesto debe ser un número válido')
            print(f"❌ monto_propuesto formato inválido: {data.get('monto_propuesto')}")
    
    # Validar monto aprobado si está presente
    if 'monto_aprobado' in data and data['monto_aprobado'] and str(data['monto_aprobado']).strip() != '' and str(data['monto_aprobado']).strip().lower() != 'nan':
        try:
            monto_str = str(data['monto_aprobado']).replace(',', '').replace(' ', '')
            monto_aprobado = float(monto_str)
            if monto_aprobado <= 0:
                errors.append('El monto aprobado debe ser mayor a 0')
                print(f"❌ monto_aprobado debe ser positivo: {monto_aprobado}")
            else:
                print(f"✅ monto_aprobado válido: {monto_aprobado}")
        except (ValueError, TypeError):
            errors.append('El monto aprobado debe ser un número válido')
            print(f"❌ monto_aprobado formato inválido: {data.get('monto_aprobado')}")
    
    # Validar fechas opcionales (solo si tienen valor)
    date_fields = ['fecha_envio_cliente', 'fecha_estimada_pago']
    for field in date_fields:
        if field in data and data[field] and str(data[field]).strip() != '' and str(data[field]).strip().lower() != 'nan':
            try:
                fecha_str = str(data[field]).strip()
                # Intentar varios formatos de fecha
                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                fecha_parsed = None
                for fmt in date_formats:
                    try:
                        fecha_parsed = datetime.strptime(fecha_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if fecha_parsed is None:
                    errors.append(f'El campo {field} debe tener formato YYYY-MM-DD, DD/MM/YYYY o MM/DD/YYYY')
                    print(f"❌ {field} formato inválido: {fecha_str}")
                else:
                    print(f"✅ {field} válido: {fecha_str}")
            except (ValueError, TypeError):
                errors.append(f'El campo {field} no es una fecha válida')
                print(f"❌ {field} no es fecha válida: {data.get(field)}")
    
    # Validar campos de texto obligatorios
    text_fields = ['proyecto', 'cliente', 'jefe_proyecto']
    for field in text_fields:
        if field in data and data[field]:
            value = str(data[field]).strip()
            if len(value) < 2:
                errors.append(f'El campo {field} debe tener al menos 2 caracteres')
                print(f"❌ {field} muy corto: {value}")
            elif len(value) > 100:
                errors.append(f'El campo {field} no puede exceder 100 caracteres')
                print(f"❌ {field} muy largo: {len(value)} caracteres")
            else:
                print(f"✅ {field} válido: {value}")
    
    validation_result = {
        'valid': len(errors) == 0,
        'errors': errors
    }
    
    print(f"🎯 Resultado validación: valid={validation_result['valid']}, errores={len(errors)}")
    if errors:
        print(f"❌ Errores encontrados: {errors}")
    
    return validation_result

def check_duplicate_edp(n_edp: int, proyecto: str, force_refresh: bool = True) -> bool:
    """Verificar si ya existe un EDP con el mismo número para el mismo proyecto."""
    try:
        # Normalizar datos para comparación
        n_edp_str = str(n_edp).strip()
        proyecto_str = str(proyecto).strip().upper()
        
        print(f"🔍 Verificando duplicado: EDP #{n_edp_str} para proyecto '{proyecto_str}' (force_refresh={force_refresh})")
        
        # Forzar actualización desde BD sin caché
        if force_refresh:
            print("🔄 Forzando actualización desde BD (sin caché)...")
            try:
                # Limpiar caché antes de consultar
                from ..services.cache_invalidation_service import CacheInvalidationService
                cache_service = CacheInvalidationService()
                
                # 1. Invalidar caché general del dashboard
                result = cache_service.force_invalidate_all()
                if result.get('success'):
                    print(f"✅ Caché general invalidado: {result.get('total_invalidated', 0)} entradas eliminadas")
                else:
                    print(f"⚠️ Error invalidando caché general: {result.get('message', 'Unknown error')}")
                
                # 2. Limpiar específicamente el caché de Google Sheets
                if cache_service.redis_client:
                    try:
                        # Limpiar caché específico de la hoja EDP
                        keys_to_delete = []
                        gsheet_keys = cache_service.redis_client.keys("gsheet:edp!*")
                        if gsheet_keys:
                            keys_to_delete.extend(gsheet_keys)
                        
                        # También limpiar caché en memoria
                        from ..utils.supabase_adapter import clear_all_cache
                        clear_all_cache()
                        
                        if keys_to_delete:
                            deleted = cache_service.redis_client.delete(*keys_to_delete)
                            print(f"✅ Caché de Google Sheets invalidado: {deleted} claves eliminadas")
                        else:
                            print("ℹ️ No se encontraron claves de caché de Google Sheets para eliminar")
                            
                    except Exception as gsheet_error:
                        print(f"⚠️ Error limpiando caché de Google Sheets: {str(gsheet_error)}")
                else:
                    print("⚠️ Redis no disponible para limpiar caché de Google Sheets")
                    
            except Exception as cache_error:
                print(f"⚠️ No se pudo limpiar caché: {str(cache_error)}")
        
        # Usar find_all en lugar de find_all_dataframe para obtener modelos EDP
        # Pasar parámetro para evitar caché si está disponible
        edps_response = edp_repository.find_all()
        if not edps_response.get('success', False):
            print(f"❌ Error obteniendo EDPs: {edps_response.get('message', 'Unknown error')}")
            print("⚠️ No se puede verificar duplicados, permitiendo creación")
            return False
            
        # El 'data' es una lista de objetos EDP
        edps_list = edps_response.get('data', [])
        
        if not edps_list:
            print(f"✅ No hay EDPs en la base de datos, EDP #{n_edp_str} es único")
            return False
        
        print(f"📊 Total EDPs encontrados en BD: {len(edps_list)}")
        
        # Log de algunos EDPs para debug
        print("🔍 Debug - Primeros 3 EDPs en BD:")
        for i, edp in enumerate(edps_list[:3]):
            try:
                debug_n_edp = getattr(edp, 'n_edp', 'N/A')
                debug_proyecto = getattr(edp, 'proyecto', 'N/A')
                debug_id = getattr(edp, 'edp_id', 'N/A')
                print(f"   {i+1}. EDP #{debug_n_edp} - Proyecto: {debug_proyecto} - ID: {debug_id}")
            except Exception as debug_error:
                print(f"   {i+1}. Error obteniendo datos: {debug_error}")
        
        # Iterar sobre los objetos EDP
        duplicates_found = []
        for edp in edps_list:
            try:
                # Acceder a los atributos del objeto EDP
                existing_n_edp = str(getattr(edp, 'n_edp', '')).strip()
                existing_proyecto = str(getattr(edp, 'proyecto', '')).strip().upper()
                existing_id = getattr(edp, 'edp_id', 'N/A')
                
                # Comparación exacta con normalización
                if existing_n_edp == n_edp_str and existing_proyecto == proyecto_str:
                    duplicates_found.append({
                        'edp_id': existing_id,
                        'n_edp': existing_n_edp,
                        'proyecto': existing_proyecto
                    })
                    print(f"🚫 DUPLICADO ENCONTRADO: EDP #{n_edp} (ID: {existing_id}) ya existe para proyecto {proyecto}")
                    
            except Exception as edp_error:
                print(f"⚠️ Error procesando EDP: {str(edp_error)}")
                continue
        
        if duplicates_found:
            print(f"🚫 Total duplicados encontrados: {len(duplicates_found)}")
            for dup in duplicates_found:
                print(f"   - EDP #{dup['n_edp']} (ID: {dup['edp_id']}) en proyecto {dup['proyecto']}")
            return True
        else:
            print(f"✅ EDP #{n_edp} para proyecto {proyecto} es único")
            return False
        
    except Exception as e:
        print(f"❌ Error verificando duplicados: {str(e)}")
        import traceback
        traceback.print_exc()
        print("⚠️ Error en verificación de duplicados, permitiendo creación por seguridad")
        # En caso de error, ser conservador y NO bloquear la creación
        return False

def validate_bulk_data(df: pd.DataFrame, preview_mode: bool = False) -> Dict[str, Any]:
    """Validar estructura y contenido del archivo para carga masiva."""
    try:
        print("🔍 Iniciando validate_bulk_data...")
        errors = []
        warnings = []
        
        # Caché temporal para duplicados durante esta validación
        duplicate_cache = {}
        
        # Pre-cargar caché global para máximo rendimiento
        print("🚀 Pre-cargando caché de EDPs para validación rápida...")
        cache_start = time.time()
        load_edps_cache()  # Esto carga el caché global si es necesario
        cache_time = time.time() - cache_start
        print(f"⚡ Caché listo en {cache_time:.2f}s")
        
        # Verificar que el DataFrame no esté vacío
        if df.empty:
            print("❌ DataFrame está vacío")
            errors.append('El archivo está vacío')
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        print(f"📊 DataFrame shape: {df.shape}")
        print(f"📋 Columnas originales: {list(df.columns)}")
        
        # Limpiar nombres de columnas
        df_work = df.copy()  # Crear una copia para trabajar
        df_work.columns = df_work.columns.str.strip().str.lower()
        print(f"📋 Columnas después de limpiar: {list(df_work.columns)}")
        
        # Columnas obligatorias
        required_columns = ['n_edp', 'proyecto', 'cliente', 'jefe_proyecto', 'fecha_emision', 'monto_propuesto']
        
        # Verificar columnas obligatorias
        missing_columns = [col for col in required_columns if col not in df_work.columns]
        if missing_columns:
            print(f"❌ Faltan columnas: {missing_columns}")
            errors.append(f'Faltan las siguientes columnas obligatorias: {", ".join(missing_columns)}')
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        print("✅ Todas las columnas obligatorias están presentes")
        
        # Validar que no hay filas completamente vacías
        df_clean = df_work.dropna(how='all').copy()
        if df_clean.empty:
            print("❌ No hay datos válidos después de limpiar")
            errors.append('No hay datos válidos en el archivo')
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        print(f"📊 Filas válidas después de limpiar: {len(df_clean)}")
        
        # Limpiar y normalizar datos
        try:
            print("🧹 Limpiando y normalizando datos...")
            
            # Reemplazar NaN con valores apropiados antes de procesar
            df_clean = df_clean.fillna({
                'fecha_envio_cliente': '',
                'monto_aprobado': '',
                'observaciones': '',
                'gestor': ''
            })
            
            # Asegurar que los montos sean enteros sin decimales
            for idx in df_clean.index:
                try:
                    if pd.notna(df_clean.at[idx, 'monto_propuesto']) and str(df_clean.at[idx, 'monto_propuesto']).strip() != '':
                        monto_str = str(df_clean.at[idx, 'monto_propuesto']).replace(',', '').replace(' ', '')
                        monto = float(monto_str)
                        df_clean.at[idx, 'monto_propuesto'] = int(monto)
                except Exception as e:
                    print(f"⚠️ Error procesando monto_propuesto en fila {idx}: {e}")
                
                if 'monto_aprobado' in df_clean.columns:
                    try:
                        monto_aprobado = df_clean.at[idx, 'monto_aprobado']
                        if pd.notna(monto_aprobado) and str(monto_aprobado).strip() != '':
                            monto_str = str(monto_aprobado).replace(',', '').replace(' ', '')
                            if monto_str:  # Solo si no está vacío
                                monto = float(monto_str)
                                df_clean.at[idx, 'monto_aprobado'] = int(monto)
                            else:
                                df_clean.at[idx, 'monto_aprobado'] = ''
                        else:
                            df_clean.at[idx, 'monto_aprobado'] = ''
                    except Exception as e:
                        print(f"⚠️ Error procesando monto_aprobado en fila {idx}: {e}")
                        df_clean.at[idx, 'monto_aprobado'] = ''
            
            print("✅ Datos limpiados y normalizados")
            
        except Exception as clean_error:
            print(f"❌ Error limpiando datos: {str(clean_error)}")
            # Continuar con validación sin la limpieza
        
        # Validaciones por fila
        print("🔍 Iniciando validaciones por fila...")
        print(f"🔍 Validando duplicados en BD para {len(df_clean)} filas...")
        row_errors = []
        duplicate_checks = []  # Para verificar duplicados
        
        for idx, row in df_clean.iterrows():
            row_error = []
            
            # Validar campos obligatorios
            for field in required_columns:
                if pd.isna(row[field]) or str(row[field]).strip() == '':
                    row_error.append(f'Fila {idx + 2}: El campo {field} es obligatorio')
            
            # Validar número EDP
            try:
                n_edp = int(row['n_edp'])
                if n_edp <= 0:
                    row_error.append(f'Fila {idx + 2}: El número EDP debe ser positivo')
                else:
                    # Verificar duplicados dentro del mismo archivo
                    proyecto = str(row['proyecto']).strip()
                    edp_key = f"{n_edp}_{proyecto}"
                    if edp_key in duplicate_checks:
                        row_error.append(f'Fila {idx + 2}: EDP #{n_edp} duplicado para proyecto {proyecto}')
                    else:
                        duplicate_checks.append(edp_key)
                        # SIEMPRE verificar duplicados en BD, incluso en preview (súper rápido)
                        if check_duplicate_fast(n_edp, proyecto):
                            row_error.append(f'Fila {idx + 2}: Ya existe EDP #{n_edp} para proyecto {proyecto}')
            except (ValueError, TypeError):
                row_error.append(f'Fila {idx + 2}: El número EDP debe ser un número válido')
            
            # Validar montos
            try:
                monto_str = str(row['monto_propuesto']).replace(',', '').replace(' ', '')
                monto = float(monto_str)
                if monto <= 0:
                    row_error.append(f'Fila {idx + 2}: El monto propuesto debe ser mayor a 0')
            except (ValueError, TypeError):
                row_error.append(f'Fila {idx + 2}: El monto propuesto debe ser un número válido')
            
            # Validar fecha de emisión
            try:
                fecha_str = str(row['fecha_emision']).strip()
                # Intentar varios formatos de fecha
                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                fecha_parsed = None
                for fmt in date_formats:
                    try:
                        fecha_parsed = datetime.strptime(fecha_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if fecha_parsed is None:
                    row_error.append(f'Fila {idx + 2}: La fecha de emisión debe tener formato YYYY-MM-DD, DD/MM/YYYY o MM/DD/YYYY')
            except (ValueError, TypeError):
                row_error.append(f'Fila {idx + 2}: La fecha de emisión no es válida')
            
            row_errors.extend(row_error)
        
        print(f"📊 Total errores encontrados: {len(row_errors)}")
        errors.extend(row_errors)
        
        # En modo preview, limitar errores mostrados
        if preview_mode and len(errors) > 10:
            errors = errors[:10]
            warnings.append('Se muestran solo los primeros 10 errores. Corrija estos para ver más.')
        
        # Si hay errores de duplicados, generar sugerencias
        suggestions = None
        if len(errors) > 0 and any('Ya existe EDP' in str(error) for error in errors):
            print("🔍 Generando sugerencias para EDPs duplicados...")
            suggestions = get_duplicate_suggestions(df_clean)
        
        result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_rows': len(df_clean),
            'suggestions': suggestions
        }
        
        print(f"✅ Validación completada: valid={result['valid']}, errores={len(errors)}")
        if suggestions and suggestions['has_duplicates']:
            print(f"💡 Generadas sugerencias para {suggestions['total_duplicates']} duplicados")
        
        return result
        
    except Exception as e:
        print(f"💥 Error en validate_bulk_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'valid': False,
            'errors': [f'Error interno validando datos: {str(e)}'],
            'warnings': [],
            'total_rows': 0
        }

def prepare_edp_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Preparar datos del EDP para creación, agregando campos automáticos."""
    import pandas as pd
    
    print(f"🔧 Iniciando preparación de datos EDP...")
    print(f"📋 Form data recibido: {form_data}")
    
    # Procesar n_edp - convertir a string (como espera Supabase)
    n_edp_value = form_data.get('n_edp')
    if pd.isna(n_edp_value) if hasattr(pd, 'isna') else n_edp_value is None:
        raise ValueError("El número EDP no puede estar vacío")
    
    try:
        # Convertir a entero primero para validar, luego a string para Supabase
        n_edp_int = int(float(str(n_edp_value)))
        if n_edp_int <= 0:
            raise ValueError("El número EDP debe ser positivo")
        n_edp_final = str(n_edp_int)
        print(f"✅ n_edp procesado: {n_edp_value} → {n_edp_final}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"El número EDP debe ser un número válido: {e}")
    
    # Limpiar y convertir montos a float
    monto_propuesto = form_data.get('monto_propuesto', 0)
    if isinstance(monto_propuesto, str):
        monto_propuesto = monto_propuesto.replace(',', '').replace(' ', '')
    try:
        monto_propuesto = float(monto_propuesto) if monto_propuesto else 0.0
        if monto_propuesto <= 0:
            raise ValueError("El monto propuesto debe ser mayor a 0")
        print(f"✅ monto_propuesto procesado: {monto_propuesto}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Monto propuesto inválido: {e}")
    
    monto_aprobado = form_data.get('monto_aprobado')
    if monto_aprobado and str(monto_aprobado).strip() and str(monto_aprobado).strip().lower() != 'nan':
        if isinstance(monto_aprobado, str):
            monto_aprobado = monto_aprobado.replace(',', '').replace(' ', '')
        try:
            monto_aprobado = float(monto_aprobado)
            print(f"✅ monto_aprobado procesado: {monto_aprobado}")
        except (ValueError, TypeError):
            print("⚠️ monto_aprobado inválido, estableciendo como None")
            monto_aprobado = None
    else:
        monto_aprobado = None
        print("✅ monto_aprobado establecido como None (vacío)")
    
    # Procesar fecha de emisión y generar mes
    try:
        fecha_emision_str = str(form_data['fecha_emision'])
        fecha_emision_dt = datetime.strptime(fecha_emision_str, '%Y-%m-%d')
        mes = fecha_emision_dt.strftime('%Y-%m')
        print(f"✅ fecha_emision y mes procesados: {fecha_emision_str}, mes: {mes}")
    except (ValueError, TypeError) as e:
        print(f"⚠️ Error procesando fecha_emision, usando fecha actual: {e}")
        fecha_emision_dt = datetime.now()
        fecha_emision_str = fecha_emision_dt.strftime('%Y-%m-%d')
        mes = fecha_emision_dt.strftime('%Y-%m')
    
    # Procesar fecha estimada de pago
    fecha_estimada_pago = form_data.get('fecha_estimada_pago')
    if fecha_estimada_pago and str(fecha_estimada_pago).strip() and str(fecha_estimada_pago).strip().lower() != 'nan':
        try:
            # Validar formato de fecha
            datetime.strptime(str(fecha_estimada_pago), '%Y-%m-%d')
            fecha_estimada_pago_final = str(fecha_estimada_pago)
            print(f"✅ fecha_estimada_pago procesada: {fecha_estimada_pago_final}")
        except ValueError:
            print("⚠️ fecha_estimada_pago inválida, calculando 30 días desde emisión")
            fecha_estimada_pago_final = (fecha_emision_dt + timedelta(days=30)).strftime('%Y-%m-%d')
    else:
        # Calcular 30 días desde emisión si no se proporciona
        fecha_estimada_pago_final = (fecha_emision_dt + timedelta(days=30)).strftime('%Y-%m-%d')
        print(f"✅ fecha_estimada_pago calculada (30 días): {fecha_estimada_pago_final}")
    
    # Procesar fecha de envío cliente
    fecha_envio_cliente = form_data.get('fecha_envio_cliente')
    if fecha_envio_cliente and str(fecha_envio_cliente).strip() and str(fecha_envio_cliente).strip().lower() != 'nan':
        try:
            # Validar formato de fecha
            datetime.strptime(str(fecha_envio_cliente), '%Y-%m-%d')
            fecha_envio_cliente_final = str(fecha_envio_cliente)
            print(f"✅ fecha_envio_cliente procesada: {fecha_envio_cliente_final}")
        except ValueError:
            print("⚠️ fecha_envio_cliente inválida, estableciendo como None")
            fecha_envio_cliente_final = None
    else:
        fecha_envio_cliente_final = None
        print("✅ fecha_envio_cliente establecida como None (vacía)")
    
    # Procesar campos de texto opcionales
    gestor = form_data.get('gestor')
    gestor_final = str(gestor).strip() if gestor and str(gestor).strip() != '' and str(gestor).strip().lower() != 'nan' else None
    
    observaciones = form_data.get('observaciones')
    observaciones_final = str(observaciones).strip() if observaciones and str(observaciones).strip() != '' and str(observaciones).strip().lower() != 'nan' else None
    
    # Procesar campo booleano conformidad_enviada
    conformidad_enviada = form_data.get('conformidad_enviada', False)
    if isinstance(conformidad_enviada, str):
        # Convertir string a booleano
        conformidad_enviada_final = conformidad_enviada.lower() in ['true', 'yes', 'si', 'sí', '1', 'on']
    elif isinstance(conformidad_enviada, (int, float)):
        conformidad_enviada_final = bool(conformidad_enviada)
    else:
        conformidad_enviada_final = bool(conformidad_enviada) if conformidad_enviada is not None else False
    
    print(f"✅ Campos opcionales procesados - gestor: {gestor_final}, observaciones: {observaciones_final}")
    print(f"✅ Campo booleano procesado - conformidad_enviada: {conformidad_enviada_final}")
    
    # Preparar datos finales
    edp_data = {
        # Campos obligatorios
        'n_edp': n_edp_final,
        'proyecto': str(form_data['proyecto']).strip(),
        'cliente': str(form_data['cliente']).strip(),
        'jefe_proyecto': str(form_data['jefe_proyecto']).strip(),
        'fecha_emision': fecha_emision_str,
        'monto_propuesto': monto_propuesto,
        
        # Campos automáticos
        'estado': 'pendiente',  # Estado inicial más apropiado
        'mes': mes,
        'conformidad_enviada': conformidad_enviada_final,  # Booleano procesado
        
        # Campos opcionales
        'gestor': gestor_final,
        'fecha_envio_cliente': fecha_envio_cliente_final,
        'monto_aprobado': monto_aprobado,
        'fecha_estimada_pago': fecha_estimada_pago_final,
        'observaciones': observaciones_final,
        
        # Campos de seguimiento
        'registrado_por': form_data.get('registrado_por', 'admin'),
        'fecha_registro': datetime.now().isoformat(),
        
        # Campos adicionales para compatibilidad con Supabase
        'n_conformidad': '',
        'fecha_conformidad': None,
        'estado_detallado': '',
        'motivo_no_aprobado': '',
        'tipo_falla': ''
    }
    
    print(f"🎯 Datos finales preparados: {edp_data}")
    return edp_data

def process_bulk_upload(df: pd.DataFrame, user: str) -> Dict[str, Any]:
    """Procesar carga masiva de EDPs con optimización de rendimiento."""
    success_count = 0
    error_count = 0
    errors = []
    batch_size = 100  # Aumentar tamaño de lote para mejor rendimiento
    
    try:
        # Preparar datos para inserción masiva
        valid_edps = []
        
        for idx, row in df.iterrows():
            try:
                # Preparar datos de la fila
                row_data = row.to_dict()
                row_data['registrado_por'] = user
                row_data['fecha_registro'] = datetime.now()
                
                # Validar fila individual
                validation = validate_edp_data(row_data)
                if not validation['valid']:
                    error_count += 1
                    errors.append({
                        'row': idx + 2,
                        'errors': validation['errors']
                    })
                    continue
                
                # Preparar datos y crear modelo
                edp_data = prepare_edp_data(row_data)
                edp = EDP.from_dict(edp_data)
                valid_edps.append(edp)
                
            except Exception as e:
                error_count += 1
                errors.append({
                    'row': idx + 2,
                    'error': str(e)
                })
        
        # Inserción masiva optimizada por lotes
        for i in range(0, len(valid_edps), batch_size):
            batch = valid_edps[i:i + batch_size]
            try:
                # Usar inserción masiva optimizada
                result = edp_repository.create_bulk(batch)
                if result['success']:
                    success_count += len(batch)
                else:
                    error_count += len(batch)
                    errors.append({
                        'batch': f'{i+1}-{i+len(batch)}',
                        'error': result['message']
                    })
            except Exception as e:
                error_count += len(batch)
                errors.append({
                    'batch': f'{i+1}-{i+len(batch)}',
                    'error': str(e)
                })
        
        # Limpiar caché de EDPs después del procesamiento masivo
        if success_count > 0:
            global _GLOBAL_EDP_CACHE
            _GLOBAL_EDP_CACHE['data'] = {}
            _GLOBAL_EDP_CACHE['last_update'] = 0
            print(f"🔄 Caché de EDPs limpiado después de crear {success_count} EDPs")
        
        return {
            'success': success_count > 0,
            'message': f'Procesamiento completado: {success_count} exitosos, {error_count} errores',
            'stats': {
                'total_rows': len(df),
                'success_count': success_count,
                'error_count': error_count,
                'success_rate': (success_count / len(df)) * 100 if len(df) > 0 else 0
            },
            'errors': errors[:10]  # Limitar errores mostrados
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error en procesamiento masivo: {str(e)}',
            'stats': {
                'total_rows': len(df),
                'success_count': success_count,
                'error_count': error_count
            },
            'errors': errors
        } 
        
        
@edp_upload_bp.route('/upload/options')
@login_required
def get_form_options():
    """Obtener opciones para los campos del formulario desde la BD."""
    try:
        print("🔍 Obteniendo opciones del formulario...")
        
        # Obtener datos desde EDPs existentes para opciones del formulario
        result = edp_repository.find_all()
        print(f"🔍 Resultado de edp_repository.find_all(): {type(result)}")
        print(f"🔍 Keys del resultado: {result.keys() if isinstance(result, dict) else 'No es dict'}")
        
        # Verificar si la operación fue exitosa
        if not result or not result.get('success', False):
            print(f"❌ Error en find_all: {result.get('message', 'Unknown error') if result else 'No result'}")
            # Devolver opciones vacías si hay error
            return jsonify({
                'success': True,
                'options': {
                    'proyectos': [],
                    'clientes': [],
                    'gestores': [],
                    'jefes_proyecto': []
                },
                'projects_info': {}
            })
        
        # Extraer la lista de EDPs del resultado
        edps_list = result.get('data', [])
        print(f"🔍 EDPs extraídos: {type(edps_list)} - Cantidad: {len(edps_list) if edps_list else 0}")
        
        # Inicializar conjuntos para opciones
        proyectos = set()
        clientes = set()
        gestores = set()
        jefes_proyecto = set()
        projects_info = {}
        
        # Si hay EDPs, extraer datos
        if edps_list and len(edps_list) > 0:
            print(f"🔍 Procesando {len(edps_list)} EDPs...")
            
            for i, edp in enumerate(edps_list):
                # Los EDPs pueden ser objetos EDP o diccionarios
                if hasattr(edp, 'to_dict'):
                    # Es un objeto EDP, convertir a diccionario
                    edp_dict = edp.to_dict()
                elif isinstance(edp, dict):
                    # Ya es un diccionario
                    edp_dict = edp
                else:
                    print(f"⚠️ EDP {i+1} no es ni objeto ni diccionario: {type(edp)}")
                    continue
                
                proyecto = edp_dict.get('proyecto', '')
                cliente = edp_dict.get('cliente', '')
                gestor = edp_dict.get('gestor', '')
                jefe = edp_dict.get('jefe_proyecto', '')
                
                if i < 3:  # Mostrar solo los primeros 3 para debug
                    print(f"🔍 EDP {i+1}: proyecto='{proyecto}', cliente='{cliente}', gestor='{gestor}', jefe='{jefe}'")
                
                if proyecto:
                    proyectos.add(proyecto)
                    if proyecto not in projects_info:
                        projects_info[proyecto] = {
                            'cliente': cliente,
                            'jefe_proyecto': jefe,
                            'gestor': gestor
                        }
                
                if cliente:
                    clientes.add(cliente)
                if gestor:
                    gestores.add(gestor)
                if jefe:
                    jefes_proyecto.add(jefe)
        else:
            print("⚠️ No hay EDPs en la base de datos")
        
        # Si no hay datos de EDPs, agregar opciones básicas de ejemplo
        if not proyectos:
            print("🔧 Agregando opciones básicas de ejemplo...")
            proyectos_ejemplo = [
                'PROYECTO_DEMO_A',
                'PROYECTO_DEMO_B', 
                'PROYECTO_DEMO_C'
            ]
            clientes_ejemplo = [
                'Cliente Demo 1',
                'Cliente Demo 2',
                'Cliente Demo 3'
            ]
            gestores_ejemplo = [
                'Gestor Demo 1',
                'Gestor Demo 2'
            ]
            jefes_ejemplo = [
                'Jefe Demo 1',
                'Jefe Demo 2'
            ]
            
            proyectos.update(proyectos_ejemplo)
            clientes.update(clientes_ejemplo)
            gestores.update(gestores_ejemplo)
            jefes_proyecto.update(jefes_ejemplo)
            
            # Crear info de proyectos demo
            for i, proyecto in enumerate(proyectos_ejemplo):
                projects_info[proyecto] = {
                    'cliente': clientes_ejemplo[i % len(clientes_ejemplo)],
                    'jefe_proyecto': jefes_ejemplo[i % len(jefes_ejemplo)],
                    'gestor': gestores_ejemplo[i % len(gestores_ejemplo)]
                }
        
        final_options = {
            'proyectos': sorted(list(proyectos)),
            'clientes': sorted(list(clientes)),
            'gestores': sorted(list(gestores)),
            'jefes_proyecto': sorted(list(jefes_proyecto))
        }
        
        print(f"✅ Opciones extraídas:")
        print(f"   - Proyectos: {len(final_options['proyectos'])} ({final_options['proyectos'][:3] if final_options['proyectos'] else []})")
        print(f"   - Clientes: {len(final_options['clientes'])} ({final_options['clientes'][:3] if final_options['clientes'] else []})")
        print(f"   - Gestores: {len(final_options['gestores'])}")
        print(f"   - Jefes: {len(final_options['jefes_proyecto'])}")
        
        return jsonify({
            'success': True,
            'options': final_options,
            'projects_info': projects_info
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo opciones: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@edp_upload_bp.route('/upload/validate-duplicate', methods=['POST'])
@login_required
def validate_duplicate():
    """Validar si un número EDP es duplicado."""
    try:
        data = request.get_json()
        n_edp = data.get('n_edp')
        proyecto = data.get('proyecto', '').strip()
        
        if not n_edp:
            return jsonify({
                'success': False,
                'message': 'Número EDP requerido'
            }), 400
        
        # Convertir a entero
        try:
            n_edp = int(n_edp)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Número EDP debe ser un número válido'
            }), 400
        
        # Verificar duplicado
        is_duplicate = check_duplicate_fast(n_edp, proyecto)
        
        return jsonify({
            'success': True,
            'is_duplicate': is_duplicate,
            'message': f'EDP #{n_edp} {"ya existe" if is_duplicate else "está disponible"}' + (f' para el proyecto {proyecto}' if proyecto else '')
        })
        
    except Exception as e:
        print(f"Error validando duplicado: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
