"""
Dashboard Service for managing dashboard data and visualizations.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import re
import logging

from . import BaseService, ServiceResponse, ValidationError
from ..models import EDP, KPI
from ..repositories.edp_repository import EDPRepository
from ..repositories.project_repository import ProjectRepository
from ..repositories.log_repository import LogRepository
from ..services.cost_service import CostService
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils
from ..utils.validation_utils import ValidationUtils

logger = logging.getLogger(__name__)

# Constants migrated from dashboard/controller.py
METAS_ENCARGADOS = {
    "Diego Bravo": 375_000_000,
    "Carolina López": 375_000_000,
    "Pedro Rojas": 375_000_000,
    "Ana Pérez": 375_000_000,
}
META_GLOBAL = 1_500_000_000


class ControllerService(BaseService):
    """Service for managing dashboard data and analytics."""

    def __init__(self):
        super().__init__()
        self.log_repository = LogRepository()
        self.project_repo = ProjectRepository()
        self.cost_service = CostService()
        self.edp_repo = EDPRepository()

    def _enriquecer_df_con_estado_detallado(
        self, df_edp: pd.DataFrame, df_log: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Enriquece el DataFrame de EDPs con el estado_detallado más reciente de cada EDP
        extrayendo esta información del log de cambios.
        """
        df_enriquecido = df_edp.copy()
        if "estado_detallado" not in df_enriquecido.columns:
            df_enriquecido["estado_detallado"] = ""

        if df_log.empty:
            logger.info(
                "Log de cambios vacío, no se puede enriquecer con estado_detallado."
            )
            return df_enriquecido

        cambios_estado = df_log[df_log["campo"] == "estado_detallado"].copy()
        if cambios_estado.empty:
            logger.info("No se encontraron registros de 'estado_detallado' en el log")
            # return df_enriquecido # Keep going to check motivos_rechazo

        cambios_estado["fecha_hora"] = pd.to_datetime(
            cambios_estado["fecha_hora"], errors="coerce"
        )

        for num_edp in df_enriquecido["n_edp"].unique():
            cambios_edp = cambios_estado[cambios_estado["n_edp"] == str(num_edp)]
            if not cambios_edp.empty:
                ultimo_cambio = cambios_edp.sort_values(
                    "fecha_hora", ascending=False
                ).iloc[0]
                ultimo_estado = ultimo_cambio["despues"]
                df_enriquecido.loc[
                    df_enriquecido["n_edp"] == num_edp, "estado_detallado"
                ] = ultimo_estado

        motivos_rechazo = df_log[df_log["campo"] == "motivo_no_aprobado"].copy()
        if not motivos_rechazo.empty:
            for num_edp in motivos_rechazo["n_edp"].unique():
                mask = (df_enriquecido["n_edp"] == num_edp) & (
                    df_enriquecido["estado_detallado"] == ""
                )
                if mask.any():
                    df_enriquecido.loc[mask, "estado_detallado"] = (
                        "re-trabajo solicitado"
                    )

        return df_enriquecido

    def _obtener_meses_ordenados(self, df: pd.DataFrame) -> list:
        """
        Obtiene los meses únicos del DataFrame y los ordena cronológicamente.
        """
        try:
            if "mes" not in df.columns:
                logger.info("WARNING: Columna 'mes' no encontrada en el DataFrame")
                return []

            meses = df["mes"].dropna().unique()
            if len(meses) == 0:
                return []

            def mes_a_numero(mes_str):
                try:
                    if "-" in mes_str:  # YYYY-MM
                        year, month = mes_str.split("-")
                        return int(year) * 100 + int(month)

                    partes = mes_str.split()  # "Enero 2023"
                    if len(partes) >= 2 and partes[-1].isdigit():
                        mes_nombre = " ".join(partes[:-1]).lower()
                        año = int(partes[-1])
                        mapeo_meses = {
                            "enero": 1,
                            "febrero": 2,
                            "marzo": 3,
                            "abril": 4,
                            "mayo": 5,
                            "junio": 6,
                            "julio": 7,
                            "agosto": 8,
                            "septiembre": 9,
                            "octubre": 10,
                            "noviembre": 11,
                            "diciembre": 12,
                        }
                        mes_num = mapeo_meses.get(mes_nombre, 0)
                        return año * 100 + mes_num
                    else:  # Solo nombre del mes
                        mes_nombre = mes_str.lower()
                        mapeo_meses = {
                            "enero": 1,
                            "febrero": 2,
                            "marzo": 3,
                            "abril": 4,
                            "mayo": 5,
                            "junio": 6,
                            "julio": 7,
                            "agosto": 8,
                            "septiembre": 9,
                            "octubre": 10,
                            "noviembre": 11,
                            "diciembre": 12,
                        }
                        return mapeo_meses.get(mes_nombre, 0)
                except Exception as e:
                    logger.info(f"Error procesando mes '{mes_str}': {str(e)}")
                    return 0

            return sorted(meses, key=mes_a_numero)
        except Exception as e:
            import traceback

            logger.info(f"Error en _obtener_meses_ordenados: {str(e)}")
            logger.info(traceback.format_exc())
            return []

    def _clean_nat_values(self, data: Any) -> Any:
        """
        Limpia valores NaT (Not a Time) de pandas convirtiéndolos en None
        para que puedan ser serializados a JSON.
        Funciona tanto con diccionarios como con listas de diccionarios.
        """
        if isinstance(data, list):
            return [self._clean_nat_values(item) for item in data]
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if pd.isna(value) or str(value) == "NaT":
                result[key] = None
            elif isinstance(value, dict):
                result[key] = self._clean_nat_values(value)
            elif isinstance(value, list):
                result[key] = [
                    self._clean_nat_values(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def _calcular_dias_espera(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula correctamente los días de espera según las reglas de negocio"""
        now = datetime.now()
        df_calculado = df.copy()
        df_calculado["dias_espera"] = None  # Initialize with a default

        for idx, row in df_calculado.iterrows():
            if pd.notna(row.get("fecha_envio_cliente")):
                fecha_envio = row["fecha_envio_cliente"]
                if row.get("conformidad_enviada") == "Sí" and pd.notna(
                    row.get("fecha_conformidad")
                ):
                    df_calculado.at[idx, "dias_espera"] = (
                        row["fecha_conformidad"] - fecha_envio
                    ).days
                else:
                    df_calculado.at[idx, "dias_espera"] = (now - fecha_envio).days
        return df_calculado

    def _calcular_dias_habiles(
        self, fecha_inicio: Any, fecha_fin: Any
    ) -> float:  # Changed return type hint
        """
        Calcula días hábiles entre dos fechas, sin incluir la fecha de inicio.
        Returns np.nan if dates are invalid.
        """
        if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
            return np.nan  # For calculations
        try:
            # Ensure they are datetime objects
            f_inicio = pd.to_datetime(fecha_inicio, errors="coerce")
            f_fin = pd.to_datetime(fecha_fin, errors="coerce")

            if pd.isna(f_inicio) or pd.isna(f_fin):  # if conversion failed
                return np.nan

            if f_fin < f_inicio:  # Ensure correct order for bdate_range
                return 0.0  # No business days if end is before start

            # pd.bdate_range is inclusive of start and end if they are business days
            # The original logic was max(len(dias) - 1, 0)
            # If fecha_inicio and fecha_fin are the same, len(dias) could be 1 (if a biz day) or 0.
            # (Timestamp('2023-01-02'), Timestamp('2023-01-02')) -> len(bdate_range) = 1. Result 0. Correct.
            # (Timestamp('2023-01-02'), Timestamp('2023-01-03')) -> len(bdate_range) = 2. Result 1. Correct.
            dias = pd.bdate_range(start=f_inicio, end=f_fin)
            return float(max(len(dias) - 1, 0))
        except Exception:
            return np.nan

    def _calcular_dso_para_dataset(self, df_datos: pd.DataFrame) -> float:
        """
        Calcula el DSO (Days Sales Outstanding) usando la columna precalculada 'dias_espera',
        ponderado por el 'monto_aprobado'.
        """
        if df_datos.empty:
            return 0

        required_cols = ["dias_espera", "monto_aprobado"]
        for col in required_cols:
            if col not in df_datos.columns:
                logger.info(f"WARNING: Columna '{col}' no encontrada.")
                return 0

        # Limpieza
        df_datos["monto_aprobado"] = pd.to_numeric(
            df_datos["monto_aprobado"], errors="coerce"
        ).fillna(0)
        df_datos["dias_espera"] = pd.to_numeric(
            df_datos["dias_espera"], errors="coerce"
        )

        # Filtrado de valores válidos
        df_valid = df_datos[
            (~df_datos["dias_espera"].isna())
            & (df_datos["dias_espera"] >= 0)
            & (df_datos["monto_aprobado"] > 0)
        ]

        if df_valid.empty:
            return 0

        # Cálculo del DSO
        dso = np.average(df_valid["dias_espera"], weights=df_valid["monto_aprobado"])
        return round(dso, 1)

    def _calcular_dso(
        self,
        df_datos: pd.DataFrame,
        mes_anterior_str: Optional[str] = None,
        df_mes_anterior: Optional[pd.DataFrame] = None,
    ) -> Tuple[float, float, list]:
        """
        Calcula el DSO (Days Sales Outstanding) y metrics relacionadas.
        df_datos: DataFrame con todos los datos.
        mes_anterior_str: String del mes anterior (e.g., "2023-01")
        df_mes_anterior: DataFrame filtrado solo con datos del mes anterior.
        """
        dso_global = self._calcular_dso_para_dataset(
            df_datos.copy()
        )  # Use copy to avoid side effects
        dso_var = 0

        # DSO Variation Calculation (Placeholder - original logic was complex and potentially buggy)
        # The original logic for dso_var was quite involved and seemed to recalculate DSO for a previous month.
        # For now, we'll set dso_var to 0. A more robust dso_var calculation would require
        # storing historical DSO values or ensuring the df_mes_anterior is correctly prepared.
        # If df_mes_anterior is provided and valid, we could calculate DSO for it:
        if df_mes_anterior is not None and not df_mes_anterior.empty:
            dso_anterior = self._calcular_dso_para_dataset(df_mes_anterior.copy())
            if (
                dso_anterior > 0 and dso_global > 0
            ):  # Avoid division by zero or meaningless variation
                dso_var = round(((dso_global - dso_anterior) / dso_anterior) * 100, 1)
            elif dso_global > 0 and dso_anterior == 0:
                dso_var = 100.0  # Or some indicator of significant change from zero
            # else dso_var remains 0 if current or previous DSO is zero

        top_proyectos = []
        # Ensure 'fecha_emision' exists for 'dias_pendiente' calculation
        if "fecha_emision" not in df_datos.columns:
            logger.info(
                "WARNING: 'fecha_emision' no encontrada para calcular top proyectos pendientes en DSO."
            )
            return round(dso_global, 1), round(dso_var, 1), top_proyectos

        df_datos["fecha_emision"] = pd.to_datetime(
            df_datos["fecha_emision"], errors="coerce"
        )
        df_pendientes = df_datos[
            df_datos["estado"].isin(["enviado", "pendiente", "revisión"])
        ].copy()

        if not df_pendientes.empty:
            # Calculate 'dias_pendiente' safely
            df_pendientes["dias_pendiente"] = (
                pd.Timestamp.now().normalize() - df_pendientes["fecha_emision"]
            ).dt.days

            # Ensure 'monto_aprobado' is numeric for sorting and display
            df_pendientes["monto_aprobado"] = pd.to_numeric(
                df_pendientes["monto_aprobado"], errors="coerce"
            ).fillna(0)

            top_3 = df_pendientes.sort_values("dias_pendiente", ascending=False).head(3)

            top_proyectos = [
                {
                    "id": row.get("n_edp", ""),
                    "nombre": row.get("proyecto", "Sin nombre"),
                    "dias": (
                        int(row["dias_pendiente"])
                        if pd.notna(row["dias_pendiente"])
                        else 0
                    ),  # Ensure dias is int
                    "monto": row.get("monto_aprobado", 0),  # Already ensured numeric
                    "jefe_proyecto": row.get("jefe_proyecto", ""),
                }
                for _, row in top_3.iterrows()
                if pd.notna(
                    row.get("dias_pendiente")
                )  # Ensure 'dias_pendiente' is not NaN
            ]
        return round(dso_global, 1), round(dso_var, 1), top_proyectos

    def _calcular_variaciones_mensuales(
        self,
        df_full: pd.DataFrame,
        mes_actual_param: Optional[str],
        meses_disponibles: list,
        total_pagado_global: float,
    ) -> Dict[str, float]:
        """
        Calcula las variaciones de métricas respecto al mes anterior.
        Uses module-level META_GLOBAL.
        """
        variaciones = {
            "meta_var_porcentaje": 0.0,  # Original was 0, ensure float for consistency
            "pagado_var_porcentaje": 0.0,
            "pendiente_var_porcentaje": 0.0,
            "avance_var_porcentaje": 0.0,
        }

        if not meses_disponibles:  # Handle empty meses_disponibles
            return variaciones

        # Ensure 'monto_aprobado' is numeric
        df_full["monto_aprobado"] = pd.to_numeric(
            df_full["monto_aprobado"], errors="coerce"
        ).fillna(0)

        mes_actual = (
            mes_actual_param
            if mes_actual_param
            else (max(meses_disponibles) if meses_disponibles else None)
        )
        mes_anterior_str = None

        if mes_actual and len(meses_disponibles) > 1:
            try:
                # Ensure meses_disponibles contains strings for index()
                meses_disponibles_str = [str(m) for m in meses_disponibles]
                idx_mes_actual = meses_disponibles_str.index(str(mes_actual))
                mes_anterior_str = (
                    meses_disponibles_str[idx_mes_actual - 1]
                    if idx_mes_actual > 0
                    else None
                )
            except (
                ValueError
            ):  # mes_actual might not be in meses_disponibles if it's a future/invalid month
                pass

        if mes_anterior_str:
            df_mes_anterior = df_full[df_full["mes"] == mes_anterior_str]

            meta_mes_anterior = META_GLOBAL
            pagado_mes_anterior = df_mes_anterior[
                df_mes_anterior["estado"] == "pagado"
            ]["monto_aprobado"].sum()
            avance_mes_anterior = (
                round(pagado_mes_anterior / meta_mes_anterior * 100, 1)
                if meta_mes_anterior > 0
                else 0.0
            )

            if pagado_mes_anterior != 0:
                variaciones["pagado_var_porcentaje"] = round(
                    (
                        (total_pagado_global - pagado_mes_anterior)
                        / pagado_mes_anterior
                        * 100
                    ),
                    1,
                )
            elif total_pagado_global > 0:  # Pagado anterior era 0, actual es > 0
                variaciones["pagado_var_porcentaje"] = (
                    100.0  # Or some large number to indicate change from zero
                )

            pendiente_actual = META_GLOBAL - total_pagado_global
            pendiente_anterior = meta_mes_anterior - pagado_mes_anterior
            if pendiente_anterior != 0:
                variaciones["pendiente_var_porcentaje"] = round(
                    (
                        (pendiente_actual - pendiente_anterior)
                        / pendiente_anterior
                        * 100
                    ),
                    1,
                )
            elif pendiente_actual != 0:  # Pendiente anterior era 0, actual no es 0
                variaciones["pendiente_var_porcentaje"] = 100.0  # Or some indicator

            avance_global_actual = (
                round(total_pagado_global / META_GLOBAL * 100, 1)
                if META_GLOBAL > 0
                else 0.0
            )
            variaciones["avance_var_porcentaje"] = round(
                avance_global_actual - avance_mes_anterior, 1
            )

        return variaciones

    def get_controller_dashboard_data(
        self, filters: Dict[str, Any] = None
    ) -> ServiceResponse:
        """Get comprehensive dashboard overview data."""
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

            return ServiceResponse(
                success=True,
                data={
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
                },
            )

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
        dso = self._calculate_dso_service_internal(df_full)  # Changed to avoid conflict

        return {
            "total_revenue": FormatUtils.format_currency(total_revenue),
            "pending_revenue": FormatUtils.format_currency(pending_revenue),
            "monthly_data": monthly_data,
            "dso": round(dso, 1),
            "cost_of_capital": FormatUtils.format_percentage(cost_of_capital * 100),
            "working_capital_impact": self._calculate_working_capital_impact(df_full),
        }

    # Placeholder for internal DSO calculation if needed by other service methods
    def _calculate_dso_service_internal(self, df: pd.DataFrame) -> float:
        # This is a simplified placeholder.
        # The main _calculate_dso and _calcular_dso_para_dataset are now the ones migrated
        # from the original controller. If other parts of this service need a different DSO,
        # this method can be fleshed out. For now, returning a default.
        if df.empty:
            return 0.0
        # A very basic DSO, not weighted, just for placeholder
        # Replace with a more accurate calculation if used by other service parts.
        # For the main dashboard, the migrated _calculate_dso will be used.
        # For now, let's call the more accurate one if columns are present
        if (
            "fecha_emision" in df.columns
            and "monto_aprobado" in df.columns
            and (
                "fecha_estimada_pago" in df.columns or "fecha_conformidad" in df.columns
            )
        ):
            return self._calcular_dso_para_dataset(df.copy())
        return 30.0  # Default placeholder

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

            # 2. Status Distribution (estado Proyectos)
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
            else:  # Fallback if 'fecha_estimada_pago' is missing
                if "fecha_emision" in df_pendientes.columns:
                    df_pendientes["fecha_emision"] = pd.to_datetime(
                        df_pendientes["fecha_emision"], errors="coerce"
                    )
                    df_pendientes["Fecha_Estimada_Calculada"] = df_pendientes[
                        "fecha_emision"
                    ] + pd.Timedelta(days=45)
                    fecha_pago_col = "Fecha_Estimada_Calculada"
                else:  # Not enough data to forecast
                    return {"labels": ["30 días", "60 días", "90 días"], "datasets": []}

            # Ensure 'monto_aprobado' is numeric
            df_pendientes["monto_aprobado"] = pd.to_numeric(
                df_pendientes["monto_aprobado"], errors="coerce"
            ).fillna(0)

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
            # Ensure 'estado' column exists and is not empty
            if "estado" not in df.columns or df.empty:
                return {"labels": [], "datasets": []}
            status_counts = df["estado"].value_counts()

            # Map status to Spanish labels and colors
            status_mapping = {
                "pagado": {"label": "Pagado", "color": "rgba(16, 185, 129, 0.8)"},
                "validado": {"label": "Validado", "color": "rgba(59, 130, 246, 0.8)"},
                "enviado": {"label": "Enviado", "color": "rgba(249, 115, 22, 0.8)"},
                "revision": {
                    "label": "Revisión",
                    "color": "rgba(245, 158, 11, 0.8)",
                },  # Original was 'revisión'
                "revisión": {"label": "Revisión", "color": "rgba(245, 158, 11, 0.8)"},
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
                status_key = str(status).lower().strip()  # Normalize key
                mapping = status_mapping.get(
                    status_key,
                    {"label": str(status).title(), "color": "rgba(156, 163, 175, 0.8)"},
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
            # Ensure 'cliente' and 'monto_aprobado' columns exist
            if (
                "cliente" not in df.columns
                or "monto_aprobado" not in df.columns
                or df.empty
            ):
                return {"labels": [], "datasets": []}

            # Ensure 'monto_aprobado' is numeric
            df["monto_aprobado"] = pd.to_numeric(
                df["monto_aprobado"], errors="coerce"
            ).fillna(0)

            # Group by client and calculate performance metrics
            client_performance = (
                df.groupby("cliente")["monto_aprobado"].sum() / 1_000_000
            )  # In millions

            if client_performance.empty:
                return {"labels": [], "datasets": []}

            # Sort by amount and take top 10
            sorted_clients = client_performance.sort_values(ascending=False)
            top_10_clientes = sorted_clients.head(10)

            # Calculate percentage of total for the top 10
            total_top_10 = top_10_clientes.sum()  # Sum of top 10 amounts
            # If total_top_10 is zero, pct_acum will be NaN. Handle this.
            if total_top_10 == 0:
                pct_acum = pd.Series(
                    [0.0] * len(top_10_clientes), index=top_10_clientes.index
                )
            else:
                pct_acum = (top_10_clientes.cumsum() / total_top_10 * 100).round(1)

            return {
                "labels": top_10_clientes.index.tolist(),
                "datasets": [
                    {
                        "type": "bar",
                        "label": "Monto (M$)",
                        "data": top_10_clientes.round(
                            1
                        ).tolist(),  # Use top_10_clientes for data
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

            df_copia = df.copy()

            if (
                "fecha_emision" not in df_copia.columns
                or "monto_aprobado" not in df_copia.columns
            ):
                return self._create_mock_monthly_trend()

            df_copia["fecha_emision"] = pd.to_datetime(
                df_copia["fecha_emision"], errors="coerce"
            )
            df_copia["monto_aprobado"] = pd.to_numeric(
                df_copia["monto_aprobado"], errors="coerce"
            ).fillna(0)
            df_copia["mes"] = df_copia["fecha_emision"].dt.strftime("%Y-%m")

            df_costs = pd.DataFrame()
            try:
                cost_response = self.cost_service.cost_repository.find_all_dataframe()
                if cost_response.get("success", False):
                    df_costs = cost_response.get("data", pd.DataFrame())
                    if not df_costs.empty:
                        if "importe_neto" in df_costs.columns:
                            df_costs["importe_neto"] = pd.to_numeric(
                                df_costs["importe_neto"], errors="coerce"
                            ).fillna(0)

                        date_col_options = [
                            "fecha_costo",
                            "created_at",
                            "fecha_emision",
                        ]  # ordered preference
                        cost_date_col_found = False
                        for col_name in date_col_options:
                            if col_name in df_costs.columns:
                                df_costs[col_name] = pd.to_datetime(
                                    df_costs[col_name], errors="coerce"
                                )
                                df_costs["mes"] = df_costs[col_name].dt.strftime(
                                    "%Y-%m"
                                )
                                cost_date_col_found = True
                                break
                        if not cost_date_col_found:  # Fallback if no date column
                            df_costs["mes"] = datetime.now().strftime("%Y-%m")
                        logger.info(
                            f"✅ Loaded {len(df_costs)} cost records for trend analysis"
                        )
            except Exception as e:
                logger.info(f"⚠️ Could not load cost data for trend: {e}")

            df_completados = df_copia[
                df_copia["estado"].str.strip().isin(["pagado", "validado"])
            ]
            ingresos_mensuales = (
                df_completados.groupby("mes")["monto_aprobado"].sum() / 1_000_000
            )
            ingresos_emitidos = (
                df_copia.groupby("mes")["monto_aprobado"].sum() / 1_000_000
            )

            costos_mensuales = pd.Series(dtype=float)
            if (
                not df_costs.empty
                and "mes" in df_costs.columns
                and "importe_neto" in df_costs.columns
            ):
                costos_mensuales = (
                    df_costs.groupby("mes")["importe_neto"].sum() / 1_000_000
                )

            todos_meses = set()
            if not ingresos_mensuales.empty:
                todos_meses.update(ingresos_mensuales.index)
            if not ingresos_emitidos.empty:
                todos_meses.update(ingresos_emitidos.index)
            if not costos_mensuales.empty:
                todos_meses.update(costos_mensuales.index)

            if not todos_meses:
                return self._create_mock_monthly_trend()

            meses_ordenados = sorted(
                list(todos_meses)
            )  # Ensure it's a list for slicing
            ultimos_6_meses = (
                meses_ordenados[-6:] if len(meses_ordenados) >= 6 else meses_ordenados
            )

            meses_proyeccion = []
            if meses_ordenados:  # Check if meses_ordenados is not empty
                ultimo_mes_dt = datetime.strptime(meses_ordenados[-1], "%Y-%m")
                for i in range(1, 4):
                    mes_futuro = ultimo_mes_dt + pd.DateOffset(
                        months=i
                    )  # Use DateOffset for month increments
                    meses_proyeccion.append(mes_futuro.strftime("%Y-%m"))

            periodo_completo = ultimos_6_meses + meses_proyeccion

            (
                labels,
                datos_ingresos_reales,
                datos_ingresos_emitidos,
                datos_costos,
                datos_margen,
                datos_cashflow_proyectado,
            ) = ([], [], [], [], [], [])

            avg_ingresos_reales = (
                ingresos_mensuales.tail(3).mean()
                if len(ingresos_mensuales) >= 3
                else (ingresos_mensuales.mean() if not ingresos_mensuales.empty else 0)
            )
            avg_ingresos_emitidos = (
                ingresos_emitidos.tail(3).mean()
                if len(ingresos_emitidos) >= 3
                else (ingresos_emitidos.mean() if not ingresos_emitidos.empty else 0)
            )
            # avg_costos = costos_mensuales.tail(3).mean() if len(costos_mensuales) >=3 else (costos_mensuales.mean() if not costos_mensuales.empty else avg_ingresos_reales * 0.65)
            # Ensure avg_costos is not NaN if other averages are 0
            if not costos_mensuales.empty:
                avg_costos = (
                    costos_mensuales.tail(3).mean()
                    if len(costos_mensuales) >= 3
                    else costos_mensuales.mean()
                )
            elif (
                avg_ingresos_reales > 0
            ):  # Base cost projection on revenue if no cost data
                avg_costos = avg_ingresos_reales * 0.65
            else:  # Default if no revenue or cost data
                avg_costos = 0

            crecimiento_mensual = 1.05

            for i, mes_str in enumerate(periodo_completo):
                try:
                    fecha = datetime.strptime(mes_str, "%Y-%m")
                    labels.append(
                        fecha.strftime("%b %Y")
                        + (" (P)" if i >= len(ultimos_6_meses) else "")
                    )
                    es_proyeccion = i >= len(ultimos_6_meses)

                    if not es_proyeccion:
                        ing_real = float(ingresos_mensuales.get(mes_str, 0))
                        ing_emit = float(ingresos_emitidos.get(mes_str, 0))
                        cost_real = float(costos_mensuales.get(mes_str, 0))
                    else:
                        factor = crecimiento_mensual ** (i - len(ultimos_6_meses) + 1)
                        ing_real = avg_ingresos_reales * factor
                        ing_emit = avg_ingresos_emitidos * factor
                        cost_real = (
                            avg_costos * factor
                        )  # Project costs based on avg_costos

                    datos_ingresos_reales.append(ing_real)
                    datos_ingresos_emitidos.append(ing_emit)
                    datos_costos.append(cost_real)
                    margen = ing_real - cost_real
                    datos_margen.append(margen)
                    datos_cashflow_proyectado.append(
                        margen
                    )  # Simplified: cashflow = margin for the month
                except Exception as e_mes:
                    logger.info(
                        f"Error procesando mes {mes_str} en trend chart: {e_mes}"
                    )
                    # Append defaults to maintain list lengths
                    labels.append(mes_str)
                    for lst in [
                        datos_ingresos_reales,
                        datos_ingresos_emitidos,
                        datos_costos,
                        datos_margen,
                        datos_cashflow_proyectado,
                    ]:
                        lst.append(0)

            datasets = [
                {
                    "label": "Ingresos Cobrados (M$)",
                    "data": datos_ingresos_reales,
                    "borderColor": "#10B981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "fill": True,
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
                    "borderDash": [5, 5],
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

            margen_real_reciente = [
                m
                for i, m in enumerate(datos_margen)
                if i < len(ultimos_6_meses) and pd.notna(m)
            ]  # Filter out NaN
            promedio_margen = (
                sum(margen_real_reciente[-3:]) / 3
                if len(margen_real_reciente) >= 3
                else (
                    sum(margen_real_reciente) / len(margen_real_reciente)
                    if margen_real_reciente
                    else 0
                )
            )

            tendencia_margen = 0
            if len(margen_real_reciente) >= 2 and margen_real_reciente[0] != 0:
                tendencia_margen = (
                    (margen_real_reciente[-1] - margen_real_reciente[0])
                    / margen_real_reciente[0]
                    * 100
                )

            cashflow_3m = sum(
                d for d in datos_cashflow_proyectado[-3:] if pd.notna(d)
            )  # Sum only non-NaN

            return {
                "labels": labels,
                "datasets": datasets,
                "estadisticas": {
                    "promedio_margen_3m": round(promedio_margen, 1),
                    "tendencia_margen": round(tendencia_margen, 1),
                    "cashflow_proyectado_3m": round(cashflow_3m, 1),
                    "mejor_mes": (
                        labels[
                            datos_margen.index(
                                max(m for m in datos_margen if pd.notna(m))
                            )
                        ]
                        if any(pd.notna(m) for m in datos_margen)
                        else "N/A"
                    ),
                    "total_meses": len(labels),
                },
            }
        except Exception as e:
            logger.info(f"Error in monthly trend chart: {e}")
            import traceback

            traceback.print_exc()
            return self._create_mock_monthly_trend()

    def _build_aging_buckets_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build aging buckets chart."""
        try:
            # Ensure 'dias_espera' column exists and is numeric
            if "dias_espera" not in df.columns or df.empty:
                return {
                    "labels": ["0-30 días", "31-60 días", "61-90 días", "90+ días"],
                    "datasets": [],
                }

            # Make a copy to avoid SettingWithCopyWarning if df is a slice
            df_copy = df.copy()
            df_copy["dias_espera"] = pd.to_numeric(
                df_copy["dias_espera"], errors="coerce"
            ).fillna(0)
            dias = df_copy["dias_espera"]

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
                            "rgba(16, 185, 129, 0.8)",
                            "rgba(59, 130, 246, 0.8)",
                            "rgba(249, 115, 22, 0.8)",
                            "rgba(239, 68, 68, 0.8)",
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

    def load_related_data(self) -> ServiceResponse:
        """Load all related data needed for manager dashboard."""
        try:
            # Get EDP data
            edps_response = self.edp_repo.find_all_dataframe()
            logs_response = self.log_repository.find_all_dataframe()

            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get(
                "success", False
            ):
                return ServiceResponse(
                    success=False,
                    message=f"Failed to load EDPs data: {edps_response.get('message', 'Unknown error')}",
                    data=None,
                )

            if isinstance(logs_response, dict) and not logs_response.get(
                "success", False
            ):
                return ServiceResponse(
                    success=False,
                    message=f"Failed to load logs data: {logs_response.get('message', 'Unknown error')}",
                    data=None,
                )

            # Extract the data based on the response type
            if isinstance(edps_response, dict):
                edps_data = edps_response.get("data", [])
            else:
                # If it's a direct list (for backward compatibility)
                edps_data = edps_response

            if isinstance(logs_response, dict):
                log_data = logs_response.get("data", [])
            else:
                # If it's a direct list (for backward compatibility)
                log_data = logs_response

            # For now, return just EDP data. In the future, this could include
            # projects, logs, and other related data
            return ServiceResponse(
                success=True,
                message="Related data loaded successfully",
                data={
                    "edps": edps_data,
                    "projects": [],  # TODO: Implement when needed
                    "logs": log_data,  # TODO: Implement when needed
                },
            )

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error loading related data: {str(e)}",
                data=None,
            )

    def _build_manager_performance_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build manager performance chart with profitability analysis using real cost data."""
        try:
            manager_col = (
                "jefe_proyecto"
                if "jefe_proyecto" in df.columns
                else ("gestor" if "gestor" in df.columns else None)
            )
            if not manager_col or df.empty:
                return {"labels": ["Sin datos"], "datasets": []}

            # Ensure required columns are present and numeric
            if "monto_aprobado" not in df.columns:
                return {"labels": ["Sin datos de monto"], "datasets": []}
            df_copy = df.copy()  # Avoid SettingWithCopyWarning
            df_copy["monto_aprobado"] = pd.to_numeric(
                df_copy["monto_aprobado"], errors="coerce"
            ).fillna(0)

            costs_lookup = {}
            try:
                cost_response = self.cost_service.cost_repository.find_all_dataframe()
                if cost_response.get("success", False):
                    df_costs = cost_response.get("data", pd.DataFrame())
                    if (
                        not df_costs.empty
                        and "project_id" in df_costs.columns
                        and "importe_neto" in df_costs.columns
                    ):
                        df_costs["project_id"] = (
                            df_costs["project_id"].astype(str).str.strip()
                        )
                        df_costs["importe_neto"] = pd.to_numeric(
                            df_costs["importe_neto"], errors="coerce"
                        ).fillna(0)

                        df_costs_valid = df_costs[
                            (df_costs["project_id"].notna())
                            & (df_costs["project_id"] != "")
                            & (df_costs["project_id"] != "nan")
                        ]
                        if not df_costs_valid.empty:
                            # Aggregate costs per project_id
                            costs_summary = (
                                df_costs_valid.groupby("project_id")
                                .agg(
                                    importe_neto=("importe_neto", "sum"),
                                    # cost_id_count=('cost_id', 'count'), # If 'cost_id' exists
                                    # estado_costo_pagado_count=('estado_costo', lambda x: (x == 'pagado').sum()) # If 'estado_costo' exists
                                )
                                .to_dict("index")
                            )
                            costs_lookup = costs_summary
            except Exception as e_cost:
                logger.info(
                    f"Warning: Could not load/process cost data for manager performance: {e_cost}"
                )

            gestores_data = {}
            for gestor_name in df_copy[manager_col].dropna().unique():
                if not pd.notna(gestor_name) or not str(gestor_name).strip():
                    continue

                df_gestor = df_copy[df_copy[manager_col] == gestor_name]
                ingresos_totales, costos_totales, proyectos_procesados = 0, 0, 0

                for _, row in df_gestor.iterrows():
                    # Determine project_id: use 'proyecto' if available, else 'n_edp'
                    proyecto_id_options = [
                        str(row.get("proyecto", "")).strip(),
                        str(row.get("n_edp", "")).strip(),
                    ]
                    proyecto_id = next(
                        (pid for pid in proyecto_id_options if pid), None
                    )  # Get first valid ID

                    ingreso_proyecto = row["monto_aprobado"]  # Already numeric

                    if str(row.get("estado", "")).strip().lower() in [
                        "pagado",
                        "validado",
                    ]:
                        ingresos_totales += ingreso_proyecto
                        if proyecto_id and proyecto_id in costs_lookup:
                            costos_totales += costs_lookup[proyecto_id].get(
                                "importe_neto", 0
                            )
                        proyectos_procesados += (
                            1  # Count project if it's pagado/validado
                        )

                if ingresos_totales > 0:  # Avoid division by zero for rentabilidad
                    margen = ingresos_totales - costos_totales
                    rentabilidad = (
                        (margen / ingresos_totales * 100)
                        if ingresos_totales != 0
                        else 0
                    )
                    gestores_data[gestor_name] = {
                        "rentabilidad": rentabilidad,
                        "ingresos": ingresos_totales / 1_000_000,
                        "margen": margen / 1_000_000,
                        "proyectos": proyectos_procesados,
                    }

            if not gestores_data:
                return {"labels": ["Sin coincidencias"], "datasets": []}

            top_gestores = dict(
                sorted(
                    gestores_data.items(),
                    key=lambda x: x[1]["rentabilidad"],
                    reverse=True,
                )[:8]
            )
            labels, rentabilidades_data, colores = [], [], []

            for gestor, data in top_gestores.items():
                rent = data["rentabilidad"]
                rentabilidades_data.append(round(rent, 1))
                label = f"{str(gestor)[:12]}{'...' if len(str(gestor)) > 12 else ''} ({data['proyectos']}p)"
                labels.append(label)

                if rent >= 35:
                    colores.append("rgba(16, 185, 129, 0.8)")  # Excelente
                elif rent >= 25:
                    colores.append("rgba(34, 197, 94, 0.7)")  # Bueno
                elif rent >= 15:
                    colores.append("rgba(59, 130, 246, 0.7)")  # Aceptable
                elif rent >= 0:
                    colores.append("rgba(249, 115, 22, 0.7)")  # Bajo
                else:
                    colores.append("rgba(239, 68, 68, 0.8)")  # Negativo

            tooltip_data_dict = {
                str(g): {
                    "rentabilidad": f"{d['rentabilidad']:.1f}%",
                    "ingresos": f"${d['ingresos']:.1f}M",
                    "margen": f"${d['margen']:.1f}M",
                    "proyectos": f"{d['proyectos']} proyectos",
                }
                for g, d in top_gestores.items()
            }

            return {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Rentabilidad por Gestor (%)",
                        "data": rentabilidades_data,
                        "backgroundColor": colores,
                        "borderColor": [
                            c.replace("0.7", "1.0").replace("0.8", "1.0")
                            for c in colores
                        ],
                        "borderWidth": 1,
                    }
                ],
                "tooltip_data": tooltip_data_dict,
            }
        except Exception as e:
            logger.info(f"Error in manager performance chart: {e}")
            import traceback

            traceback.print_exc()
            return {"labels": [], "datasets": []}

    def _build_opex_capex_chart(
        self, df: pd.DataFrame
    ) -> Dict[str, Any]:  # df here is edp_df, not costs_df
        try:
            cost_response = self.cost_service.cost_repository.find_all_dataframe()
            if not cost_response.get("success", False):
                return {"error": "Failed to load cost data for OPEX/CAPEX chart"}

            df_costs = cost_response.get("data", pd.DataFrame())
            if (
                df_costs.empty
                or "tipo_costo" not in df_costs.columns
                or "importe_neto" not in df_costs.columns
            ):
                return {
                    "labels": ["OPEX", "CAPEX"],
                    "datasets": [{"data": [0, 0]}],
                }  # Default empty structure

            df_costs["tipo_costo"] = df_costs["tipo_costo"].str.lower().fillna("opex")
            df_costs["importe_neto"] = pd.to_numeric(
                df_costs["importe_neto"], errors="coerce"
            ).fillna(0)

            analisis_tipo = (
                df_costs.groupby("tipo_costo")["importe_neto"]
                .agg(total="sum")
                .reset_index()
            )

            # Ensure both opex and capex are present, even if zero
            opex_total = (
                analisis_tipo[analisis_tipo["tipo_costo"] == "opex"]["total"].sum()
                / 1_000_000
            )
            capex_total = (
                analisis_tipo[analisis_tipo["tipo_costo"] == "capex"]["total"].sum()
                / 1_000_000
            )

            return {
                "labels": ["OPEX", "CAPEX"],  # Fixed labels
                "datasets": [
                    {
                        "data": [round(opex_total, 2), round(capex_total, 2)],
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

            logger.info(f"Error in _build_opex_capex_chart: {e}")
            traceback.print_exc()
            return {"error": f"❌ Error en análisis de costos OPEX/CAPEX: {e}"}

    def _create_mock_monthly_trend(self) -> Dict[str, Any]:
        """Create mock monthly trend data when real data is not available."""
        from datetime import datetime, timedelta
        import random

        months = [
            (datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m")
            for i in range(6, 0, -1)
        ]
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
        # Ensure required columns are present
        if df.empty or not all(
            col in df.columns
            for col in ["estado", "fecha_estimada_pago", "monto_aprobado"]
        ):
            return {
                "months": ["Oct", "Nov", "Dic"],
                "amounts": [10, 15, 20],
                "total_expected": 45,
            }  # Mock

        df_copy = df.copy()
        df_copy["fecha_estimada_pago"] = pd.to_datetime(
            df_copy["fecha_estimada_pago"], errors="coerce"
        )
        df_copy["monto_aprobado"] = pd.to_numeric(
            df_copy["monto_aprobado"], errors="coerce"
        ).fillna(0)

        pending_payments = df_copy[
            (df_copy["estado"].isin(["validado", "enviado"]))
            & (pd.notna(df_copy["fecha_estimada_pago"]))
        ]

        if not pending_payments.empty:
            pending_payments["Mes_Pago"] = pending_payments[
                "fecha_estimada_pago"
            ].dt.strftime("%Y-%m")
            monthly_forecast = (
                pending_payments.groupby("Mes_Pago")["monto_aprobado"].sum() / 1_000_000
            )  # In Millions

            # Format for display (e.g., last 3-6 months or next 3-6 months)
            # For simplicity, let's take up to 6 future months if available
            future_months_forecast = monthly_forecast[
                monthly_forecast.index >= datetime.now().strftime("%Y-%m")
            ].head(6)

            return {
                "months": future_months_forecast.index.tolist(),
                "amounts": future_months_forecast.round(1).tolist(),
                "total_expected": round(future_months_forecast.sum(), 1),
            }
        else:  # Fallback to mock if no pending payments with dates
            return {
                "months": ["Oct", "Nov", "Dic"],
                "amounts": [10, 15, 20],
                "total_expected": round(45.0, 1),
            }

    def _generate_alerts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate system alerts and warnings."""
        alerts = []
        if df.empty:
            return alerts

        # Critical EDPs alert
        # Ensure 'critico' column exists, treat missing as False
        df["critico"] = (
            df.get("critico", pd.Series(False, index=df.index))
            .fillna(False)
            .astype(bool)
        )
        critical_count = len(df[df["critico"] == True])  # Explicitly check for True
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
        if "dias_espera" in df.columns and "estado" in df.columns:
            # Ensure 'dias_espera' is numeric
            df["dias_espera"] = pd.to_numeric(
                df["dias_espera"], errors="coerce"
            ).fillna(0)
            old_pending_df = df[
                (df["estado"].isin(["enviado", "revisión", "pendiente"]))
                & (df["dias_espera"] > 30)
            ]
            old_pending_count = len(old_pending_df)
            if old_pending_count > 0:
                alerts.append(
                    {
                        "type": "error",
                        "title": "EDPs Atrasados",
                        "message": f"{old_pending_count} EDPs llevan más de 30 días en proceso",
                        "count": old_pending_count,
                    }
                )
        return alerts

    def get_empty_kpis(self) -> Dict[str, Any]:
        """Returns a dictionary with empty/default KPI values."""
        return {
            "total_edp_global": 0,
            "total_validados_global": 0,
            "dias_espera_promedio_global": 0,
            "porcentaje_validacion_rapida_global": 0,
            "total_filtrados": 0,
            "total_criticos_filtrados": 0,
            "dias_espera_promedio_filtrado": 0,
            "dias_habiles_promedio_filtrado": 0,
            "total_pagado_global": 0,
            "total_propuesto_global": 0,
            "total_aprobado_global": 0,
            "meta_global": META_GLOBAL,
            "diferencia_montos": 0,
            "porcentaje_diferencia": 0,
            "avance_global": 0,
            "meta_var_porcentaje": 0,
            "pagado_var_porcentaje": 0,
            "pendiente_var_porcentaje": 0,
            "avance_var_porcentaje": 0,
            "meta_por_encargado": 0,
            "monto_pagado_encargado": 0,
            "avance_encargado": 0,
            "monto_pendiente_encargado": 0,
            "total_con_conformidad": 0,
            "porcentaje_conformidad": 0,
            "tiempo_promedio_conformidad": 0,
            "total_retrabajos": 0,
            "porcentaje_retrabajos": 0,
            "motivos_rechazo": {},
            "tipos_falla": {},
            "total_edp_pagados_conformados": 0,
            "total_pagado_global_kpi": 0,
            "pagado_reciente": 0,
            "pagado_medio": 0,
            "pagado_critico": 0,
            "total_edps_por_cobrar": 0,
            "total_pendiente_por_cobrar": 0,
            "pendiente_reciente": 0,
            "pendiente_medio": 0,
            "pendiente_critico": 0,
            "dso_global": 0,
            "dso_var": 0,
            "top_dso_proyectos": [],
            "dso_filtrado": 0,
            "total_pendiente_filtrado": 0,
            "total_pagado_filtrado": 0,
        }

    def _prepare_kpi_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepares DataFrame for KPI calculations: type conversions, ensures columns."""
        if df.empty:  # Handle empty DataFrame input
            # Define all expected columns to avoid issues later, even if empty
            expected_cols = [
                "fecha_emision",
                "fecha_envio_cliente",
                "fecha_conformidad",
                "fecha_estimada_pago",
                "Fecha Estimada de Pago",
                "monto_propuesto",
                "monto_aprobado",
                "Validado",
                "critico",
                "conformidad_enviada",
                "dias_espera",
                "Días Hábiles",
                "estado",
                "mes",
                "cliente",
                "jefe_proyecto",
                "estado_detallado",
                "motivo_no_aprobado",
                "tipo_falla",
                "n_edp",
                "proyecto",  # Added n_edp, proyecto
            ]
            df_prepared = pd.DataFrame(columns=expected_cols)
            # Set appropriate dtypes for an empty DataFrame if necessary, though operations below handle it.
            return df_prepared

        df_prepared = df.copy()

        date_cols = [
            "fecha_emision",
            "fecha_envio_cliente",
            "fecha_conformidad",
            "fecha_estimada_pago",
            "Fecha Estimada de Pago",
        ]
        for col in date_cols:
            if col in df_prepared.columns:
                df_prepared[col] = pd.to_datetime(df_prepared[col], errors="coerce")
            else:
                df_prepared[col] = pd.NaT

        money_cols = ["monto_propuesto", "monto_aprobado"]
        for col in money_cols:
            if col in df_prepared.columns:
                df_prepared[col] = pd.to_numeric(
                    df_prepared[col], errors="coerce"
                ).fillna(0.0)
            else:
                df_prepared[col] = 0.0

        bool_cols_map = {"Validado": False, "critico": False}
        for col, default_val in bool_cols_map.items():
            if col in df_prepared.columns:
                if df_prepared[col].dtype == "object":
                    df_prepared[col] = (
                        df_prepared[col]
                        .astype(str)
                        .str.lower()
                        .map(
                            {
                                "sí": True,
                                "true": True,
                                "1": True,
                                "yes": True,
                                "verdadero": True,
                                "no": False,
                                "false": False,
                                "0": False,
                                "nan": False,
                                "": False,
                                None: False,
                            }
                        )
                        .fillna(default_val)
                    )
                elif pd.api.types.is_numeric_dtype(
                    df_prepared[col]
                ):  # Handle 1/0 as int/float
                    df_prepared[col] = df_prepared[col].map({1: True, 0: False}).fillna(default_val).astype(bool)
            else:
                df_prepared[col] = default_val

        if "conformidad_enviada" not in df_prepared.columns:
            df_prepared["conformidad_enviada"] = "No"
        else:
            df_prepared["conformidad_enviada"] = df_prepared[
                "conformidad_enviada"
            ].fillna("No")

        df_prepared = self._calcular_dias_espera(df_prepared)

        if (
            "fecha_envio_cliente" in df_prepared.columns
            and "fecha_conformidad" in df_prepared.columns
        ):
            df_prepared["Días Hábiles"] = df_prepared.apply(
                lambda row: self._calcular_dias_habiles(
                    row.get("fecha_envio_cliente"), row.get("fecha_conformidad")
                ),
                axis=1,
            )
        else:  # Ensure column exists even if calculation can't be done
            df_prepared["Días Hábiles"] = np.nan

        # Ensure 'Días Hábiles' is numeric after apply (it should be due to _calcular_dias_habiles returning float/nan)
        df_prepared["Días Hábiles"] = pd.to_numeric(
            df_prepared["Días Hábiles"], errors="coerce"
        )

        ensure_cols_with_defaults = {
            "estado": "",
            "mes": "",
            "cliente": "",
            "jefe_proyecto": "",
            "estado_detallado": "",
            "motivo_no_aprobado": "",
            "tipo_falla": "",
            "n_edp": "",
            "proyecto": "",  # Added n_edp, proyecto
        }
        for col, default_value in ensure_cols_with_defaults.items():
            if col not in df_prepared.columns:
                df_prepared[col] = default_value
            else:  # Fill NaNs for string columns that should exist
                if df_prepared[col].dtype == "object":
                    df_prepared[col] = df_prepared[col].fillna(default_value)

        return df_prepared

    # Placeholder for _calculate_financial_kpis, _calculate_operational_kpis etc.
    # These will be replaced by the new get_controller_dashboard_context logic or integrated.
    def _calculate_financial_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def _calculate_operational_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def _calculate_profitability_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def _calculate_aging_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def _calculate_efficiency_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def _calculate_monthly_financials(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def _calculate_working_capital_impact(self, df: pd.DataFrame) -> float:
        return 0.0

    def _get_manager_filter_options(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def _calculate_performance_by_period(
        self, df: pd.DataFrame, period: str
    ) -> Dict[str, Any]:
        return {}

    def _calculate_trends(self, df: pd.DataFrame, period: str) -> Dict[str, Any]:
        return {}

    def _generate_recommendations(self, perf_data: Dict, trends: Dict) -> List[str]:
        return []

    def _get_default_processed_context(
        self, request_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Returns a default, empty structure for the dashboard context."""
        empty_kpis_flat = self.get_empty_kpis()
        return {
            "registros": [],
            "filtros": request_filters or {},
            "meses": [],
            "encargados": [],
            "clientes": [],
            "estados_detallados": [],
            "dso_global": 0.0,
            "dso_var": 0.0,
            "top_dso_proyectos": [],
            "dso_filtrado": 0.0,
            "total_pendiente_filtrado": 0.0,
            "total_pagado_filtrado": 0.0,
            **empty_kpis_flat,
        }

    def get_processed_dashboard_context(
        self,
        df_edp_raw: pd.DataFrame,
        df_log_raw: pd.DataFrame,
        request_filters: Dict[str, Any],
    ) -> ServiceResponse:
        """
        Processes raw EDP and Log data with filters to generate the full context
        for the controller dashboard, matching the original controller's output.
        """
        try:
            # 1. Initial Data Preparation
            # Ensure copies are used if methods modify DFs, though _prepare_kpi_data already makes a copy.
            df_full_prepared = self._prepare_kpi_data(df_edp_raw)
            df_full = self._enriquecer_df_con_estado_detallado(
                df_full_prepared,
                df_log_raw.copy() if df_log_raw is not None else pd.DataFrame(),
            )

            # Handle case where df_full might be empty after preparation (e.g., if df_edp_raw was None or unprocessable)
            if df_full.empty:
                logger.info(
                    "Warning: df_full is empty after preparation. Returning default context."
                )
                return ServiceResponse(
                    success=True,
                    data=self._get_default_processed_context(request_filters),
                    message="Input data was empty or unprocessable, dashboard shows default values.",
                )

            # 2. Filter Options
            meses_ordenados = self._obtener_meses_ordenados(df_full)
            clientes_unicos = (
                sorted(list(df_full["cliente"].dropna().unique()))
                if "cliente" in df_full.columns
                else []
            )
            jefes_unicos = (
                sorted(list(df_full["jefe_proyecto"].dropna().unique()))
                if "jefe_proyecto" in df_full.columns
                else []
            )
            estado_filter = (
                sorted(list(df_full["estado"].dropna().unique()))
                if "estado" in df_full.columns
                else []
            )

            filter_options = {
                "mes": meses_ordenados,
                "cliente": clientes_unicos,
                "jefe_proyecto": jefes_unicos,
                "estado": estado_filter,
            }

            # 3. Apply Filters
            filters = {
                "mes": request_filters.get("mes"),
                "jefe_proyecto": request_filters.get("jefe_proyecto"),
                "cliente": request_filters.get("cliente"),
                "estado": request_filters.get("estado"),
            }
            print(filters)

            df = df_full.copy()
            if filters["mes"]:
                df = df[df["mes"] == filters["mes"]]
            if filters["jefe_proyecto"] and filters["jefe_proyecto"] != "todos":
                df = df[df["jefe_proyecto"] == filters["jefe_proyecto"]]
            if filters["cliente"] and filters["cliente"] != "todos":
                df = df[df["cliente"] == filters["cliente"]]

            # Aplicar filtro de estado con nueva lógica
            if filters["estado"] == "pendientes":
                # Filtro "Pendientes" - solo muestra estados de revisión y enviado
                df = df[df["estado"].isin(["revisión", "enviado"])]
            elif filters["estado"] == "todos" or not filters["estado"]:  
                # No aplicar filtro de estado, mostrar todo
                pass
            else:
                # Filtro específico (validado, pagado, etc)
                df = df[df["estado"] == filters["estado"]]

            df_filtered = df.copy()  # Keep filtered DataFrame for later use

            mes_filter = filters["mes"] if filters["mes"] else None
            jefes_filter = (
                filters["jefe_proyecto"]
                if filters["jefe_proyecto"] and filters["jefe_proyecto"] != "todos"
                else None
            )
            cliente_filter = (
                filters["cliente"]
                if filters["cliente"] and filters["cliente"] != "todos"
                else None
            )
            estado_filter = (
                filters["estado"]
                if filters["estado"] and filters["estado"] != "todos"
                else None
            )
            # 4. Calculate KPIs and Metrics

            # KPIs Globales
            total_edp_global = df_full.shape[0]
            total_validados_global = df_full[
                df_full["estado"].isin(["validado", "pagado"])
            ].shape[0]
            # Use pd.Series.mean() which handles empty series by returning NaN
            dias_espera_promedio_global_raw = df_full["dias_espera"].mean()
            dias_espera_promedio_global = round(
                (
                    dias_espera_promedio_global_raw
                    if pd.notna(dias_espera_promedio_global_raw)
                    else 0
                ),
                1,
            )

            validados_rapidos_global = df_full[
                df_full["estado"].isin(["validado", "pagado"])
                & (df_full["dias_espera"] <= 30)
            ].shape[0]
            porcentaje_validacion_rapida_global = (
                round(validados_rapidos_global / total_validados_global * 100, 1)
                if total_validados_global > 0
                else 0.0
            )
            kpis_globales = {
                "total_edp_global": total_edp_global,
                "total_validados_global": total_validados_global,
                "dias_espera_promedio_global": dias_espera_promedio_global,
                "porcentaje_validacion_rapida_global": porcentaje_validacion_rapida_global,
            }

            # KPIs Filtrados
            total_filtrados = df_filtered.shape[0]
            total_criticos_filtrados = df_filtered[
                df_filtered["critico"] == True
            ].shape[0]

            dias_espera_promedio_filtrado_raw = df_filtered["dias_espera"].mean()
            dias_espera_promedio_filtrado = round(
                (
                    dias_espera_promedio_filtrado_raw
                    if pd.notna(dias_espera_promedio_filtrado_raw)
                    else 0
                ),
                1,
            )

            dias_habiles_promedio_filtrado_raw = df_filtered[
                "Días Hábiles"
            ].mean()  # Días Hábiles is float/np.nan
            dias_habiles_promedio_filtrado = round(
                (
                    dias_habiles_promedio_filtrado_raw
                    if pd.notna(dias_habiles_promedio_filtrado_raw)
                    else 0
                ),
                1,
            )
            kpis_filtrados = {
                "total_filtrados": total_filtrados,
                "total_criticos_filtrados": total_criticos_filtrados,
                "dias_espera_promedio_filtrado": dias_espera_promedio_filtrado,
                "dias_habiles_promedio_filtrado": dias_habiles_promedio_filtrado,
            }

            # Métricas Financieras
            total_pagado_global = df_full[df_full["estado"].isin(["pagado", "validado"])][
                "monto_aprobado"
            ].sum()
            total_propuesto_global = df_full["monto_propuesto"].sum()
            total_aprobado_global = df_full["monto_aprobado"].sum()

            diferencia_montos = total_aprobado_global - total_propuesto_global
            porcentaje_diferencia = (
                round((diferencia_montos / total_propuesto_global * 100), 1)
                if total_propuesto_global > 0
                else 0.0
            )
            avance_global = (
                round(total_pagado_global / META_GLOBAL * 100, 1)
                if META_GLOBAL > 0
                else 0.0
            )
            metricas_financieras = {
                "total_pagado_global": total_pagado_global,
                "total_propuesto_global": total_propuesto_global,
                "total_aprobado_global": total_aprobado_global,
                "meta_global": META_GLOBAL,  # Constant
                "diferencia_montos": diferencia_montos,
                "porcentaje_diferencia": porcentaje_diferencia,
                "avance_global": avance_global,
            }
            # Specific filtered financial KPIs (passed separately to template in original)
            dso_filtrado = (
                self._calcular_dso_para_dataset(df_filtered.copy())
                if not df_filtered.empty
                else 0.0
            )
            total_pendiente_filtrado = df_filtered[
                df_filtered["estado"].isin(["enviado", "pendiente", "revisión"])
            ]["monto_propuesto"].sum()
            total_pagado_filtrado = df_filtered[
                df_filtered["estado"].isin(["pagado", "validado"])
            ]["monto_aprobado"].sum()

            # Variaciones Mensuales
            variaciones = self._calcular_variaciones_mensuales(
                df_full.copy(), mes_filter, meses_ordenados, total_pagado_global
            )

            # Info Encargado
            meta_por_encargado = METAS_ENCARGADOS.get(jefes_filter, 0)
            monto_pagado_encargado = 0.0
            avance_encargado = 0.0
            monto_pendiente_encargado = 0.0
            if (
                jefes_filter
            ):  # df_filtered is already filtered by encargado if filter is active
                monto_pagado_encargado = df_filtered[df_filtered["estado"] == "pagado"][
                    "monto_aprobado"
                ].sum()
                # Original used monto_aprobado for pendiente_por_pago_encargado
                pendiente_por_pago_encargado = df_filtered[
                    df_filtered["estado"].isin(["pendiente", "revisión", "enviado"])
                ]["monto_aprobado"].sum()
                monto_pendiente_encargado = (
                    pendiente_por_pago_encargado
                    if pd.notna(pendiente_por_pago_encargado)
                    else 0.0
                )

                if meta_por_encargado > 0:
                    avance_encargado = round(
                        monto_pagado_encargado / meta_por_encargado * 100, 1
                    )
            info_encargado = {
                "meta_por_encargado": meta_por_encargado,
                "monto_pagado_encargado": monto_pagado_encargado,
                "avance_encargado": avance_encargado,
                "monto_pendiente_encargado": monto_pendiente_encargado,
            }

            # KPIs Conformidad
            total_con_conformidad = df_full[
                df_full["conformidad_enviada"] == "Sí"
            ].shape[0]
            porcentaje_conformidad = (
                round((total_con_conformidad / total_edp_global * 100), 1)
                if total_edp_global > 0
                else 0.0
            )

            tiempo_promedio_conformidad = 0.0
            mask_fechas_validas = (
                df_full["fecha_envio_cliente"].notna()
                & df_full["fecha_conformidad"].notna()
            )
            if mask_fechas_validas.any():
                tiempos_conformidad = (
                    df_full.loc[mask_fechas_validas, "fecha_conformidad"]
                    - df_full.loc[mask_fechas_validas, "fecha_envio_cliente"]
                ).dt.days
                # Filter out negative days if any, though less likely for conformity
                tiempos_conformidad_positivos = tiempos_conformidad[
                    tiempos_conformidad >= 0
                ]
                if not tiempos_conformidad_positivos.empty:
                    tiempo_promedio_conformidad_raw = (
                        tiempos_conformidad_positivos.mean()
                    )
                    tiempo_promedio_conformidad = round(
                        (
                            tiempo_promedio_conformidad_raw
                            if pd.notna(tiempo_promedio_conformidad_raw)
                            else 0
                        ),
                        1,
                    )

            kpis_conformidad = {
                "total_con_conformidad": total_con_conformidad,
                "porcentaje_conformidad": porcentaje_conformidad,
                "tiempo_promedio_conformidad": tiempo_promedio_conformidad,
            }

            # Análisis Retrabajos
            total_retrabajos = df_full[
                df_full["estado_detallado"] == "re-trabajo solicitado"
            ].shape[0]
            porcentaje_retrabajos = (
                round((total_retrabajos / total_edp_global * 100), 1)
                if total_edp_global > 0
                else 0.0
            )
            motivos_rechazo_series = (
                df_full["motivo_no_aprobado"].value_counts()
                if "motivo_no_aprobado" in df_full.columns
                else pd.Series(dtype="object")
            )
            tipos_falla_series = (
                df_full["tipo_falla"].value_counts()
                if "tipo_falla" in df_full.columns
                else pd.Series(dtype="object")
            )
            analisis_retrabajos = {
                "total_retrabajos": total_retrabajos,
                "porcentaje_retrabajos": porcentaje_retrabajos,
                "motivos_rechazo": (
                    motivos_rechazo_series.to_dict()
                    if not motivos_rechazo_series.empty
                    else {}
                ),
                "tipos_falla": (
                    tipos_falla_series.to_dict() if not tipos_falla_series.empty else {}
                ),
            }

            # Pagos Data (uses df_full)
            edps_pagados_conformados_df = df_full[
                df_full["estado"].isin(["pagado", "validado"])
            ]
            pagos_data = {
                "total_edp_pagados_conformados": edps_pagados_conformados_df.shape[0],
                "total_pagado_global_kpi": edps_pagados_conformados_df[
                    "monto_aprobado"
                ].sum(),
                "pagado_reciente": edps_pagados_conformados_df[
                    edps_pagados_conformados_df["dias_espera"] <= 30
                ]["monto_aprobado"].sum(),
                "pagado_medio": edps_pagados_conformados_df[
                    (edps_pagados_conformados_df["dias_espera"] > 30)
                    & (edps_pagados_conformados_df["dias_espera"] <= 60)
                ]["monto_aprobado"].sum(),
                "pagado_critico": edps_pagados_conformados_df[
                    edps_pagados_conformados_df["dias_espera"] > 60
                ]["monto_aprobado"].sum(),
            }

            # Pendientes Data (uses df_full)
            edps_por_cobrar_df = df_full[
                df_full["estado"].isin(["enviado", "pendiente", "revisión"])
            ]
            pendientes_data = {
                "total_edps_por_cobrar": edps_por_cobrar_df.shape[0],
                "total_pendiente_por_cobrar": edps_por_cobrar_df[
                    "monto_propuesto"
                ].sum(),  # Original uses monto_propuesto here
                "pendiente_reciente": edps_por_cobrar_df[
                    edps_por_cobrar_df["dias_espera"] <= 30
                ]["monto_propuesto"].sum(),
                "pendiente_medio": edps_por_cobrar_df[
                    (edps_por_cobrar_df["dias_espera"] > 30)
                    & (edps_por_cobrar_df["dias_espera"] <= 60)
                ]["monto_propuesto"].sum(),
                "pendiente_critico": edps_por_cobrar_df[
                    edps_por_cobrar_df["dias_espera"] > 60
                ]["monto_propuesto"].sum(),
            }

            # DSO Calculations
            mes_anterior_para_dso = None
            df_mes_anterior_para_dso = None
            if mes_filter and len(meses_ordenados) > 1:
                try:
                    # Ensure meses_ordenados contains strings for index() if mes_filter is string
                    meses_ordenados_str = [str(m) for m in meses_ordenados]
                    idx_mes_actual = meses_ordenados_str.index(str(mes_filter))
                    if idx_mes_actual > 0:
                        mes_anterior_para_dso = meses_ordenados_str[idx_mes_actual - 1]
                        df_mes_anterior_para_dso = df_full[
                            df_full["mes"] == mes_anterior_para_dso
                        ].copy()
                except ValueError:  # mes_filter might not be in list
                    pass

            dso_global, dso_var, top_dso_proyectos_raw = self._calcular_dso(
                df_full.copy(), mes_anterior_para_dso, df_mes_anterior_para_dso
            )
            top_dso_proyectos = self._clean_nat_values(top_dso_proyectos_raw)

            # 5. Registros
            registros_raw = df_filtered.to_dict(orient="records")
            registros = self._clean_nat_values(registros_raw)

            total_edps_criticos_global = df_full[
                df_full["estado"].isin(["enviado", "pendiente", "revisión"])
                & (df_full["dias_espera"] >= 30)
            ].shape[0]

            # 6. Construct Final Context Dictionary
            context = {
                "registros": registros,
                "filtros": request_filters,  # Pass back the applied filters
                "meses": filter_options["mes"],
                "jefes_proyectos": filter_options["jefe_proyecto"],
                "clientes": filter_options["cliente"],
                "estados_detallados": filter_options["estado"],
                "dso_global": dso_global,
                "dso_var": dso_var,
                "top_dso_proyectos": top_dso_proyectos,
                "dso_filtrado": dso_filtrado,
                "total_pendiente_filtrado": total_pendiente_filtrado,
                "total_pagado_filtrado": total_pagado_filtrado,
                "total_edps_criticos_global": total_edps_criticos_global,
                **kpis_globales,
                **kpis_filtrados,
                **metricas_financieras,
                **variaciones,
                **info_encargado,
                **kpis_conformidad,
                **analisis_retrabajos,
                **pagos_data,
                **pendientes_data,
            }

            return ServiceResponse(success=True, data=context)

        except Exception as e:
            import traceback

            error_message = f"Error in get_processed_dashboard_context: {str(e)}\n{traceback.format_exc()}"
            logger.info(error_message)
            # Return a default, structured, empty context on failure
            default_context = self._get_default_processed_context(request_filters)
            return ServiceResponse(
                success=False, message=error_message, data=default_context
            )
