import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.config import Config

from datetime import datetime, timezone, timedelta
import re

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
def idx_to_a1(idx):          # 0-based
    s = ""
    while idx >= 0:
        idx, r = divmod(idx, 26)
        s = chr(65 + r) + s
        idx -= 1
    return s
ALLOWED = {
    "creado": ["revisión interna"],
    "revisión interna": ["enviado cliente", "re-trabajo"],
    "enviado cliente": ["revisión cliente", "re-trabajo"],
    "revisión cliente": ["aprobado", "re-trabajo"],
    "aprobado": ["conformidad emitida"],
    "re-trabajo": ["revisión interna"],
    "conformidad emitida": []         # fin de flujo operativo
}


def generate_unique_id():
    """Genera un nuevo ID único para un EDP"""
    service = get_service()
    
    # Obtener todos los IDs existentes
    result = service.spreadsheets().values().get(
        spreadsheetId=Config.SHEET_ID,
        range="edp!A:A"
    ).execute()
    values = result.get("values", [])
    
    # Filtrar encabezado y valores no numéricos
    ids = [int(val[0]) for val in values[1:] if val and val[0].isdigit()]
    
    # Devolver el siguiente ID
    return max(ids) + 1 if ids else 1



def append_edp(edp_data):
    """Inserta un nuevo EDP asignándole un ID único"""
    # Generar ID único
    unique_id = generate_unique_id()
    
    # Preparar fila con ID al principio
    row_values = [unique_id]
    
    # Añadir el resto de datos del EDP
    for campo in ["N° EDP", "Proyecto", "Cliente", "Estado", ...]:
        row_values.append(edp_data.get(campo, ""))
    
    # Insertar en la hoja
    append_row(row_values, sheet_name="edp")
    
    # Devolver el ID asignado
    return unique_id

def son_diferentes(v1, v2):
    """
    Compara dos valores con inteligencia para determinar si son realmente diferentes.
    Maneja específicamente casos de fechas y números.
    """
    # Convertir a strings para comparación básica
    str_v1 = str(v1).strip()
    str_v2 = str(v2).strip()
    
    # Caso trivial: exactamente iguales
    if str_v1 == str_v2:
        return False
    
    # Normalización específica para montos
    try:
        # Eliminar TODOS los caracteres no numéricos
        num_v1 = re.sub(r'[^\d]', '', str_v1)
        num_v2 = re.sub(r'[^\d]', '', str_v2)
        
        # Si después de limpiar son iguales, no son diferentes
        if num_v1 == num_v2:
            return False
    except:
        pass
        
    # Intentar normalizar fechas (extraer solo YYYY-MM-DD)
    try:
        # Verificar si es una fecha con formato de fecha y hora
        if ' ' in str_v1 or ' ' in str_v2:
            # Extraer solo la parte de la fecha (YYYY-MM-DD)
            date_pattern = r'(\d{4}-\d{2}-\d{2})'
            
            date_v1 = re.search(date_pattern, str_v1)
            date_v2 = re.search(date_pattern, str_v2)
            
            if date_v1 and date_v2:
                # Comparar solo la parte de la fecha
                return date_v1.group(1) != date_v2.group(1)
    except:
        pass
    
    # Para otros tipos, comparación insensible a mayúsculas/minúsculas
    return str_v1.lower() != str_v2.lower()


def validar_transicion(estado_actual, nuevo_estado):
    if nuevo_estado not in ALLOWED.get(estado_actual, []):
        raise ValueError(f"Transición {estado_actual} → {nuevo_estado} no permitida")


def validar_edp(edp_original, updates):
    cur = edp_original["Estado Detallado"]
    new = updates.get("Estado Detallado", cur)

    validar_transicion(cur, new)  # la func. que vimos antes

    # reglas extra
    if new == "aprobado":
        faltan = [c for c in ("Monto Aprobado", "Fecha Estimada de Pago") if not updates.get(c)]
        if faltan:
            raise ValueError(f"Faltan campos requeridos: {', '.join(faltan)}")

    if new == "re-trabajo solicitado" and not updates.get("Motivo No-aprobado"):
        raise ValueError("Debes elegir Motivo No-aprobado al pasar a Re-trabajo")

    # Mejora para la validación de Conformidad Enviada
    if updates.get("Conformidad Enviada") == "Sí":
        campos_requeridos = ["N° Conformidad", "Fecha Conformidad"]
        faltan = [c for c in campos_requeridos if not updates.get(c)]
        if faltan:
            raise ValueError(f"Al marcar Conformidad Enviada como 'Sí', debes completar: {', '.join(faltan)}")

def get_service():
    creds = Credentials.from_service_account_file(Config.GOOGLE_CREDENTIALS, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def read_sheet(range_name, apply_transformations=True):
    """
    Lee datos de Google Sheets y los convierte en DataFrame de pandas.
    
    Args:
        range_name (str): Rango a leer, ej: "edp!A1:Z"
        apply_transformations (bool): Si se deben aplicar transformaciones específicas por tipo de hoja
    
    Returns:
        DataFrame: Datos solicitados
    """
    service = get_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=Config.SHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    if not values:
        print(f"No hay datos en el rango {range_name}")
        return pd.DataFrame()
    
    # Crear DataFrame (primero verificar que hay datos después de la cabecera)
    if len(values) > 1:
        # Verificar duplicados en encabezados
        headers = values[0]
        duplicate_headers = [h for h in set(headers) if headers.count(h) > 1]
        
        if duplicate_headers:
            print(f"Advertencia: Columnas duplicadas encontradas en {range_name}: {duplicate_headers}")
            # Renombrar encabezados duplicados agregando un sufijo
            unique_headers = []
            counts = {}
            for h in headers:
                if h in counts:
                    counts[h] += 1
                    unique_headers.append(f"{h}_{counts[h]}")
                else:
                    counts[h] = 0
                    unique_headers.append(h)
            df = pd.DataFrame(values[1:], columns=unique_headers)
        else:
            df = pd.DataFrame(values[1:], columns=headers)
        
        df = df.fillna("")
    else:
        # Solo hay encabezados, crear DataFrame vacío con esas columnas
        return pd.DataFrame(columns=values[0])
    
    # Si no queremos aplicar transformaciones, devolver el DataFrame tal cual
    if not apply_transformations:
        return df
    
    # Determinar el tipo de hoja basado en el nombre del rango
    sheet_type = range_name.split('!')[0].lower() if '!' in range_name else ""
    
    # Fecha actual para cálculos
    hoy = pd.to_datetime(datetime.today())
    
    # Aplicar transformaciones según el tipo de hoja
    if sheet_type == "issues":
        # Transformaciones específicas para la hoja de incidencias
        for date_col in ["Timestamp", "Fecha última actualización", "Fecha resolución"]:
            if date_col in df.columns:
                try:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                except ValueError as e:
                    if "duplicate keys" in str(e):
                        print(f"Advertencia: Valores duplicados en columna {date_col}, usando conversión segura")
                        # Usar método alternativo fila por fila
                        df[date_col] = df[date_col].apply(lambda x: pd.to_datetime(x, errors='coerce'))
                    else:
                        raise e
                
        # Convertir ID a numérico si existe
        if 'ID' in df.columns:
            df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
    
    else:  # Para "edp" u otras hojas, aplicar las transformaciones originales
        # Monto
        for col in ["Monto Propuesto", "Monto Aprobado"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
        categorical_cols = ['Estado', 'Estado Detallado', 'Motivo No-aprobado', 'Tipo_falla']
        existentes = [c for c in categorical_cols if c in df.columns]
        if existentes:
            df[existentes] = df[existentes].apply(lambda s: s.str.strip().str.lower())

        # Fechas - usar método seguro para evitar error de duplicate keys
        date_cols = [
            "Fecha Emisión", "Fecha Envío al Cliente", "Fecha Estimada de Pago",
            "Fecha Conformidad", "Fecha Registro", "Fecha y Hora"
        ]
        for col in date_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except ValueError as e:
                    if "duplicate keys" in str(e):
                        print(f"Advertencia: Valores duplicados en columna {col}, usando conversión segura")
                        # Usar método alternativo fila por fila
                        df[col] = df[col].apply(lambda x: pd.to_datetime(x, errors='coerce'))
                    else:
                        raise e

        # Estado limpio
        if "Estado" in df.columns:
            df["Estado"] = df["Estado"].str.strip().str.lower()
            df["Validado"] = df["Estado"] == "validado"
        else:
            df["Validado"] = False

        # Días Espera - usar versión segura en caso de que haya problemas con las fechas
        if "Fecha Envío al Cliente" in df.columns:
            try:
                fecha_envio = df["Fecha Envío al Cliente"]
                fecha_ref = df["Fecha Conformidad"] if "Fecha Conformidad" in df.columns else hoy
                df["Días Espera"] = (fecha_ref.fillna(hoy) - fecha_envio).dt.days
            except Exception as e:
                print(f"Error calculando Días Espera: {str(e)}")
                df["Días Espera"] = "—"
        else:
            df["Días Espera"] = "—"

        # Resto del código sin cambios...
        # (El resto del código permanece igual)
        
        # Días Hábiles
        if "Fecha Envío al Cliente" in df.columns:
            def calcular_dias_habiles(row):
                inicio = row.get("Fecha Envío al Cliente")
                fin = row.get("Fecha Conformidad")
                if pd.isna(inicio):
                    return "—"
                if pd.isna(fin):
                    fin = hoy
                try:
                    dias = pd.bdate_range(start=inicio, end=fin)
                    return max(len(dias) - 1, 0)
                except Exception:
                    return "—"
            df["Días Hábiles"] = df.apply(calcular_dias_habiles, axis=1)
        else:
            df["Días Hábiles"] = "—"

        # Conformidad Pendiente
        if "Conformidad Enviada" in df.columns and "Fecha Conformidad" in df.columns:
            df["Falta Conformidad"] = (df["Conformidad Enviada"] == "No") & (df["Fecha Conformidad"].isna())
        else:
            df["Falta Conformidad"] = False

        # Crítico - Ahora verificamos que Días Espera sea numérico antes de comparar
        if "Días Espera" in df.columns:
            # Crear una máscara booleana para filas donde Días Espera es un número
            is_numeric = pd.to_numeric(df["Días Espera"], errors='coerce').notna()
            
            # Inicializar la columna Crítico como False para todas las filas
            df["Crítico"] = False
            
            # Solo aplicar la condición > 30 donde tenemos valores numéricos
            if is_numeric.any():
                df.loc[is_numeric, "Crítico"] = pd.to_numeric(df.loc[is_numeric, "Días Espera"]) > 30
        else:
            df["Crítico"] = False
            
        # Estado visual
        if "Validado" in df.columns and "Crítico" in df.columns:
            def estado_visual(row):
                if row["Validado"]:
                    return "Validado"
                elif row["Crítico"]:
                    return "Crítico"
                else:
                    return "En espera"
            df["Estado Visual"] = df.apply(estado_visual, axis=1)

    return df

def append_row(row_values, sheet_name="edp"):
    """
    Inserta una fila al final de la sheet `sheet_name`.
    - Ajusta el largo de row_values a las columnas reales del Sheet.
    - Usa USER_ENTERED para respetar fórmulas/formato.
    """
    service = get_service()
    sheet   = service.spreadsheets()

    # 1) Leer encabezados (primera fila)
    header_range = f"{sheet_name}!1:1"
    headers = sheet.values().get(
        spreadsheetId=Config.SHEET_ID,
        range=header_range
    ).execute().get("values", [[]])[0]

    # 2) Igualar longitud
    n_cols = len(headers)
    row_values = (row_values + [""] * n_cols)[:n_cols]

    # 3) Append dinámico (indica sólo la hoja, sin rango fijo)
    sheet.values().append(
        spreadsheetId   = Config.SHEET_ID,
        range           = sheet_name,       # ← deja que Sheets coloque al final
        valueInputOption= "USER_ENTERED",
        insertDataOption= "INSERT_ROWS",
        body            = {"values": [row_values]}
    ).execute()


def update_edp_by_id(edp_id, updates, usuario="Sistema"):
    """
    Actualiza un EDP utilizando su ID único
    
    Args:
        edp_id (int): ID único del EDP
        updates (dict): Cambios a aplicar
        usuario (str): Usuario que realiza los cambios
    """
    try:
        # Buscar la fila por ID único
        df = read_sheet("edp!A1:Z")
        matches = df[df["ID"] == str(edp_id)]
        
        if matches.empty:
            print(f"EDP con ID {edp_id} no encontrado")
            return False
            
        # Obtener el índice de fila (1-based para sheets)
        row_idx = matches.index[0] + 2  # +1 por el encabezado, +1 porque sheets empieza en 1
        
        # Usar la función update_row existente pero con la fila correcta
        update_row(row_idx, updates, sheet_name="edp", usuario=usuario)
        return True
        
    except Exception as e:
        print(f"Error al actualizar EDP por ID: {str(e)}")
        return False
    
def update_row(row_number, updates, sheet_name="edp", usuario="Sistema", force_update=False):
    """
    Actualiza columnas específicas en la fila `row_number` (base-1, incluye encabezado)
    y deja un registro en la hoja `log`.

    Parámetros
    ----------
    row_number : int
        Fila que se va a modificar (1 = encabezado, 2 = primera fila de datos).
    updates : dict
        { "Nombre Columna": nuevo_valor, ... }
    sheet_name : str
        Nombre de la pestaña con los datos EDP (sin !A1).
    usuario : str
        Quien ejecuta el cambio (para el log).
    force_update : bool
        Si es True, ignora la comparación y fuerza la actualización.
    """
    try:
        service = get_service()
        sheet = service.spreadsheets()

        # --- 1. Obtener encabezados ---
        header_range = f"{sheet_name}!A1:1"
        result = sheet.values().get(
            spreadsheetId=Config.SHEET_ID,
            range=header_range
        ).execute()
        
        if not result.get("values"):
            print(f"Error: No se encontraron encabezados en {sheet_name}")
            return False
            
        headers = result.get("values")[0]

        # --- 2. Traer la fila antes del cambio ---
        last_col = idx_to_a1(len(headers) - 1)
        row_range = f"{sheet_name}!A{row_number}:{last_col}{row_number}"
        
        result = sheet.values().get(
            spreadsheetId=Config.SHEET_ID,
            range=row_range
        ).execute()
        
        if not result.get("values"):
            print(f"Error: No se encontraron datos en la fila {row_number}")
            return False
            
        row_values = result.get("values")[0]

        # Asegurar que row_values tiene la misma longitud que headers
        row_values += [""] * (len(headers) - len(row_values))
        before = dict(zip(headers, row_values))

        # --- 3. Aplicar los cambios en memoria ---
        cambios_reales = []  # Rastrear solo cambios reales
        
        for key, value in updates.items():
            if key in headers:
                idx = headers.index(key)
                valor_anterior = row_values[idx]
                
                # --- 3a. Verificar si el valor realmente cambió O si force_update está activado ---
                if force_update or son_diferentes(valor_anterior, value):
                    # Registrar el cambio real
                    cambios_reales.append((key, valor_anterior, value))
                    # Actualizar el valor en la fila
                    row_values[idx] = value
                    # Log para debugging
                    print(f"Cambio detectado en {key}: '{valor_anterior}' -> '{value}'")
            else:
                print(f"Advertencia: La columna '{key}' no existe en {sheet_name}")

        # --- 4. Enviar la fila actualizada a Sheets (solo si hay cambios) ---
        if cambios_reales:
            body = {"values": [row_values]}
            sheet.values().update(
                spreadsheetId=Config.SHEET_ID,
                range=row_range,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            print(f"Actualización enviada a Sheets: {len(cambios_reales)} cambios")
            
            # --- 5. Registrar solo los cambios reales en el log ---
            id_edp = before.get("ID", "0")  # Obtener el ID único como identificador primario
            n_edp = before.get("N° EDP", "—")
            proyecto = before.get("Proyecto", "—")
            
            for campo, antes, despues in cambios_reales:
                log_cambio_edp(
                    n_edp=n_edp,
                    proyecto=proyecto,
                    campo=campo,
                    antes=antes,
                    despues=despues,
                    usuario=usuario
                )
            
            return True
        else:
            print("No se detectaron cambios para actualizar")
            return False
            
    except Exception as e:
        import traceback
        print(f"Error en update_row: {str(e)}")
        print(traceback.format_exc())
        return False
    

def normalizar_valor_log(valor):
    """
    Normaliza valores para mostrar en el log, especialmente fechas y números.
    - Para fechas: extrae solo la parte YYYY-MM-DD
    - Para números: normaliza a formato estándar sin separadores
    """
    str_valor = str(valor).strip()
    
    # Detectar si es una fecha con formato fecha-hora
    date_pattern = r'(\d{4}-\d{2}-\d{2})(?:\s+\d{1,2}:\d{1,2}:\d{1,2})?'
    match = re.search(date_pattern, str_valor)
    
    if match:
        # Devolver solo la parte de fecha YYYY-MM-DD
        return match.group(1)
    
    # Detectar y normalizar números
    try:
        # Eliminar todos los caracteres no numéricos (puntos, comas, espacios)
        num_str = re.sub(r'[^\d]', '', str_valor)
        if num_str:
            # Convertir a entero y volver a string para formato estándar
            return str(int(num_str))
    except:
        pass
    
    return str_valor






# Caché para evitar entradas duplicadas en el log
_recent_log_entries = {}
def log_cambio_edp(n_edp: str,
                   proyecto: str,  # Nuevo parámetro
                   campo: str,
                   antes: str,
                   despues: str,
                   usuario: str = "Sistema"):
    """
    Registra un cambio en la pestaña `log` del mismo Spreadsheet.
    Incluye deduplicación para evitar entradas repetidas.

    Columnas:
    A) Fecha y Hora (UTC-3) · B) N° EDP · C) Proyecto · D) Campo · E) Antes · F) Después · G) Usuario
    """
        # Manejar formato antiguo (compatibilidad)
    if campo is None and 'campo' in kwargs:
        campo = kwargs['campo']
    if antes is None and 'antes' in kwargs:
        antes = kwargs['antes']
    if despues is None and 'despues' in kwargs:
        despues = kwargs['despues']
    # 1. Hora en Chile (UTC-3)
    chile_tz = timezone(timedelta(hours=-3))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Normalizar valores para el log
    antes_normalizado = normalizar_valor_log(antes)
    despues_normalizado = normalizar_valor_log(despues)
    
    # No registrar si son iguales después de normalizar
    if antes_normalizado == despues_normalizado:
        return
        
    # DEDUPLICACIÓN con proyecto incluido en la clave
    entry_key = f"{n_edp}:{proyecto}:{campo}:{antes_normalizado}:{despues_normalizado}"
    
    # Verificar si hemos registrado este cambio recientemente (últimos 30 segundos)
    current_time = datetime.now()
    if entry_key in _recent_log_entries:
        last_time = _recent_log_entries[entry_key]
        if (current_time - last_time).total_seconds() < 30:
            # Ya registramos este mismo cambio hace menos de 30 segundos, no duplicar
            return
    
    # Actualizar el caché de entradas recientes
    _recent_log_entries[entry_key] = current_time
    
    # Limpiar entradas antiguas del caché (más de 5 minutos)
    for k in list(_recent_log_entries.keys()):
        if (current_time - _recent_log_entries[k]).total_seconds() > 300:
            del _recent_log_entries[k]
    
    # 2. Preparar fila - ahora con el campo proyecto
    valores = [timestamp, str(n_edp), str(proyecto), campo, antes_normalizado, despues_normalizado, usuario]

    # 3. Escribir - actualizado rango a A:G para incluir la columna proyecto
    service = get_service()
    service.spreadsheets().values().append(
        spreadsheetId   = Config.SHEET_ID,
        range           = "log!A:G",  # Actualizado de A:F a A:G
        valueInputOption= "USER_ENTERED",
        insertDataOption= "INSERT_ROWS",
        body            = {"values": [valores]}
    ).execute()
    
def read_log(n_edp=None, proyecto=None, usuario=None, range_name="log!A1:G"):
    """
    Devuelve el DataFrame del historial de cambios.
    Permite filtrar por número de EDP, proyecto o usuario.
    
    Args:
        n_edp (str, optional): Filtrar por número de EDP
        proyecto (str, optional): Filtrar por proyecto 
        usuario (str, optional): Filtrar por usuario
        range_name (str): Rango a leer
    """
    service = get_service()
    sheet = service.spreadsheets()

    result = sheet.values().get(
        spreadsheetId=Config.SHEET_ID,
        range=range_name
    ).execute()
    values = result.get("values", [])

    if not values:
        # Devolver DataFrame vacío con columnas esperadas
        return pd.DataFrame(columns=['Fecha y Hora', 'N° EDP', 'Proyecto', 'Campo', 'Antes', 'Después', 'Usuario'])

    # Manejar compatibilidad con formato antiguo (sin columna Proyecto)
    if len(values[0]) == 6:  # Formato antiguo: A:F
        # Insertar columna 'Proyecto' en la posición 2 (entre N° EDP y Campo)
        values[0].insert(2, 'Proyecto')
        for row in values[1:]:
            # Añadir valor vacío para la columna proyecto en filas de datos
            if len(row) == 6:
                row.insert(2, '')
            
    # Crear DataFrame y llenar valores vacíos
    df = pd.DataFrame(values[1:], columns=values[0]).fillna("")

    # Convertir fecha-hora
    if "Fecha y Hora" in df.columns:
        df["Fecha y Hora"] = pd.to_datetime(df["Fecha y Hora"], errors="coerce")

    # Filtrado
    if n_edp:
        df = df[df["N° EDP"] == str(n_edp)]
    if proyecto:
        df = df[df["Proyecto"] == str(proyecto)]
    if usuario:
        df = df[df["Usuario"].str.lower() == usuario.lower()]

    # Orden descendente
    if "Fecha y Hora" in df.columns:
        df = df.sort_values("Fecha y Hora", ascending=False)

    return df


def crear_incidencia(tipo: str, 
                     severidad: str,
                     estado: str, 
                     descripcion: str,
                     edp_relacionado: str = None,
                     proyecto_relacionado: str = None,
                     usuario_reporta: str = "Sistema",
                     usuario_asignado: str = None):
    """
    Crea una nueva incidencia en la hoja 'issues'.
    
    Columnas:
    A) ID · B) Timestamp · C) Tipo · D) Severidad · E) Estado
    F) Descripción · G) EDP Relacionado · H) Proyecto Relacionado
    I) Usuario que reporta · J) Usuario asignado · K) Fecha última actualización
    L) Fecha resolución · M) `Solución/Comentarios`
    """
    service = get_service()
    
    # 1. Obtener el último ID de incidencia
    result = service.spreadsheets().values().get(
        spreadsheetId=Config.SHEET_ID,
        range="issues!A:A"
    ).execute()
    values = result.get("values", [])
    
    # Ignorar la fila de encabezado
    if len(values) > 1:
        # Filtrar valores no numéricos y encontrar el máximo
        ids = [int(val[0]) for val in values[1:] if val and val[0].isdigit()]
        next_id = max(ids) + 1 if ids else 1
    else:
        next_id = 1
    
    # 2. Preparar los datos
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3. Crear la fila de datos
    nueva_fila = [
        next_id,                  # ID
        timestamp,                # Timestamp
        tipo,                     # Tipo
        severidad,                # Severidad
        estado,                   # Estado
        descripcion,              # Descripción
        edp_relacionado or "",    # EDP Relacionado
        proyecto_relacionado or "",  # Proyecto Relacionado
        usuario_reporta,          # Usuario que reporta
        usuario_asignado or "",   # Usuario asignado
        timestamp,                # Fecha última actualización
        "",                       # Fecha resolución (vacía al crear)
        ""                        # Solución/Comentarios (vacío al crear)
    ]
    
    # 4. Insertar en la hoja
    service.spreadsheets().values().append(
        spreadsheetId=Config.SHEET_ID,
        range="issues!A:R",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [nueva_fila]}
    ).execute()
    
    return next_id


def leer_incidencias(filtros=None):
    """
    Lee las incidencias de la hoja 'issues' con opciones de filtrado.
    
    Args:
        filtros (dict, optional): Filtros a aplicar, como:
            - id: ID específico de incidencia
            - estado: Estado de las incidencias
            - tipo: Tipo de incidencia
            - edp_relacionado: EDP relacionado
            - proyecto_relacionado: Proyecto relacionado
            
    Returns:
        DataFrame: DataFrame con las incidencias que cumplen los filtros
    """
    df = read_sheet("issues!A:R")
    
    if df.empty:
        # Si la hoja está vacía o no existe, devolver DataFrame vacío con columnas esperadas
        return pd.DataFrame(columns=[
            'ID', 'Timestamp', 'Tipo', 'Severidad', 'Estado', 'Descripción',
            'EDP Relacionado', 'Proyecto Relacionado', 'Usuario que reporta',
            'Usuario asignado', 'Fecha última actualización', 'Fecha resolución',
            'Solución/Comentarios'
        ])
    
    # Aplicar filtros si existen
    if filtros:
        if 'id' in filtros and filtros['id']:
            df = df[df['ID'] == str(filtros['id'])]
        if 'estado' in filtros and filtros['estado']:
            df = df[df['Estado'] == filtros['estado']]
        if 'tipo' in filtros and filtros['tipo']:
            df = df[df['Tipo'] == filtros['tipo']]
        if 'edp_relacionado' in filtros and filtros['edp_relacionado']:
            df = df[df['EDP Relacionado'] == filtros['edp_relacionado']]
        if 'proyecto_relacionado' in filtros and filtros['proyecto_relacionado']:
            df = df[df['Proyecto Relacionado'] == filtros['proyecto_relacionado']]
    
    # Convertir columnas de fecha a datetime
    for col in ['Timestamp', 'Fecha última actualización', 'Fecha resolución']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Ordenar por ID descendente (más recientes primero)
    if 'ID' in df.columns:
        df = df.sort_values('ID', ascending=False)

    # Aplicar transformaciones específicas para incidencias
    for date_col in ["Timestamp", "Fecha última actualización", "Fecha resolución"]:
        if date_col in df.columns:
            # Convertir a datetime y normalizar las zonas horarias
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            
            # Asegurarse de que todas las fechas tengan el mismo formato (sin zona horaria)
            if hasattr(df[date_col].dt, 'tz'):
                df[date_col] = df[date_col].dt.tz_localize(None)
    return df


def actualizar_incidencia(id_incidencia, actualizaciones, usuario="Sistema"):
    """
    Actualiza una incidencia existente.
    
    Args:
        id_incidencia (int): ID de la incidencia a actualizar
        actualizaciones (dict): Diccionario con los campos a actualizar
        usuario (str): Usuario que realiza la actualización
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        df = read_sheet("issues!A:M")
        
        # Buscar la fila por ID
        fila = df[df['ID'] == str(id_incidencia)]
        if fila.empty:
            print(f"Incidencia ID {id_incidencia} no encontrada.")
            return False
        
        row_idx = fila.index[0] + 2  # +1 por encabezado, +1 porque Sheets arranca en 1
        
        # Siempre actualizar la fecha de última actualización
        actualizaciones['Fecha última actualización'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Si el estado cambia a "resuelta", añadir fecha de resolución
        if actualizaciones.get('Estado') == 'resuelta' and not actualizaciones.get('Fecha resolución'):
            actualizaciones['Fecha resolución'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Mapear nombres de columnas a letras de columna
        columnas = {
            'Tipo': 'C',
            'Severidad': 'D',
            'Estado': 'E',
            'Descripción': 'F',
            'EDP Relacionado': 'G',
            'Proyecto Relacionado': 'H',
            'Usuario asignado': 'J',
            'Fecha última actualización': 'K',
            'Fecha resolución': 'L',
            'Solución/Comentarios': 'M'
        }
        
        # Preparar actualizaciones para Google Sheets
        service = get_service()
        
        for campo, valor in actualizaciones.items():
            if campo in columnas:
                col_letra = columnas[campo]
                # Actualizar celda
                service.spreadsheets().values().update(
                    spreadsheetId=Config.SHEET_ID,
                    range=f"issues!{col_letra}{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[valor]]}
                ).execute()
        
        return True
    
    except Exception as e:
        print(f"Error actualizando incidencia: {str(e)}")
        return False


def agregar_comentario_incidencia(id_incidencia, comentario, usuario="Sistema"):
    """
    Agrega un comentario a una incidencia existente.
    Los comentarios se guardan como una lista en formato texto en la columna "Solución/Comentarios".
    
    Args:
        id_incidencia (int): ID de la incidencia
        comentario (str): Texto del comentario
        usuario (str): Usuario que realiza el comentario
        
    Returns:
        bool: True si se agregó correctamente, False en caso contrario
    """
    try:
        df = read_sheet("issues!A:M")
        
        # Buscar la fila por ID
        fila = df[df['ID'] == str(id_incidencia)]
        if fila.empty:
            return False
            
        row_idx = fila.index[0] + 2  # +1 por encabezado, +1 porque Sheets arranca en 1
        
        # Obtener comentarios existentes
        comentarios_actuales = fila.iloc[0].get('Solución/Comentarios', '')
        
        # Formatear nuevo comentario
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nuevo_comentario = f"[{timestamp} - {usuario}] {comentario}"
        
        # Concatenar con los comentarios existentes
        if comentarios_actuales:
            comentarios_actualizados = f"{comentarios_actuales}\n\n{nuevo_comentario}"
        else:
            comentarios_actualizados = nuevo_comentario
        
        # Actualizar la celda
        service = get_service()
        service.spreadsheets().values().update(
            spreadsheetId=Config.SHEET_ID,
            range=f"issues!M{row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[comentarios_actualizados]]}
        ).execute()
        
        # Actualizar también la fecha de última actualización
        service.spreadsheets().values().update(
            spreadsheetId=Config.SHEET_ID,
            range=f"issues!K{row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[timestamp]]}
        ).execute()
        
        return True
        
    except Exception as e:
        print(f"Error agregando comentario a incidencia: {str(e)}")
        return False
    
    
