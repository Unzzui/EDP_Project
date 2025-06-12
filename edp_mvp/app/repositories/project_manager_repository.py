"""
Repository for Project Manager (Jefe de Proyecto) data operations.
Handles data access for project manager specific functions.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..repositories.cost_repository import CostRepository
from ..repositories.edp_repository import EDPRepository
from ..repositories.project_repository import ProjectRepository
from ..utils.date_utils import DateUtils
import pandas as pd
import logging
import traceback

logger = logging.getLogger(__name__)

class ProjectManagerRepository:
    """Repository for project manager data operations."""

    def __init__(self):
        self.edp_repo = EDPRepository()
        self.project_repo = ProjectRepository()
        self.cost_repo = CostRepository()

    def get_manager_projects(self, manager_name: str) -> List[Dict[str, Any]]:
        """Obtiene todos los proyectos únicos asignados a un jefe de proyecto."""
        try:
            edps_data = self.edp_repo.find_by_filters({'jefe_proyecto': manager_name})
            proyectos = [edp.__dict__ if hasattr(edp, '__dict__') else edp for edp in edps_data]
            return proyectos
        except Exception as e:
            logger.error(f"Error getting manager projects for {manager_name}: {str(e)}")
            return []

    def get_manager_summary(self, manager_name: str) -> Dict[str, Any]:
        """Get summary statistics for a project manager."""
        try:
            proyectos = self.get_manager_projects(manager_name)
            df = pd.DataFrame(proyectos)
            if df.empty:
                return {
                    'total_projects': 0,
                    'total_edps': 0,
                    'total_amount_proposed': 0,
                    'total_amount_approved': 0,
                    'total_amount_paid': 0,
                    'pending_amount': 0,
                    'avg_processing_days': 0,
                    'critical_edps': 0,
                    'completion_rate': 0
                }
            for col in ["monto_propuesto", "monto_aprobado", "dias_espera"]:
                if col not in df.columns:
                    df[col] = 0
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            if "estado" not in df.columns:
                df["estado"] = ""
            df["monto_pagado"] = df.apply(
                lambda row: row["monto_aprobado"] if str(row["estado"]).lower() in ["pagado", "validado"] else 0, axis=1
            )
            total_projects = df['proyecto'].nunique() if 'proyecto' in df.columns else 0
            total_edps = len(df)
            total_proposed = df['monto_propuesto'].sum()
            total_approved = df['monto_aprobado'].sum()
            total_paid = df['monto_pagado'].sum()
            pending_amount = total_approved - total_paid
            avg_days = df['dias_espera'].mean() if 'dias_espera' in df.columns else 0
            completion_rate = (total_paid / total_approved * 100) if total_approved > 0 else 0

            return {
                'total_projects': int(total_projects),
                'total_edps': int(total_edps),
                'total_amount_proposed': float(total_proposed),
                'total_amount_approved': float(total_approved),
                'total_amount_paid': float(total_paid),
                'pending_amount': float(pending_amount),
                'avg_processing_days': round(float(avg_days), 1),
                'critical_edps': int(0),  # Aquí puedes calcularlo con pandas si tienes la lógica
                'completion_rate': round(float(completion_rate), 1)
            }
        except Exception as e:
            logger.error(f"Error getting manager summary for {manager_name}: {str(e)}")
            return {}

    def get_projects_by_status(self, manager_name: str) -> Dict[str, List[Dict]]:
        """Get projects grouped by status for a project manager."""
        try:
            proyectos = self.get_manager_projects(manager_name)
            df = pd.DataFrame(proyectos)
            
            status_groups = {
                'pending': [],      # Proyectos con EDPs pendientes/en revisión
                'in_progress': [],  # Proyectos con EDPs enviados/en proceso
                'completed': [],    # Proyectos con la mayoría de EDPs validados/pagados
                'overdue': []       # Proyectos con EDPs vencidos (>45 días)
            }
            
            if df.empty or 'proyecto' not in df.columns:
                return status_groups
            
            # Ensure required columns exist
            for col in ["monto_propuesto", "monto_aprobado", "estado"]:
                if col not in df.columns:
                    df[col] = 0 if col.startswith('monto') else ""
                    
            # Convert numeric columns
            for col in ["monto_propuesto", "monto_aprobado"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
            # Calculate days since emission for overdue detection
            if 'fecha_emision' in df.columns:
                df['fecha_emision'] = pd.to_datetime(df['fecha_emision'], errors='coerce')
                df['days_since_emission'] = (datetime.now() - df['fecha_emision']).dt.days
            else:
                df['days_since_emission'] = 0
            
            # Group by project and analyze status
            for project_name, project_group in df.groupby('proyecto'):
                total_edps = len(project_group)
                total_proposed = project_group['monto_propuesto'].sum()
                total_approved = project_group['monto_aprobado'].sum()
                
                # Count EDPs by status
                status_counts = project_group['estado'].str.lower().value_counts().to_dict()
                
                # Calculate completion metrics
                completion_rate = (total_approved / total_proposed * 100) if total_proposed > 0 else 0
                
                # Count different status types
                validated_count = status_counts.get('validado', 0) + status_counts.get('pagado', 0)
                sent_count = status_counts.get('enviado', 0)
                pending_count = status_counts.get('revisión', 0) + status_counts.get('revision', 0)
                
                # Check for overdue EDPs (>45 days)
                overdue_edps = len(project_group[project_group['days_since_emission'] > 45])
                
                # Determine project status
                project_info = {
                    'project_name': project_name,
                    'total_edps': total_edps,
                    'total_proposed': float(total_proposed),
                    'total_approved': float(total_approved),
                    'completion_rate': round(completion_rate, 1),
                    'status_distribution': status_counts,
                    'overdue_edps': overdue_edps
                }
                
                # Classify project status
                if overdue_edps > 0:
                    status_groups['overdue'].append(project_info)
                elif completion_rate >= 90:
                    status_groups['completed'].append(project_info)
                elif completion_rate >= 30 or sent_count > 0:
                    status_groups['in_progress'].append(project_info)
                else:
                    status_groups['pending'].append(project_info)
            
            logger.info(f"Project status distribution for {manager_name}: "
                       f"Pending: {len(status_groups['pending'])}, "
                       f"In Progress: {len(status_groups['in_progress'])}, "
                       f"Completed: {len(status_groups['completed'])}, "
                       f"Overdue: {len(status_groups['overdue'])}")
            
            return status_groups
            
        except Exception as e:
            logger.error(f"Error getting projects by status for {manager_name}: {str(e)}")
            logger.error(traceback.format_exc())
            return {'pending': [], 'in_progress': [], 'completed': [], 'overdue': []}

    def get_financial_metrics(self, manager_name: str) -> Dict[str, Any]:
        """Get financial metrics for a project manager."""
        try:
            proyectos = self.get_manager_projects(manager_name)
            df = pd.DataFrame(proyectos)
            if df.empty:
                return {
                    'monthly_target': 0,
                    'current_month_collected': 0,
                    'target_achievement': 0,
                    'payment_velocity': 0,
                    'total_portfolio': 0
                }
            for col in ["monto_aprobado", "monto_pagado"]:
                if col not in df.columns:
                    df[col] = 0
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            if "estado" not in df.columns:
                df["estado"] = ""
            # Calcular monto_pagado si no existe
            if 'monto_pagado' not in df.columns or df['monto_pagado'].sum() == 0:
                df["monto_pagado"] = df.apply(
                    lambda row: row["monto_aprobado"] if str(row["estado"]).lower() in ["pagado", "validado"] else 0, axis=1
                )
            total_approved = df['monto_aprobado'].sum()
            monthly_target = 250_000_000
            current_month = datetime.now().month
            current_year = datetime.now().year
            current_month_collected = 0
            if 'fecha_pago' in df.columns:
                for _, edp in df.iterrows():
                    fecha_pago = edp.get('fecha_envio_conformidad')
                    if pd.notnull(fecha_pago) and hasattr(fecha_pago, 'month'):
                        if fecha_pago.month == current_month and fecha_pago.year == current_year:
                            current_month_collected += edp.get('monto_pagado', 0)
            target_achievement = (current_month_collected / monthly_target * 100) if monthly_target > 0 else 0
            # Payment velocity
            payment_days = []
            if 'fecha_emision' in df.columns and 'fecha_pago' in df.columns:
                for _, edp in df.iterrows():
                    fecha_creacion = edp.get('fecha_emision')
                    fecha_pago = edp.get('fecha_envio_conformidad')
                    if pd.notnull(fecha_creacion) and pd.notnull(fecha_pago):
                        days = (fecha_pago - fecha_creacion).days
                        payment_days.append(days)
            payment_velocity = sum(payment_days) / len(payment_days) if payment_days else 0
            return {
                'monthly_target': float(monthly_target),
                'current_month_collected': float(current_month_collected),
                'target_achievement': round(float(target_achievement), 1),
                'payment_velocity': round(float(payment_velocity), 1),
                'total_portfolio': float(total_approved)
            }
        except Exception as e:
            logger.error(f"Error getting financial metrics for {manager_name}: {str(e)}")
            return {}

    def get_project_details(self, manager_name: str, project_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific project."""
        try:
            proyectos = self.get_manager_projects(manager_name)
            df = pd.DataFrame(proyectos)
            if df.empty:
                return {}
            df_project = df[df['proyecto'] == project_name] if 'proyecto' in df.columns else pd.DataFrame()
            if df_project.empty:
                return {}
            for col in ["monto_propuesto", "monto_aprobado", "monto_pagado"]:
                if col not in df_project.columns:
                    df_project[col] = 0
                df_project[col] = pd.to_numeric(df_project[col], errors="coerce").fillna(0)
            if "estado" not in df_project.columns:
                df_project["estado"] = ""
            if 'monto_pagado' not in df_project.columns or df_project['monto_pagado'].sum() == 0:
                df_project["monto_pagado"] = df_project.apply(
                    lambda row: row["monto_aprobado"] if str(row["estado"]).lower() in ["pagado", "validado"] else 0, axis=1
                )
            total_edps = len(df_project)
            total_proposed = df_project['monto_propuesto'].sum()
            total_approved = df_project['monto_aprobado'].sum()
            total_paid = df_project['monto_pagado'].sum()
            progress = (total_paid / total_approved * 100) if total_approved > 0 else 0
            status_counts = df_project['estado'].value_counts().to_dict()
            return {
                'project_name': project_name,
                'total_edps': int(total_edps),
                'total_proposed': float(total_proposed),
                'total_approved': float(total_approved),
                'total_paid': float(total_paid),
                'pending_amount': float(total_approved - total_paid),
                'progress_percentage': round(progress, 1),
                'status_distribution': status_counts,
                'edps': df_project.to_dict(orient='records')
            }
        except Exception as e:
            logger.error(f"Error getting project details for {project_name}: {str(e)}")
            return {}

    def get_team_performance(self, manager_name: str) -> Dict[str, Any]:
        """Get performance metrics for the project manager's team."""
        try:
            proyectos = self.get_manager_projects(manager_name)
            df = pd.DataFrame(proyectos)
            if df.empty:
                return {}
            if 'encargado' not in df.columns:
                return {}
            team_members = set(df['encargado'].dropna().unique()) - {manager_name}
            team_performance = {}
            for member in team_members:
                member_edps = df[df['encargado'] == member]
                total_handled = len(member_edps)
                total_amount = member_edps['monto_aprobado'].sum() if 'monto_aprobado' in member_edps.columns else 0
                processing_times = []
                if 'fecha_emision' in member_edps.columns and 'fecha_pago' in member_edps.columns:
                    for _, edp in member_edps.iterrows():
                        fecha_creacion = edp.get('fecha_emision')
                        fecha_pago = edp.get('fecha_pago')
                        if pd.notnull(fecha_creacion):
                            if pd.notnull(fecha_pago):
                                days = (fecha_pago - fecha_creacion).days
                            else:
                                days = (datetime.now() - fecha_creacion).days
                            processing_times.append(days)
                avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0
                team_performance[member] = {
                    'total_edps': total_handled,
                    'total_amount': float(total_amount),
                    'avg_processing_days': round(avg_processing, 1),
                    'efficiency_score': max(0, 100 - (avg_processing - 30) * 2)  # Penalty after 30 days
                }
            return team_performance
        except Exception as e:
            logger.error(f"Error getting team performance for {manager_name}: {str(e)}")
            return {}
    def get_projects_cost(self, manager_name: str) -> Dict[str, Any]:
        
        """Get the cost of all projects for a project manager."""
        try:
            proyectos = self.cost_repo.get_cost_by_manager(manager_name)
         
            return proyectos
        except Exception as e:
            logger.error(f"Error getting projects cost for {manager_name}: {str(e)}")
            return 0