/**
 * Google Apps Script para automatizar la invalidación de cache
 * cuando los datos cambian en Google Sheets
 * 
 * Instalar este script en Google Apps Script y configurar triggers
 * para que se ejecute cuando las hojas cambien.
 */

// Configuración
const WEBHOOK_URL = 'YOUR_FLASK_APP_URL/manager/webhook/data-changed';
const WEBHOOK_KEY = 'default_key_123'; // Debe coincidir con CACHE_WEBHOOK_KEY en Flask

/**
 * Función principal que se ejecuta cuando hay cambios en la hoja
 */
function onEdit(e) {
  try {
    const sheet = e.source.getActiveSheet();
    const sheetName = sheet.getName().toLowerCase();
    
    // Solo procesar hojas específicas
    if (!['edp', 'proyectos', 'costos'].includes(sheetName)) {
      return;
    }
    
    const range = e.range;
    const editedRange = `${range.getA1Notation()}`;
    
    console.log(`Cambio detectado en hoja: ${sheetName}, rango: ${editedRange}`);
    
    // Determinar el tipo de cambio
    let changeType = 'edp_updated';
    if (sheetName === 'proyectos') changeType = 'project_updated';
    if (sheetName === 'costos') changeType = 'cost_updated';
    
    // Obtener IDs afectados si es posible
    const affectedIds = getAffectedIds(sheet, range);
    
    // Enviar webhook
    notifyCacheInvalidation(changeType, affectedIds, {
      sheet_name: sheetName,
      edited_range: editedRange,
      timestamp: new Date().toISOString(),
      user: Session.getActiveUser().getEmail()
    });
    
  } catch (error) {
    console.error('Error en onEdit:', error);
  }
}

/**
 * Función que se ejecuta cuando hay cambios masivos (importación, etc.)
 */
function onBulkChange(sheetName, recordCount) {
  try {
    notifyCacheInvalidation('data_import', [], {
      sheet_name: sheetName,
      record_count: recordCount,
      timestamp: new Date().toISOString(),
      type: 'bulk_import'
    });
    
    console.log(`Invalidación de cache enviada para cambio masivo en ${sheetName}`);
    
  } catch (error) {
    console.error('Error en onBulkChange:', error);
  }
}

/**
 * Obtiene los IDs de registros afectados basado en el rango editado
 */
function getAffectedIds(sheet, range) {
  try {
    const startRow = range.getRow();
    const numRows = range.getNumRows();
    const affectedIds = [];
    
    // Asumiendo que la primera columna contiene el ID o N_EDP
    for (let i = startRow; i < startRow + numRows; i++) {
      const cellValue = sheet.getRange(i, 1).getValue();
      if (cellValue && cellValue.toString().trim()) {
        affectedIds.push(cellValue.toString());
      }
    }
    
    return affectedIds;
    
  } catch (error) {
    console.error('Error obteniendo IDs afectados:', error);
    return [];
  }
}

/**
 * Envía notificación de invalidación de cache al webhook
 */
function notifyCacheInvalidation(changeType, affectedRecords, metadata) {
  try {
    const payload = {
      webhook_key: WEBHOOK_KEY,
      change_type: changeType,
      affected_records: affectedRecords,
      source_system: 'google_sheets',
      timestamp: new Date().toISOString(),
      metadata: metadata
    };
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      payload: JSON.stringify(payload)
    };
    
    const response = UrlFetchApp.fetch(WEBHOOK_URL, options);
    const responseData = JSON.parse(response.getContentText());
    
    if (responseData.success) {
      console.log('✅ Cache invalidation webhook enviado exitosamente');
    } else {
      console.error('❌ Error en webhook response:', responseData.error);
    }
    
  } catch (error) {
    console.error('❌ Error enviando webhook:', error);
    
    // Opcional: guardar en una hoja de log para debugging
    logWebhookError(changeType, affectedRecords, error.toString());
  }
}

/**
 * Registra errores de webhook para debugging
 */
function logWebhookError(changeType, affectedRecords, error) {
  try {
    const logSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('webhook_log');
    if (!logSheet) {
      // Crear hoja de log si no existe
      const newLogSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet('webhook_log');
      newLogSheet.getRange(1, 1, 1, 5).setValues([
        ['Timestamp', 'Change Type', 'Affected Records', 'Error', 'Status']
      ]);
    }
    
    const logSheet2 = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('webhook_log');
    logSheet2.appendRow([
      new Date().toISOString(),
      changeType,
      affectedRecords.join(', '),
      error,
      'ERROR'
    ]);
    
  } catch (logError) {
    console.error('Error logging webhook error:', logError);
  }
}

/**
 * Función de testing manual
 */
function testWebhook() {
  notifyCacheInvalidation('test_event', ['TEST-001'], {
    test: true,
    timestamp: new Date().toISOString()
  });
}

/**
 * Función para configurar triggers automáticamente
 */
function setupTriggers() {
  // Eliminar triggers existentes
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => ScriptApp.deleteTrigger(trigger));
  
  // Crear nuevo trigger para cambios en la hoja
  ScriptApp.newTrigger('onEdit')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onEdit()
    .create();
    
  console.log('Triggers configurados exitosamente');
}

/**
 * Función para validar la configuración
 */
function validateSetup() {
  console.log('=== VALIDACIÓN DE CONFIGURACIÓN ===');
  console.log('Webhook URL:', WEBHOOK_URL);
  console.log('Webhook Key configurado:', WEBHOOK_KEY ? 'Sí' : 'No');
  console.log('Spreadsheet ID:', SpreadsheetApp.getActiveSpreadsheet().getId());
  console.log('Hojas disponibles:', SpreadsheetApp.getActiveSpreadsheet().getSheets().map(s => s.getName()));
  
  // Test de conectividad
  try {
    testWebhook();
    console.log('✅ Test de webhook exitoso');
  } catch (error) {
    console.log('❌ Test de webhook falló:', error);
  }
}
