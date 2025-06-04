"""
KPI Service for managing KPI calculations and analytics.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from statistics import mean, median
from ..models import EDP, KPI
from ..repositories.edp_repository import EDPRepository
from . import BaseService, ServiceResponse


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
            
            # Financial KPIs
            kpis.update(self._calculate_financial_kpis(edp))
            
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
            
            # Generate mock trend data
            trend_data = self._generate_mock_trend_data(edp_id, start_date, end_date)
            
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
    
    def _calculate_financial_kpis(self, edp: EDP) -> Dict[str, Any]:
        """Calculate financial KPIs."""
        kpis = {}
        
        if edp.budget:
            # For now, using mock data for spent amount
            # In real implementation, this would come from financial tracking
            mock_spent_percentage = 0.65  # 65% spent
            spent_amount = edp.budget * mock_spent_percentage
            
            kpis['budget_total'] = edp.budget
            kpis['budget_spent'] = round(spent_amount, 2)
            kpis['budget_remaining'] = round(edp.budget - spent_amount, 2)
            kpis['budget_utilization'] = round(mock_spent_percentage * 100, 2)
            
            # Cost efficiency (mock calculation)
            if edp.status == 'completed':
                kpis['cost_efficiency'] = round((edp.budget / spent_amount * 100), 2) if spent_amount > 0 else 100
        
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
    
    def _generate_mock_trend_data(self, edp_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate mock trend data for visualization."""
        # This is a placeholder for actual trend data
        # In a real implementation, this would query historical data
        
        import random
        
        days = (end_date - start_date).days
        dates = [start_date + timedelta(days=i) for i in range(days + 1)]
        
        trend_data = {
            'dates': [date.strftime('%Y-%m-%d') for date in dates],
            'completion_rate': [min(100, max(0, 50 + random.randint(-5, 10) + i*0.5)) for i in range(len(dates))],
            'budget_utilization': [min(100, max(0, 30 + random.randint(-3, 5) + i*0.3)) for i in range(len(dates))],
            'quality_score': [min(100, max(60, 85 + random.randint(-5, 5))) for _ in range(len(dates))]
        }
        
        return trend_data
