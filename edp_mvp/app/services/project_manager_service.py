"""
Service for Project Manager (Jefe de Proyecto) business logic.
Handles calculations and data processing for project manager views.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from ..repositories.project_manager_repository import ProjectManagerRepository
from ..repositories.edp_repository import EDPRepository
from ..services.analytics_service import AnalyticsService
from ..services.kpi_service import KPIService
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils
import pandas as pd
import logging
import traceback

logger = logging.getLogger(__name__)

class ProjectManagerService:
    """Service class for project manager business logic."""

    def __init__(self):
        self.pm_repo = ProjectManagerRepository()
        self.edp_repo = EDPRepository()
        self.analytics_service = AnalyticsService()
        self.kpi_service = KPIService()

    def get_dashboard_data(self, manager_name: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a project manager."""
        try:
            # Get basic manager data
            manager_summary = self.pm_repo.get_manager_summary(manager_name)
            projects_by_status = self.pm_repo.get_projects_by_status(manager_name)
            financial_metrics = self.pm_repo.get_financial_metrics(manager_name)
            
            # Calculate KPIs
            kpis = self._calculate_manager_kpis(manager_name)
            
            # Get project performance data
            project_performance = self._get_project_performance(manager_name)
            
            # Get team metrics
            team_performance = self.pm_repo.get_team_performance(manager_name)
            
            # Calculate trends
            trends = self._calculate_trends(manager_name)
            
            # Get alerts and notifications
            alerts = self._generate_alerts(manager_name, manager_summary, projects_by_status)
            
            return {
                'manager_name': manager_name,
                'summary': manager_summary,
                'projects_by_status': projects_by_status,
                'financial_metrics': financial_metrics,
                'kpis': kpis,
                'project_performance': project_performance,
                'team_performance': team_performance,
                'trends': trends,
                'alerts': alerts,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for {manager_name}: {str(e)}")
            return {}

    def _calculate_manager_kpis(self, manager_name: str) -> Dict[str, Any]:
        """Calculate key performance indicators for the project manager."""
        try:
            proyectos = self.pm_repo.get_manager_projects(manager_name)
            projects_cost = self.pm_repo.get_projects_cost(manager_name)
            df = pd.DataFrame(proyectos)
            if df.empty:
                return {
                    'project_efficiency': 0,
                    'budget_performance': 0,
                    'time_performance': 0,
                    'quality_score': 0,
                    'overall_score': 0,
                    'avg_processing_days': 0,
                    'target_days': 45
                }
            for col in ["monto_propuesto", "monto_aprobado", "monto_pagado", "dias_espera"]:
                if col not in df.columns:
                    df[col] = 0
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            if "estado" not in df.columns:
                df["estado"] = ""
            if 'monto_pagado' not in df.columns or df['monto_pagado'].sum() == 0:
                df["monto_pagado"] = df.apply(
                    lambda row: row["monto_aprobado"] if str(row["estado"]).lower() in ["pagado", "validado"] else 0, axis=1
                )
            # Project Efficiency (% of projects on time)
            on_time_projects = 0
            total_completed = 0
            if 'fecha_emision' in df.columns and 'fecha_envio_conformidad' in df.columns:
                for _, row in df.iterrows():
                    if str(row['estado']).lower() in ['pagado', 'conformado']:
                        total_completed += 1
                        fecha_creacion = row.get('fecha_emision')
                        fecha_pago = row.get('fecha_envio_conformidad')
                        if pd.notnull(fecha_creacion) and pd.notnull(fecha_pago):
                            days = (fecha_pago - fecha_creacion).days
                            if days <= 45:
                                on_time_projects += 1
            project_efficiency = (on_time_projects / total_completed * 100) if total_completed > 0 else 0
            # Budget Performance (approved vs proposed)
            total_proposed = df['monto_propuesto'].sum()
            total_approved = df['monto_aprobado'].sum()
            budget_performance = (total_approved / total_proposed * 100) if total_proposed > 0 else 0
            # Time Performance (average processing days vs target)
            avg_processing = df['dias_espera'].mean() if 'dias_espera' in df.columns else 0
            target_days = 45
            time_performance = max(0, 100 - ((avg_processing - target_days) / target_days * 100))
            # Quality Score (based on rework rate)
            quality_score = self._calculate_quality_score(df)
            # Overall Score
            overall_score = (project_efficiency + budget_performance + time_performance + quality_score) / 4
            
            total_costs = projects_cost
            
            profit_margin = (total_approved - total_costs) / total_costs * 100 if total_costs > 0 else 0
            print(f'Total costs: {total_costs}')
            return {
                'project_efficiency': round(project_efficiency, 1),
                'budget_performance': round(min(100, budget_performance), 1),
                'time_performance': round(time_performance, 1),
                'quality_score': round(quality_score, 1),
                'overall_score': round(overall_score, 1),
                'avg_processing_days': round(avg_processing, 1),
                'target_days': target_days,
                'total_costs': round(total_costs, 0),
                'profit_margin': round(profit_margin, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating KPIs for {manager_name}: {str(e)}")
            return {}

    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate quality score based on rework and revision patterns."""
        try:
            if df.empty:
                return 0
            revision_count = 0
            total_edps = len(df)
            for _, row in df.iterrows():
                observaciones = str(row.get('observaciones', '')).lower()
                descripcion = str(row.get('descripcion', '')).lower() if 'descripcion' in row else ''
                revision_indicators = ['revision', 'corrección', 'error', 'cambio', 'modificación', 'ajuste']
                if any(indicator in observaciones or indicator in descripcion for indicator in revision_indicators):
                    revision_count += 1
            rework_rate = revision_count / total_edps if total_edps > 0 else 0
            quality_score = max(0, 100 - (rework_rate * 100))
            return quality_score
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 75

    def _get_project_performance(self, manager_name: str) -> List[Dict[str, Any]]:
        """Get performance metrics for all projects under the manager."""
        try:
            proyectos = self.pm_repo.get_manager_projects(manager_name)
            df = pd.DataFrame(proyectos)
            if df.empty or 'proyecto' not in df.columns:
                return []
            for col in ["monto_propuesto", "monto_aprobado", "monto_pagado", "dias_espera"]:
                if col not in df.columns:
                    df[col] = 0
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            if "estado" not in df.columns:
                df["estado"] = ""
            if 'monto_pagado' not in df.columns or df['monto_pagado'].sum() == 0:
                df["monto_pagado"] = df.apply(
                    lambda row: row["monto_aprobado"] if str(row["estado"]).lower() in ["pagado", "validado"] else 0, axis=1
                )
            project_performance = []
            for project_name, group in df.groupby('proyecto'):
                total_edps = len(group)
                total_proposed = group['monto_propuesto'].sum()
                total_approved = group['monto_aprobado'].sum()
                total_paid = group['monto_pagado'].sum()
                avg_processing = group['dias_espera'].mean() if 'dias_espera' in group.columns else 0
                completion_rate = (total_paid / total_approved * 100) if total_approved > 0 else 0
                progress_class = 'green' if completion_rate >= 90 else 'amber' if completion_rate >= 60 else 'red'
                status = 'completed' if completion_rate >= 99 else 'in_progress' if completion_rate >= 60 else 'pending'
                project_performance.append({
                    'project_name': project_name,
                    'total_edps': int(total_edps),
                    'total_proposed': float(total_proposed),
                    'total_approved': float(total_approved),
                    'total_paid': float(total_paid),
                    'pending_amount': float(total_approved - total_paid),
                    'completion_rate': round(completion_rate, 1),
                    'avg_processing_days': round(avg_processing, 1),
                    'progress_class': progress_class,
                    'status': status
                })
            return project_performance
        except Exception as e:
            logger.error(f"Error getting project performance for {manager_name}: {str(e)}")
            return []

    def _get_progress_class(self, completion_rate: float) -> str:
        """Get CSS class for progress indication."""
        if completion_rate >= 90:
            return 'success'
        elif completion_rate >= 70:
            return 'warning'
        elif completion_rate >= 50:
            return 'info'
        else:
            return 'danger'

    def _get_urgency_class(self, avg_days: float) -> str:
        """Get CSS class for urgency indication."""
        if avg_days <= 30:
            return 'success'
        elif avg_days <= 45:
            return 'warning'
        else:
            return 'danger'

    def _calculate_trends(self, manager_name: str) -> Dict[str, Any]:
        """Calculate trend data for the manager's metrics."""
        try:
            projects = self.pm_repo.get_manager_projects(manager_name)
            
            # Group by month for trend analysis
            monthly_data = {}
            
            for edp in projects:
                # Handle both dict and object formats
                if hasattr(edp, '__dict__'):
                    edp_data = edp.__dict__
                else:
                    edp_data = edp
                
                # Try different date field names
                fecha_emision = edp_data.get('fecha_emision') or edp_data.get('Fecha_Creacion')
                
                # Parse date if it's a string
                if fecha_emision:
                    if isinstance(fecha_emision, str):
                        try:
                            fecha_emision = datetime.strptime(fecha_emision, '%Y-%m-%d')
                        except ValueError:
                            try:
                                fecha_emision = datetime.strptime(fecha_emision, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                continue
                    
                    if isinstance(fecha_emision, datetime):
                        month_key = fecha_emision.strftime('%Y-%m')
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {
                                'edps_sent': 0,
                                'edps_approved': 0,
                                'edps_paid': 0,
                                'amount_proposed': 0,
                                'amount_approved': 0,
                                'amount_paid': 0
                            }
                        
                        # Count EDPs sent (created)
                        monthly_data[month_key]['edps_sent'] += 1
                        monthly_data[month_key]['amount_proposed'] += float(edp_data.get('monto_propuesto', 0) or 0)
                        
                        # Count EDPs approved
                        estado = str(edp_data.get('estado', '')).lower()
                        if estado in ['validado', 'pagado', 'enviado']:
                            monthly_data[month_key]['edps_approved'] += 1
                            monthly_data[month_key]['amount_approved'] += float(edp_data.get('monto_aprobado', 0) or 0)
                        
                        # Count EDPs paid
                        if estado in ['pagado', 'validado']:
                            monthly_data[month_key]['edps_paid'] += 1
                            monthly_data[month_key]['amount_paid'] += float(edp_data.get('monto_aprobado', 0) or 0)
            
            # Get last 6 months
            current_date = datetime.now()
            last_6_months = []
            
            # Spanish month names
            month_names = {
                1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
            }
            
            for i in range(5, -1, -1):
                month_date = current_date - timedelta(days=i*30)
                month_key = month_date.strftime('%Y-%m')
                month_name = month_names.get(month_date.month, month_date.strftime('%b'))
                
                data = monthly_data.get(month_key, {
                    'edps_sent': 0,
                    'edps_approved': 0,
                    'edps_paid': 0,
                    'amount_proposed': 0,
                    'amount_approved': 0,
                    'amount_paid': 0
                })
                
                last_6_months.append({
                    'month': month_name,
                    'month_key': month_key,
                    **data
                })
            
            return {
                'monthly_trends': last_6_months,
                'total_months': len(last_6_months)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends for {manager_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return {'monthly_trends': [], 'total_months': 0}

    def _generate_alerts(self, manager_name: str, summary: Dict, projects_by_status: Dict) -> List[Dict[str, Any]]:
        """Generate alerts and notifications for the project manager."""
        try:
            alerts = []
            
            # Critical EDPs alert
            if summary.get('critical_edps', 0) > 0:
                alerts.append({
                    'type': 'danger',
                    'icon': 'exclamation-triangle',
                    'title': 'EDPs Críticos',
                    'message': f"Tienes {summary['critical_edps']} EDPs con más de 45 días de procesamiento",
                    'action_url': f'/jefe-proyecto/{manager_name}/criticos',
                    'priority': 'high'
                })
            
            # Low completion rate alert
            completion_rate = summary.get('completion_rate', 0)
            if completion_rate < 60:
                alerts.append({
                    'type': 'warning',
                    'icon': 'chart-line',
                    'title': 'Tasa de Completación Baja',
                    'message': f"Tu tasa de completación es del {completion_rate}%. Meta: 80%",
                    'action_url': f'/jefe-proyecto/{manager_name}/performance',
                    'priority': 'medium'
                })
            
            # High pending amount alert
            pending_amount = summary.get('pending_amount', 0)
            if pending_amount > 1000000:  # 1M threshold
                formatted_amount = FormatUtils.format_currency(pending_amount)
                alerts.append({
                    'type': 'info',
                    'icon': 'dollar-sign',
                    'title': 'Alto Monto Pendiente',
                    'message': f"Tienes {formatted_amount} pendientes de pago",
                    'action_url': f'/jefe-proyecto/{manager_name}/pendientes',
                    'priority': 'medium'
                })
            
            # Overdue projects alert
            overdue_count = len(projects_by_status.get('overdue', []))
            if overdue_count > 0:
                alerts.append({
                    'type': 'danger',
                    'icon': 'clock',
                    'title': 'Proyectos Vencidos',
                    'message': f"Tienes {overdue_count} proyectos con retraso significativo",
                    'action_url': f'/jefe-proyecto/{manager_name}/overdue',
                    'priority': 'high'
                })
            
            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            alerts.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            return alerts[:5]  # Limit to top 5 alerts
            
        except Exception as e:
            logger.error(f"Error generating alerts for {manager_name}: {str(e)}")
            return []

    def get_project_detail(self, manager_name: str, project_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific project."""
        try:
            return self.pm_repo.get_project_details(manager_name, project_name)
        except Exception as e:
            logger.error(f"Error getting project detail: {str(e)}")
            return {}

    def get_team_dashboard(self, manager_name: str) -> Dict[str, Any]:
        """Get team performance dashboard data."""
        try:
            team_performance = self.pm_repo.get_team_performance(manager_name)
            
            # Calculate team metrics
            team_metrics = {
                'total_members': len(team_performance),
                'avg_efficiency': 0,
                'total_team_workload': 0,
                'top_performer': None,
                'needs_attention': []
            }
            
            if team_performance:
                efficiencies = [member['efficiency_score'] for member in team_performance.values()]
                team_metrics['avg_efficiency'] = sum(efficiencies) / len(efficiencies)
                
                team_metrics['total_team_workload'] = sum(
                    member['total_edps'] for member in team_performance.values()
                )
                
                # Find top performer
                top_performer = max(
                    team_performance.items(),
                    key=lambda x: x[1]['efficiency_score']
                )
                team_metrics['top_performer'] = {
                    'name': top_performer[0],
                    'score': top_performer[1]['efficiency_score']
                }
                
                # Find members needing attention (efficiency < 70)
                team_metrics['needs_attention'] = [
                    {'name': name, 'score': data['efficiency_score']}
                    for name, data in team_performance.items()
                    if data['efficiency_score'] < 70
                ]
            
            return {
                'team_performance': team_performance,
                'team_metrics': team_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting team dashboard for {manager_name}: {str(e)}")
            return {}

    def export_manager_report(self, manager_name: str, format_type: str = 'excel') -> str:
        """Export comprehensive manager report."""
        try:
            dashboard_data = self.get_dashboard_data(manager_name)
            
            if format_type == 'excel':
                return self._export_to_excel(manager_name, dashboard_data)
            elif format_type == 'pdf':
                return self._export_to_pdf(manager_name, dashboard_data)
            else:
                return self._export_to_csv(manager_name, dashboard_data)
                
        except Exception as e:
            logger.error(f"Error exporting report for {manager_name}: {str(e)}")
            return ""

    def _export_to_excel(self, manager_name: str, data: Dict) -> str:
        """Export data to Excel format."""
        # Implementation for Excel export
        return f"report_{manager_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"

    def _export_to_pdf(self, manager_name: str, data: Dict) -> str:
        """Export data to PDF format."""
        # Implementation for PDF export
        return f"report_{manager_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

    def _export_to_csv(self, manager_name: str, data: Dict) -> str:
        """Export data to CSV format."""
        # Implementation for CSV export
        return f"report_{manager_name}_{datetime.now().strftime('%Y%m%d')}.csv"
