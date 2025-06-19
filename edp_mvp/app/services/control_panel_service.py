"""
Kanban Service for managing board operations and data processing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import os
import json

try:  # pragma: no cover - optional redis cache
    import redis
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(redis_url) if redis_url else None
except Exception:
    redis_client = None

from . import BaseService, ServiceResponse, ValidationError
from ..models import EDP
from ..repositories.edp_repository import EDPRepository
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils
from ..utils.validation_utils import ValidationUtils

logger = logging.getLogger(__name__)


class KanbanService(BaseService):
    """Service for handling Kanban board operations."""

    def __init__(self):
        super().__init__()
        self.edp_repo = EDPRepository()

    def get_kanban_data(self, filters: Dict[str, Any] = None) -> ServiceResponse:
        """Get data for Kanban board view."""
        try:
            cache_key = f"kanban:{json.dumps(filters, sort_keys=True)}"
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return ServiceResponse(success=True, data=data)

            # Get EDPs data
            edps_response = self.edp_repo.get_all()
            if not edps_response.success:
                return ServiceResponse(
                    success=False, message="Failed to load EDPs data", data=None
                )

            df = edps_response.data
            original_count = len(df)

            # Apply filters
            df = self._apply_kanban_filters(df, filters or {})

            # Remove old validated EDPs unless explicitly requested
            if not filters.get("mostrar_validados_antiguos", False):
                df = self._filter_old_validated_edps(df)

            # Group EDPs by status
            columns = self._group_edps_by_status(df)

            # Generate statistics
            statistics = self._calculate_kanban_statistics(df, original_count)

            # Get filter options
            filter_options = self._get_filter_options(df)

            result_data = {
                "columns": columns,
                "statistics": statistics,
                "filter_options": filter_options,
                "filters": filters or {},
            }
            if redis_client:
                redis_client.setex(cache_key, 300, json.dumps(result_data))
            return ServiceResponse(success=True, data=result_data)

        except Exception as e:
            return ServiceResponse(
                success=False, message=f"Error loading Kanban data: {str(e)}", data=None
            )

    def get_kanban_board_data(
        self, df_edp_raw: pd.DataFrame, filters: Dict[str, Any]
    ) -> ServiceResponse:
        """Get comprehensive Kanban board data with filters and statistics - fully migrated from original dashboard."""
        try:
            df = df_edp_raw

            # Convert date columns explicitly to avoid format issues
            date_columns = [
                "fecha_emision",
                "fecha_envio_cliente",
                "fecha_conformidad",
                "fecha_estimada_pago",
            ]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Note: dias_espera is already calculated in the repository's _apply_transformations method

            # Capture original size for metrics
            total_registros_original = len(df)

            # Apply filters from request
            df = self._apply_comprehensive_filters(df, filters or {})
            # Filter old validated EDPs (more than 10 days since conformity)
            fecha_limite = datetime.now() - timedelta(days=10)

            # Count how many old validated EDPs there are before filtering
            validados_antiguos = df[
                (df["estado"] == "validado")
                & (pd.notna(df["fecha_conformidad"]))
                & (df["fecha_conformidad"] < fecha_limite)
            ]
            total_validados_antiguos = len(validados_antiguos)

            # Filter only if not requested to show all
            mostrar_validados_antiguos = (
                filters.get("mostrar_validados_antiguos", False) if filters else False
            )
            if not mostrar_validados_antiguos:
                df = df[
                    ~(
                        (df["estado"] == "validado")
                        & (pd.notna(df["fecha_conformidad"]))
                        & (df["fecha_conformidad"] < fecha_limite)
                    )
                ]

            # Metrics for optimization
            total_registros_filtrados = len(df)
            porcentaje_reduccion = (
                (
                    (total_registros_original - total_registros_filtrados)
                    / total_registros_original
                    * 100
                )
                if total_registros_original > 0
                else 0
            )

            # Convert numeric columns for consistent calculations
            for col in ["monto_propuesto", "monto_aprobado"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            # Group by status (SINGLE LOOP OPTIMIZATION)
            estados = ["revisión", "enviado", "validado", "pagado"]
            columnas = {estado: [] for estado in estados}

            # Variables para análisis de carga de datos
            total_items = 0
            items_por_estado = {}

            # Un solo bucle que procesa todas las tarjetas con sus campos adicionales
            for _, row in df.iterrows():
                estado = row["estado"]
                if estado in columnas:
                    # Crear el diccionario base con los campos necesarios
                    item = row.to_dict()
                    total_items += 1
                    items_por_estado[estado] = items_por_estado.get(estado, 0) + 1

                    # Añadir campo para optimización de lazy loading
                    item["lazy_index"] = items_por_estado[estado]

                    # Procesar fechas para formato adecuado
                    try:
                        if not pd.isna(row.get("fecha_estimada_pago")):
                            item["dias_para_pago"] = (
                                row["fecha_estimada_pago"] - datetime.today()
                            ).days
                        else:
                            item["dias_para_pago"] = None
                    except Exception as e:
                        item["dias_para_pago"] = None
                        logger.error(f"Error calculando dias_para_pago: {e}")

                    # Format dates for template display
                    date_fields = [
                        "fecha_estimada_pago",
                        "fecha_envio_cliente",
                        "fecha_conformidad",
                        "fecha_emision",
                    ]
                    for field in date_fields:
                        if field in item and pd.notna(item[field]):
                            if hasattr(item[field], "strftime"):
                                item[field] = item[field].strftime("%d-%m-%Y")

                    # Añadir diferencia entre monto propuesto y aprobado
                    try:
                        if not pd.isna(row.get("monto_propuesto")) and not pd.isna(
                            row.get("monto_aprobado")
                        ):
                            item["diferencia_montos"] = (
                                row["monto_aprobado"] - row["monto_propuesto"]
                            )
                            item["porcentaje_diferencia"] = (
                                (
                                    item["diferencia_montos"]
                                    / row["monto_propuesto"]
                                    * 100
                                )
                                if row["monto_propuesto"] > 0
                                else 0
                            )
                        else:
                            item["diferencia_montos"] = 0
                            item["porcentaje_diferencia"] = 0
                    except Exception as e:
                        item["diferencia_montos"] = 0
                        item["porcentaje_diferencia"] = 0
                        logger.error(f"Error calculando diferencia_montos: {e}")

                    # Clasificación de validados antiguos vs nuevos (para destacar visualmente)
                    if estado == "validado" and not pd.isna(
                        row.get("fecha_conformidad")
                    ):
                        dias_desde_conformidad = (
                            datetime.now() - row["fecha_conformidad"]
                        ).days
                        item["antiguedad_validado"] = (
                            "antiguo" if dias_desde_conformidad > 10 else "reciente"
                        )

                    # Verificar si es crítico para destacarlo visualmente
                    item["es_critico"] = bool(row.get("critico", False))

                    # Agregar una sola vez a la columna correspondiente
                    columnas[estado].append(item)
            # Get filter options from original data for dropdowns
            filter_options = self._get_comprehensive_filter_options(df)

            # Clean NaT values before sending to template
            for estado, edps in columnas.items():
                for i in range(len(edps)):
                    edps[i] = self._clean_nat_values(edps[i])

            # Card distribution analysis for optimization
            distribucion_cards = {
                estado: len(items) for estado, items in columnas.items()
            }

            # Global statistics for decision making
            estadisticas = {
                "total_registros": total_registros_original,
                "registros_filtrados": total_registros_filtrados,
                "porcentaje_reduccion": round(porcentaje_reduccion, 1),
                "distribucion_cards": distribucion_cards,
                "total_validados_antiguos": total_validados_antiguos,
            }

            return ServiceResponse(
                success=True,
                data={
                    "columnas": columnas,
                    "filter_options": filter_options,
                    "estadisticas": estadisticas,
                    "total_validados_antiguos": total_validados_antiguos,
                    "filters": filters or {},
                },
            )

        except Exception as e:
            import traceback

            logger.error(f"Error in get_kanban_board_data: {str(e)}")
            logger.error(traceback.format_exc())
            return ServiceResponse(
                success=False,
                message=f"Error loading Kanban board data: {str(e)}",
                data=None,
            )

    def update_edp_status(
        self, edp_id: str, new_status: str, additional_data: Dict[str, Any] = None
    ) -> ServiceResponse:
        """Update EDP status in Kanban board with minimal write."""
        try:
            if not edp_id or not new_status:
                return ServiceResponse(
                    success=False,
                    message="EDP ID and new status are required",
                    data=None,
                )

            updates = {"estado": new_status}

            if new_status.lower() in ["pagado", "validado"]:
                updates["conformidad_enviada"] = "Sí"

            if additional_data:
                updates.update(additional_data)

            validation_result = ValidationUtils.validate_edp_update(updates)
            if not validation_result["valid"]:
                return ServiceResponse(
                    success=False,
                    message=f"Validation failed: {', '.join(validation_result['errors'])}",
                    data=None,
                )

            success_write = self.edp_repo.update_fields(int(edp_id), updates)
            if not success_write:
                return ServiceResponse(
                    success=False,
                    message="Failed to update EDP",
                    data=None,
                )

            from ..utils.supabase_adapter import _range_cache
            _range_cache.clear()

            return ServiceResponse(
                success=True,
                message=f"EDP {edp_id} updated successfully",
                data={"edp_id": edp_id, "new_status": new_status, "updates": updates},
            )

        except Exception as e:
            return ServiceResponse(
                success=False, message=f"Error updating EDP status: {str(e)}", data=None
            )

    def update_edp_status_detailed(
        self,
        edp_id: str,
        new_status: str,
        usuario: str,
        additional_data: Dict[str, Any] = None,
    ) -> ServiceResponse:
        """Update EDP status with detailed information from modal."""
        try:
            # Use the existing update_edp_status method with additional data
            return self.update_edp_status(edp_id, new_status, additional_data)

        except Exception as e:
            return ServiceResponse(
                success=False,
                message=f"Error updating EDP status with details: {str(e)}",
                data=None,
            )

    def _apply_kanban_filters(
        self, df: pd.DataFrame, filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply filters to DataFrame."""
        filtered_df = df.copy()

        if filters.get("mes"):
            filtered_df = filtered_df[filtered_df["Mes"] == filters["mes"]]

        if filters.get("encargado"):
            filtered_df = filtered_df[
                filtered_df["Jefe de Proyecto"] == filters["encargado"]
            ]

        if filters.get("cliente"):
            filtered_df = filtered_df[filtered_df["Cliente"] == filters["cliente"]]

        if filters.get("estado_detallado"):
            filtered_df = filtered_df[
                filtered_df["Estado Detallado"] == filters["estado_detallado"]
            ]

        return filtered_df

    def _filter_old_validated_edps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out old validated EDPs (>10 days)."""
        cutoff_date = datetime.now() - timedelta(days=10)

        # Create mask for old validated EDPs
        old_validated_mask = (
            (df["Estado"] == "validado")
            & (pd.notna(df["fecha_conformidad"]))
            & (pd.to_datetime(df["fecha_conformidad"], errors="coerce") < cutoff_date)
        )

        # Return DataFrame without old validated EDPs
        return df[~old_validated_mask]

    def _group_edps_by_status(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Group EDPs by status for Kanban columns."""
        status_columns = ["revisión", "enviado", "validado", "pagado"]
        columns = {status: [] for status in status_columns}

        # Convert numeric columns
        for col in ["monto_propuesto", "Monto Aprobado"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        for _, row in df.iterrows():
            status = row.get("Estado", "").lower()
            if status in columns:
                item = self._prepare_kanban_item(row)
                columns[status].append(item)

        return columns

    def _prepare_kanban_item(self, row: pd.Series) -> Dict[str, Any]:
        """Prepare a single EDP item for Kanban display."""
        item = row.to_dict()

        # Calculate days until payment
        try:
            if pd.notna(row.get("Fecha Estimada de Pago")):
                payment_date = pd.to_datetime(row["Fecha Estimada de Pago"])
                item["dias_para_pago"] = (payment_date - datetime.now()).days
            else:
                item["dias_para_pago"] = None
        except Exception:
            item["dias_para_pago"] = None

        # Calculate amount difference
        try:
            proposed = row.get("monto_propuesto", 0) or 0
            approved = row.get("Monto Aprobado", 0) or 0

            if proposed > 0 and approved > 0:
                item["diferencia_montos"] = approved - proposed
                item["porcentaje_diferencia"] = (
                    item["diferencia_montos"] / proposed * 100
                )
            else:
                item["diferencia_montos"] = 0
                item["porcentaje_diferencia"] = 0
        except Exception:
            item["diferencia_montos"] = 0
            item["porcentaje_diferencia"] = 0

        # Check if critical
        item["es_critico"] = bool(row.get("Crítico", False))

        # Check if old validated
        if row.get("Estado") == "validado" and pd.notna(row.get("fecha_conformidad")):
            try:
                conformity_date = pd.to_datetime(row["fecha_conformidad"])
                days_since_conformity = (datetime.now() - conformity_date).days
                item["antiguedad_validado"] = (
                    "antiguo" if days_since_conformity > 10 else "reciente"
                )
            except Exception:
                item["antiguedad_validado"] = "reciente"

        # Clean NaT values
        item = self._clean_nat_values(item)

        return item

    def _clean_nat_values(self, data):
        """
        Limpia valores NaT, NaN o similares convirtiéndolos en None.
        Soporta estructuras anidadas (dicts y listas).
        """
        if isinstance(data, list):
            return [self._clean_nat_values(item) for item in data]

        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if pd.isna(value) or str(value).strip().lower() in ["nat", "nan"]:
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

    def _calculate_kanban_statistics(
        self, df: pd.DataFrame, original_count: int
    ) -> Dict[str, Any]:
        """Calculate statistics for Kanban board."""
        filtered_count = len(df)
        reduction_percentage = 0
        if original_count > 0:
            reduction_percentage = (
                (original_count - filtered_count) / original_count * 100
            )

        # Distribution by status
        distribution = df["Estado"].value_counts().to_dict()

        # Critical EDPs count
        critical_count = len(df[df.get("Crítico", False) == True])

        # Average days waiting
        avg_days_waiting = (
            df["Días Espera"].mean() if "Días Espera" in df.columns else 0
        )

        return {
            "total_registros": original_count,
            "registros_filtrados": filtered_count,
            "porcentaje_reduccion": round(reduction_percentage, 1),
            "distribucion_cards": distribution,
            "edps_criticos": critical_count,
            "promedio_dias_espera": round(avg_days_waiting or 0, 1),
        }

    def _get_filter_options(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Get available options for filters."""
        return {
            "meses": (
                sorted(df["Mes"].dropna().unique().tolist())
                if "Mes" in df.columns
                else []
            ),
            "encargados": (
                sorted(df["Jefe de Proyecto"].dropna().unique().tolist())
                if "Jefe de Proyecto" in df.columns
                else []
            ),
            "clientes": (
                sorted(df["Cliente"].dropna().unique().tolist())
                if "Cliente" in df.columns
                else []
            ),
            "estados_detallados": (
                sorted(df["Estado Detallado"].dropna().unique().tolist())
                if "Estado Detallado" in df.columns
                else []
            ),
        }

    def _calcular_dias_espera(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates waiting days according to business rules - migrated from dashboard controller."""
        now = datetime.now()

        # Create the waiting days column correctly
        df = df.copy()
        df["dias_espera"] = None

        for idx, row in df.iterrows():
            # Check if there's a shipping date
            if pd.notna(row.get("fecha_envio_cliente")):
                fecha_envio = row["fecha_envio_cliente"]

                # If conformity was sent, count days until conformity date
                if row.get("conformidad_enviada") == "Sí" and pd.notna(
                    row.get("fecha_conformidad")
                ):
                    df.at[idx, "dias_espera"] = (
                        row["fecha_conformidad"] - fecha_envio
                    ).days
                # If no conformity, count days until today
                else:
                    df.at[idx, "dias_espera"] = (now - fecha_envio).days

        return df

    def _apply_comprehensive_filters(
        self, df: pd.DataFrame, filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply comprehensive filters matching the original dashboard implementation."""
        df = df.copy()

        mes = filters.get("mes")
        jefe_proyecto = filters.get("jefe_proyecto")
        cliente = filters.get("cliente")
        estado = filters.get("estado")

        if mes and mes != "todos":
            df = df[df["mes"] == mes]
        if jefe_proyecto and jefe_proyecto != "todos":
            df = df[df["jefe_proyecto"] == jefe_proyecto]
        if cliente and cliente != "todos":
            df = df[df["cliente"] == cliente]
        if estado and estado != "todos":
            df = df[df["estado"] == estado]

        return df

    def _get_comprehensive_filter_options(self, df: pd.DataFrame) -> Dict[str, List]:
        """Get comprehensive filter options for dropdowns - migrated from original implementation."""
        return {
            "meses": sorted(df["mes"].dropna().unique()) if "mes" in df.columns else [],
            "jefe_proyectos": (
                sorted(df["jefe_proyecto"].dropna().unique())
                if "jefe_proyecto" in df.columns
                else []
            ),
            "clientes": (
                sorted(df["cliente"].dropna().unique())
                if "cliente" in df.columns
                else []
            ),
            "estados": (
                sorted(df["estado"].dropna().unique()) if "estado" in df.columns else []
            ),
        }

    def _clean_nat_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean NaT values from dictionary - migrated from dashboard controller."""
        cleaned = {}
        for key, value in data.items():
            if pd.isna(value) or (isinstance(value, pd.Timestamp) and pd.isna(value)):
                cleaned[key] = None
            elif isinstance(value, pd.Timestamp):
                cleaned[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, (np.int64, np.float64)):
                cleaned[key] = float(value) if not pd.isna(value) else None
            else:
                cleaned[key] = value
        return cleaned
