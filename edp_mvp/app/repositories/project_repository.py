"""
Project Repository for handling project data operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models import Project
from . import BaseRepository
import logging
import pandas as pd
from . import BaseRepository, SheetsRepository

logger = logging.getLogger(__name__)
class ProjectRepository(BaseRepository):
    """Repository for managing projects."""


    def __init__(self):
        super().__init__()
        self.sheets_repo = SheetsRepository()
        self.sheet_name = "projects"
        self.range_name = "projects!A:I"
    def find_all(self) -> List[Project]:
        """Get all projects."""
        try:
            df = self.sheets_repo.read_sheet_raw(self.range_name)
            models = self._dataframe_to_models(df)
            return models
        except Exception as e:
            logger.info(f"Error fetching all projects: {e}")
            return []
    def get_project_manager(self) -> Optional[Project]:
        try:
            df = self.sheets_repo.read_sheet_raw(self.range_name)
            project_managers = df['jefe_proyecto'].unique()
            return project_managers
        except Exception as e:
            logger.info(f"Error fetching project manager: {e}")
            return None
    def get_manager_projects(self, manager_name: str) -> List[Dict[str, Any]]:
        """Get all projects for a project manager."""
        try:
            df = self.sheets_repo.read_sheet_raw(self.range_name)
            df_projects = df[df["jefe_proyecto"] == manager_name]
            return df_projects
        except Exception as e:
            logger.info(f"Error fetching manager projects: {e}")
            return []
    def find_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by its ID."""
        try:
            projects = self.find_all()
            return next((p for p in projects if p.id == project_id), None)
        except Exception as e:
            logger.info(f"Error fetching project {project_id}: {e}")
            return None

    def find_by_edp_id(self, edp_id: str) -> List[Project]:
        """Get all projects for a specific EDP."""
        try:
            all_projects = self.find_all()
            return [project for project in all_projects if project.edp_id == edp_id]
        except Exception as e:
            logger.info(f"Error fetching projects for EDP {edp_id}: {e}")
            return []

    def find_by_status(self, status: str) -> List[Project]:
        """Get projects by status."""
        try:
            all_projects = self.find_all()
            return [project for project in all_projects if project.status == status]
        except Exception as e:
            logger.info(f"Error fetching projects by status {status}: {e}")
            return []

    def find_active_projects(self) -> List[Project]:
        """Get all active projects (not completed or cancelled)."""
        try:
            all_projects = self.find_all()
            active_statuses = ["planning", "in_progress", "on_hold", "review"]
            return [
                project for project in all_projects if project.status in active_statuses
            ]
        except Exception as e:
            logger.info(f"Error fetching active projects: {e}")
            return []

    def find_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Project]:
        """Get projects within a date range (by start_date)."""
        try:
            all_projects = self.find_all()
            return [
                project
                for project in all_projects
                if project.start_date and start_date <= project.start_date <= end_date
            ]
        except Exception as e:
            logger.info(f"Error fetching projects by date range: {e}")
            return []

    def create(self, project: Project) -> bool:
        """Create a new project."""
        try:
            sheet = self.get_sheet(self.sheet_name)
            if not sheet:
                return False

            row_data = self._project_to_list(project)
            sheet.append_row(row_data)
            return True
        except Exception as e:
            logger.info(f"Error creating project: {e}")
            return False

    def update(self, project: Project) -> bool:
        """Update an existing project."""
        try:
            sheet = self.get_sheet(self.sheet_name)
            if not sheet:
                return False

            records = sheet.get_all_records()
            for i, record in enumerate(
                records, start=2
            ):  # Start at 2 (header is row 1)
                if record.get("id") == project.id:
                    row_data = self._project_to_list(project)
                    for j, value in enumerate(row_data, start=1):
                        sheet.update_cell(i, j, value)
                    return True

            logger.info(f"Project {project.id} not found for update")
            return False
        except Exception as e:
            logger.info(f"Error updating project: {e}")
            return False

    def update_status(self, project_id: str, status: str) -> bool:
        """Update only the status of a project."""
        try:
            project = self.find_by_id(project_id)
            if not project:
                return False

            project.status = status
            if status == "completed":
                project.end_date = datetime.now()

            return self.update(project)
        except Exception as e:
            logger.info(f"Error updating project status: {e}")
            return False

    def update_progress(self, project_id: str, progress: float) -> bool:
        """Update only the progress of a project."""
        try:
            project = self.find_by_id(project_id)
            if not project:
                return False

            project.progress = max(0, min(100, progress))  # Ensure 0-100 range

            # Auto-update status based on progress
            if project.progress == 100 and project.status != "completed":
                project.status = "completed"
                project.end_date = datetime.now()
            elif project.progress > 0 and project.status == "planning":
                project.status = "in_progress"

            return self.update(project)
        except Exception as e:
            logger.info(f"Error updating project progress: {e}")
            return False

    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        try:
            sheet = self.get_sheet(self.sheet_name)
            if not sheet:
                return False

            records = sheet.get_all_records()
            for i, record in enumerate(
                records, start=2
            ):  # Start at 2 (header is row 1)
                if record.get("id") == project_id:
                    sheet.delete_rows(i)
                    return True

            logger.info(f"Project {project_id} not found for deletion")
            return False
        except Exception as e:
            logger.info(f"Error deleting project: {e}")
            return False

    def get_project_statistics(self) -> Dict[str, Any]:
        """Get statistics about projects."""
        try:
            projects = self.find_all()
            if not projects:
                return {}

            total_projects = len(projects)
            status_counts = {}
            avg_progress = 0
            completed_projects = 0

            for project in projects:
                status = project.status
                status_counts[status] = status_counts.get(status, 0) + 1
                avg_progress += project.progress
                if project.status == "completed":
                    completed_projects += 1

            avg_progress = avg_progress / total_projects if total_projects > 0 else 0
            completion_rate = (
                (completed_projects / total_projects * 100) if total_projects > 0 else 0
            )

            return {
                "total_projects": total_projects,
                "status_distribution": status_counts,
                "average_progress": round(avg_progress, 2),
                "completion_rate": round(completion_rate, 2),
                "active_projects": len(self.find_active_projects()),
            }
        except Exception as e:
            logger.info(f"Error getting project statistics: {e}")
            return {}

    def _dict_to_project(self, record: Dict[str, Any]) -> Project:
        """Supabase integration (migrated from Google Sheets)"""
        start_date = None
        end_date = None

        if record.get("start_date"):
            try:
                start_date = datetime.fromisoformat(record["start_date"])
            except ValueError:
                pass

        if record.get("end_date"):
            try:
                end_date = datetime.fromisoformat(record["end_date"])
            except ValueError:
                pass

        return Project(
            id=record.get("id", ""),
            edp_id=record.get("edp_id", ""),
            name=record.get("name", ""),
            description=record.get("description", ""),
            status=record.get("status", "planning"),
            priority=record.get("priority", "medium"),
            start_date=start_date,
            end_date=end_date,
            progress=float(record.get("progress", 0)),
            budget=float(record.get("budget", 0)) if record.get("budget") else None,
            assigned_to=record.get("assigned_to", ""),
            tags=record.get("tags", "").split(",") if record.get("tags") else [],
        )

    def _dataframe_to_models(self, df: pd.DataFrame) -> List[Project]:
        """Convert DataFrame to list of Project models."""
        models = []
        for _, row in df.iterrows():
            try:
                # Parse dates
                fecha_inicio = None
                fecha_fin_prevista = None
                
                if pd.notna(row.get('fecha_inicio')):
                    try:
                        fecha_inicio = pd.to_datetime(row['fecha_inicio']).to_pydatetime()
                    except:
                        pass
                
                if pd.notna(row.get('fecha_fin_prevista')):
                    try:
                        fecha_fin_prevista = pd.to_datetime(row['fecha_fin_prevista']).to_pydatetime()
                    except:
                        pass
                
                # Parse monto_contrato
                monto_contrato = None
                if pd.notna(row.get('monto_contrato')):
                    try:
                        monto_contrato = float(row['monto_contrato'])
                    except:
                        pass
                
                project = Project(
                    id=row.get('project_id', ''),
                    project_id=row.get('project_id', ''),
                    proyecto=row.get('proyecto', ''),
                    cliente=row.get('cliente', ''),
                    gestor=row.get('gestor', ''),
                    jefe_proyecto=row.get('jefe_proyecto', ''),
                    fecha_inicio=fecha_inicio,
                    fecha_fin_prevista=fecha_fin_prevista,
                    monto_contrato=monto_contrato,
                    moneda=row.get('moneda', 'CLP'),
                    estado_proyecto=row.get('estado_proyecto', 'activo')
                )
                models.append(project)
            except Exception as e:
                logger.warning(f"Error converting row to Project model: {e}")
                continue
        
        return models

    def _project_to_list(self, project: Project) -> List[Any]:
        """Supabase integration (migrated from Google Sheets)"""
        return [
            project.project_id,
            project.proyecto,
            project.cliente,
            project.gestor,
            project.jefe_proyecto,
            project.fecha_inicio.isoformat() if project.fecha_inicio else "",
            project.fecha_fin_prevista.isoformat() if project.fecha_fin_prevista else "",
            project.monto_contrato if project.monto_contrato else "",
            project.moneda,
        ]
