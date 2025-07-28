#!/usr/bin/env python3
"""
Comando rápido para gestionar el sistema de alertas progresivas.
"""
import sys
import os
import argparse
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_progressive_alerts():
    """Ejecutar alertas progresivas"""
    print("🚨 EJECUTANDO ALERTAS PROGRESIVAS...")
    
    from edp_mvp.app import create_app
    from edp_mvp.app.services.alert_service import EDPAlertService
    
    app = create_app()
    
    with app.app_context():
        alert_service = EDPAlertService()
        results = alert_service.send_progressive_alerts()
        
        print(f"✅ Resultados:")
        print(f"   📊 EDPs procesados: {results['total_edps_processed']}")
        print(f"   📧 Alertas enviadas: {results['alerts_sent']}")
        print(f"   ⏭️ Alertas omitidas: {results['alerts_skipped']}")
        print(f"   ❌ Errores: {results['errors']}")

def send_test_alert(email):
    """Enviar alerta de prueba"""
    print(f"🧪 ENVIANDO ALERTA DE PRUEBA A: {email}")
    
    from edp_mvp.app import create_app
    from edp_mvp.app.services.alert_service import EDPAlertService
    
    app = create_app()
    
    with app.app_context():
        alert_service = EDPAlertService()
        results = alert_service.test_alert_system(email)
        
        print(f"✅ Prueba completada:")
        print(f"   📧 Email enviado: {'✅' if results.get('email_sent') else '❌'}")
        print(f"   📧 Destinatario: {results.get('test_recipient', 'N/A')}")

def show_edps_status():
    """Mostrar estado de EDPs"""
    print("📊 ESTADO ACTUAL DE EDPs...")
    
    from edp_mvp.app import create_app
    from edp_mvp.app.services.alert_service import EDPAlertService
    
    app = create_app()
    
    with app.app_context():
        alert_service = EDPAlertService()
        edps = alert_service.get_edps_for_alerts()
        
        if not edps:
            print("   ✅ No hay EDPs que requieran alertas")
            return
        
        critical = len([e for e in edps if e['is_critical']])
        urgent = len([e for e in edps if e['dias_sin_movimiento'] >= 21 and not e['is_critical']])
        warning = len([e for e in edps if e['dias_sin_movimiento'] >= 14 and e['dias_sin_movimiento'] < 21])
        info = len([e for e in edps if e['dias_sin_movimiento'] >= 7 and e['dias_sin_movimiento'] < 14])
        
        print(f"   📊 Total EDPs con alertas: {len(edps)}")
        print(f"   🚨 Críticos (30+ días): {critical}")
        print(f"   ⚠️ Urgentes (21-29 días): {urgent}")
        print(f"   📋 Advertencia (14-20 días): {warning}")
        print(f"   ℹ️ Informativos (7-13 días): {info}")
        
        print(f"\n   📋 Detalle de EDPs críticos:")
        for edp in edps:
            if edp['is_critical']:
                print(f"      • EDP {edp['n_edp']}: {edp['dias_sin_movimiento']} días ({edp['cliente']})")

def send_critical_summary():
    """Enviar resumen crítico"""
    print("📊 ENVIANDO RESUMEN CRÍTICO...")
    
    from edp_mvp.app import create_app
    from edp_mvp.app.services.alert_service import EDPAlertService
    
    app = create_app()
    
    with app.app_context():
        alert_service = EDPAlertService()
        results = alert_service.send_daily_critical_summary()
        
        print(f"✅ Resumen enviado:")
        print(f"   📊 EDPs críticos: {results.get('critical_edps_count', 0)}")
        print(f"   📧 Email enviado: {'✅' if results.get('email_sent') else '❌'}")

def start_celery_worker():
    """Iniciar worker de Celery"""
    print("🔄 INICIANDO CELERY WORKER...")
    os.system("celery -A edp_mvp.app.celery worker --loglevel=info --pool=solo")

def start_celery_beat():
    """Iniciar scheduler de Celery"""
    print("⏰ INICIANDO CELERY BEAT...")
    os.system("celery -A edp_mvp.app.celery beat --loglevel=info")

def main():
    parser = argparse.ArgumentParser(description='Gestión de alertas progresivas EDP')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando: run
    subparsers.add_parser('run', help='Ejecutar alertas progresivas')
    
    # Comando: test
    test_parser = subparsers.add_parser('test', help='Enviar alerta de prueba')
    test_parser.add_argument('email', help='Email de destino para la prueba')
    
    # Comando: status
    subparsers.add_parser('status', help='Mostrar estado de EDPs')
    
    # Comando: summary
    subparsers.add_parser('summary', help='Enviar resumen crítico')
    
    # Comando: worker
    subparsers.add_parser('worker', help='Iniciar Celery worker')
    
    # Comando: beat
    subparsers.add_parser('beat', help='Iniciar Celery beat scheduler')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print(f"🚀 COMANDO: {args.command.upper()}")
    print(f"⏰ Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 50)
    
    try:
        if args.command == 'run':
            run_progressive_alerts()
        elif args.command == 'test':
            send_test_alert(args.email)
        elif args.command == 'status':
            show_edps_status()
        elif args.command == 'summary':
            send_critical_summary()
        elif args.command == 'worker':
            start_celery_worker()
        elif args.command == 'beat':
            start_celery_beat()
        
        print("-" * 50)
        print("✅ COMANDO COMPLETADO")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
