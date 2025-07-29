#!/usr/bin/env python3
from edp_mvp.app import create_app
from edp_mvp.app.extensions import socketio
from dotenv import load_dotenv
import os
import socket

load_dotenv()

app = create_app()

def get_local_ip():
    """Obtiene la IP local de la máquina"""
    try:
        # Conectar a un servidor externo para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "192.168.1.100"  # IP por defecto si no se puede obtener

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 5000
    
    print("\n" + "="*60)
    print("🚀 SERVIDOR EDP INICIANDO...")
    print("="*60)
    print(f"📍 Servidor disponible en:")
    print(f"   • Local:    http://localhost:{port}")
    print(f"   • Red:      http://127.0.0.1:{port}")
    print(f"   • Red LAN:  http://{local_ip}:{port}")
    print("="*60)
    print("💡 Para acceder desde otros dispositivos en la red:")
    print(f"   Usar: http://{local_ip}:{port}")
    print("="*60)
    print("⚠️  Asegúrate de que el firewall permita conexiones en el puerto 5000")
    print("🔥 Presiona Ctrl+C para detener el servidor")
    print("="*60)
    
    try:
        # Configuración para acceso desde la red local
        socketio.run(
            app, 
            host="0.0.0.0",  # Permite acceso desde cualquier IP de la red
            port=port, 
            debug=True,
            allow_unsafe_werkzeug=True  # Permite Werkzeug en modo debug con host 0.0.0.0
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
