"""
Dashboard Service for managing dashboard data and visualizations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models import EDP
from ..repositories.edp_repository import EDPRepository
from ..repositories.log_repository import LogRepository
from .edp_service import EDPService
from .kpi_service import KPIService
from . import BaseService, ServiceResponse


class DashboardService(BaseService):
    """Service for managing dashboard data and analytics."""
    
    def __init__(self):
        super().__init__()
        self.edp_repository = EDPRepository()
        self.log_repository = LogRepository()
        self.edp_service = EDPService()
        self.kpi_service = KPIService()
    
    def get_dashboard_overview(self, filters: Dict[str, Any] = None) -> ServiceResponse:
        """Get comprehensive dashboard overview data."""
        try:
            filters = filters or {}
            
            # Get all EDPs
            edps_response = self.edp_service.get_all_edps()
            if not edps_response.success:
                return edps_response
            
            edps_data = edps_response.data
            
            # Get KPI statistics
            kpi_response = self.kpi_service.calculate_all_kpis()
            kpi_data = kpi_response.data if kpi_response.success else {}
            
            # Get recent activity
            recent_logs = self._get_recent_activity(limit=10)
            
            # Calculate overview metrics
            overview_metrics = self._calculate_overview_metrics(edps_data)
            
            # Get chart data
            chart_data = self._prepare_chart_data(edps_data, kpi_data)
            
            # Get alerts and notifications
            alerts = self._get_alerts(edps_data)
            
            dashboard_data = {
                'overview_metrics': overview_metrics,
                'chart_data': chart_data,
                'recent_activity': recent_logs,
                'alerts': alerts,
                'kpi_summary': kpi_data.get('aggregate_kpis', {}),
                'last_updated': datetime.now().isoformat()
            }
            
            return ServiceResponse(
                success=True,
                data=dashboard_data,
                message="Dashboard overview retrieved successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving dashboard overview: {str(e)}"
            )
    
    def get_status_summary(self) -> ServiceResponse:
        """Get status summary for all EDPs."""
        try:
            edps = self.edp_repository.find_all()
            
            status_summary = {
                'total': len(edps),
                'by_status': {},
                'by_priority': {},
                'overdue': 0,
                'completed_this_month': 0,
                'active': 0
            }
            
            now = datetime.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            for edp in edps:
                # Count by status
                status = edp.status
                status_summary['by_status'][status] = status_summary['by_status'].get(status, 0) + 1
                
                # Count by priority
                priority = edp.priority
                status_summary['by_priority'][priority] = status_summary['by_priority'].get(priority, 0) + 1
                
                # Count overdue
                if (edp.end_date and now > edp.end_date and 
                    edp.status not in ['completed', 'cancelled']):
                    status_summary['overdue'] += 1
                
                # Count completed this month
                if (edp.status == 'completed' and edp.last_update and 
                    edp.last_update >= month_start):
                    status_summary['completed_this_month'] += 1
                
                # Count active
                if edp.status == 'active':
                    status_summary['active'] += 1
            
            return ServiceResponse(
                success=True,
                data=status_summary,
                message="Status summary retrieved successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving status summary: {str(e)}"
            )
    
    def get_performance_metrics(self) -> ServiceResponse:
        """Get performance metrics for dashboard."""
        try:
            edps = self.edp_repository.find_all()
            
            if not edps:
                return ServiceResponse(
                    success=True,
                    data={'message': 'No EDPs found'},
                    message="No data available"
                )
            
            # Calculate performance metrics
            total_edps = len(edps)
            completed_edps = sum(1 for edp in edps if edp.status == 'completed')
            active_edps = sum(1 for edp in edps if edp.status == 'active')
            overdue_edps = sum(1 for edp in edps if self._is_overdue(edp))
            
            # Calculate average completion time for completed EDPs
            completion_times = []
            for edp in edps:
                if edp.status == 'completed' and edp.start_date:
                    completion_time = (edp.last_update or datetime.now()) - edp.start_date
                    completion_times.append(completion_time.days)
            
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
            
            # Calculate budget utilization
            total_budget = sum(edp.budget for edp in edps if edp.budget)
            # Mock spent amount (in real implementation, this would come from actual data)
            mock_spent_ratio = 0.65
            total_spent = total_budget * mock_spent_ratio
            
            performance_metrics = {
                'completion_rate': round((completed_edps / total_edps * 100), 2) if total_edps > 0 else 0,
                'active_rate': round((active_edps / total_edps * 100), 2) if total_edps > 0 else 0,
                'overdue_rate': round((overdue_edps / total_edps * 100), 2) if total_edps > 0 else 0,
                'avg_completion_time_days': round(avg_completion_time, 1),
                'budget_utilization': round((total_spent / total_budget * 100), 2) if total_budget > 0 else 0,
                'total_budget': total_budget,
                'total_spent': round(total_spent, 2),
                'budget_remaining': round(total_budget - total_spent, 2)
            }
            
            return ServiceResponse(
                success=True,
                data=performance_metrics,
                message="Performance metrics calculated successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error calculating performance metrics: {str(e)}"
            )
    
    def get_recent_activity(self, limit: int = 20) -> ServiceResponse:
        """Get recent activity logs."""
        try:
            recent_logs = self._get_recent_activity(limit)
            
            return ServiceResponse(
                success=True,
                data=recent_logs,
                message=f"Retrieved {len(recent_logs)} recent activities"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving recent activity: {str(e)}"
            )
    
    def get_alerts_and_notifications(self) -> ServiceResponse:
        """Get alerts and notifications for the dashboard."""
        try:
            edps_response = self.edp_service.get_all_edps()
            if not edps_response.success:
                return edps_response
            
            alerts = self._get_alerts(edps_response.data)
            
            return ServiceResponse(
                success=True,
                data=alerts,
                message=f"Retrieved {len(alerts)} alerts"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving alerts: {str(e)}"
            )
    
    def get_trend_data(self, days: int = 30) -> ServiceResponse:
        """Get trend data for charts."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Generate mock trend data (in real implementation, this would query historical data)
            trend_data = self._generate_trend_data(start_date, end_date)
            
            return ServiceResponse(
                success=True,
                data=trend_data,
                message=f"Retrieved {days}-day trend data"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving trend data: {str(e)}"
            )
    
    def get_edp_health_scores(self) -> ServiceResponse:
        """Get health scores for all EDPs."""
        try:
            edps_response = self.edp_service.get_all_edps()
            if not edps_response.success:
                return edps_response
            
            health_data = []
            for edp_data in edps_response.data:
                health_data.append({
                    'id': edp_data['id'],
                    'name': edp_data['name'],
                    'health_score': edp_data.get('health_score', 0),
                    'status': edp_data['status'],
                    'priority': edp_data['priority']
                })
            
            # Sort by health score (lowest first for attention)
            health_data.sort(key=lambda x: x['health_score'])
            
            return ServiceResponse(
                success=True,
                data=health_data,
                message="Health scores retrieved successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving health scores: {str(e)}"
            )
    
    def _calculate_overview_metrics(self, edps_data: List[Dict]) -> Dict[str, Any]:
        """Calculate high-level overview metrics."""
        if not edps_data:
            return {}
        
        total_edps = len(edps_data)
        completed = sum(1 for edp in edps_data if edp['status'] == 'completed')
        active = sum(1 for edp in edps_data if edp['status'] == 'active')
        overdue = sum(1 for edp in edps_data if edp.get('days_overdue', 0) > 0)
        
        # Calculate average health score
        health_scores = [edp.get('health_score', 0) for edp in edps_data]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        
        return {
            'total_edps': total_edps,
            'completed_edps': completed,
            'active_edps': active,
            'overdue_edps': overdue,
            'completion_rate': round((completed / total_edps * 100), 1) if total_edps > 0 else 0,
            'average_health_score': round(avg_health, 1),
            'health_status': self._get_health_status(avg_health)
        }
    
    def _prepare_chart_data(self, edps_data: List[Dict], kpi_data: Dict) -> Dict[str, Any]:
        """Prepare data for dashboard charts."""
        chart_data = {}
        
        # Status distribution pie chart
        status_counts = {}
        priority_counts = {}
        
        for edp in edps_data:
            status = edp['status']
            priority = edp['priority']
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        chart_data['status_distribution'] = {
            'labels': list(status_counts.keys()),
            'data': list(status_counts.values())
        }
        
        chart_data['priority_distribution'] = {
            'labels': list(priority_counts.keys()),
            'data': list(priority_counts.values())
        }
        
        # Health score distribution
        health_ranges = {'Poor (0-49)': 0, 'Fair (50-69)': 0, 'Good (70-89)': 0, 'Excellent (90-100)': 0}
        
        for edp in edps_data:
            health_score = edp.get('health_score', 0)
            if health_score < 50:
                health_ranges['Poor (0-49)'] += 1
            elif health_score < 70:
                health_ranges['Fair (50-69)'] += 1
            elif health_score < 90:
                health_ranges['Good (70-89)'] += 1
            else:
                health_ranges['Excellent (90-100)'] += 1
        
        chart_data['health_distribution'] = {
            'labels': list(health_ranges.keys()),
            'data': list(health_ranges.values())
        }
        
        return chart_data
    
    def _get_alerts(self, edps_data: List[Dict]) -> List[Dict[str, Any]]:
        """Generate alerts based on EDP data."""
        alerts = []
        
        for edp in edps_data:
            # Overdue alerts
            if edp.get('days_overdue', 0) > 0:
                alerts.append({
                    'type': 'error',
                    'title': 'Overdue EDP',
                    'message': f"EDP '{edp['name']}' is {edp['days_overdue']} days overdue",
                    'edp_id': edp['id'],
                    'priority': 'high'
                })
            
            # Low health score alerts
            health_score = edp.get('health_score', 100)
            if health_score < 50:
                alerts.append({
                    'type': 'warning',
                    'title': 'Low Health Score',
                    'message': f"EDP '{edp['name']}' has a low health score ({health_score})",
                    'edp_id': edp['id'],
                    'priority': 'medium'
                })
            
            # Stale EDP alerts
            days_since_update = edp.get('days_since_last_update', 0)
            if days_since_update > 30:
                alerts.append({
                    'type': 'info',
                    'title': 'Stale EDP',
                    'message': f"EDP '{edp['name']}' hasn't been updated in {days_since_update} days",
                    'edp_id': edp['id'],
                    'priority': 'low'
                })
        
        # Sort alerts by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return alerts[:10]  # Return top 10 alerts
    
    def _get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity logs."""
        try:
            logs = self.log_repository.find_all()
            # Sort by timestamp, most recent first
            recent_logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            return [
                {
                    'id': log.id,
                    'edp_id': log.edp_id,
                    'timestamp': log.timestamp.isoformat(),
                    'type': log.log_type,
                    'message': log.message,
                    'user': log.user,
                    'relative_time': self._get_relative_time(log.timestamp)
                }
                for log in recent_logs
            ]
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    def _is_overdue(self, edp: EDP) -> bool:
        """Check if an EDP is overdue."""
        return (edp.end_date and datetime.now() > edp.end_date and 
                edp.status not in ['completed', 'cancelled'])
    
    def _get_health_status(self, avg_health: float) -> str:
        """Get overall health status based on average health score."""
        if avg_health >= 90:
            return 'excellent'
        elif avg_health >= 70:
            return 'good'
        elif avg_health >= 50:
            return 'fair'
        else:
            return 'poor'
    
    def _get_relative_time(self, timestamp: datetime) -> str:
        """Get relative time string."""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def _generate_trend_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate trend data for charts (mock implementation)."""
        import random
        
        days = (end_date - start_date).days
        dates = [start_date + timedelta(days=i) for i in range(days + 1)]
        
        return {
            'completion_trend': {
                'dates': [date.strftime('%Y-%m-%d') for date in dates],
                'values': [min(100, max(0, 60 + random.randint(-5, 5) + i*0.2)) for i in range(len(dates))]
            },
            'health_trend': {
                'dates': [date.strftime('%Y-%m-%d') for date in dates],
                'values': [min(100, max(50, 80 + random.randint(-5, 5))) for _ in range(len(dates))]
            },
            'activity_trend': {
                'dates': [date.strftime('%Y-%m-%d') for date in dates],
                'values': [random.randint(5, 25) for _ in range(len(dates))]
            }
        }
