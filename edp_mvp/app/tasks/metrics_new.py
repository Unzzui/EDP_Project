import json
import logging
from typing import Dict, Any
from datetime import datetime
from celery import current_app as celery_app

logger = logging.getLogger(__name__)

# Import services when needed to avoid circular imports
def get_manager_service():
    from ..services.manager_service import ManagerService
    return ManagerService()

def get_analytics_service():
    from ..services.analytics_service import AnalyticsService
    return AnalyticsService()

def get_cashflow_service():
    from ..services.cashflow_service import CashFlowService
    return CashFlowService()

def get_kanban_service():
    from ..services.control_panel_service import KanbanService
    return KanbanService()

def get_kpi_service():
    from ..services.kpi_service import KPIService
    return KPIService()

def get_redis_client():
    from ..repositories import _redis_client
    return _redis_client


@celery_app.task(bind=True, max_retries=3)
def refresh_executive_kpis(self):
    """Calculate executive KPIs and cache the result."""
    try:
        service = get_manager_service()
        response = service.get_manager_dashboard_data_sync()
        data = response.data.get("executive_kpis", {}) if response.success else {}
        
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex("kpis:latest", 900, json.dumps(data))
            logger.info("✅ Executive KPIs cached successfully")
        
        return data
    except Exception as e:
        logger.error(f"❌ Error refreshing executive KPIs: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def refresh_manager_dashboard_async(self, filters: Dict[str, Any] = None):
    """Asynchronously calculate complete dashboard data and cache it."""
    try:
        service = get_manager_service()
        response = service.get_manager_dashboard_data_sync(filters)
        
        if not response.success:
            logger.error(f"❌ Dashboard calculation failed: {response.message}")
            raise Exception(response.message)
        
        data = response.data
        
        # Cache with multiple keys for different access patterns
        redis_client = get_redis_client()
        if redis_client:
            # Generate cache key
            import hashlib
            filters_hash = hashlib.md5(json.dumps(filters or {}, sort_keys=True).encode()).hexdigest()[:12]
            cache_key = f"manager_dashboard:{filters_hash}"
            
            # Cache complete dashboard data
            redis_client.setex(cache_key, 300, json.dumps(data))
            
            # Cache individual components for faster access
            redis_client.setex(f"kpis:{filters_hash}", 600, json.dumps(data.get("executive_kpis", {})))
            redis_client.setex(f"charts:{filters_hash}", 900, json.dumps(data.get("chart_data", {})))
            redis_client.setex(f"financials:{filters_hash}", 1800, json.dumps(data.get("financial_metrics", {})))
            
            # Keep stale copy for fallback
            redis_client.setex(f"{cache_key}:stale", 1200, json.dumps(data))
            
            logger.info(f"✅ Dashboard data cached successfully: {cache_key}")
        
        return data
    except Exception as e:
        logger.error(f"❌ Error in dashboard async task: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def refresh_kanban_metrics(self):
    """Compute Kanban metrics and cache the result."""
    try:
        service = get_kanban_service()
        response = service.get_kanban_data()
        data = response.data if response.success else {}
        
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex("kanban:latest", 900, json.dumps(data))
            logger.info("✅ Kanban data cached successfully")
        
        return data
    except Exception as e:
        logger.error(f"❌ Error refreshing kanban metrics: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def refresh_cashflow(self):
    """Generate cashflow forecast and cache it."""
    try:
        service = get_cashflow_service()
        response = service.get_cashflow_data()
        data = response.data if response.success else {}
        
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex("cashflow:latest", 1800, json.dumps(data))
            logger.info("✅ Cashflow data cached successfully")
        
        return data
    except Exception as e:
        logger.error(f"❌ Error refreshing cashflow: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def refresh_global_analytics(self):
    """Generate global analytics charts and cache them."""
    try:
        service = get_analytics_service()
        response = service.get_analytics_data()
        data = response.data if response.success else {}
        
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex("analytics:latest", 1800, json.dumps(data))
            logger.info("✅ Global analytics cached successfully")
        
        return data
    except Exception as e:
        logger.error(f"❌ Error refreshing global analytics: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def refresh_all_kpis(self):
    """Calculate full KPI set across all EDPs."""
    try:
        service = get_kpi_service()
        response = service.get_all_kpis()
        data = response.data if response.success else {}
        
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex("all_kpis:latest", 1200, json.dumps(data))
            logger.info("✅ All KPIs cached successfully")
        
        return data
    except Exception as e:
        logger.error(f"❌ Error refreshing all KPIs: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def precompute_dashboard_variants(self):
    """Precompute dashboard data for common filter combinations."""
    try:
        service = get_manager_service()
        
        # Common filter combinations to precompute
        filter_combinations = [
            {},  # No filters
            {"estado": "enviado"},
            {"estado": "validado"},
            {"estado": "pagado"},
            {"departamento": "finanzas"},
            {"departamento": "operaciones"},
        ]
        
        results = {}
        for filters in filter_combinations:
            response = service.get_manager_dashboard_data_sync(filters)
            if response.success:
                results[str(filters)] = response.data
        
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex("dashboard:precomputed", 1800, json.dumps(results))
            logger.info(f"✅ Precomputed {len(results)} dashboard variants")
        
        return results
    except Exception as e:
        logger.error(f"❌ Error precomputing dashboards: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def cleanup_stale_cache(self):
    """Clean up old cache entries to prevent memory bloat."""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return {"cleaned": 0}
        
        # Patterns to clean up
        patterns = ["temp:*", "session:*", "*:expired"]
        cleaned_count = 0
        
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            for key in keys:
                ttl = redis_client.ttl(key)
                if ttl < 60:  # Less than 1 minute remaining
                    redis_client.delete(key)
                    cleaned_count += 1
        
        logger.info(f"✅ Cleaned up {cleaned_count} stale cache entries")
        return {"cleaned": cleaned_count}
    except Exception as e:
        logger.error(f"❌ Error cleaning cache: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def monitor_cache_system(self):
    """Monitor cache invalidation system health and performance."""
    try:
        from ..services.cache_invalidation_service import CacheInvalidationService
        
        cache_service = CacheInvalidationService()
        health_report = cache_service.get_cache_health_report()
        
        # Log health status
        if health_report.get('redis_available'):
            total_keys = sum(
                cache_type.get('total_keys', 0) 
                for cache_type in health_report.get('cache_types', {}).values()
            )
            recent_events = health_report.get('recent_events', 0)
            
            logger.info(f"📊 Cache System Health: {total_keys} keys, {recent_events} recent events")
            
            # Alert if too many cache keys (memory management)
            if total_keys > 10000:
                logger.warning(f"⚠️ High cache key count: {total_keys}. Consider cleanup.")
                
            # Alert if no recent invalidation events (might indicate system issues)
            if recent_events == 0:
                logger.warning("⚠️ No recent cache invalidation events detected")
                
        else:
            logger.error("❌ Redis not available for cache monitoring")
            
        return health_report
        
    except Exception as e:
        logger.error(f"❌ Error monitoring cache system: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def cleanup_cache_events(self):
    """Clean up old cache invalidation events to prevent memory bloat."""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return {"cleaned": 0, "message": "Redis not available"}
        
        # Clean old cache events (older than 24 hours)
        pattern = "cache_events:*"
        keys = redis_client.keys(pattern)
        cleaned_count = 0
        current_time = datetime.now()
        
        for key in keys:
            try:
                # Extract timestamp from key if possible
                timestamp_str = key.decode('utf-8').split(':')[-1]
                if len(timestamp_str) == 14:  # YYYYMMDDHHMMSS format
                    key_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                    age_hours = (current_time - key_time).total_seconds() / 3600
                    
                    if age_hours > 24:  # Older than 24 hours
                        redis_client.delete(key)
                        cleaned_count += 1
                        
            except (ValueError, UnicodeDecodeError):
                # If we can't parse the timestamp, delete keys older than TTL
                ttl = redis_client.ttl(key)
                if ttl < 300:  # Less than 5 minutes remaining
                    redis_client.delete(key)
                    cleaned_count += 1
        
        logger.info(f"✅ Cleaned up {cleaned_count} old cache events")
        return {"cleaned": cleaned_count, "message": f"Cleaned {cleaned_count} old events"}
        
    except Exception as e:
        logger.error(f"❌ Error cleaning cache events: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def auto_warm_cache(self):
    """Automatically warm frequently accessed cache entries."""
    try:
        from ..services.manager_service import ManagerService
        
        service = ManagerService()
        
        # Warm cache for common filter combinations
        common_filters = [
            {},  # No filters (default view)
            {'mes_actual': True},  # Current month
            {'estado': 'pendiente'},  # Pending EDPs
        ]
        
        warmed_count = 0
        for filters in common_filters:
            try:
                # This will populate cache if not present
                response = service.get_manager_dashboard_data(filters, max_cache_age=300)
                if response.success:
                    warmed_count += 1
                    logger.info(f"✅ Cache warmed for filters: {filters}")
                    
            except Exception as filter_error:
                logger.warning(f"Failed to warm cache for filters {filters}: {filter_error}")
                
        logger.info(f"🔥 Cache warming completed: {warmed_count} entries warmed")
        return {"warmed": warmed_count}
        
    except Exception as e:
        logger.error(f"❌ Error in cache warming: {e}")
        raise self.retry(countdown=60, exc=e)
