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
            
            # Get pending EDPs for validation (enviado y revisión)
            pending_edps = self.pm_repo.get_pending_edps_for_validation(manager_name)
            
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
                'pending_edps': pending_edps,
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
            for col in ["monto_propuesto", "monto_aprobado", "monto_pagado", "dso_actual"]:
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
            avg_processing = df['dso_actual'].mean() if 'dso_actual' in df.columns else 0
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
            for col in ["monto_propuesto", "monto_aprobado", "monto_pagado", "dso_actual"]:
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
                avg_processing = group['dso_actual'].mean() if 'dso_actual' in group.columns else 0
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
        """Get team performance dashboard data with cost management."""
        try:
            team_performance = self.pm_repo.get_team_performance(manager_name)
            
            # Ensure team_performance values are JSON serializable
            team_performance = self._ensure_json_serializable(team_performance)
            
            # Calculate team metrics
            team_metrics = {
                'total_members': len(team_performance),
                'avg_efficiency': 0.0,
                'total_team_workload': 0,
                'top_performer': None,
                'needs_attention': []
            }
            
            # Get cost data for team analysis
            team_cost_data = self._get_team_cost_analysis(manager_name, team_performance)
            
            if team_performance:
                efficiencies = [float(member['efficiency_score']) for member in team_performance.values()]
                team_metrics['avg_efficiency'] = round(sum(efficiencies) / len(efficiencies), 1)
                
                team_metrics['total_team_workload'] = sum(
                    int(member['total_edps']) for member in team_performance.values()
                )
                
                # Find top performer
                top_performer = max(
                    team_performance.items(),
                    key=lambda x: float(x[1]['efficiency_score'])
                )
                team_metrics['top_performer'] = {
                    'name': top_performer[0],
                    'score': float(top_performer[1]['efficiency_score'])
                }
                
                # Find members needing attention (efficiency < 70)
                team_metrics['needs_attention'] = [
                    {'name': name, 'score': float(data['efficiency_score'])}
                    for name, data in team_performance.items()
                    if float(data['efficiency_score']) < 70
                ]
            
            result = {
                'team_performance': team_performance,
                'team_metrics': team_metrics,
                'cost_analysis': team_cost_data
            }
            
            return self._ensure_json_serializable(result)
            
        except Exception as e:
            logger.error(f"Error getting team dashboard for {manager_name}: {str(e)}")
            return {}

    def _ensure_json_serializable(self, obj):
        """Convert numpy types to native Python types for JSON serialization."""
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._ensure_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_json_serializable(item) for item in obj]
        else:
            return obj

    def _get_team_cost_analysis(self, manager_name: str, team_performance: Dict) -> Dict[str, Any]:
        """Analyze cost metrics for team members."""
        try:
            from ..repositories.cost_repository import CostRepository
            cost_repo = CostRepository()
            
            # Get total project costs for manager
            total_project_costs = cost_repo.get_cost_by_manager(manager_name)
            
            # Define average monthly salaries by role (in pesos)
            SALARY_DATA = {
                'inspector_senior': 2_800_000,
                'inspector_junior': 2_200_000,
                'administrativo_senior': 2_500_000,
                'administrativo_junior': 1_900_000,
                'coordinador': 3_200_000
            }
            
            # Calculate cost metrics per team member
            team_cost_metrics = {}
            total_salary_cost = 0
            total_revenue = 0
            
            for member_name, performance_data in team_performance.items():
                # Ensure all performance data values are JSON serializable
                performance_data = self._ensure_json_serializable(performance_data)
                
                # Estimate member role based on performance (simplified logic)
                efficiency_score = float(performance_data.get('efficiency_score', 0))
                total_edps = int(performance_data.get('total_edps', 0))
                
                if efficiency_score >= 85:
                    role = 'inspector_senior' if total_edps > 15 else 'administrativo_senior'
                elif efficiency_score >= 70:
                    role = 'inspector_junior' if total_edps > 10 else 'administrativo_junior'
                else:
                    role = 'inspector_junior'
                
                # If top performer with high volume, could be coordinator
                if efficiency_score >= 90 and total_edps >= 20:
                    role = 'coordinador'
                
                monthly_salary = SALARY_DATA.get(role, 2_200_000)
                member_revenue = float(performance_data.get('total_amount', 0))
                
                # Calculate ROI and productivity metrics
                roi = ((member_revenue - monthly_salary) / monthly_salary * 100) if monthly_salary > 0 else 0
                cost_per_edp = monthly_salary / total_edps if total_edps > 0 else 0
                revenue_per_cost = member_revenue / monthly_salary if monthly_salary > 0 else 0
                
                team_cost_metrics[member_name] = {
                    'role': role,
                    'monthly_salary': int(monthly_salary),
                    'member_revenue': float(member_revenue),
                    'roi_percentage': round(float(roi), 1),
                    'cost_per_edp': round(float(cost_per_edp), 0),
                    'revenue_per_cost': round(float(revenue_per_cost), 2),
                    'efficiency_score': float(efficiency_score),
                    'cost_efficiency_score': float(self._calculate_cost_efficiency(roi, efficiency_score))
                }
                
                total_salary_cost += monthly_salary
                total_revenue += member_revenue
            
            # Calculate team-wide cost metrics
            team_roi = ((total_revenue - total_salary_cost) / total_salary_cost * 100) if total_salary_cost > 0 else 0
            avg_cost_per_member = total_salary_cost / len(team_performance) if team_performance else 0
            cost_efficiency_ratio = total_revenue / total_salary_cost if total_salary_cost > 0 else 0
            
            # Generate cost alerts
            cost_alerts = self._generate_cost_alerts(team_cost_metrics, team_roi)
            
            result = {
                'team_cost_metrics': team_cost_metrics,
                'total_salary_cost': int(total_salary_cost),
                'total_revenue': float(total_revenue),
                'team_roi': round(float(team_roi), 1),
                'avg_cost_per_member': round(float(avg_cost_per_member), 0),
                'cost_efficiency_ratio': round(float(cost_efficiency_ratio), 2),
                'operational_costs': float(total_project_costs) if total_project_costs else 0,
                'cost_alerts': cost_alerts,
                'salary_breakdown': self._get_salary_breakdown(team_cost_metrics)
            }
            
            # Ensure all nested values are also serializable
            return self._ensure_json_serializable(result)
            
        except Exception as e:
            logger.error(f"Error analyzing team costs: {str(e)}")
            return {}

    def _calculate_cost_efficiency(self, roi: float, efficiency_score: float) -> float:
        """Calculate combined cost-efficiency score."""
        # Weighted combination: 60% efficiency, 40% ROI impact
        roi_normalized = max(0, min(100, roi + 50))  # Normalize ROI to 0-100 scale
        return round((efficiency_score * 0.6) + (roi_normalized * 0.4), 1)

    def _generate_cost_alerts(self, team_metrics: Dict, team_roi: float) -> List[Dict]:
        """Generate cost-related alerts for team management."""
        alerts = []
        
        # Team ROI alerts
        if team_roi < 50:
            alerts.append({
                'type': 'danger',
                'title': 'ROI del Equipo Bajo',
                'message': f'El ROI del equipo es {team_roi:.1f}%, por debajo del objetivo (50%)',
                'priority': 'high'
            })
        elif team_roi < 100:
            alerts.append({
                'type': 'warning',
                'title': 'ROI del Equipo Moderado',
                'message': f'El ROI del equipo es {team_roi:.1f}%, revisar optimizaciones',
                'priority': 'medium'
            })
        
        # Individual member alerts
        low_roi_members = [
            name for name, data in team_metrics.items() 
            if data['roi_percentage'] < 20
        ]
        
        if low_roi_members:
            alerts.append({
                'type': 'warning',
                'title': 'Miembros con ROI Bajo',
                'message': f'{len(low_roi_members)} miembro(s) con ROI < 20%: {", ".join(low_roi_members[:3])}',
                'priority': 'medium'
            })
        
        # High cost per EDP alerts
        high_cost_members = [
            name for name, data in team_metrics.items() 
            if data['cost_per_edp'] > 200_000
        ]
        
        if high_cost_members:
            alerts.append({
                'type': 'info',
                'title': 'Costos por EDP Elevados',
                'message': f'{len(high_cost_members)} miembro(s) con costo/EDP > $200K',
                'priority': 'low'
            })
        
        return alerts

    def _get_salary_breakdown(self, team_metrics: Dict) -> Dict:
        """Get salary breakdown by role."""
        breakdown = {}
        total_cost = sum(data['monthly_salary'] for data in team_metrics.values())
        
        for member_name, data in team_metrics.items():
            role = data['role']
            if role not in breakdown:
                breakdown[role] = {
                    'count': 0,
                    'total_cost': 0,
                    'avg_roi': 0,
                    'members': [],
                    'monthly_salary': int(data['monthly_salary'])
                }
            
            breakdown[role]['count'] += 1
            breakdown[role]['total_cost'] += int(data['monthly_salary'])
            breakdown[role]['avg_roi'] += float(data['roi_percentage'])
            breakdown[role]['members'].append(member_name)
        
        # Calculate averages and percentages
        for role_data in breakdown.values():
            if role_data['count'] > 0:
                role_data['avg_roi'] = round(float(role_data['avg_roi'] / role_data['count']), 1)
                role_data['percentage'] = round(float(role_data['total_cost'] / total_cost * 100), 1) if total_cost > 0 else 0
        
        return breakdown

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

    def get_kanban_data(self, manager_name: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get kanban board data filtered for a specific project manager."""
        try:
            from ..services.control_panel_service import KanbanService
            
            # Get all EDPs for this manager
            proyectos = self.pm_repo.get_manager_projects(manager_name)
            df = pd.DataFrame(proyectos)
            
            if df.empty:
                return {
                    'columnas': {},
                    'filter_options': {
                        'meses': [],
                        'proyectos': [],
                        'clientes': [],
                        'estados_detallados': []
                    },
                    'estadisticas': {}
                }
            
            # Initialize kanban service
            kanban_service = KanbanService()
            
            # Apply additional filters if provided
            if filters:
                # Remove the jefe_proyecto filter since we already filtered by manager
                filters_copy = filters.copy()
                filters_copy.pop('jefe_proyecto', None)
                
                # Apply other filters
                for key, value in filters_copy.items():
                    if value and key in df.columns:
                        if key in ['monto_min', 'monto_max']:
                            # Handle numeric filters
                            try:
                                filter_value = float(value)
                                if key == 'monto_min':
                                    df = df[pd.to_numeric(df.get('monto_aprobado', 0), errors='coerce') >= filter_value]
                                elif key == 'monto_max':
                                    df = df[pd.to_numeric(df.get('monto_aprobado', 0), errors='coerce') <= filter_value]
                            except ValueError:
                                pass
                        elif key == 'buscar':
                            # Handle search filter
                            search_cols = ['proyecto', 'cliente', 'n_edp', 'observaciones']
                            mask = pd.Series([False] * len(df))
                            for col in search_cols:
                                if col in df.columns:
                                    mask |= df[col].astype(str).str.contains(value, case=False, na=False)
                            df = df[mask]
                        else:
                            # Handle exact match filters
                            df = df[df[key].astype(str).str.contains(value, case=False, na=False)]
            
            # Get kanban data using the kanban service
            kanban_response = kanban_service.get_kanban_board_data(df, filters or {})
            
            if not kanban_response.success:
                logger.error(f"Error getting kanban data: {kanban_response.message}")
                return {}
            
            kanban_data = kanban_response.data
            
            # Add manager-specific filter options
            if not df.empty:
                kanban_data['filter_options'] = {
                    'meses': sorted(df['mes'].dropna().unique().tolist()) if 'mes' in df.columns else [],
                    'proyectos': sorted(df['proyecto'].dropna().unique().tolist()) if 'proyecto' in df.columns else [],
                    'clientes': sorted(df['cliente'].dropna().unique().tolist()) if 'cliente' in df.columns else [],
                    'estados_detallados': sorted(df['estado_detallado'].dropna().unique().tolist()) if 'estado_detallado' in df.columns else []
                }
            
            return kanban_data
            
        except Exception as e:
            logger.error(f"Error getting kanban data for {manager_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return {}

    def update_edp_status(self, edp_id: int, nuevo_estado: str, estado_anterior: str, usuario: str) -> bool:
        """Update EDP status and log the change."""
        try:
            # Update the EDP status in the repository
            success = self.pm_repo.update_edp_status(edp_id, nuevo_estado, estado_anterior, usuario)
            
            if success:
                logger.info(f"EDP {edp_id} status updated from {estado_anterior} to {nuevo_estado} by {usuario}")
                return True
            else:
                logger.error(f"Failed to update EDP {edp_id} status")
                return False
                
        except Exception as e:
            logger.error(f"Error updating EDP {edp_id} status: {str(e)}")
            logger.error(traceback.format_exc())
            return False
