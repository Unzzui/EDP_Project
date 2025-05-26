# ConformiTrack MVP

Control y trazabilidad de EDPs y conformidades (versión mínima).

## Pasos rápidos

```bash
# 1. Crear entorno
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Variables de entorno (ejemplo)
export SECRET_KEY="cambia-esto"
export GOOGLE_CREDENTIALS="/ruta/credenciales.json"
export SHEET_ID="tu_spreadsheet_id"

# 4. Ejecutar
python run.py
```

Luego visita `http://127.0.0.1:5000/login`

## Estructura
- `app/` módulos Flask
- `static/` estilos y JS
- `requirements.txt` dependencias
- `run.py` entrypoint
