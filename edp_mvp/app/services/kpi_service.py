"""
KPI Service for managing KPI calculations and analytics.
Central service for all KPI calculations to avoid duplication.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from statistics import mean, median
import pandas as pd
import numpy as np
import logging
import calendar
import traceback

from ..models import EDP, KPI
from ..repositories.edp_repository import EDPRepository
from . import BaseService, ServiceResponse
from ..utils.business_rules import business_rules, es_critico

logger = logging.getLogger(__name__)


class KPIService(BaseService):
    """Service for managing KPI calculations and analytics."""
    
    def __init__(self):
        super().__init__()
        self.edp_repository = EDPRepository()
    
    def calculate_all_kpis(self) -> ServiceResponse:
        """Calculate all KPIs for all EDPs."""
        try:
            edps = self.edp_repository.find_all()
            all_kpis = {}
            
            for edp in edps:
                edp_kpis = self.calculate_edp_kpis(edp.id)
                if edp_kpis.success:
                    all_kpis[edp.id] = edp_kpis.data
            
            # Calculate aggregate KPIs
            aggregate_kpis = self._calculate_aggregate_kpis(edps)
            
            return ServiceResponse(
                success=True,
                data={
                    'individual_kpis': all_kpis,
                    'aggregate_kpis': aggregate_kpis,
                    'calculation_timestamp': datetime.now().isoformat()
                },
                message=f"Calculated KPIs for {len(edps)} EDPs"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error calculating KPIs: {str(e)}"
            )
    
    def calculate_edp_kpis(self, edp_id: str) -> ServiceResponse:
        """Calculate KPIs for a specific EDP."""
        try:
            edp = self.edp_repository.find_by_id(edp_id)
            if not edp:
                return ServiceResponse(
                    success=False,
                    message=f"EDP with ID {edp_id} not found"
                )
            
            kpis = {}
            
            # Time-based KPIs
            kpis.update(self._calculate_time_kpis(edp))
            
            # Financial KPIs (convert EDP to row format)
            edp_row = {
                'budget': edp.budget,
                'status': edp.status
            }
            kpis.update(self._calculate_financial_kpis_from_row(edp_row))
            
            # Performance KPIs
            kpis.update(self._calculate_performance_kpis(edp))
            
            # Status KPIs
            kpis.update(self._calculate_status_kpis(edp))
            
            return ServiceResponse(
                success=True,
                data=kpis,
                message="KPIs calculated successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error calculating KPIs for EDP {edp_id}: {str(e)}"
            )
    
    def get_kpi_trends(self, edp_id: str, days: int = 30) -> ServiceResponse:
        """Get KPI trends for the last N days."""
        try:
            # For now, return mock trend data
            # In a real implementation, this would query historical KPI data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Generate real trend data
            trend_data = self._generate_real_trend_data(edp_id, start_date, end_date)
            
            return ServiceResponse(
                success=True,
                data=trend_data,
                message=f"Retrieved {days}-day trend data"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving KPI trends: {str(e)}"
            )
    
    def get_kpi_benchmarks(self) -> ServiceResponse:
        """Get KPI benchmarks across all EDPs."""
        try:
            edps = self.edp_repository.find_all()
            if not edps:
                return ServiceResponse(
                    success=False,
                    message="No EDPs found for benchmark calculation"
                )
            
            benchmarks = {}
            
            # Calculate benchmarks for each KPI type
            completion_rates = []
            budget_utilizations = []
            time_efficiencies = []
            
            for edp in edps:
                kpi_response = self.calculate_edp_kpis(edp.id)
                if kpi_response.success:
                    kpis = kpi_response.data
                    
                    if 'completion_rate' in kpis:
                        completion_rates.append(kpis['completion_rate'])
                    
                    if 'budget_utilization' in kpis:
                        budget_utilizations.append(kpis['budget_utilization'])
                    
                    if 'time_efficiency' in kpis:
                        time_efficiencies.append(kpis['time_efficiency'])
            
            # Calculate benchmark statistics
            if completion_rates:
                benchmarks['completion_rate'] = self._calculate_benchmark_stats(completion_rates)
            
            if budget_utilizations:
                benchmarks['budget_utilization'] = self._calculate_benchmark_stats(budget_utilizations)
            
            if time_efficiencies:
                benchmarks['time_efficiency'] = self._calculate_benchmark_stats(time_efficiencies)
            
            return ServiceResponse(
                success=True,
                data=benchmarks,
                message="Benchmarks calculated successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error calculating benchmarks: {str(e)}"
            )
    
    def update_kpi_targets(self, edp_id: str, targets: Dict[str, float]) -> ServiceResponse:
        """Update KPI targets for an EDP."""
        try:
            edp = self.edp_repository.find_by_id(edp_id)
            if not edp:
                return ServiceResponse(
                    success=False,
                    message=f"EDP with ID {edp_id} not found"
                )
            
            # Validate targets
            valid_kpis = ['completion_rate', 'budget_utilization', 'time_efficiency', 'quality_score']
            invalid_kpis = [kpi for kpi in targets.keys() if kpi not in valid_kpis]
            
            if invalid_kpis:
                return ServiceResponse(
                    success=False,
                    message=f"Invalid KPI names: {', '.join(invalid_kpis)}",
                    errors={'invalid_kpis': invalid_kpis}
                )
            
            # Update KPI targets in the EDP's KPIs
            current_kpis = edp.kpis or {}
            for kpi_name, target_value in targets.items():
                if kpi_name not in current_kpis:
                    current_kpis[kpi_name] = {}
                current_kpis[kpi_name]['target'] = target_value
            
            # Save updated KPIs
            success = self.edp_repository.update_kpis(edp_id, current_kpis)
            
            if success:
                return ServiceResponse(
                    success=True,
                    data={'updated_targets': targets},
                    message="KPI targets updated successfully"
                )
            else:
                return ServiceResponse(
                    success=False,
                    message="Failed to update KPI targets"
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error updating KPI targets: {str(e)}"
            )
    
    def calculate_manager_dashboard_kpis(self, df_full: pd.DataFrame, df_filtered: pd.DataFrame = None) -> ServiceResponse:
        """Calculate ALL KPIs for manager dashboard including new dashboard.tsx components."""
        try:
            if df_full.empty:
                return ServiceResponse(
                    success=True,
                    data=self.get_empty_manager_kpis(),
                    message="No data available, returning empty KPIs"
                )
            
            df_full = self._prepare_kpi_data(df_full)
            
            # Calculate ALL KPIs needed for dashboard
            all_kpis = {}
            
            # 1. EXISTING COMPONENTS
            # Header metrics (3 fields)
            all_kpis.update(self._calculate_header_metrics(df_full))
            
            # KPI cards metrics (12 fields)
            all_kpis.update(self._calculate_kpi_cards_metrics(df_full))
            
            # Forecast 7 days (7 fields)
            all_kpis.update(self._calculate_forecast_7_days(df_full))
            
            # Executive summary (6 fields)
            all_kpis.update(self._calculate_executive_summary_metrics(df_full))
            
            # 2. NEW DASHBOARD.TSX COMPONENTS
            # Executive dashboard KPIs (all new components)
            all_kpis.update(self.calculate_executive_dashboard_kpis(df_full))
            
            # Sanitize for JSON
            all_kpis = self._sanitize_for_json(all_kpis)
            
            return ServiceResponse(
                success=True,
                data=all_kpis,
                message="All dashboard KPIs calculated successfully"
            )
        except Exception as e:
            logger.error(f"Error calculating dashboard KPIs: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error calculating dashboard KPIs: {str(e)}",
                data=self.get_empty_manager_kpis()
            )

    def _calculate_header_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate header metrics: dso_actual, forecast_7_dias, progreso_objetivo"""
        try:
            # DSO Actual
            dso_actual = self._calculate_dso(df)
            
            # Forecast 7 días (suma de los 7 días)
            forecast_metrics = self._calculate_forecast_7_days(df)
            forecast_7_dias = sum([
                forecast_metrics.get('forecast_day_1', 0),
                forecast_metrics.get('forecast_day_2', 0),
                forecast_metrics.get('forecast_day_3', 0),
                forecast_metrics.get('forecast_day_4', 0),
                forecast_metrics.get('forecast_day_5', 0),
                forecast_metrics.get('forecast_day_6', 0),
                forecast_metrics.get('forecast_day_7', 0)
            ])
            
            # Progreso objetivo (basado en tasa de completación)
            completed_projects = len(df[df["estado"].str.strip().str.lower().isin(["pagado", "validado"])])
            total_projects = len(df)
            completion_rate = (completed_projects / max(1, total_projects) * 100)
            target_completion_rate = 80.0  # 80% target
            progreso_objetivo = min(100, (completion_rate / target_completion_rate * 100))
            
            return {
                'dso_actual': round(dso_actual, 1),
                'forecast_7_dias': round(forecast_7_dias, 1),
                'progreso_objetivo': round(progreso_objetivo, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating header metrics: {e}")
            return {
                'dso_actual': 0.0,
                'forecast_7_dias': 0.0,
                'progreso_objetivo': 0.0
            }

    def _calculate_kpi_cards_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate KPI cards metrics: critical projects, aging 31-60, fast collection, meta gap"""
        try:
            # Critical Projects (>30 días DSO and not paid - same as API)
            critical_projects_count = self._calculate_critical_projects_count(df)
            critical_amount = self._calculate_critical_amount(df) / 1_000_000  # Convert to millions
            
            # Aging 31-60 días - USAR dso_actual en lugar de dias_espera
            aging_31_60_count = 0
            aging_31_60_amount = 0.0
            
            if 'dso_actual' in df.columns:
                aging_31_60_mask = (pd.to_numeric(df['dso_actual'], errors='coerce') >= 31) & (pd.to_numeric(df['dso_actual'], errors='coerce') <= 60)
                aging_31_60_count = aging_31_60_mask.sum()
                aging_31_60_amount = df[aging_31_60_mask]['monto_propuesto'].sum() / 1_000_000
            
            # Fast Collection (<30 días DSO) - USAR dso_actual
            fast_collection_count = 0
            fast_collection_amount = 0.0
            
            if 'dso_actual' in df.columns:
                fast_collection_mask = pd.to_numeric(df['dso_actual'], errors='coerce') < 30
                fast_collection_count = fast_collection_mask.sum()
                fast_collection_amount = df[fast_collection_mask]['monto_propuesto'].sum() / 1_000_000
            
            # Meta Gap
            completed_amount = df[df["estado"].str.strip().str.lower().isin(["pagado"])]["monto_aprobado"].sum() / 1_000_000
            meta_mensual = 40.0  # 40M CLP target
            meta_gap = max(0, meta_mensual - completed_amount)
            
            # Days remaining (simplified)
            from datetime import datetime
            current_day = datetime.now().day
            days_remaining = 30 - current_day if current_day <= 30 else 0
            
            return {
                'critical_projects_count': critical_projects_count,
                'critical_projects_change': 0.0,  # No historical data for change
                'critical_amount': round(critical_amount, 1),
                'aging_31_60_count': aging_31_60_count,
                'aging_31_60_change': 0.0,  # No historical data for change
                'aging_31_60_amount': round(aging_31_60_amount, 1),
                'fast_collection_count': fast_collection_count,
                'fast_collection_change': 0.0,  # No historical data for change
                'fast_collection_amount': round(fast_collection_amount, 1),
                'meta_gap': round(meta_gap, 1),
                'days_remaining': days_remaining
            }
        except Exception as e:
            logger.error(f"Error calculating KPI cards metrics: {e}")
            return {
                'critical_projects_count': 0,
                'critical_projects_change': 0.0,
                'critical_amount': 0.0,
                'aging_31_60_count': 0,
                'aging_31_60_change': 0.0,
                'aging_31_60_amount': 0.0,
                'fast_collection_count': 0,
                'fast_collection_change': 0.0,
                'fast_collection_amount': 0.0,
                'meta_gap': 0.0,
                'days_remaining': 0
            }

    def _calculate_forecast_7_days(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate 7-day forecast based on REAL project completion probability using actual states from database"""
        try:
            # Projects likely to complete in next 7 days based on estado
            # From your DB: estado can be 'enviado', 'pagado', 'pendiente', 'revisión', 'validado'
            forecast_base = df[df["estado"].str.strip().str.lower().isin(["enviado", "pendiente", "revisión"])]
            
            if forecast_base.empty:
                return {f'forecast_day_{i}': 0.0 for i in range(1, 8)}
            
            # Use monto_aprobado for forecast calculation
            total_forecast_amount = forecast_base["monto_aprobado"].sum() / 1_000_000
            
            # Distribute forecast across 7 days with realistic probability decay
            # Higher probability for earlier days
            daily_probabilities = [0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.05]  # Decreasing probability
            
            forecast_days = {}
            for i, prob in enumerate(daily_probabilities, 1):
                forecast_days[f'forecast_day_{i}'] = round(total_forecast_amount * prob, 1)
            
            return forecast_days
            
        except Exception as e:
            logger.error(f"Error calculating forecast 7 days: {e}")
            return {f'forecast_day_{i}': 0.0 for i in range(1, 8)}

    def _calculate_executive_summary_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate executive summary metrics: ingresos_totales, crecimiento_ingresos, efficiency_score, roi_promedio, proyectos_completados, satisfaccion_cliente"""
        try:
            # Ingresos totales (only pagado projects - real completed projects from database)
            completed_df = df[df["estado"].str.strip().str.lower() == "pagado"]
            ingresos_totales = completed_df["monto_aprobado"].sum() / 1_000_000
            
            # Proyectos completados (only pagado)
            proyectos_completados = len(completed_df)
            
            # Crecimiento ingresos (simplified - no historical data available)
            crecimiento_ingresos = 0.0  # Would need historical data
            
            # Efficiency score (based on completion rate and DSO)
            total_projects = len(df)
            completion_rate = (proyectos_completados / max(1, total_projects) * 100)
            dso = self._calculate_dso(df)
            dso_efficiency = max(0, min(100, (35.0 / max(1, dso)) * 100)) if dso > 0 else 0
            efficiency_score = (completion_rate * 0.6 + dso_efficiency * 0.4)
            
            # ROI promedio (simplified calculation)
            total_revenue = ingresos_totales
            estimated_costs = total_revenue * 0.65  # 65% cost ratio
            net_profit = total_revenue - estimated_costs
            total_investment = df["monto_propuesto"].sum() / 1_000_000 * 0.1  # 10% investment ratio
            roi_promedio = (net_profit / max(1, total_investment) * 100) if total_investment > 0 else 0
            
            # Satisfacción cliente (based on performance metrics)
            satisfaccion_cliente = (completion_rate * 0.6 + dso_efficiency * 0.4)
            
            return {
                'ingresos_totales': round(ingresos_totales, 1),
                'crecimiento_ingresos': round(crecimiento_ingresos, 1),
                'efficiency_score': round(max(0, min(100, efficiency_score)), 1),
                'roi_promedio': round(max(0, roi_promedio), 1),
                'proyectos_completados': proyectos_completados,
                'satisfaccion_cliente': round(max(0, min(100, satisfaccion_cliente)), 1)
            }
        except Exception as e:
            logger.error(f"Error calculating executive summary metrics: {e}")
            return {
                'ingresos_totales': 0.0,
                'crecimiento_ingresos': 0.0,
                'efficiency_score': 0.0,
                'roi_promedio': 0.0,
                'proyectos_completados': 0,
                'satisfaccion_cliente': 0.0
            }

    def calculate_essential_kpis(self, df_full: pd.DataFrame, df_filtered: pd.DataFrame = None) -> ServiceResponse:
        """Calculate essential KPIs for immediate response, including template requirements."""
        try:
            if df_full.empty:
                return ServiceResponse(
                    success=True,
                    data=self.get_empty_manager_kpis(),
                    message="No data available, returning empty KPIs"
                )

            df_full = self._prepare_kpi_data(df_full)

            # Calculate comprehensive KPIs with real data
            total_edps = len(df_full)
            df_numeric = df_full.copy()

            # Ensure numeric columns
            for col in ["monto_propuesto", "monto_aprobado"]:
                if col in df_numeric.columns:
                    df_numeric[col] = pd.to_numeric(
                        df_numeric[col], errors="coerce"
                    ).fillna(0)

            # Basic financial metrics
            total_amount = df_numeric["monto_propuesto"].sum()
            approved_amount = df_numeric["monto_aprobado"].sum()

            # Status counts with comprehensive status mapping
            status_counts = df_full["estado"].str.strip().str.lower().value_counts()
            paid_count = status_counts.get("pagado", 0)
            validated_count = status_counts.get("validado", 0)
            pending_count = status_counts.get("enviado", 0) + status_counts.get("pendiente", 0) + status_counts.get("revision", 0)
            
            # Calculate completed projects (paid + validated)
            completed_projects = paid_count + validated_count
            
            # Calculate ingresos_totales from completed projects
            estados_completados = ["pagado", "validado"]
            df_completados = df_full[df_full["estado"].str.strip().str.lower().isin(estados_completados)]
            ingresos_totales = df_completados["monto_aprobado"].sum() / 1_000_000 if not df_completados.empty else 0

            # Calculate pending amount
            estados_pendientes = ["enviado", "pendiente", "revision"]
            df_pendientes = df_full[df_full["estado"].str.strip().str.lower().isin(estados_pendientes)]
            monto_pendiente = df_pendientes["monto_propuesto"].sum() / 1_000_000 if not df_pendientes.empty else 0

            # Financial ratios and performance metrics
            approval_rate = (approved_amount / total_amount * 100) if total_amount > 0 else 0
            payment_rate = (completed_projects / total_edps * 100) if total_edps > 0 else 0
            completion_rate = (completed_projects / total_edps * 100) if total_edps > 0 else 0

            # Calculate meta ingresos based on total proposed amount
            meta_ingresos = total_amount * 0.85 / 1_000_000  # 85% target conversion rate
            vs_meta_ingresos = ((ingresos_totales - meta_ingresos) / meta_ingresos * 100) if meta_ingresos > 0 else 0
            pct_meta_ingresos = (ingresos_totales / meta_ingresos * 100) if meta_ingresos > 0 else 0

            # Calculate DSO metrics
            overall_dso = self._calculate_dso(df_full)
            dso_benchmark = 35.0  # Industry standard
            dso_target_progress = (dso_benchmark / max(1, overall_dso) * 100) if overall_dso > 0 else 0

            # Calculate critical projects (projects with high DSO or high value at risk)
            critical_projects_count = self._calculate_critical_projects_count(df_full)
            critical_amount = self._calculate_critical_amount(df_full)

            # Calculate aging metrics
            aging_metrics = self._calculate_aging_metrics_comprehensive(df_full)

            # Calculate forecast accuracy based on completion vs. initial projections
            forecast_accuracy = self._calculate_forecast_accuracy(df_full)

            # Calculate efficiency metrics
            efficiency_score = self._calculate_efficiency_score(df_full, approval_rate, payment_rate, overall_dso)
            quality_score = self._calculate_quality_score(df_full, approval_rate, completion_rate)

            # Calculate ROI based on revenue vs costs
            roi_promedio = self._calculate_roi_promedio(df_full, ingresos_totales)

            # Calculate satisfaction based on project success metrics
            satisfaccion_cliente = self._calculate_client_satisfaction(df_full, completion_rate, overall_dso)

            # Calculate progress towards objectives
            progreso_objetivo = self._calculate_progress_towards_objectives(df_full, completion_rate, ingresos_totales, meta_ingresos)

            # Calculate forecast metrics for next 7 days
            forecast_metrics = self._calculate_forecast_metrics(df_full)

            # Calculate growth metrics
            crecimiento_ingresos = self._calculate_revenue_growth(df_full)

            # Calculate run rate
            run_rate_anual = ingresos_totales * 12 if ingresos_totales > 0 else 0

            # Calculate budget variance
            presupuesto_anual = total_amount / 1_000_000
            variacion_presupuesto = ((ingresos_totales - presupuesto_anual) / presupuesto_anual * 100) if presupuesto_anual > 0 else 0

            essential_kpis = {
                # Financial KPIs - All calculated from real data
                "ingresos_totales": round(ingresos_totales, 1),
                "monto_pendiente": round(monto_pendiente, 1),
                "meta_ingresos": round(meta_ingresos, 1),
                "run_rate_anual": round(run_rate_anual, 1),
                "vs_meta_ingresos": round(vs_meta_ingresos, 1),
                "pct_meta_ingresos": round(min(pct_meta_ingresos, 100), 1),
                "crecimiento_ingresos": round(crecimiento_ingresos, 1),
                "variacion_presupuesto": round(variacion_presupuesto, 1),
                "historial_6_meses": [],  # Will be populated with real historical data when available
                
                # Basic operational KPIs
                "total_edps": total_edps,
                "total_approved": completed_projects,
                "total_pending": pending_count,
                "proyectos_completados": completed_projects,
                "approval_rate": round(approval_rate, 1),
                "payment_rate": round(payment_rate, 1),
                "completion_rate": round(completion_rate, 1),
                
                # DSO and performance metrics
                "dso": round(overall_dso, 1),
                "dso_actual": round(overall_dso, 1),
                "dso_benchmark": dso_benchmark,
                "dso_target_progress": round(dso_target_progress, 1),
                
                # Critical projects and risk metrics
                "critical_projects_count": critical_projects_count,
                "critical_amount": round(critical_amount, 1),
                "critical_projects_change": 0.0,  # Will be calculated with historical data
                
                # Aging metrics
                **aging_metrics,
                
                # Quality and efficiency metrics
                "forecast_accuracy": round(forecast_accuracy, 1),
                "efficiency_score": round(efficiency_score, 1),
                "quality_score": round(quality_score, 1),
                
                # Client and satisfaction metrics
                "roi_promedio": round(roi_promedio, 1),
                "satisfaccion_cliente": round(satisfaccion_cliente, 1),
                "progreso_objetivo": round(progreso_objetivo, 1),
                "objetivo_anual": round(meta_ingresos * 12, 1),  # Annual target based on monthly meta
                
                # Forecast metrics
                **forecast_metrics,
                
                # Additional metrics for template compatibility
                "client_satisfaction": round(satisfaccion_cliente, 1),
                "forecast_year": round(run_rate_anual, 1),
                "tendencia_pendiente": round(self._calculate_pending_trend(df_full), 1),
            }

            return ServiceResponse(
                success=True,
                data=self._sanitize_for_json(essential_kpis),
                message="Essential KPIs calculated successfully"
            )
        except Exception as e:
            logger.error(f"Error calculating essential KPIs: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error calculating essential KPIs: {str(e)}",
                data=self.get_empty_manager_kpis()
            )

    def _calculate_critical_projects_count(self, df: pd.DataFrame) -> int:
        """Calculate number of critical projects using centralized business rules."""
        try:
            if df.empty or 'dso_actual' not in df.columns or 'estado' not in df.columns:
                return 0
            
            # Use centralized business rules
            critical_count = 0
            for _, row in df.iterrows():
                dso_actual = row.get('dso_actual', 0)
                estado = row.get('estado', '')
                
                if es_critico(dso_actual, estado):
                    critical_count += 1
            
            return critical_count
        except Exception as e:
            logger.error(f"Error calculating critical projects count: {str(e)}")
            return 0

    def _calculate_critical_amount(self, df: pd.DataFrame) -> float:
        """Calculate total amount at risk in critical projects using centralized business rules."""
        try:
            if df.empty or 'dso_actual' not in df.columns or 'monto_propuesto' not in df.columns or 'estado' not in df.columns:
                return 0.0
            
            # Use centralized business rules
            critical_amount = 0.0
            for _, row in df.iterrows():
                dso_actual = row.get('dso_actual', 0)
                estado = row.get('estado', '')
                
                if es_critico(dso_actual, estado):
                    monto = pd.to_numeric(row.get('monto_propuesto', 0), errors='coerce')
                    if pd.notna(monto):
                        critical_amount += float(monto)
            
            return critical_amount  # Return in original units, will be converted to millions later
        except Exception as e:
            logger.error(f"Error calculating critical amount: {str(e)}")
            return 0.0

    def _calculate_aging_metrics_comprehensive(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive aging metrics using dso_actual from database."""
        try:
            if df.empty or 'dso_actual' not in df.columns:
                return self._get_empty_aging_metrics()
            
            # Use dso_actual for aging calculation
            df_with_days = df.copy()
            df_with_days['days_numeric'] = pd.to_numeric(df_with_days['dso_actual'], errors='coerce').fillna(0)
            
            # Filter out rows with 0 days for more accurate aging calculation
            df_valid_days = df_with_days[df_with_days['days_numeric'] > 0]
            
            if df_valid_days.empty:
                return self._get_empty_aging_metrics()
            
            # Calculate aging buckets based on DSO
            aging_0_30 = df_valid_days[df_valid_days['days_numeric'] <= 30]
            aging_31_60 = df_valid_days[(df_valid_days['days_numeric'] > 30) & (df_valid_days['days_numeric'] <= 60)]
            aging_61_90 = df_valid_days[(df_valid_days['days_numeric'] > 60) & (df_valid_days['days_numeric'] <= 90)]
            aging_90_plus = df_valid_days[df_valid_days['days_numeric'] > 90]
            
            total_projects = len(df_valid_days)
            
            # Calculate percentages
            pct_30d = (len(aging_0_30) / total_projects * 100) if total_projects > 0 else 0
            pct_60d = (len(aging_31_60) / total_projects * 100) if total_projects > 0 else 0
            pct_90d = (len(aging_61_90) / total_projects * 100) if total_projects > 0 else 0
            pct_mas90d = (len(aging_90_plus) / total_projects * 100) if total_projects > 0 else 0
            
            # Calculate amounts using monto_propuesto
            aging_31_60_amount = 0.0
            fast_collection_amount = 0.0
            
            if 'monto_propuesto' in df.columns:
                aging_31_60_amount = aging_31_60['monto_propuesto'].sum() / 1_000_000 if not aging_31_60.empty else 0
                fast_collection_amount = aging_0_30['monto_propuesto'].sum() / 1_000_000 if not aging_0_30.empty else 0
            
            print(f"📊 Aging calculation using dso_actual: Total projects with valid DSO: {total_projects}")
            print(f"   0-30 days DSO: {len(aging_0_30)} projects ({pct_30d:.1f}%)")
            print(f"   31-60 days DSO: {len(aging_31_60)} projects ({pct_60d:.1f}%)")
            print(f"   61-90 days DSO: {len(aging_61_90)} projects ({pct_90d:.1f}%)")
            print(f"   90+ days DSO: {len(aging_90_plus)} projects ({pct_mas90d:.1f}%)")
            
            return {
                "aging_31_60_count": len(aging_31_60),
                "aging_31_60_amount": round(aging_31_60_amount, 1),
                "aging_31_60_change": 0.0,  # Will be calculated with historical data
                "fast_collection_count": len(aging_0_30),
                "fast_collection_amount": round(fast_collection_amount, 1),
                "fast_collection_change": 0.0,  # Will be calculated with historical data
                "pct_30d": round(pct_30d, 1),
                "pct_60d": round(pct_60d, 1),
                "pct_90d": round(pct_90d, 1),
                "pct_mas90d": round(pct_mas90d, 1),
            }
        except Exception as e:
            logger.error(f"Error calculating aging metrics: {str(e)}")
            return self._get_empty_aging_metrics()

    def _get_empty_aging_metrics(self) -> Dict[str, Any]:
        """Return empty aging metrics structure."""
        return {
            "aging_31_60_count": 0,
            "aging_31_60_amount": 0.0,
            "aging_31_60_change": 0.0,
            "fast_collection_count": 0,
            "fast_collection_amount": 0.0,
            "fast_collection_change": 0.0,
            "pct_30d": 0.0,
            "pct_60d": 0.0,
            "pct_90d": 0.0,
            "pct_mas90d": 0.0,
        }

    def _calculate_efficiency_score(self, df: pd.DataFrame, approval_rate: float, payment_rate: float, dso: float) -> float:
        """Calculate overall efficiency score based on multiple factors."""
        try:
            if df.empty:
                return 0.0
            
            # Efficiency components
            approval_efficiency = min(100, approval_rate)  # Max 100%
            payment_efficiency = min(100, payment_rate)    # Max 100%
            
            # DSO efficiency (inverse relationship - lower DSO is better)
            dso_benchmark = 35.0
            dso_efficiency = max(0, min(100, (dso_benchmark / max(1, dso)) * 100)) if dso > 0 else 0
            
            # Time efficiency based on project completion times
            time_efficiency = self._calculate_time_efficiency(df)
            
            # Weighted average efficiency score
            efficiency_score = (
                approval_efficiency * 0.3 +    # 30% weight
                payment_efficiency * 0.3 +     # 30% weight
                dso_efficiency * 0.25 +        # 25% weight
                time_efficiency * 0.15         # 15% weight
            )
            
            return min(100, max(0, efficiency_score))
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {str(e)}")
            return 0.0

    def _calculate_time_efficiency(self, df: pd.DataFrame) -> float:
        """Calculate time efficiency based on DSO actual from database."""
        try:
            if df.empty or 'dso_actual' not in df.columns:
                return 75.0  # Default efficiency when no data
            
            # Use dso_actual for time calculation
            dso_numeric = pd.to_numeric(df['dso_actual'], errors='coerce').dropna()
            
            if len(dso_numeric) == 0:
                return 75.0
            
            avg_dso = dso_numeric.mean()
            target_dso = 30.0  # Target DSO
            
            # Calculate efficiency (inverse relationship - lower DSO is better)
            time_efficiency = max(0, min(100, (target_dso / max(1, avg_dso)) * 100))
            
            return time_efficiency
        except Exception as e:
            logger.error(f"Error calculating time efficiency: {str(e)}")
            return 75.0

    def _calculate_quality_score(self, df: pd.DataFrame, approval_rate: float, completion_rate: float) -> float:
        """Calculate quality score based on approval and completion rates."""
        try:
            if df.empty:
                return 0.0
            
            # Quality components
            approval_quality = min(100, approval_rate)
            completion_quality = min(100, completion_rate)
            
            # Rejection rate (inverse quality indicator)
            rejected_states = ['rechazado', 'devuelto', 'revision']
            rejected_count = len(df[df['estado'].str.strip().str.lower().isin(rejected_states)])
            rejection_rate = (rejected_count / len(df) * 100) if len(df) > 0 else 0
            rejection_quality = max(0, 100 - rejection_rate)
            
            # Weighted quality score
            quality_score = (
                approval_quality * 0.4 +      # 40% weight
                completion_quality * 0.4 +    # 40% weight
                rejection_quality * 0.2       # 20% weight
            )
            
            return min(100, max(0, quality_score))
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 0.0

    def _calculate_roi_promedio(self, df: pd.DataFrame, ingresos_totales: float) -> float:
        """Calculate average ROI based on revenue vs investment."""
        try:
            if df.empty or ingresos_totales == 0:
                return 0.0
            
            # Estimate investment as a percentage of total proposed amount
            total_proposed = df['monto_propuesto'].sum() / 1_000_000 if 'monto_propuesto' in df.columns else 0
            
            if total_proposed == 0:
                return 0.0
            
            # Assume operational costs are 65% of revenue
            operational_costs = ingresos_totales * 0.65
            
            # Calculate net profit
            net_profit = ingresos_totales - operational_costs
            
            # ROI = (Net Profit / Investment) * 100
            roi = (net_profit / total_proposed * 100) if total_proposed > 0 else 0
            
            return max(0, roi)
        except Exception as e:
            logger.error(f"Error calculating ROI: {str(e)}")
            return 0.0

    def _calculate_client_satisfaction(self, df: pd.DataFrame, completion_rate: float, dso: float) -> float:
        """Calculate client satisfaction based on performance metrics."""
        try:
            if df.empty:
                return 0.0
            
            # Satisfaction factors
            completion_satisfaction = min(100, completion_rate)
            
            # DSO satisfaction (inverse relationship)
            dso_benchmark = 35.0
            dso_satisfaction = max(0, min(100, (dso_benchmark / max(1, dso)) * 100)) if dso > 0 else 0
            
            # On-time delivery satisfaction
            on_time_projects = self._calculate_projects_on_time(df)
            on_time_satisfaction = min(100, on_time_projects)
            
            # Quality satisfaction (based on rejection rate)
            rejected_states = ['rechazado', 'devuelto']
            rejected_count = len(df[df['estado'].str.strip().str.lower().isin(rejected_states)])
            rejection_rate = (rejected_count / len(df) * 100) if len(df) > 0 else 0
            quality_satisfaction = max(0, 100 - rejection_rate * 2)  # Double penalty for rejections
            
            # Weighted satisfaction score
            satisfaction = (
                completion_satisfaction * 0.3 +   # 30% weight
                dso_satisfaction * 0.25 +         # 25% weight
                on_time_satisfaction * 0.25 +     # 25% weight
                quality_satisfaction * 0.2        # 20% weight
            )
            
            return min(100, max(0, satisfaction))
        except Exception as e:
            logger.error(f"Error calculating client satisfaction: {str(e)}")
            return 0.0

    def _calculate_progress_towards_objectives(self, df: pd.DataFrame, completion_rate: float, ingresos_totales: float, meta_ingresos: float) -> float:
        """Calculate progress towards annual objectives."""
        try:
            if df.empty:
                return 0.0
            
            # Revenue progress
            revenue_progress = (ingresos_totales / meta_ingresos * 100) if meta_ingresos > 0 else 0
            
            # Completion progress
            completion_progress = min(100, completion_rate)
            
            # DSO progress
            dso = self._calculate_dso(df)
            dso_benchmark = 35.0
            dso_progress = max(0, min(100, (dso_benchmark / max(1, dso)) * 100)) if dso > 0 else 0
            
            # Overall progress (weighted average)
            overall_progress = (
                revenue_progress * 0.5 +      # 50% weight
                completion_progress * 0.3 +   # 30% weight
                dso_progress * 0.2           # 20% weight
            )
            
            return min(100, max(0, overall_progress))
        except Exception as e:
            logger.error(f"Error calculating progress towards objectives: {str(e)}")
            return 0.0

    def _calculate_forecast_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate forecast metrics for the next 7 days."""
        try:
            if df.empty:
                return {
                    "forecast_7_dias": 0.0,
                    "forecast_day_1": 0.0,
                    "forecast_day_2": 0.0,
                    "forecast_day_3": 0.0,
                    "forecast_day_4": 0.0,
                    "forecast_day_5": 0.0,
                    "forecast_day_6": 0.0,
                    "forecast_day_7": 0.0,
                    "meta_gap": 0.0,
                    "days_remaining": 0,
                }
            
            # Calculate daily forecast based on pending projects and their probability
            pending_states = ['enviado', 'validado', 'pendiente', 'revision']
            df_pending = df[df['estado'].str.strip().str.lower().isin(pending_states)]
            
            print(f"📊 Forecast calculation: {len(df_pending)} pending projects from {len(df)} total")
            
            if df_pending.empty:
                print("⚠️ No pending projects found for forecast")
                return {
                    "forecast_7_dias": 0.0,
                    "forecast_day_1": 0.0,
                    "forecast_day_2": 0.0,
                    "forecast_day_3": 0.0,
                    "forecast_day_4": 0.0,
                    "forecast_day_5": 0.0,
                    "forecast_day_6": 0.0,
                    "forecast_day_7": 0.0,
                    "meta_gap": 0.0,
                    "days_remaining": 30,  # Default month remaining
                }
            
            # Calculate probability of payment based on project age and status
            total_pending_amount = 0
            if 'monto_propuesto' in df_pending.columns:
                total_pending_amount = pd.to_numeric(df_pending['monto_propuesto'], errors='coerce').sum() / 1_000_000
            elif 'monto_aprobado' in df_pending.columns:
                total_pending_amount = pd.to_numeric(df_pending['monto_aprobado'], errors='coerce').sum() / 1_000_000
            
            print(f"📊 Total pending amount: {total_pending_amount:.1f}M CLP")
            
            # Distribute forecast across 7 days with realistic probabilities based on status
            # Higher probability for projects closer to completion
            
            validated_df = df_pending[df_pending['estado'].str.strip().str.lower() == 'validado']
            sent_df = df_pending[df_pending['estado'].str.strip().str.lower() == 'enviado']
            pending_df = df_pending[df_pending['estado'].str.strip().str.lower().isin(['pendiente', 'revision'])]
            
            validated_amount = 0
            sent_amount = 0
            pending_amount = 0
            
            if not validated_df.empty and 'monto_propuesto' in validated_df.columns:
                validated_amount = pd.to_numeric(validated_df['monto_propuesto'], errors='coerce').sum() / 1_000_000
            if not sent_df.empty and 'monto_propuesto' in sent_df.columns:
                sent_amount = pd.to_numeric(sent_df['monto_propuesto'], errors='coerce').sum() / 1_000_000
            if not pending_df.empty and 'monto_propuesto' in pending_df.columns:
                pending_amount = pd.to_numeric(pending_df['monto_propuesto'], errors='coerce').sum() / 1_000_000
            
            print(f"   Validated: {validated_amount:.1f}M, Sent: {sent_amount:.1f}M, Pending: {pending_amount:.1f}M")
            
            # Daily forecast distribution based on realistic conversion probabilities
            forecast_day_1 = validated_amount * 0.4 + sent_amount * 0.1  # 40% validated, 10% sent
            forecast_day_2 = validated_amount * 0.3 + sent_amount * 0.15  # 30% validated, 15% sent
            forecast_day_3 = validated_amount * 0.2 + sent_amount * 0.2   # 20% validated, 20% sent
            forecast_day_4 = validated_amount * 0.1 + sent_amount * 0.2   # 10% validated, 20% sent
            forecast_day_5 = sent_amount * 0.25 + pending_amount * 0.1    # 25% sent, 10% pending
            forecast_day_6 = sent_amount * 0.1 + pending_amount * 0.15    # 10% sent, 15% pending
            forecast_day_7 = pending_amount * 0.1                         # 10% pending
            
            forecast_7_dias = forecast_day_1 + forecast_day_2 + forecast_day_3 + forecast_day_4 + forecast_day_5 + forecast_day_6 + forecast_day_7
            
            # Calculate meta gap using the real monthly target (1,200M CLP)
            monthly_target = 1200.0  # 1,200M CLP monthly target
            meta_gap = max(0, monthly_target - forecast_7_dias)
            
            # Days remaining in current month
            from datetime import datetime
            today = datetime.now()
            import calendar
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            days_remaining = max(0, days_in_month - today.day)
            
            print(f"📊 Forecast 7 days: {forecast_7_dias:.1f}M CLP")
            print(f"📊 Meta gap: {meta_gap:.1f}M CLP (target: {monthly_target}M)")
            
            return {
                "forecast_7_dias": round(forecast_7_dias, 1),
                "forecast_day_1": round(forecast_day_1, 1),
                "forecast_day_2": round(forecast_day_2, 1),
                "forecast_day_3": round(forecast_day_3, 1),
                "forecast_day_4": round(forecast_day_4, 1),
                "forecast_day_5": round(forecast_day_5, 1),
                "forecast_day_6": round(forecast_day_6, 1),
                "forecast_day_7": round(forecast_day_7, 1),
                "meta_gap": round(meta_gap, 1),
                "days_remaining": days_remaining,
            }
        except Exception as e:
            logger.error(f"Error calculating forecast metrics: {str(e)}")
            return {
                "forecast_7_dias": 0.0,
                "forecast_day_1": 0.0,
                "forecast_day_2": 0.0,
                "forecast_day_3": 0.0,
                "forecast_day_4": 0.0,
                "forecast_day_5": 0.0,
                "forecast_day_6": 0.0,
                "forecast_day_7": 0.0,
                "meta_gap": 0.0,
                "days_remaining": 0,
            }

    def _calculate_revenue_growth(self, df: pd.DataFrame) -> float:
        """Calculate revenue growth rate based on historical data."""
        try:
            if df.empty or 'fecha_modificacion' not in df.columns:
                return 0.0
            
            # Ensure date column is datetime
            df = self._ensure_date_columns(df)
            
            # Filter completed projects
            completed_states = ['pagado', 'validado']
            df_completed = df[df['estado'].str.strip().str.lower().isin(completed_states)]
            
            if df_completed.empty:
                return 0.0
            
            # Group by month and calculate revenue
            df_completed['year_month'] = df_completed['fecha_modificacion'].dt.to_period('M')
            monthly_revenue = df_completed.groupby('year_month')['monto_aprobado'].sum()
            
            if len(monthly_revenue) < 2:
                return 0.0
            
            # Calculate growth rate between most recent months
            recent_months = monthly_revenue.tail(2)
            if len(recent_months) == 2:
                current_month = recent_months.iloc[-1]
                previous_month = recent_months.iloc[-2]
                
                if previous_month > 0:
                    growth_rate = ((current_month - previous_month) / previous_month * 100)
                    return growth_rate
            
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating revenue growth: {str(e)}")
            return 0.0

    def _calculate_pending_trend(self, df: pd.DataFrame) -> float:
        """Calculate trend in pending amounts."""
        try:
            if df.empty or 'fecha_creacion' not in df.columns:
                return 0.0
            
            # Ensure date column is datetime
            df = self._ensure_date_columns(df)
            
            # Filter pending projects
            pending_states = ['enviado', 'pendiente', 'revision']
            df_pending = df[df['estado'].str.strip().str.lower().isin(pending_states)]
            
            if df_pending.empty:
                return 0.0
            
            # Group by month and calculate pending amounts
            df_pending['year_month'] = df_pending['fecha_creacion'].dt.to_period('M')
            monthly_pending = df_pending.groupby('year_month')['monto_propuesto'].sum()
            
            if len(monthly_pending) < 2:
                return 0.0
            
            # Calculate trend between most recent months
            recent_months = monthly_pending.tail(2)
            if len(recent_months) == 2:
                current_month = recent_months.iloc[-1]
                previous_month = recent_months.iloc[-2]
                
                if previous_month > 0:
                    trend = ((current_month - previous_month) / previous_month * 100)
                    return trend
            
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating pending trend: {str(e)}")
            return 0.0

    def _ensure_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure date columns are properly formatted."""
        try:
            df = df.copy()
            # Map database column names to expected names
            date_columns_mapping = {
                'created_at': 'fecha_creacion',
                'updated_at': 'fecha_modificacion', 
                'fecha_ultimo_seguimiento': 'fecha_ultimo_seguimiento'
            }
            
            # Create mapped columns if they don't exist
            for db_col, expected_col in date_columns_mapping.items():
                if db_col in df.columns and expected_col not in df.columns:
                    df[expected_col] = pd.to_datetime(df[db_col], errors='coerce')
                elif expected_col in df.columns:
                    df[expected_col] = pd.to_datetime(df[expected_col], errors='coerce')
            
            # Also ensure original columns are datetime
            all_date_columns = ['created_at', 'updated_at', 'fecha_ultimo_seguimiento', 
                              'fecha_creacion', 'fecha_modificacion', 'fecha_emision', 
                              'fecha_envio_cliente', 'fecha_estimada_pago', 'fecha_conformidad']
            
            for col in all_date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
        except Exception as e:
            logger.error(f"Error ensuring date columns: {str(e)}")
            return df

    def get_empty_manager_kpis(self) -> Dict[str, Any]:
        """Return empty KPI structure for manager dashboard that includes all components."""
        # Start with existing empty structure
        empty_kpis = {
            # Financial KPIs that match template
            "ingresos_totales": 0.0,
            "monto_pendiente": 0.0,
            "meta_ingresos": 0.0,
            "run_rate_anual": 0.0,
            "vs_meta_ingresos": 0.0,
            "pct_meta_ingresos": 0.0,
            "crecimiento_ingresos": 0.0,
            "tendencia_pendiente": 0.0,
            "historial_6_meses": [],
            
            # Template-specific KPIs that the dashboard uses
            "roi_promedio": 0.0,
            "proyectos_completados": 0,
            "satisfaccion_cliente": 0.0,
            "progreso_objetivo": 0.0,
            "objetivo_anual": 0.0,
            "score_equipo": 0,
            "efficiency_score": 0.0,
            "critical_projects_count": 0,
            "total_edps": 0,
            
            # DSO and target progress metrics for template
            "dso_actual": 0.0,
            "dso_target_progress": 0.0,
            "quality_score": 0.0,
            
            # Critical project metrics
            "critical_projects_change": 0.0,
            "critical_amount": 0.0,
            
            # Aging metrics
            "aging_31_60_count": 0,
            "aging_31_60_change": 0.0,
            "aging_31_60_amount": 0.0,
            
            # Fast collection metrics
            "fast_collection_count": 0,
            "fast_collection_change": 0.0,
            "fast_collection_amount": 0.0,
            
            # Target and gap metrics
            "meta_gap": 0.0,
            "days_remaining": 0,
            
            # Forecast metrics (7-day forecast)
            "forecast_7_dias": 0.0,
            "forecast_day_1": 0.0,
            "forecast_day_2": 0.0,
            "forecast_day_3": 0.0,
            "forecast_day_4": 0.0,
            "forecast_day_5": 0.0,
            "forecast_day_6": 0.0,
            "forecast_day_7": 0.0,
            "forecast_accuracy": 0.0,
            "forecast_growth": 0.0,
            "forecast_confidence": 0.0,
            
            # Advanced DSO and payment metrics
            "dso": 0.0,
            "dso_cliente_principal": 0.0,
            "dso_by_client": {},
            "dso_by_project_type": {},
            "dso_by_project_manager": {},
            "dso_trend_3m": 0.0,
            "dso_trend_6m": 0.0,
            "dso_benchmark": 35.0,
            "dso_vs_benchmark": 0.0,
            "dso_vs_target": 0.0,
            "payment_velocity": 0.0,
            "payment_velocity_trend": "sin_datos",
            "payment_acceleration": 0.0,
            "pct_ingresos_principal": 0.0,
            "riesgo_pago_principal": 0.0,
            "tendencia_pago_principal": "sin_datos",
        }
        
        # Add all new executive dashboard KPIs
        empty_kpis.update(self.get_empty_executive_kpis())
        
        return empty_kpis

    def _prepare_kpi_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for KPI calculations."""
        try:
            if df.empty:
                return df
            
            # Ensure required columns exist and have proper data types
            required_columns = ['monto_propuesto', 'estado', 'dso_actual']
            
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"Column {col} not found in dataframe")
                    if col == 'monto_propuesto':
                        df[col] = 0
                    elif col == 'estado':
                        df[col] = 'pendiente'
                    elif col == 'dso_actual':
                        df[col] = 0
            
            # Convert numeric columns
            numeric_columns = ['monto_propuesto', 'dso_actual']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Clean estado column
            if 'estado' in df.columns:
                df['estado'] = df['estado'].astype(str).str.strip().str.lower()
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing KPI data: {str(e)}")
            return df
          

    def _prepare_kpi_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for KPI calculations."""
        if df.empty:
            return df

        df = df.copy()

        # Ensure numeric columns
        numeric_columns = ["monto_propuesto", "monto_aprobado"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Ensure date columns
        date_columns = ["fecha_creacion", "fecha_modificacion"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Clean status column
        if "estado" in df.columns:
            df["estado"] = df["estado"].astype(str).str.strip().str.lower()

        return df

    def _calculate_financial_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate financial KPIs matching manager dashboard template requirements."""
        try:
            if df.empty:
                return {}

            # Basic financial calculations
            total_proposed = df["monto_propuesto"].sum() if "monto_propuesto" in df.columns else 0
            
            # CORREGIDO: Calcular ingresos totales de EDPs completados/pagados
            # Usar múltiples estados para capturar todos los ingresos realizados
            estados_completados = ["pagado"]
            df_completados = df[df["estado"].str.strip().str.lower().isin([e.lower() for e in estados_completados])]
            
            total_paid = 0
            if not df_completados.empty and "monto_aprobado" in df_completados.columns:
                # Usar monto_aprobado para EDPs completados
                total_paid = df_completados["monto_aprobado"].sum()
            
            # Si no hay monto_aprobado o está vacío, usar monto_propuesto como fallback
            if total_paid == 0 and not df_completados.empty and "monto_propuesto" in df_completados.columns:
                total_paid = df_completados["monto_propuesto"].sum()
                
            # Si aún está en 0, usar una estimación basada en el total de EDPs
            if total_paid == 0 and total_proposed > 0:
                # Estimar que al menos el 70% del monto propuesto se ha realizado
                total_paid = total_proposed * 0.7
                logger.info(f"Using estimated revenue: {total_paid} from proposed: {total_proposed}")

            # Calcular pendientes
            estados_pendientes = ["enviado", "revisión", "pendiente", "en_proceso"]
            df_pendientes = df[df["estado"].str.strip().str.lower().isin([e.lower() for e in estados_pendientes])]
            
            pending_amount = 0
            if not df_pendientes.empty:
                if "monto_propuesto" in df_pendientes.columns:
                    pending_amount = df_pendientes["monto_propuesto"].sum()
                elif "monto_aprobado" in df_pendientes.columns:
                    pending_amount = df_pendientes["monto_aprobado"].sum()

            # Calculate target and performance metrics - USE REAL TARGET
            meta_ingresos = 1200.0  # 1,200M CLP monthly target (FIXED)
            meta_ingresos_clp = meta_ingresos * 1_000_000  # Convert to CLP for calculations
            
            ingresos_totales_clp = total_paid
            ingresos_totales_m = ingresos_totales_clp / 1_000_000  # Convert to millions for display
            
            vs_meta_ingresos = (
                ((ingresos_totales_m - meta_ingresos) / meta_ingresos * 100)
                if meta_ingresos > 0 else 0
            )
            pct_meta_ingresos = (
                (ingresos_totales_m / meta_ingresos * 100) if meta_ingresos > 0 else 0
            )

            # Growth calculations (real data only)
            crecimiento_ingresos = 0.0  # No growth calculation without historical data
            tendencia_pendiente = 0.0  # No trend calculation without historical data

            # Format values to match template expectations (in millions)
            monto_pendiente = round(pending_amount / 1_000_000, 1)
            run_rate_anual = round(ingresos_totales_m * 12, 1)

            # Historical 6 months (real data only)
            historial_6_meses = []  # Empty without real historical data

            logger.info(f"Calculated financial KPIs - Total Revenue: {total_paid:,.0f} CLP ({ingresos_totales_m} M)")
            logger.info(f"Completed EDPs: {len(df_completados)}, Pending Amount: {pending_amount:,.0f} CLP")
            logger.info(f"Meta: {meta_ingresos}M CLP, Achievement: {pct_meta_ingresos:.1f}%")

            return {
                "ingresos_totales": round(ingresos_totales_m, 1),
                "monto_pendiente": monto_pendiente,
                "meta_ingresos": meta_ingresos,  # Real target in millions
                "run_rate_anual": run_rate_anual,
                "vs_meta_ingresos": round(vs_meta_ingresos, 1),
                "pct_meta_ingresos": min(round(pct_meta_ingresos, 1), 100),
                "crecimiento_ingresos": crecimiento_ingresos,
                "tendencia_pendiente": tendencia_pendiente,
                "historial_6_meses": historial_6_meses,
            }

        except Exception as e:
            logger.error(f"Error calculating financial KPIs: {str(e)}")
            return {}

    def _calculate_operational_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate operational KPIs matching manager dashboard template requirements."""
        try:
            if df.empty:
                return {}

            # Basic counts
            total_edps = len(df)
            total_approved = len(df[df["estado"] == 'pagado' ])
            total_pending = len(
                df[df["estado"].isin(["enviado", "revisión", "pendiente","validado"])]
            )

            # Critical EDPs - ENSURE this is calculated and included
            critical_projects_count = self._calculate_critical_projects_count(df)
            critical_amount = self._calculate_critical_amount(df)

            # DSO calculations - ENSURE dso_actual is included
            try:
                dso = self._calculate_dso(df)
                dso_actual = dso  # Make sure dso_actual is explicitly set
                dso_cliente_principal = 0.0  # No client-specific DSO without real data
            except Exception as e:
                logger.info(f"Error calculating DSO: {e}")
                dso = 0.0  # No DSO without real data
                dso_actual = 0.0  # Explicit dso_actual
                dso_cliente_principal = 0.0

            # Client analysis (real data only)
            pct_ingresos_principal = 0.0  # No client analysis without real data
            riesgo_pago_principal = 0.0   # No risk analysis without real data
            tendencia_pago_principal = "sin_datos"  # No trend without real data

            # Calculate project timing KPIs
            try:
                proyectos_on_time = self._calculate_projects_on_time(df)
                proyectos_retrasados = self._calculate_projects_delayed(df)
            except Exception as e:
                logger.info(f"Error calculating project timing KPIs: {e}")
                proyectos_on_time = 0  # No timing data without real projects
                proyectos_retrasados = 0  # No timing data without real projects

            # Calculate efficiency score - ENSURE this is included
            approval_rate = (total_approved / total_edps * 100) if total_edps > 0 else 0
            payment_rate = (total_approved / total_edps * 100) if total_edps > 0 else 0
            efficiency_score = self._calculate_efficiency_score(df, approval_rate, payment_rate, dso_actual)

            # Calculate forecast accuracy - ENSURE this is included
            forecast_accuracy = self._calculate_forecast_accuracy(df)

            return {
                "total_edps": total_edps,
                "total_approved": total_approved,
                "total_pending": total_pending,
                "approval_rate": round(approval_rate, 1),
                
                # CRITICAL FIELDS - explicitly included
                "dso_actual": round(dso_actual, 1),  # Explicit dso_actual field
                "critical_projects_count": critical_projects_count,  # Explicit critical projects count
                "efficiency_score": round(efficiency_score, 1),  # Explicit efficiency score
                "forecast_accuracy": round(forecast_accuracy, 1),  # Explicit forecast accuracy
                
                # Legacy fields for compatibility
                "critical_edps": critical_projects_count,  # Legacy name
                "critical_amount": round(critical_amount, 1),
                "dso": round(dso, 1),  # Legacy DSO field
                
                # Client metrics
                "dso_cliente_principal": round(dso_cliente_principal, 1),
                "pct_ingresos_principal": pct_ingresos_principal,
                "riesgo_pago_principal": riesgo_pago_principal,
                "tendencia_pago_principal": tendencia_pago_principal,
                
                # Project timing
                "proyectos_on_time": proyectos_on_time,
                "proyectos_retrasados": proyectos_retrasados,
            }

        except Exception as e:
            logger.error(f"Error calculating operational KPIs: {str(e)}")
            return {
                # Return at least the critical fields with default values
                "dso_actual": 0.0,
                "critical_projects_count": 0,
                "efficiency_score": 0.0,
                "forecast_accuracy": 0.0,
            }
    
    def _calculate_dso(self, df: pd.DataFrame) -> float:
        """Calculate Days Sales Outstanding using real DSO data from database."""
        try:
            # Use the real DSO data calculated automatically in the database
            if df.empty:
                return 0.0  # No DSO without real data
            
            # Check if we have the new DSO column from database
            if 'dso_actual' in df.columns:
                dso_values = pd.to_numeric(df['dso_actual'], errors='coerce')
                valid_dso = dso_values.dropna()
                
                if len(valid_dso) > 0:
                    # Calculate weighted average DSO (weighted by amount if available)
                    if 'monto_aprobado' in df.columns:
                        amounts = pd.to_numeric(df['monto_aprobado'], errors='coerce').fillna(0)
                        # Only use rows where both DSO and amount are valid
                        valid_mask = ~dso_values.isna() & (amounts > 0)
                        if valid_mask.sum() > 0:
                            weighted_dso = (dso_values[valid_mask] * amounts[valid_mask]).sum() / amounts[valid_mask].sum()
                            return round(weighted_dso, 1)
                    
                    # Simple average if no amounts or weighting fails
                    return round(valid_dso.mean(), 1)
            
            # Fallback to old calculation if DSO column not available
            # NOTE: dias_espera column doesn't exist in database, removed fallback
            return 0.0  # No DSO without real data
            
        except Exception as e:
            logger.error(f"Error calculating DSO: {e}")
            return 0.0

    def _calculate_projects_on_time(self, df: pd.DataFrame) -> int:
        """Calculate percentage of projects delivered on time using DSO actual."""
        try:
            if "dso_actual" not in df.columns or df.empty:
                return 0  # No data without real projects

            # Convert dso_actual to numeric
            dso_actual_validos = pd.to_numeric(df["dso_actual"], errors="coerce")
            
            # Filter valid values
            dso_validos = dso_actual_validos.dropna()
            
            if len(dso_validos) == 0:
                return 0  # No data if no valid data

            # Consider "on time" as <= 35 days DSO (industry benchmark)
            on_time_count = len(dso_validos[dso_validos <= 35])
            total_count = len(dso_validos)
            
            on_time_percentage = round((on_time_count / total_count * 100) if total_count > 0 else 0)
            
            # Ensure it's in range 0-100
            return max(0, min(100, on_time_percentage))
            
        except Exception as e:
            logger.error(f"Error calculating projects on time: {e}")
            return 0  # No data on error

    def _calculate_projects_delayed(self, df: pd.DataFrame) -> int:
        """Calculate percentage of projects that are delayed using DSO actual."""
        try:
            if "dso_actual" not in df.columns or df.empty:
                return 0  # No data without real projects

            # Convert dso_actual to numeric
            dso_actual_validos = pd.to_numeric(df["dso_actual"], errors="coerce")
            
            # Filter valid values
            dso_validos = dso_actual_validos.dropna()
            
            if len(dso_validos) == 0:
                return 0  # No data if no valid data

            # Consider "delayed" as > 60 days DSO (significantly beyond benchmark)
            delayed_count = len(dso_validos[dso_validos > 60])
            total_count = len(dso_validos)
            
            delayed_percentage = round((delayed_count / total_count * 100) if total_count > 0 else 0)
            
            # Ensure it's in range 0-100
            return max(0, min(100, delayed_percentage))
            
        except Exception as e:
            logger.error(f"Error calculating projects delayed: {e}")
            return 0  # No data on error

    def _calculate_profitability_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate profitability KPIs."""
        try:
            if df.empty:
                return {}

            # Calculate margin-related metrics
            total_revenue = df[df["estado"].isin(["pagado", "validado"])]["monto_aprobado"].sum()
            
            # Mock cost calculation (would be real in production)
            estimated_costs = total_revenue * 0.65  # Assume 65% cost ratio
            gross_profit = total_revenue - estimated_costs
            
            profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # ROI calculation (simplified)
            investment = df["monto_propuesto"].sum() * 0.1  # Assume 10% investment
            roi = (gross_profit / investment * 100) if investment > 0 else 0

            return {
                "gross_profit": round(gross_profit / 1_000_000, 1),
                "profit_margin": round(profit_margin, 1),
                "roi": round(roi, 1),
                "cost_efficiency": round(100 - (estimated_costs / total_revenue * 100), 1) if total_revenue > 0 else 0,
                "profitability_score": round((profit_margin + roi) / 2, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating profitability KPIs: {str(e)}")
            return {}

    def _calculate_aging_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate project aging KPIs."""
        try:
            if df.empty:
                return {}

            df = self._ensure_date_columns(df)
      
            
            # Calculate days since creation for each project
            df_age = df.copy()
   
            df_age["days_old"] = df_age['dso_actual']
            
            # Filter valid ages (remove negative or null ages)
            df_age = df_age[df_age["days_old"] >= 0]
            
            if df_age.empty:
                return {}
            
            # Count projects by age buckets
            projects_30_days = len(df_age[df_age["days_old"] <= 30])
            projects_60_days = len(df_age[(df_age["days_old"] > 30) & (df_age["days_old"] <= 60)])
            projects_90_days = len(df_age[df_age["days_old"] > 60])
            
            # Critical aging (projects over 90 days not completed)
            non_completed_states = ["enviado", "pendiente", "en_revision", "revision"]
            aging_critical = len(df_age[
                (df_age["days_old"] > 90) & 
                (df_age["estado"].str.strip().str.lower().isin(non_completed_states))
            ])

            print(f"📊 Aging KPI calculation: {len(df_age)} projects with valid dates")
            print(f"   0-30 days: {projects_30_days} projects")
            print(f"   31-60 days: {projects_60_days} projects") 
            print(f"   60+ days: {projects_90_days} projects")
            print(f"   Critical (90+ days pending): {aging_critical} projects")

            return {
                "projects_30_days": projects_30_days,
                "projects_60_days": projects_60_days,
                "projects_90_days": projects_90_days,
                "aging_critical": aging_critical,
                "avg_project_age": round(df_age["days_old"].mean(), 1) if not df_age.empty else 0,
                "aging_health_score": round(max(0, 100 - (aging_critical * 10)), 1)
            }
        except Exception as e:
            logger.error(f"Error calculating aging KPIs: {str(e)}")
            return {}

    def _calculate_efficiency_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate efficiency KPIs."""
        try:
            if df.empty:
                return {}

            # Calculate approval efficiency
            total_projects = len(df)
            approved_projects = len(df[df["estado"].isin(["pagado", "validado", "aprobado"])])
            approval_efficiency = (approved_projects / total_projects * 100) if total_projects > 0 else 0

            # Calculate time efficiency (mock calculation)
            avg_cycle_time = 25.5  # Would be calculated from actual dates
            target_cycle_time = 20.0
            time_efficiency = (target_cycle_time / avg_cycle_time * 100) if avg_cycle_time > 0 else 0

            # Calculate resource efficiency
            resource_utilization = 78.5  # Mock value

            overall_efficiency = (approval_efficiency + time_efficiency + resource_utilization) / 3

            return {
                "approval_efficiency": round(approval_efficiency, 1),
                "time_efficiency": round(time_efficiency, 1),
                "resource_utilization": round(resource_utilization, 1),
                "overall_efficiency": round(overall_efficiency, 1),
                "efficiency_trend": "improving"  # Would be calculated from historical data
            }
        except Exception as e:
            logger.error(f"Error calculating efficiency KPIs: {str(e)}")
            return {}

    def _calculate_critical_projects_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate critical projects KPIs."""
        try:
            if df.empty:
                return {}

            df = self._ensure_date_columns(df)
            
            # Define critical criteria
            high_value_threshold = df["monto_propuesto"].quantile(0.8)  # Top 20% by value
            old_threshold_days = 60

            current_date = datetime.now()
            df_critical = df.copy()
            
            # Use the correct date column for age calculation
            if 'fecha_creacion' in df_critical.columns:
                date_col = 'fecha_creacion'
            elif 'created_at' in df_critical.columns:
                date_col = 'created_at'
                df_critical['fecha_creacion'] = pd.to_datetime(df_critical[date_col], errors='coerce')
                date_col = 'fecha_creacion'
            else:
                logger.warning("No date column found for critical projects calculation")
                return {}
                
            df_critical["days_old"] = (current_date - df_critical[date_col]).dt.days
            
            # Filter valid ages
            df_critical = df_critical[df_critical["days_old"] >= 0]

            # Critical by value
            critical_by_value = df_critical[df_critical["monto_propuesto"] >= high_value_threshold]
            
            # Critical by age
            critical_by_age = df_critical[df_critical["days_old"] > old_threshold_days]
            
            # Critical by status (stuck projects)
            stuck_states = ["en_revision", "pendiente", "revision"]
            critical_by_status = df_critical[df_critical["estado"].str.strip().str.lower().isin(stuck_states)]

            # Combined critical projects
            critical_projects = pd.concat([critical_by_value, critical_by_age, critical_by_status]).drop_duplicates()

            critical_amount = critical_projects["monto_propuesto"].sum()

            print(f"📊 Critical projects calculation:")
            print(f"   By value (top 20%): {len(critical_by_value)} projects")
            print(f"   By age (>60 days): {len(critical_by_age)} projects")
            print(f"   By status (stuck): {len(critical_by_status)} projects")
            print(f"   Total critical: {len(critical_projects)} projects")

            return {
                "critical_projects_count": len(critical_projects),
                "critical_by_value": len(critical_by_value),
                "critical_by_age": len(critical_by_age),
                "critical_by_status": len(critical_by_status),
                "critical_total_amount": round(critical_amount / 1_000_000, 1),
                "critical_risk_score": round(len(critical_projects) / len(df) * 100, 1) if len(df) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating critical projects KPIs: {str(e)}")
            return {}

    def _sanitize_for_json(self, data):
        """Sanitize data for JSON serialization by converting numpy types and handling NaN values."""
        if isinstance(data, dict):
            return {key: self._sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, (np.int64, np.int32, np.int_)):
            return int(data)
        elif isinstance(data, (np.float64, np.float32, np.floating)):
            if np.isnan(data) or np.isinf(data):
                return None
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif pd.isna(data) or str(data) == "NaT":
            return None
        else:
            return data
    
    def _calculate_time_kpis(self, edp: EDP) -> Dict[str, Any]:
        """Calculate time-related KPIs."""
        kpis = {}
        
        now = datetime.now()
        
        # Days since creation
        days_since_creation = (now - edp.created_at).days
        kpis['days_since_creation'] = days_since_creation
        
        # Days since last update
        if edp.last_update:
            days_since_update = (now - edp.last_update).days
            kpis['days_since_last_update'] = days_since_update
        
        # Time efficiency (if dates are available)
        if edp.start_date and edp.end_date:
            planned_duration = (edp.end_date - edp.start_date).days
            
            if edp.status == 'completed':
                # Calculate actual duration
                actual_duration = days_since_creation
                time_efficiency = (planned_duration / actual_duration * 100) if actual_duration > 0 else 0
                kpis['time_efficiency'] = round(min(time_efficiency, 200), 2)  # Cap at 200%
            else:
                # Calculate progress against timeline
                elapsed_time = (now - edp.start_date).days if now > edp.start_date else 0
                expected_progress = (elapsed_time / planned_duration * 100) if planned_duration > 0 else 0
                kpis['timeline_progress'] = round(min(expected_progress, 100), 2)
        
        # Overdue status
        if edp.end_date and now > edp.end_date and edp.status != 'completed':
            days_overdue = (now - edp.end_date).days
            kpis['days_overdue'] = days_overdue
            kpis['is_overdue'] = True
        else:
            kpis['is_overdue'] = False
        
        return kpis
    
    def _calculate_financial_kpis_from_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate financial KPIs from a DataFrame row."""
        kpis = {}
        
        budget = row.get('budget', 0)
        if budget and budget > 0:
            # For now, using mock data for spent amount
            # In real implementation, this would come from financial tracking
            mock_spent_percentage = 0.65  # 65% spent
            spent_amount = budget * mock_spent_percentage
            
            kpis['budget_total'] = budget
            kpis['budget_spent'] = round(spent_amount, 2)
            kpis['budget_remaining'] = round(budget - spent_amount, 2)
            kpis['budget_utilization'] = round(mock_spent_percentage * 100, 2)
            
            # Cost efficiency (mock calculation)
            status = row.get('status', '')
            if status == 'completed':
                kpis['cost_efficiency'] = round((budget / spent_amount * 100), 2) if spent_amount > 0 else 100
        
        return kpis
    
    def _calculate_performance_kpis(self, edp: EDP) -> Dict[str, Any]:
        """Calculate performance KPIs."""
        kpis = {}
        
        # Completion rate (mock calculation based on status)
        status_completion_map = {
            'planning': 10,
            'active': 60,
            'on_hold': 40,
            'completed': 100,
            'cancelled': 0
        }
        
        completion_rate = status_completion_map.get(edp.status, 0)
        kpis['completion_rate'] = completion_rate
        
        # Quality score (mock calculation)
        # In real implementation, this would be based on actual quality metrics
        base_quality = 85
        status_modifier = {
            'planning': -10,
            'active': 0,
            'on_hold': -15,
            'completed': 10,
            'cancelled': -50
        }
        
        quality_score = base_quality + status_modifier.get(edp.status, 0)
        kpis['quality_score'] = max(0, min(100, quality_score))
        
        # Risk level (based on various factors)
        risk_level = self._calculate_risk_level(edp)
        kpis['risk_level'] = risk_level
        
        return kpis
    
    def _calculate_status_kpis(self, edp: EDP) -> Dict[str, Any]:
        """Calculate status-related KPIs."""
        kpis = {}
        
        kpis['current_status'] = edp.status
        kpis['priority_level'] = edp.priority
        
        # Status health score
        status_health = {
            'planning': 70,
            'active': 90,
            'on_hold': 40,
            'completed': 100,
            'cancelled': 0
        }
        
        kpis['status_health'] = status_health.get(edp.status, 50)
        
        return kpis
    
    def _calculate_risk_level(self, edp: EDP) -> str:
        """Calculate risk level for an EDP."""
        risk_score = 0
        
        # Time-based risk
        if edp.end_date and datetime.now() > edp.end_date and edp.status != 'completed':
            risk_score += 30
        
        # Status-based risk
        status_risk = {
            'planning': 10,
            'active': 5,
            'on_hold': 25,
            'completed': 0,
            'cancelled': 50
        }
        risk_score += status_risk.get(edp.status, 20)
        
        # Update frequency risk
        if edp.last_update:
            days_since_update = (datetime.now() - edp.last_update).days
            if days_since_update > 30:
                risk_score += 20
            elif days_since_update > 14:
                risk_score += 10
        
        # Priority-based risk
        priority_risk = {
            'low': 0,
            'medium': 5,
            'high': 15,
            'critical': 25
        }
        risk_score += priority_risk.get(edp.priority, 10)
        
        # Determine risk level
        if risk_score >= 50:
            return 'high'
        elif risk_score >= 25:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_aggregate_kpis(self, edps: List[EDP]) -> Dict[str, Any]:
        """Calculate aggregate KPIs across all EDPs."""
        if not edps:
            return {}
        
        aggregate = {}
        
        # Status distribution
        status_counts = {}
        priority_counts = {}
        
        total_budget = 0
        completed_count = 0
        overdue_count = 0
        
        for edp in edps:
            # Count statuses
            status = edp.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count priorities
            priority = edp.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Sum budgets
            if edp.budget:
                total_budget += edp.budget
            
            # Count completed
            if edp.status == 'completed':
                completed_count += 1
            
            # Count overdue
            if (edp.end_date and datetime.now() > edp.end_date and 
                edp.status not in ['completed', 'cancelled']):
                overdue_count += 1
        
        total_edps = len(edps)
        
        aggregate.update({
            'total_edps': total_edps,
            'status_distribution': status_counts,
            'priority_distribution': priority_counts,
            'total_budget': total_budget,
            'completion_rate': round((completed_count / total_edps * 100), 2) if total_edps > 0 else 0,
            'overdue_rate': round((overdue_count / total_edps * 100), 2) if total_edps > 0 else 0,
            'active_edps': status_counts.get('active', 0),
            'planning_edps': status_counts.get('planning', 0)
        })
        
        return aggregate
    
    def _calculate_benchmark_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical benchmarks for a list of values."""
        if not values:
            return {}
        
        return {
            'mean': round(mean(values), 2),
            'median': round(median(values), 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'percentile_25': round(sorted(values)[len(values)//4], 2),
            'percentile_75': round(sorted(values)[3*len(values)//4], 2)
        }
    
    def _generate_real_trend_data(self, edp_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate trend data based on real EDP data."""
        # Return empty trend data - only show trends when we have real historical data
        
        days = (end_date - start_date).days
        dates = [start_date + timedelta(days=i) for i in range(days + 1)]
        
        trend_data = {
            'dates': [date.strftime('%Y-%m-%d') for date in dates],
            'completion_rate': [0 for _ in range(len(dates))],
            'budget_utilization': [0 for _ in range(len(dates))],
            'quality_score': [0 for _ in range(len(dates))]
        }
        
        return trend_data
    
    # ==========================================================================
    # DASHBOARD.TSX STYLE KPIs - NEW EXECUTIVE COMPONENTS
    # ==========================================================================
    
    def calculate_executive_dashboard_kpis(self, df_full: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all KPIs needed for the new dashboard.tsx style components."""
        try:
            if df_full.empty:
                return self.get_empty_executive_kpis()
            
            df_full = self._prepare_kpi_data(df_full)
            
            # Calculate all executive KPIs
            executive_kpis = {}
            
            # 1. Executive KPI Cards
            executive_kpis.update(self._calculate_executive_kpi_cards(df_full))
            
            # 2. Aging Distribution Matrix
            executive_kpis.update(self._calculate_aging_distribution_matrix(df_full))
            
            # 3. Client Risk Analysis
            executive_kpis.update(self._calculate_client_risk_analysis(df_full))
            
            # 4. Additional metrics for existing components
            executive_kpis.update(self._calculate_additional_metrics(df_full))
            
            # Sanitize for JSON
            executive_kpis = self._sanitize_for_json(executive_kpis)
            
            return executive_kpis
            
        except Exception as e:
            logger.error(f"Error calculating executive dashboard KPIs: {str(e)}")
            return self.get_empty_executive_kpis()
    
    def _calculate_executive_kpi_cards(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate the 4 main executive KPI cards using REAL database data."""
        try:
            if df.empty:
                return {
                    'executive_total_receivables': 0.0,
                    'executive_receivables_change': 0.0,
                    'executive_critical_amount': 0.0,
                    'executive_critical_percentage': 0.0,
                    'executive_active_accounts': 0,
                    'executive_open_invoices': 0,
                    'executive_avg_collection_days': 0,
                    'executive_collection_vs_target': 0,
                    # Also include template-expected names
                    'total_monto_propuesto': 0.0,
                    'critical_amount': 0.0,
                    'critical_projects_count': 0
                }
            
            # TOTAL RECEIVABLES - Sum all EDPs that are NOT paid/completed (pending receivables)
            # Estados que NO están completamente pagados/cerrados
            completed_states = ['pagado', 'validado', 'completado', 'cerrado', 'finalizado']
            df_pending = df[~df['estado'].str.strip().str.lower().isin(completed_states)]
            
            total_receivables = 0.0
            if not df_pending.empty and 'monto_propuesto' in df_pending.columns:
                total_receivables = pd.to_numeric(df_pending['monto_propuesto'], errors='coerce').fillna(0).sum()
            
            # Convert to millions for display
            total_receivables_m = total_receivables / 1_000_000
            
            # CRITICAL (+90D) - EDPs with DSO > 90 days AND still pending (not paid)
            critical_amount = 0.0
            critical_count = 0
            if 'dso_actual' in df.columns and not df_pending.empty:
                # Only consider pending EDPs for critical calculation
                df_pending_copy = df_pending.copy()
                df_pending_copy['dso_numeric'] = pd.to_numeric(df_pending_copy['dso_actual'], errors='coerce').fillna(0)
                
                # Critical = pending EDPs with DSO > 90 days
                critical_mask = df_pending_copy['dso_numeric'] > 90
                critical_df = df_pending_copy[critical_mask]
                
                if not critical_df.empty:
                    critical_count = len(critical_df)
                    if 'monto_propuesto' in critical_df.columns:
                        critical_amount = pd.to_numeric(critical_df['monto_propuesto'], errors='coerce').fillna(0).sum()
            
            critical_amount_m = critical_amount / 1_000_000
            # Critical percentage should be calculated ONLY from pending receivables
            critical_percentage = (critical_amount / max(1, total_receivables)) * 100 if total_receivables > 0 else 0
            
            # ACTIVE ACCOUNTS - Total EDPs not completed (same as pending for consistency)
            active_accounts = len(df_pending)
            
            # Open invoices = EDPs that are specifically sent or invoiced but not paid
            invoice_states = ['enviado', 'facturado', 'revision']
            df_invoices = df[df['estado'].str.strip().str.lower().isin(invoice_states)]
            open_invoices = len(df_invoices)
            
            # AVG COLLECTION (DSO using real data)
            avg_collection_days = 0
            if 'dso_actual' in df.columns:
                dso_values = pd.to_numeric(df['dso_actual'], errors='coerce').dropna()
                if len(dso_values) > 0:
                    avg_collection_days = dso_values.mean()
            
            # Collection vs target
            target_days = 60  # Standard target
            collection_vs_target = avg_collection_days - target_days
            
            # Calculate receivables change (simplified - would need historical data)
            receivables_change = 0.0  # Would be calculated from previous period
            
            print(f"📊 Executive KPI Cards calculated:")
            print(f"   Total Receivables: ${total_receivables_m:.1f}M CLP ({len(df_pending)} EDPs pending)")
            print(f"   Critical Amount: ${critical_amount_m:.1f}M CLP ({critical_count} EDPs >90d)")
            print(f"   Critical Percentage: {critical_percentage:.1f}% of total receivables")
            print(f"   Active Accounts: {active_accounts} EDPs")
            print(f"   Open Invoices: {open_invoices} EDPs")
            print(f"   Avg Collection: {avg_collection_days:.0f} days")
            
            return {
                # Executive dashboard names
                'executive_total_receivables': round(total_receivables_m, 1),
                'executive_receivables_change': round(receivables_change, 1),
                'executive_critical_amount': round(critical_amount_m, 1),
                'executive_critical_percentage': round(critical_percentage, 1),
                'executive_active_accounts': active_accounts,
                'executive_open_invoices': open_invoices,
                'executive_avg_collection_days': round(avg_collection_days, 0),
                'executive_collection_vs_target': round(collection_vs_target, 0),
                
                # Template-expected names (for backward compatibility)
                'total_monto_propuesto': round(total_receivables, 0),  # In CLP (not millions)
                'critical_amount': round(critical_amount, 0),  # In CLP (not millions)
                'critical_projects_count': critical_count,
                'total_edps_activos': active_accounts,
                'dso_vs_target': round(collection_vs_target, 1),
                
                # Additional names that might be expected
                'receivables_change': round(receivables_change, 1),
                'critical_percentage': round(critical_percentage, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating executive KPI cards: {str(e)}")
            return {
                'executive_total_receivables': 0.0,
                'executive_receivables_change': 0.0,
                'executive_critical_amount': 0.0,
                'executive_critical_percentage': 0.0,
                'executive_active_accounts': 0,
                'executive_open_invoices': 0,
                'executive_avg_collection_days': 0,
                'executive_collection_vs_target': 0,
                'total_monto_propuesto': 0.0,
                'critical_amount': 0.0,
                'critical_projects_count': 0
            }
            
 
    
    def _calculate_aging_distribution_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate aging distribution matrix with 6 ranges using REAL database data."""
        try:
            if df.empty or 'dso_actual' not in df.columns:
                return self._get_empty_aging_matrix()
            
            # Convert dso_actual to numeric, handle errors
            df_days = df.copy()
            df_days['days_numeric'] = pd.to_numeric(df_days['dso_actual'], errors='coerce').fillna(0)
            
            # Filter out completed states (consistent with executive KPI cards)
            estados_completados = ['pagado', 'validado', 'completado', 'cerrado', 'finalizado']
            # Filter out paid states if needed
            if 'estado' in df_days.columns:
                df_days = df_days[~df_days['estado'].str.strip().str.lower().isin(estados_completados)]
            # Filter only rows with valid DSO data (> 0)
            df_valid = df_days[df_days['days_numeric'] > 0]
            
            if df_valid.empty:
                return self._get_empty_aging_matrix()
            
            # Calculate aging buckets based on DSO ranges
            aging_ranges = {
                '0_15': (df_valid['days_numeric'] >= 0) & (df_valid['days_numeric'] <= 15),
                '16_30': (df_valid['days_numeric'] >= 16) & (df_valid['days_numeric'] <= 30),
                '31_45': (df_valid['days_numeric'] >= 31) & (df_valid['days_numeric'] <= 45),
                '46_60': (df_valid['days_numeric'] >= 46) & (df_valid['days_numeric'] <= 60),
                '61_90': (df_valid['days_numeric'] >= 61) & (df_valid['days_numeric'] <= 90),
                '90_plus': df_valid['days_numeric'] > 90
            }
            
            # Calculate total receivables for percentage calculations
            total_amount = 0.0
            if 'monto_propuesto' in df_valid.columns:
                total_amount = pd.to_numeric(df_valid['monto_propuesto'], errors='coerce').fillna(0).sum()
            
            aging_matrix = {}
            total_weighted_days = 0.0
            total_weight = 0.0
            
            print(f"📊 Aging Distribution Matrix calculation: {len(df_valid)} EDPs with valid DSO")
            
            for range_key, mask in aging_ranges.items():
                df_range = df_valid[mask]
                count = len(df_range)
                
                amount = 0.0
                if not df_range.empty and 'monto_propuesto' in df_range.columns:
                    amount = pd.to_numeric(df_range['monto_propuesto'], errors='coerce').fillna(0).sum()
                
                percentage = (amount / max(1, total_amount)) * 100 if total_amount > 0 else 0
                amount_m = amount / 1_000_000  # Convert to millions
                
                # Calculate weighted average days for this range
                if not df_range.empty:
                    range_avg_days = df_range['days_numeric'].mean()
                    total_weighted_days += range_avg_days * amount
                    total_weight += amount
                
                aging_matrix.update({
                    f'aging_{range_key}_count': count,
                    f'aging_{range_key}_amount': round(amount, 0),  # Keep in CLP for template compatibility
                    f'aging_{range_key}_percentage': round(percentage, 1)
                })
                
                print(f"   {range_key}: {count} EDPs, ${amount_m:.1f}M ({percentage:.1f}%)")
            
            # Calculate weighted average days
            weighted_avg_days = (total_weighted_days / max(1, total_weight)) if total_weight > 0 else 0
            
            # Calculate total receivables in millions
            total_receivables_m = total_amount / 1_000_000
            
            # Calculate at-risk amount (60+ days) - Keep in CLP for template compatibility
            at_risk_amount_clp = 0.0
            if 'monto_propuesto' in df_valid.columns:
                at_risk_mask = df_valid['days_numeric'] > 60
                at_risk_df = df_valid[at_risk_mask]
                if not at_risk_df.empty:
                    at_risk_amounts = pd.to_numeric(at_risk_df['monto_propuesto'], errors='coerce').fillna(0)
                    at_risk_amount_clp = at_risk_amounts.sum()
            
            # Collection efficiency (amounts in 0-30 day range)
            safe_amount_clp = aging_matrix.get('aging_0_15_amount', 0) + aging_matrix.get('aging_16_30_amount', 0)
            collection_efficiency = (safe_amount_clp / max(1, total_amount)) * 100 if total_amount > 0 else 0
            
            # Add summary metrics - note: some fields aren't used by template but kept for completeness
            aging_matrix.update({
                'aging_total_receivables': round(total_receivables_m, 1),  # Not used by template
                'aging_weighted_avg_days': round(weighted_avg_days, 0),   # Not used by template  
                'aging_at_risk_amount': round(at_risk_amount_clp / 1_000_000, 1),  # Not used by template
                'collection_efficiency': round(collection_efficiency, 1)   # Used by template
            })
            
            print(f"📊 Aging Matrix Summary: ${total_receivables_m:.1f}M total, {weighted_avg_days:.0f}d avg, ${at_risk_amount_clp/1_000_000:.1f}M at risk")
            
            return aging_matrix
            
        except Exception as e:
            logger.error(f"Error calculating aging distribution matrix: {str(e)}")
            return self._get_empty_aging_matrix()
    
    def _calculate_client_risk_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate client risk analysis metrics using REAL database data."""
        try:
            if df.empty or 'dso_actual' not in df.columns:
                return self._get_empty_client_risk_analysis()
            
            # Convert DSO to numeric for analysis
            df_with_days = df.copy()
            df_with_days['days_numeric'] = pd.to_numeric(df_with_days['dso_actual'], errors='coerce').fillna(0)
            
            # Filter out completed states (consistent with other functions)
            estados_completados = ['pagado', 'validado', 'completado', 'cerrado', 'finalizado']
            if 'estado' in df_with_days.columns:
                df_with_days = df_with_days[~df_with_days['estado'].str.strip().str.lower().isin(estados_completados)]
            
            # Filter valid DSO data
            df_valid = df_with_days[df_with_days['days_numeric'] > 0]
            
            if df_valid.empty:
                return self._get_empty_client_risk_analysis()
            
            # Risk categories based on aging (using real business rules)
            high_risk_mask = df_valid['days_numeric'] > 90  # Critical risk
            watch_list_mask = (df_valid['days_numeric'] > 30) & (df_valid['days_numeric'] <= 90)  # Watch list
            safe_mask = df_valid['days_numeric'] <= 30  # Safe
            
            # Count clients in each category
            high_risk_clients_count = len(df_valid[high_risk_mask])
            watch_list_clients_count = len(df_valid[watch_list_mask])
            safe_clients_count = len(df_valid[safe_mask])
            
            # Calculate amounts at risk
            high_risk_amount = 0.0
            watch_list_amount = 0.0
            safe_amount = 0.0
            
            if 'monto_propuesto' in df_valid.columns:
                high_risk_amount = pd.to_numeric(df_valid[high_risk_mask]['monto_propuesto'], errors='coerce').fillna(0).sum() / 1_000_000
                watch_list_amount = pd.to_numeric(df_valid[watch_list_mask]['monto_propuesto'], errors='coerce').fillna(0).sum() / 1_000_000
                safe_amount = pd.to_numeric(df_valid[safe_mask]['monto_propuesto'], errors='coerce').fillna(0).sum() / 1_000_000
            
            # Calculate average risk score (0-100 scale based on DSO)
            if not df_valid.empty:
                # Risk score based on DSO: 0-30 days = low risk, 90+ days = high risk
                avg_dso = df_valid['days_numeric'].mean()
                # Map DSO to risk score: 30 days = 20%, 60 days = 50%, 90+ days = 100%
                if avg_dso <= 30:
                    average_risk_score = (avg_dso / 30) * 20  # 0-20% risk
                elif avg_dso <= 60:
                    average_risk_score = 20 + ((avg_dso - 30) / 30) * 30  # 20-50% risk
                else:
                    average_risk_score = 50 + min(50, ((avg_dso - 60) / 30) * 50)  # 50-100% risk
            else:
                average_risk_score = 0
            
            # Risk trend (simplified - would need historical data)
            risk_trend = "stable"  # Would be "increasing", "decreasing", or "stable"
            
            # Calculate total monitored amount
            total_monitored = high_risk_amount + watch_list_amount + safe_amount
            
            print(f"📊 Client Risk Analysis: {len(df_valid)} EDPs analyzed")
            print(f"   High Risk: {high_risk_clients_count} EDPs (${high_risk_amount:.1f}M)")
            print(f"   Watch List: {watch_list_clients_count} EDPs (${watch_list_amount:.1f}M)")
            print(f"   Safe: {safe_clients_count} EDPs (${safe_amount:.1f}M)")
            print(f"   Avg Risk Score: {average_risk_score:.1f}%")
            
            return {
                'client_high_risk_count': high_risk_clients_count,
                'client_high_risk_amount': round(high_risk_amount, 1),
                'client_watch_list_count': watch_list_clients_count,
                'client_watch_list_amount': round(watch_list_amount, 1),
                'client_safe_count': safe_clients_count,
                'client_safe_amount': round(safe_amount, 1),
                'client_average_risk_score': round(average_risk_score, 1),
                'client_risk_trend': risk_trend,
                'client_total_monitored': round(total_monitored, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating client risk analysis: {str(e)}")
            return self._get_empty_client_risk_analysis()
    
    def _get_empty_aging_matrix(self) -> Dict[str, Any]:
        """Return empty aging matrix structure."""
        return {
            'aging_0_15_count': 0,
            'aging_0_15_amount': 0.0,
            'aging_0_15_percentage': 0.0,
            'aging_16_30_count': 0,
            'aging_16_30_amount': 0.0,
            'aging_16_30_percentage': 0.0,
            'aging_31_45_count': 0,
            'aging_31_45_amount': 0.0,
            'aging_31_45_percentage': 0.0,
            'aging_46_60_count': 0,
            'aging_46_60_amount': 0.0,
            'aging_46_60_percentage': 0.0,
            'aging_61_90_count': 0,
            'aging_61_90_amount': 0.0,
            'aging_61_90_percentage': 0.0,
            'aging_90_plus_count': 0,
            'aging_90_plus_amount': 0.0,
            'aging_90_plus_percentage': 0.0,
            'aging_total_receivables': 0.0,
            'aging_weighted_avg_days': 0,
            'aging_at_risk_amount': 0.0,
            'aging_collection_efficiency': 0.0
        }
    
    def _get_empty_client_risk_analysis(self) -> Dict[str, Any]:
        """Return empty client risk analysis structure."""
        return {
            'client_high_risk_count': 0,
            'client_high_risk_amount': 0.0,
            'client_watch_list_count': 0,
            'client_watch_list_amount': 0.0,
            'client_safe_count': 0,
            'client_safe_amount': 0.0,
            'client_average_risk_score': 0.0,
            'client_risk_trend': 'stable',
            'client_total_monitored': 0.0
        }
    
    def get_detailed_client_risk_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get detailed client risk data for dashboard.tsx style table."""
        try:
            if df.empty or 'cliente' not in df.columns:
                return []
            
            # Convert DSO to numeric for analysis
            df_with_days = df.copy()
            df_with_days['days_numeric'] = pd.to_numeric(df_with_days['dso_actual'], errors='coerce').fillna(0)
            df_with_days['monto_numeric'] = pd.to_numeric(df_with_days['monto_propuesto'], errors='coerce').fillna(0)
            
            # Group by client and calculate aging distribution
            client_data = []
            for cliente, client_df in df_with_days.groupby('cliente'):
                if pd.isna(cliente) or cliente.strip() == '':
                    continue
                
                # Calculate total amounts by aging ranges
                total_amount = client_df['monto_numeric'].sum()
                current_amount = client_df[client_df['days_numeric'] <= 15]['monto_numeric'].sum()
                days_1_30 = client_df[(client_df['days_numeric'] > 15) & (client_df['days_numeric'] <= 30)]['monto_numeric'].sum()
                days_31_60 = client_df[(client_df['days_numeric'] > 30) & (client_df['days_numeric'] <= 60)]['monto_numeric'].sum()
                days_61_90 = client_df[(client_df['days_numeric'] > 60) & (client_df['days_numeric'] <= 90)]['monto_numeric'].sum()
                days_90_plus = client_df[client_df['days_numeric'] > 90]['monto_numeric'].sum()
                
                # Calculate risk level based on aging distribution
                critical_pct = (days_90_plus / total_amount * 100) if total_amount > 0 else 0
                high_risk_pct = ((days_61_90 + days_90_plus) / total_amount * 100) if total_amount > 0 else 0
                
                if critical_pct > 30:
                    risk_level = "CRITICAL"
                elif high_risk_pct > 40:
                    risk_level = "HIGH"
                elif days_31_60 > total_amount * 0.5:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "LOW"
                
                # Calculate average aging
                weighted_days = 0
                total_weight = 0
                for _, row in client_df.iterrows():
                    if row['monto_numeric'] > 0:
                        weighted_days += row['days_numeric'] * row['monto_numeric']
                        total_weight += row['monto_numeric']
                
                avg_aging = weighted_days / total_weight if total_weight > 0 else 0
                
                # Get contact info (first available)
                contact_info = client_df.iloc[0]
                project_manager = contact_info.get('jefe_proyecto', 'N/A')
                invoice_count = len(client_df)
                
                # Calculate trend (simplified - would need historical data)
                trend = "STABLE"  # Could be "IMPROVING", "DECLINING", "STABLE"
                
                # Last payment date (if available)
                last_payment = contact_info.get('fecha_ultimo_pago', '2024-01-15')
                if pd.isna(last_payment):
                    last_payment = '2024-01-15'
                
                client_data.append({
                    'cliente': str(cliente).strip(),
                    'contacto': f"Contact {cliente[:10]}",  # Would need real contact data
                    'email': f"contact@{cliente.lower().replace(' ', '').replace('.', '')[:10]}.com",
                    'telefono': "+57-1-234-5678",  # Would need real phone data
                    'total': int(total_amount),
                    'corriente': int(current_amount),
                    'dias30': int(days_1_30),
                    'dias60': int(days_31_60),
                    'dias90': int(days_61_90),
                    'mas90': int(days_90_plus),
                    'facturas': invoice_count,
                    'ultimoPago': str(last_payment),
                    'riesgo': risk_level,
                    'tendencia': trend,
                    'avg_aging_days': round(avg_aging, 1),
                    'project_manager': str(project_manager)
                })
            
            # Sort by total amount descending
            client_data.sort(key=lambda x: x['total'], reverse=True)
            
            print(f"📊 Generated detailed client risk data for {len(client_data)} clients")
            
            return client_data[:20]  # Return top 20 clients
            
        except Exception as e:
            logger.error(f"Error generating detailed client risk data: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _calculate_additional_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate additional metrics needed for dashboard functionality."""
        try:
            # These are additional fields that existing components might need
            return {
                'forecast_confidence': 85.0,  # Would be calculated from model accuracy
                'meta_gap': 0,  # Would be calculated from monthly targets
                'days_remaining': 30,  # Days remaining in current period
                'objetivo_anual': 0,  # Annual target
                'ingresos_totales': df['monto_propuesto'].sum() if 'monto_propuesto' in df.columns else 0,
                'efficiency_score': 78.5,  # Operational efficiency score
                'roi_promedio': 15.2,  # Average ROI
                'proyectos_completados': len(df[df['estado'].str.strip().str.lower().isin(['pagado', 'validado'])]) if 'estado' in df.columns else 0,
                'satisfaccion_cliente': 92.0,  # Client satisfaction score
                'crecimiento_ingresos': 8.3,  # Revenue growth percentage
            }
            
        except Exception as e:
            logger.error(f"Error calculating additional metrics: {str(e)}")
            return {
                'forecast_confidence': 0,
                'meta_gap': 0,
                'days_remaining': 0,
                'objetivo_anual': 0,
                'ingresos_totales': 0,
                'efficiency_score': 0,
                'roi_promedio': 0,
                'proyectos_completados': 0,
                'satisfaccion_cliente': 0,
                'crecimiento_ingresos': 0,
            }
    
    def _get_empty_aging_matrix(self) -> Dict[str, Any]:
        """Return empty aging matrix structure."""
        ranges = ['0_15', '16_30', '31_45', '46_60', '61_90', '90_plus']
        empty_matrix = {}
        
        for range_key in ranges:
            empty_matrix.update({
                f'aging_{range_key}_count': 0,
                f'aging_{range_key}_amount': 0,
                f'aging_{range_key}_percentage': 0
            })
        
        empty_matrix['collection_efficiency'] = 0
        return empty_matrix
    
    def get_empty_executive_kpis(self) -> Dict[str, Any]:
        """Return empty executive KPIs structure."""
        empty_kpis = {}
        
        # Executive KPI Cards
        empty_kpis.update({
            'total_monto_propuesto': 0,
            'receivables_change': 0,
            'critical_amount': 0,
            'critical_percentage': 0,
            'total_edps_activos': 0,
            'dso_vs_target': 0,
        })
        
        # Aging Distribution Matrix
        empty_kpis.update(self._get_empty_aging_matrix())
        
        # Client Risk Analysis
        empty_kpis.update({
            'high_risk_clients_count': 0,
            'high_risk_clients_amount': 0,
            'watch_list_clients_count': 0,
            'watch_list_clients_amount': 0,
            'safe_clients_count': 0,
            'safe_clients_amount': 0,
            'average_risk_score': 0,
            'risk_score_trend': 0
        })
        
        # Additional Metrics
        empty_kpis.update({
            'forecast_confidence': 0,
            'meta_gap': 0,
            'days_remaining': 0,
            'objetivo_anual': 0,
            'ingresos_totales': 0,
            'efficiency_score': 0,
            'roi_promedio': 0,
            'proyectos_completados': 0,
            'satisfaccion_cliente': 0,
            'crecimiento_ingresos': 0,
        })
        
        return empty_kpis
    
    def _calculate_forecast_accuracy(self, df: pd.DataFrame) -> float:
        """Calculate forecast accuracy based on completion vs projections."""
        try:
            if df.empty:
                return 0.0
            
            # Simplified forecast accuracy calculation
            # Would be calculated from historical forecast vs actual completion data
            completed_projects = len(df[df['estado'].str.strip().str.lower().isin(['pagado', 'validado'])])
            total_projects = len(df)
            
            # Forecast accuracy based on completion rate (simplified)
            if total_projects > 0:
                accuracy = (completed_projects / total_projects) * 85  # 85% base accuracy
                return min(100, max(0, accuracy))
            
            return 75.0  # Default accuracy
            
        except Exception as e:
            logger.error(f"Error calculating forecast accuracy: {str(e)}")
            return 75.0