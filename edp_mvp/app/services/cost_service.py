"""
Cost Service - Service for handling cost management operations.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from . import BaseService, ServiceResponse
from ..repositories.cost_repository import CostRepository
from ..models import Cost
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils


class CostService(BaseService):
    """Service for handling cost management operations."""
    
    def __init__(self):
        super().__init__()
        self.cost_repository = CostRepository()
        self.date_utils = DateUtils()
        self.format_utils = FormatUtils()
    
    def get_cost_dashboard_data(self, filters: Dict[str, Any] = None) -> ServiceResponse:
        """Get cost dashboard data with KPIs and analytics."""
        try:
            filters = filters or {}
            
            # Get all costs as DataFrame
            costs_response = self.cost_repository.find_all_dataframe()
            if not costs_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message="Failed to load costs data",
                    data=self._get_empty_cost_dashboard()
                )
            
            df_costs = costs_response.get('data', pd.DataFrame())
            print(f'importe_neto: {df_costs.get("importe_neto", 0)}')
            
            if df_costs.empty:
                return ServiceResponse(
                    success=True,
                    message="No cost data available",
                    data=self._get_empty_cost_dashboard()
                )
            
            # Apply filters
            df_filtered = self._apply_filters(df_costs, filters)
            
            # Calculate KPIs
            cost_kpis = self._calculate_cost_kpis(df_filtered)
            
            # Generate charts data
            charts_data = self._generate_cost_charts(df_filtered)
            
            # Get cost breakdown
            breakdown = self._get_cost_breakdown(df_filtered)
            
            # Get pending payments
            pending_payments = self._get_pending_payments_summary(df_filtered)
            
            # Get provider analysis
            provider_analysis = self._get_provider_analysis(df_filtered)
            
            dashboard_data = {
                'kpis': cost_kpis,
                'charts': charts_data,
                'breakdown': breakdown,
                'pending_payments': pending_payments,
                'provider_analysis': provider_analysis,
                'filters_applied': filters,
                'last_updated': datetime.now().isoformat()
            }
            
            return ServiceResponse(
                success=True,
                data=dashboard_data,
                message="Cost dashboard data generated successfully"
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error generating cost dashboard: {str(e)}",
                data=self._get_empty_cost_dashboard()
            )
    
    def get_cost_trends(self, period: str = "monthly") -> ServiceResponse:
        """Get cost trends analysis."""
        try:
            costs_response = self.cost_repository.find_all_dataframe()
            if not costs_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message="Failed to load costs data"
                )
            
            df_costs = costs_response.get('data', pd.DataFrame())
            if df_costs.empty:
                return ServiceResponse(
                    success=True,
                    message="No cost data available for trends",
                    data={'trends': [], 'period': period}
                )
            
            # Calculate trends
            trends = self._calculate_cost_trends(df_costs, period)
            
            return ServiceResponse(
                success=True,
                data={'trends': trends, 'period': period},
                message="Cost trends calculated successfully"
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error calculating cost trends: {str(e)}"
            )
    
    def get_overdue_analysis(self) -> ServiceResponse:
        """Get overdue costs analysis."""
        try:
            costs_response = self.cost_repository.find_all_dataframe()
            if not costs_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message="Failed to load costs data"
                )
            
            df_costs = costs_response.get('data', pd.DataFrame())
            if df_costs.empty:
                return ServiceResponse(
                    success=True,
                    message="No cost data available",
                    data={'overdue_costs': [], 'summary': {}}
                )
            
            # Get overdue costs
            overdue_analysis = self._analyze_overdue_costs(df_costs)
            
            return ServiceResponse(
                success=True,
                data=overdue_analysis,
                message="Overdue analysis completed successfully"
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error analyzing overdue costs: {str(e)}"
            )
    
    def get_cost_forecast(self, months: int = 6) -> ServiceResponse:
        """Get cost forecast for specified months."""
        try:
            costs_response = self.cost_repository.find_all_dataframe()
            if not costs_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message="Failed to load costs data"
                )
            
            df_costs = costs_response.get('data', pd.DataFrame())
            if df_costs.empty:
                return ServiceResponse(
                    success=True,
                    message="No cost data available for forecast",
                    data={'forecast': [], 'months': months}
                )
            
            # Generate forecast
            forecast = self._generate_cost_forecast(df_costs, months)
            
            return ServiceResponse(
                success=True,
                data={'forecast': forecast, 'months': months},
                message="Cost forecast generated successfully"
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error generating cost forecast: {str(e)}"
            )
    
    def _calculate_cost_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate cost KPIs."""
        if df.empty:
            return self._get_empty_kpis()
        
        try:
            # Basic metrics
            total_costs = len(df)
            total_amount = df['importe_neto'].sum() if 'importe_neto' in df.columns else 0
       
            # Status breakdown
            paid_costs = len(df[df.get('estado_costo', '') == 'pagado'])
            pending_costs = len(df[df.get('estado_costo', '') != 'pagado'])
            
            # Payment metrics
            if 'importe_neto' in df.columns:
                paid_amount = df[df.get('estado_costo', '') == 'pagado']['importe_neto'].sum()
                pending_amount = df[df.get('estado_costo', '') != 'pagado']['importe_neto'].sum()
            else:
                paid_amount = 0
                pending_amount = 0
            
            # Overdue analysis
            today = pd.Timestamp.now()
            if 'fecha_vencimiento' in df.columns and 'estado_costo' in df.columns:
                overdue_mask = (
                    (pd.to_datetime(df['fecha_vencimiento'], errors='coerce') < today) &
                    (df['estado_costo'] != 'pagado')
                )
                overdue_costs = df[overdue_mask]
                overdue_count = len(overdue_costs)
                overdue_amount = overdue_costs['importe_neto'].sum() if 'importe_neto' in overdue_costs.columns else 0
            else:
                overdue_count = 0
                overdue_amount = 0
            
            # Payment rate
            payment_rate = (paid_costs / total_costs * 100) if total_costs > 0 else 0
            
            # Average cost
            avg_cost = total_amount / total_costs if total_costs > 0 else 0
            
            # Type breakdown (OPEX vs CAPEX)
            type_breakdown = {}
            if 'tipo_costo' in df.columns:
                type_counts = df['tipo_costo'].value_counts()
                type_breakdown = {
                    str(k): int(v) for k, v in type_counts.items()
                }
            
            return {
                'total_costs': total_costs,
                'total_amount': self.format_utils.format_currency(total_amount),
                'paid_costs': paid_costs,
                'pending_costs': pending_costs,
                'paid_amount': self.format_utils.format_currency(paid_amount),
                'pending_amount': self.format_utils.format_currency(pending_amount),
                'overdue_count': overdue_count,
                'overdue_amount': self.format_utils.format_currency(overdue_amount),
                'payment_rate': round(payment_rate, 1),
                'avg_cost': self.format_utils.format_currency(avg_cost),
                'type_breakdown': type_breakdown
            }
            
        except Exception as e:
            print(f"Error calculating cost KPIs: {e}")
            return self._get_empty_kpis()
    
    def _generate_cost_charts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate chart data for cost dashboard."""
        if df.empty:
            return {'monthly_costs': [], 'cost_by_type': [], 'payment_status': []}
        
        try:
            charts = {}
            
            # Monthly costs trend
            if 'fecha_factura' in df.columns:
                df_monthly = df.copy()
                df_monthly['month'] = pd.to_datetime(
                    df_monthly['fecha_factura'], errors='coerce'
                ).dt.strftime('%Y-%m')
                
                monthly_costs = df_monthly.groupby('month')['importe_neto'].sum().reset_index()
                charts['monthly_costs'] = [
                    {'month': row['month'], 'amount': float(row['importe_neto'])}
                    for _, row in monthly_costs.iterrows()
                ]
            else:
                charts['monthly_costs'] = []
            
            # Cost by type
            if 'tipo_costo' in df.columns:
                type_costs = df.groupby('tipo_costo')['importe_neto'].sum().reset_index()
                charts['cost_by_type'] = [
                    {'type': row['tipo_costo'], 'amount': float(row['importe_neto'])}
                    for _, row in type_costs.iterrows()
                ]
            else:
                charts['cost_by_type'] = []
            
            # Payment status
            if 'estado_costo' in df.columns:
                status_costs = df.groupby('estado_costo')['importe_neto'].sum().reset_index()
                charts['payment_status'] = [
                    {'status': row['estado_costo'], 'amount': float(row['importe_neto'])}
                    for _, row in status_costs.iterrows()
                ]
            else:
                charts['payment_status'] = []
            
            # Top providers
            if 'proveedor' in df.columns:
                provider_costs = df.groupby('proveedor')['importe_neto'].sum().nlargest(10).reset_index()
                charts['top_providers'] = [
                    {'provider': row['proveedor'], 'amount': float(row['importe_neto'])}
                    for _, row in provider_costs.iterrows()
                ]
            else:
                charts['top_providers'] = []
            
            return charts
            
        except Exception as e:
            print(f"Error generating cost charts: {e}")
            return {'monthly_costs': [], 'cost_by_type': [], 'payment_status': []}
    
    def _get_cost_breakdown(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get detailed cost breakdown."""
        if df.empty:
            return {'by_project': [], 'by_category': [], 'by_provider': []}
        
        try:
            breakdown = {}
            
            # By project
            if 'project_id' in df.columns:
                project_breakdown = df.groupby('project_id').agg({
                    'importe_neto': 'sum',
                    'cost_id': 'count'
                }).reset_index()
                breakdown['by_project'] = [
                    {
                        'project': row['project_id'],
                        'amount': float(row['importe_neto']),
                        'count': int(row['cost_id'])
                    }
                    for _, row in project_breakdown.iterrows()
                ]
            else:
                breakdown['by_project'] = []
            
            # By category (tipo_costo)
            if 'tipo_costo' in df.columns:
                category_breakdown = df.groupby('tipo_costo').agg({
                    'importe_neto': 'sum',
                    'cost_id': 'count'
                }).reset_index()
                breakdown['by_category'] = [
                    {
                        'category': row['tipo_costo'],
                        'amount': float(row['importe_neto']),
                        'count': int(row['cost_id'])
                    }
                    for _, row in category_breakdown.iterrows()
                ]
            else:
                breakdown['by_category'] = []
            
            # By provider
            if 'proveedor' in df.columns:
                provider_breakdown = df.groupby('proveedor').agg({
                    'importe_neto': 'sum',
                    'cost_id': 'count'
                }).reset_index()
                breakdown['by_provider'] = [
                    {
                        'provider': row['proveedor'],
                        'amount': float(row['importe_neto']),
                        'count': int(row['cost_id'])
                    }
                    for _, row in provider_breakdown.iterrows()
                ]
            else:
                breakdown['by_provider'] = []
            
            return breakdown
            
        except Exception as e:
            print(f"Error getting cost breakdown: {e}")
            return {'by_project': [], 'by_category': [], 'by_provider': []}
    
    def _get_pending_payments_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get pending payments summary."""
        if df.empty:
            return {'total_pending': 0, 'overdue': 0, 'upcoming': []}
        
        try:
            # Filter pending payments
            pending_df = df[df.get('estado_costo', '') != 'pagado'].copy()
            
            if pending_df.empty:
                return {'total_pending': 0, 'overdue': 0, 'upcoming': []}
            
            total_pending = pending_df['importe_neto'].sum() if 'importe_neto' in pending_df.columns else 0
            
            # Overdue payments
            today = pd.Timestamp.now()
            if 'fecha_vencimiento' in pending_df.columns:
                overdue_df = pending_df[
                    pd.to_datetime(pending_df['fecha_vencimiento'], errors='coerce') < today
                ]
                overdue_amount = overdue_df['importe_neto'].sum() if 'importe_neto' in overdue_df.columns else 0
            else:
                overdue_amount = 0
            
            # Upcoming payments (next 30 days)
            upcoming = []
            if 'fecha_vencimiento' in pending_df.columns:
                next_30_days = today + pd.Timedelta(days=30)
                upcoming_df = pending_df[
                    (pd.to_datetime(pending_df['fecha_vencimiento'], errors='coerce') >= today) &
                    (pd.to_datetime(pending_df['fecha_vencimiento'], errors='coerce') <= next_30_days)
                ].sort_values('fecha_vencimiento')
                
                upcoming = [
                    {
                        'provider': row.get('proveedor', ''),
                        'amount': float(row.get('importe_neto', 0)),
                        'due_date': str(row.get('fecha_vencimiento', '')),
                        'days_until_due': (
                            pd.to_datetime(row.get('fecha_vencimiento')) - today
                        ).days if pd.notna(row.get('fecha_vencimiento')) else 0
                    }
                    for _, row in upcoming_df.head(10).iterrows()
                ]
            
            return {
                'total_pending': self.format_utils.format_currency(total_pending),
                'overdue': self.format_utils.format_currency(overdue_amount),
                'upcoming': upcoming
            }
            
        except Exception as e:
            print(f"Error getting pending payments summary: {e}")
            return {'total_pending': 0, 'overdue': 0, 'upcoming': []}
    
    def _get_provider_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get provider analysis."""
        if df.empty or 'proveedor' not in df.columns:
            return {'top_providers': [], 'payment_performance': []}
        
        try:
            # Top providers by amount
            top_providers = df.groupby('proveedor').agg({
                'importe_neto': 'sum',
                'cost_id': 'count'
            }).nlargest(10, 'importe_neto').reset_index()
            
            top_providers_list = [
                {
                    'provider': row['proveedor'],
                    'total_amount': float(row['importe_neto']),
                    'invoice_count': int(row['cost_id'])
                }
                for _, row in top_providers.iterrows()
            ]
            
            # Payment performance by provider
            payment_performance = []
            if 'estado_costo' in df.columns:
                provider_performance = df.groupby('proveedor').agg({
                    'cost_id': 'count',
                    'estado_costo': lambda x: (x == 'pagado').sum()
                }).reset_index()
                
                provider_performance['payment_rate'] = (
                    provider_performance['estado_costo'] / provider_performance['cost_id'] * 100
                )
                
                payment_performance = [
                    {
                        'provider': row['proveedor'],
                        'total_invoices': int(row['cost_id']),
                        'paid_invoices': int(row['estado_costo']),
                        'payment_rate': round(row['payment_rate'], 1)
                    }
                    for _, row in provider_performance.iterrows()
                ]
            
            return {
                'top_providers': top_providers_list,
                'payment_performance': payment_performance
            }
            
        except Exception as e:
            print(f"Error getting provider analysis: {e}")
            return {'top_providers': [], 'payment_performance': []}
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to the DataFrame."""
        if df.empty or not filters:
            return df
        
        try:
            filtered_df = df.copy()
            
            # Date range filter
            if 'start_date' in filters and 'end_date' in filters:
                start_date = pd.to_datetime(filters['start_date'])
                end_date = pd.to_datetime(filters['end_date'])
                
                if 'fecha_factura' in filtered_df.columns:
                    date_mask = (
                        (pd.to_datetime(filtered_df['fecha_factura'], errors='coerce') >= start_date) &
                        (pd.to_datetime(filtered_df['fecha_factura'], errors='coerce') <= end_date)
                    )
                    filtered_df = filtered_df[date_mask]
            
            # Project filter
            if 'project_id' in filters and 'project_id' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['project_id'] == filters['project_id']
                ]
            
            # Provider filter
            if 'provider' in filters and 'proveedor' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['proveedor'].str.contains(
                        filters['provider'], case=False, na=False
                    )
                ]
            
            # Status filter
            if 'status' in filters and 'estado_costo' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['estado_costo'] == filters['status']
                ]
            
            # Type filter
            if 'tipo_costo' in filters and 'tipo_costo' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['tipo_costo'] == filters['tipo_costo']
                ]
            
            return filtered_df
            
        except Exception as e:
            print(f"Error applying filters: {e}")
            return df
    
    def _calculate_cost_trends(self, df: pd.DataFrame, period: str) -> List[Dict[str, Any]]:
        """Calculate cost trends by period."""
        if df.empty or 'fecha_factura' not in df.columns:
            return []
        
        try:
            df_trends = df.copy()
            df_trends['fecha_factura'] = pd.to_datetime(df_trends['fecha_factura'], errors='coerce')
            
            if period == "monthly":
                df_trends['period'] = df_trends['fecha_factura'].dt.strftime('%Y-%m')
            elif period == "quarterly":
                df_trends['period'] = df_trends['fecha_factura'].dt.to_period('Q').astype(str)
            else:  # yearly
                df_trends['period'] = df_trends['fecha_factura'].dt.strftime('%Y')
            
            trends = df_trends.groupby('period').agg({
                'importe_neto': 'sum',
                'cost_id': 'count'
            }).reset_index()
            
            return [
                {
                    'period': row['period'],
                    'total_amount': float(row['importe_neto']),
                    'total_count': int(row['cost_id'])
                }
                for _, row in trends.iterrows()
            ]
            
        except Exception as e:
            print(f"Error calculating cost trends: {e}")
            return []
    
    def _analyze_overdue_costs(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overdue costs."""
        if df.empty:
            return {'overdue_costs': [], 'summary': {}}
        
        try:
            today = pd.Timestamp.now()
            
            # Filter overdue costs
            if 'fecha_vencimiento' in df.columns and 'estado_costo' in df.columns:
                overdue_df = df[
                    (pd.to_datetime(df['fecha_vencimiento'], errors='coerce') < today) &
                    (df['estado_costo'] != 'pagado')
                ].copy()
                
                if not overdue_df.empty:
                    # Calculate days overdue
                    overdue_df['days_overdue'] = (
                        today - pd.to_datetime(overdue_df['fecha_vencimiento'], errors='coerce')
                    ).dt.days
                    
                    overdue_list = [
                        {
                            'provider': row.get('proveedor', ''),
                            'amount': float(row.get('importe_neto', 0)),
                            'due_date': str(row.get('fecha_vencimiento', '')),
                            'days_overdue': int(row.get('days_overdue', 0)),
                            'invoice': row.get('factura', '')
                        }
                        for _, row in overdue_df.iterrows()
                    ]
                    
                    summary = {
                        'total_overdue': len(overdue_df),
                        'total_amount': self.format_utils.format_currency(
                            overdue_df['importe_neto'].sum()
                        ),
                        'avg_days_overdue': round(overdue_df['days_overdue'].mean(), 1),
                        'max_days_overdue': int(overdue_df['days_overdue'].max())
                    }
                else:
                    overdue_list = []
                    summary = {
                        'total_overdue': 0,
                        'total_amount': self.format_utils.format_currency(0),
                        'avg_days_overdue': 0,
                        'max_days_overdue': 0
                    }
            else:
                overdue_list = []
                summary = {
                    'total_overdue': 0,
                    'total_amount': self.format_utils.format_currency(0),
                    'avg_days_overdue': 0,
                    'max_days_overdue': 0
                }
            
            return {
                'overdue_costs': overdue_list,
                'summary': summary
            }
            
        except Exception as e:
            print(f"Error analyzing overdue costs: {e}")
            return {'overdue_costs': [], 'summary': {}}
    
    def _generate_cost_forecast(self, df: pd.DataFrame, months: int) -> List[Dict[str, Any]]:
        """Generate cost forecast."""
        if df.empty or 'fecha_factura' not in df.columns:
            return []
        
        try:
            # Simple forecast based on historical averages
            df_forecast = df.copy()
            df_forecast['fecha_factura'] = pd.to_datetime(df_forecast['fecha_factura'], errors='coerce')
            
            # Calculate monthly averages from last 12 months
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=12)
            recent_df = df_forecast[df_forecast['fecha_factura'] >= cutoff_date]
            
            if recent_df.empty:
                return []
            
            monthly_avg = recent_df.groupby(
                recent_df['fecha_factura'].dt.strftime('%Y-%m')
            )['importe_neto'].sum().mean()
            
            # Generate forecast for next N months
            forecast = []
            current_date = pd.Timestamp.now()
            
            for i in range(months):
                forecast_date = current_date + pd.DateOffset(months=i+1)
                forecast.append({
                    'month': forecast_date.strftime('%Y-%m'),
                    'projected_amount': float(monthly_avg),
                    'confidence': 'medium'  # Could be enhanced with statistical modeling
                })
            
            return forecast
            
        except Exception as e:
            print(f"Error generating cost forecast: {e}")
            return []
    
    def _get_empty_cost_dashboard(self) -> Dict[str, Any]:
        """Get empty cost dashboard structure."""
        return {
            'kpis': self._get_empty_kpis(),
            'charts': {'monthly_costs': [], 'cost_by_type': [], 'payment_status': []},
            'breakdown': {'by_project': [], 'by_category': [], 'by_provider': []},
            'pending_payments': {'total_pending': 0, 'overdue': 0, 'upcoming': []},
            'provider_analysis': {'top_providers': [], 'payment_performance': []},
            'filters_applied': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_empty_kpis(self) -> Dict[str, Any]:
        """Get empty KPIs structure."""
        return {
            'total_costs': 0,
            'total_amount': self.format_utils.format_currency(0),
            'paid_costs': 0,
            'pending_costs': 0,
            'paid_amount': self.format_utils.format_currency(0),
            'pending_amount': self.format_utils.format_currency(0),
            'overdue_count': 0,
            'overdue_amount': self.format_utils.format_currency(0),
            'payment_rate': 0,
            'avg_cost': self.format_utils.format_currency(0),
            'type_breakdown': {}
        }
