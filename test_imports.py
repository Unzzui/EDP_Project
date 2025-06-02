import sys
import os

# Agregar el directorio del proyecto al path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print("Probando imports...")

try:
    from edp_mvp.app import create_app
    print("✅ create_app import OK")
    
    app = create_app()
    print("✅ create_app() ejecutado OK")
    print(f"✅ App creada: {app}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()