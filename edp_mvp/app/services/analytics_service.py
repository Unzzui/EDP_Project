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
    
    def analizar_retrabajos(self, filtros: Optional[Dict] = None) -> ServiceResponse:
        """
        Análisis completo de retrabajos basado en histórico de logs
        
        Args:
            filtros: Filtros opcionales (mes, encargado, cliente, fechas, etc.)
            
        Returns:
            ServiceResponse con análisis detallado de retrabajos
        """
        try:
            # Obtener datos necesarios
            edps_response = self.edp_repository.get_all()
            logs_response = self.log_repository.get_all()
            
            if not edps_response.success or not logs_response.success:
                return ServiceResponse(
                    success=False,
                    message="Error al obtener datos para análisis de retrabajos"
                )
            
            # Convert to DataFrames if needed
            df_edp = edps_response.data if isinstance(edps_response.data, pd.DataFrame) else pd.DataFrame(edps_response.data)
            df_log = logs_response.data if isinstance(logs_response.data, pd.DataFrame) else pd.DataFrame(logs_response.data)
            
            # Aplicar filtros básicos
            filtros = filtros or {}
            df_filtrado = self._aplicar_filtros_analytics(df_edp, filtros)
            
            # Filtrar retrabajos del log
            df_retrabajos = self._extraer_retrabajos_del_log(df_log, filtros)
            
            # Enriquecer log con datos de EDP
            df_enriquecido = self._enriquecer_log_con_edp(df_retrabajos, df_filtrado)
            
            # Realizar análisis detallado
            analisis = self._realizar_analisis_retrabajos(df_enriquecido, df_filtrado)
            
            return ServiceResponse(
                success=True,
                data=analisis,
                message="Análisis de retrabajos completado exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de retrabajos: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al realizar análisis de retrabajos: {str(e)}"
            )
    
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
                    'tipos_incidencia': {'counts': {}, 'percentages': {}},
                    'tipos_falla': {'counts': {}, 'percentages': {}},
                    'por_proyecto': {},
                    'tendencias': {},
                    'tiempo_resolucion': None,
                    'stats': {
                        'total_incidencias': 0,
                        'incidencias_resueltas': 0,
                        'porcentaje_resuelto': 0
                    }
                },
                message="Análisis de incidencias completado (datos de prueba)"
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
                'tipos_incidencia': analisis_tipos,
                'tipos_falla': analisis_fallas,
                'por_proyecto': analisis_proyectos,
                'tendencias': tendencias,
                'tiempo_resolucion': tiempo_resolucion,
                'stats': {
                    'total_incidencias': len(df_issues),
                    'incidencias_resueltas': len(df_issues.dropna(subset=['Fecha resolución'])),
                    'porcentaje_resuelto': round(
                        len(df_issues.dropna(subset=['Fecha resolución'])) / len(df_issues) * 100, 1
                    ) if len(df_issues) > 0 else 0
                }
            }
            
            return ServiceResponse(
                success=True,
                data=analisis,
                message="Análisis de incidencias completado exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de incidencias: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al realizar análisis de incidencias: {str(e)}"
            )
    
    def obtener_vista_encargado(self, nombre: str, filtros: Optional[Dict] = None) -> ServiceResponse:
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
            if not edps_response.success:
                return ServiceResponse(
                    success=False,
                    message="Error al obtener datos de EDP"
                )
            df = edps_response.data
            df_edp = pd.DataFrame(df.get('edps', []))
            
            # Filtrar por encargado
            df_encargado = df_edp[df_edp["jefe_proyecto"] == nombre].copy()
            print(df_encargado.head())  # Debugging line
            if df_encargado.empty:
                return ServiceResponse(
                    success=False,
                    message=f"No hay EDPs registrados para {nombre}"
                )
            
            # Limpiar y preparar datos
            
            # Análisis financiero
            analisis_financiero = self._analizar_financiero_encargado(df_encargado, nombre)
            
            # Análisis de rendimiento
            analisis_rendimiento = self._analizar_rendimiento_encargado(df_encargado, df_edp)
            
            # Resumen por proyecto
            resumen_proyectos = self._generar_resumen_proyectos(df_encargado)
            
            # Tendencias
            tendencias = self._analizar_tendencias_encargado(df_encargado)
            
            datos_encargado = {
                'nombre': nombre,
                'resumen_proyectos': resumen_proyectos,
                'analisis_financiero': analisis_financiero,
                'analisis_rendimiento': analisis_rendimiento,
                'tendencias': tendencias,
                'registros': df_encargado.to_dict('records')
            }
            
            return ServiceResponse(
                success=True,
                data=datos_encargado,
                message=f"Datos del encargado {nombre} obtenidos exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener vista de encargado {nombre}: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al obtener datos del encargado: {str(e)}"
            )
    
    def obtener_vista_global_encargados(self, filtros: Optional[Dict] = None) -> ServiceResponse:
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
            metricas_comparativas = self._calcular_metricas_comparativas(analisis_encargados)
            
            # Ranking de rendimiento
            ranking = self._generar_ranking_encargados(analisis_encargados)
            
            # Opciones para filtros
            opciones_filtro = self._generar_opciones_filtro(df_edp)
            
            datos_globales = {
                'analisis_encargados': analisis_encargados,
                'metricas_comparativas': metricas_comparativas,
                'ranking': ranking,
                'opciones_filtro': opciones_filtro,
                'filtros_aplicados': filtros
            }
            
            return ServiceResponse(
                success=True,
                data=datos_globales,
                message="Vista global de encargados obtenida exitosamente"
            )
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error al obtener vista global de encargados:\n{error_trace}")
            return ServiceResponse(
                success=False,
                message=f"Error técnico al obtener vista global:\n{str(e)}"
            )
    
    # Métodos privados de apoyo
    
    def _aplicar_filtros_analytics(self, df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
        """Aplica filtros comunes a los DataFrames"""
        df_filtrado = df.copy()
        
        if filtros.get('mes'):
            df_filtrado = df_filtrado[df_filtrado['mes'] == filtros['mes']]
        
        if filtros.get('encargado'):
            df_filtrado = df_filtrado[df_filtrado['jefe_proyecto'] == filtros['encargado']]
        
        if filtros.get('cliente'):
            df_filtrado = df_filtrado[df_filtrado['cliente'] == filtros['cliente']]
        
        if filtros.get('estado'):
            df_filtrado = df_filtrado[df_filtrado['estado'] == filtros['estado']]
        
        return df_filtrado
    
    def _extraer_retrabajos_del_log(self, df_log: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
        """Extrae registros de retrabajos del log histórico"""
        # Filtrar cambios a "re-trabajo solicitado"
        df_retrabajos = df_log[
            (df_log["Campo"] == "Estado Detallado") & 
            (df_log["Después"] == "re-trabajo solicitado")
        ].copy()
        
        # Convertir fechas
        df_retrabajos["Fecha y Hora"] = pd.to_datetime(df_retrabajos["Fecha y Hora"])
        
        # Aplicar filtros temporales
        if filtros.get('fecha_desde'):
            fecha_desde = pd.to_datetime(filtros['fecha_desde'])
            df_retrabajos = df_retrabajos[df_retrabajos["Fecha y Hora"] >= fecha_desde]
        
        if filtros.get('fecha_hasta'):
            fecha_hasta = pd.to_datetime(filtros['fecha_hasta'])
            df_retrabajos = df_retrabajos[df_retrabajos["Fecha y Hora"] <= fecha_hasta]
        
        return df_retrabajos
    
    def _enriquecer_log_con_edp(self, df_log: pd.DataFrame, df_edp: pd.DataFrame) -> pd.DataFrame:
        """Enriquece datos del log con información de EDP"""
        # Limpiar columnas duplicadas si existen
        if "Proyecto" in df_log.columns:
            df_log = df_log.drop(columns=["Proyecto"])
        
        # Hacer merge con datos de EDP
        df_enriquecido = pd.merge(
            df_log,
            df_edp[["N° EDP", "Proyecto", "Jefe de Proyecto", "Cliente", "Mes", 
                   "Tipo_falla", "Motivo No-aprobado", "Monto Aprobado"]],
            on="N° EDP",
            how="left"
        )
        
        return df_enriquecido
    
    def _realizar_analisis_retrabajos(self, df_enriquecido: pd.DataFrame, df_edp: pd.DataFrame) -> Dict:
        """Realiza análisis detallado de retrabajos"""
        # Estadísticas básicas
        total_retrabajos = len(df_enriquecido)
        edps_unicos = df_enriquecido["N° EDP"].nunique()
        total_edps = len(df_edp)
        
        # Análisis por motivo
        motivos_rechazo = df_enriquecido["Motivo No-aprobado"].value_counts().to_dict() if not df_enriquecido.empty else {}
        
        # Análisis por tipo de falla
        tipos_falla = df_enriquecido["Tipo_falla"].value_counts().to_dict() if not df_enriquecido.empty else {}
        
        # Análisis por encargado
        retrabajos_por_encargado = df_enriquecido["Jefe de Proyecto"].value_counts().to_dict() if not df_enriquecido.empty else {}
        
        # Tendencias temporales
        if not df_enriquecido.empty:
            df_enriquecido["mes"] = df_enriquecido["Fecha y Hora"].dt.strftime("%Y-%m")
            tendencia_por_mes = df_enriquecido["mes"].value_counts().sort_index().to_dict()
        else:
            tendencia_por_mes = {}
        
        # Análisis por proyecto
        if not df_enriquecido.empty:
            proyectos_raw = df_enriquecido["Proyecto"].value_counts().to_dict()
            proyectos_problematicos = {}
            
            for proyecto, cantidad in proyectos_raw.items():
                total_edps_proyecto = len(df_edp[df_edp["Proyecto"] == proyecto])
                porcentaje = round((cantidad / total_edps_proyecto * 100), 1) if total_edps_proyecto > 0 else 0
                
                proyectos_problematicos[proyecto] = {
                    "total": total_edps_proyecto,
                    "retrabajos": cantidad,
                    "porcentaje": porcentaje
                }
        else:
            proyectos_problematicos = {}
        
        # Calcular porcentajes
        porcentaje_edps_afectados = round((edps_unicos / total_edps * 100), 1) if total_edps > 0 else 0
        
        porcentaje_motivos = {}
        for motivo, cantidad in motivos_rechazo.items():
            porcentaje_motivos[motivo] = round((cantidad / total_retrabajos * 100), 1) if total_retrabajos > 0 else 0
        
        porcentaje_tipos = {}
        for tipo, cantidad in tipos_falla.items():
            porcentaje_tipos[tipo] = round((cantidad / total_retrabajos * 100), 1) if total_retrabajos > 0 else 0
        
        return {
            'stats': {
                'total_retrabajos': total_retrabajos,
                'edps_con_retrabajo': edps_unicos,
                'porcentaje_edps_afectados': porcentaje_edps_afectados,
                'promedio_retrabajos_por_edp': round(total_retrabajos / edps_unicos, 2) if edps_unicos > 0 else 0
            },
            'motivos_rechazo': motivos_rechazo,
            'porcentaje_motivos': porcentaje_motivos,
            'tipos_falla': tipos_falla,
            'porcentaje_tipos': porcentaje_tipos,
            'retrabajos_por_encargado': retrabajos_por_encargado,
            'tendencia_por_mes': tendencia_por_mes,
            'proyectos_problematicos': proyectos_problematicos,
            'chart_data': {
                'motivos_labels': list(motivos_rechazo.keys()),
                'motivos_data': list(motivos_rechazo.values()),
                'tipos_labels': list(tipos_falla.keys()),
                'tipos_data': list(tipos_falla.values()),
                'tendencia_meses': list(tendencia_por_mes.keys()),
                'tendencia_valores': list(tendencia_por_mes.values()),
                'encargados': list(retrabajos_por_encargado.keys()),
                'retrabajos_encargado': list(retrabajos_por_encargado.values())
            }
        }
    
    def _analizar_tipos_incidencia(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza tipos de incidencia"""
        if 'Tipo' in df_issues.columns:
            tipos = df_issues['Tipo'].value_counts().to_dict()
            total = sum(tipos.values())
            porcentajes = {k: round(v/total*100, 1) for k, v in tipos.items()}
            return {'counts': tipos, 'percentages': porcentajes}
        return {'counts': {}, 'percentages': {}}
    
    def _analizar_tipos_falla(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza tipos de falla"""
        if 'Tipo_falla' in df_issues.columns:
            fallas = df_issues['Tipo_falla'].value_counts().to_dict()
            total = sum(fallas.values())
            porcentajes = {k: round(v/total*100, 1) for k, v in fallas.items()}
            return {'counts': fallas, 'percentages': porcentajes}
        return {'counts': {}, 'percentages': {}}
    
    def _analizar_incidencias_por_proyecto(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza incidencias por proyecto"""
        if 'Proyecto Relacionado' in df_issues.columns:
            return df_issues['Proyecto Relacionado'].value_counts().to_dict()
        return {}
    
    def _analizar_tendencias_incidencias(self, df_issues: pd.DataFrame) -> Dict:
        """Analiza tendencias temporales de incidencias"""
        if 'Timestamp' in df_issues.columns:
            df_issues['Semana'] = df_issues['Timestamp'].dt.isocalendar().week
            return df_issues.groupby('Semana').size().to_dict()
        return {}
    
    def _calcular_tiempo_resolucion(self, df_issues: pd.DataFrame) -> Optional[float]:
        """Calcula tiempo promedio de resolución"""
        if 'Timestamp' in df_issues.columns and 'Fecha resolución' in df_issues.columns:
            resueltas = df_issues.dropna(subset=['Fecha resolución'])
            if not resueltas.empty:
                timestamp_col = pd.to_datetime(resueltas['Timestamp'])
                resolucion_col = pd.to_datetime(resueltas['Fecha resolución'])
                
                # Normalizar zonas horarias
                if hasattr(timestamp_col.dt, 'tz'):
                    timestamp_col = timestamp_col.dt.tz_localize(None)
                if hasattr(resolucion_col.dt, 'tz'):
                    resolucion_col = resolucion_col.dt.tz_localize(None)
                
                # Calcular diferencia en días
                diferencia = resolucion_col - timestamp_col
                tiempo_resolucion = diferencia.dt.total_seconds() / (60 * 60 * 24)
                return tiempo_resolucion.mean()
        return None
    

    
    def _analizar_financiero_encargado(self, df_encargado: pd.DataFrame, nombre: str) -> Dict:
        """Análisis financiero del encargado"""
        # Metas por encargado (esto debería venir de configuración)
        METAS_ENCARGADOS = {
            "Diego Bravo": 375_000_000,
            "Carolina López": 375_000_000,
            "Pedro Rojas": 375_000_000,
            "Ana Pérez": 375_000_000,
        }
        
        meta_encargado = METAS_ENCARGADOS.get(nombre, 375_000_000)
        
        # EDPs pagados
        df_pagados = df_encargado[df_encargado["estado"].isin(["pagado", "validado"])]
        
        monto_pagado = df_pagados["monto_aprobado"].sum()
        monto_pendiente = df_encargado[~df_encargado["estado"].isin(["pagado", "validado"])]["monto_propuesto"].sum()
        
        avance_meta = (monto_pagado / meta_encargado * 100) if meta_encargado > 0 else 0
        
        return {
            'meta_encargado': meta_encargado,
            'monto_pagado': monto_pagado,
            'monto_pendiente': monto_pendiente,
            'avance_meta': round(avance_meta, 1),
            'total_edps': len(df_encargado),
            'edps_pagados': len(df_pagados)
        }
    
    def _analizar_rendimiento_encargado(self, df_encargado: pd.DataFrame, df_global: pd.DataFrame) -> Dict:
        """Análisis de rendimiento comparativo del encargado"""
        # DSO del encargado vs global
        dso_encargado = self._calcular_dso_dataset(df_encargado)
        dso_global = self._calcular_dso_dataset(df_global)
        
        # Análisis de criticidad
        edps_criticos = df_encargado[df_encargado["critico"] == 1]
        porcentaje_criticos = (len(edps_criticos) / len(df_encargado) * 100) if len(df_encargado) > 0 else 0
        
        return {
            'dso_encargado': dso_encargado,
            'dso_global': dso_global,
            'diferencia_dso': dso_encargado - dso_global,
            'edps_criticos': len(edps_criticos),
            'porcentaje_criticos': round(porcentaje_criticos, 1)
        }
    
    def _generar_resumen_proyectos(self, df_encargado: pd.DataFrame) -> Dict:
        """Genera resumen por proyecto para el encargado"""
        resumen = df_encargado.groupby("Proyecto").agg({
            "n_edp": "count",
            "critico": "sum",
            "monto_propuesto": "sum",
            "monto_aprobado": "sum"
        }).rename(columns={
            "n_edp": "Total_EDP",
            "critico": "Críticos",
            "monto_propuesto": "Monto_Propuesto_Total",
            "monto_aprobado": "Monto_Aprobado_Total"
        })
        
        # Calcular montos pagados por proyecto
        df_pagados = df_encargado[df_encargado["estado"].isin(["pagado", "validado"])]
        monto_pagado_por_proyecto = df_pagados.groupby("proyecto")["monto_aprobado"].sum()
        
        resumen = resumen.merge(monto_pagado_por_proyecto.rename("Monto_Pagado"), 
                               left_index=True, right_index=True, how="left")
        resumen["Monto_Pagado"] = resumen["Monto_Pagado"].fillna(0)
        
        # Calcular monto pendiente
        resumen["Monto_Pendiente"] = resumen["Monto_Aprobado_Total"] - resumen["Monto_Pagado"]
        
        return resumen.to_dict('index')
    
    def _analizar_tendencias_encargado(self, df_encargado: pd.DataFrame) -> Dict:
        """Analiza tendencias del encargado"""
        # Análisis por mes (últimos 3 meses)
        meses_unicos = sorted(df_encargado["mes"].unique())[-3:]
        
        tendencia_cobro = []
        for mes in meses_unicos:
            df_mes = df_encargado[(df_encargado["mes"] == mes) & (df_encargado["estado"] == "pagado")]
            monto_mes = df_mes["monto_aprobado"].sum()
            tendencia_cobro.append({
                'mes': mes,
                'monto': monto_mes
            })
        
        return {
            'tendencia_cobro': tendencia_cobro,
            'meses_analizados': meses_unicos
        }
    
    def _calcular_dso_dataset(self, df: pd.DataFrame) -> float:
        """
        Calcula DSO global (promedio de días en que los EDPs han estado abiertos),
        considerando tanto los pagados como los pendientes. Se asume que la columna
        'dias_espera' ya está calculada correctamente para cada estado.
        """
        if df.empty or 'dias_espera' not in df.columns:
            return 0
        return df['dias_espera'].mean()

    
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
            df_pagados = df_encargado[df_encargado["estado"].isin(["pagado", "validado"])]
            monto_pagado = df_pagados["monto_aprobado"].sum()
            monto_pendiente = df_encargado[~df_encargado["estado"].isin(["pagado", "validado"])]["monto_propuesto"].sum()
            
            # DSO
            dso = self._calcular_dso_dataset(df_encargado)
            
            # Criticidad
            edps_criticos = len(df_encargado[df_encargado["critico"] == 1])
            
            analisis[encargado] = {
                'total_edps': total_edps,
                'edps_pagados': len(df_pagados),
                'monto_pagado': monto_pagado,
                'monto_pendiente': monto_pendiente,
                'dso': round(dso, 1),
                'edps_criticos': edps_criticos,
                'porcentaje_criticos': round((edps_criticos / total_edps * 100), 1) if total_edps > 0 else 0,
                'eficiencia': round((len(df_pagados) / total_edps * 100), 1) if total_edps > 0 else 0
            }
        
        return analisis
    
    def _calcular_metricas_comparativas(self, analisis_encargados: Dict) -> Dict:
        """Calcula métricas comparativas entre encargados"""
        if not analisis_encargados:
            return {}
        
        # Extraer valores para comparación
        montos_pagados = [data['monto_pagado'] for data in analisis_encargados.values()]
        dsos = [data['dso'] for data in analisis_encargados.values()]
        eficiencias = [data['eficiencia'] for data in analisis_encargados.values()]
        
        return {
            'promedio_monto_pagado': np.mean(montos_pagados),
            'mejor_monto_pagado': max(montos_pagados),
            'peor_monto_pagado': min(montos_pagados),
            'promedio_dso': np.mean(dsos),
            'mejor_dso': min(dsos),  # Menor DSO es mejor
            'peor_dso': max(dsos),
            'promedio_eficiencia': np.mean(eficiencias),
            'mejor_eficiencia': max(eficiencias),
            'peor_eficiencia': min(eficiencias)
        }
    
    def _generar_ranking_encargados(self, analisis_encargados: Dict) -> List[Dict]:
        """Genera ranking de encargados por rendimiento"""
        ranking = []
        
        for encargado, data in analisis_encargados.items():
            # Cálculo de score compuesto (ejemplo)
            score_monto = data['monto_pagado'] / 1_000_000  # Normalizar a millones
            score_eficiencia = data['eficiencia']
            score_dso = max(0, 100 - data['dso'])  # Inverso del DSO
            
            score_total = (score_monto * 0.4) + (score_eficiencia * 0.3) + (score_dso * 0.3)
            
            ranking.append({
                'encargado': encargado,
                'score_total': round(score_total, 2),
                'monto_pagado': data['monto_pagado'],
                'eficiencia': data['eficiencia'],
                'dso': data['dso']
            })
        
        # Ordenar por score total descendente
        ranking.sort(key=lambda x: x['score_total'], reverse=True)
        
        # Agregar posición
        for i, item in enumerate(ranking):
            item['posicion'] = i + 1
        
        return ranking
    
    def _generar_opciones_filtro(self, df: pd.DataFrame) -> Dict:
        """Genera opciones para filtros dinámicos"""
        return {
            'meses': sorted(df["mes"].dropna().unique()),
            'encargados': sorted(df["jefe_proyecto"].dropna().unique()),
            'clientes': sorted(df["cliente"].dropna().unique()),
            'estados': sorted(df["estado"].dropna().unique()),
            'proyectos': sorted(df["proyecto"].dropna().unique())
        }
