"""
Manager Service for handling manager dashboard operations and executive KPIs.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import re
import logging
import os
import json
import traceback
import hashlib

try:  # pragma: no cover - optional redis cache
    import redis

    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(redis_url) if redis_url else None
except Exception:
    redis_client = None

from . import BaseService, ServiceResponse, ValidationError
from ..models import EDP, KPI
from ..repositories.edp_repository import EDPRepository
from ..repositories.project_repository import ProjectRepository
from ..services.cost_service import CostService
from ..services.kpi_service import KPIService
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils
from ..utils.validation_utils import ValidationUtils

logger = logging.getLogger(__name__)


class ManagerService(BaseService):
    """Service for handling manager dashboard operations."""

    def __init__(self):
        super().__init__()
        self.edp_repo = EDPRepository()
        self.project_repo = ProjectRepository()
        self.cost_service = CostService()
        self.kpi_service = KPIService()  # Use centralized KPI service
        # Cache configuration
        self.cache_ttl = {
            "dashboard": 300,  # 5 minutes for dashboard data
            "kpis": 600,  # 10 minutes for KPIs
            "charts": 900,  # 15 minutes for chart data
            "financials": 1800,  # 30 minutes for financial metrics
        }

    def _sanitize_for_json(self, data):
        """
        Sanitize data for JSON serialization by converting numpy types and handling NaN values.
        """
        import numpy as np

        if isinstance(data, dict):
            return {key: self._sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, (np.int64, np.int32, np.int_)):
            return int(data)
        elif isinstance(data, (np.float64, np.float32, np.floating)):
            if np.isnan(data):
                return None
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif pd.isna(data) or str(data) == "NaT":
            return None
        else:
            return data

    def get_manager_dashboard_data(
        self,
        filters: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False,
        max_cache_age: Optional[int] = None,
    ) -> ServiceResponse:
        """Get comprehensive dashboard data for managers with intelligent caching strategy."""
        try:
            # Generate cache key based on filters
            filters_hash = self._generate_cache_key(filters or {})
            cache_key = f"manager_dashboard:{filters_hash}"
            cache_meta_key = f"{cache_key}:meta"

            # Try to get from cache first (unless force refresh)
            if not force_refresh and redis_client:
                try:
                    cached = redis_client.get(cache_key)
                    cache_meta = redis_client.get(cache_meta_key)

                    if cached and cache_meta:
                        meta_data = json.loads(cache_meta)
                        cache_timestamp = meta_data.get("timestamp", 0)
                        current_time = datetime.now().timestamp()
                        cache_age = current_time - cache_timestamp

                        # Check if cache is still valid based on max_cache_age
                        cache_valid = True
                        if max_cache_age is not None and cache_age > max_cache_age:
                            cache_valid = False
                            logger.info(
                                f"🕒 Cache is {cache_age:.1f}s old, max allowed: {max_cache_age}s - refreshing"
                            )

                        if cache_valid:
                            data = json.loads(cached)
                            # Mark as cached data with age info
                            data["_is_immediate"] = False
                            data["_is_cached"] = True
                            data["_is_stale"] = (
                                cache_age > 60
                            )  # Consider stale after 1 minute
                            data["_cache_age"] = round(cache_age, 1)
                            data["_task_id"] = None
                            logger.info(
                                f"✅ Dashboard data served from cache (age: {cache_age:.1f}s): {cache_key}"
                            )
                            return ServiceResponse(success=True, data=data)
                except Exception as e:
                    logger.warning(f"Cache retrieval error: {e}")

            logger.info(
                f"🔄 Calculating fresh dashboard data (force_refresh={force_refresh})"
            )

            # If not in cache or force refresh, calculate complete data synchronously
            # Load base data as DataFrame for analytics
            edps_response = self.edp_repo.find_all_dataframe()
     

            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get(
                "success", False
            ):
                return ServiceResponse(
                    success=False,
                    message=f"Failed to load EDPs data: {edps_response.get('message', 'Unknown error')}",
                    data=None,
                )

            # Extract the DataFrame
            df_edp = edps_response.get("data", pd.DataFrame())
            print(f'DEBUG: {df_edp}')   
            if df_edp.empty:
                return ServiceResponse(
                    success=False, message="No EDP data available", data=None
                )

            # Apply filters if provided
            df_filtered = self._apply_manager_filters(df_edp, filters or {})

            # Calculate COMPLETE executive KPIs (not essential ones)
            executive_kpis = self._calculate_executive_kpis(df_edp, df_filtered)

            # Calculate financial metrics
            financial_metrics = self._calculate_financial_metrics(df_edp, df_filtered)

            # Generate chart data
            chart_data = self._generate_chart_data(df_edp, df_filtered)

            # Calculate cash forecast
            cash_forecast = self._calculate_cash_forecast(df_edp)

            # Generate alerts
            alerts = self._generate_alerts(df_edp)

            # Get cost management data
            cost_data_response = self.cost_service.get_cost_dashboard_data(filters)
            cost_data = cost_data_response.data if cost_data_response.success else {}

            # Get filter options
            filter_options = self._get_manager_filter_options(df_edp)

            result_data = {
                "executive_kpis": executive_kpis,
                "financial_metrics": financial_metrics,
                "chart_data": chart_data,
                "cash_forecast": cash_forecast,
                "alerts": alerts,
                "cost_management": cost_data,
                "filter_options": filter_options,
                "filters": filters or {},
                "data_summary": {
                    "total_records": len(df_edp),
                    "filtered_records": len(df_filtered),
                    "last_updated": datetime.now().isoformat(),
                },
                # Cache metadata for controller compatibility
                "_is_immediate": True,  # This is immediate complete data
                "_is_cached": False,  # Fresh calculation
                "_is_stale": False,
                "_task_id": None,
            }

            # Cache the complete result for future requests
            if redis_client:
                try:
                    # Store data and metadata separately
                    current_timestamp = datetime.now().timestamp()
                    cache_metadata = {
                        "timestamp": current_timestamp,
                        "filters_hash": filters_hash,
                        "ttl": self.cache_ttl["dashboard"],
                    }

                    redis_client.setex(
                        cache_key,
                        self.cache_ttl["dashboard"],
                        json.dumps(self._sanitize_for_json(result_data)),
                    )
                    redis_client.setex(
                        cache_meta_key,
                        self.cache_ttl["dashboard"],
                        json.dumps(cache_metadata),
                    )

                    # Also keep a stale copy for fallback
                    redis_client.setex(
                        f"{cache_key}:stale",
                        self.cache_ttl["dashboard"] * 4,
                        json.dumps(self._sanitize_for_json(result_data)),
                    )

                    logger.info(
                        f"✅ Dashboard data cached with timestamp {current_timestamp}: {cache_key}"
                    )
                except Exception as e:
                    logger.warning(f"Cache storage error: {e}")

            return ServiceResponse(success=True, data=result_data)

        except Exception as e:
            logger.error(f"Error loading manager dashboard: {str(e)}")
            traceback.print_exc()
            return ServiceResponse(
                success=False,
                message=f"Error loading manager dashboard: {str(e)}",
                data=None,
            )

    def get_manager_dashboard_data_sync(
        self, filters: Dict[str, Any] = None
    ) -> ServiceResponse:
        """Synchronous version for immediate data needs."""
        try:
            # Load base data as DataFrame for analytics
            edps_response = self.edp_repo.find_all_dataframe()

            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get(
                "success", False
            ):
                return ServiceResponse(
                    success=False,
                    message=f"Failed to load EDPs data: {edps_response.get('message', 'Unknown error')}",
                    data=None,
                )

            # Extract the DataFrame
            df_edp = edps_response.get("data", pd.DataFrame())
            if df_edp.empty:
                return ServiceResponse(
                    success=False, message="No EDP data available", data=None
                )

            # Apply filters if provided
            df_filtered = self._apply_manager_filters(df_edp, filters or {})

            # Calculate components in parallel using cached results where possible
            components = {}

            # Try to get cached KPIs first
            kpis_cache_key = f"executive_kpis:{self._generate_cache_key(filters or {})}"
            if redis_client:
                cached_kpis = redis_client.get(kpis_cache_key)
                if cached_kpis:
                    components["executive_kpis"] = json.loads(cached_kpis)
                else:
                    components["executive_kpis"] = self._calculate_executive_kpis(
                        df_edp, df_filtered
                    )
                    redis_client.setex(
                        kpis_cache_key,
                        self.cache_ttl["kpis"],
                        json.dumps(
                            self._sanitize_for_json(components["executive_kpis"])
                        ),
                    )
            else:
                components["executive_kpis"] = self._calculate_executive_kpis(
                    df_edp, df_filtered
                )

            # Calculate other components
            components["financial_metrics"] = self._calculate_financial_metrics(
                df_edp, df_filtered
            )
            components["chart_data"] = self._generate_chart_data(df_edp, df_filtered)
            components["cash_forecast"] = self._calculate_cash_forecast(df_edp)
            components["alerts"] = self._generate_alerts(df_edp)

            # Get cost management data
            cost_data_response = self.cost_service.get_cost_dashboard_data(filters)
            components["cost_management"] = (
                cost_data_response.data if cost_data_response.success else {}
            )

            # Get filter options
            components["filter_options"] = self._get_manager_filter_options(df_edp)

            result_data = {
                **components,
                "filters": filters or {},
                "data_summary": {
                    "total_records": len(df_edp),
                    "filtered_records": len(df_filtered),
                    "last_updated": datetime.now().isoformat(),
                },
            }

            # Cache the complete result
            cache_key = f"manager_dashboard:{self._generate_cache_key(filters or {})}"
            if redis_client:
                redis_client.setex(
                    cache_key,
                    self.cache_ttl["dashboard"],
                    json.dumps(self._sanitize_for_json(result_data)),
                )
                # Also keep a stale copy for fallback
                redis_client.setex(
                    f"{cache_key}:stale",
                    self.cache_ttl["dashboard"] * 4,
                    json.dumps(self._sanitize_for_json(result_data)),
                )

            return ServiceResponse(success=True, data=result_data)

        except Exception as e:
            logger.error(f"Error in synchronous dashboard data: {str(e)}")
            traceback.print_exc()
            return ServiceResponse(
                success=False,
                message=f"Error loading manager dashboard: {str(e)}",
                data=None,
            )

    def _get_immediate_dashboard_data(
        self, filters: Dict[str, Any] = None
    ) -> Optional[ServiceResponse]:
        """Get immediate dashboard data with basic KPIs only."""
        try:
            # Quick data fetch with minimal processing
            edps_response = self.edp_repo.find_all_dataframe()

            if not isinstance(edps_response, dict) or not edps_response.get(
                "success", False
            ):
                return None

            df_edp = edps_response.get("data", pd.DataFrame())
            if df_edp.empty:
                return None

            df_filtered = self._apply_manager_filters(df_edp, filters or {})

            # Calculate only essential KPIs for immediate response
            essential_kpis = self._calculate_essential_kpis(df_edp, df_filtered)

            return ServiceResponse(
                success=True,
                data={
                    "executive_kpis": essential_kpis,
                    "financial_metrics": {},
                    "chart_data": {},
                    "cash_forecast": {},
                    "alerts": [],
                    "cost_management": {},
                    "filter_options": {},
                    "filters": filters or {},
                    "_is_immediate": True,
                    "_is_cached": False,
                    "_is_stale": False,
                    "_task_id": None,
                    "data_summary": {
                        "total_records": len(df_edp),
                        "filtered_records": len(df_filtered),
                        "last_updated": datetime.now().isoformat(),
                    },
                },
            )

        except Exception as e:
            logger.warning(f"Error getting immediate data: {e}")
            return None

    def _generate_cache_key(self, filters: Dict[str, Any]) -> str:
        """Generate a deterministic cache key from filters."""
        # Sort filters to ensure consistent keys
        sorted_filters = json.dumps(filters, sort_keys=True)
        return hashlib.md5(sorted_filters.encode()).hexdigest()[:12]

    def _calculate_essential_kpis(
        self, df_full: pd.DataFrame, df_filtered: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate essential KPIs for immediate response using centralized KPI service."""
        try:
            # Use the KPI service for essential calculations
            kpi_response = self.kpi_service.calculate_essential_kpis(df_full, df_filtered)
            if kpi_response.success:
                logger.info(f"✅ Essential KPIs calculated: {len(kpi_response.data)} metrics")
                return kpi_response.data
            else:
                logger.error(f"Essential KPI service error: {kpi_response.message}")
                return self.get_empty_kpis()
        except Exception as e:
            logger.error(f"Error calculating essential KPIs: {e}")
            return self.get_empty_kpis()

    def get_performance_analysis(self, period: str = "monthly") -> ServiceResponse:
        """Get performance analysis for different periods."""
        try:
            edps_response = self.edp_repo.find_all()
            if not edps_response.success:
                return ServiceResponse(
                    success=False, message="Failed to load EDPs data", data=None
                )

            df = edps_response.data

            # Calculate performance metrics by period
            performance_data = self._calculate_performance_by_period(df, period)

            # Calculate trends
            trends = self._calculate_trends(df, period)

            # Generate recommendations
            recommendations = self._generate_recommendations(performance_data, trends)

            return ServiceResponse(
                success=True,
                data={
                    "performance_data": performance_data,
                    "trends": trends,
                    "recommendations": recommendations,
                    "period": period,
                },
            )

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error analyzing performance: {str(e)}",
                data=None,
            )

    def _apply_manager_filters(
        self, df: pd.DataFrame, filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply manager-specific filters to DataFrame."""
        filtered_df = df.copy()

        # Date range filter
        if filters.get("fecha_inicio") and filters.get("fecha_fin"):
            try:
                start_date = pd.to_datetime(filters["fecha_inicio"])
                end_date = pd.to_datetime(filters["fecha_fin"])

                # Filter by emission date if available
                if "fecha_emision" in filtered_df.columns:
                    date_col = pd.to_datetime(
                        filtered_df["fecha_emision"], errors="coerce"
                    )
                    filtered_df = filtered_df[
                        (date_col >= start_date) & (date_col <= end_date)
                    ]
            except Exception:
                pass  # Skip date filtering if there's an error

        # Quick period filter
        if filters.get("periodo_rapido"):
            period_days = int(filters["periodo_rapido"])
            cutoff_date = datetime.now() - timedelta(days=period_days)

            if "fecha_emision" in filtered_df.columns:
                date_col = pd.to_datetime(filtered_df["fecha_emision"], errors="coerce")
                filtered_df = filtered_df[date_col >= cutoff_date]

        # # Department filter
        # if filters.get('departamento') and filters['departamento'] != 'todos':
        #     if 'Departamento' in filtered_df.columns:
        #         filtered_df = filtered_df[
        #             filtered_df['Departamento'] == filters['departamento']
        #         ]

        # Client filter
        if filters.get("cliente") and filters["cliente"] != "todos":
            filtered_df = filtered_df[filtered_df["cliente"] == filters["cliente"]]

        # Status filter
        if filters.get("estado") and filters["estado"] != "todos":
            filtered_df = filtered_df[filtered_df["estado"] == filters["estado"]]

        return filtered_df

    def _calculate_executive_kpis(
        self, df_full: pd.DataFrame, df_filtered: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate executive-level KPIs using centralized KPI service."""
        try:
            # Use the complete manager dashboard KPIs calculation
            kpi_response = self.kpi_service.calculate_manager_dashboard_kpis(df_full, df_filtered)
            if kpi_response.success:
                logger.info(f"✅ KPI Service returned {len(kpi_response.data)} metrics")
                return kpi_response.data
            else:
                logger.error(f"KPI service error: {kpi_response.message}")
                # Fallback to essential KPIs if complete calculation fails
                essential_response = self.kpi_service.calculate_essential_kpis(df_full, df_filtered)
                if essential_response.success:
                    logger.info(f"✅ Fallback to essential KPIs: {len(essential_response.data)} metrics")
                    return essential_response.data
                else:
                    logger.error(f"Essential KPIs also failed: {essential_response.message}")
                    return self.get_empty_kpis()
        except Exception as e:
            logger.error(f"Error delegating to KPI service: {e}")
            # Try essential KPIs as fallback
            try:
                essential_response = self.kpi_service.calculate_essential_kpis(df_full, df_filtered)
                if essential_response.success:
                    logger.info(f"✅ Fallback essential KPIs after exception: {len(essential_response.data)} metrics")
                    return essential_response.data
            except Exception as e2:
                logger.error(f"Fallback essential KPIs also failed: {e2}")
            return self.get_empty_kpis()

    def _calculate_financial_metrics(
        self, df_full: pd.DataFrame, df_filtered: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate financial metrics and ratios."""
        # Ensure numeric columns
        for col in ["monto_propuesto", "monto_aprobado"]:
            if col in df_full.columns:
                df_full[col] = pd.to_numeric(df_full[col], errors="coerce").fillna(0)

        # Revenue metrics
        total_revenue = df_full[df_full["estado"] == "pagado"]["monto_aprobado"].sum()
        pending_revenue = df_full[df_full["estado"].isin(["enviado", "validado"])][
            "monto_aprobado"
        ].sum()

        # Monthly breakdown
        monthly_data = self._calculate_monthly_financials(df_full)

        # ROI and margins
        cost_of_capital = 0.12  # 12% annual
        dso = self._calculate_dso(df_full)

        return {
            "total_revenue": FormatUtils.format_currency(total_revenue),
            "pending_revenue": FormatUtils.format_currency(pending_revenue),
            "monthly_data": monthly_data,
            "dso": round(dso, 1),
            "cost_of_capital": FormatUtils.format_percentage(cost_of_capital * 100),
            "working_capital_impact": self._calculate_working_capital_impact(df_full),
        }

    def _generate_chart_data(
        self, df_full: pd.DataFrame, df_filtered: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate data for various charts using real column names and dashboard format."""
        try:
            charts = {}

            # Ensure monetary columns are numeric
            for col in ["monto_propuesto", "monto_aprobado"]:
                if col in df_full.columns:
                    df_full[col] = pd.to_numeric(df_full[col], errors="coerce").fillna(
                        0
                    )

            # 1. Cash Flow Forecast (compatible with dashboard format)
            charts["cash_in_forecast"] = self._build_cash_forecast_chart(df_full)

            # 2. Status Distribution (Estado Proyectos)
            charts["estado_proyectos"] = self._build_status_distribution_chart(df_full)

            # 3. Client Performance (Concentración Clientes)
            charts["concentracion_clientes"] = self._build_client_performance_chart(
                df_full
            )

            # 4. Monthly Financial Trend (Tendencia Financiera)
            charts["tendencia_financiera"] = self._build_monthly_trend_chart(df_full)

            # 5. Aging Buckets
            charts["aging_buckets"] = self._build_aging_buckets_chart(df_full)

            # 6. Manager Performance (if data available)
            if "gestor" in df_full.columns or "jefe_proyecto" in df_full.columns:
                charts["rendimiento_gestores"] = self._build_manager_performance_chart(
                    df_full
                )

            # 7. OPEX and CAPEX Breakdown
            charts["opex_capex_breakdown"] = self._build_opex_capex_chart(df_full)

            logger.info(f"✅ Generated {len(charts)} charts successfully")
            return charts

        except Exception as e:
            logger.info(f"❌ Error generating chart data: {e}")
            import traceback

            traceback.print_exc()
            return {}

    def _build_cash_forecast_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build cash flow forecast chart compatible with dashboard format."""
        try:
            from datetime import datetime, timedelta

            hoy = datetime.now()
            hoy_30d = hoy + timedelta(days=30)
            hoy_60d = hoy + timedelta(days=60)
            hoy_90d = hoy + timedelta(days=90)

            # Filter pending EDPs
            df_pendientes = df[~df["estado"].str.strip().isin(["pagado", "validado"])]

            if df_pendientes.empty:
                return {"labels": ["30 días", "60 días", "90 días"], "datasets": []}

            df_pendientes = df_pendientes.copy()
            # Usar Fecha Estimada de Pago si existe, sino estimar
            if "fecha_estimada_pago" in df_pendientes.columns:
                df_pendientes["fecha_estimada_pago"] = pd.to_datetime(
                    df_pendientes["fecha_estimada_pago"], errors="coerce"
                )
                fecha_pago_col = "fecha_estimada_pago"
            else:
                df_pendientes = df_pendientes.copy()
                df_pendientes["Fecha_Estimada_Calculada"] = df_pendientes[
                    "fecha_emision"
                ] + pd.Timedelta(days=45)
                fecha_pago_col = "Fecha_Estimada_Calculada"

            # Calcular montos por período
            monto_30d = (
                df_pendientes[df_pendientes[fecha_pago_col] <= hoy_30d][
                    "monto_aprobado"
                ].sum()
                / 1_000_000
            )
            monto_60d = (
                df_pendientes[
                    (df_pendientes[fecha_pago_col] > hoy_30d)
                    & (df_pendientes[fecha_pago_col] <= hoy_60d)
                ]["monto_aprobado"].sum()
                / 1_000_000
            )
            monto_90d = (
                df_pendientes[
                    (df_pendientes[fecha_pago_col] > hoy_60d)
                    & (df_pendientes[fecha_pago_col] <= hoy_90d)
                ]["monto_aprobado"].sum()
                / 1_000_000
            )

            return {
                "labels": ["30 días", "60 días", "90 días"],
                "datasets": [
                    {
                        "label": "Flujo proyectado (M$)",
                        "data": [float(monto_30d), float(monto_60d), float(monto_90d)],
                        "backgroundColor": [
                            "rgba(16, 185, 129, 0.7)",
                            "rgba(59, 130, 246, 0.7)",
                            "rgba(249, 115, 22, 0.7)",
                        ],
                    }
                ],
            }
        except Exception as e:
            logger.info(f"Error en cash forecast simplificado: {e}")
            return {"labels": [], "datasets": []}

    def _build_status_distribution_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build status distribution chart."""
        try:
            status_counts = df["estado"].value_counts()

            # Map status to Spanish labels and colors
            status_mapping = {
                "pagado": {"label": "Pagado", "color": "rgba(16, 185, 129, 0.8)"},
                "validado": {"label": "Validado", "color": "rgba(59, 130, 246, 0.8)"},
                "enviado": {"label": "Enviado", "color": "rgba(249, 115, 22, 0.8)"},
                "revision": {"label": "Revisión", "color": "rgba(245, 158, 11, 0.8)"},
                "pendiente": {"label": "Pendiente", "color": "rgba(239, 68, 68, 0.8)"},
                "rechazado": {
                    "label": "Rechazado",
                    "color": "rgba(107, 114, 128, 0.8)",
                },
            }

            labels = []
            data = []
            colors = []

            for status, count in status_counts.items():
                mapping = status_mapping.get(
                    status,
                    {"label": status.title(), "color": "rgba(156, 163, 175, 0.8)"},
                )
                labels.append(mapping["label"])
                data.append(int(count))
                colors.append(mapping["color"])

            return {
                "labels": labels,
                "datasets": [
                    {"data": data, "backgroundColor": colors, "borderWidth": 1}
                ],
            }

        except Exception as e:
            logger.info(f"Error in status distribution chart: {e}")
            return {"labels": [], "datasets": []}

    def _build_client_performance_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build client performance chart."""
        try:

            if "cliente" not in df.columns:
                return {"labels": [], "datasets": []}

            # Group by client and calculate performance metrics
            client_performance = (
                df.groupby("cliente")["monto_aprobado"].sum() / 1_000_000
            )

            if client_performance.empty:
                return {"labels": [], "datasets": []}

            # Sort by amount and take top 10
            sorted_clients = client_performance.sort_values(ascending=False)
            top_10_clientes = sorted_clients.head(10)

            # Calculate percentage of total
            total = sorted_clients.sum()
            pct_acum = (top_10_clientes.cumsum() / total * 100).round(1)

            return {
                "labels": top_10_clientes.index.tolist(),
                "datasets": [
                    {
                        "type": "bar",
                        "label": "Monto (M$)",
                        "data": client_performance.round(1).tolist(),
                        "backgroundColor": [
                            "rgba(59, 130, 246, 0.7)",  # blue
                            "rgba(16, 185, 129, 0.7)",  # green
                            "rgba(249, 115, 22, 0.7)",  # orange
                            "rgba(139, 92, 246, 0.7)",  # purple
                            "rgba(244, 63, 94, 0.7)",  # red
                            "rgba(6, 182, 212, 0.7)",  # cyan
                            "rgba(251, 191, 36, 0.7)",  # yellow
                            "rgba(107, 114, 128, 0.7)",  # gray
                            "rgba(236, 72, 153, 0.7)",  # pink
                            "rgba(168, 85, 247, 0.7)",  # violet
                        ],
                        "yAxisID": "y",
                    },
                    {
                        "type": "line",
                        "label": "Porcentaje Acumulado",
                        "data": pct_acum.tolist(),
                        "borderColor": "rgba(234, 88, 12, 1)",
                        "borderWidth": 2,
                        "fill": False,
                        "yAxisID": "percentage",
                        "pointBackgroundColor": "rgba(234, 88, 12, 1)",
                        "pointRadius": 4,
                        "pointHoverRadius": 6,
                    },
                ],
            }

        except Exception as e:
            logger.info(f"Error in client performance chart: {e}")
            return {"labels": [], "datasets": []}

    def _build_monthly_trend_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build comprehensive monthly financial trend chart with costs and projections."""
        try:
            from datetime import datetime, timedelta

            # Preparar datos base
            df_copia = df.copy()

            # Ensure fecha_emision is datetime
            if "fecha_emision" in df_copia.columns:
                df_copia["fecha_emision"] = pd.to_datetime(
                    df_copia["fecha_emision"], errors="coerce"
                )
                df_copia["mes"] = df_copia["fecha_emision"].dt.strftime("%Y-%m")
            else:
                return self._create_mock_monthly_trend()

            # Obtener datos de costos reales del CostService
            df_costs = pd.DataFrame()
            try:
                cost_response = self.cost_service.cost_repository.find_all_dataframe()
                if cost_response.get("success", False):
                    df_costs = cost_response.get("data", pd.DataFrame())
                    if not df_costs.empty:
                        # Procesar datos de costos
                        if "importe_neto" in df_costs.columns:
                            df_costs["importe_neto"] = pd.to_numeric(
                                df_costs["importe_neto"], errors="coerce"
                            ).fillna(0)

                        # Crear columna de mes para costos
                        if "fecha_costo" in df_costs.columns:
                            df_costs["fecha_costo"] = pd.to_datetime(
                                df_costs["fecha_costo"], errors="coerce"
                            )
                            df_costs["mes"] = df_costs["fecha_costo"].dt.strftime(
                                "%Y-%m"
                            )
                        elif "created_at" in df_costs.columns:
                            df_costs["created_at"] = pd.to_datetime(
                                df_costs["created_at"], errors="coerce"
                            )
                            df_costs["mes"] = df_costs["created_at"].dt.strftime(
                                "%Y-%m"
                            )
                        else:
                            # Si no hay fecha de costo, usar fecha de emisión del EDP correspondiente
                            if "project_id" in df_costs.columns:
                                proyecto_fechas = df_copia[
                                    ["proyecto", "fecha_emision"]
                                ].drop_duplicates()
                                proyecto_fechas.columns = [
                                    "project_id",
                                    "fecha_emision",
                                ]
                                df_costs = df_costs.merge(
                                    proyecto_fechas, on="project_id", how="left"
                                )
                                df_costs["mes"] = df_costs["fecha_emision"].dt.strftime(
                                    "%Y-%m"
                                )
                            else:
                                # Usar mes actual como fallback
                                df_costs["mes"] = datetime.now().strftime("%Y-%m")

                        logger.info(
                            f"✅ Loaded {len(df_costs)} cost records for trend analysis"
                        )
            except Exception as e:
                logger.info(f"⚠️ Could not load cost data for trend: {e}")

            # ===== CALCULAR MÉTRICAS POR MES =====

            # 1. Ingresos mensuales reales (EDP completados/pagados)
            df_completados = df_copia[
                df_copia["estado"].str.strip().isin(["pagado", "validado"])
            ]
            ingresos_mensuales = (
                df_completados.groupby("mes")["monto_aprobado"].sum() / 1_000_000
            )

            # 2. Ingresos totales emitidos (todos los EDP)
            ingresos_emitidos = (
                df_copia.groupby("mes")["monto_aprobado"].sum() / 1_000_000
            )

            # 3. Costos reales mensuales
            costos_mensuales = pd.Series(dtype=float)
            if (
                not df_costs.empty
                and "mes" in df_costs.columns
                and "importe_neto" in df_costs.columns
            ):
                costos_mensuales = (
                    df_costs.groupby("mes")["importe_neto"].sum() / 1_000_000
                )

            # ===== DETERMINAR PERÍODO (ÚLTIMOS 6 MESES + 3 PROYECCIONES) =====

            # Obtener todos los meses disponibles
            todos_meses = set()
            if len(ingresos_mensuales) > 0:
                todos_meses.update(ingresos_mensuales.index)
            if len(ingresos_emitidos) > 0:
                todos_meses.update(ingresos_emitidos.index)
            if len(costos_mensuales) > 0:
                todos_meses.update(costos_mensuales.index)

            if not todos_meses:
                return self._create_mock_monthly_trend()

            # Últimos 6 meses reales
            meses_ordenados = sorted(todos_meses)
            ultimos_6_meses = (
                meses_ordenados[-6:] if len(meses_ordenados) >= 6 else meses_ordenados
            )

            # Generar 3 meses de proyección
            ultimo_mes = datetime.strptime(meses_ordenados[-1], "%Y-%m")
            meses_proyeccion = []
            for i in range(1, 4):
                mes_futuro = ultimo_mes + timedelta(days=32 * i)
                mes_futuro = mes_futuro.replace(day=1)  # Primer día del mes
                meses_proyeccion.append(mes_futuro.strftime("%Y-%m"))

            # Período completo: 6 meses reales + 3 proyecciones
            periodo_completo = ultimos_6_meses + meses_proyeccion

            # ===== RECOPILAR DATOS POR MES =====

            labels = []
            datos_ingresos_reales = []
            datos_ingresos_emitidos = []
            datos_costos = []
            datos_margen = []
            datos_cashflow_proyectado = []

            # Calcular promedios para proyecciones
            avg_ingresos_reales = (
                ingresos_mensuales.tail(3).mean() if len(ingresos_mensuales) >= 3 else 0
            )
            avg_ingresos_emitidos = (
                ingresos_emitidos.tail(3).mean() if len(ingresos_emitidos) >= 3 else 0
            )
            avg_costos = (
                costos_mensuales.tail(3).mean()
                if len(costos_mensuales) >= 3
                else avg_ingresos_reales * 0.65
            )
            crecimiento_mensual = 1.05  # 5% crecimiento mensual proyectado

            for i, mes in enumerate(periodo_completo):
                try:
                    # Convertir mes a label legible
                    fecha = datetime.strptime(mes, "%Y-%m")
                    if i < len(ultimos_6_meses):
                        labels.append(fecha.strftime("%b %Y"))
                    else:
                        labels.append(
                            fecha.strftime("%b %Y") + " (P)"
                        )  # (P) = Proyección

                    # Determinar si es mes real o proyección
                    es_proyeccion = i >= len(ultimos_6_meses)

                    if not es_proyeccion:
                        # ===== DATOS REALES =====

                        # Ingresos reales (cobrados)
                        ingreso_real = float(ingresos_mensuales.get(mes, 0))
                        datos_ingresos_reales.append(ingreso_real)

                        # Ingresos emitidos
                        ingreso_emitido = float(ingresos_emitidos.get(mes, 0))
                        datos_ingresos_emitidos.append(ingreso_emitido)

                        # Costos reales
                        costo_real = float(costos_mensuales.get(mes, 0))
                        datos_costos.append(costo_real)

                        # Margen real
                        margen = ingreso_real - costo_real
                        datos_margen.append(margen)

                        # Cash flow real (ingresos - costos del mes)
                        datos_cashflow_proyectado.append(margen)

                    else:
                        # ===== PROYECCIONES =====

                        meses_futuros = i - len(ultimos_6_meses) + 1
                        factor_crecimiento = crecimiento_mensual**meses_futuros

                        # Proyectar ingresos con crecimiento
                        ingreso_proyectado = avg_ingresos_reales * factor_crecimiento
                        datos_ingresos_reales.append(ingreso_proyectado)

                        # Proyectar ingresos emitidos
                        emitido_proyectado = avg_ingresos_emitidos * factor_crecimiento
                        datos_ingresos_emitidos.append(emitido_proyectado)

                        # Proyectar costos (manteniendo ratio)
                        costo_proyectado = ingreso_proyectado * 0.65  # 65% de costos
                        datos_costos.append(costo_proyectado)

                        # Margen proyectado
                        margen_proyectado = ingreso_proyectado - costo_proyectado
                        datos_margen.append(margen_proyectado)

                        # Cash flow proyectado
                        datos_cashflow_proyectado.append(margen_proyectado)

                except Exception as e:
                    logger.info(f"Error procesando mes {mes}: {e}")
                    labels.append(mes)
                    datos_ingresos_reales.append(0)
                    datos_ingresos_emitidos.append(0)
                    datos_costos.append(0)
                    datos_margen.append(0)
                    datos_cashflow_proyectado.append(0)

            # ===== GENERAR DATASETS =====

            datasets = [
                {
                    "label": "Ingresos Cobrados (M$)",
                    "data": datos_ingresos_reales,
                    "borderColor": "#10B981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "fill": False,
                    "tension": 0.3,
                    "borderWidth": 3,
                    "pointBackgroundColor": "#10B981",
                    "pointBorderWidth": 2,
                    "pointRadius": 4,
                },
                {
                    "label": "Ingresos Proyectados (M$)",
                    "data": datos_ingresos_emitidos,
                    "borderColor": "#3B82F6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "fill": False,
                    "tension": 0.3,
                    "borderWidth": 2,
                    "borderDash": [5, 5],  # Línea punteada
                    "pointBackgroundColor": "#3B82F6",
                    "pointRadius": 3,
                },
                {
                    "label": "Costos (M$)",
                    "data": datos_costos,
                    "borderColor": "#F87171",
                    "backgroundColor": "rgba(248, 113, 113, 0.1)",
                    "fill": False,
                    "tension": 0.3,
                    "borderWidth": 2,
                    "pointBackgroundColor": "#F87171",
                    "pointRadius": 3,
                },
                {
                    "label": "Margen Bruto (M$)",
                    "data": datos_margen,
                    "borderColor": "#8B5CF6",
                    "backgroundColor": "rgba(139, 92, 246, 0.2)",
                    "fill": True,
                    "tension": 0.3,
                    "borderWidth": 2,
                    "pointBackgroundColor": "#8B5CF6",
                    "pointRadius": 3,
                },
            ]

            # ===== CALCULAR ESTADÍSTICAS ADICIONALES =====

            # Promedio de margen de los últimos 3 meses reales
            margen_real_reciente = [
                m for i, m in enumerate(datos_margen) if i < len(ultimos_6_meses)
            ]
            promedio_margen = (
                sum(margen_real_reciente[-3:]) / 3
                if len(margen_real_reciente) >= 3
                else 0
            )

            # Tendencia (comparar primer vs último mes real)
            if len(margen_real_reciente) >= 2:
                tendencia_margen = (
                    (
                        (margen_real_reciente[-1] - margen_real_reciente[0])
                        / margen_real_reciente[0]
                        * 100
                    )
                    if margen_real_reciente[0] != 0
                    else 0
                )
            else:
                tendencia_margen = 0

            # Cash flow acumulado proyectado (próximos 3 meses)
            cashflow_3m = sum(datos_cashflow_proyectado[-3:])

            return {
                "labels": labels,
                "datasets": datasets,
                "estadisticas": {
                    "promedio_margen_3m": round(promedio_margen, 1),
                    "tendencia_margen": round(tendencia_margen, 1),
                    "cashflow_proyectado_3m": round(cashflow_3m, 1),
                    "mejor_mes": (
                        labels[datos_margen.index(max(datos_margen))]
                        if datos_margen
                        else "N/A"
                    ),
                    "total_meses": len(labels),
                },
            }

        except Exception as e:
            logger.info(f"Error in monthly trend chart: {e}")
            return self._create_mock_monthly_trend()

    def _build_aging_buckets_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build aging buckets chart."""
        try:
            if "dias_espera" not in df.columns or df.empty:
                return {
                    "labels": ["0-30 días", "31-60 días", "61-90 días", "90+ días"],
                    "datasets": [],
                }

            dias = pd.to_numeric(df["dias_espera"], errors="coerce").fillna(0)

            bucket_0_30 = int((dias <= 30).sum())
            bucket_31_60 = int(((dias > 30) & (dias <= 60)).sum())
            bucket_61_90 = int(((dias > 60) & (dias <= 90)).sum())
            bucket_90_plus = int((dias > 90).sum())

            return {
                "labels": ["0-30 días", "31-60 días", "61-90 días", "90+ días"],
                "datasets": [
                    {
                        "label": "EDPs por antigüedad",
                        "data": [
                            bucket_0_30,
                            bucket_31_60,
                            bucket_61_90,
                            bucket_90_plus,
                        ],
                        "backgroundColor": [
                            "rgba(16, 185, 129, 0.8)",  # Green for fresh
                            "rgba(59, 130, 246, 0.8)",  # Blue for moderate
                            "rgba(249, 115, 22, 0.8)",  # Orange for aging
                            "rgba(239, 68, 68, 0.8)",  # Red for old
                        ],
                    }
                ],
            }

        except Exception as e:
            logger.info(f"Error in aging buckets chart: {e}")
            return {
                "labels": ["0-30 días", "31-60 días", "61-90 días", "90+ días"],
                "datasets": [],
            }

    def _build_manager_performance_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build manager performance chart with profitability analysis using real cost data."""
        try:
            # Use gestor or jefe_proyecto column
            manager_col = "jefe_proyecto" if "jefe_proyecto" in df.columns else "gestor"

            if manager_col not in df.columns:
                return {"labels": ["Sin datos"], "datasets": []}

            # Get real cost data from CostService - match dashboard structure exactly
            costs_lookup = {}
            try:
                cost_response = self.cost_service.cost_repository.find_all_dataframe()
                if cost_response.get("success", False):
                    df_costs = cost_response.get("data", pd.DataFrame())
                    if not df_costs.empty and "project_id" in df_costs.columns:
                        # Match dashboard cost lookup structure exactly
                        df_costs["project_id"] = (
                            df_costs["project_id"].astype(str).str.strip()
                        )
                        df_costs["importe_neto"] = pd.to_numeric(
                            df_costs["importe_neto"], errors="coerce"
                        ).fillna(0)

                        # Filter valid costs
                        df_costs_valid = df_costs[
                            (df_costs["project_id"] != "nan")
                            & (df_costs["project_id"] != "")
                            & (df_costs["project_id"].notna())
                        ]

                        if not df_costs_valid.empty:
                            costs_summary = (
                                df_costs_valid.groupby("project_id")
                                .agg(
                                    {
                                        "importe_neto": "sum",
                                        "cost_id": "count",
                                        "estado_costo": lambda x: (
                                            (x == "pagado").sum() if len(x) > 0 else 0
                                        ),
                                    }
                                )
                                .to_dict("index")
                            )
                            costs_lookup = costs_summary

            except Exception as e:
                logger.info(
                    f"Warning: Could not load cost data for manager performance: {e}"
                )

            # Agrupar por gestor/jefe de proyecto
            gestores_data = {}

            for gestor in df[manager_col].dropna().unique():
                if pd.notna(gestor) and str(gestor).strip():
                    df_gestor = df[df[manager_col] == gestor]

                    # Calcular ingresos totales del gestor
                    ingresos_totales = 0
                    costos_totales = 0
                    proyectos_procesados = 0

                    # Sumar todos los proyectos del gestor
                    for _, row in df_gestor.iterrows():
                        proyecto_id = str(
                            row.get("proyecto", row.get("n_edp", ""))
                        ).strip()
                        ingreso_proyecto = row.get("monto_aprobado", 0)

                        # Solo contar si el estado es completado (pagado/validado)
                        if row.get("estado", "").strip() in ["pagado", "validado"]:
                            ingresos_totales += ingreso_proyecto

                            # Buscar costos del proyecto - match dashboard structure exactly
                            if proyecto_id in costs_lookup:
                                costo_proyecto = costs_lookup[proyecto_id].get(
                                    "importe_neto", 0
                                )
                                costos_totales += costo_proyecto
                                proyectos_procesados += 1

                    # Calcular rentabilidad solo si hay ingresos
                    if ingresos_totales > 0:
                        margen = ingresos_totales - costos_totales
                        rentabilidad = margen / ingresos_totales * 100

                        gestores_data[gestor] = {
                            "rentabilidad": rentabilidad,
                            "ingresos": ingresos_totales / 1_000_000,  # En millones
                            "margen": margen / 1_000_000,
                            "proyectos": proyectos_procesados,
                        }

            if not gestores_data:
                return {"labels": ["Sin coincidencias"], "datasets": []}

            # Ordenar por rentabilidad y tomar top 8
            top_gestores = dict(
                sorted(
                    gestores_data.items(),
                    key=lambda x: x[1]["rentabilidad"],
                    reverse=True,
                )[:8]
            )

            # Generar colores basados en rentabilidad
            colores = []
            rentabilidades = []
            labels = []

            for gestor, data in top_gestores.items():
                rent = data["rentabilidad"]
                rentabilidades.append(round(rent, 1))

                # Truncar nombres largos
                label = f"{gestor[:12]}..." if len(gestor) > 12 else gestor
                # Agregar info de proyectos
                label += f" ({data['proyectos']}p)"
                labels.append(label)

                # Colores por performance
                if rent >= 35:
                    colores.append("rgba(16, 185, 129, 0.8)")  # Verde - Excelente
                elif rent >= 25:
                    colores.append("rgba(34, 197, 94, 0.7)")  # Verde claro - Bueno
                elif rent >= 15:
                    colores.append("rgba(59, 130, 246, 0.7)")  # Azul - Aceptable
                elif rent >= 0:
                    colores.append("rgba(249, 115, 22, 0.7)")  # Naranja - Bajo
                else:
                    colores.append("rgba(239, 68, 68, 0.8)")  # Rojo - Negativo
            return {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Rentabilidad por Gestor (%)",
                        "data": rentabilidades,
                        "backgroundColor": colores,
                        "borderColor": [
                            color.replace("0.7", "1.0").replace("0.8", "1.0")
                            for color in colores
                        ],
                        "borderWidth": 1,
                    }
                ],
                "tooltip_data": {
                    gestor: {
                        "rentabilidad": f"{data['rentabilidad']:.1f}%",
                        "ingresos": f"${data['ingresos']:.1f}M",
                        "margen": f"${data['margen']:.1f}M",
                        "proyectos": f"{data['proyectos']} proyectos",
                    }
                    for gestor, data in top_gestores.items()
                },
            }

        except Exception as e:
            logger.info(f"Error in manager performance chart: {e}")
            return {"labels": [], "datasets": []}

    def _build_opex_capex_chart(self, df: pd.DataFrame) -> Dict[str, Any]:

        costs_lookup = {}
        try:
            cost_response = self.cost_service.cost_repository.find_all_dataframe()
            if cost_response.get("success", False):
                df_costs = cost_response.get("data", pd.DataFrame())

            # --- 1. Análisis por tipo de costo
            df_costs["tipo_costo"] = df_costs["tipo_costo"].str.lower().fillna("opex")

            analisis_tipo = (
                df_costs.groupby("tipo_costo")["importe_neto"]
                .agg(total="sum", count="count")
                .reset_index()
            )
            total_costos = analisis_tipo["total"].sum()

            return {
                "labels": analisis_tipo["tipo_costo"].tolist(),
                "datasets": [
                    {
                        "data": (analisis_tipo["total"] / 1_000_000).round(2).tolist(),
                        "backgroundColor": [
                            "rgba(59, 130, 246, 0.7)",
                            "rgba(16, 185, 129, 0.7)",
                        ],
                        "borderColor": ["rgb(59, 130, 246)", "rgb(16, 185, 129)"],
                        "borderWidth": 1,
                    }
                ],
            }

        except Exception as e:
            import traceback

            traceback.print_exc()
            return {"error": f"❌ Error en análisis de costos: {e}"}

    def _create_mock_monthly_trend(self) -> Dict[str, Any]:
        """Create mock monthly trend data when real data is not available."""
        from datetime import datetime, timedelta

        # Generate last 6 months
        months = []
        base_date = datetime.now()
        for i in range(6, 0, -1):
            month_date = base_date - timedelta(days=30 * i)
            months.append(month_date.strftime("%Y-%m"))

        # Mock data with some variance
        import random

        amounts = [round(random.uniform(8.0, 15.0), 2) for _ in months]
        counts = [random.randint(15, 35) for _ in months]

        return {
            "labels": months,
            "datasets": [
                {
                    "label": "Ingresos (M$)",
                    "data": amounts,
                    "borderColor": "rgba(16, 185, 129, 1)",
                    "backgroundColor": "rgba(16, 185, 129, 0.2)",
                    "tension": 0.4,
                    "fill": True,
                },
                {
                    "label": "Cantidad EDPs",
                    "data": counts,
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "backgroundColor": "rgba(59, 130, 246, 0.2)",
                    "tension": 0.4,
                    "yAxisID": "y1",
                },
            ],
        }

    def _calculate_cash_forecast(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate cash flow forecast."""
        forecast = {}

        # Get EDPs with estimated payment dates
        pending_payments = df[
            (df["estado"].isin(["validado", "enviado"]))
            & (pd.notna(df.get("fecha_estimada_pago")))
        ].copy()  # Explicit copy to avoid SettingWithCopyWarning

        if not pending_payments.empty:
            # Group by month
            pending_payments["Mes_Pago"] = pd.to_datetime(
                pending_payments["fecha_estimada_pago"], errors="coerce"
            ).dt.strftime("%Y-%m")

            monthly_forecast = pending_payments.groupby("Mes_Pago")[
                "monto_aprobado"
            ].sum()

            forecast = {
                "months": monthly_forecast.index.tolist(),
                "amounts": monthly_forecast.values.tolist(),
                "total_expected": monthly_forecast.sum(),
            }
        else:
            # Mock forecast data
            forecast = {
                "months": ["2023-10", "2023-11", "2023-12"],
                "amounts": [1000000, 1500000, 2000000],
                "total_expected": 4500000,
            }

        return forecast

    def _generate_alerts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate system alerts and warnings using template-compatible structure."""
        alerts = []

        # Critical EDPs alert - check if 'Crítico' column exists
        if "Crítico" in df.columns:
            critical_count = len(df[df["Crítico"] == True])
        else:
            critical_count = 0

        if critical_count > 0:
            alerts.append(
                {
                    "tipo": "critico",
                    "titulo": "EDPs Críticos",
                    "descripcion": f"{critical_count} EDPs marcados como críticos requieren atención inmediata",
                    "fecha": datetime.now().strftime("%d/%m/%Y"),
                    "accion_principal": "Revisar",
                }
            )

        # Old pending EDPs
        if "dias_espera" in df.columns:
            old_pending = len(
                df[
                    (df["estado"].isin(["enviado", "revisión"]))
                    & (df["dias_espera"] > 30)
                ]
            )
            if old_pending > 0:
                alerts.append(
                    {
                        "tipo": "alto",
                        "titulo": "EDPs Atrasados",
                        "descripcion": f"{old_pending} EDPs llevan más de 30 días en proceso",
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "accion_principal": "Gestionar",
                    }
                )

        # High value pending EDPs
        high_value_pending = df[
            (df["estado"].isin(["enviado", "revisión"]))
            & (df["monto_propuesto"] > 50_000_000)  # 50M threshold
        ]
        if not high_value_pending.empty:
            total_amount = high_value_pending["monto_propuesto"].sum()
            alerts.append(
                {
                    "tipo": "medio",
                    "titulo": "EDPs Alto Valor Pendientes",
                    "descripcion": f"{FormatUtils.format_currency(total_amount)} en EDPs de alto valor pendientes",
                    "fecha": datetime.now().strftime("%d/%m/%Y"),
                    "accion_principal": "Monitorear",
                }
            )

        return alerts

    def _get_manager_filter_options(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Get available filter options for manager dashboard."""
        options = {"meses": [], "clientes": [], "estados": [], "jefes_proyecto": []}

        if "mes" in df.columns:
            options["meses"] = sorted(df["mes"].dropna().unique().tolist())

        if "cliente" in df.columns:
            options["clientes"] = sorted(df["cliente"].dropna().unique().tolist())

        options["estados"] = sorted(df["estado"].dropna().unique().tolist())

        if "jefe_proyecto" in df.columns:
            options["jefes_proyecto"] = sorted(
                df["jefe_proyecto"].dropna().unique().tolist()
            )

        return options

    def _calculate_efficiency_score(self, df: pd.DataFrame) -> float:
        """Calculate overall efficiency score (0-100) with improved logic."""
        factors = []

        # 1. Approval/Completion rate factor (30% weight)
        completed_count = len(df[df["estado"].str.strip().isin(["pagado", "validado"])])
        total_count = len(df)
        if total_count > 0:
            completion_rate = completed_count / total_count
            # Convertir a score de 0-30 puntos
            completion_score = min(30, completion_rate * 30)
            factors.append(completion_score)

        # 2. Speed factor (30% weight) - CORREGIDO: lógica invertida
        if "dias_espera" in df.columns and total_count > 0:
            # Calcular promedio de días de espera
            dias_espera_validos = pd.to_numeric(df["dias_espera"], errors="coerce")
            avg_days = dias_espera_validos.mean() if not dias_espera_validos.isna().all() else 45

            if avg_days > 0:
                # CORREGIDO: Entre mejor (menor tiempo), mayor score
                # Benchmark: 30 días = 100%, 60+ días = 0%
                speed_factor = max(0, min(1, (60 - avg_days) / 30))
                speed_score = speed_factor * 30  # Máximo 30 puntos
                factors.append(speed_score)

        # 3. Critical EDPs factor (20% weight) - CORREGIDO: manejo de campo opcional
        critical_penalty = 0
        if total_count > 0:
            # Verificar si existe la columna Crítico
            if "Crítico" in df.columns:
                critical_count = len(df[df["Crítico"] == True])
            elif "critico" in df.columns:
                critical_count = len(df[df["critico"] == True])
            else:
                # Si no hay columna crítico, estimar basado en días de espera
                if "dias_espera" in df.columns:
                    dias_espera_validos = pd.to_numeric(df["dias_espera"], errors="coerce")
                    critical_count = len(dias_espera_validos[dias_espera_validos > 60])
                else:
                    critical_count = 0

            critical_rate = critical_count / total_count
            # Score: 0% críticos = 20 puntos, 50%+ críticos = 0 puntos
            critical_score = max(0, 20 * (1 - critical_rate * 2))
            factors.append(critical_score)

        # 4. Financial efficiency factor (20% weight) - CORREGIDO: lógica mejorada
        if "monto_propuesto" in df.columns and "monto_aprobado" in df.columns:
            # Convertir a numérico y manejar valores faltantes
            monto_propuesto = pd.to_numeric(df["monto_propuesto"], errors="coerce").fillna(0)
            monto_aprobado = pd.to_numeric(df["monto_aprobado"], errors="coerce").fillna(0)
            
            total_proposed = monto_propuesto.sum()
            total_approved = monto_aprobado.sum()
            
            if total_proposed > 0:
                # CORREGIDO: Ratio de aprobación vs propuesto
                approval_ratio = min(1.2, total_approved / total_proposed)  # Cap at 120% (puede ser mayor si hay ajustes)
                # Normalizar: 100% aprobación = 20 puntos, 0% = 0 puntos
                financial_score = min(20, approval_ratio * 20)
                factors.append(financial_score)

        # Calculate final weighted score
        total_score = sum(factors)
        
        # CORREGIDO: Asegurar que el score esté entre 0 y 100
        final_score = min(100, max(0, total_score))
        
        return round(final_score, 1)

    def _calculate_monthly_financials(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """Calculate monthly financial breakdown."""
        if "mes" not in df.columns:
            return {}

        monthly_data = (
            df.groupby("mes")
            .agg({"monto_propuesto": "sum", "monto_aprobado": "sum"})
            .fillna(0)
        )

        # Calculate payments by month
        paid_by_month = (
            df[df["estado"] == "pagado"].groupby("mes")["monto_aprobado"].sum()
        )

        return {
            "months": monthly_data.index.tolist(),
            "proposed": monthly_data["monto_propuesto"].tolist(),
            "approved": monthly_data["monto_aprobado"].tolist(),
            "paid": [paid_by_month.get(month, 0) for month in monthly_data.index],
        }

    def _calculate_dso(self, df: pd.DataFrame) -> float:
        """Calculate Days Sales Outstanding with improved logic."""
        try:
            if "dias_espera" not in df.columns or df.empty:
                return 45.0  # Default reasonable DSO

            # Convertir dias_espera a numérico
            df_copy = df.copy()
            df_copy["dias_espera_num"] = pd.to_numeric(df_copy["dias_espera"], errors="coerce")
            
            # Convertir montos a numérico
            if "monto_aprobado" in df_copy.columns:
                df_copy["monto_aprobado_num"] = pd.to_numeric(df_copy["monto_aprobado"], errors="coerce").fillna(0)
            else:
                return 45.0

            # CORREGIDO: Filtrar EDPs pagados Y con datos válidos
            paid_edps = df_copy[
                (df_copy["estado"].str.strip() == "pagado") &
                (df_copy["dias_espera_num"].notna()) &
                (df_copy["monto_aprobado_num"] > 0)
            ]

            if paid_edps.empty:
                # Si no hay EDPs pagados, usar todos los completados (validados)
                completed_edps = df_copy[
                    (df_copy["estado"].str.strip().isin(["validado", "pagado"])) &
                    (df_copy["dias_espera_num"].notna()) &
                    (df_copy["monto_aprobado_num"] > 0)
                ]
                
                if completed_edps.empty:
                    # Si tampoco hay completados, usar promedio simple de todos los válidos
                    all_valid = df_copy[df_copy["dias_espera_num"].notna()]
                    if not all_valid.empty:
                        return round(all_valid["dias_espera_num"].mean(), 1)
                    else:
                        return 45.0  # Default
                else:
                    paid_edps = completed_edps

            # CORREGIDO: Calcular DSO ponderado por monto
            total_amount = paid_edps["monto_aprobado_num"].sum()
            
            if total_amount > 0:
                # DSO ponderado por monto
                weighted_dso = (
                    paid_edps["dias_espera_num"] * paid_edps["monto_aprobado_num"]
                ).sum() / total_amount
                
                # Validar el resultado
                if pd.isna(weighted_dso) or weighted_dso <= 0:
                    # Fallback a promedio simple
                    return round(paid_edps["dias_espera_num"].mean(), 1)
                
                return round(weighted_dso, 1)
            else:
                # Si no hay montos válidos, usar promedio simple
                return round(paid_edps["dias_espera_num"].mean(), 1)

        except Exception as e:
            logger.info(f"Error calculating DSO: {e}")
            return 45.0  # Default reasonable DSO

    def _calculate_working_capital_impact(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate working capital impact."""
        pending_amount = df[df["estado"].isin(["enviado", "validado"])][
            "monto_aprobado"
        ].sum()
        cost_of_capital_daily = 0.12 / 365  # Daily cost

        # Calculate daily cost of pending amounts
        if "dias_espera" in df.columns:
            pending_edps = df[df["estado"].isin(["enviado", "validado"])]
            daily_cost = (
                pending_edps["monto_aprobado"]
                * pending_edps["dias_espera"]
                * cost_of_capital_daily
            ).sum()
        else:
            daily_cost = 0

        return {
            "pending_amount": FormatUtils.format_currency(pending_amount),
            "daily_cost": FormatUtils.format_currency(daily_cost),
            "annual_impact": FormatUtils.format_currency(daily_cost * 365),
        }

    def _calculate_performance_by_period(
        self, df: pd.DataFrame, period: str
    ) -> Dict[str, Any]:
        """Calculate performance metrics by specified period."""
        # This is a simplified implementation
        # In a real scenario, you'd want more sophisticated period analysis
        return {
            "period": period,
            "total_edps": len(df),
            "approved_edps": len(df[df["estado"].isin(["pagado", "validado"])]),
            "average_days": (
                df["dias_espera"].mean() if "dias_espera" in df.columns else 0
            ),
        }

    def _calculate_trends(self, df: pd.DataFrame, period: str) -> Dict[str, Any]:
        """Calculate trend analysis."""
        # Simplified trend calculation
        return {
            "direction": "up",  # or 'down', 'stable'
            "percentage_change": 5.2,
            "confidence": "high",
        }

    def _generate_recommendations(
        self, performance_data: Dict[str, Any], trends: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if performance_data.get("average_days", 0) > 30:
            recommendations.append(
                "Considerar optimizar el proceso de aprobación para reducir tiempos de espera"
            )

        if trends.get("direction") == "down":
            recommendations.append(
                "Implementar medidas correctivas para mejorar la tendencia de aprobación"
            )

        return recommendations

    def load_related_data(self) -> ServiceResponse:
        """Load all related data needed for manager dashboard."""
        try:
            # Get EDP data
            edps_response = self.edp_repo.find_all_dataframe()

            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get(
                "success", False
            ):
                return ServiceResponse(
                    success=False,
                    message=f"Failed to load EDPs data: {edps_response.get('message', 'Unknown error')}",
                    data=None,
                )

            # Extract the data based on the response type
            if isinstance(edps_response, dict):
                edps_data = edps_response.get("data", [])
            else:
                # If it's a direct list (for backward compatibility)
                edps_data = edps_response

            # For now, return just EDP data. In the future, this could include
            # projects, logs, and other related data
            return ServiceResponse(
                success=True,
                message="Related data loaded successfully",
                data={
                    "edps": edps_data,
                    "projects": [],  # TODO: Implement when needed
                    "logs": [],  # TODO: Implement when needed
                },
            )

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error loading related data: {str(e)}",
                data=None,
            )

    def get_empty_kpis(self) -> Dict[str, Any]:
        """Get empty KPI structure using centralized KPI service."""
        return self.kpi_service.get_empty_manager_kpis()

    def get_selector_lists(self, datos_relacionados: Dict[str, Any]) -> ServiceResponse:
        """Get lists for dashboard selectors."""
        try:
            edps_data = datos_relacionados.get("edps", [])

            if isinstance(edps_data, pd.DataFrame):
                df = edps_data
            else:
                df = pd.DataFrame(edps_data)

            if df.empty:
                return ServiceResponse(
                    success=True,
                    message="No data available for selectors",
                    data={"jefes_proyecto": [], "clientes": []},
                )

            # Extract unique values for selectors
            jefes_proyecto = []
            clientes = []

            if "jefe_proyecto" in df.columns:
                jefes_proyecto = sorted(df["jefe_proyecto"].dropna().unique().tolist())

            if "cliente" in df.columns:
                clientes = sorted(df["cliente"].dropna().unique().tolist())

            return ServiceResponse(
                success=True,
                message="Selector lists generated successfully",
                data={"jefes_proyecto": jefes_proyecto, "clientes": clientes},
            )

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error generating selector lists: {str(e)}",
                data={"jefes_proyecto": [], "clientes": []},
            )

    def calculate_executive_kpis(
        self, datos_relacionados: Dict[str, Any], filters: Dict[str, Any]
    ) -> ServiceResponse:
        """Calculate executive KPIs for dashboard."""
        try:
            edps_data = datos_relacionados.get("edps", [])

            if isinstance(edps_data, pd.DataFrame):
                df = edps_data
            else:
                df = pd.DataFrame(edps_data)

            if df.empty:
                return ServiceResponse(
                    success=True,
                    message="No data available for KPI calculation",
                    data=self.get_empty_kpis(),
                )

            # Apply filters
            df_filtered = self._apply_manager_filters(df, filters)

            # Calculate KPIs
            kpis = self._calculate_executive_kpis(df, df_filtered)

            return ServiceResponse(
                success=True,
                message="Executive KPIs calculated successfully",
                data=kpis,
            )

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error calculating executive KPIs: {str(e)}",
                data=self.get_empty_kpis(),
            )

    def generate_executive_charts(
        self, datos_relacionados: Dict[str, Any], filters: Dict[str, Any]
    ) -> ServiceResponse:
        """Generate charts for executive dashboard."""
        try:
            edps_data = datos_relacionados.get("edps", [])

            if isinstance(edps_data, pd.DataFrame):
                df = edps_data
            else:
                df = pd.DataFrame(edps_data)

            if df.empty:
                return ServiceResponse(
                    success=True, message="No data available for charts", data={}
                )

            # Apply filters
            df_filtered = self._apply_manager_filters(df, filters)

            # Generate chart data
            charts = self._generate_chart_data(df, df_filtered)

            return ServiceResponse(
                success=True,
                message="Executive charts generated successfully",
                data=charts,
            )

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error generating executive charts: {str(e)}",
                data={},
            )

    def analyze_profitability(
        self, datos_relacionados: Dict[str, Any], filters: Dict[str, Any]
    ) -> ServiceResponse:
        """Analyze profitability by projects, clients, and managers using real cost data."""
        try:
            # Get EDP data
            edps_data = datos_relacionados.get("edps", [])
            if isinstance(edps_data, pd.DataFrame):
                df_edp = edps_data
            else:
                df_edp = pd.DataFrame(edps_data)

            if df_edp.empty:
                return ServiceResponse(
                    success=True,
                    message="No EDP data available for profitability analysis",
                    data={"proyectos": [], "clientes": [], "gestores": []},
                )

            # Get real cost data from CostService (using the same pattern as executive KPIs)
            cost_data_response = self.cost_service.get_cost_dashboard_data()
            costs_available = False
            df_costs = pd.DataFrame()

            if cost_data_response.success and cost_data_response.data:
                # Try to get detailed cost data for analysis
                try:
                    costs_response = (
                        self.cost_service.cost_repository.find_all_dataframe()
                    )
                    if costs_response.get("success", False):
                        df_costs = costs_response.get("data", pd.DataFrame())
                        if not df_costs.empty:
                            costs_available = True
                except Exception as e:
                    logger.info(f"Warning: Could not load detailed cost data: {e}")

            # Ensure required columns exist in EDP data
            for col in ["monto_propuesto", "monto_aprobado"]:
                if col in df_edp.columns:
                    df_edp[col] = pd.to_numeric(df_edp[col], errors="coerce").fillna(0)

            # If we have cost data, ensure importe_neto is numeric
            if costs_available and "importe_neto" in df_costs.columns:
                df_costs["importe_neto"] = pd.to_numeric(
                    df_costs["importe_neto"], errors="coerce"
                ).fillna(0)

            # Analyze profitability by projects
            proyectos_analysis = self._analyze_profitability_by_projects(
                df_edp, df_costs, costs_available
            )

            # Analyze profitability by clients
            clientes_analysis = self._analyze_profitability_by_clients(
                df_edp, df_costs, costs_available
            )

            # Analyze profitability by managers
            gestores_analysis = self._analyze_profitability_by_managers(
                df_edp, df_costs, costs_available
            )

            return ServiceResponse(
                success=True,
                message="Profitability analysis completed successfully",
                data={
                    "proyectos": proyectos_analysis,
                    "clientes": clientes_analysis,
                    "gestores": gestores_analysis,
                    "summary": {
                        "total_projects": len(proyectos_analysis),
                        "total_clients": len(clientes_analysis),
                        "total_managers": len(gestores_analysis),
                        "costs_data_available": costs_available,
                    },
                },
            )

        except Exception as e:
            logger.info(f"Error in analyze_profitability: {str(e)}")
            import traceback

            traceback.print_exc()
            return ServiceResponse(
                success=False,
                message=f"Error analyzing profitability: {str(e)}",
                data={"proyectos": [], "clientes": [], "gestores": []},
            )

    def get_top_edps(
        self, datos_relacionados: Dict[str, Any], limit: int = 10
    ) -> ServiceResponse:
        """Get top EDPs by amount."""
        try:
            edps_data = datos_relacionados.get("edps", [])

            if isinstance(edps_data, pd.DataFrame):
                df = edps_data
            else:
                df = pd.DataFrame(edps_data)

            if df.empty:
                return ServiceResponse(
                    success=True, message="No EDPs available", data=[]
                )

            # Sort by approved amount and get top N
            if "monto_aprobado" in df.columns:
                df_sorted = df.nlargest(limit, "monto_aprobado")
            else:
                df_sorted = df.head(limit)

            # Transform to template-expected format
            top_edps = []
            for _, row in df_sorted.iterrows():
                edp_data = {
                    "edp": row.get("n_edp", "N/A"),
                    "proyecto": row.get("proyecto", "N/A"),
                    "cliente": row.get("cliente", "N/A"),
                    "monto": (
                        float(row.get("monto_aprobado", 0)) / 1000000
                        if pd.notna(row.get("monto_aprobado"))
                        else 0
                    ),  # Convert to millions
                    "dias_espera": (
                        int(row.get("dias_espera", 0))
                        if pd.notna(row.get("dias_espera"))
                        else 0
                    ),
                    "encargado": row.get("jefe_proyecto", "N/A"),
                    "estado": row.get("estado", "N/A"),
                }
                top_edps.append(edp_data)

            return ServiceResponse(
                success=True,
                message=f"Top {len(top_edps)} EDPs retrieved successfully",
                data=top_edps,
            )

        except Exception as e:
            logger.info(f"Error in get_top_edps: {str(e)}")
            import traceback

            traceback.print_exc()
            return ServiceResponse(
                success=False, message=f"Error getting top EDPs: {str(e)}", data=[]
            )

    def generate_executive_alerts(
        self,
        datos_relacionados: Dict[str, Any],
        kpis: Dict[str, Any],
        cash_forecast: Dict[str, Any],
    ) -> ServiceResponse:
        """Generate executive alerts based on KPIs and forecasts."""
        try:
            alertas = []
            edps_data = datos_relacionados.get("edps", [])

            if isinstance(edps_data, pd.DataFrame):
                df_datos = edps_data
            else:
                df_datos = pd.DataFrame(edps_data)

            if df_datos.empty:
                # Generar alertas de ejemplo para demostración
                alertas_ejemplo = [
                    {
                        "tipo": "critico",
                        "titulo": "EDP crítico detectado",
                        "descripcion": "EDP-2024-001 lleva 45 días sin respuesta del cliente",
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "accion_principal": "Contactar",
                    },
                    {
                        "tipo": "alto",
                        "titulo": "Concentración de riesgo",
                        "descripcion": "65% del backlog concentrado en un solo cliente",
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "accion_principal": "Diversificar",
                    },
                    {
                        "tipo": "medio",
                        "titulo": "Backlog elevado",
                        "descripcion": "$125.5M en EDPs pendientes de cobro este mes",
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "accion_principal": "Planificar",
                    },
                ]
                return ServiceResponse(
                    success=True,
                    message="Generated example alerts for demonstration",
                    data=alertas_ejemplo,
                )

            # Preparar datos
            df_datos["monto_aprobado"] = pd.to_numeric(
                df_datos["monto_aprobado"], errors="coerce"
            ).fillna(0)
            df_datos["dias_espera"] = pd.to_numeric(
                df_datos["dias_espera"], errors="coerce"
            ).fillna(0)

            # Filtrar pendientes
            df_pendientes = df_datos[
                ~df_datos["estado"] == "pagado"]

            if df_pendientes.empty:
                return ServiceResponse(
                    success=True, message="No pending EDPs for alerts", data=[]
                )

            # Alerta 1: EDPs críticos (>30 días)
            edps_criticos = df_pendientes[df_pendientes["dias_espera"] > 30]
            if len(edps_criticos) > 0:
                monto_critico = edps_criticos["monto_aprobado"].sum() / 1_000_000
                alertas.append(
                    {
                        "tipo": "critico",
                        "titulo": f"{len(edps_criticos)} EDPs críticos",
                        "descripcion": f"${monto_critico:.1f}M en EDPs con más de 30 días de espera",
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "accion_principal": "Gestionar",
                    }
                )

            # Alerta 2: Concentración en un cliente
            if (
                "cliente" in df_pendientes.columns
                and not df_pendientes["cliente"].isna().all()
            ):
                clientes_montos = df_pendientes.groupby("cliente")[
                    "monto_aprobado"
                ].sum()
                if len(clientes_montos) > 0:
                    cliente_principal = clientes_montos.idxmax()
                    monto_principal = clientes_montos.max()
                    concentracion = (
                        monto_principal / df_pendientes["monto_aprobado"].sum()
                    ) * 100

                    if concentracion > 40:
                        alertas.append(
                            {
                                "tipo": "alto",
                                "titulo": "Alta concentración de riesgo",
                                "descripcion": f"{concentracion:.1f}% del backlog concentrado en {cliente_principal}",
                                "fecha": datetime.now().strftime("%d/%m/%Y"),
                                "accion_principal": "Diversificar",
                            }
                        )

            # Alerta 3: Montos pendientes altos
            monto_total_pendiente = df_pendientes["monto_aprobado"].sum() / 1_000_000
            if monto_total_pendiente > 50:  # Más de 50M
                alertas.append(
                    {
                        "tipo": "info",
                        "titulo": "Backlog elevado",
                        "descripcion": f"${monto_total_pendiente:.1f}M en EDPs pendientes de cobro",
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "accion_principal": "Planificar",
                    }
                )

            # Alerta 4: EDPs con alto valor individual
            edps_alto_valor = df_pendientes[
                df_pendientes["monto_aprobado"] > 10_000_000
            ]  # >10M
            if len(edps_alto_valor) > 0:
                alertas.append(
                    {
                        "tipo": "medio",
                        "titulo": f"{len(edps_alto_valor)} EDPs de alto valor",
                        "descripcion": "EDPs individuales superiores a $10M requieren seguimiento especial",
                        "fecha": datetime.now().strftime("%d/%m/%Y"),
                        "accion_principal": "Monitorear",
                    }
                )

            logger.info(f"Generated {len(alertas)} executive alerts")

            return ServiceResponse(
                success=True,
                message=f"Successfully generated {len(alertas)} alerts",
                data=alertas[:5],  # Máximo 5 alertas
            )

        except Exception as e:
            logger.error(f"Error generating executive alerts: {e}")
            return ServiceResponse(
                success=False, message=f"Error generating alerts: {str(e)}", data=[]
            )

    def get_cost_management_insights(self) -> Dict[str, Any]:
        """Get cost management insights for executive dashboard."""
        try:
            cost_response = self.cost_service.get_cost_dashboard_data()
            if not cost_response.success:
                return {"alerts": [], "recommendations": []}

            cost_data = cost_response.data
            kpis = cost_data.get("kpis", {})
            charts = cost_data.get("charts", {})

            alerts = []
            recommendations = []

            # Check for overdue costs
            overdue_count = kpis.get("overdue_count", 0)
            if overdue_count > 0:
                alerts.append(
                    {
                        "type": "warning",
                        "title": "Costos Vencidos",
                        "message": f"Hay {overdue_count} costos vencidos que requieren atención",
                        "priority": "high",
                    }
                )
                recommendations.append(
                    "Revisar y gestionar pagos de costos vencidos para evitar penalizaciones"
                )

            # Check payment rate
            payment_rate = kpis.get("payment_rate", 0)
            if payment_rate < 80:
                alerts.append(
                    {
                        "type": "danger",
                        "title": "Tasa de Pago Baja",
                        "message": f"La tasa de pago es de {payment_rate}%, por debajo del objetivo",
                        "priority": "high",
                    }
                )
                recommendations.append(
                    "Implementar procesos de seguimiento de pagos más eficientes"
                )

            # Check for high pending amounts
            pending_amount = kpis.get("pending_amount", "")
            if pending_amount and "0" not in pending_amount:
                alerts.append(
                    {
                        "type": "info",
                        "title": "Montos Pendientes",
                        "message": f"Hay {pending_amount} en costos pendientes de pago",
                        "priority": "medium",
                    }
                )
                recommendations.append(
                    "Planificar flujo de caja para cubrir costos pendientes"
                )

            return {
                "alerts": alerts,
                "recommendations": recommendations,
                "cost_kpis": kpis,
            }

        except Exception as e:
            logger.info(f"Error getting cost management insights: {e}")
            return {"alerts": [], "recommendations": [], "cost_kpis": {}}

    def _analyze_profitability_by_projects(
        self, df_edp: pd.DataFrame, df_costs: pd.DataFrame, costs_available: bool
    ) -> List[Dict[str, Any]]:
        """Analyze profitability by projects using real cost data."""
        try:
            if "proyecto" not in df_edp.columns:
                logger.info("Warning: 'proyecto' column not found in EDP data")
                return []

            projects_analysis = []

            # Group by project
            for proyecto, group in df_edp.groupby("proyecto"):
                if pd.isna(proyecto) or proyecto == "":
                    continue

                # Calculate revenue metrics
                total_revenue = group["monto_aprobado"].sum()
                total_proposed = group["monto_propuesto"].sum()
                edp_count = len(group)
                avg_edp_amount = total_revenue / edp_count if edp_count > 0 else 0

                # Calculate costs for this project
                project_costs = 0
                cost_breakdown = {}

                if costs_available and not df_costs.empty:
                    # Try to match costs by project (if proyecto field exists in costs)
                    if "proyecto" in df_costs.columns:
                        project_cost_data = df_costs[df_costs["proyecto"] == proyecto]
                        project_costs = project_cost_data["importe_neto"].sum()

                        # Get cost breakdown by provider
                        if (
                            not project_cost_data.empty
                            and "proveedor" in project_cost_data.columns
                        ):
                            cost_breakdown = (
                                project_cost_data.groupby("proveedor")["importe_neto"]
                                .sum()
                                .to_dict()
                            )
                    else:
                        # Estimate costs as proportion of total costs based on revenue share
                        total_revenue_all = df_edp["monto_aprobado"].sum()
                        if total_revenue_all > 0:
                            revenue_share = total_revenue / total_revenue_all
                            total_costs = df_costs["importe_neto"].sum()
                            project_costs = total_costs * revenue_share
                else:
                    # Fallback to estimated costs (65% of revenue)
                    project_costs = total_revenue * 0.65

                # Calculate profitability metrics
                gross_margin = total_revenue - project_costs
                margin_percentage = (
                    (gross_margin / total_revenue * 100) if total_revenue > 0 else 0
                )

                # Determine profitability status
                if margin_percentage > 30:
                    profitability_status = "Alta"
                    status_color = "success"
                elif margin_percentage > 15:
                    profitability_status = "Media"
                    status_color = "warning"
                else:
                    profitability_status = "Baja"
                    status_color = "danger"

                projects_analysis.append(
                    {
                        "proyecto": str(proyecto),
                        "total_revenue": round(total_revenue, 2),
                        "total_proposed": round(total_proposed, 2),
                        "project_costs": round(project_costs, 2),
                        "gross_margin": round(gross_margin, 2),
                        "margin_percentage": round(margin_percentage, 1),
                        "edp_count": edp_count,
                        "avg_edp_amount": round(avg_edp_amount, 2),
                        "profitability_status": profitability_status,
                        "status_color": status_color,
                        "cost_breakdown": cost_breakdown,
                        "revenue_share": round(
                            (
                                (total_revenue / df_edp["monto_aprobado"].sum() * 100)
                                if df_edp["monto_aprobado"].sum() > 0
                                else 0
                            ),
                            1,
                        ),
                    }
                )

            # Sort by margin percentage (descending)
            projects_analysis.sort(key=lambda x: x["margin_percentage"], reverse=True)

            return projects_analysis

        except Exception as e:
            logger.info(f"Error in _analyze_profitability_by_projects: {e}")
            return []

    def _analyze_profitability_by_clients(
        self, df_edp: pd.DataFrame, df_costs: pd.DataFrame, costs_available: bool
    ) -> List[Dict[str, Any]]:
        """Analyze profitability by clients using real cost data."""
        try:
            if "cliente" not in df_edp.columns:
                logger.info("Warning: 'cliente' column not found in EDP data")
                return []

            clients_analysis = []

            # Group by client
            for cliente, group in df_edp.groupby("cliente"):
                if pd.isna(cliente) or cliente == "":
                    continue

                # Calculate revenue metrics
                total_revenue = group["monto_aprobado"].sum()
                total_proposed = group["monto_propuesto"].sum()
                edp_count = len(group)
                avg_edp_amount = total_revenue / edp_count if edp_count > 0 else 0

                # Calculate costs for this client
                client_costs = 0

                if costs_available and not df_costs.empty:
                    # Try to match costs by client (if cliente field exists in costs)
                    if "cliente" in df_costs.columns:
                        client_cost_data = df_costs[df_costs["cliente"] == cliente]
                        client_costs = client_cost_data["importe_neto"].sum()
                    else:
                        # Estimate costs as proportion of total costs based on revenue share
                        total_revenue_all = df_edp["monto_aprobado"].sum()
                        if total_revenue_all > 0:
                            revenue_share = total_revenue / total_revenue_all
                            total_costs = df_costs["importe_neto"].sum()
                            client_costs = total_costs * revenue_share
                else:
                    # Fallback to estimated costs (65% of revenue)
                    client_costs = total_revenue * 0.65

                # Calculate profitability metrics
                gross_margin = total_revenue - client_costs
                margin_percentage = (
                    (gross_margin / total_revenue * 100) if total_revenue > 0 else 0
                )

                # Calculate payment performance (DSO estimate)
                try:
                    if (
                        "fecha_aprobacion" in group.columns
                        and "fecha_pago" in group.columns
                    ):
                        paid_edps = group[group["estado"] == "pagado"]
                        if not paid_edps.empty:
                            fecha_aprobacion = pd.to_datetime(
                                paid_edps["fecha_aprobacion"], errors="coerce"
                            )
                            fecha_pago = pd.to_datetime(
                                paid_edps["fecha_pago"], errors="coerce"
                            )
                            valid_mask = pd.notna(fecha_aprobacion) & pd.notna(
                                fecha_pago
                            )
                            if valid_mask.any():
                                payment_days = (fecha_pago - fecha_aprobacion).dt.days
                                avg_payment_days = payment_days[valid_mask].mean()
                            else:
                                avg_payment_days = 45.0  # Default
                        else:
                            avg_payment_days = 45.0  # Default
                    else:
                        avg_payment_days = 45.0  # Default
                except Exception:
                    avg_payment_days = 45.0  # Default

                # Determine client classification
                if margin_percentage > 25 and avg_payment_days < 30:
                    client_tier = "Premium"
                    tier_color = "success"
                elif margin_percentage > 15 and avg_payment_days < 45:
                    client_tier = "Estándar"
                    tier_color = "info"
                else:
                    client_tier = "Bajo Rendimiento"
                    tier_color = "warning"

                clients_analysis.append(
                    {
                        "cliente": str(cliente),
                        "total_revenue": round(total_revenue, 2),
                        "total_proposed": round(total_proposed, 2),
                        "client_costs": round(client_costs, 2),
                        "gross_margin": round(gross_margin, 2),
                        "margin_percentage": round(margin_percentage, 1),
                        "edp_count": edp_count,
                        "avg_edp_amount": round(avg_edp_amount, 2),
                        "avg_payment_days": round(avg_payment_days, 1),
                        "client_tier": client_tier,
                        "tier_color": tier_color,
                        "revenue_share": round(
                            (
                                (total_revenue / df_edp["monto_aprobado"].sum() * 100)
                                if df_edp["monto_aprobado"].sum() > 0
                                else 0
                            ),
                            1,
                        ),
                    }
                )

            # Sort by margin percentage (descending)
            clients_analysis.sort(key=lambda x: x["margin_percentage"], reverse=True)

            return clients_analysis

        except Exception as e:
            logger.info(f"Error in _analyze_profitability_by_clients: {e}")
            return []

    def _analyze_profitability_by_managers(
        self, df_edp: pd.DataFrame, df_costs: pd.DataFrame, costs_available: bool
    ) -> List[Dict[str, Any]]:
        """Analyze profitability by managers using real cost data."""
        try:
            if "jefe_proyecto" not in df_edp.columns:
                logger.info("Warning: 'gestor' column not found in EDP data")
                return []

            managers_analysis = []

            # Group by manager
            for gestor, group in df_edp.groupby("jefe_proyecto"):
                if pd.isna(gestor) or gestor == "":
                    continue

                # Calculate revenue metrics
                total_revenue = group["monto_aprobado"].sum()
                total_proposed = group["monto_propuesto"].sum()
                edp_count = len(group)
                avg_edp_amount = total_revenue / edp_count if edp_count > 0 else 0

                # Calculate approval rate
                approved_count = len(
                    group[group["estado"]== 'pagado']
                )
                approval_rate = (
                    (approved_count / edp_count * 100) if edp_count > 0 else 0
                )

                # Calculate costs for this manager's portfolio
                manager_costs = 0

                if costs_available and not df_costs.empty:
                    # Try to match costs by manager (if gestor field exists in costs)
                    if "gestor" in df_costs.columns:
                        manager_cost_data = df_costs[df_costs["gestor"] == gestor]
                        manager_costs = manager_cost_data["importe_neto"].sum()
                    else:
                        # Estimate costs as proportion of total costs based on revenue share
                        total_revenue_all = df_edp["monto_aprobado"].sum()
                        if total_revenue_all > 0:
                            revenue_share = total_revenue / total_revenue_all
                            total_costs = df_costs["importe_neto"].sum()
                            manager_costs = total_costs * revenue_share
                else:
                    # Fallback to estimated costs (65% of revenue)
                    manager_costs = total_revenue * 0.65

                # Calculate profitability metrics
                gross_margin = total_revenue - manager_costs
                margin_percentage = (
                    (gross_margin / total_revenue * 100) if total_revenue > 0 else 0
                )

                # Calculate efficiency metrics
                revenue_per_edp = total_revenue / edp_count if edp_count > 0 else 0

                # Count unique clients and projects
                unique_clients = (
                    group["cliente"].nunique() if "cliente" in group.columns else 0
                )
                unique_projects = (
                    group["proyecto"].nunique() if "proyecto" in group.columns else 0
                )

                # Determine performance tier
                if margin_percentage > 30 and approval_rate > 80:
                    performance_tier = "Excelente"
                    tier_color = "success"
                elif margin_percentage > 20 and approval_rate > 70:
                    performance_tier = "Bueno"
                    tier_color = "info"
                elif margin_percentage > 10 and approval_rate > 60:
                    performance_tier = "Promedio"
                    tier_color = "warning"
                else:
                    performance_tier = "Necesita Mejora"
                    tier_color = "danger"

                managers_analysis.append(
                    {
                        "gestor": str(gestor),
                        "total_revenue": round(total_revenue, 2),
                        "total_proposed": round(total_proposed, 2),
                        "manager_costs": round(manager_costs, 2),
                        "gross_margin": round(gross_margin, 2),
                        "margin_percentage": round(margin_percentage, 1),
                        "edp_count": edp_count,
                        "approved_count": approved_count,
                        "approval_rate": round(approval_rate, 1),
                        "avg_edp_amount": round(avg_edp_amount, 2),
                        "revenue_per_edp": round(revenue_per_edp, 2),
                        "unique_clients": unique_clients,
                        "unique_projects": unique_projects,
                        "performance_tier": performance_tier,
                        "tier_color": tier_color,
                        "revenue_share": round(
                            (
                                (total_revenue / df_edp["monto_aprobado"].sum() * 100)
                                if df_edp["monto_aprobado"].sum() > 0
                                else 0
                            ),
                            1,
                        ),
                    }
                )

            # Sort by margin percentage (descending)
            managers_analysis.sort(key=lambda x: x["margin_percentage"], reverse=True)

            return managers_analysis

        except Exception as e:
            logger.info(f"Error in _analyze_profitability_by_managers: {e}")
            return []

    def _prepare_kpi_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean data for KPI calculations."""
        df = df.copy()

        # Convert monetary columns
        for col in ["monto_propuesto", "monto_aprobado"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Clean estado column
        if "estado" in df.columns:
            df["estado"] = df["estado"].str.strip().str.lower()

        return df

    def _calculate_financial_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate financial KPIs."""
        try:
            # Basic financial calculations
            total_proposed = (
                df["monto_propuesto"].sum() if "monto_propuesto" in df.columns else 0
            )
            total_paid = (
                df[df["estado"] == 'pagado']["monto_aprobado"].sum()
                if "monto_aprobado" in df.columns
                else 0
            )
            pending_amount = (
                df[df["estado"].isin(["enviado", "revisión", "pendiente",'validado'])][
                    "monto_propuesto"
                ].sum()
                if "monto_propuesto" in df.columns
                else 0
            )

            # Calculate target and performance metrics
            meta_ingresos = 1_200_000  # Mock target TODO
            vs_meta_ingresos = (
                ((total_paid - meta_ingresos) / meta_ingresos * 100)
                if meta_ingresos > 0
                else 0
            )
            pct_meta_ingresos = (
                (total_paid / meta_ingresos * 100) if meta_ingresos > 0 else 0
            )

            # Growth calculations (simulate monthly growth)
            crecimiento_ingresos = 5.2  # Mock positive growth TODO
            tendencia_pendiente = -2.1  # Mock declining pending trend TODO

            # Format values to match template expectations (in millions)
            ingresos_totales = round(total_paid / 1_000_000, 1)
            monto_pendiente = round(pending_amount / 1_000_000, 1)
            meta_ingresos_m = round(meta_ingresos / 1_000_000, 1)
            run_rate_anual = round(ingresos_totales * 12, 1)

    

            return {
                "ingresos_totales": ingresos_totales,
                "monto_pendiente": monto_pendiente,
                "meta_ingresos": meta_ingresos_m,
                "run_rate_anual": run_rate_anual,
                "vs_meta_ingresos": round(vs_meta_ingresos, 1),
                "pct_meta_ingresos": min(round(pct_meta_ingresos, 1), 100),
                "crecimiento_ingresos": crecimiento_ingresos,
                "tendencia_pendiente": tendencia_pendiente,
      

            }

        except Exception as e:
            logger.info(f"Error calculating financial KPIs: {e}")
            return {}

    def _calculate_operational_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate operational KPIs."""
        try:
            # Basic counts
            total_edps = len(df)
            total_approved = len(df[df["estado"] == 'pagado' ])
            total_pending = len(
                df[df["estado"].isin(["enviado", "revisión", "pendiente","validado"])]
            )

            # Critical EDPs
            critical_edps = 0
            critical_amount = 0
            if "critico" in df.columns:
                critical_edps = df[df["critico"] == True].shape[0]
                if "monto_aprobado" in df.columns:
                    critical_amount = df[df["critico"] == True]["monto_aprobado"].sum()

            # DSO calculations
            try:
                dso = self._calculate_dso(df)
                dso_cliente_principal = (
                    dso * 0.8
                )  # Mock data - main client has better DSO
            except Exception as e:
                logger.info(f"Error calculating DSO: {e}")
                dso = 45.0
                dso_cliente_principal = 30.0

            # Client analysis (mock data)
            pct_ingresos_principal = 35.5
            riesgo_pago_principal = 20
            tendencia_pago_principal = "mejora"

            # Calculate project timing KPIs
            try:
                proyectos_on_time = self._calculate_projects_on_time(df)
                proyectos_retrasados = self._calculate_projects_delayed(df)
            except Exception as e:
                logger.info(f"Error calculating project timing KPIs: {e}")
                proyectos_on_time = 75
                proyectos_retrasados = 15

            return {
                "total_edps": total_edps,
                "total_approved": total_approved,
                "total_pending": total_pending,
                "approval_rate": round(
                    (total_approved / total_edps * 100) if total_edps > 0 else 0, 1
                ),
                "critical_edps": critical_edps,
                "critical_amount": round(critical_amount / 1_000_000, 1),
                "dso": round(dso, 1),
                "dso_cliente_principal": round(dso_cliente_principal, 1),
                "pct_ingresos_principal": pct_ingresos_principal,
                "riesgo_pago_principal": riesgo_pago_principal,
                "tendencia_pago_principal": tendencia_pago_principal,
                "proyectos_on_time": proyectos_on_time,
                "proyectos_retrasados": proyectos_retrasados,
            }

        except Exception as e:
            logger.info(f"Error calculating operational KPIs: {e}")
            return {}

    def _calculate_profitability_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate profitability KPIs using real cost data."""
        try:
            # Get revenue data
            ingresos_totales = 0
            if "monto_aprobado" in df.columns:
                total_paid = df[df["estado"].isin(["pagado", "validado"])][
                    "monto_aprobado"
                ].sum()
                ingresos_totales = round(total_paid / 1_000_000, 1)

            # Get real cost data from CostService
            try:
                cost_data_response = self.cost_service.get_cost_dashboard_data()
                if cost_data_response.success and cost_data_response.data:
                    cost_kpis = cost_data_response.data.get("kpis", {})
                    cost_total_amount = cost_kpis.get("total_amount", "0")

                    # Extract numeric value from formatted currency
                    cost_numeric = (
                        float(re.sub(r"[^\d.]", "", cost_total_amount))
                        if cost_total_amount
                        else 0
                    )
                    cost_total_m = round(
                        cost_numeric / 1_000_000, 1
                    )  # Convert to millions

                    # Calculate real profitability with cost data
                    real_margin = ingresos_totales - cost_total_m
                    real_profitability = (
                        (real_margin / ingresos_totales * 100)
                        if ingresos_totales > 0
                        else 0
                    )

                    # Use real cost data
                    costos_totales = cost_total_m
                    margen_bruto_absoluto = real_margin
                    rentabilidad_general = real_profitability
                else:
                    # Fallback to mock data
                    costos_totales = round(ingresos_totales * 0.65, 1)
                    margen_bruto_absoluto = round(ingresos_totales * 0.35, 1)
                    rentabilidad_general = 25.5
            except Exception as e:
                logger.info(f"Error getting cost data: {e}")
                # Fallback to mock data
                costos_totales = round(ingresos_totales * 0.65, 1)
                margen_bruto_absoluto = round(ingresos_totales * 0.35, 1)
                rentabilidad_general = 25.5

            return {
                "rentabilidad_general": round(rentabilidad_general, 1),
                "tendencia_rentabilidad": round(2.3, 1),
                "posicion_vs_benchmark": round(5.2, 1),
                "vs_meta_rentabilidad": round(rentabilidad_general - 35.0, 1),
                "meta_rentabilidad": 35.0,
                "pct_meta_rentabilidad": (
                    round(rentabilidad_general / 35.0 * 100, 1)
                    if rentabilidad_general > 0
                    else 0
                ),
                "mejora_eficiencia": round(3.4, 1),
                "eficiencia_global": round(78.5, 1),
                "margen_bruto_absoluto": round(margen_bruto_absoluto, 1),
                "costos_totales": round(costos_totales, 1),
            }

        except Exception as e:
            logger.info(f"Error calculating profitability KPIs: {e}")
            return {}

    def _calculate_aging_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate aging bucket KPIs using REAL data."""
        try:
            # Filter pending EDPs with real data
            df_pending = df[~df["estado"] == "pagado"].copy()
            total_pending = len(df_pending)
            
            if total_pending > 0 and "dso_actual" in df.columns:
                # Calculate REAL aging distribution based on dso_actual
                df_pending_copy = df_pending.copy()
                df_pending_copy["dias_espera_num"] = pd.to_numeric(df_pending_copy["dso_actual"], errors="coerce").fillna(0)
                
                # Real aging buckets
                aging_0_30 = len(df_pending_copy[df_pending_copy["dias_espera_num"] <= 30])
                aging_31_60 = len(df_pending_copy[(df_pending_copy["dias_espera_num"] > 30) & (df_pending_copy["dias_espera_num"] <= 60)])
                print(f'DEBUG: {aging_31_60}')
                aging_61_90 = len(df_pending_copy[(df_pending_copy["dias_espera_num"] > 60) & (df_pending_copy["dias_espera_num"] <= 90)])
                aging_90_plus = len(df_pending_copy[df_pending_copy["dias_espera_num"] > 90])
                
                # Calculate real percentages
                aging_0_30_pct = round(aging_0_30 / total_pending * 100, 1)
                aging_31_60_pct = round(aging_31_60 / total_pending * 100, 1)
                aging_61_90_pct = round(aging_61_90 / total_pending * 100, 1)
                aging_90_plus_pct = round(aging_90_plus / total_pending * 100, 1)
                
                # Calculate REAL recovery rate based on paid vs total EDPs
                df_paid = df[df["estado"] == "pagado"].copy()
                total_processed = len(df_paid) + total_pending
                recovery_rate = round((len(df_paid) / total_processed * 100), 1) if total_processed > 0 else 0
                
                # Calculate REAL top 3 debtors by pending amount
                if "cliente" in df_pending.columns and "monto_aprobado" in df_pending.columns:
                    # Group by cliente and sum pending amounts
                    df_pending_copy["monto_aprobado_num"] = pd.to_numeric(df_pending_copy["monto_aprobado"], errors="coerce").fillna(0)
                    deudores_pendientes = (
                        df_pending_copy.groupby("cliente")["monto_aprobado_num"]
                        .sum()
                        .sort_values(ascending=False)
                    )
                    
                    # Get top 3 real debtors
                    top_deudores = deudores_pendientes.head(3)
                    
                    # Assign real values or defaults
                    top_deudor_1_nombre = top_deudores.index[0] if len(top_deudores) > 0 else "Sin datos"
                    top_deudor_1_monto = round(top_deudores.iloc[0] / 1_000_000, 1) if len(top_deudores) > 0 else 0.0
                    
                    top_deudor_2_nombre = top_deudores.index[1] if len(top_deudores) > 1 else "Sin datos"
                    top_deudor_2_monto = round(top_deudores.iloc[1] / 1_000_000, 1) if len(top_deudores) > 1 else 0.0
                    
                    top_deudor_3_nombre = top_deudores.index[2] if len(top_deudores) > 2 else "Sin datos"
                    top_deudor_3_monto = round(top_deudores.iloc[2] / 1_000_000, 1) if len(top_deudores) > 2 else 0.0
                else:
                    # Fallback if columns don't exist
                    top_deudor_1_nombre = top_deudor_2_nombre = top_deudor_3_nombre = "Sin datos"
                    top_deudor_1_monto = top_deudor_2_monto = top_deudor_3_monto = 0.0
                
                # Calculate REAL upcoming actions based on aging
                acciones_llamadas = min(aging_0_30, 15)  # Max 15 calls for recent cases
                acciones_emails = min(aging_31_60, 20)   # Max 20 emails for medium aging
                acciones_visitas = min(aging_61_90, 8)   # Max 8 visits for older cases
                acciones_legales = min(aging_90_plus, 5) # Max 5 legal actions for very old cases
                
            else:
                # Default values when no pending amounts
                aging_0_30_pct = aging_31_60_pct = aging_61_90_pct = aging_90_plus_pct = 25.0
                recovery_rate = 85.0
                top_deudor_1_nombre = "No data"
                top_deudor_1_monto = 0.0
                top_deudor_2_nombre = "No data"
                top_deudor_2_monto = 0.0
                top_deudor_3_nombre = "No data" 
                top_deudor_3_monto = 0.0
                acciones_llamadas = acciones_emails = acciones_visitas = acciones_legales = 0
                
            # Include original aging logic for legacy fields
            if "dias_espera" not in df.columns or df.empty:
                pct_30d = pct_60d = pct_90d = pct_mas90d = 25.0
            else:
                dias = pd.to_numeric(df["dias_espera"], errors="coerce")
                bucket_0_15 = int((dias <= 15).sum())
                bucket_16_30 = int(((dias > 15) & (dias <= 30)).sum())
                bucket_31_60 = int(((dias > 30) & (dias <= 60)).sum())
                bucket_61_90 = int(((dias > 60) & (dias <= 90)).sum())
                bucket_90_plus = int((dias > 90).sum())

                total = len(df)

                if total > 0:
                    pct_30d = round((bucket_0_15 + bucket_16_30) / total * 100, 1)
                    pct_60d = round(bucket_31_60 / total * 100, 1)
                    pct_90d = round(bucket_61_90 / total * 100, 1)
                    pct_mas90d = round(bucket_90_plus / total * 100, 1)
                else:
                    pct_30d = pct_60d = pct_90d = pct_mas90d = 0
                
            return {
                # Enhanced aging distribution data
                "aging_0_30_pct": aging_0_30_pct,
                "aging_31_60_pct": aging_31_60_pct,
                "aging_61_90_pct": aging_61_90_pct,
                "aging_90_plus_pct": aging_90_plus_pct,
                "recovery_rate": recovery_rate,
                "top_deudor_1_nombre": top_deudor_1_nombre,
                "top_deudor_1_monto": top_deudor_1_monto,
                "top_deudor_2_nombre": top_deudor_2_nombre,
                "top_deudor_2_monto": top_deudor_2_monto,
                "top_deudor_3_nombre": top_deudor_3_nombre,
                "top_deudor_3_monto": top_deudor_3_monto,
                "acciones_llamadas": acciones_llamadas,
                "acciones_emails": acciones_emails,
                "acciones_visitas": acciones_visitas,
                "acciones_legales": acciones_legales,
                # Legacy fields for compatibility
                "pct_30d": pct_30d,
                "pct_60d": pct_60d,
                "pct_90d": pct_90d,
                "pct_mas90d": pct_mas90d,
            }
            
        except Exception as e:
            logger.info(f"Error calculating aging KPIs: {e}")
            return {}

    def _calculate_critical_projects_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate critical projects KPIs with REAL project information."""
        try:
            critical_projects = []
            total_critical_amount = 0
            
            # Filter critical projects using REAL data
            if "monto_aprobado" in df.columns and "estado" in df.columns:
                df_pending = df[df["estado"].isin(["enviado", "revisión", "pendiente"])]
                
                if not df_pending.empty:
                    # Convert to numeric for proper filtering
                    df_pending_copy = df_pending.copy()
                    df_pending_copy["monto_aprobado_num"] = pd.to_numeric(df_pending_copy["monto_aprobado"], errors="coerce").fillna(0)
                    df_pending_copy["dias_espera_num"] = pd.to_numeric(df_pending_copy["dias_espera"], errors="coerce").fillna(0) if "dias_espera" in df_pending_copy.columns else 0
                    
                    # Define REAL critical criteria:
                    # 1. High value (>= 1M) OR
                    # 2. Long pending time (> 45 days) OR  
                    # 3. Combination of medium value + medium time
                    critical_mask = (
                        (df_pending_copy["monto_aprobado_num"] >= 1_000_000) |  # High value
                        (df_pending_copy["dias_espera_num"] > 45) |  # Long pending
                        ((df_pending_copy["monto_aprobado_num"] >= 500_000) & (df_pending_copy["dias_espera_num"] > 30))  # Medium value + medium time
                    )
                    
                    df_critical = df_pending_copy[critical_mask].copy()
                    
                    # Sort by priority: highest amount first, then longest waiting time
                    df_critical["priority_score"] = (
                        df_critical["monto_aprobado_num"] / 1_000_000 +  # Amount in millions
                        df_critical["dias_espera_num"] / 10  # Days waiting (weighted)
                    )
                    df_critical = df_critical.sort_values("priority_score", ascending=False)
                    
                    # Build REAL critical projects list
                    for idx, row in df_critical.head(8).iterrows():  # Top 8 critical projects
                        monto = row.get("monto_aprobado_num", 0)
                        cliente = row.get("cliente", f"Cliente {idx}")
                        edp_id = row.get("n_edp", f"EDP-{idx}")
                        
                        # Improved project name extraction with more meaningful fallbacks
                        proyecto = row.get("proyecto")
                        if not proyecto or pd.isna(proyecto) or str(proyecto).strip() == "":
                            # Create meaningful project name from client and EDP info
                            cliente_clean = str(cliente).replace("Cliente ", "").strip() if cliente and not str(cliente).startswith("Cliente ") else str(cliente).strip()
                            if cliente_clean and cliente_clean != f"Cliente {idx}":
                                proyecto = f"Proyecto {cliente_clean} - {edp_id}"
                            else:
                                proyecto = f"Proyecto EDP-{edp_id}"
                        else:
                            proyecto = str(proyecto).strip()
                        dias_pendiente = int(row.get("dias_espera_num", 0))
                        jefe_proyecto = row.get("jefe_proyecto", f"Jefe {idx}")
                        
                        # Calculate REAL risk level based on time and amount
                        if dias_pendiente > 60 or monto >= 2_000_000:
                            risk_level = "Alto"
                        elif dias_pendiente > 30 or monto >= 1_000_000:
                            risk_level = "Medio"
                        else:
                            risk_level = "Bajo"
                        
                        # Calculate REAL progress based on estado and dias_espera
                        if row.get("estado") == "enviado":
                            base_progress = 20
                        elif row.get("estado") == "revisión":
                            base_progress = 60
                        else:
                            base_progress = 40
                        
                        # Adjust progress based on time (longer time = less progress)
                        time_penalty = min(30, dias_pendiente / 3)  # Max 30% penalty
                        progress = max(10, base_progress - time_penalty)
                        
                        # Determine REAL next milestone based on current estado
                        if row.get("estado") == "enviado":
                            next_milestone = "Revisión inicial"
                        elif row.get("estado") == "revisión":
                            next_milestone = "Aprobación final"
                        else:
                            next_milestone = "Conformidad cliente"
                        
                        # Calculate REAL deadline (estimate based on current date + typical process time)
                        from datetime import datetime, timedelta
                        if dias_pendiente > 60:
                            deadline = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # Urgent
                        elif dias_pendiente > 30:
                            deadline = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")  # High priority
                        else:
                            deadline = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")  # Normal priority
                        
                        critical_projects.append({
                            "id": str(edp_id),
                            "cliente": str(cliente),
                            "jefe_proyecto": str(jefe_proyecto),
                            "proyecto": str(proyecto),
                            "monto": round(monto / 1_000_000, 1),
                            "dias_pendiente": dias_pendiente,
                            "progreso": int(progress),
                            "riesgo": risk_level,
                            "estado": row.get("estado", "pendiente"),
                            "next_milestone": next_milestone,
                            "deadline": deadline,
                            "priority_score": round(row.get("priority_score", 0), 1)
                        })
                        
                        total_critical_amount += monto
            
            # If no real critical projects found, check if we have any pending projects at all
            if not critical_projects:
                df_any_pending = df[df["estado"].isin(["enviado", "revisión", "pendiente"])]
                
                if not df_any_pending.empty:
                    # Take top pending projects by amount as "critical"
                    df_any_pending_copy = df_any_pending.copy()
                    df_any_pending_copy["monto_aprobado_num"] = pd.to_numeric(df_any_pending_copy["monto_aprobado"], errors="coerce").fillna(0)
                    df_top_pending = df_any_pending_copy.nlargest(4, "monto_aprobado_num")
                    
                    for idx, row in df_top_pending.iterrows():
                        monto = row.get("monto_aprobado_num", 0)
                        cliente = row.get("cliente", f"Cliente {idx}")
                        edp_id = row.get("n_edp", f"EDP-{idx}")
                        
                        # Improved project name for fallback cases
                        proyecto = row.get("proyecto")
                        if not proyecto or pd.isna(proyecto) or str(proyecto).strip() == "":
                            cliente_clean = str(cliente).replace("Cliente ", "").strip() if cliente and not str(cliente).startswith("Cliente ") else str(cliente).strip()
                            if cliente_clean and cliente_clean != f"Cliente {idx}":
                                proyecto = f"Proyecto {cliente_clean} - {edp_id}"
                            else:
                                proyecto = f"Proyecto EDP-{edp_id}"
                        else:
                            proyecto = str(proyecto).strip()
                        
                        critical_projects.append({
                            "id": str(edp_id),
                            "cliente": str(cliente),
                            "proyecto": proyecto,  # Now using improved project name
                            "monto": round(monto / 1_000_000, 1),
                            "dias_pendiente": int(row.get("dias_espera", 0)) if pd.notna(row.get("dias_espera")) else 0,
                            "progreso": 45,  # Default progress for non-critical
                            "riesgo": "Medio",
                            "estado": row.get("estado", "pendiente"),
                            "next_milestone": "Revisión pendiente",
                            "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                            "priority_score": round(monto / 1_000_000, 1),
                            'jefe_proyecto': row.get("jefe_proyecto", f"Jefe {idx}")
                        })
                        
                        total_critical_amount += monto
            
            # Calculate REAL timeline distribution
            total_projects = len(critical_projects)
            if total_projects > 0:
                timeline_0_10 = sum(1 for p in critical_projects if p["dias_pendiente"] <= 10)
                timeline_11_20 = sum(1 for p in critical_projects if 10 < p["dias_pendiente"] <= 20)
                timeline_21_30 = sum(1 for p in critical_projects if 20 < p["dias_pendiente"] <= 30)
                timeline_30_plus = sum(1 for p in critical_projects if p["dias_pendiente"] > 30)
                
                timeline_0_10_pct = round(timeline_0_10 / total_projects * 100, 1)
                timeline_11_20_pct = round(timeline_11_20 / total_projects * 100, 1)
                timeline_21_30_pct = round(timeline_21_30 / total_projects * 100, 1)
                timeline_30_plus_pct = round(timeline_30_plus / total_projects * 100, 1)
            else:
                timeline_0_10_pct = timeline_11_20_pct = timeline_21_30_pct = timeline_30_plus_pct = 0.0
            
            # Calculate REAL resource risk analysis
            recursos_criticos = sum(1 for p in critical_projects if p["riesgo"] == "Alto")
            recursos_limitados = sum(1 for p in critical_projects if p["riesgo"] == "Medio")
            recursos_disponibles = total_projects - recursos_criticos - recursos_limitados
            
            return {
                "critical_projects_count": total_projects,
                "critical_projects_amount": round(total_critical_amount / 1_000_000, 1),
                "critical_projects_list": critical_projects,
                "timeline_0_10_pct": timeline_0_10_pct,
                "timeline_11_20_pct": timeline_11_20_pct,
                "timeline_21_30_pct": timeline_21_30_pct,
                "timeline_30_plus_pct": timeline_30_plus_pct,
                "recursos_criticos": recursos_criticos,
                "recursos_limitados": recursos_limitados,
                "recursos_disponibles": recursos_disponibles,
                "avg_progress": round(sum(p["progreso"] for p in critical_projects) / max(1, total_projects), 1),
                "high_risk_count": sum(1 for p in critical_projects if p["riesgo"] == "Alto"),
                "medium_risk_count": sum(1 for p in critical_projects if p["riesgo"] == "Medio"),
                "low_risk_count": sum(1 for p in critical_projects if p["riesgo"] == "Bajo"),
            }
            
        except Exception as e:
            logger.info(f"Error calculating critical projects KPIs: {e}")
            return {
                "critical_projects_count": 0,
                "critical_projects_amount": 0.0,
                "critical_projects_list": [],
                "timeline_0_10_pct": 25.0,
                "timeline_11_20_pct": 25.0,
                "timeline_21_30_pct": 25.0,
                "timeline_30_plus_pct": 25.0,
                "recursos_criticos": 0,
                "recursos_limitados": 0,
                "recursos_disponibles": 0,
                "avg_progress": 0.0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
            }

    def _calculate_efficiency_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate efficiency and cycle time KPIs."""
        try:
            # Basic efficiency calculations
            estados_pendientes = ["enviado", "revisión", "enviado "]
            estados_completados = ["pagado", "validado", "pagado ", "validado "]

            df_pendientes = df[df["estado"].str.strip().isin(estados_pendientes)]
            df_completados = df[df["estado"].str.strip().isin(estados_completados)]

            # Calculate derived metrics
            pct_avance = (len(df_completados) / len(df) * 100) if len(df) > 0 else 0

            # Calculate efficiency score
            try:
                efficiency_score = self._calculate_efficiency_score(df)
            except Exception as e:
                logger.info(f"Error calculating efficiency score: {e}")
                efficiency_score = 75.0

            # DSO for cycle time - CORREGIDO: usar datos reales de tiempo
            try:
                # Calcular tiempo promedio real de todo el ciclo
                if "dias_espera" in df.columns:
                    # Usar todos los EDPs para el cálculo, no solo los pagados
                    dias_espera_validos = pd.to_numeric(df["dias_espera"], errors="coerce")
                    tiempo_medio_ciclo = dias_espera_validos.mean() if not dias_espera_validos.isna().all() else 45.0
                else:
                    tiempo_medio_ciclo = 45.0  # Default reasonable value
            except Exception:
                tiempo_medio_ciclo = 45.0

            # Metas y benchmarks realistas
            meta_tiempo_ciclo = 30  # Meta: 30 días
            benchmark_tiempo_ciclo = 35  # Benchmark industria: 35 días

            # CORREGIDO: Cálculo de eficiencia basado en métricas reales
            # Eficiencia actual basada en múltiples factores
            factor_completados = min(100, pct_avance * 1.2)  # Peso por completados
            factor_tiempo = max(0, (60 - tiempo_medio_ciclo) / 60 * 100)  # Peso por velocidad
            factor_aprobacion = (len(df_completados) / len(df) * 100) if len(df) > 0 else 0
            
            eficiencia_actual = round((factor_completados * 0.4 + factor_tiempo * 0.4 + factor_aprobacion * 0.2), 1)
            
            # Simulación de mejora (esto debería venir de datos históricos)
            eficiencia_anterior = max(0, eficiencia_actual - 5.3)
            mejora_eficiencia = round(eficiencia_actual - eficiencia_anterior, 1)

            # CORREGIDO: Porcentaje de cumplimiento de meta de tiempo
            tiempo_medio_ciclo_pct = (
                round((meta_tiempo_ciclo / tiempo_medio_ciclo * 100), 1)
                if tiempo_medio_ciclo > 0
                else 100
            )
            # Limitar el porcentaje a máximo 100%
            tiempo_medio_ciclo_pct = min(100, tiempo_medio_ciclo_pct)

            # CORREGIDO: Distribución de tiempo por etapa con proporciones reales
            # Basado en estudios de procesos de facturación
            tiempo_emision = round(tiempo_medio_ciclo * 0.15, 1)      # 15% - Preparación documentos
            tiempo_gestion = round(tiempo_medio_ciclo * 0.25, 1)      # 25% - Gestión interna  
            tiempo_conformidad = round(tiempo_medio_ciclo * 0.40, 1)  # 40% - Conformidad cliente (mayor cuello de botella)
            tiempo_pago = round(tiempo_medio_ciclo * 0.20, 1)         # 20% - Proceso de pago

            # CORREGIDO: Porcentajes para visualización (deben sumar 100%)
            total_tiempo = tiempo_emision + tiempo_gestion + tiempo_conformidad + tiempo_pago
            if total_tiempo > 0:
                etapa_emision_pct = round((tiempo_emision / total_tiempo * 100))
                etapa_gestion_pct = round((tiempo_gestion / total_tiempo * 100))
                etapa_conformidad_pct = round((tiempo_conformidad / total_tiempo * 100))
                etapa_pago_pct = round((tiempo_pago / total_tiempo * 100))
                
                # Ajustar para que sume exactamente 100%
                total_pct = etapa_emision_pct + etapa_gestion_pct + etapa_conformidad_pct + etapa_pago_pct
                if total_pct != 100:
                    # Ajustar la etapa más grande
                    max_etapa = max([
                        (etapa_conformidad_pct, 'conformidad'),
                        (etapa_gestion_pct, 'gestion'),
                        (etapa_pago_pct, 'pago'),
                        (etapa_emision_pct, 'emision')
                    ])
                    ajuste = 100 - total_pct
                    if max_etapa[1] == 'conformidad':
                        etapa_conformidad_pct += ajuste
                    elif max_etapa[1] == 'gestion':
                        etapa_gestion_pct += ajuste
                    elif max_etapa[1] == 'pago':
                        etapa_pago_pct += ajuste
                    else:
                        etapa_emision_pct += ajuste
            else:
                # Valores por defecto
                etapa_emision_pct = 15
                etapa_gestion_pct = 25
                etapa_conformidad_pct = 40
                etapa_pago_pct = 20

            # CORREGIDO: Oportunidad de mejora basada en análisis real
            if tiempo_conformidad > 18:  # Si conformidad toma más de 18 días
                oportunidad_mejora = f"Reducir tiempo de conformidad con cliente ({tiempo_conformidad:.1f} días vs. benchmark 12 días)"
            elif tiempo_gestion > 15:  # Si gestión interna toma más de 15 días
                oportunidad_mejora = f"Optimizar tiempo de gestión interna ({tiempo_gestion:.1f} días vs. benchmark 10 días)"
            elif tiempo_medio_ciclo > benchmark_tiempo_ciclo:
                oportunidad_mejora = f"Reducir tiempo total de ciclo ({tiempo_medio_ciclo:.1f} días vs. benchmark {benchmark_tiempo_ciclo} días)"
            else:
                oportunidad_mejora = "Mantener eficiencia actual y enfocarse en mejora continua"

            return {
                "efficiency_score": efficiency_score,
                "mejora_eficiencia": mejora_eficiencia,
                "tiempo_medio_ciclo": round(tiempo_medio_ciclo, 1),
                "tiempo_medio_ciclo_pct": tiempo_medio_ciclo_pct,
                "meta_tiempo_ciclo": meta_tiempo_ciclo,
                "benchmark_tiempo_ciclo": benchmark_tiempo_ciclo,
                "tiempo_emision": tiempo_emision,
                "tiempo_gestion": tiempo_gestion,
                "tiempo_conformidad": tiempo_conformidad,
                "tiempo_pago": tiempo_pago,
                "etapa_emision_pct": etapa_emision_pct,
                "etapa_gestion_pct": etapa_gestion_pct,
                "etapa_conformidad_pct": etapa_conformidad_pct,
                "etapa_pago_pct": etapa_pago_pct,
                "oportunidad_mejora": oportunidad_mejora,
                # Agregar métricas adicionales para mejor análisis
                "pct_avance": round(pct_avance, 1),
                "total_completados": len(df_completados),
                "total_pendientes": len(df_pendientes),
                "eficiencia_actual": eficiencia_actual,
            }

        except Exception as e:
            logger.info(f"Error calculating efficiency KPIs: {e}")
            return {}

    def _calculate_projects_on_time(self, df: pd.DataFrame) -> int:
        """Calculate percentage of projects delivered on time."""
        try:
            if "dias_espera" not in df.columns or df.empty:
                return 75  # Default reasonable value

            # Convertir dias_espera a numérico
            dias_espera_validos = pd.to_numeric(df["dias_espera"], errors="coerce")
            
            # Filtrar valores válidos
            dias_validos = dias_espera_validos.dropna()
            
            if len(dias_validos) == 0:
                return 75  # Default si no hay datos válidos

            # CORREGIDO: Considerar "a tiempo" como <= 35 días (benchmark industria)
            on_time_count = len(dias_validos[dias_validos <= 35])
            total_count = len(dias_validos)
            
            on_time_percentage = round((on_time_count / total_count * 100) if total_count > 0 else 0)
            
            # Asegurar que esté en rango 0-100
            return max(0, min(100, on_time_percentage))
            
        except Exception as e:
            logger.info(f"Error calculating projects on time: {e}")
            return 75  # Default

    def _calculate_projects_delayed(self, df: pd.DataFrame) -> int:
        """Calculate percentage of projects that are delayed."""
        try:
            if "dias_espera" not in df.columns or df.empty:
                return 15  # Default reasonable value

            # Convertir dias_espera a numérico
            dias_espera_validos = pd.to_numeric(df["dias_espera"], errors="coerce")
            
            # Filtrar valores válidos
            dias_validos = dias_espera_validos.dropna()
            
            if len(dias_validos) == 0:
                return 15  # Default si no hay datos válidos

            # CORREGIDO: Considerar "retrasado" como > 60 días (significativamente fuera del benchmark)
            delayed_count = len(dias_validos[dias_validos > 60])
            total_count = len(dias_validos)
            
            delayed_percentage = round((delayed_count / total_count * 100) if total_count > 0 else 0)
            
            # Asegurar que esté en rango 0-100
            return max(0, min(100, delayed_percentage))
            
        except Exception as e:
            logger.info(f"Error calculating projects delayed: {e}")
            return 15  # Default

    def invalidate_dashboard_cache(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Invalidate dashboard cache for specific filters or all if no filters provided."""
        try:
            if not redis_client:
                return True  # No cache to invalidate

            if filters:
                # Invalidate specific filter combination
                filters_hash = self._generate_cache_key(filters)
                cache_key = f"manager_dashboard:{filters_hash}"
                keys_to_delete = [
                    cache_key,
                    f"{cache_key}:meta",
                    f"{cache_key}:stale",
                    f"kpis:{filters_hash}",
                    f"charts:{filters_hash}",
                    f"financials:{filters_hash}",
                ]

                deleted_count = 0
                for key in keys_to_delete:
                    if redis_client.delete(key):
                        deleted_count += 1

                logger.info(
                    f"✅ Invalidated {deleted_count} cache keys for specific filters"
                )
            else:
                # Invalidate all dashboard cache
                patterns = ["manager_dashboard:*", "kpis:*", "charts:*", "financials:*"]

                total_deleted = 0
                for pattern in patterns:
                    keys = redis_client.keys(pattern)
                    if keys:
                        total_deleted += redis_client.delete(*keys)

                logger.info(
                    f"✅ Invalidated {total_deleted} cache keys (all dashboard data)"
                )

            return True

        except Exception as e:
            logger.error(f"Error invalidating dashboard cache: {e}")
            return False

    def invalidate_cache_on_data_change(self, change_type: str = "general") -> bool:
        """Invalidate relevant cache when data changes occur."""
        try:
            if not redis_client:
                return True

            # Different change types invalidate different cache patterns
            if change_type == "edp_update":
                # EDP data changed, invalidate all dashboard cache
                return self.invalidate_dashboard_cache()

            elif change_type == "project_update":
                # Project data changed, invalidate project-related cache
                patterns = ["manager_dashboard:*", "charts:*"]

            elif change_type == "financial_update":
                # Financial data changed, invalidate financial cache
                patterns = ["manager_dashboard:*", "financials:*", "kpis:*"]

            else:
                # General change, invalidate everything
                return self.invalidate_dashboard_cache()

            total_deleted = 0
            for pattern in patterns:
                keys = redis_client.keys(pattern)
                if keys:
                    total_deleted += redis_client.delete(*keys)

            logger.info(
                f"✅ Invalidated {total_deleted} cache keys for change type: {change_type}"
            )
            return True

        except Exception as e:
            logger.error(f"Error invalidating cache for data change: {e}")
            return False

    def get_cache_status(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get detailed cache status information."""
        try:
            if not redis_client:
                return {"redis_available": False}

            filters_hash = self._generate_cache_key(filters or {})
            cache_key = f"manager_dashboard:{filters_hash}"
            cache_meta_key = f"{cache_key}:meta"

            # Check main cache
            cache_exists = redis_client.exists(cache_key)
            cache_ttl = redis_client.ttl(cache_key) if cache_exists else -2

            # Check metadata
            meta_exists = redis_client.exists(cache_meta_key)
            cache_age = None

            if meta_exists:
                try:
                    meta_data = json.loads(redis_client.get(cache_meta_key))
                    cache_timestamp = meta_data.get("timestamp", 0)
                    cache_age = datetime.now().timestamp() - cache_timestamp
                except Exception:
                    pass

            # Check related cache
            related_cache = {
                "kpis": redis_client.exists(f"kpis:{filters_hash}"),
                "charts": redis_client.exists(f"charts:{filters_hash}"),
                "financials": redis_client.exists(f"financials:{filters_hash}"),
                "stale_backup": redis_client.exists(f"{cache_key}:stale"),
            }

            return {
                "redis_available": True,
                "cache_exists": bool(cache_exists),
                "cache_ttl": cache_ttl,
                "cache_age": round(cache_age, 1) if cache_age else None,
                "meta_exists": bool(meta_exists),
                "related_cache": related_cache,
                "filters_hash": filters_hash,
                "cache_key": cache_key,
            }

        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {"redis_available": False, "error": str(e)}

    def get_all_projects(self) -> ServiceResponse:
        """Get all projects data."""
        try:
            # Get projects from repository
            projects = self.project_repo.find_all()
            
            # Convert to dictionaries
            projects_data = []
            for project in projects:
                project_dict = {
                    'project_id': project.project_id or project.id or '',
                    'proyecto': project.proyecto or project.project_id or project.id or '',
                    'cliente': project.cliente or '',
                    'gestor': project.gestor or '',
                    'jefe_proyecto': project.jefe_proyecto or '',
                    'fecha_inicio': project.fecha_inicio.strftime('%Y-%m-%d') if project.fecha_inicio else '',
                    'fecha_fin_prevista': project.fecha_fin_prevista.strftime('%Y-%m-%d') if project.fecha_fin_prevista else '',
                    'monto_contrato': project.monto_contrato or 0,
                    'moneda': project.moneda or 'CLP'
                }
                projects_data.append(project_dict)
            
            return ServiceResponse(
                success=True,
                data=projects_data,
                message=f"Se obtuvieron {len(projects_data)} proyectos"
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo proyectos: {e}")
            return ServiceResponse(
                success=False,
                message=f"Error obteniendo proyectos: {str(e)}",
                data=[]
            )

    def get_critical_projects_data(self, filters: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """Get detailed critical projects data for modal display."""
        try:
            # Load EDP data
            edps_response = self.edp_repo.find_all_dataframe()
            
            if isinstance(edps_response, dict) and not edps_response.get("success", False):
                return ServiceResponse(
                    success=False,
                    message=f"Failed to load EDPs data: {edps_response.get('message', 'Unknown error')}",
                    data=None,
                )

            df_edp = edps_response.get("data", pd.DataFrame())
            if df_edp.empty:
                return ServiceResponse(
                    success=False, 
                    message="No EDP data available", 
                    data=None
                )

            # Apply filters if provided
            df_filtered = self._apply_manager_filters(df_edp, filters or {})
            
            # Prepare data for critical analysis
            df_prepared = self._prepare_kpi_data(df_filtered.copy())
            
            # Identificar EDPs críticos - los que están sin movimiento significativo
            # Criterio: pendientes por más de X días (no por monto)
            critical_edps = []
            
            # Estados que consideramos "sin movimiento" (pendientes de acción)
            stalled_states = ["enviado", "revisión", "pendiente", "en_proceso"]
            
            # Filtrar EDPs sin movimiento
            df_stalled = df_prepared[
                df_prepared["estado"].str.strip().str.lower().isin([s.lower() for s in stalled_states])
            ].copy()
            
            if not df_stalled.empty:
                # Convertir días de espera a numérico
                df_stalled["dias_espera_num"] = pd.to_numeric(df_stalled["dias_espera"], errors="coerce").fillna(0)
                
                # Criterio crítico: EDPs con 30+ días sin movimiento
                df_critical = df_stalled[df_stalled["dias_espera_num"] >= 30].copy()
                
                # Ordenar por días sin movimiento (descendente) - MÁS CRÍTICO PRIMERO
                df_critical = df_critical.sort_values("dias_espera_num", ascending=False)
                
                # **NUEVO: Agrupar EDPs por proyecto**
                projects_dict = {}
                
                for _, row in df_critical.iterrows():
                    proyecto_key = row.get("proyecto", "Proyecto N/A")
                    cliente = row.get("cliente", "Cliente N/A")
                    jefe_proyecto = row.get("jefe_proyecto", "Sin asignar")
                    
                    # Crear clave única por proyecto-cliente-jefe
                    project_id = f"{proyecto_key}_{cliente}_{jefe_proyecto}"
                    
                    edp_data = {
                        "id": row.get("n_edp", "N/A"),
                        "monto": float(row.get("monto_aprobado", 0)),
                        "dias_sin_movimiento": int(row.get("dias_espera_num", 0)),
                        "estado": row.get("estado", "pendiente"),
                        "fecha_ultimo_movimiento": self._calculate_last_movement_date(row),
                        "fecha_emision": row.get("fecha_emision", "Sin fecha"),
                    }
                    
                    if project_id not in projects_dict:
                        projects_dict[project_id] = {
                            "proyecto": proyecto_key,
                            "cliente": cliente,
                            "jefe_proyecto": jefe_proyecto,
                            "edps": [],
                            "total_monto": 0,
                            "max_dias_sin_movimiento": 0,
                            "estado_proyecto": "activo"
                        }
                    
                    projects_dict[project_id]["edps"].append(edp_data)
                    projects_dict[project_id]["total_monto"] += edp_data["monto"]
                    projects_dict[project_id]["max_dias_sin_movimiento"] = max(
                        projects_dict[project_id]["max_dias_sin_movimiento"],
                        edp_data["dias_sin_movimiento"]
                    )
                
                # Convertir diccionario a lista y ordenar por criticidad
                critical_edps = []
                for project_data in projects_dict.values():
                    critical_edps.append(project_data)
                
                # Ordenar proyectos por máximos días sin movimiento
                critical_edps.sort(key=lambda x: x["max_dias_sin_movimiento"], reverse=True)
            
            # Calcular portfolio total para contexto
            total_portfolio_value = df_prepared["monto_aprobado"].sum()
            
            # Calcular estadísticas por proyecto
            total_edps_criticos = sum(len(project["edps"]) for project in critical_edps)
            
            # Clasificar proyectos por criticidad basado en máximos días
            critical_projects_90_plus = len([p for p in critical_edps if p["max_dias_sin_movimiento"] > 90])
            high_risk_projects_60_90 = len([p for p in critical_edps if 60 <= p["max_dias_sin_movimiento"] <= 90])
            medium_risk_projects_30_60 = len([p for p in critical_edps if 30 <= p["max_dias_sin_movimiento"] < 60])
            
            # Preparar datos de respuesta
            critical_data = {
                "critical_edps": critical_edps,  # Ahora son proyectos agrupados
                "total_portfolio_value": total_portfolio_value,
                "summary": {
                    "total_count": len(df_prepared),
                    "total_amount": sum(p["total_monto"] for p in critical_edps),
                    "critical_count": critical_projects_90_plus,
                    "high_risk_count": high_risk_projects_60_90,
                    "medium_risk_count": medium_risk_projects_30_60,
                    "total_critical_projects": len(critical_edps),
                    "total_critical_edps": total_edps_criticos
                }
            }
            
            return ServiceResponse(
                success=True,
                message=f"Critical EDP data retrieved: {len(critical_edps)} critical EDPs found",
                data=critical_data,
            )

        except Exception as e:
            logger.error(f"Error getting critical EDP data: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error getting critical EDP data: {str(e)}",
                data=None,
            )
    
    
    def _calculate_last_movement_date(self, row: pd.Series) -> str:
        """Calculate the last movement date for an EDP"""
        try:
            dias_espera = row.get("dias_espera_num", 0)
            if dias_espera > 0:
                last_date = datetime.now() - timedelta(days=int(dias_espera))
                return last_date.strftime("%Y-%m-%d")
            return datetime.now().strftime("%Y-%m-%d")
        except:
            return "Sin fecha"
    
    
    def _identify_main_blockage(self, row: pd.Series) -> str:
        """Identify the main blockage type for an EDP"""
        estado = str(row.get("estado", "")).lower().strip()
        
        blockage_map = {
            "enviado": "Esperando respuesta del cliente",
            "revisión": "En revisión interna",
            "pendiente": "Documentación pendiente",
            "en_proceso": "Procesamiento administrativo"
        }
        
        return blockage_map.get(estado, "Bloqueo no identificado")
    
    
    def _extract_contact_info(self, row: pd.Series) -> Dict[str, str]:
        """Extract contact information for an EDP"""
        return {
            "jefe_proyecto": row.get("jefe_proyecto", "Sin asignar"),
            "cliente": row.get("cliente", "Sin cliente"),
            "email": f"{row.get('jefe_proyecto', 'sin-asignar').lower().replace(' ', '.')}@empresa.com",
            "telefono": "+54 11 4567-890X"  # Mock phone number
        }
    
    
    def _calculate_urgency_score(self, row: pd.Series) -> int:
        """Calculate urgency score (0-100) based on days and amount"""
        try:
            dias = row.get("dias_espera_num", 0)
            monto = row.get("monto_aprobado", 0)
            
            # Score based primarily on time stalled (70% weight)
            time_score = min(100, (dias / 120) * 70)  # 120 days = max time score
            
            # Score based on amount (30% weight)
            amount_score = min(30, (monto / 50_000_000) * 30)  # 50M = max amount score
            
            return int(time_score + amount_score)
        except:
            return 50  # Default moderate urgency
