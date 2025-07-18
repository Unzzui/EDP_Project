"""
Cash Flow Service - Servicio para proyecciones de flujo de caja y análisis financiero avanzado
Maneja forecasting, análisis de aging buckets, proyecciones de cobro y alertas financieras
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

logger = logging.getLogger(__name__)

class CashFlowService:
    """Servicio para análisis de flujo de caja y proyecciones financieras"""
    
    def __init__(self):
        from ..repositories.edp_repository import EDPRepository
        from ..repositories.log_repository import LogRepository
        self.edp_repository = EDPRepository()
        self.log_repository = LogRepository()
        self.date_utils = DateUtils()
        self.format_utils = FormatUtils()
        self.validation_utils = ValidationUtils()
    
    def generar_cash_forecast(self, filtros: Optional[Dict] = None) -> ServiceResponse:
        """
        Genera proyección de flujo de caja basada en EDPs pendientes
        
        Args:
            filtros: Filtros para el análisis (fechas, clientes, etc.)
            
        Returns:
            ServiceResponse con proyección de cash flow
        """
        try:
            # Obtener datos de EDP como DataFrame
            edps_response = self.edp_repository.find_all_dataframe()
            
            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message=f"Error al obtener datos de EDP para cash forecast: {edps_response.get('message', 'Error desconocido')}"
                )
            
            # Extract the DataFrame
            df_edp = edps_response.get('data', pd.DataFrame())
            if df_edp.empty:
                return ServiceResponse(
                    success=False,
                    message="No hay datos de EDP disponibles para generar forecast"
                )
                
            # Aplicar filtros
            filtros = filtros or {}
            df_filtrado = self._aplicar_filtros_cashflow(df_edp, filtros)
            
            # Filtrar solo EDPs pendientes de cobro
            df_pendientes = df_filtrado[
                ~df_filtrado["estado"].isin(["pagado", "validado"])
            ].copy()
            
            if df_pendientes.empty:
                return ServiceResponse(
                    success=True,
                    data=self._cash_forecast_vacio(),
                    message="No hay EDPs pendientes para proyección"
                )
            
            # Calcular días pendientes
            hoy = pd.Timestamp.now().normalize()
            df_pendientes["dias_pendiente"] = (
                hoy - pd.to_datetime(df_pendientes["fecha_emision"])
            ).dt.days
            
            # Generar buckets de aging
            buckets = self._generar_aging_buckets(df_pendientes)
            
            # Aplicar distribución inteligente si es necesario
            buckets_ajustados = self._aplicar_distribucion_inteligente(
                df_pendientes, buckets, df_filtrado
            )
            
            # Calcular probabilidades de cobro
            probabilidades = self._calcular_probabilidades_cobro(buckets_ajustados)
            
            # Generar proyección final
            proyeccion = self._generar_proyeccion_final(buckets_ajustados, probabilidades)
            
            # Agregar métricas de calidad
            metricas_calidad = self._calcular_metricas_calidad(df_pendientes)
            
            forecast_data = {
                **proyeccion,
                'buckets': buckets_ajustados,
                'probabilidades': probabilidades,
                'metricas_calidad': metricas_calidad,
                'fecha_generacion': datetime.now().isoformat(),
                'total_backlog': float(df_pendientes["monto_aprobado"].sum())
            }
            
            return ServiceResponse(
                success=True,
                data=forecast_data,
                message="Cash forecast generado exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error generando cash forecast: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al generar cash forecast: {str(e)}"
            )
    
    def analizar_aging_buckets(self, filtros: Optional[Dict] = None) -> ServiceResponse:
        """
        Análisis detallado de aging buckets y distribución por antigüedad
        
        Args:
            filtros: Filtros para el análisis
            
        Returns:
            ServiceResponse con análisis de aging
        """
        try:
            # Obtener datos de EDP como DataFrame
            edps_response = self.edp_repository.find_all_dataframe()
            
            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message=f"Error al obtener datos para aging analysis: {edps_response.get('message', 'Error desconocido')}"
                )
            
            # Extract the DataFrame
            df_edp = edps_response.get('data', pd.DataFrame())
            if df_edp.empty:
                return ServiceResponse(
                    success=False,
                    message="No hay datos de EDP disponibles para análisis de aging"
                )
            
            # Aplicar filtros
            filtros = filtros or {}
            df_filtrado = self._aplicar_filtros_cashflow(df_edp, filtros)
            
            # Filtrar pendientes
            df_pendientes = df_filtrado[
                ~df_filtrado["estado"].isin(["pagado", "validado"])
            ].copy()
            
            if df_pendientes.empty:
                return ServiceResponse(
                    success=True,
                    data={'buckets': [], 'stats': {}},
                    message="No hay EDPs pendientes para análisis de aging"
                )
            
            # Calcular días pendientes
            hoy = pd.Timestamp.now().normalize()
            df_pendientes["dias_pendiente"] = (
                hoy - pd.to_datetime(df_pendientes["fecha_emision"])
            ).dt.days
            
            # Generar buckets detallados
            buckets_detallados = self._generar_buckets_detallados(df_pendientes)
            
            # Estadísticas de aging
            stats_aging = self._calcular_estadisticas_aging(df_pendientes)
            
            # Análisis por cliente
            aging_por_cliente = self._analizar_aging_por_cliente(df_pendientes)
            
            # Trends históricos
            trends_historicos = self._analizar_trends_aging(df_edp)
            
            aging_data = {
                'buckets_detallados': buckets_detallados,
                'stats_aging': stats_aging,
                'aging_por_cliente': aging_por_cliente,
                'trends_historicos': trends_historicos
            }
            
            return ServiceResponse(
                success=True,
                data=aging_data,
                message="Análisis de aging completado exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de aging: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al analizar aging buckets: {str(e)}"
            )
    
    def obtener_alertas_criticas(self, filtros: Optional[Dict] = None) -> ServiceResponse:
        """
        Obtiene alertas críticas financieras y operacionales
        
        Args:
            filtros: Filtros para las alertas
            
        Returns:
            ServiceResponse con alertas críticas
        """
        try:
            # Obtener datos de EDP como DataFrame
            edps_response = self.edp_repository.find_all_dataframe()
            
            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message=f"Error al obtener datos para alertas: {edps_response.get('message', 'Error desconocido')}"
                )
            
            # Extract the DataFrame
            df_edp = edps_response.get('data', pd.DataFrame())
            if df_edp.empty:
                return ServiceResponse(
                    success=False,
                    message="No hay datos de EDP disponibles para generar alertas"
                )
                
            # Aplicar filtros
            filtros = filtros or {}
            df_filtrado = self._aplicar_filtros_cashflow(df_edp, filtros)
            
            alertas = []
            
            # Alertas de EDPs vencidos
            alertas_vencidos = self._generar_alertas_vencidos(df_filtrado)
            alertas.extend(alertas_vencidos)
            
            # Alertas de concentración de cliente
            alertas_concentracion = self._generar_alertas_concentracion(df_filtrado)
            alertas.extend(alertas_concentracion)
            
            # Alertas de cash flow
            alertas_cashflow = self._generar_alertas_cashflow(df_filtrado)
            alertas.extend(alertas_cashflow)
            
            # Alertas de rendimiento
            alertas_rendimiento = self._generar_alertas_rendimiento(df_filtrado)
            alertas.extend(alertas_rendimiento)
            
            # Priorizar alertas
            alertas_priorizadas = self._priorizar_alertas(alertas)
            
            return ServiceResponse(
                success=True,
                data={'alertas': alertas_priorizadas},
                message=f"Generadas {len(alertas_priorizadas)} alertas críticas"
            )
            
        except Exception as e:
            logger.error(f"Error generando alertas: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al generar alertas: {str(e)}"
            )
    
    def proyectar_flujo_caja_detallado(self, meses: int = 6, filtros: Optional[Dict] = None) -> ServiceResponse:
        """
        Proyección detallada de flujo de caja por períodos específicos
        
        Args:
            meses: Número de meses a proyectar
            filtros: Filtros para la proyección
            
        Returns:
            ServiceResponse con proyección detallada
        """
        try:
            # Obtener datos de EDP como DataFrame
            edps_response = self.edp_repository.find_all_dataframe()
            
            # Check if the response has a success key (dictionary)
            if isinstance(edps_response, dict) and not edps_response.get('success', False):
                return ServiceResponse(
                    success=False,
                    message=f"Error al obtener datos para proyección: {edps_response.get('message', 'Error desconocido')}"
                )
            
            # Extract the DataFrame
            df_edp = edps_response.get('data', pd.DataFrame())
            if df_edp.empty:
                return ServiceResponse(
                    success=False,
                    message="No hay datos de EDP disponibles para proyección"
                )
            
            # Aplicar filtros
            filtros = filtros or {}
            df_filtrado = self._aplicar_filtros_cashflow(df_edp, filtros)
            
            # Generar proyección mensual
            proyeccion_mensual = self._generar_proyeccion_mensual(df_filtrado, meses)
            
            # Análisis de escenarios
            escenarios = self._generar_analisis_escenarios(df_filtrado, meses)
            
            # Métricas de confianza
            metricas_confianza = self._calcular_metricas_confianza(df_filtrado)
            
            proyeccion_data = {
                'proyeccion_mensual': proyeccion_mensual,
                'escenarios': escenarios,
                'metricas_confianza': metricas_confianza,
                'periodo_analisis': meses
            }
            
            return ServiceResponse(
                success=True,
                data=proyeccion_data,
                message="Proyección detallada generada exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error en proyección detallada: {str(e)}")
            return ServiceResponse(
                success=False,
                message=f"Error al generar proyección detallada: {str(e)}"
            )
    
    # Métodos privados de apoyo
    
    def _aplicar_filtros_cashflow(self, df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
        """Aplica filtros específicos para análisis de cash flow"""
        df_filtrado = df.copy()
        
        if filtros.get('fecha_inicio'):
            df_filtrado = df_filtrado[
                pd.to_datetime(df_filtrado['fecha_emision']) >= 
                pd.to_datetime(filtros['fecha_inicio'])
            ]
        
        if filtros.get('fecha_fin'):
            df_filtrado = df_filtrado[
                pd.to_datetime(df_filtrado['fecha_emision']) <= 
                pd.to_datetime(filtros['fecha_fin'])
            ]
        
        if filtros.get('cliente'):
            df_filtrado = df_filtrado[df_filtrado['cliente'] == filtros['cliente']]
        
        if filtros.get('departamento'):
            df_filtrado = df_filtrado[df_filtrado['jefe_proyecto'] == filtros['departamento']]
        
        if filtros.get('estado'):
            df_filtrado = df_filtrado[df_filtrado['estado'] == filtros['estado']]
        
        return df_filtrado
    
    def _generar_aging_buckets(self, df_pendientes: pd.DataFrame) -> Dict:
        """Genera buckets de aging estándar (30, 60, 90+ días)"""
        # Bucket 0-30 días
        df_30d = df_pendientes[df_pendientes["dias_pendiente"] <= 30]
        total_30d = float(df_30d["monto_aprobado"].sum())
        
        # Bucket 31-60 días
        df_60d = df_pendientes[
            (df_pendientes["dias_pendiente"] > 30) & (df_pendientes["dias_pendiente"] <= 60)
        ]
        total_60d = float(df_60d["monto_aprobado"].sum())
        
        # Bucket 61-90 días
        df_90d = df_pendientes[
            (df_pendientes["dias_pendiente"] > 60) & (df_pendientes["dias_pendiente"] <= 90)
        ]
        total_90d = float(df_90d["monto_aprobado"].sum())
        
        # Bucket 90+ días
        df_90plus = df_pendientes[df_pendientes["dias_pendiente"] > 90]
        total_90plus = float(df_90plus["monto_aprobado"].sum())
        
        return {
            '0-30': {'monto': total_30d, 'count': len(df_30d), 'df': df_30d},
            '31-60': {'monto': total_60d, 'count': len(df_60d), 'df': df_60d},
            '61-90': {'monto': total_90d, 'count': len(df_90d), 'df': df_90d},
            '90+': {'monto': total_90plus, 'count': len(df_90plus), 'df': df_90plus}
        }
    
    def _aplicar_distribucion_inteligente(self, df_pendientes: pd.DataFrame, 
                                        buckets: Dict, df_completo: pd.DataFrame) -> Dict:
        """Aplica distribución inteligente cuando hay concentración excesiva"""
        total_backlog = sum(bucket['monto'] for bucket in buckets.values())
        
        if total_backlog == 0:
            return buckets
        
        # Calcular concentración máxima
        concentraciones = [bucket['monto'] / total_backlog for bucket in buckets.values()]
        concentracion_maxima = max(concentraciones)
        
        # Si hay concentración excesiva (>80%), aplicar redistribución
        if concentracion_maxima > 0.8:
            return self._redistribuir_buckets_inteligente(df_pendientes, buckets, df_completo)
        
        return buckets
    
    def _redistribuir_buckets_inteligente(self, df_pendientes: pd.DataFrame, 
                                        buckets: Dict, df_historico: pd.DataFrame) -> Dict:
        """Redistribuye buckets usando patrones históricos"""
        # Análisis histórico de cobros por aging
        patrones_historicos = self._analizar_patrones_historicos(df_historico)
        
        # Aplicar redistribución basada en patrones
        total_a_redistribuir = sum(bucket['monto'] for bucket in buckets.values())
        
        # Nuevas distribuciones basadas en histórico
        nueva_dist = {
            '0-30': patrones_historicos.get('30d_rate', 0.4),
            '31-60': patrones_historicos.get('60d_rate', 0.3),
            '61-90': patrones_historicos.get('90d_rate', 0.2),
            '90+': patrones_historicos.get('90plus_rate', 0.1)
        }
        
        buckets_redistribuidos = {}
        for bucket_name, rate in nueva_dist.items():
            new_amount = total_a_redistribuir * rate
            buckets_redistribuidos[bucket_name] = {
                'monto': new_amount,
                'count': buckets[bucket_name]['count'],
                'redistribuido': True
            }
        
        return buckets_redistribuidos
    
    def _calcular_probabilidades_cobro(self, buckets: Dict) -> Dict:
        """Calcula probabilidades de cobro por bucket"""
        probabilidades = {}
        
        for bucket_name, data in buckets.items():
            if bucket_name == '0-30':
                prob = self._calcular_probabilidad_30d(data)
            elif bucket_name == '31-60':
                prob = self._calcular_probabilidad_60d(data)
            elif bucket_name == '61-90':
                prob = self._calcular_probabilidad_90d(data)
            else:  # 90+
                prob = self._calcular_probabilidad_90plus(data)
            
            probabilidades[bucket_name] = prob
        
        return probabilidades
    
    def _calcular_probabilidad_30d(self, bucket_data: Dict) -> float:
        """Calcula probabilidad para bucket 0-30 días"""
        # EDPs recientes tienen alta probabilidad
        base_prob = 0.85
        
        # Ajustar por volumen (muchos EDPs puede reducir probabilidad)
        if bucket_data['count'] > 20:
            base_prob *= 0.9
        
        return min(base_prob, 0.95)
    
    def _calcular_probabilidad_60d(self, bucket_data: Dict) -> float:
        """Calcula probabilidad para bucket 31-60 días"""
        # Probabilidad media-alta
        base_prob = 0.70
        
        # Ajustar por volumen
        if bucket_data['count'] > 15:
            base_prob *= 0.85
        
        return min(base_prob, 0.85)
    
    def _calcular_probabilidad_90d(self, bucket_data: Dict) -> float:
        """Calcula probabilidad para bucket 61-90 días"""
        # Probabilidad media
        base_prob = 0.55
        
        # Ajustar por volumen
        if bucket_data['count'] > 10:
            base_prob *= 0.8
        
        return min(base_prob, 0.70)
    
    def _calcular_probabilidad_90plus(self, bucket_data: Dict) -> float:
        """Calcula probabilidad para bucket 90+ días"""
        # Probabilidad baja pero no cero
        base_prob = 0.35
        
        # EDPs muy antiguos tienen menor probabilidad
        if bucket_data['count'] > 5:
            base_prob *= 0.7
        
        return max(base_prob, 0.15)
    
    def _generar_proyeccion_final(self, buckets: Dict, probabilidades: Dict) -> Dict:
        """Genera proyección final ponderada por probabilidades"""
        total_ponderado = 0
        proyeccion_por_bucket = {}
        
        for bucket_name, bucket_data in buckets.items():
            monto = bucket_data['monto']
            prob = probabilidades.get(bucket_name, 0.5)
            monto_ponderado = monto * prob
            
            total_ponderado += monto_ponderado
            proyeccion_por_bucket[bucket_name] = {
                'monto_original': monto,
                'probabilidad': prob,
                'monto_ponderado': monto_ponderado
            }
        
        return {
            'total_30d': buckets['0-30']['monto'],
            'total_60d': buckets['31-60']['monto'],
            'total_90d': buckets['61-90']['monto'],
            'total_90plus': buckets['90+']['monto'],
            'prob_30d': probabilidades['0-30'],
            'prob_60d': probabilidades['31-60'],
            'prob_90d': probabilidades['61-90'],
            'prob_90plus': probabilidades['90+'],
            'total_ponderado': total_ponderado,
            'proyeccion_por_bucket': proyeccion_por_bucket,
            'labels': ['30 días', '60 días', '90 días', '90+ días'],
            'valores': [buckets['0-30']['monto'], buckets['31-60']['monto'], 
                       buckets['61-90']['monto'], buckets['90+']['monto']]
        }
    
    def _calcular_metricas_calidad(self, df_pendientes: pd.DataFrame) -> Dict:
        """Calcula métricas de calidad del forecast"""
        total_edps = len(df_pendientes)
        total_monto = df_pendientes["monto_aprobado"].sum()
        
        # Concentración por cliente
        concentracion_cliente = (
            df_pendientes.groupby("cliente")["monto_aprobado"].sum().max() / total_monto
        ) if total_monto > 0 else 0
        
        # Variabilidad de montos
        std_monto = df_pendientes["monto_aprobado"].std()
        cv_monto = std_monto / df_pendientes["monto_aprobado"].mean() if df_pendientes["monto_aprobado"].mean() > 0 else 0
        
        # Distribución por días
        dias_promedio = df_pendientes["dias_pendiente"].mean()
        dias_mediana = df_pendientes["dias_pendiente"].median()
        
        return {
            'total_edps_pendientes': total_edps,
            'concentracion_cliente': round(concentracion_cliente, 3),
            'coeficiente_variacion': round(cv_monto, 3),
            'dias_promedio_pendiente': round(dias_promedio, 1),
            'dias_mediana_pendiente': round(dias_mediana, 1),
            'volatilidad': self._calcular_volatilidad_backlog(df_pendientes)
        }
    
    def _calcular_volatilidad_backlog(self, df_pendientes: pd.DataFrame) -> str:
        """Calcula volatilidad del backlog"""
        if len(df_pendientes) == 0:
            return "Sin datos"
        
        cv = df_pendientes["monto_aprobado"].std() / df_pendientes["monto_aprobado"].mean()
        
        if cv < 0.5:
            return "Baja"
        elif cv < 1.0:
            return "Media"
        else:
            return "Alta"
    
    def _cash_forecast_vacio(self) -> Dict:
        """Retorna estructura vacía para cash forecast"""
        return {
            'total_30d': 0,
            'total_60d': 0,
            'total_90d': 0,
            'total_90plus': 0,
            'prob_30d': 0,
            'prob_60d': 0,
            'prob_90d': 0,
            'prob_90plus': 0,
            'total_ponderado': 0,
            'labels': ['30 días', '60 días', '90 días', '90+ días'],
            'valores': [0, 0, 0, 0],
            'metricas_calidad': {
                'total_edps_pendientes': 0,
                'concentracion_cliente': 0,
                'volatilidad': 'Sin datos'
            }
        }
    
    def _analizar_patrones_historicos(self, df_historico: pd.DataFrame) -> Dict:
        """Analiza patrones históricos de cobro"""
        # Análisis simplificado - en producción sería más sofisticado
        df_pagados = df_historico[df_historico["estado"].isin(["pagado", "validado"])]
        
        if df_pagados.empty:
            return {
                '30d_rate': 0.4,
                '60d_rate': 0.3,
                '90d_rate': 0.2,
                '90plus_rate': 0.1
            }
        
        # Calcular días desde emisión hasta pago
        df_pagados = df_pagados.copy()
        df_pagados['dias_hasta_pago'] = (
            pd.to_datetime(df_pagados['Fecha Pago']) - 
            pd.to_datetime(df_pagados['fecha_emision'])
        ).dt.days
        
        # Calcular tasas por bucket
        total_pagados = len(df_pagados)
        
        rate_30d = len(df_pagados[df_pagados['dias_hasta_pago'] <= 30]) / total_pagados
        rate_60d = len(df_pagados[
            (df_pagados['dias_hasta_pago'] > 30) & 
            (df_pagados['dias_hasta_pago'] <= 60)
        ]) / total_pagados
        rate_90d = len(df_pagados[
            (df_pagados['dias_hasta_pago'] > 60) & 
            (df_pagados['dias_hasta_pago'] <= 90)
        ]) / total_pagados
        rate_90plus = len(df_pagados[df_pagados['dias_hasta_pago'] > 90]) / total_pagados
        
        return {
            '30d_rate': rate_30d,
            '60d_rate': rate_60d,
            '90d_rate': rate_90d,
            '90plus_rate': rate_90plus
        }
    
    def _generar_buckets_detallados(self, df_pendientes: pd.DataFrame) -> List[Dict]:
        """Genera buckets más detallados para aging analysis"""
        buckets = [
            {'rango': '0-15', 'min': 0, 'max': 15},
            {'rango': '16-30', 'min': 16, 'max': 30},
            {'rango': '31-45', 'min': 31, 'max': 45},
            {'rango': '46-60', 'min': 46, 'max': 60},
            {'rango': '61-90', 'min': 61, 'max': 90},
            {'rango': '91-120', 'min': 91, 'max': 120},
            {'rango': '120+', 'min': 121, 'max': float('inf')}
        ]
        
        buckets_con_datos = []
        
        for bucket in buckets:
            if bucket['max'] == float('inf'):
                df_bucket = df_pendientes[df_pendientes["dias_pendiente"] >= bucket['min']]
            else:
                df_bucket = df_pendientes[
                    (df_pendientes["dias_pendiente"] >= bucket['min']) & 
                    (df_pendientes["dias_pendiente"] <= bucket['max'])
                ]
            
            monto_total = df_bucket["monto_aprobado"].sum()
            count = len(df_bucket)
            
            buckets_con_datos.append({
                'rango': bucket['rango'],
                'monto': float(monto_total),
                'count': count,
                'porcentaje': round((monto_total / df_pendientes["monto_aprobado"].sum() * 100), 1) 
                if df_pendientes["monto_aprobado"].sum() > 0 else 0
            })
        
        return buckets_con_datos
    
    def _calcular_estadisticas_aging(self, df_pendientes: pd.DataFrame) -> Dict:
        """Calcula estadísticas generales de aging"""
        if df_pendientes.empty:
            return {}
        
        return {
            'dso_promedio': round(df_pendientes["dias_pendiente"].mean(), 1),
            'dso_mediana': round(df_pendientes["dias_pendiente"].median(), 1),
            'dias_max': int(df_pendientes["dias_pendiente"].max()),
            'dias_min': int(df_pendientes["dias_pendiente"].min()),
            'edps_criticos': len(df_pendientes[df_pendientes["dias_pendiente"] > 90]),
            'monto_critico': float(df_pendientes[df_pendientes["dias_pendiente"] > 90]["monto_aprobado"].sum()),
            'porcentaje_critico': round(
                len(df_pendientes[df_pendientes["dias_pendiente"] > 90]) / len(df_pendientes) * 100, 1
            )
        }
    
    def _analizar_aging_por_cliente(self, df_pendientes: pd.DataFrame) -> Dict:
        """Analiza aging por cliente"""
        aging_clientes = {}
        
        for cliente in df_pendientes["cliente"].unique():
            if pd.isna(cliente):
                continue
                
            df_cliente = df_pendientes[df_pendientes["cliente"] == cliente]
            
            aging_clientes[cliente] = {
                'total_edps': len(df_cliente),
                'monto_total': float(df_cliente["monto_aprobado"].sum()),
                'dso_promedio': round(df_cliente["dias_pendiente"].mean(), 1),
                'edps_criticos': len(df_cliente[df_cliente["dias_pendiente"] > 90]),
                'monto_critico': float(df_cliente[df_cliente["dias_pendiente"] > 90]["monto_aprobado"].sum())
            }
        
        return aging_clientes
    
    def _analizar_trends_aging(self, df_historico: pd.DataFrame) -> Dict:
        """Analiza trends históricos de aging"""
        # Análisis simplificado de tendencias por mes
        if df_historico.empty:
            return {}
        
        # Agrupar por mes y calcular DSO promedio
        df_historico = df_historico.copy()
        df_historico['fecha_emision'] = pd.to_datetime(df_historico['fecha_emision'])
        df_historico['año_mes'] = df_historico['fecha_emision'].dt.to_period('M')
        
        trends = df_historico.groupby('año_mes').agg({
            'N° EDP': 'count',
            'monto_aprobado': 'sum'
        }).tail(6)  # Últimos 6 meses
        
        return {
            'meses': [str(periodo) for periodo in trends.index],
            'edps_por_mes': trends['N° EDP'].tolist(),
            'montos_por_mes': trends['monto_aprobado'].tolist()
        }
    
    def _generar_alertas_vencidos(self, df: pd.DataFrame) -> List[Dict]:
        """Genera alertas para EDPs vencidos"""
        alertas = []
        
        # Calcular días pendientes
        hoy = pd.Timestamp.now().normalize()
        df_pendientes = df[~df["estado"].isin(["pagado", "validado"])].copy()
        df_pendientes["dias_pendiente"] = (hoy - pd.to_datetime(df_pendientes["fecha_emision"])).dt.days
        
        # EDPs críticos (>90 días)
        edps_criticos = df_pendientes[df_pendientes["dias_pendiente"] > 90]
        
        if not edps_criticos.empty:
            monto_critico = edps_criticos["monto_aprobado"].sum()
            alertas.append({
                'tipo': 'vencidos_criticos',
                'severidad': 'alta',
                'titulo': f'{len(edps_criticos)} EDPs vencidos críticos',
                'descripcion': f'${monto_critico:,.0f} en EDPs con más de 90 días pendientes',
                'accion': 'Revisar y gestionar cobro inmediato',
                'valor': len(edps_criticos)
            })
        
        return alertas
    
    def _generar_alertas_concentracion(self, df: pd.DataFrame) -> List[Dict]:
        """Genera alertas de concentración de riesgo"""
        alertas = []
        
        # Concentración por cliente
        df_pendientes = df[~df["estado"].isin(["pagado", "validado"])]
        if not df_pendientes.empty:
            total_pendiente = df_pendientes["monto_aprobado"].sum()
            max_cliente = df_pendientes.groupby("cliente")["monto_aprobado"].sum().max()
            concentracion = max_cliente / total_pendiente if total_pendiente > 0 else 0
            
            if concentracion > 0.4:  # Más del 40% en un cliente
                alertas.append({
                    'tipo': 'concentracion_cliente',
                    'severidad': 'media',
                    'titulo': 'Alta concentración en cliente único',
                    'descripcion': f'{concentracion*100:.1f}% del backlog en un solo cliente',
                    'accion': 'Diversificar cartera de clientes',
                    'valor': round(concentracion * 100, 1)
                })
        
        return alertas
    
    def _generar_alertas_cashflow(self, df: pd.DataFrame) -> List[Dict]:
        """Genera alertas específicas de cash flow"""
        alertas = []
        
        # Bajo flujo proyectado para próximos 30 días
        df_pendientes = df[~df["estado"].isin(["pagado", "validado"])].copy()
        if not df_pendientes.empty:
            hoy = pd.Timestamp.now().normalize()
            df_pendientes["dias_pendiente"] = (hoy - pd.to_datetime(df_pendientes["fecha_emision"])).dt.days
            
            monto_30d = df_pendientes[df_pendientes["dias_pendiente"] <= 30]["monto_aprobado"].sum()
            monto_total = df_pendientes["monto_aprobado"].sum()
            porcentaje_30d = monto_30d / monto_total if monto_total > 0 else 0
            
            if porcentaje_30d < 0.3:  # Menos del 30% cobrable en 30 días
                alertas.append({
                    'tipo': 'bajo_flujo_30d',
                    'severidad': 'media',
                    'titulo': 'Bajo flujo proyectado 30 días',
                    'descripcion': f'Solo {porcentaje_30d*100:.1f}% del backlog cobrable en 30 días',
                    'accion': 'Acelerar procesos de cobro',
                    'valor': round(porcentaje_30d * 100, 1)
                })
        
        return alertas
    
    def _generar_alertas_rendimiento(self, df: pd.DataFrame) -> List[Dict]:
        """Genera alertas de rendimiento general"""
        alertas = []
        
        # DSO alto
        df_pendientes = df[~df["estado"].isin(["pagado", "validado"])].copy()
        if not df_pendientes.empty:
            hoy = pd.Timestamp.now().normalize()
            df_pendientes["dias_pendiente"] = (hoy - pd.to_datetime(df_pendientes["fecha_emision"])).dt.days
            
            dso_promedio = df_pendientes["dias_pendiente"].mean()
            
            if dso_promedio > 75:  # DSO alto
                alertas.append({
                    'tipo': 'dso_alto',
                    'severidad': 'media',
                    'titulo': f'DSO elevado: {dso_promedio:.0f} días',
                    'descripcion': 'Tiempo promedio de cobro superior al target (60 días)',
                    'accion': 'Optimizar proceso de cobro',
                    'valor': round(dso_promedio, 0)
                })
        
        return alertas
    
    def _priorizar_alertas(self, alertas: List[Dict]) -> List[Dict]:
        """Prioriza alertas por severidad e impacto"""
        orden_severidad = {'alta': 3, 'media': 2, 'baja': 1}
        
        alertas_priorizadas = sorted(
            alertas, 
            key=lambda x: (orden_severidad.get(x['severidad'], 0), x.get('valor', 0)), 
            reverse=True
        )
        
        return alertas_priorizadas[:10]  # Top 10 alertas
    
    def _generar_proyeccion_mensual(self, df: pd.DataFrame, meses: int) -> List[Dict]:
        """Genera proyección mensual detallada"""
        proyeccion = []
        
        # Simplificado - en producción usaría modelos más sofisticados
        for i in range(meses):
            fecha = datetime.now() + timedelta(days=30*i)
            
            # Proyección básica basada en patterns históricos
            monto_base = df["monto_aprobado"].sum() / meses
            factor_estacional = 1 + (0.1 * np.sin(i * np.pi / 6))  # Variación estacional
            
            proyeccion.append({
                'mes': fecha.strftime('%Y-%m'),
                'monto_proyectado': monto_base * factor_estacional,
                'confianza': max(90 - i*5, 50)  # Decrece confianza con el tiempo
            })
        
        return proyeccion
    
    def _generar_analisis_escenarios(self, df: pd.DataFrame, meses: int) -> Dict:
        """Genera análisis de escenarios optimista/pesimista/realista"""
        base_amount = df[~df["estado"].isin(["pagado", "validado"])]["monto_aprobado"].sum()
        
        return {
            'optimista': {
                'probabilidad_cobro': 0.9,
                'monto_proyectado': base_amount * 0.9,
                'descripcion': 'Escenario con excelente gestión de cobro'
            },
            'realista': {
                'probabilidad_cobro': 0.7,
                'monto_proyectado': base_amount * 0.7,
                'descripcion': 'Escenario basado en performance histórica'
            },
            'pesimista': {
                'probabilidad_cobro': 0.5,
                'monto_proyectado': base_amount * 0.5,
                'descripcion': 'Escenario conservador con retrasos'
            }
        }
    
    def _calcular_metricas_confianza(self, df: pd.DataFrame) -> Dict:
        """Calcula métricas de confianza de la proyección"""
        # Análisis de estabilidad histórica
        meses_unicos = df["Mes"].nunique()
        variabilidad_mensual = df.groupby("Mes")["monto_aprobado"].sum().std()
        promedio_mensual = df.groupby("Mes")["monto_aprobado"].sum().mean()
        
        cv = variabilidad_mensual / promedio_mensual if promedio_mensual > 0 else 0
        
        if cv < 0.2:
            nivel_confianza = "Alto"
        elif cv < 0.5:
            nivel_confianza = "Medio"
        else:
            nivel_confianza = "Bajo"
        
        return {
            'nivel_confianza': nivel_confianza,
            'coeficiente_variacion': round(cv, 3),
            'meses_analizados': meses_unicos,
            'estabilidad_historica': round((1 - cv) * 100, 1)
        }
