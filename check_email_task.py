#!/usr/bin/env python3
"""
Script para verificar el estado de una tarea de email específica.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def check_task_status(task_id):
    """Verifica el estado de una tarea específica."""
    print(f"🔍 Verificando estado de la tarea: {task_id}")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/api/email/test/task-status/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                state = data.get("state", "UNKNOWN")
                
                print(f"   🔄 Intento {attempt + 1}/{max_attempts}: {state}")
                
                if state == "SUCCESS":
                    result = data.get("result", {})
                    print(f"✅ ¡Tarea completada exitosamente!")
                    print(f"   📧 Destinatarios: {result.get('recipients_count', 0)}")
                    print(f"   📧 Lista: {result.get('recipients', [])}")
                    print(f"   💬 Mensaje: {result.get('message', 'N/A')}")
                    return True
                elif state == "FAILURE":
                    print(f"❌ La tarea falló: {data.get('status', 'Error desconocido')}")
                    return False
                elif state == "PENDING":
                    print(f"   ⏳ Tarea en espera...")
                elif state == "PROGRESS":
                    print(f"   🔄 Tarea en progreso...")
                else:
                    print(f"   ❓ Estado desconocido: {state}")
                    print(f"   📄 Datos completos: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
                break
                
        except Exception as e:
            print(f"❌ Error al verificar estado: {e}")
            break
        
        if attempt < max_attempts - 1:
            time.sleep(2)  # Esperar 2 segundos entre verificaciones
    
    print(f"⏰ Tiempo de espera agotado para la tarea {task_id}")
    return False

def main():
    """Función principal."""
    print("📧 VERIFICACIÓN DE TAREA DE EMAIL")
    print("=" * 50)
    
    # Usar el task_id del resultado anterior
    task_id = "54b7cb3b-8aa8-4a0c-bb0d-555ba7a0b8e8"
    
    print(f"🎯 Verificando tarea: {task_id}")
    print("=" * 30)
    
    success = check_task_status(task_id)
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 ¡EMAIL ENVIADO EXITOSAMENTE!")
        print("📧 Revisa tu email: diegobravobe@gmail.com")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ PROBLEMA CON EL ENVÍO DE EMAIL")
        print("🔧 Verifica la configuración de Gmail SMTP")
        print("📖 Revisa los logs de la aplicación")
        print("=" * 50)

if __name__ == "__main__":
    main() 