#!/usr/bin/env python3
"""
Test rápido para verificar el modo demo
"""
import sys
import os

# Añadir el proyecto al path
sys.path.insert(0, '/home/unzzui/Documents/coding/EDP_Project')

def test_demo_mode():
    """Test del modo demo"""
    print("🎭 TESTING MODO DEMO")
    print("=" * 40)
    
    try:
        # Test 1: Datos demo de EDP
        from edp_mvp.app.utils.demo_data import get_demo_edp_data
        edp_df = get_demo_edp_data()
        
        if not edp_df.empty:
            print(f"✅ Datos demo EDP: {len(edp_df)} registros")
            print(f"   Columnas: {list(edp_df.columns)}")
        else:
            print("❌ Datos demo EDP vacíos")
            return False
            
        # Test 2: Datos demo de logs
        from edp_mvp.app.utils.demo_data import get_demo_logs_data
        logs_df = get_demo_logs_data()
        
        if not logs_df.empty:
            print(f"✅ Datos demo logs: {len(logs_df)} registros")
            print(f"   Columnas: {list(logs_df.columns)}")
        else:
            print("❌ Datos demo logs vacíos")
            return False
            
        # Test 3: Función read_sheet con modo demo
        from edp_mvp.app.utils.gsheet import read_sheet
        
        print("\n🔍 Testing read_sheet con modo demo...")
        
        # Simular que no hay Google Sheets disponible
        edp_data = read_sheet("edp!A:V")
        if not edp_data.empty:
            print(f"✅ read_sheet EDP funciona: {len(edp_data)} registros")
        else:
            print("❌ read_sheet EDP retorna vacío")
            return False
            
        logs_data = read_sheet("log!A:G") 
        if not logs_data.empty:
            print(f"✅ read_sheet logs funciona: {len(logs_data)} registros")
        else:
            print("❌ read_sheet logs retorna vacío")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TEST RÁPIDO DEL MODO DEMO")
    print("=" * 50)
    
    if test_demo_mode():
        print("\n🎉 ¡MODO DEMO FUNCIONA CORRECTAMENTE!")
        print("✅ La aplicación debería mostrar datos incluso sin Google Sheets")
        sys.exit(0)
    else:
        print("\n❌ Modo demo tiene problemas")
        print("💡 Revisar implementación de datos demo")
        sys.exit(1)
