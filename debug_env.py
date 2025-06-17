#!/usr/bin/env python3
"""
Script de debug para verificar variables de entorno en Render
"""
import os

def debug_env():
    """Debug environment variables"""
    print("🔍 DEBUGGER DE VARIABLES DE ENTORNO")
    print("=" * 50)
    
    # Variables críticas
    critical_vars = [
        'DATABASE_URL',
        'REDIS_URL', 
        'FLASK_ENV',
        'SECRET_KEY',
        'PORT'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Ocultar información sensible
            if var in ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']:
                display_value = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***HIDDEN***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print("\n🔍 ANÁLISIS DATABASE_URL:")
    database_url = os.getenv('DATABASE_URL', '')
    if database_url:
        print(f"📄 URL completa (primeros 50 chars): {database_url[:50]}...")
        
        # Detectar placeholders
        placeholders = ['username', 'password', 'hostname', 'port', 'database', 'host']
        found_placeholders = [p for p in placeholders if p in database_url.lower()]
        
        if found_placeholders:
            print(f"⚠️  PLACEHOLDERS DETECTADOS: {found_placeholders}")
            print("💡 Esto significa que Render aún no ha sustituido los valores reales")
        else:
            print("✅ No se detectaron placeholders - URL parece válida")
            
        # Análisis de esquema
        if database_url.startswith('postgres://'):
            print("🔧 URL usa esquema 'postgres://' - se convertirá a 'postgresql://'")
        elif database_url.startswith('postgresql://'):
            print("✅ URL usa esquema correcto 'postgresql://'")
        else:
            print(f"⚠️  Esquema desconocido: {database_url.split('://')[0] if '://' in database_url else 'N/A'}")
    else:
        print("❌ DATABASE_URL no configurado")
    
    print("\n🔍 ANÁLISIS REDIS_URL:")
    redis_url = os.getenv('REDIS_URL', '')
    if redis_url:
        print(f"📄 Redis URL (primeros 30 chars): {redis_url[:30]}...")
        if 'localhost' in redis_url:
            print("⚠️  URL contiene 'localhost' - probablemente no es correcto para producción")
        else:
            print("✅ Redis URL parece ser externo")
    else:
        print("❌ REDIS_URL no configurado")

if __name__ == "__main__":
    debug_env()
