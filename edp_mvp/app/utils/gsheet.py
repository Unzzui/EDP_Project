import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.config import Config

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_service():
    creds = Credentials.from_service_account_file(Config.GOOGLE_CREDENTIALS, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def read_sheet(range_name="edp!A1:Q"):
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

def append_row(row_values, sheet_name="edp!A1:O"):
    service = get_service()
    body = {"values": [row_values]}
    service.spreadsheets().values().append(
        spreadsheetId=Config.SHEET_ID,
        range=sheet_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
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
    last_col = chr(65 + len(headers) - 1)          # col final (A=65)
    row_range = f"{sheet_name}!A{row_number}:{last_col}{row_number}"
    row_values = sheet.values().get(
        spreadsheetId=Config.SHEET_ID,
        range=row_range
    ).execute().get("values", [[]])[0]

    row_values += [""] * (len(headers) - len(row_values))   # padding
    before = dict(zip(headers, row_values))                 # snapshot

    # --- 3. Aplicar los cambios en memoria ---
    for key, value in updates.items():
        if key in headers:
            idx = headers.index(key)
            row_values[idx] = value

            # --- 3a. Registrar diff SOLO si el valor cambió ---
            if str(before.get(key, "")) != str(value):
                n_edp = before.get("N° EDP", "—")
                log_cambio_edp(
                    n_edp   = n_edp,
                    campo   = key,
                    antes   = before.get(key, ""),
                    despues = value,
                    usuario = usuario
                )

    # --- 4. Enviar la fila actualizada a Sheets ---
    body = {"values": [row_values]}
    sheet.values().update(
        spreadsheetId = Config.SHEET_ID,
        range          = row_range,
        valueInputOption = "USER_ENTERED",
        body = body
    ).execute()


def log_cambio_edp(n_edp, campo, antes, despues, usuario):
    service = get_service()
    hoja = service.spreadsheets()

    valores = [
        str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),  # Fecha y hora
        str(n_edp),
        campo,
        str(antes),
        str(despues),
        usuario
    ]

    hoja.values().append(
        spreadsheetId=Config.SHEET_ID,
        range="log!A1",  # Asumiendo que ya existe la hoja "log"
        valueInputOption="USER_ENTERED",
        body={"values": [valores]}
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
