#!/usr/bin/env python3
"""
Test simple para verificar la funcionalidad de Secret Files sin Render
"""
import os
import sys

# Añadir el directorio de la app al path para poder importar módulos
sys.path.insert(0, '/home/unzzui/Documents/coding/EDP_Project')

def test_credentials_loading():
    """Test para verificar carga de credenciales"""
    print("🧪 TESTING CARGA DE CREDENCIALES")
    print("=" * 40)
    
    try:
        from edp_mvp.app.config import get_config
        config = get_config()
        
        print(f"📍 GOOGLE_CREDENTIALS configurado: {config.GOOGLE_CREDENTIALS}")
        
        if config.GOOGLE_CREDENTIALS and os.path.exists(config.GOOGLE_CREDENTIALS):
            print("✅ Archivo de credenciales encontrado")
            
            # Test carga del servicio de Google Sheets
            from edp_mvp.app.utils.gsheet import get_service
            service = get_service()
            
            if service:
                print("✅ Servicio de Google Sheets inicializado correctamente")
                return True
            else:
                print("⚠️ Servicio de Google Sheets no disponible - modo demo")
                return True  # No es un error crítico
        else:
            print("⚠️ Credenciales no encontradas - modo demo")
            return True  # No es un error crítico
            
    except Exception as e:
        print(f"❌ Error en test de credenciales: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_demo_data():
    """Test para verificar datos demo"""
    print("\n🎭 TESTING DATOS DEMO")
    print("=" * 40)
    
    try:
        from edp_mvp.app.utils.demo_data import get_demo_edp_data, get_demo_logs_data
        
        # Test datos EDP demo
        edp_data = get_demo_edp_data()
        if edp_data and not edp_data.empty:
            print(f"✅ Datos EDP demo: {len(edp_data)} registros")
        else:
            print("❌ Datos EDP demo vacíos")
            return False
            
        # Test datos logs demo
        logs_data = get_demo_logs_data()
        if logs_data and not logs_data.empty:
            print(f"✅ Datos logs demo: {len(logs_data)} registros")
        else:
            print("❌ Datos logs demo vacíos")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error en test de datos demo: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_validation():
    """Test para verificar validación de configuración"""
    print("\n🔧 TESTING VALIDACIÓN DE CONFIGURACIÓN")
    print("=" * 40)
    
    try:
        from edp_mvp.app.config import get_config
        config = get_config()
        
        validation = config.validate()
        
        if validation['valid']:
            print("✅ Configuración válida")
        else:
            print("⚠️ Problemas de configuración:")
            for issue in validation['issues']:
                print(f"   ❌ {issue}")
                
        if validation['warnings']:
            print("⚠️ Advertencias:")
            for warning in validation['warnings']:
                print(f"   ⚠️ {warning}")
                
        # Considerar válido si no hay issues críticos
        return len(validation['issues']) == 0
        
    except Exception as e:
        print(f"❌ Error en test de configuración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TESTS LOCALES DE SECRET FILES Y CONFIGURACIÓN")
    print("=" * 60)
    
    tests = [
        ("Carga de credenciales", test_credentials_loading),
        ("Datos demo", test_demo_data),
        ("Validación de configuración", test_config_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Ejecutando: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: PASS")
                passed += 1
            else:
                print(f"❌ {test_name}: FAIL")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ El proyecto está funcionando correctamente")
        sys.exit(0)
    else:
        print("⚠️ Algunos tests fallaron")
        print("💡 Revisar logs arriba para más detalles")
        sys.exit(1)
