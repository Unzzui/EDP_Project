"""
Business Rules Configuration
============================

Centralización de todas las reglas de negocio del sistema EDP.
Modificar aquí para cambiar criterios en todo el sistema.

Autor: Sistema EDP
Fecha: 2025
"""

from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass, field


class EstadoEDP(Enum):
    """Estados posibles de un EDP"""
    PAGADO = "pagado"
    COBRADO = "cobrado"
    FACTURADO_COBRADO = "facturado y cobrado"
    CERRADO = "cerrado"
    FINALIZADO = "finalizado"
    COMPLETADO = "completado"
    ENVIADO = "enviado"
    REVISION = "revision"
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    VALIDADO = "validado"


@dataclass
class CriteriosEDPs:
    """Criterios centralizados para clasificación de EDPs"""
    
    # ============= EDPS CRÍTICOS =============
    CRITICOS_DSO_MINIMO: int = 60  # Días mínimos para considerar crítico
    
    CRITICOS_ESTADOS_EXCLUIDOS: List[str] = field(default_factory=lambda: [
        EstadoEDP.PAGADO.value,
        EstadoEDP.COBRADO.value,
        EstadoEDP.FACTURADO_COBRADO.value,
        EstadoEDP.CERRADO.value,
        EstadoEDP.FINALIZADO.value,
        EstadoEDP.COMPLETADO.value
    ])
    
    # ============= AGING EDPs =============
    AGING_DSO_MINIMO: int = 30  # Días mínimos para aging
    AGING_DSO_MAXIMO: int = 60  # Días máximos para aging
    
    # ============= FAST COLLECTION =============
    FAST_COLLECTION_DSO_MAXIMO: int = 25  # Días máximos para fast collection
    
    FAST_COLLECTION_ESTADOS_FAVORABLES: List[str] = field(default_factory=lambda: [
        EstadoEDP.VALIDADO.value,
        EstadoEDP.PAGADO.value,
        "aprobado"
    ])
    
    # ============= DSO BENCHMARKS =============
    DSO_TARGET: int = 35  # Target ideal de DSO
    DSO_BENCHMARK_INDUSTRIA: int = 45  # Benchmark industria
    DSO_CRITICO: int = 60  # DSO considerado crítico por tiempo
    
    # ============= MONTOS Y VALORES =============
    MONTO_ALTO_THRESHOLD: int = 1_000_000  # 1M CLP para montos altos
    MONTO_MEDIO_THRESHOLD: int = 500_000   # 500K CLP para montos medios
    
    # ============= TENDENCIAS =============
    TENDENCIA_POSITIVA_THRESHOLD: int = -10  # % de cambio para tendencia positiva
    TENDENCIA_NEGATIVA_THRESHOLD: int = 10   # % de cambio para tendencia negativa


class BusinessRules:
    """Reglas de negocio centralizadas del sistema EDP"""
    
    def __init__(self):
        self.criterios = CriteriosEDPs()
    
    # ============= VALIDACIONES PRINCIPALES =============
    
    def es_edp_critico(self, dso_actual: float, estado: str) -> bool:
        """
        Determina si un EDP es crítico según reglas de negocio.
        
        Criterios:
        1. NO está en estado pagado/cobrado/finalizado
        2. DSO actual > umbral definido (30 días por defecto)
        """
        estado_lower = str(estado).strip().lower()
        estados_excluidos = [e.lower() for e in self.criterios.CRITICOS_ESTADOS_EXCLUIDOS]
        
        # No debe estar pagado/cobrado
        no_esta_pagado = estado_lower not in estados_excluidos
        
        # DSO debe superar umbral
        dso_supera_umbral = float(dso_actual or 0) > self.criterios.CRITICOS_DSO_MINIMO
        
        return no_esta_pagado and dso_supera_umbral
    
    def es_edp_aging(self, dso_actual: float, estado: str) -> bool:
        """
        Determina si un EDP está en aging (zona de riesgo medio).
        
        Criterios:
        1. NO está pagado/cobrado
        2. DSO entre umbrales de aging (20-45 días por defecto)
        """
        estado_lower = str(estado).strip().lower()
        estados_excluidos = [e.lower() for e in self.criterios.CRITICOS_ESTADOS_EXCLUIDOS]
        
        no_esta_pagado = estado_lower not in estados_excluidos
        dso_value = float(dso_actual or 0)
        
        en_rango_aging = (
            self.criterios.AGING_DSO_MINIMO <= dso_value <= self.criterios.AGING_DSO_MAXIMO
        )
        
        return no_esta_pagado and en_rango_aging
    
    def es_edp_fast_collection(self, dso_actual: float, estado: str) -> bool:
        """
        Determina si un EDP es de cobro rápido.
        
        Criterios:
        1. DSO bajo (< 25 días por defecto) O
        2. Estado favorable (validado, aprobado, etc.)
        """
        dso_value = float(dso_actual or 0)
        estado_lower = str(estado).strip().lower()
        
        dso_rapido = dso_value < self.criterios.FAST_COLLECTION_DSO_MAXIMO
        
        estados_favorables = [e.lower() for e in self.criterios.FAST_COLLECTION_ESTADOS_FAVORABLES]
        estado_favorable = estado_lower in estados_favorables
        
        return dso_rapido or estado_favorable
    
    # ============= CÁLCULOS DE TENDENCIA =============
    
    def calcular_tendencia_criticos(self, cantidad_criticos: int) -> Dict[str, Any]:
        """
        Calcula tendencia basada en cantidad de EDPs críticos.
        
        Lógica:
        - Más críticos = tendencia negativa
        - Menos críticos = tendencia positiva
        """
        if cantidad_criticos > 5:
            return {"cambio_pct": 12, "direccion": "empeorando", "color": "critical"}
        elif cantidad_criticos > 2:
            return {"cambio_pct": -8, "direccion": "mejorando", "color": "warning"}
        elif cantidad_criticos > 0:
            return {"cambio_pct": -15, "direccion": "buena", "color": "positive"}
        else:
            return {"cambio_pct": -25, "direccion": "excelente", "color": "positive"}
    
    def calcular_tendencia_aging(self, cantidad_aging: int) -> Dict[str, Any]:
        """Calcula tendencia para EDPs en aging"""
        if cantidad_aging > 8:
            return {"cambio_pct": 18, "direccion": "preocupante", "color": "critical"}
        elif cantidad_aging > 4:
            return {"cambio_pct": 5, "direccion": "neutral", "color": "warning"}
        elif cantidad_aging > 0:
            return {"cambio_pct": -12, "direccion": "controlado", "color": "positive"}
        else:
            return {"cambio_pct": -20, "direccion": "excelente", "color": "positive"}
    
    def calcular_tendencia_fast_collection(self, cantidad_fast: int) -> Dict[str, Any]:
        """Calcula tendencia para EDPs de cobro rápido"""
        if cantidad_fast > 10:
            return {"cambio_pct": -25, "direccion": "excelente", "color": "positive"}
        elif cantidad_fast > 5:
            return {"cambio_pct": -15, "direccion": "bueno", "color": "positive"}
        elif cantidad_fast > 2:
            return {"cambio_pct": -8, "direccion": "moderado", "color": "warning"}
        elif cantidad_fast > 0:
            return {"cambio_pct": 5, "direccion": "necesita_mejora", "color": "warning"}
        else:
            return {"cambio_pct": 15, "direccion": "preocupante", "color": "critical"}
    
    # ============= UTILIDADES =============
    
    def obtener_configuracion(self) -> Dict[str, Any]:
        """Retorna toda la configuración actual para debugging/documentación"""
        return {
            "version": "1.0.0",
            "fecha_actualizacion": "2024-12-19",
            "criterios_criticos": {
                "dso_minimo": self.criterios.CRITICOS_DSO_MINIMO,
                "estados_excluidos": self.criterios.CRITICOS_ESTADOS_EXCLUIDOS
            },
            "criterios_aging": {
                "dso_minimo": self.criterios.AGING_DSO_MINIMO,
                "dso_maximo": self.criterios.AGING_DSO_MAXIMO
            },
            "criterios_fast_collection": {
                "dso_maximo": self.criterios.FAST_COLLECTION_DSO_MAXIMO,
                "estados_favorables": self.criterios.FAST_COLLECTION_ESTADOS_FAVORABLES
            },
            "benchmarks": {
                "dso_target": self.criterios.DSO_TARGET,
                "dso_industria": self.criterios.DSO_BENCHMARK_INDUSTRIA,
                "dso_critico": self.criterios.DSO_CRITICO
            }
        }
    
    def validar_configuracion(self) -> Dict[str, bool]:
        """Valida que la configuración sea coherente"""
        return {
            "aging_range_valid": self.criterios.AGING_DSO_MINIMO < self.criterios.AGING_DSO_MAXIMO,
            "thresholds_logical": self.criterios.FAST_COLLECTION_DSO_MAXIMO < self.criterios.CRITICOS_DSO_MINIMO,
            "states_not_empty": len(self.criterios.CRITICOS_ESTADOS_EXCLUIDOS) > 0,
            "dso_benchmarks_logical": self.criterios.DSO_TARGET < self.criterios.DSO_BENCHMARK_INDUSTRIA < self.criterios.DSO_CRITICO
        }


# ============= INSTANCIA GLOBAL =============
# Instancia única para usar en todo el sistema
business_rules = BusinessRules()


# ============= FUNCIONES DE CONVENIENCIA =============
# Funciones directas para uso rápido

def es_critico(dso_actual: float, estado: str) -> bool:
    """Función directa para validar si un EDP es crítico"""
    return business_rules.es_edp_critico(dso_actual, estado)

def es_aging(dso_actual: float, estado: str) -> bool:
    """Función directa para validar si un EDP está en aging"""
    return business_rules.es_edp_aging(dso_actual, estado)

def es_fast_collection(dso_actual: float, estado: str) -> bool:
    """Función directa para validar si un EDP es de cobro rápido"""
    return business_rules.es_edp_fast_collection(dso_actual, estado)

def obtener_tendencia_criticos(cantidad: int) -> Dict[str, Any]:
    """Función directa para calcular tendencia de críticos"""
    return business_rules.calcular_tendencia_criticos(cantidad)

def obtener_tendencia_aging(cantidad: int) -> Dict[str, Any]:
    """Función directa para calcular tendencia de aging"""
    return business_rules.calcular_tendencia_aging(cantidad)

def obtener_tendencia_fast_collection(cantidad: int) -> Dict[str, Any]:
    """Función directa para calcular tendencia de fast collection"""
    return business_rules.calcular_tendencia_fast_collection(cantidad) 