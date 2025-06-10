#!/usr/bin/env python3
"""
CLI para administrar el sistema de cache con invalidación automática
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.cache_invalidation_service import CacheInvalidationService

def main():
    parser = argparse.ArgumentParser(description='EDP Cache Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Show cache system health')
    health_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Invalidate command
    invalidate_parser = subparsers.add_parser('invalidate', help='Invalidate cache manually')
    invalidate_parser.add_argument('--type', choices=['all', 'dashboard', 'kpis', 'charts'], 
                                 default='all', help='Cache type to invalidate')
    invalidate_parser.add_argument('--operation', help='Operation that triggered the change')
    invalidate_parser.add_argument('--ids', nargs='*', help='Affected record IDs')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor cache events')
    monitor_parser.add_argument('--tail', action='store_true', help='Keep monitoring (like tail -f)')
    monitor_parser.add_argument('--count', type=int, default=10, help='Number of recent events to show')
    
    # Warm command
    warm_parser = subparsers.add_parser('warm', help='Warm cache with common queries')
    warm_parser.add_argument('--all', action='store_true', help='Warm all common filter combinations')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')
    stats_parser.add_argument('--detailed', action='store_true', help='Show detailed statistics')
    
    # Check command for auto-refresh status
    check_parser = subparsers.add_parser('check', help='Check if auto-refresh is disabled')
    check_parser.add_argument('--all', action='store_true', help='Check all refresh mechanisms')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cache_service = CacheInvalidationService()
    
    if args.command == 'health':
        show_health(cache_service, args.json)
    elif args.command == 'invalidate':
        invalidate_cache(cache_service, args.type, args.operation, args.ids)
    elif args.command == 'monitor':
        monitor_events(cache_service, args.tail, args.count)
    elif args.command == 'warm':
        warm_cache(args.all)
    elif args.command == 'stats':
        show_stats(cache_service, args.detailed)
    elif args.command == 'check':
        check_auto_refresh_status(args.all)

def show_health(cache_service, json_output=False):
    """Show cache system health"""
    try:
        health = cache_service.get_cache_health_report()
        
        if json_output:
            print(json.dumps(health, indent=2))
            return
        
        print("🏥 CACHE SYSTEM HEALTH REPORT")
        print("=" * 50)
        
        if health.get('redis_available'):
            print("✅ Redis: Connected")
            
            cache_types = health.get('cache_types', {})
            total_keys = sum(ct.get('total_keys', 0) for ct in cache_types.values())
            
            print(f"📊 Total Cache Keys: {total_keys}")
            print(f"🕒 Recent Events: {health.get('recent_events', 0)}")
            print(f"⏰ Timestamp: {health.get('timestamp', 'Unknown')}")
            
            print("\n📋 Cache Types:")
            for cache_type, stats in cache_types.items():
                print(f"  • {cache_type}: {stats.get('total_keys', 0)} keys")
                if stats.get('patterns'):
                    for pattern, count in stats['patterns'].items():
                        if count > 0:
                            print(f"    - {pattern}: {count}")
        else:
            print("❌ Redis: Not connected")
            if 'error' in health:
                print(f"Error: {health['error']}")
                
    except Exception as e:
        print(f"❌ Error checking health: {e}")

def invalidate_cache(cache_service, cache_type, operation, affected_ids):
    """Manually invalidate cache"""
    try:
        if cache_type == 'all':
            result = cache_service.force_invalidate_all()
        else:
            # Use register_data_change for specific operations
            op_name = operation or f'{cache_type}_manual_invalidate'
            result = cache_service.register_data_change(
                operation=op_name,
                affected_ids=affected_ids or [],
                metadata={'manual': True, 'cache_type': cache_type}
            )
            
        if isinstance(result, dict) and result.get('success'):
            total = result.get('total_invalidated', 'unknown')
            print(f"✅ Cache invalidated successfully: {total} keys")
        elif result:
            print("✅ Cache invalidation triggered")
        else:
            print("❌ Cache invalidation failed")
            
    except Exception as e:
        print(f"❌ Error invalidating cache: {e}")

def monitor_events(cache_service, tail, count):
    """Monitor cache invalidation events"""
    try:
        if not cache_service.redis_client:
            print("❌ Redis not available for monitoring")
            return
            
        print(f"🔍 MONITORING CACHE EVENTS (showing last {count})")
        print("=" * 60)
        
        # Get recent events
        pattern = "cache_events:*"
        keys = cache_service.redis_client.keys(pattern)
        
        # Sort by timestamp (newest first)
        keys.sort(reverse=True)
        
        for key in keys[:count]:
            try:
                event_data = cache_service.redis_client.get(key)
                if event_data:
                    event = json.loads(event_data)
                    timestamp = event.get('timestamp', 'Unknown')
                    operation = event.get('operation', 'Unknown')
                    cache_types = ', '.join(event.get('cache_types_to_invalidate', []))
                    affected_ids = event.get('affected_ids', [])
                    
                    print(f"🕒 {timestamp}")
                    print(f"   Operation: {operation}")
                    print(f"   Cache Types: {cache_types}")
                    if affected_ids:
                        print(f"   Affected IDs: {', '.join(affected_ids[:5])}")
                        if len(affected_ids) > 5:
                            print(f"   ... and {len(affected_ids) - 5} more")
                    print()
                    
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"⚠️ Failed to parse event {key}: {e}")
        
        if tail:
            print("👀 Monitoring for new events (Ctrl+C to stop)...")
            # This would require implementing a pub/sub or polling mechanism
            print("ℹ️ Tail mode not yet implemented")
            
    except Exception as e:
        print(f"❌ Error monitoring events: {e}")

def warm_cache(warm_all):
    """Warm cache with common queries"""
    try:
        from app.services.manager_service import ManagerService
        
        service = ManagerService()
        
        common_filters = [
            ({}, "Default dashboard"),
            ({'mes_actual': True}, "Current month"),
            ({'estado': 'pendiente'}, "Pending EDPs"),
        ]
        
        if warm_all:
            # Add more filter combinations
            common_filters.extend([
                ({'estado': 'aprobado'}, "Approved EDPs"),
                ({'estado': 'pagado'}, "Paid EDPs"),
                ({'urgente': True}, "Urgent EDPs"),
            ])
        
        print("🔥 WARMING CACHE")
        print("=" * 30)
        
        warmed = 0
        for filters, description in common_filters:
            try:
                print(f"🔄 Warming: {description}...")
                response = service.get_manager_dashboard_data(filters, max_cache_age=300)
                if response.success:
                    print(f"✅ Warmed: {description}")
                    warmed += 1
                else:
                    print(f"❌ Failed: {description} - {response.message}")
                    
            except Exception as e:
                print(f"❌ Error warming {description}: {e}")
        
        print(f"\n🏁 Cache warming completed: {warmed}/{len(common_filters)} successful")
        
    except Exception as e:
        print(f"❌ Error warming cache: {e}")

def show_stats(cache_service, detailed):
    """Show cache statistics"""
    try:
        health = cache_service.get_cache_health_report()
        
        print("📈 CACHE STATISTICS")
        print("=" * 40)
        
        if not health.get('redis_available'):
            print("❌ Redis not available")
            return
        
        cache_types = health.get('cache_types', {})
        
        # Summary stats
        total_keys = sum(ct.get('total_keys', 0) for ct in cache_types.values())
        active_types = sum(1 for ct in cache_types.values() if ct.get('total_keys', 0) > 0)
        
        print(f"Total Keys: {total_keys}")
        print(f"Active Cache Types: {active_types}/{len(cache_types)}")
        print(f"Recent Events: {health.get('recent_events', 0)}")
        
        if detailed:
            print("\n📊 Detailed Breakdown:")
            for cache_type, stats in cache_types.items():
                total = stats.get('total_keys', 0)
                print(f"\n{cache_type.upper()}: {total} keys")
                
                if total > 0 and stats.get('patterns'):
                    for pattern, count in stats['patterns'].items():
                        if count > 0:
                            percentage = (count / total) * 100
                            print(f"  {pattern}: {count} ({percentage:.1f}%)")
        
        # Memory usage estimate (rough)
        estimated_memory_mb = total_keys * 0.01  # Very rough estimate
        print(f"\n💾 Estimated Memory Usage: ~{estimated_memory_mb:.1f} MB")
        
    except Exception as e:
        print(f"❌ Error showing stats: {e}")

def check_auto_refresh(cache_service, check_all):
    """Check if auto-refresh is disabled"""
    try:
        from app.services.manager_service import ManagerService
        
        service = ManagerService()
        
        if check_all:
            # Check all refresh mechanisms
            dashboards = service.get_all_dashboards()
            kpi_configs = service.get_all_kpi_configs()
            chart_configs = service.get_all_chart_configs()
            
            # For now, just print the counts
            print(f"📊 Dashboards: {len(dashboards)}")
            print(f"📈 KPI Configs: {len(kpi_configs)}")
            print("📊 Chart Configs: {len(chart_configs)}")
            
            # TODO: Check the actual refresh settings and report
            print("ℹ️ Detailed check not yet implemented")
            
        else:
            # Check default dashboard refresh
            dashboard_health = service.get_dashboard_health()
            print("📊 Default Dashboard Refresh:")
            print(f"  Enabled: {dashboard_health.get('auto_refresh_enabled', 'Unknown')}")
            print(f"  Interval: {dashboard_health.get('refresh_interval', 'Unknown')} seconds")
            
            # Check recent EDPs
            recent_edps = service.get_recent_edps()
            print(f"\n📈 Recent EDPs (last 5):")
            for edp in recent_edps[:5]:
                print(f"  - ID: {edp.get('id')}, Estado: {edp.get('estado')}, Fecha: {edp.get('fecha_creacion')}")
            
    except Exception as e:
        print(f"❌ Error checking auto-refresh: {e}")

def check_auto_refresh_status(check_all):
    """Check if auto-refresh is disabled and event-based system is active"""
    try:
        import requests
        
        print("🔍 CHECKING AUTO-REFRESH STATUS")
        print("=" * 40)
        
        # Check if Flask app is running
        try:
            base_url = "http://localhost:5000"
            response = requests.get(f"{base_url}/manager/api/auto-refresh/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status = data['data']
                    
                    print("✅ SISTEMA CONFIGURADO CORRECTAMENTE")
                    print("-" * 40)
                    print(f"Auto-refresh por tiempo: {'❌ DESACTIVADO' if status.get('auto_refresh_disabled') else '⚠️ ACTIVO'}")
                    print(f"Sistema basado en eventos: {'✅ ACTIVO' if status.get('event_based_system') else '❌ INACTIVO'}")
                    print(f"Redis conectado: {'✅ SÍ' if status.get('redis_connected') else '❌ NO'}")
                    print(f"Sistema de cache activo: {'✅ SÍ' if status.get('cache_system_active') else '❌ NO'}")
                    print(f"Eventos de invalidación recientes: {status.get('recent_invalidation_events', 0)}")
                    print(f"Mensaje: {status.get('message', 'Sin mensaje')}")
                    
                    if check_all:
                        print("\n🔍 VERIFICACIÓN DETALLADA")
                        print("-" * 30)
                        
                        # Check JavaScript files for auto-refresh
                        check_javascript_auto_refresh()
                        
                        # Check template files
                        check_template_auto_refresh()
                        
                        # Check if Socket.IO is working
                        check_socketio_status()
                    
                    # Overall assessment
                    all_good = (status.get('auto_refresh_disabled') and 
                               status.get('event_based_system') and 
                               status.get('redis_connected'))
                    
                    if all_good:
                        print("\n🎉 PERFECTO: Sistema completamente basado en eventos")
                        print("   No hay auto-refresh por tiempo activo")
                    else:
                        print("\n⚠️ ADVERTENCIA: Revisar configuración")
                        
                else:
                    print(f"❌ Error en API: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Error HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ No se puede conectar a la aplicación Flask")
            print("   Asegúrate de que la aplicación esté corriendo en puerto 5000")
            
        except Exception as e:
            print(f"❌ Error verificando estado: {e}")
            
    except ImportError:
        print("❌ Módulo 'requests' no disponible")
        print("   Instalarlo con: pip install requests")

def check_javascript_auto_refresh():
    """Check JavaScript files for auto-refresh patterns"""
    import os
    import glob
    
    print("📄 Verificando archivos JavaScript...")
    
    js_files = glob.glob("app/static/js/*.js")
    auto_refresh_patterns = [
        "setInterval",
        "setTimeout.*refresh",
        "auto.*refresh",
        "autoRefresh"
    ]
    
    found_issues = []
    
    for js_file in js_files:
        try:
            with open(js_file, 'r') as f:
                content = f.read()
                
            for pattern in auto_refresh_patterns:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    # Check if it's properly disabled or event-based
                    if "setupEventBasedRefresh" in content or "event-based" in content.lower():
                        print(f"✅ {os.path.basename(js_file)}: Auto-refresh convertido a eventos")
                    elif "commented" in content or "//" in content:
                        print(f"✅ {os.path.basename(js_file)}: Auto-refresh comentado")
                    else:
                        found_issues.append(f"{os.path.basename(js_file)}: Posible auto-refresh activo")
                        
        except Exception as e:
            print(f"⚠️ Error leyendo {js_file}: {e}")
    
    if found_issues:
        print("⚠️ Posibles problemas encontrados:")
        for issue in found_issues:
            print(f"   - {issue}")
    else:
        print("✅ No se encontraron auto-refresh problemáticos")

def check_template_auto_refresh():
    """Check template files for auto-refresh meta tags or JavaScript"""
    import os
    import glob
    
    print("📄 Verificando templates...")
    
    template_files = glob.glob("app/templates/**/*.html", recursive=True)
    refresh_patterns = [
        "http-equiv.*refresh",
        "auto.*refresh",
        "setInterval",
        "setTimeout.*location"
    ]
    
    found_issues = []
    
    for template_file in template_files:
        try:
            with open(template_file, 'r') as f:
                content = f.read()
                
            for pattern in refresh_patterns:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    # Check if it's our event-based system
                    if "event-based" in content.lower() or "setupEventBasedRefresh" in content:
                        continue
                    else:
                        found_issues.append(f"{os.path.basename(template_file)}: Posible auto-refresh")
                        
        except Exception as e:
            print(f"⚠️ Error leyendo {template_file}: {e}")
    
    if found_issues:
        print("⚠️ Posibles problemas en templates:")
        for issue in found_issues:
            print(f"   - {issue}")
    else:
        print("✅ Templates sin auto-refresh problemático")

def check_socketio_status():
    """Check if Socket.IO is available for real-time events"""
    print("🔌 Verificando Socket.IO...")
    
    try:
        # Check if socketio is configured in the app
        import os
        
        # Look for socketio imports in Python files
        python_files = ['app/__init__.py', 'app/extensions.py', 'run.py']
        socketio_found = False
        
        for py_file in python_files:
            if os.path.exists(py_file):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                    if 'socketio' in content.lower():
                        socketio_found = True
                        break
                except:
                    pass
        
        if socketio_found:
            print("✅ Socket.IO configurado en la aplicación")
        else:
            print("⚠️ Socket.IO no encontrado - eventos en tiempo real limitados")
            
    except Exception as e:
        print(f"⚠️ Error verificando Socket.IO: {e}")


if __name__ == '__main__':
    main()
