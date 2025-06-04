"""
EDP Service for business logic related to EDP operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models import EDP, LogEntry
from ..repositories.edp_repository import EDPRepository
from ..repositories.log_repository import LogRepository
from . import BaseService, ServiceResponse, ValidationError, BusinessLogicError


class EDPService(BaseService):
    """Service for managing EDP business logic."""
    
    def __init__(self):
        super().__init__()
        self.edp_repository = EDPRepository()
        self.log_repository = LogRepository()
    
    def get_all_edps(self) -> ServiceResponse:
        """Get all EDPs with enriched data."""
        try:
            edps = self.edp_repository.find_all()
            
            # Enrich EDPs with calculated fields
            enriched_edps = []
            for edp in edps:
                edp_dict = self._edp_to_dict(edp)
                edp_dict['health_score'] = self._calculate_health_score(edp)
                edp_dict['status_color'] = self._get_status_color(edp.status)
                edp_dict['days_since_last_update'] = self._days_since_last_update(edp)
                enriched_edps.append(edp_dict)
            
            return ServiceResponse(
                success=True,
                data=enriched_edps,
                message=f"Retrieved {len(enriched_edps)} EDPs successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving EDPs: {str(e)}"
            )
    
    def get_edp_by_id(self, edp_id: str) -> ServiceResponse:
        """Get a specific EDP with detailed information."""
        try:
            edp = self.edp_repository.find_by_id(edp_id)
            if not edp:
                return ServiceResponse(
                    success=False,
                    message=f"EDP with ID {edp_id} not found"
                )
            
            # Get recent logs for this EDP
            logs = self.log_repository.find_by_edp_id(edp_id)
            recent_logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:5]
            
            edp_data = self._edp_to_dict(edp)
            edp_data['health_score'] = self._calculate_health_score(edp)
            edp_data['status_color'] = self._get_status_color(edp.status)
            edp_data['days_since_last_update'] = self._days_since_last_update(edp)
            edp_data['recent_logs'] = [self._log_to_dict(log) for log in recent_logs]
            
            return ServiceResponse(
                success=True,
                data=edp_data,
                message="EDP retrieved successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving EDP: {str(e)}"
            )
    
    def create_edp(self, edp_data: Dict[str, Any]) -> ServiceResponse:
        """Create a new EDP."""
        try:
            # Validate required fields
            required_fields = ['name', 'responsible', 'status']
            if not self.validate_required_fields(edp_data, required_fields):
                return ServiceResponse(
                    success=False,
                    message="Missing required fields",
                    errors={'required_fields': required_fields}
                )
            
            # Create EDP object
            edp_id = self.generate_id()
            edp = EDP(
                id=edp_id,
                name=self.sanitize_string(edp_data['name']),
                description=self.sanitize_string(edp_data.get('description', '')),
                responsible=self.sanitize_string(edp_data['responsible']),
                status=edp_data['status'],
                priority=edp_data.get('priority', 'medium'),
                budget=float(edp_data['budget']) if edp_data.get('budget') else None,
                start_date=datetime.fromisoformat(edp_data['start_date']) if edp_data.get('start_date') else None,
                end_date=datetime.fromisoformat(edp_data['end_date']) if edp_data.get('end_date') else None,
                tags=edp_data.get('tags', []),
                kpis=edp_data.get('kpis', {})
            )
            
            # Validate business rules
            validation_response = self._validate_edp_business_rules(edp)
            if not validation_response.success:
                return validation_response
            
            # Save EDP
            if self.edp_repository.create(edp):
                # Create log entry
                self._log_edp_action(edp_id, 'created', f"EDP '{edp.name}' created", edp_data.get('user', 'system'))
                
                return ServiceResponse(
                    success=True,
                    data={'id': edp_id},
                    message="EDP created successfully"
                )
            else:
                return ServiceResponse(
                    success=False,
                    message="Failed to create EDP"
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error creating EDP: {str(e)}"
            )
    
    def update_edp(self, edp_id: str, edp_data: Dict[str, Any]) -> ServiceResponse:
        """Update an existing EDP."""
        try:
            # Get existing EDP
            existing_edp = self.edp_repository.find_by_id(edp_id)
            if not existing_edp:
                return ServiceResponse(
                    success=False,
                    message=f"EDP with ID {edp_id} not found"
                )
            
            # Update fields
            updated_fields = []
            if 'name' in edp_data and edp_data['name'] != existing_edp.name:
                existing_edp.name = self.sanitize_string(edp_data['name'])
                updated_fields.append('name')
            
            if 'description' in edp_data and edp_data['description'] != existing_edp.description:
                existing_edp.description = self.sanitize_string(edp_data['description'])
                updated_fields.append('description')
            
            if 'responsible' in edp_data and edp_data['responsible'] != existing_edp.responsible:
                existing_edp.responsible = self.sanitize_string(edp_data['responsible'])
                updated_fields.append('responsible')
            
            if 'status' in edp_data and edp_data['status'] != existing_edp.status:
                old_status = existing_edp.status
                existing_edp.status = edp_data['status']
                updated_fields.append('status')
                
                # Log status change
                self._log_edp_action(
                    edp_id, 
                    'status_change', 
                    f"Status changed from {old_status} to {edp_data['status']}", 
                    edp_data.get('user', 'system')
                )
            
            if 'priority' in edp_data and edp_data['priority'] != existing_edp.priority:
                existing_edp.priority = edp_data['priority']
                updated_fields.append('priority')
            
            if 'budget' in edp_data:
                new_budget = float(edp_data['budget']) if edp_data['budget'] else None
                if new_budget != existing_edp.budget:
                    existing_edp.budget = new_budget
                    updated_fields.append('budget')
            
            # Update timestamps
            existing_edp.last_update = datetime.now()
            
            # Validate business rules
            validation_response = self._validate_edp_business_rules(existing_edp)
            if not validation_response.success:
                return validation_response
            
            # Save changes
            if self.edp_repository.update(existing_edp):
                if updated_fields:
                    self._log_edp_action(
                        edp_id, 
                        'updated', 
                        f"Updated fields: {', '.join(updated_fields)}", 
                        edp_data.get('user', 'system')
                    )
                
                return ServiceResponse(
                    success=True,
                    data={'updated_fields': updated_fields},
                    message="EDP updated successfully"
                )
            else:
                return ServiceResponse(
                    success=False,
                    message="Failed to update EDP"
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error updating EDP: {str(e)}"
            )
    
    def update_edp_kpis(self, edp_id: str, kpis: Dict[str, Any]) -> ServiceResponse:
        """Update KPIs for an EDP."""
        try:
            success = self.edp_repository.update_kpis(edp_id, kpis)
            if success:
                self._log_edp_action(edp_id, 'kpi_update', "KPIs updated", "system")
                return ServiceResponse(
                    success=True,
                    message="KPIs updated successfully"
                )
            else:
                return ServiceResponse(
                    success=False,
                    message="Failed to update KPIs"
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error updating KPIs: {str(e)}"
            )
    
    def get_edp_statistics(self) -> ServiceResponse:
        """Get overall EDP statistics."""
        try:
            statistics = self.edp_repository.get_edp_statistics()
            
            # Add calculated metrics
            statistics['health_distribution'] = self._get_health_distribution()
            statistics['status_distribution'] = self._get_status_distribution()
            statistics['priority_distribution'] = self._get_priority_distribution()
            
            return ServiceResponse(
                success=True,
                data=statistics,
                message="Statistics retrieved successfully"
            )
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error retrieving statistics: {str(e)}"
            )
    
    def _validate_edp_business_rules(self, edp: EDP) -> ServiceResponse:
        """Validate business rules for EDP."""
        errors = {}
        
        # Validate date ranges
        if edp.start_date and edp.end_date and edp.start_date > edp.end_date:
            errors['dates'] = "Start date cannot be after end date"
        
        # Validate budget
        if edp.budget is not None and edp.budget < 0:
            errors['budget'] = "Budget cannot be negative"
        
        # Validate status transitions
        if edp.status not in ['planning', 'active', 'on_hold', 'completed', 'cancelled']:
            errors['status'] = "Invalid status"
        
        if errors:
            return ServiceResponse(
                success=False,
                message="Validation failed",
                errors=errors
            )
        
        return ServiceResponse(success=True)
    
    def _calculate_health_score(self, edp: EDP) -> float:
        """Calculate a health score for the EDP based on various factors."""
        score = 100.0
        
        # Deduct points for overdue EDPs
        if edp.end_date and datetime.now() > edp.end_date and edp.status != 'completed':
            days_overdue = (datetime.now() - edp.end_date).days
            score -= min(days_overdue * 2, 50)  # Max 50 points deduction
        
        # Deduct points for stale EDPs (no recent updates)
        days_since_update = self._days_since_last_update(edp)
        if days_since_update > 30:
            score -= min((days_since_update - 30) * 1, 30)  # Max 30 points deduction
        
        # Adjust based on status
        status_modifiers = {
            'completed': 0,
            'active': 0,
            'planning': -5,
            'on_hold': -20,
            'cancelled': -50
        }
        score += status_modifiers.get(edp.status, 0)
        
        return max(0, min(100, score))
    
    def _get_status_color(self, status: str) -> str:
        """Get color code for status."""
        color_map = {
            'planning': '#FFA500',  # Orange
            'active': '#28A745',    # Green
            'on_hold': '#FFC107',   # Yellow
            'completed': '#6F42C1', # Purple
            'cancelled': '#DC3545'  # Red
        }
        return color_map.get(status, '#6C757D')  # Default gray
    
    def _days_since_last_update(self, edp: EDP) -> int:
        """Calculate days since last update."""
        if edp.last_update:
            return (datetime.now() - edp.last_update).days
        return (datetime.now() - edp.created_at).days
    
    def _get_health_distribution(self) -> Dict[str, int]:
        """Get distribution of health scores."""
        edps = self.edp_repository.find_all()
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for edp in edps:
            score = self._calculate_health_score(edp)
            if score >= 90:
                distribution['excellent'] += 1
            elif score >= 70:
                distribution['good'] += 1
            elif score >= 50:
                distribution['fair'] += 1
            else:
                distribution['poor'] += 1
        
        return distribution
    
    def _get_status_distribution(self) -> Dict[str, int]:
        """Get distribution of statuses."""
        edps = self.edp_repository.find_all()
        distribution = {}
        
        for edp in edps:
            status = edp.status
            distribution[status] = distribution.get(status, 0) + 1
        
        return distribution
    
    def _get_priority_distribution(self) -> Dict[str, int]:
        """Get distribution of priorities."""
        edps = self.edp_repository.find_all()
        distribution = {}
        
        for edp in edps:
            priority = edp.priority
            distribution[priority] = distribution.get(priority, 0) + 1
        
        return distribution
    
    def _log_edp_action(self, edp_id: str, action_type: str, message: str, user: str):
        """Log an action performed on an EDP."""
        log_entry = LogEntry(
            id=self.generate_id(),
            edp_id=edp_id,
            timestamp=datetime.now(),
            log_type=action_type,
            message=message,
            user=user,
            details={}
        )
        self.log_repository.create(log_entry)
    
    def _edp_to_dict(self, edp: EDP) -> Dict[str, Any]:
        """Convert EDP object to dictionary."""
        return {
            'id': edp.id,
            'name': edp.name,
            'description': edp.description,
            'responsible': edp.responsible,
            'status': edp.status,
            'priority': edp.priority,
            'budget': edp.budget,
            'start_date': edp.start_date.isoformat() if edp.start_date else None,
            'end_date': edp.end_date.isoformat() if edp.end_date else None,
            'created_at': edp.created_at.isoformat(),
            'last_update': edp.last_update.isoformat() if edp.last_update else None,
            'tags': edp.tags,
            'kpis': edp.kpis
        }
    
    def _log_to_dict(self, log: LogEntry) -> Dict[str, Any]:
        """Convert LogEntry object to dictionary."""
        return {
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'log_type': log.log_type,
            'message': log.message,
            'user': log.user,
            'details': log.details
        }
