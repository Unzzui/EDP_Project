"""
Analytics Service - Servicio para análisis avanzados y reportes
Maneja análisis de retrabajos, issues, tendencias y reportes detallados
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..repositories import BaseRepository
from ..utils.date_utils import DateUtils
from ..utils.format_utils import FormatUtils
from ..utils.validation_utils import ValidationUtils
from . import ServiceResponse
import logging
import traceback

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Servicio para análisis avanzados y reportes detallados"""

    def __init__(self):
        from ..repositories.edp_repository import EDPRepository
        from ..repositories.log_repository import LogRepository

        self.edp_repository = EDPRepository()
        self.log_repository = LogRepository()
        self.date_utils = DateUtils()
        self.format_utils = FormatUtils()
        self.validation_utils = ValidationUtils()

    def _clean_nat_values(self, data):
        """
        Limpia valores NaT (Not a Time) de pandas convirtiéndolos en None
        para que puedan ser serializados a JSON.

        Funciona tanto con diccionarios como con listas de diccionarios.
        """
        if isinstance(data, list):
            # Si recibimos una lista de diccionarios, procesarla iterativamente
            return [self._clean_nat_values(item) for item in data]

        # Caso base: data es un diccionario
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if pd.isna(value) or value == "NaT" or str(value) == "NaT":
                result[key] = None
            elif isinstance(value, dict):
                result[key] = self._clean_nat_values(
                    value
                )  # Recursivamente para sub-diccionarios
            elif isinstance(value, list):
                result[key] = [
                    self._clean_nat_values(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def analizar_issues(self, filtros: Optional[Dict] = None) -> ServiceResponse:
        """
        Análisis de incidencias para mejora de procesos

        Args:
            filtros: Filtros opcionales

        Returns:
            ServiceResponse con análisis de incidencias
        """
        try:
            # Obtener datos de incidencias - for now return empty analysis as issues repository isn't implemented
            # TODO: Implement issues repository when issues data structure is defined
            return ServiceResponse(
                success=True,
                data={
                    "tipos_incidencia": {"counts": {}, "percentages": {}},
                    "tipos_falla": {"counts": {}, "percentages": {}},
                    "por_proyecto": {},
                    "tendencias": {},
                    "tiempo_resolucion": None,
                    "stats": {
                        "total_incidencias": 0,
                        "incidencias_resueltas": 0,
                        "porcentaje_resuelto": 0,
                    },
                },
                message="Análisis de incidencias completado (datos de prueba)",
            )

            # Análisis por tipo de incidencia
            analisis_tipos = self._analizar_tipos_incidencia(df_issues)

            # Análisis por tipo de falla
            analisis_fallas = self._analizar_tipos_falla(df_issues)

            # Análisis por proyecto
            analisis_proyectos = self._analizar_incidencias_por_proyecto(df_issues)

            # Tendencias temporales
            tendencias = self._analizar_tendencias_incidencias(df_issues)

            # Tiempo de resolución
            tiempo_resolucion = self._calcular_tiempo_resolucion(df_issues)

            analisis = {
                "tipos_incidencia": analisis_tipos,
                "tipos_falla": analisis_fallas,
                "por_proyecto": analisis_proyectos,
                "tendencias": tendencias,
                "tiempo_resolucion": tiempo_resolucion,
                "stats": {
                    "total_incidencias": len(df_issues),
                    "incidencias_resueltas": len(
                        df_issues.dropna(subset=["Fecha resolución"])
                    ),
                    "porcentaje_resuelto": (
                        round(
                            len(df_issues.dropna(subset=["Fecha resolución"]))
                            / len(df_issues)
                            * 100,
                            1,
                        )
                        if len(df_issues) > 0
                        else 0
                    ),
                },
            }

            return ServiceResponse(
                success=True,
                data=analisis,
                message="Análisis de incidencias completado exitosamente",
            )

        except Exception as e:
            logger.error(f"Error en análisis de incidencias: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al realizar análisis de incidencias: {str(e)}",
            )

    def obtener_vista_encargado(
        self, nombre: str, filtros: Optional[Dict] = None
    ) -> ServiceResponse:
        """
        Vista detallada de un encargado específico

        Args:
            nombre: Nombre del encargado
            filtros: Filtros adicionales

        Returns:
            ServiceResponse con datos del encargado
        """
        try:
            edps_response = self.edp_repository.find_all_dataframe()

            df_edp = pd.DataFrame(edps_response.get("data", []))

            # Filtrar por encargado
            df_encargado = df_edp[df_edp["jefe_proyecto"] == nombre].copy()
            logger.debug(df_encargado.head())  # Debugging line
            if df_encargado.empty:
                return ServiceResponse(
                    success=False, message=f"No hay EDPs registrados para {nombre}"
                )

            # Limpiar y preparar datos

            # Análisis financiero
            analisis_financiero = self._analizar_financiero_encargado(
                df_encargado, nombre
            )

            # Análisis de rendimiento
            analisis_rendimiento = self._analizar_rendimiento_encargado(
                df_encargado, df_edp
            )

            # Resumen por proyecto
            resumen_proyectos = self._generar_resumen_proyectos(df_encargado)

            # Tendencias
            tendencias = self._analizar_tendencias_encargado(df_encargado)

            # Tendencia semanal de cobranza
            tendencia_semanal = self._generar_tendencia_semanal_cobro(df_encargado)

            # Top EDPs pendientes individuales
            top_edps_pendientes = self._obtener_top_edps_pendientes(df_encargado, 10)

            datos_encargado = {
                "nombre": nombre,
                "resumen_proyectos": resumen_proyectos,
                "analisis_financiero": analisis_financiero,
                "analisis_rendimiento": analisis_rendimiento,
                "tendencias": tendencias,
                "tendencia_semanal": tendencia_semanal,
                "top_edps_pendientes": top_edps_pendientes,
                "registros": df_encargado.to_dict("records"),
            }

            return ServiceResponse(
                success=True,
                data=datos_encargado,
                message=f"Datos del encargado {nombre} obtenidos exitosamente",
            )

        except Exception as e:
            logger.error(f"Error al obtener vista de encargado {nombre}: {str(e)}")
            return ServiceResponse(
                success=False, message=f"Error al obtener datos del encargado: {str(e)}"
            )

    def obtener_vista_global_encargados(
        self, filtros: Optional[Dict] = None
    ) -> ServiceResponse:
        """
        Vista comparativa de todos los encargados

        Args:
            filtros: Filtros para análisis comparativo

        Returns:
            ServiceResponse con comparativa de encargados
        """
        try:
            edps_response = self.edp_repository.find_all_dataframe()
            # Debugging line
            df_edp = pd.DataFrame(edps_response.get("data", []))

            # Aplicar filtros si existen
            filtros = filtros or {}
            df_filtrado = self._aplicar_filtros_analytics(df_edp, filtros)

            # Análisis por encargado
            analisis_encargados = self._analizar_todos_encargados(df_filtrado)

            # Métricas comparativas
            metricas_comparativas = self._calcular_metricas_comparativas(
                analisis_encargados
            )

            # Ranking de rendimiento
            ranking = self._generar_ranking_encargados(analisis_encargados)

            # Opciones para filtros
            opciones_filtro = self._generar_opciones_filtro(df_edp)

            datos_globales = {
                "analisis_encargados": analisis_encargados,
                "metricas_comparativas": metricas_comparativas,
                "ranking": ranking,
                "opciones_filtro": opciones_filtro,
                "filtros_aplicados": filtros,
            }

            return ServiceResponse(
                success=True,
                data=datos_globales,
                message="Vista global de encargados obtenida exitosamente",
            )

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error al obtener vista global de encargados:\n{error_trace}")
            return ServiceResponse(
                success=False,
                message=f"Error técnico al obtener vista global:\n{str(e)}",
            )

    def _calcular_metricas_comparativas(self, analisis_encargados: Dict) -> Dict:
        """Calcula métricas comparativas entre encargados"""
        if not analisis_encargados:
            return {}

        # Extraer valores para comparación
        montos_pagados = [data["monto_pagado"] for data in analisis_encargados.values()]
        dsos = [data["dso"] for data in analisis_encargados.values()]
        eficiencias = [data["eficiencia"] for data in analisis_encargados.values()]

        return {
            "promedio_monto_pagado": np.mean(montos_pagados),
            "mejor_monto_pagado": max(montos_pagados),
            "peor_monto_pagado": min(montos_pagados),
            "promedio_dso": np.mean(dsos),
            "mejor_dso": min(dsos),  # Menor DSO es mejor
            "peor_dso": max(dsos),
            "promedio_eficiencia": np.mean(eficiencias),
            "mejor_eficiencia": max(eficiencias),
            "peor_eficiencia": min(eficiencias),
        }

    def _generar_ranking_encargados(self, analisis_encargados: Dict) -> List[Dict]:
        """Genera ranking de encargados por rendimiento"""
        ranking = []

        for encargado, data in analisis_encargados.items():
            # Cálculo de score compuesto (ejemplo)
            score_monto = data["monto_pagado"] / 1_000_000  # Normalizar a millones
            score_eficiencia = data["eficiencia"]
            score_dso = max(0, 100 - data["dso"])  # Inverso del DSO

            score_total = (
                (score_monto * 0.4) + (score_eficiencia * 0.3) + (score_dso * 0.3)
            )

            ranking.append(
                {
                    "encargado": encargado,
                    "score_total": round(score_total, 2),
                    "monto_pagado": data["monto_pagado"],
                    "eficiencia": data["eficiencia"],
                    "dso": data["dso"],
                }
            )

        # Ordenar por score total descendente
        ranking.sort(key=lambda x: x["score_total"], reverse=True)

        # Agregar posición
        for i, item in enumerate(ranking):
            item["posicion"] = i + 1

        return ranking

    def _analizar_todos_encargados(self, df: pd.DataFrame) -> Dict:
        """Analiza todos los encargados para vista comparativa"""
        encargados = df["jefe_proyecto"].unique()
        analisis = {}

        for encargado in encargados:
            if pd.isna(encargado):
                continue

            df_encargado = df[df["jefe_proyecto"] == encargado]

            # Cálculos básicos
            total_edps = len(df_encargado)
            df_pagados = df_encargado[
                df_encargado["estado"].isin(["pagado", "validado"])
            ]
            monto_pagado = df_pagados["monto_aprobado"].sum()
            monto_pendiente = df_encargado[
                ~df_encargado["estado"].isin(["pagado", "validado"])
            ]["monto_propuesto"].sum()

            # DSO
            dso = self._calcular_dso_dataset(df_encargado)

            # Criticidad
            edps_criticos = len(df_encargado[df_encargado["critico"] == 1])

            analisis[encargado] = {
                "total_edps": total_edps,
                "edps_pagados": len(df_pagados),
                "monto_pagado": monto_pagado,
                "monto_pendiente": monto_pendiente,
                "dso": round(dso, 1),
                "edps_criticos": edps_criticos,
                "porcentaje_criticos": (
                    round((edps_criticos / total_edps * 100), 1)
                    if total_edps > 0
                    else 0
                ),
                "eficiencia": (
                    round((len(df_pagados) / total_edps * 100), 1)
                    if total_edps > 0
                    else 0
                ),
            }

        return analisis

    def _calcular_dso_dataset(self, df: pd.DataFrame) -> float:
        """
        Calcula DSO ponderado por monto aprobado para mayor precisión.
        Un DSO más alto indica más días promedio para cobrar, ponderado por el valor de cada EDP.
        """
        if (
            df.empty
            or "dias_espera" not in df.columns
            or "monto_aprobado" not in df.columns
        ):
            return 0

        # Filter valid records with positive amounts and days
        df_valid = df[
            (df["dias_espera"].notna())
            & (df["monto_aprobado"].notna())
            & (df["monto_aprobado"] > 0)
            & (df["dias_espera"] >= 0)
        ].copy()

        if df_valid.empty:
            return 0

        # Calculate weighted average DSO
        total_amount = df_valid["monto_aprobado"].sum()
        if total_amount > 0:
            weighted_dso = (
                df_valid["dias_espera"] * df_valid["monto_aprobado"]
            ).sum() / total_amount
            return weighted_dso

        return df_valid["dias_espera"].mean()

    def get_basic_stats(self) -> ServiceResponse:
        """
        Obtiene estadísticas básicas para la landing page

        Returns:
            ServiceResponse con estadísticas básicas del sistema
        """
        try:
            # Obtener datos de EDPs
            edps_response = self.edp_repository.get_all()

            if not edps_response.success:
                return ServiceResponse(
                    success=False,
                    message="Error al obtener datos de EDPs",
                    data={
                        "total_edps": 0,
                        "monto_total": 0,
                        "edps_pendientes": 0,
                        "edps_criticos": 0,
                        "tasa_aprobacion": 0,
                    },
                )

            df = edps_response.data

            if df.empty:
                return ServiceResponse(
                    success=True,
                    data={
                        "total_edps": 0,
                        "monto_total": 0,
                        "edps_pendientes": 0,
                        "edps_criticos": 0,
                        "tasa_aprobacion": 0,
                    },
                )

            # Calcular estadísticas básicas
            total_edps = len(df)

            # Monto total (monto aprobado si existe, sino monto propuesto)
            monto_total = 0
            if "monto_aprobado" in df.columns:
                monto_total = df["monto_aprobado"].fillna(0).sum()
            elif "monto_propuesto" in df.columns:
                monto_total = df["monto_propuesto"].fillna(0).sum()

            # EDPs pendientes (no pagados ni validados)
            edps_pendientes = 0
            if "estado" in df.columns:
                estados_pendientes = df["estado"].isin(["revisión", "enviado"])
                edps_pendientes = estados_pendientes.sum()

            # EDPs críticos
            edps_criticos = 0
            if "critico" in df.columns:
                edps_criticos = df["critico"].fillna(False).sum()
            elif "dias_espera" in df.columns:
                # Si no hay columna critico, considerar críticos los que tienen >30 días
                edps_criticos = (df["dias_espera"].fillna(0) > 30).sum()

            # Tasa de aprobación
            tasa_aprobacion = 0
            if "estado" in df.columns:
                total_procesados = len(
                    df[df["estado"].isin(["pagado", "validado", "enviado"])]
                )
                pagados_validados = len(df[df["estado"].isin(["pagado", "validado"])])
                if total_procesados > 0:
                    tasa_aprobacion = round(
                        (pagados_validados / total_procesados) * 100, 1
                    )

            return ServiceResponse(
                success=True,
                data={
                    "total_edps": int(total_edps),
                    "monto_total": float(monto_total),
                    "edps_pendientes": int(edps_pendientes),
                    "edps_criticos": int(edps_criticos),
                    "tasa_aprobacion": float(tasa_aprobacion),
                },
            )

        except Exception as e:
            logger.error(f"Error al obtener estadísticas básicas: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al calcular estadísticas: {str(e)}",
                data={
                    "total_edps": 0,
                    "monto_total": 0,
                    "edps_pendientes": 0,
                    "edps_criticos": 0,
                    "tasa_aprobacion": 0,
                },
            )

    # Métodos privados de apoyo

    def _aplicar_filtros_analytics(
        self, df: pd.DataFrame, filtros: Dict
    ) -> pd.DataFrame:
        """Aplica filtros comunes a los DataFrames"""
        df_filtrado = df.copy()

        if filtros.get("mes"):
            df_filtrado = df_filtrado[df_filtrado["mes"] == filtros["mes"]]

        if filtros.get("encargado"):
            df_filtrado = df_filtrado[
                df_filtrado["jefe_proyecto"] == filtros["encargado"]
            ]

        if filtros.get("cliente"):
            df_filtrado = df_filtrado[df_filtrado["cliente"] == filtros["cliente"]]

        if filtros.get("estado"):
            df_filtrado = df_filtrado[df_filtrado["estado"] == filtros["estado"]]

        return df_filtrado

    def _extraer_retrabajos_del_log(
        self, df_log: pd.DataFrame, filtros: Dict
    ) -> pd.DataFrame:
        """Extrae registros de retrabajos del log histórico"""
        # Filtrar cambios a "re-trabajo solicitado"
        df_retrabajos = df_log[
            (df_log["Campo"] == "Estado Detallado")
            & (df_log["Después"] == "re-trabajo solicitado")
        ].copy()

        # Convertir fechas
        df_retrabajos["fecha_hora"] = pd.to_datetime(df_retrabajos["fecha_hora"])

        # Aplicar filtros temporales
        if filtros.get("fecha_inicio"):
            fecha_inicio = pd.to_datetime(filtros["fecha_inicio"])
            df_retrabajos = df_retrabajos[df_retrabajos["fecha_hora"] >= fecha_inicio]

        if filtros.get("fecha_fin"):
            fecha_fin = pd.to_datetime(filtros["fecha_fin"])
            df_retrabajos = df_retrabajos[df_retrabajos["fecha_hora"] <= fecha_fin]

        return df_retrabajos

    def _enriquecer_log_con_edp(
        self, df_log: pd.DataFrame, df_edp: pd.DataFrame
    ) -> pd.DataFrame:
        """Enriquece datos del log con información de EDP"""
        # Limpiar columnas duplicadas si existen
        if "proyecto" in df_log.columns:
            df_log = df_log.drop(columns=["proyecto"])

        # Hacer merge con datos de EDP
        df_enriquecido = pd.merge(
            df_log,
            df_edp[
                [
                    "n_edp",
                    "proyceto",
                    "jefe_proyecto",
                    "cliente",
                    "mes",
                    "tipo_falla",
                    "motivo_no_aprobado",
                    "monto_aprobado",
                ]
            ],
            on="n_edp",
            how="left",
        )

        return df_enriquecido

    def _analizar_tipos_incidencia(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza tipos de incidencia"""
        if "Tipo" in df_issues.columns:
            tipos = df_issues["Tipo"].value_counts().to_dict()
            total = sum(tipos.values())
            porcentajes = {k: round(v / total * 100, 1) for k, v in tipos.items()}
            return {"counts": tipos, "percentages": porcentajes}
        return {"counts": {}, "percentages": {}}

    def _analizar_tipos_falla(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza tipos de falla"""
        if "Tipo_falla" in df_issues.columns:
            fallas = df_issues["Tipo_falla"].value_counts().to_dict()
            total = sum(fallas.values())
            porcentajes = {k: round(v / total * 100, 1) for k, v in fallas.items()}
            return {"counts": fallas, "percentages": porcentajes}
        return {"counts": {}, "percentages": {}}

    def _analizar_incidencias_por_proyecto(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza incidencias por proyecto"""
        if "Proyecto Relacionado" in df_issues.columns:
            return df_issues["Proyecto Relacionado"].value_counts().to_dict()
        return {}

    def _analizar_tendencias_incidencias(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza tendencias temporales de incidencias"""
        if "Timestamp" in df_issues.columns:
            df_issues["Semana"] = df_issues["Timestamp"].dt.isocalendar().week
            return df_issues.groupby("Semana").size().to_dict()
        return {}

    def _calcular_tiempo_resolucion(self, df_issues: pd.DataFrame) -> Optional[float]:
        """Calcula tiempo promedio de resolución"""
        if "Timestamp" in df_issues.columns and "Fecha resolución" in df_issues.columns:
            resueltas = df_issues.dropna(subset=["Fecha resolución"])
            if not resueltas.empty:
                timestamp_col = pd.to_datetime(resueltas["Timestamp"])
                resolucion_col = pd.to_datetime(resueltas["Fecha resolución"])

                # Normalizar zonas horarias
                if hasattr(timestamp_col.dt, "tz"):
                    timestamp_col = timestamp_col.dt.tz_localize(None)
                if hasattr(resolucion_col.dt, "tz"):
                    resolucion_col = resolucion_col.dt.tz_localize(None)

                # Calcular diferencia en días
                diferencia = resolucion_col - timestamp_col
                tiempo_resolucion = diferencia.dt.total_seconds() / (60 * 60 * 24)
                return tiempo_resolucion.mean()
        return None

    def _analizar_financiero_encargado(
        self, df_encargado: pd.DataFrame, nombre: str
    ) -> Dict:
        """Análisis financiero del encargado"""
        # Metas por encargado (esto debería venir de configuración)
        METAS_ENCARGADOS = {
            "Diego Bravo": 375_000_000,
            "Carolina López": 375_000_000,
            "Pedro Rojas": 375_000_000,
            "Ana Pérez": 375_000_000,
            "Carlos Alvarez": 375_000_000,
        }

        meta_encargado = METAS_ENCARGADOS.get(nombre, 375_000_000)

        # EDPs pagados
        df_pagados = df_encargado[df_encargado["estado"].isin(["pagado", "validado"])]

        monto_pagado = df_pagados["monto_aprobado"].sum()
        monto_pendiente = df_encargado[
            ~df_encargado["estado"].isin(["pagado", "validado"])
        ]["monto_propuesto"].sum()

        avance_meta = (monto_pagado / meta_encargado * 100) if meta_encargado > 0 else 0

        # Calculate approval effectiveness
        total_edps = len(df_encargado)
        edps_aprobados = len(df_pagados)
        tasa_aprobacion = (edps_aprobados / total_edps * 100) if total_edps > 0 else 0

        # Calculate upcoming collections (próximos a cobrar) - EDPs close to payment
        df_proximos = df_encargado[
            (df_encargado["estado"].isin(["enviado", "revisión", "pendiente"]))
            & (df_encargado["dias_espera"] <= 15)
            & (df_encargado["dias_espera"] >= 0)
        ]
        monto_proximo_cobro = df_proximos["monto_aprobado"].sum()
        cantidad_edp_proximos = len(df_proximos)

        # Calculate critical pending amounts (pendientes críticos > 30 días)
        df_criticos = df_encargado[
            (df_encargado["estado"].isin(["enviado", "revisión", "pendiente"]))
            & (df_encargado["dias_espera"] > 30)
        ]
        monto_pendiente_critico = df_criticos["monto_aprobado"].sum()
        cantidad_edp_criticos = len(df_criticos)

        # Calculate distribution by aging buckets
        df_pendientes = df_encargado[
            ~df_encargado["estado"].isin(["pagado", "validado"])
        ]

        distribucion_aging = {
            "reciente": len(df_pendientes[df_pendientes["dias_espera"] <= 15]),
            "medio": len(
                df_pendientes[
                    (df_pendientes["dias_espera"] > 15)
                    & (df_pendientes["dias_espera"] <= 30)
                ]
            ),
            "critico": len(df_pendientes[df_pendientes["dias_espera"] > 30]),
        }

        # Calculate amounts by aging buckets
        montos_aging = {
            "reciente": df_pendientes[df_pendientes["dias_espera"] <= 15][
                "monto_aprobado"
            ].sum(),
            "medio": df_pendientes[
                (df_pendientes["dias_espera"] > 15)
                & (df_pendientes["dias_espera"] <= 30)
            ]["monto_aprobado"].sum(),
            "critico": df_pendientes[df_pendientes["dias_espera"] > 30][
                "monto_aprobado"
            ].sum(),
        }

        # Calculate efficiency metrics
        tiempo_promedio_resolucion = (
            df_pagados["dias_espera"].mean() if len(df_pagados) > 0 else 0
        )

        # Calculate risk score (0-100, lower is better)
        riesgo_score = 0
        if total_edps > 0:
            riesgo_score = (
                (cantidad_edp_criticos / total_edps * 40)  # Critical EDPs weight: 40%
                + (
                    max(0, (tiempo_promedio_resolucion - 30)) / 60 * 30
                )  # Time over 30 days weight: 30%
                + (
                    max(0, (100 - tasa_aprobacion)) / 100 * 30
                )  # Low approval rate weight: 30%
            )

        return {
            "meta_encargado": meta_encargado,
            "monto_pagado": monto_pagado,
            "monto_pendiente": monto_pendiente,
            "avance_meta": round(avance_meta, 1),
            "total_edps": total_edps,
            "edps_pagados": edps_aprobados,
            "tasa_aprobacion": round(tasa_aprobacion, 1),
            "monto_proximo_cobro": float(monto_proximo_cobro),
            "cantidad_edp_proximos": cantidad_edp_proximos,
            "monto_pendiente_critico": float(monto_pendiente_critico),
            "cantidad_edp_criticos": cantidad_edp_criticos,
            "distribucion_aging": distribucion_aging,
            "montos_aging": montos_aging,
            "tiempo_promedio_resolucion": round(tiempo_promedio_resolucion, 1),
            "riesgo_score": round(riesgo_score, 1),
        }

    def _analizar_rendimiento_encargado(
        self, df_encargado: pd.DataFrame, df_global: pd.DataFrame
    ) -> Dict:
        """Análisis de rendimiento comparativo del encargado"""
        # DSO del encargado vs global - using weighted average by amount
        dso_encargado = self._calcular_dso_dataset(df_encargado)
        dso_global = self._calcular_dso_dataset(df_global)

        # Global approval rate for comparison
        if len(df_global) > 0:
            df_global_pagados = df_global[
                df_global["estado"].isin(["pagado", "validado"])
            ]
            tasa_aprobacion_global = len(df_global_pagados) / len(df_global) * 100
        else:
            tasa_aprobacion_global = 0

        # Análisis de criticidad
        edps_criticos = df_encargado[df_encargado["critico"] == 1]
        porcentaje_criticos = (
            (len(edps_criticos) / len(df_encargado) * 100)
            if len(df_encargado) > 0
            else 0
        )

        # Calculate average approval time (días promedio de aprobación)
        df_con_fechas = df_encargado[
            (df_encargado["estado"].isin(["pagado", "validado"]))
            & (df_encargado["dias_espera"].notna())
            & (df_encargado["dias_espera"] > 0)
        ]
        dias_promedio_aprobacion = (
            df_con_fechas["dias_espera"].mean() if len(df_con_fechas) > 0 else 0
        )

        # Calculate velocity metrics (EDPs processed per month)
        if "mes" in df_encargado.columns:
            edps_por_mes = df_encargado.groupby("mes").size()
            velocidad_procesamiento = (
                edps_por_mes.mean() if len(edps_por_mes) > 0 else 0
            )

            # Calculate monthly payment velocity
            pagos_por_mes = (
                df_encargado[df_encargado["estado"].isin(["pagado", "validado"])]
                .groupby("mes")["monto_aprobado"]
                .sum()
            )
            velocidad_cobro = pagos_por_mes.mean() if len(pagos_por_mes) > 0 else 0
        else:
            velocidad_procesamiento = 0
            velocidad_cobro = 0

        # Calculate improvement trends (last 2 months comparison)
        meses_unicos = (
            sorted(df_encargado["mes"].unique())
            if "mes" in df_encargado.columns
            else []
        )
        tendencia_mejora = "estable"

        if len(meses_unicos) >= 2:
            ultimo_mes = meses_unicos[-1]
            penultimo_mes = meses_unicos[-2]

            dso_ultimo = self._calcular_dso_dataset(
                df_encargado[df_encargado["mes"] == ultimo_mes]
            )
            dso_penultimo = self._calcular_dso_dataset(
                df_encargado[df_encargado["mes"] == penultimo_mes]
            )

            if dso_ultimo < dso_penultimo * 0.9:  # 10% improvement
                tendencia_mejora = "mejorando"
            elif dso_ultimo > dso_penultimo * 1.1:  # 10% deterioration
                tendencia_mejora = "empeorando"

        return {
            "dso_encargado": round(dso_encargado, 1),
            "dso_global": round(dso_global, 1),
            "diferencia_dso": round(dso_encargado - dso_global, 1),
            "edps_criticos": len(edps_criticos),
            "porcentaje_criticos": round(porcentaje_criticos, 1),
            "tasa_aprobacion_global": round(tasa_aprobacion_global, 1),
            "dias_promedio_aprobacion": round(dias_promedio_aprobacion, 1),
            "velocidad_procesamiento": round(velocidad_procesamiento, 1),
            "velocidad_cobro": round(velocidad_cobro, 0),
            "tendencia_mejora": tendencia_mejora,
        }

    def _generar_resumen_proyectos(self, df_encargado: pd.DataFrame) -> Dict:
        """Genera resumen por proyecto para el encargado"""
        resumen = (
            df_encargado.groupby("proyecto")
            .agg(
                {
                    "n_edp": "count",
                    "critico": "sum",
                    "validado": "sum",
                    "monto_propuesto": "sum",
                    "monto_aprobado": "sum",
                }
            )
            .rename(
                columns={
                    "n_edp": "Total_EDP",
                    "critico": "Críticos",
                    "validado": "Validados",
                    "monto_propuesto": "Monto_Propuesto_Total",
                    "monto_aprobado": "Monto_Aprobado_Total",
                }
            )
        )

        # Calcular montos pagados por proyecto
        df_pagados = df_encargado[df_encargado["estado"].isin(["pagado", "validado"])]
        monto_pagado_por_proyecto = df_pagados.groupby("proyecto")[
            "monto_aprobado"
        ].sum()

        resumen = resumen.merge(
            monto_pagado_por_proyecto.rename("Monto_Pagado"),
            left_index=True,
            right_index=True,
            how="left",
        )
        resumen["Monto_Pagado"] = resumen["Monto_Pagado"].fillna(0)

        # Calcular monto pendiente
        resumen["Monto_Pendiente"] = (
            resumen["Monto_Aprobado_Total"] - resumen["Monto_Pagado"]
        )

        return resumen.to_dict("index")

    def _analizar_tendencias_encargado(self, df_encargado: pd.DataFrame) -> Dict:
        """Analiza tendencias del encargado con métricas adicionales"""
        # Análisis por mes (últimos 3 meses)
        meses_unicos = sorted(df_encargado["mes"].unique())[-3:]

        tendencia_cobro = []
        for mes in meses_unicos:
            df_mes = df_encargado[
                (df_encargado["mes"] == mes)
                & (df_encargado["estado"].isin(["pagado", "validado"]))
            ]
            monto_mes = df_mes["monto_aprobado"].sum()
            tendencia_cobro.append((mes, float(monto_mes)))

        # Calculate monthly variation and averages
        monto_cobrado_ultimo_mes = tendencia_cobro[-1][1] if tendencia_cobro else 0
        monto_cobrado_penultimo_mes = (
            tendencia_cobro[-2][1] if len(tendencia_cobro) > 1 else 1
        )

        variacion_mensual_cobro = 0
        if monto_cobrado_penultimo_mes > 0:
            variacion_mensual_cobro = (
                (monto_cobrado_ultimo_mes - monto_cobrado_penultimo_mes)
                / monto_cobrado_penultimo_mes
                * 100
            )

        promedio_cobro_mensual = (
            sum(monto for _, monto in tendencia_cobro) / len(tendencia_cobro)
            if tendencia_cobro
            else 0
        )
        maximo_cobro_mensual = (
            max(monto for _, monto in tendencia_cobro) if tendencia_cobro else 1
        )

        # Calculate current month projection
        from datetime import datetime

        meta_mes_actual = (
            375_000_000  # Monthly target (assuming annual target divided by 12)
        )

        # Calculate projections based on current trends
        if tendencia_cobro:
            # Linear projection based on last 3 months
            if len(tendencia_cobro) >= 2:
                crecimiento_promedio = sum(
                    (tendencia_cobro[i][1] - tendencia_cobro[i - 1][1])
                    for i in range(1, len(tendencia_cobro))
                ) / (len(tendencia_cobro) - 1)

                proyeccion_siguiente_mes = (
                    monto_cobrado_ultimo_mes + crecimiento_promedio
                )
            else:
                proyeccion_siguiente_mes = monto_cobrado_ultimo_mes
        else:
            proyeccion_siguiente_mes = 0

        # Calculate risk alerts
        alertas = []

        if monto_cobrado_ultimo_mes < meta_mes_actual * 0.7:
            alertas.append(
                {
                    "tipo": "warning",
                    "mensaje": "Cobro mensual por debajo del 70% de la meta",
                    "valor": f"${monto_cobrado_ultimo_mes:,.0f} vs ${meta_mes_actual:,.0f}",
                }
            )

        if variacion_mensual_cobro < -20:
            alertas.append(
                {
                    "tipo": "danger",
                    "mensaje": "Caída significativa en cobros mensuales",
                    "valor": f"{variacion_mensual_cobro:.1f}%",
                }
            )

        if len(meses_unicos) >= 3:
            # Check for consistent decline
            ultimos_3_meses = (
                [tendencia_cobro[i][1] for i in range(-3, 0)]
                if len(tendencia_cobro) >= 3
                else []
            )
            if (
                len(ultimos_3_meses) == 3
                and ultimos_3_meses[0] > ultimos_3_meses[1] > ultimos_3_meses[2]
            ):
                alertas.append(
                    {
                        "tipo": "danger",
                        "mensaje": "Tendencia declinante por 3 meses consecutivos",
                        "valor": "Revisar estrategia",
                    }
                )

        # Calculate efficiency score (0-100, higher is better)
        efficiency_score = 0
        if promedio_cobro_mensual > 0 and meta_mes_actual > 0:
            cumplimiento_meta = min(
                100, (promedio_cobro_mensual / meta_mes_actual) * 100
            )
            consistency_score = 100 - abs(
                variacion_mensual_cobro
            )  # Lower variation is better
            efficiency_score = (cumplimiento_meta * 0.7) + (consistency_score * 0.3)

        return {
            "tendencia_cobro": tendencia_cobro,
            "meses_analizados": meses_unicos,
            "monto_cobrado_ultimo_mes": float(monto_cobrado_ultimo_mes),
            "variacion_mensual_cobro": round(variacion_mensual_cobro, 1),
            "promedio_cobro_mensual": float(promedio_cobro_mensual),
            "maximo_cobro_mensual": float(maximo_cobro_mensual),
            "meta_mes_actual": float(meta_mes_actual),
            "proyeccion_siguiente_mes": float(proyeccion_siguiente_mes),
            "alertas": alertas,
            "efficiency_score": round(efficiency_score, 1),
        }

    def _generar_tendencia_semanal_cobro(
        self, df_encargado: pd.DataFrame
    ) -> List[Dict]:
        """Genera datos de tendencia semanal de cobranza para los últimos 12 semanas"""
        from datetime import datetime, timedelta
        import pandas as pd

        # Filtrar solo EDPs pagados o validados
        df_pagados = df_encargado[
            df_encargado["estado"].isin(["pagado", "validado"])
        ].copy()

        if df_pagados.empty:
            # Si no hay datos, devolver lista vacía (no generar datos simulados)
            return []

        # Si tenemos datos reales, procesarlos
        # Agregar columna de semana si no existe
        if "fecha_pago" not in df_pagados.columns:
            # Simular fechas de pago basadas en el mes
            df_pagados["fecha_pago"] = pd.to_datetime(
                df_pagados["mes"].astype(str) + "-01"
            )
        else:
            df_pagados["fecha_pago"] = pd.to_datetime(df_pagados["fecha_pago"])

        # Agrupar por semana
        df_pagados["semana"] = df_pagados["fecha_pago"].dt.strftime("Sem %W")
        df_pagados["año_semana"] = df_pagados["fecha_pago"].dt.strftime("%Y-Sem%W")

        # Calcular montos por semana
        cobros_semanales = (
            df_pagados.groupby(["año_semana", "semana"])["monto_aprobado"]
            .sum()
            .reset_index()
        )

        # Obtener las últimas 12 semanas
        cobros_semanales = cobros_semanales.sort_values("año_semana").tail(12)

        # Formatear resultados
        resultado = []
        for _, row in cobros_semanales.iterrows():
            resultado.append(
                {
                    "semana": row["semana"],
                    "fecha": row["año_semana"],
                    "monto": float(row["monto_aprobado"]),
                    "es_simulado": False,
                }
            )

        # Si tenemos menos de 12 semanas, completar con datos simulados
        if len(resultado) < 12:
            fecha_actual = datetime.now()
            semanas_faltantes = 12 - len(resultado)

            for i in range(semanas_faltantes, 0, -1):
                fecha_semana = fecha_actual - timedelta(weeks=i + len(resultado))
                semana_str = f"Sem {fecha_semana.strftime('%W')}"

                # Usar promedio de datos reales para simular
                promedio_real = (
                    sum(item["monto"] for item in resultado) / len(resultado)
                    if resultado
                    else 20_000_000
                )
                monto_simulado = promedio_real * (0.8 + (i * 0.05))  # Variación gradual

                resultado.insert(
                    0,
                    {
                        "semana": semana_str,
                        "fecha": fecha_semana.strftime("%Y-%m-%d"),
                        "monto": float(monto_simulado),
                        "es_simulado": True,
                    },
                )

        return resultado[-12:]  # Asegurar que solo devolvemos las últimas 12 semanas

    def _generar_opciones_filtro(self, df: pd.DataFrame) -> Dict:
        """Genera opciones para filtros dinámicos"""
        return {
            "meses": sorted(df["mes"].dropna().unique()),
            "encargados": sorted(df["jefe_proyecto"].dropna().unique()),
            "clientes": sorted(df["cliente"].dropna().unique()),
            "estados": sorted(df["estado"].dropna().unique()),
            "proyectos": sorted(df["proyecto"].dropna().unique()),
        }

    def _obtener_top_edps_pendientes(
        self, df_encargado: pd.DataFrame, top_n: int = 10
    ) -> List[Dict]:
        """Obtiene los top N EDPs individuales con mayor monto pendiente"""
        # Filtrar solo EDPs que no están pagados ni validados
        df_pendientes = df_encargado[
            ~df_encargado["estado"].isin(["pagado", "validado"])
        ].copy()

        # Calcular monto pendiente por EDP (usar monto_aprobado si no hay monto_pagado)
        df_pendientes["monto_pendiente"] = df_pendientes.get("monto_aprobado", 0)

        # Seleccionar columnas relevantes y ordenar por monto pendiente
        columnas_necesarias = [
            "n_edp",
            "proyecto",
            "cliente",
            "estado",
            "critico",
            "monto_pendiente",
        ]

        # Verificar que las columnas existan
        for col in columnas_necesarias:
            if col not in df_pendientes.columns:
                if col == "monto_pendiente":
                    df_pendientes[col] = df_pendientes.get("monto_aprobado", 0)
                elif col == "cliente":
                    df_pendientes[col] = "Cliente No Especificado"
                elif col == "critico":
                    df_pendientes[col] = 0
                else:
                    df_pendientes[col] = f"No especificado ({col})"

        # Ordenar por monto pendiente descendente y tomar top N
        edps_pendientes = df_pendientes.nlargest(top_n, "monto_pendiente")

        # Convertir a lista de diccionarios con formato requerido
        resultado = []
        for _, row in edps_pendientes.iterrows():
            resultado.append(
                {
                    "n_edp": str(row["n_edp"]),
                    "proyecto": str(row["proyecto"]),
                    "cliente": str(row.get("cliente", "Cliente No Especificado")),
                    "estado": str(row["estado"]),
                    "es_critico": bool(row.get("critico", 0)),
                    "monto_pendiente": float(row["monto_pendiente"]),
                    "dias_espera": int(row.get("dias_espera", 30)),
                }
            )

        return resultado

    def get_rework_analysis(self, filters: Dict) -> Dict:
        """Obtiene el análisis de re-trabajos"""
        try:
            # Obtener datos de EDP y LOG
            filtros = filters
            df_edp = self.edp_repository.find_all_dataframe()
            df_log = self.log_repository.find_all_dataframe()

            df_edp = df_edp.get("data", pd.DataFrame())
            df_log = df_log.get("data", pd.DataFrame())

            df_log_retrabajos = df_log[
                (df_log["campo"] == "estado_detallado")
                & (df_log["despues"] == "re-trabajo solicitado")
            ]

            # Convertir fechas para filtrado temporal
            df_log_retrabajos = df_log_retrabajos.copy()

            df_log_retrabajos.loc[:, "fecha_hora"] = pd.to_datetime(
                df_log_retrabajos["fecha_hora"]
            )
            # Aplicar filtros temporales si existen
            if filtros["fecha_inicio"]:
                fecha_inicio = pd.to_datetime(filtros["fecha_inicio"])
                df_log_retrabajos = df_log_retrabajos[
                    df_log_retrabajos["fecha_hora"] >= fecha_inicio
                ]

            if filtros["fecha_fin"]:
                fecha_fin = pd.to_datetime(filtros["fecha_fin"])
                df_log_retrabajos = df_log_retrabajos[
                    df_log_retrabajos["fecha_hora"] <= fecha_fin
                ]

            if "proyecto" in df_log_retrabajos.columns:
                df_log_retrabajos = df_log_retrabajos.drop(columns=["proyecto"], axis=1)
            # Enriquecer log con información de EDP para poder filtrar por encargado y cliente
            df_log_enriquecido = pd.merge(
                df_log_retrabajos,
                df_edp[
                    [
                        "n_edp",
                        "proyecto",
                        "jefe_proyecto",
                        "cliente",
                        "mes",
                        "tipo_falla",
                        "motivo_no_aprobado",
                        "monto_aprobado",
                    ]
                ],
                on="n_edp",
                how="left",
            )

            # Aplicar filtros de EDP también al log
            if filtros["jefe_proyecto"]:
                df_log_enriquecido = df_log_enriquecido[
                    df_log_enriquecido["jefe_proyecto"] == filtros["jefe_proyecto"]
                ]

            if filtros["cliente"]:
                df_log_enriquecido = df_log_enriquecido[
                    df_log_enriquecido["cliente"] == filtros["cliente"]
                ]

            if filtros["mes"]:
                df_log_enriquecido = df_log_enriquecido[
                    df_log_enriquecido["mes"] == filtros["mes"]
                ]

            if filtros["tipo_falla"]:
                df_log_enriquecido = df_log_enriquecido[
                    df_log_enriquecido["tipo_falla"] == filtros["tipo_falla"]
                ]

            # Estadísticas basadas en el log
            total_retrabajos_log = len(df_log_enriquecido)
            edps_unicos_con_retrabajo = df_log_enriquecido["n_edp"].nunique()

            # Buscar motivos y tipos asociados a cada ocurrencia de re-trabajo
            retrabajos_completos = []

            for _, row in df_log_enriquecido.iterrows():
                edp_id = row["n_edp"]
                fecha_cambio = row["fecha_hora"]

                # Buscar registros de motivo y tipo de falla cercanos (mismo día, mismo EDP)
                fecha_inicio = fecha_cambio - pd.Timedelta(hours=1)
                fecha_fin = fecha_cambio + pd.Timedelta(hours=1)

                # Buscar motivo cercano
                motivo_cercano = df_log[
                    (df_log["n_edp"] == edp_id)
                    & (df_log["campo"] == "motivo_no_aprobado")
                    & (pd.to_datetime(df_log["fecha_hora"]) >= fecha_inicio)
                    & (pd.to_datetime(df_log["fecha_hora"]) <= fecha_fin)
                ]

                # Buscar tipo de falla cercano
                tipo_cercano = df_log[
                    (df_log["n_edp"] == edp_id)
                    & (df_log["campo"] == "tipo_falla")
                    & (pd.to_datetime(df_log["fecha_hora"]) >= fecha_inicio)
                    & (pd.to_datetime(df_log["fecha_hora"]) <= fecha_fin)
                ]

                # Crear registro enriquecido
                registro = {
                    "n_edp": edp_id,
                    "proyecto": row.get("proyecto", ""),
                    "cliente": row.get("cliente", ""),
                    "jefe_proyecto": row.get("jefe_proyecto", ""),
                    "Fecha": fecha_cambio,
                    "Estado Anterior": row["antes"],
                    "motivo_no_aprobado": (
                        motivo_cercano["despues"].iloc[0]
                        if not motivo_cercano.empty
                        else row.get("motivo_no_aprobado", "")
                    ),
                    "tipo_falla": (
                        tipo_cercano["despues"].iloc[0]
                        if not tipo_cercano.empty
                        else row.get("tipo_falla", "")
                    ),
                    "usuario": row["usuario"],
                }

                retrabajos_completos.append(registro)

            # Crear DataFrame para análisis detallado
            df_analisis = pd.DataFrame(retrabajos_completos)
            # ====== ANÁLISIS DETALLADO DE RETRABAJOS ======
            # 1. Análisis por motivo de rechazo
            if not df_analisis.empty and "motivo_no_aprobado" in df_analisis.columns:
                motivos_rechazo = (
                    df_analisis["motivo_no_aprobado"].value_counts().to_dict()
                )
            else:
                motivos_rechazo = {}

            # 2. Análisis por tipo de falla
            if not df_analisis.empty and "tipo_falla" in df_analisis.columns:
                tipos_falla = df_analisis["tipo_falla"].value_counts().to_dict()
            else:
                tipos_falla = {}

            # 3. Análisis por encargado
            if not df_analisis.empty and "jefe_proyecto" in df_analisis.columns:
                retrabajos_por_encargado = (
                    df_analisis["jefe_proyecto"].value_counts().to_dict()
                )
            else:
                retrabajos_por_encargado = {}

            # 4. Análisis temporal
            if not df_analisis.empty and "Fecha" in df_analisis.columns:
                df_analisis["mes"] = df_analisis["Fecha"].dt.strftime("%Y-%m")
                tendencia_por_mes = (
                    df_analisis["mes"].value_counts().sort_index().to_dict()
                )
            else:
                tendencia_por_mes = {}

            # 5. Análisis por proyecto
            if not df_analisis.empty and "proyecto" in df_analisis.columns:
                retrabajos_por_proyecto_raw = (
                    df_analisis["proyecto"].value_counts().to_dict()
                )

                # Estructura correcta para cada proyecto
                proyectos_problematicos = {}
                for proyecto, cantidad in retrabajos_por_proyecto_raw.items():
                    # Buscar el total de EDPs para este proyecto
                    total_edps_proyecto = (
                        len(df_edp[df_edp["proyecto"] == proyecto])
                        if "proyecto" in df_edp.columns
                        else 0
                    )

                    # Calcular el porcentaje
                    porcentaje = (
                        round((cantidad / total_edps_proyecto * 100), 1)
                        if total_edps_proyecto > 0
                        else 0
                    )

                    # Crear estructura de datos correcta
                    proyectos_problematicos[proyecto] = {
                        "total": total_edps_proyecto,
                        "retrabajos": cantidad,
                        "porcentaje": porcentaje,
                    }
            else:
                proyectos_problematicos = {}
            # 6. Análisis por usuario solicitante
            if not df_analisis.empty and "usuario" in df_analisis.columns:
                usuarios_solicitantes = df_analisis["usuario"].value_counts().to_dict()
            else:
                usuarios_solicitantes = {}

            # Calcular estadísticas globales
            total_edps = len(df_edp)
            porcentaje_edps_afectados = (
                round((edps_unicos_con_retrabajo / total_edps * 100), 1)
                if total_edps > 0
                else 0
            )

            # ====== CALCULAR PORCENTAJES ======
            porcentaje_motivos = {}
            for motivo, cantidad in motivos_rechazo.items():
                porcentaje_motivos[motivo] = (
                    round((cantidad / total_retrabajos_log * 100), 1)
                    if total_retrabajos_log > 0
                    else 0
                )

            porcentaje_tipos = {}
            for tipo, cantidad in tipos_falla.items():
                porcentaje_tipos[tipo] = (
                    round((cantidad / total_retrabajos_log * 100), 1)
                    if total_retrabajos_log > 0
                    else 0
                )

            # ====== PREPARAR DATOS PARA GRÁFICOS ======
            chart_data = {
                "motivos_labels": list(motivos_rechazo.keys()),
                "motivos_data": list(motivos_rechazo.values()),
                "tipos_labels": list(tipos_falla.keys()),
                "tipos_data": list(tipos_falla.values()),
                "tendencia_meses": list(tendencia_por_mes.keys()),
                "tendencia_valores": list(tendencia_por_mes.values()),
                "encargados": list(retrabajos_por_encargado.keys()),
                "retrabajos_encargado": list(retrabajos_por_encargado.values()),
                # Add missing 'eficiencia' key to chart_data
                "eficiencia": [],  # Initialize with empty list
            }
            # Calculate efficiency metrics if we have data for encargados
            if chart_data["encargados"]:

                for encargado in chart_data["encargados"]:
                    # Find total EDPs for this encargado in the original dataset
                    total_edps_encargado = len(
                        df_edp[df_edp["jefe_proyecto"] == encargado]
                    )
                    # Find retrabajos count for this encargado
                    retrabajos_count = retrabajos_por_encargado.get(encargado, 0)

                    if total_edps_encargado > 0:
                        # Efficiency = 100 - (retrabajos/total_edps * 100)
                        # Higher is better - fewer retrabajos per EDP means higher efficiency
                        eficiencia = 100 - (
                            retrabajos_count / total_edps_encargado * 100
                        )
                        # Cap at 0 to avoid negative efficiency
                        eficiencia = max(0, round(eficiencia, 1))
                    else:
                        eficiencia = 0

                    chart_data["eficiencia"].append(eficiencia)
            # ====== Calcular Impacto Financiero ======
            impacto_financiero = 0
            # for _, row in df_log_enriquecido.iterrows():
            #     impacto_financiero += row.get("monto_aprobado", 0)

            # ====== PREPARAR DATOS PARA LA TABLA DE REGISTROS ======
            registros = retrabajos_completos
            registros = self._clean_nat_values(registros)

            # ====== OPCIONES PARA FILTROS ======
            filter_options = {
                "meses": sorted(df_edp["mes"].dropna().unique()),
                "encargados": sorted(df_edp["jefe_proyecto"].dropna().unique()),
                "clientes": sorted(df_edp["cliente"].dropna().unique()),
                "tipos_falla": (
                    sorted(df_edp["tipo_falla"].dropna().unique())
                    if "tipo_falla" in df_edp.columns
                    else []
                ),
            }

            # ====== ESTADÍSTICAS RESUMEN ======
            stats = {
                "total_edps": total_edps,
                "total_retrabajos": total_retrabajos_log,  # Total de ocurrencias de re-trabajo
                "edps_con_retrabajo": edps_unicos_con_retrabajo,  # Número de EDPs únicos con re-trabajo
                "porcentaje_edps_afectados": porcentaje_edps_afectados,
                "porcentaje_retrabajos": porcentaje_edps_afectados,  # Añadir este campo para compatibilidad
                "promedio_retrabajos_por_edp": (
                    round(total_retrabajos_log / edps_unicos_con_retrabajo, 2)
                    if edps_unicos_con_retrabajo > 0
                    else 0
                ),
            }
            data = {
                "stats": stats,
                "motivos_rechazo": motivos_rechazo,
                "porcentaje_motivos": porcentaje_motivos,
                "tipos_falla": tipos_falla,
                "porcentaje_tipos": porcentaje_tipos,
                "retrabajos_por_encargado": retrabajos_por_encargado,
                "tendencia_por_mes": tendencia_por_mes,
                "proyectos_problematicos": proyectos_problematicos,
                "registros": registros,
                "chart_data": chart_data,
                "filter_options": filter_options,
                "usuarios_solicitantes": usuarios_solicitantes,
                "impacto_financiero": impacto_financiero,
            }
            # ====== RETORNAR TEMPLATE CON TODOS LOS DATOS ======
            return data
        except Exception as e:
            import traceback

            logger.error(f"Error en analisis_retrabajos: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "data": [],
                "message": f"Error retrieving EDPs DataFrame: {str(e)}",
            }
