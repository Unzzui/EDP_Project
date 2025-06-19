import json
import logging
from typing import Dict, Any
from .. import celery

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


@celery.task(bind=True, max_retries=3)
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


@celery.task(bind=True, max_retries=3)
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


@celery.task(bind=True, max_retries=3)
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


@celery.task(bind=True, max_retries=3)
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


@celery.task(bind=True, max_retries=3)
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


@celery.task(bind=True, max_retries=3)
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


@celery.task(bind=True, max_retries=3)
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


@celery.task(bind=True, max_retries=3)
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
