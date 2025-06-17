# 🚨 SOLUCIÓN INMEDIATA - Problema "GOOGLE_CREDENTIALS es None" en Render

## 🎯 **PROBLEMA ACTUAL**

La aplicación en Render muestra:

```
❌ GOOGLE_CREDENTIALS es None o vacío
🎭 Activando modo demo
```

Esto significa que las variables de entorno **SÍ están configuradas** en Render, pero la aplicación no las está encontrando correctamente.

## 🔧 **SOLUCIÓN PASO A PASO**

### **1. VERIFICAR CONFIGURACIÓN EN RENDER**

**A. Variables de Entorno en Web Service:**

```
GOOGLE_APPLICATION_CREDENTIALS = /etc/secrets/edp-control-system-f3cfafc0093a.json
GOOGLE_CREDENTIALS = /etc/secrets/edp-control-system-f3cfafc0093a.json
SHEET_ID = [tu-google-sheet-id]
```

**B. Secret Files en Web Service:**

- **Filename**: `edp-control-system-f3cfafc0093a.json`
- **Content**: [JSON completo de Google Service Account]

### **2. HACER REDEPLOY CON ARCHIVOS ACTUALIZADOS**

Los archivos que hemos arreglado deben estar en tu repositorio:

- ✅ `entrypoint.sh` (recreado sin caracteres corruptos)
- ✅ `fix_render_secrets.py` (mejorado)
- ✅ `edp_mvp/app/config/__init__.py` (prioriza variables de entorno)
- ✅ `edp_mvp/app/utils/gsheet.py` (fallback robusto a demo)
- ✅ `diagnose_render.py` (diagnóstico completo)

**Comando para commit y push:**

```bash
git add .
git commit -m "Fix: Solved GOOGLE_CREDENTIALS None issue in Render"
git push origin main  # o production, según tu branch
```

### **3. VERIFICAR LOGS DESPUÉS DEL DEPLOY**

En los logs de Render, deberías ver:

**✅ SI FUNCIONA CORRECTAMENTE:**

```
🔧 Ejecutando como root - corrigiendo Secret Files...
✅ Script fix_render_secrets.py encontrado
✅ Copiado y verificado: edp-control-system-f3cfafc0093a.json
👤 Cambiando a usuario appuser...
🔍 Buscando credenciales Google en 11 ubicaciones...
✅ USANDO CREDENCIALES: /app/secrets/edp-control-system-f3cfafc0093a.json
✅ Servicio de Google Sheets inicializado correctamente
```

**⚠️ SI AÚN HAY PROBLEMAS:**

```
❌ GOOGLE_CREDENTIALS es None o vacío
🎭 Activando modo demo
```

### **4. DIAGNÓSTICO SI PERSISTE EL PROBLEMA**

**A. Añadir endpoint de diagnóstico temporal:**

1. En cualquier controlador, añade esta ruta temporal:

```python
@app.route('/debug-credentials')
def debug_credentials():
    import os
    return f"""
    <h1>Debug Credenciales</h1>
    <p>GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}</p>
    <p>GOOGLE_CREDENTIALS: {os.getenv('GOOGLE_CREDENTIALS')}</p>
    <p>SHEET_ID: {os.getenv('SHEET_ID')}</p>
    <p>/etc/secrets existe: {os.path.exists('/etc/secrets')}</p>
    <p>/app/secrets existe: {os.path.exists('/app/secrets')}</p>
    """
```

2. Visita `https://tu-app.onrender.com/debug-credentials`

**B. Verificar en logs de Render que aparezcan estas líneas:**

```
🔍 === DIAGNÓSTICO COMPLETO ===
📋 Variables de entorno importantes:
   ✅ GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/...
```

### **5. SI TODO FALLA - MODO DEMO TEMPORAL**

Si necesitas que la app funcione **YA** mientras solucionamos el problema de credenciales:

**A. En Render, elimina temporalmente las variables:**

- ❌ `GOOGLE_APPLICATION_CREDENTIALS`
- ❌ `GOOGLE_CREDENTIALS`

**B. Mantén solo:**

- ✅ `SHEET_ID` (puede estar vacío)

**C. La app funcionará en modo demo completo:**

```
🎭 Usando datos demo de EDP para edp!A:V
✅ Datos demo: 50 registros EDP, 100 logs
```

## 🎯 **RESULTADO ESPERADO**

Después de aplicar estos cambios, deberías ver en los logs:

```
✅ Servicio de Google Sheets inicializado correctamente
📧 Client Email: tu-service-account@proyecto.iam.gserviceaccount.com
📊 Datos cargados desde Google Sheets: edp!A:V
```

Y en la aplicación:

- ✅ **Dashboard con datos reales** de Google Sheets
- ✅ **KPIs calculados** con datos actuales
- ✅ **Funcionalidad completa** sin modo demo

## 🆘 **SI NECESITAS AYUDA INMEDIATA**

1. **Revisa logs de deploy** en Render Dashboard
2. **Verifica que las variables estén SET** (no vacías)
3. **Confirma que el Secret File esté subido** correctamente
4. **Haz un nuevo deploy** después de confirmar todo

**¡La aplicación DEBERÍA funcionar con Google Sheets real después de estos cambios!**
