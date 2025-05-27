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

def read_sheet(range_name="edp!A1:T"):
    service = get_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=Config.SHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()

    df = pd.DataFrame(values[1:], columns=values[0])
    df = df.fillna("")

    hoy = pd.to_datetime(datetime.today())

    # Monto
    for col in ["Monto Propuesto", "Monto Aprobado"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    categorical_cols = ['Estado', 'Estado Detallado', 'Motivo No-aprobado', 'Tipo_falla']
    existentes = [c for c in categorical_cols if c in df.columns]
    if existentes:
        df[existentes] = df[existentes].apply(lambda s: s.str.strip().str.lower())


    # Fechas
    date_cols = [
        "Fecha Emisión", "Fecha Envío al Cliente", "Fecha Estimada de Pago",
        "Fecha Conformidad", "Fecha Registro", "Fecha y Hora"
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Estado limpio
    if "Estado" in df.columns:
        df["Estado"] = df["Estado"].str.strip().str.lower()
        df["Validado"] = df["Estado"] == "validado"
    else:
        df["Validado"] = False

    # Días Espera
    if "Fecha Envío al Cliente" in df.columns:
        fecha_envio = df["Fecha Envío al Cliente"]
        fecha_ref = df["Fecha Conformidad"] if "Fecha Conformidad" in df.columns else hoy
        df["Días Espera"] = (fecha_ref.fillna(hoy) - fecha_envio).dt.days
    else:
        df["Días Espera"] = "—"

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

    # Crítico
    if "Días Espera" in df.columns:
        df["Crítico"] = df["Días Espera"] > 30
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



def update_row(row_number, updates, sheet_name="edp", usuario="Sistema"):
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
    """
    service = get_service()
    sheet  = service.spreadsheets()

    # --- 1. Obtener encabezados ---
    header_range  = f"{sheet_name}!A1:1"
    headers       = sheet.values().get(
        spreadsheetId=Config.SHEET_ID,
        range=header_range
    ).execute().get("values", [])[0]

    # --- 2. Traer la fila antes del cambio ---
    last_col = idx_to_a1(len(headers) - 1)         # col final (A=65)
    row_range = f"{sheet_name}!A{row_number}:{last_col}{row_number}"
    row_values = sheet.values().get(
        spreadsheetId=Config.SHEET_ID,
        range=row_range
    ).execute().get("values", [[]])[0]

    row_values += [""] * (len(headers) - len(row_values))   # padding
    before = dict(zip(headers, row_values))                 # snapshot

    # --- 3. Aplicar los cambios en memoria ---
    cambios_reales = []  # Rastrear solo cambios reales
    
    for key, value in updates.items():
        if key in headers:
            idx = headers.index(key)
            valor_anterior = row_values[idx]
            
            # --- 3a. Verificar si el valor realmente cambió usando son_diferentes() ---
            if son_diferentes(valor_anterior, value):
                # Registrar el cambio real
                cambios_reales.append((key, valor_anterior, value))
                # Actualizar el valor en la fila
                row_values[idx] = value

    # --- 4. Enviar la fila actualizada a Sheets (solo si hay cambios) ---
    if cambios_reales:
        body = {"values": [row_values]}
        sheet.values().update(
            spreadsheetId = Config.SHEET_ID,
            range          = row_range,
            valueInputOption = "USER_ENTERED",
            body = body
        ).execute()
        
        # --- 5. Registrar solo los cambios reales en el log ---
        n_edp = before.get("N° EDP", "—")
        for campo, antes, despues in cambios_reales:
            log_cambio_edp(
                n_edp   = n_edp,
                campo   = campo, 
                antes   = antes,
                despues = despues,
                usuario = usuario
            )

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

def log_cambio_edp(n_edp: str,
                   campo: str,
                   antes: str,
                   despues: str,
                   usuario: str = "Sistema"):
    """
    Registra un cambio en la pestaña `log` del mismo Spreadsheet.

    Columnas:
    A) Fecha y Hora (UTC-3) · B) N° EDP · C) Campo · D) Antes · E) Después · F) Usuario
    """
    # 1.  Hora en Chile (UTC-3) ─ evita confusiones al mirar el log
    chile_tz = timezone(timedelta(hours=-3))
    timestamp = datetime.now(chile_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    # Normalizar valores para el log (especialmente fechas)
    antes_normalizado = normalizar_valor_log(antes)
    despues_normalizado = normalizar_valor_log(despues)
    
    # No registrar si son iguales después de normalizar
    if antes_normalizado == despues_normalizado:
        return
        
    # 2.  Preparar fila
    valores = [timestamp, str(n_edp), campo, antes_normalizado, despues_normalizado, usuario]

    # 3.  Escribir
    service = get_service()
    service.spreadsheets().values().append(
        spreadsheetId   = Config.SHEET_ID,
        range           = "log!A:F",           # Basta con indicar el bloque de columnas
        valueInputOption= "USER_ENTERED",
        insertDataOption= "INSERT_ROWS",
        body            = {"values": [valores]}
    ).execute()
    
def read_log(n_edp=None, usuario=None, range_name="log!A1:F"):
    """
    Devuelve el DataFrame del historial de cambios.
    No aplica las transformaciones de read_sheet() porque la estructura es distinta.
    """
    service = get_service()
    sheet   = service.spreadsheets()

    result  = sheet.values().get(
        spreadsheetId=Config.SHEET_ID,
        range=range_name
    ).execute()
    values = result.get("values", [])

    if not values:
        return pd.DataFrame()

    df = pd.DataFrame(values[1:], columns=values[0]).fillna("")

    # Convertir fecha-hora
    if "Fecha y Hora" in df.columns:
        df["Fecha y Hora"] = pd.to_datetime(df["Fecha y Hora"], errors="coerce")

    # Filtrado
    if n_edp:
        df = df[df["N° EDP"] == str(n_edp)]
    if usuario:
        df = df[df["Usuario"].str.lower() == usuario.lower()]

    # Orden descendente
    if "Fecha y Hora" in df.columns:
        df = df.sort_values("Fecha y Hora", ascending=False)

    return df
