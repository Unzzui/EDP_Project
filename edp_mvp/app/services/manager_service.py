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

    def get_manager_dashboard_data(
        self, filters: Dict[str, Any] = None
    ) -> ServiceResponse:
        """Get comprehensive dashboard data for managers."""
        try:
            cache_key = f"manager_dashboard:{json.dumps(filters, sort_keys=True)}"
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return ServiceResponse(success=True, data=data)

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

            # Calculate executive KPIs
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
                        "last_updated": datetime.now(),
                    },
            }
            if redis_client:
                redis_client.setex(cache_key, 300, json.dumps(result_data))
            return ServiceResponse(success=True, data=result_data)

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error loading manager dashboard: {str(e)}",
                data=None,
            )

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
        """Calculate executive-level KPIs that match template expectations."""
        try:
            if df_full.empty:
                logger.info("Warning: DataFrame is empty, returning default KPIs")
                return self.get_empty_kpis()

            # Prepare data
            df_full = self._prepare_kpi_data(df_full)

            # Calculate different KPI categories
            financial_kpis = self._calculate_financial_kpis(df_full)
            operational_kpis = self._calculate_operational_kpis(df_full)
            profitability_kpis = self._calculate_profitability_kpis(df_full)
            aging_kpis = self._calculate_aging_kpis(df_full)
            efficiency_kpis = self._calculate_efficiency_kpis(df_full)

            # Combine all KPIs
            kpis = {
                **financial_kpis,
                **operational_kpis,
                **profitability_kpis,
                **aging_kpis,
                **efficiency_kpis,
            }

            return kpis

        except Exception as e:
            logger.info(f"Error in _calculate_executive_kpis: {str(e)}")
            import traceback

            traceback.print_exc()
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
        ]

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
        """Generate system alerts and warnings."""
        alerts = []

        # Critical EDPs alert
        critical_count = len(df[df.get("Crítico", False) == True])
        if critical_count > 0:
            alerts.append(
                {
                    "type": "warning",
                    "title": "EDPs Críticos",
                    "message": f"{critical_count} EDPs marcados como críticos requieren atención inmediata",
                    "count": critical_count,
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
                        "type": "error",
                        "title": "EDPs Atrasados",
                        "message": f"{old_pending} EDPs llevan más de 30 días en proceso",
                        "count": old_pending,
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
                    "type": "info",
                    "title": "EDPs Alto Valor Pendientes",
                    "message": f"{FormatUtils.format_currency(total_amount)} en EDPs de alto valor pendientes",
                    "count": len(high_value_pending),
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
        """Calculate overall efficiency score (0-100)."""
        factors = []

        # Approval rate factor
        approved_count = len(df[df["estado"].isin(["pagado", "validado"])])
        total_count = len(df)
        if total_count > 0:
            approval_rate = approved_count / total_count
            factors.append(approval_rate * 30)  # 30% weight

        # Speed factor (inverse of average processing time)
        if "dias_espera" in df.columns:
            avg_days = df["dias_espera"].mean()
            if avg_days and avg_days > 0:
                speed_score = max(0, (60 - avg_days) / 60)  # 60 days as benchmark
                factors.append(speed_score * 25)  # 25% weight

        # Critical EDPs factor (penalty for high critical percentage)
        critical_count = len(df[df.get("Crítico", False) == True])
        if total_count > 0:
            critical_rate = critical_count / total_count
            critical_score = max(0, 1 - critical_rate * 2)  # Penalty for critical EDPs
            factors.append(critical_score * 25)  # 25% weight

        # Financial efficiency (approval vs proposed amounts)
        if "monto_propuesto" in df.columns and "monto_aprobado" in df.columns:
            total_proposed = df["monto_propuesto"].sum()
            total_approved = df["monto_aprobado"].sum()
            if total_proposed > 0:
                financial_efficiency = min(1, total_approved / total_proposed)
                factors.append(financial_efficiency * 20)  # 20% weight

        # Calculate weighted average
        if factors:
            return round(sum(factors), 1)
        return 0.0

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
        """Calculate Days Sales Outstanding."""
        if "dias_espera" not in df.columns:
            return 0.0

        # Filter for paid EDPs
        paid_edps = df[df["estado"] == "pagado"]
        if paid_edps.empty:
            return 0.0

        # Calculate weighted average DSO
        total_amount = paid_edps["monto_aprobado"].sum()
        if total_amount > 0:
            weighted_dso = (
                paid_edps["dias_espera"] * paid_edps["monto_aprobado"]
            ).sum() / total_amount
            return weighted_dso

        return paid_edps["dias_espera"].mean()

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
        """Get empty KPI structure for error cases that matches template expectations."""
        return {
            # Financial KPIs that match template
            "ingresos_totales": 0,
            "monto_pendiente": 0,
            "meta_ingresos": 0,
            "run_rate_anual": 0,
            "vs_meta_ingresos": 0,
            "pct_meta_ingresos": 0,
            "crecimiento_ingresos": 0,
            "tendencia_pendiente": 0,
            "historial_6_meses": [0, 0, 0, 0, 0, 0],
            # DSO and payment metrics
            "dso": 45,  # Default reasonable DSO
            "dso_cliente_principal": 30,
            "pct_ingresos_principal": 25,
            "riesgo_pago_principal": 15,
            "tendencia_pago_principal": "estable",
            # Rentabilidad KPIs - MISSING ONES CAUSING ERRORS
            "rentabilidad_general": 0,
            "tendencia_rentabilidad": 0,  # This was causing the TypeError
            "posicion_vs_benchmark": 0,
            "vs_meta_rentabilidad": 0,
            "meta_rentabilidad": 35.0,  # Default target
            "pct_meta_rentabilidad": 0,  # Percentage of target achieved
            "mejora_eficiencia": 0,
            "eficiencia_global": 0,
            # Additional financial metrics
            "margen_bruto_absoluto": 0,
            "costos_totales": 0,
            # Additional KPIs for aging buckets
            "pct_30d": 25,
            "pct_60d": 25,
            "pct_90d": 25,
            "pct_mas90d": 25,
            # Project timing KPIs - MISSING ONES CAUSING CURRENT ERROR
            "proyectos_on_time": 75,  # Default 75% on time
            "proyectos_retrasados": 15,  # Default 15% delayed
            # Top drivers
            "top_driver_1_name": "Sin datos",
            "top_driver_1_value": 0,
            "top_driver_2_name": "Sin datos",
            "top_driver_2_value": 0,
            # Legacy fields for compatibility
            "total_edps": 0,
            "total_approved": 0,
            "total_pending": 0,
            "approval_rate": 0,
            "critical_edps": 0,
            "efficiency_score": 0,
        }

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
            datos_relacionados = datos_relacionados.get("edps", [])
            datos_relacionados = pd.DataFrame(datos_relacionados)

            # Preparar datos
            datos_relacionados["monto_aprobado"] = pd.to_numeric(
                datos_relacionados["monto_aprobado"], errors="coerce"
            ).fillna(0)
            datos_relacionados["dias_espera"] = pd.to_numeric(
                datos_relacionados["dias_espera"], errors="coerce"
            ).fillna(0)

            # Filtrar pendientes
            df_pendientes = datos_relacionados[
                ~datos_relacionados["estado"].str.strip().isin(["pagado", "validado"])
            ]

            if df_pendientes.empty:
                return alertas

            # Alerta 1: EDPs críticos (>30 días)
            edps_criticos = df_pendientes[df_pendientes["dias_espera"] > 30]
            if len(edps_criticos) > 0:
                monto_critico = edps_criticos["monto_aprobado"].sum() / 1_000_000
                alertas.append(
                    {
                        "tipo": "critico",
                        "titulo": f"{len(edps_criticos)} EDPs críticos",
                        "mensaje": f"${monto_critico:.1f}M en EDPs con más de 30 días de espera",
                        "icono": "exclamation-triangle",
                    }
                )

            # Alerta 2: Concentración en un cliente
            if "cliente" in df_pendientes.columns:
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
                                "tipo": "warning",
                                "titulo": "Alta concentración",
                                "mensaje": f"{concentracion:.1f}% del backlog en {cliente_principal}",
                                "icono": "chart-pie",
                            }
                        )

            # Alerta 3: Montos pendientes altos
            monto_total_pendiente = df_pendientes["monto_aprobado"].sum() / 1_000_000
            if monto_total_pendiente > 1000:  # Más de 1000M
                alertas.append(
                    {
                        "tipo": "info",
                        "titulo": "Backlog alto",
                        "mensaje": f"${monto_total_pendiente:.1f}M en EDPs pendientes",
                        "icono": "currency-dollar",
                    }
                )

            return alertas[:10]  # Máximo 5 alertas

        except Exception as e:
            logger.info(f"Error en obtener_alertas_criticas: {e}")
            return []

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
                    group[group["estado"].isin(["pagado", "validado"])]
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
                df[df["estado"].isin(["pagado", "validado"])]["monto_aprobado"].sum()
                if "monto_aprobado" in df.columns
                else 0
            )
            pending_amount = (
                df[df["estado"].isin(["enviado", "revisión", "pendiente"])][
                    "monto_propuesto"
                ].sum()
                if "monto_propuesto" in df.columns
                else 0
            )

            # Calculate target and performance metrics
            meta_ingresos = (
                total_proposed * 1.1
            )  # Assume target is 10% higher than proposed
            vs_meta_ingresos = (
                ((total_paid - meta_ingresos) / meta_ingresos * 100)
                if meta_ingresos > 0
                else 0
            )
            pct_meta_ingresos = (
                (total_paid / meta_ingresos * 100) if meta_ingresos > 0 else 0
            )

            # Growth calculations (simulate monthly growth)
            crecimiento_ingresos = 5.2  # Mock positive growth
            tendencia_pendiente = -2.1  # Mock declining pending trend

            # Format values to match template expectations (in millions)
            ingresos_totales = round(total_paid / 1_000_000, 1)
            monto_pendiente = round(pending_amount / 1_000_000, 1)
            meta_ingresos_m = round(meta_ingresos / 1_000_000, 1)
            run_rate_anual = round(ingresos_totales * 12, 1)

            # Generate sample historical data for sparkline
            historial_6_meses = [
                round(ingresos_totales * 0.8, 1),
                round(ingresos_totales * 0.9, 1),
                round(ingresos_totales * 0.85, 1),
                round(ingresos_totales * 1.1, 1),
                round(ingresos_totales * 1.05, 1),
                ingresos_totales,
            ]

            # Top drivers (mock data for now)
            top_driver_1_name = "Proyecto Principal"
            top_driver_1_value = round(ingresos_totales * 0.3, 1)
            top_driver_2_name = "Cliente Premium"
            top_driver_2_value = round(ingresos_totales * 0.25, 1)

            return {
                "ingresos_totales": ingresos_totales,
                "monto_pendiente": monto_pendiente,
                "meta_ingresos": meta_ingresos_m,
                "run_rate_anual": run_rate_anual,
                "vs_meta_ingresos": round(vs_meta_ingresos, 1),
                "pct_meta_ingresos": min(round(pct_meta_ingresos, 1), 100),
                "crecimiento_ingresos": crecimiento_ingresos,
                "tendencia_pendiente": tendencia_pendiente,
                "historial_6_meses": historial_6_meses,
                "top_driver_1_name": top_driver_1_name,
                "top_driver_1_value": top_driver_1_value,
                "top_driver_2_name": top_driver_2_name,
                "top_driver_2_value": top_driver_2_value,
            }

        except Exception as e:
            logger.info(f"Error calculating financial KPIs: {e}")
            return {}

    def _calculate_operational_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate operational KPIs."""
        try:
            # Basic counts
            total_edps = len(df)
            total_approved = len(df[df["estado"].isin(["pagado", "validado"])])
            total_pending = len(
                df[df["estado"].isin(["enviado", "revisión", "pendiente"])]
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
        """Calculate aging bucket KPIs."""
        try:
            if "dias_espera" not in df.columns or df.empty:
                return {"pct_30d": 25, "pct_60d": 25, "pct_90d": 25, "pct_mas90d": 25}

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
                "pct_30d": pct_30d,
                "pct_60d": pct_60d,
                "pct_90d": pct_90d,
                "pct_mas90d": pct_mas90d,
            }

        except Exception as e:
            logger.info(f"Error calculating aging KPIs: {e}")
            return {}

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

            # DSO for cycle time
            try:
                dso = self._calculate_dso(df)
            except Exception:
                dso = 45.0

            # Cycle time metrics
            tiempo_medio_ciclo = dso
            meta_tiempo_ciclo = 30
            benchmark_tiempo_ciclo = 35

            eficiencia_actual = round(pct_avance * 0.8, 1)  # Simplified calculation
            eficiencia_anterior = max(0, eficiencia_actual - 5.3)
            mejora_eficiencia = round(eficiencia_actual - eficiencia_anterior, 1)

            tiempo_medio_ciclo_pct = (
                round((meta_tiempo_ciclo / tiempo_medio_ciclo * 100), 1)
                if tiempo_medio_ciclo > 0
                else 0
            )

            # Tiempos por etapa
            tiempo_emision = round(tiempo_medio_ciclo * 0.18, 1)
            tiempo_gestion = round(tiempo_medio_ciclo * 0.27, 1)
            tiempo_conformidad = round(tiempo_medio_ciclo * 0.33, 1)
            tiempo_pago = round(tiempo_medio_ciclo * 0.22, 1)

            etapa_emision_pct = (
                int(tiempo_emision / tiempo_medio_ciclo * 100)
                if tiempo_medio_ciclo > 0
                else 18
            )
            etapa_gestion_pct = (
                int(tiempo_gestion / tiempo_medio_ciclo * 100)
                if tiempo_medio_ciclo > 0
                else 27
            )
            etapa_conformidad_pct = (
                int(tiempo_conformidad / tiempo_medio_ciclo * 100)
                if tiempo_medio_ciclo > 0
                else 33
            )
            etapa_pago_pct = (
                int(tiempo_pago / tiempo_medio_ciclo * 100)
                if tiempo_medio_ciclo > 0
                else 22
            )

            # Oportunidad de mejora
            if tiempo_conformidad > 15:
                oportunidad_mejora = f"Reducir tiempo de conformidad con cliente ({tiempo_conformidad:.1f} días vs. benchmark 7 días)"
            elif tiempo_gestion > 12:
                oportunidad_mejora = f"Optimizar tiempo de gestión interna ({tiempo_gestion:.1f} días vs. benchmark 8 días)"
            else:
                oportunidad_mejora = "Mantener tiempos actuales dentro del benchmark"

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
            }

        except Exception as e:
            logger.info(f"Error calculating efficiency KPIs: {e}")
            return {}

    def _calculate_projects_on_time(self, df: pd.DataFrame) -> int:
        """Calculate percentage of projects delivered on time."""
        # Simplified calculation - in reality would need proper date analysis
        if "dias_espera" in df.columns:
            on_time = (df["dias_espera"] <= 30).sum()
            return round((on_time / len(df) * 100) if len(df) > 0 else 0)
        return 75  # Default

    def _calculate_projects_delayed(self, df: pd.DataFrame) -> int:
        """Calculate percentage of projects that are delayed."""
        if "dias_espera" in df.columns:
            delayed = (df["dias_espera"] > 45).sum()
            return round((delayed / len(df) * 100) if len(df) > 0 else 0)
        return 15  # Default
