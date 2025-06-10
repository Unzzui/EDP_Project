import os
from dotenv import load_dotenv
from pathlib import Path

# Construir la ruta absoluta al archivo .env
env_path = Path("/Users/diegobravo/Documents/Coding_Projects/EDP/EDP_Project/.env")
# O encontrarlo de forma relativa a tu script
# env_path = Path(__file__).parent.parent / '.env'

# Cargar variables con ruta explícita
load_dotenv(dotenv_path=env_path)

# Verificar
print(f"SHEET_ID: {os.getenv('SHEET_ID')}")
print(f"GOOGLE_CREDENTIALS: {os.getenv('GOOGLE_CREDENTIALS')}")
print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")
