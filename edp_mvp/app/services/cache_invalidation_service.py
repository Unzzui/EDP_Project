"""
Cache Invalidation Service - Sistema de invalidación de cache basado en eventos.
Invalida cache automáticamente cuando los datos cambian.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import redis
    import os
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(redis_url) if redis_url else None
except ImportError:
    redis_client = None

from . import BaseService, ServiceResponse

logger = logging.getLogger(__name__)


class CacheInvalidationService(BaseService):
    """Service for managing cache invalidation based on data changes."""
    
    def __init__(self):
        super().__init__()
        self.redis_client = redis_client
        self.cache_dependencies = {
            # Qué tipos de cache dependen de qué tablas/datos
            'manager_dashboard': ['edps', 'projects', 'costs'],
            'kpis': ['edps', 'projects'],
            'charts': ['edps', 'projects', 'costs'],
            'financials': ['edps', 'costs'],
            'analytics': ['edps', 'projects'],
            'kanban': ['edps'],
            'cashflow': ['edps', 'costs']
        }
        
        # Mapeo de operaciones a tipos de datos afectados
        self.operation_mapping = {
            'edp_created': ['edps'],
            'edp_updated': ['edps'],
            'edp_deleted': ['edps'],
            'edp_state_changed': ['edps'],
            'project_updated': ['projects'],
            'cost_updated': ['costs'],
            'bulk_edp_update': ['edps'],
            'data_import': ['edps', 'projects', 'costs']
        }
    
    def register_data_change(self, operation: str, affected_ids: Optional[List[str]] = None, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Registra un cambio en los datos y dispara la invalidación de cache correspondiente.
        
        Args:
            operation: Tipo de operación (edp_updated, project_updated, etc.)
            affected_ids: IDs de registros afectados
            metadata: Metadata adicional sobre el cambio
        """
        try:
            if not self.redis_client:
                logger.warning("Redis no disponible - no se puede invalidar cache")
                return True
            
            # Determinar qué tipos de datos fueron afectados
            affected_data_types = self.operation_mapping.get(operation, ['edps'])
            
            # Determinar qué tipos de cache necesitan invalidación
            cache_types_to_invalidate = set()
            for data_type in affected_data_types:
                for cache_type, dependencies in self.cache_dependencies.items():
                    if data_type in dependencies:
                        cache_types_to_invalidate.add(cache_type)
            
            # Registrar el evento
            change_event = {
                'operation': operation,
                'affected_data_types': affected_data_types,
                'affected_ids': affected_ids or [],
                'cache_types_to_invalidate': list(cache_types_to_invalidate),
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Guardar el evento en Redis para auditoría
            event_key = f"cache_events:{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.redis_client.setex(event_key, 3600, json.dumps(change_event))  # 1 hora de retención
            
            # Ejecutar invalidación
            invalidated_count = self._invalidate_cache_types(cache_types_to_invalidate)
            
            logger.info(f"✅ Data change registered: {operation} -> invalidated {invalidated_count} cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Error registering data change: {e}")
            return False
    
    def _invalidate_cache_types(self, cache_types: set) -> int:
        """Invalida los tipos de cache especificados."""
        total_invalidated = 0
        
        for cache_type in cache_types:
            try:
                # Patrones de cache para cada tipo
                patterns = self._get_cache_patterns(cache_type)
                
                for pattern in patterns:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        deleted = self.redis_client.delete(*keys)
                        total_invalidated += deleted
                        logger.info(f"Invalidated {deleted} keys for pattern: {pattern}")
                        
            except Exception as e:
                logger.error(f"Error invalidating cache type {cache_type}: {e}")
        
        return total_invalidated
    
    def _get_cache_patterns(self, cache_type: str) -> List[str]:
        """Obtiene los patrones de cache para un tipo específico."""
        patterns = {
            'manager_dashboard': [
                'manager_dashboard:*',
                'manager_dashboard:*:meta',
                'manager_dashboard:*:stale'
            ],
            'kpis': [
                'kpis:*',
                'executive_kpis:*',
                'all_kpis:*'
            ],
            'charts': [
                'charts:*',
                'chart_data:*'
            ],
            'financials': [
                'financials:*',
                'financial_metrics:*'
            ],
            'analytics': [
                'analytics:*',
                'global_analytics:*'
            ],
            'kanban': [
                'kanban:*'
            ],
            'cashflow': [
                'cashflow:*',
                'cash_forecast:*'
            ]
        }
        
        return patterns.get(cache_type, [f'{cache_type}:*'])
    
    def force_invalidate_all(self) -> Dict[str, Any]:
        """Fuerza la invalidación de todo el cache del dashboard."""
        try:
            if not self.redis_client:
                return {'success': False, 'message': 'Redis not available'}
            
            all_patterns = []
            for cache_type in self.cache_dependencies.keys():
                all_patterns.extend(self._get_cache_patterns(cache_type))
            
            total_invalidated = 0
            results = {}
            
            for pattern in set(all_patterns):  # Remove duplicates
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    total_invalidated += deleted
                    results[pattern] = deleted
            
            # Registrar evento de invalidación total
            self.register_data_change('force_invalidate_all', metadata={
                'total_invalidated': total_invalidated,
                'patterns': results
            })
            
            return {
                'success': True,
                'total_invalidated': total_invalidated,
                'patterns_cleared': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in force invalidate all: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_cache_health_report(self) -> Dict[str, Any]:
        """Genera un reporte de salud del cache."""
        try:
            if not self.redis_client:
                return {'redis_available': False}
            
            health_report = {
                'redis_available': True,
                'timestamp': datetime.now().isoformat(),
                'cache_types': {}
            }
            
            for cache_type in self.cache_dependencies.keys():
                patterns = self._get_cache_patterns(cache_type)
                type_stats = {
                    'total_keys': 0,
                    'patterns': {}
                }
                
                for pattern in patterns:
                    keys = self.redis_client.keys(pattern)
                    pattern_count = len(keys)
                    type_stats['total_keys'] += pattern_count
                    type_stats['patterns'][pattern] = pattern_count
                
                health_report['cache_types'][cache_type] = type_stats
            
            # Eventos recientes
            event_keys = self.redis_client.keys('cache_events:*')
            health_report['recent_events'] = len(event_keys)
            
            return health_report
            
        except Exception as e:
            logger.error(f"Error generating cache health report: {e}")
            return {'redis_available': False, 'error': str(e)}
    
    def setup_auto_invalidation_hooks(self):
        """
        Configura hooks automáticos para invalidación de cache.
        Esto se llamaría desde los servicios que modifican datos.
        """
        # Esta función se usaría para configurar decoradores o hooks
        # que automáticamente llamen a register_data_change cuando se modifiquen datos
        pass


# Decorador para marcar automáticamente cambios de datos
def invalidate_cache_on_change(operation: str, data_types: List[str] = None):
    """
    Decorador que automáticamente invalida cache cuando se ejecuta una función.
    
    Usage:
        @invalidate_cache_on_change('edp_updated', ['edps'])
        def update_edp(self, edp_id, data):
            # ... código que actualiza EDP
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Ejecutar la función original
                result = func(*args, **kwargs)
                
                # Si la función fue exitosa, invalidar cache
                should_invalidate = False
                
                # Verificar diferentes formatos de resultado exitoso
                if isinstance(result, dict) and result.get('success'):
                    should_invalidate = True
                elif hasattr(result, 'success') and result.success:
                    should_invalidate = True
                elif result is True:  # Para funciones que devuelven True directamente
                    should_invalidate = True
                elif result is not None and result is not False:  # Para funciones que devuelven objetos/valores
                    should_invalidate = True
                
                if should_invalidate:
                    invalidation_service = CacheInvalidationService()
                    invalidation_service.register_data_change(
                        operation=operation,
                        metadata={'function': func.__name__, 'args_count': len(args)}
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in cache invalidation decorator: {e}")
                # Continuar con la función original incluso si la invalidación falla
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
