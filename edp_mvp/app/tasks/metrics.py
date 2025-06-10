import json
from .. import celery
from ..services.manager_service import ManagerService
from ..services.analytics_service import AnalyticsService
from ..services.cashflow_service import CashflowService
from ..services.kanban_service import KanbanService
from ..services.kpi_service import KPIService
from ..repositories import _redis_client as redis_client


@celery.task(bind=True, max_retries=3)
def refresh_executive_kpis(self):
    """Calculate executive KPIs and cache the result."""
    service = ManagerService()
    response = service.get_manager_dashboard_data()
    data = response.data.get("executive_kpis", {}) if response.success else {}
    if redis_client:
        redis_client.setex("kpis:latest", 900, json.dumps(data))
    return data


@celery.task(bind=True, max_retries=3)
def refresh_kanban_metrics(self):
    """Compute Kanban metrics and cache the result."""
    service = KanbanService()
    response = service.get_kanban_data()
    data = response.data if response.success else {}
    if redis_client:
        redis_client.setex("kanban:metrics", 300, json.dumps(data))
    return data


@celery.task(bind=True, max_retries=3)
def refresh_cashflow(self):
    """Generate cashflow forecast and cache it."""
    service = CashflowService()
    response = service.generar_cash_forecast()
    data = response.data if response.success else {}
    if redis_client:
        redis_client.setex("cashflow:latest", 3600, json.dumps(data))
    return data


@celery.task(bind=True, max_retries=3)
def refresh_global_analytics(self):
    """Generate global analytics charts and cache them."""
    service = AnalyticsService()
    response = service.obtener_vista_global_encargados()
    data = response.data if response.success else {}
    if redis_client:
        redis_client.setex("analytics:global", 900, json.dumps(data))
    return data


@celery.task(bind=True, max_retries=3)
def refresh_all_kpis(self):
    """Calculate full KPI set across all EDPs."""
    service = KPIService()
    response = service.calculate_all_kpis()
    data = response.data if response.success else {}
    if redis_client:
        redis_client.setex("kpis:all", 900, json.dumps(data))
    return data
