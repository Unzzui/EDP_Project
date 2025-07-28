#!/usr/bin/env python3
"""
Script para verificar que toda la configuración de emails apunte a diegobravobe@gmail.com
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edp_mvp.app.config.alert_rules import (
    PROJECT_MANAGER_EMAILS, 
    CONTROLLER_EMAILS, 
    MANAGER_EMAILS,
    get_recipients_by_type
)

def verificar_configuracion_emails():
    """Verificar que todos los emails estén configurados correctamente para pruebas"""
    print("🔍 VERIFICANDO CONFIGURACIÓN DE EMAILS PARA PRUEBAS")
    print("=" * 60)
    
    test_email = "diegobravobe@gmail.com"
    all_correct = True
    
    # Verificar PROJECT_MANAGER_EMAILS
    print("\n1. 📋 PROJECT_MANAGER_EMAILS:")
    for manager, email in PROJECT_MANAGER_EMAILS.items():
        status = "✅" if email == test_email else "❌"
        if email != test_email:
            all_correct = False
        print(f"   {status} {manager}: {email}")
    
    # Verificar CONTROLLER_EMAILS  
    print("\n2. 🎛️ CONTROLLER_EMAILS:")
    for email in CONTROLLER_EMAILS:
        status = "✅" if email == test_email else "❌" 
        if email != test_email:
            all_correct = False
        print(f"   {status} {email}")
    
    # Verificar MANAGER_EMAILS
    print("\n3. 👔 MANAGER_EMAILS:")
    for email in MANAGER_EMAILS:
        status = "✅" if email == test_email else "❌"
        if email != test_email:
            all_correct = False
        print(f"   {status} {email}")
    
    # Probar función get_recipients_by_type
    print("\n4. 🧪 PROBANDO get_recipients_by_type:")
    
    test_cases = [
        ('project_manager', 'Juan Pérez'),
        ('controller', None),
        ('all', 'María González')
    ]
    
    for recipients_type, jefe_proyecto in test_cases:
        recipients = get_recipients_by_type(recipients_type, jefe_proyecto)
        print(f"   • Tipo '{recipients_type}' (jefe: {jefe_proyecto}): {recipients}")
        
        # Verificar que todos sean el email de prueba
        for recipient in recipients:
            if recipient != test_email:
                all_correct = False
                print(f"     ❌ Email incorrecto: {recipient}")
            else:
                print(f"     ✅ Email correcto: {recipient}")
    
    # Resultado final
    print(f"\n{'='*60}")
    if all_correct:
        print("✅ CONFIGURACIÓN CORRECTA: Todos los emails apuntan a diegobravobe@gmail.com")
    else:
        print("❌ ERROR EN CONFIGURACIÓN: Algunos emails no apuntan a diegobravobe@gmail.com")
    
    print("=" * 60)
    
    return all_correct

if __name__ == "__main__":
    verificar_configuracion_emails()
