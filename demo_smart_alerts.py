#!/usr/bin/env python3
"""
Demo del Sistema Inteligente de Alertas
Muestra cómo funciona la experiencia de usuario mejorada
"""
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edp_mvp.app import create_app
from edp_mvp.app.services.alert_service import EDPAlertService
from edp_mvp.app.services.smart_alert_service import AlertAction

def demo_smart_alerts():
    """Demostración del sistema inteligente de alertas"""
    print("🧠 DEMO: SISTEMA INTELIGENTE DE ALERTAS")
    print("=" * 60)
    print("🎯 Objetivo: Mejorar la experiencia del usuario y reducir el spam de emails")
    print()
    
    app = create_app()
    
    with app.app_context():
        alert_service = EDPAlertService()
        smart_service = alert_service.smart_alert_service
        
        # Simular un EDP crítico
        critical_edp = {
            'id': 'EDP-DEMO-001',
            'n_edp': 'EDP-DEMO-001',
            'cliente': 'Cliente Importante S.A.',
            'dias_sin_movimiento': 35,
            'estado': 'enviado'
        }
        
        # Simular regla crítica
        critical_rule = {
            'alert_level': 'critical',
            'frequency_hours': 24,
            'day_threshold': 30
        }
        
        print("📋 CASO DE USO: EDP Crítico (35 días sin movimiento)")
        print("-" * 50)
        print(f"• EDP: {critical_edp['n_edp']}")
        print(f"• Cliente: {critical_edp['cliente']}")
        print(f"• Días sin movimiento: {critical_edp['dias_sin_movimiento']}")
        print()
        
        # Escenario 1: Primera alerta
        print("🔄 ESCENARIO 1: Primera alerta crítica")
        should_send = smart_service.should_send_alert(critical_edp, critical_rule)
        print(f"   ¿Enviar alerta? {should_send} ✅")
        
        if should_send:
            smart_service.record_alert_sent(critical_edp, critical_rule)
            print("   📤 Alerta enviada y registrada")
        print()
        
        # Escenario 2: Usuario reconoce la alerta
        print("🔄 ESCENARIO 2: Usuario reconoce que vio la alerta")
        result = alert_service.acknowledge_alert(critical_edp['id'], 'acknowledged')
        print(f"   ✅ {result['message']}")
        print()
        
        # Escenario 3: Intentar enviar otra alerta inmediatamente
        print("🔄 ESCENARIO 3: Intento de enviar otra alerta inmediatamente")
        should_send = smart_service.should_send_alert(critical_edp, critical_rule)
        print(f"   ¿Enviar alerta? {should_send} ❌ (en cooldown)")
        print("   💡 Sistema inteligente previene spam")
        print()
        
        # Escenario 4: Usuario indica que está trabajando en el EDP
        print("🔄 ESCENARIO 4: Usuario indica que está trabajando en el caso")
        result = alert_service.acknowledge_alert(critical_edp['id'], 'in_progress')
        print(f"   ✅ {result['message']}")
        print()
        
        # Escenario 5: Obtener insights inteligentes
        print("🔄 ESCENARIO 5: Insights y recomendaciones inteligentes")
        insights = alert_service.get_alert_insights(critical_edp['id'])
        if 'smart_suggestions' in insights:
            suggestions = insights['smart_suggestions']
            print("   📊 Recomendaciones:")
            for action in suggestions.get('recommended_actions', []):
                print(f"      • {action}")
            
            for insight in suggestions.get('smart_insights', []):
                print(f"   💡 {insight}")
        print()
        
        # Mostrar configuración mejorada
        print("⚙️ MEJORAS IMPLEMENTADAS:")
        print("-" * 30)
        print("✅ Cooldowns inteligentes basados en acciones del usuario")
        print("✅ Límite máximo de 3 alertas por EDP por día")
        print("✅ Respeto por horarios laborales (9 AM - 6 PM)")
        print("✅ Frecuencias adaptativas según el historial")
        print("✅ Mensajes con instrucciones para pausar alertas")
        print("✅ Sistema de reconocimiento de acciones del usuario")
        print()
        
        print("📈 COMPARATIVA DE FRECUENCIAS:")
        print("-" * 30)
        print("❌ Antes: Críticos cada 12 horas (muy molesto)")
        print("✅ Ahora: Críticos cada 24 horas inicial, con cooldowns inteligentes")
        print()
        print("❌ Antes: Sin consideración de acciones del usuario")
        print("✅ Ahora: Si usuario reconoce → pausa de 24h automática")
        print("✅ Ahora: Si usuario trabaja en caso → pausa de 48h")
        print("✅ Ahora: Si usuario pausa → pausa de 72h")
        print()
        
        print("💬 EXPERIENCIA DE USUARIO:")
        print("-" * 25)
        print("• Los emails críticos incluyen instrucciones para pausar")
        print("• El sistema aprende del comportamiento del usuario")
        print("• Reduce automáticamente la frecuencia si hay mucha actividad")
        print("• Respeta horarios laborales para alertas no críticas")
        print("• Proporciona insights y recomendaciones contextuales")

def show_alert_frequency_comparison():
    """Muestra comparación de frecuencias antes y después"""
    print("\n" + "=" * 60)
    print("📊 COMPARATIVA DE FRECUENCIAS DE ALERTAS")
    print("=" * 60)
    
    scenarios = [
        {
            'name': 'EDP 7 días (INFO)',
            'old_freq': '168h (1 semana)',
            'new_freq': '168h (sin cambios)',
            'improvement': 'Sin cambios - frecuencia ya apropiada'
        },
        {
            'name': 'EDP 14 días (WARNING)', 
            'old_freq': '72h (3 días)',
            'new_freq': '96h (4 días)',
            'improvement': 'Menos presión, más tiempo para actuar'
        },
        {
            'name': 'EDP 21 días (URGENT)',
            'old_freq': '48h (2 días)',
            'new_freq': '72h (3 días)',
            'improvement': 'Reducción del estrés, manteniendo urgencia'
        },
        {
            'name': 'EDP 28 días (PRE-CRÍTICO)',
            'old_freq': '24h (diario)',
            'new_freq': '48h (cada 2 días)',
            'improvement': 'Menos spam, más efectivo'
        },
        {
            'name': 'EDP 30+ días (CRÍTICO)',
            'old_freq': '12h (muy agresivo)',
            'new_freq': '24h + cooldowns inteligentes',
            'improvement': '⭐ GRAN MEJORA: considera acciones del usuario'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"   ❌ Antes: {scenario['old_freq']}")
        print(f"   ✅ Ahora: {scenario['new_freq']}")
        print(f"   💡 Mejora: {scenario['improvement']}")

def main():
    """Función principal de la demo"""
    demo_smart_alerts()
    show_alert_frequency_comparison()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE BENEFICIOS")
    print("=" * 60)
    print("1. ❌ Reduce molestias: Menos emails innecesarios")
    print("2. 🧠 Sistema inteligente: Aprende del comportamiento")
    print("3. ⏰ Respeta horarios: Solo urgentes fuera de horario laboral")
    print("4. 🎯 Más efectivo: Alertas contextuales y accionables")
    print("5. 💬 Mejor UX: Usuarios pueden controlar las notificaciones")
    print("6. 📊 Insights útiles: Recomendaciones basadas en contexto")
    
    print("\n✅ El sistema ahora es MUCHO menos molesto y más inteligente!")

if __name__ == "__main__":
    main()
