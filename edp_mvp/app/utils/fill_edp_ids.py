import pandas as pd
from app.utils.gsheet import get_service
from app.config import Config
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fill_missing_edp_ids():
    """
    Asigna IDs numéricos correlativos a todas las filas de la hoja 'edp'
    que no tengan un ID asignado. Los IDs son secuenciales empezando por 1.
    """
    logger.info("Iniciando asignación de IDs para EDPs existentes...")
    
    try:
        # Obtener servicio de Google Sheets
        service = get_service()
        
        # 1. Obtener todos los datos de la hoja
        result = service.spreadsheets().values().get(
            spreadsheetId=Config.SHEET_ID,
            range="edp!A1:Z"  # Leer todas las columnas
        ).execute()
        
        values = result.get("values", [])
        if not values:
            logger.warning("No se encontraron datos en la hoja 'edp'")
            return False, "No hay datos en la hoja"
            
        # 2. Verificar que la primera columna sea "ID"
        header = values[0]
        if header[0] != "ID":
            logger.error("La primera columna debe ser 'ID'. Verifica tu estructura de datos.")
            return False, "La primera columna no es 'ID'"
            
        # 3. Identificar filas sin ID y encontrar el máximo ID existente
        filas_sin_id = []
        max_id = 0
        
        for i, row in enumerate(values[1:], 2):  # Empezar en fila 2 (1-indexed)
            # Verificar si la fila tiene al menos una celda
            if not row:
                continue
                
            # Verificar si el ID está vacío o no es un número
            id_value = row[0] if row else ""
            if not id_value or not id_value.isdigit():
                filas_sin_id.append(i)
            else:
                # Actualizar max_id si encontramos uno mayor
                try:
                    current_id = int(id_value)
                    max_id = max(max_id, current_id)
                except ValueError:
                    pass
        
        # 4. Asignar IDs si hay filas que lo necesiten
        if not filas_sin_id:
            logger.info("Todas las filas ya tienen un ID asignado.")
            return True, "Todas las filas ya tienen ID"
            
        # Preparar actualizaciones por lotes
        next_id = max_id + 1
        updates = []
        
        for fila in filas_sin_id:
            updates.append({
                "range": f"edp!A{fila}",
                "values": [[str(next_id)]]
            })
            next_id += 1
        
        # 5. Aplicar actualizaciones en un solo lote (más eficiente)
        batch_update_body = {
            "valueInputOption": "USER_ENTERED",
            "data": updates
        }
        
        response = service.spreadsheets().values().batchUpdate(
            spreadsheetId=Config.SHEET_ID,
            body=batch_update_body
        ).execute()
        
        # 6. Reportar resultados
        ids_asignados = len(filas_sin_id)
        logger.info(f"Se asignaron IDs correlativos a {ids_asignados} filas (desde {max_id + 1} hasta {next_id - 1}).")
        
        return True, f"Se asignaron {ids_asignados} IDs correlativos"
        
    except Exception as e:
        import traceback
        error_msg = f"Error al asignar IDs: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return False, error_msg

if __name__ == "__main__":
    # Ejecutar el script directamente
    success, message = fill_missing_edp_ids()
    print(message)