# Import tasks to ensure they are registered
from .metrics import refresh_manager_dashboard_async, refresh_executive_kpis

__all__ = ['refresh_manager_dashboard_async', 'refresh_executive_kpis']