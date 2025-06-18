from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# === ENUMS ===
class EstadoEDP(str, Enum):
    ENVIADO = "enviado"
    REVISION = "revisión"
    VALIDADO = "validado"
    PAGADO = "pagado"
    PENDIENTE = "pendiente"

class TipoMovimiento(str, Enum):
    INGRESO = "ingreso"
    EGRESO = "egreso"

# === MODELOS DE EDP ===
class EDPEstado(str, Enum):
    creado = "creado"
    revision_interna = "revisión interna"
    revision = "revisión"  # Agregado para compatibilidad
    enviado_cliente = "enviado cliente"
    revision_cliente = "revisión cliente"
    aprobado = "aprobado"
    retrabajo = "re-trabajo"
    conformidad_emitida = "conformidad emitida"
    enviado = "enviado"

class TipoFalla(str, Enum):
    retraso_documental = "retraso_documental"
    inconsistencia_montos = "inconsistencia_montos"
    error_tecnico = "error_tecnico"
    falta_informacion = "falta_informacion"
    documentacion = "documentación"  # Agregado para compatibilidad

class MotivoNoAprobado(str, Enum):
    inconsistencia_montos = "inconsistencia_montos"
    documentacion_incompleta = "documentacion_incompleta"
    error_tecnico = "error_tecnico"
    revision_pendiente = "revision_pendiente"
    fuera_alcance = "fuera_alcance"  # Agregado para compatibilidad
    requisitos_tecnicos = "requisitos_tecnicos"  # Agregado para compatibilidad
    fecha_incorrecta = "Fecha incorrecta"  # Agregado para compatibilidad

class EDP(BaseModel):
    id: Optional[str] = None  # Cambiado a string para compatibilidad con datos demo
    n_edp: Optional[int] = None
    proyecto: Optional[str] = None
    cliente: Optional[str] = None
    gestor: Optional[str] = None
    jefe_proyecto: Optional[str] = None
    mes: Optional[str] = None  # Format: YYYY-MM
    fecha_emision: Optional[date] = None
    fecha_envio_cliente: Optional[date] = None
    monto_propuesto: Optional[float] = None
    monto_aprobado: Optional[float] = None
    fecha_estimada_pago: Optional[date] = None
    conformidad_enviada: Optional[str] = None  # "Sí" / "No"
    n_conformidad: Optional[str] = None
    fecha_conformidad: Optional[date] = None
    estado: Optional[str] = None  # Cambiado a string para flexibilidad
    observaciones: Optional[str] = None
    registrado_por: Optional[str] = None
    estado_detallado: Optional[str] = None
    fecha_registro: Optional[date] = None
    motivo_no_aprobado: Optional[str] = None  # Cambiado a string para flexibilidad
    tipo_falla: Optional[str] = None  # Cambiado a string para flexibilidad

class EDPFilters(BaseModel):
    estado: Optional[str] = None
    cliente: Optional[str] = None
    jefe_proyecto: Optional[str] = None
    mes: Optional[str] = None
    proyecto: Optional[str] = None
    gestor: Optional[str] = None
    conformidad_enviada: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None

class EDPResponse(BaseModel):
    data: List[EDP]
    total: int
    limit: int
    offset: int
    has_more: bool
    cache_info: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None

class EDPStats(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_client: Dict[str, int]
    by_project_manager: Dict[str, int]
    total_amount_proposed: float
    total_amount_approved: float
    average_amount: float
    conformity_rate: float
    last_updated: datetime

# === MODELOS PARA PROYECTOS ===
class Moneda(str, Enum):
    CLP = "CLP"
    USD = "USD"
    EUR = "EUR"

class Project(BaseModel):
    project_id: str
    proyecto: Optional[str] = None
    cliente: Optional[str] = None
    gestor: Optional[str] = None
    jefe_proyecto: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin_prevista: Optional[date] = None
    monto_contrato: Optional[float] = None
    moneda: Optional[Moneda] = None

class ProjectFilters(BaseModel):
    cliente: Optional[str] = None
    jefe_proyecto: Optional[str] = None
    gestor: Optional[str] = None
    moneda: Optional[str] = None  # Cambiado a string para flexibilidad
    fecha_inicio_desde: Optional[date] = None
    fecha_inicio_hasta: Optional[date] = None

class ProjectResponse(BaseModel):
    data: List[Project]
    total: int
    stats: Dict[str, Any]
    last_updated: Optional[datetime] = None

# === MODELOS PARA COSTOS ===
class EstadoCosto(str, Enum):
    pendiente = "pendiente"
    pagado = "pagado"
    vencido = "vencido"
    en_revision = "en_revision"

class TipoCosto(str, Enum):
    opex = "opex"
    capex = "capex"
    materiales = "materiales"
    servicios = "servicios"

class CostHeader(BaseModel):
    cost_id: int
    project_id: str
    proveedor: Optional[str] = None
    factura: Optional[str] = None
    fecha_factura: Optional[date] = None
    fecha_recepcion: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    fecha_pago: Optional[date] = None
    importe_bruto: Optional[float] = None
    importe_neto: Optional[float] = None
    moneda: Optional[Moneda] = None
    estado_costo: Optional[str] = None  # Cambiado a string para flexibilidad
    tipo_costo: Optional[str] = None  # Cambiado a string para flexibilidad
    detalle_costo: Optional[str] = None
    detalle_especifico_costo: Optional[str] = None
    responsable_registro: Optional[str] = None
    url_respaldo: Optional[str] = None

class CostLine(BaseModel):
    line_id: int
    cost_id: int
    categoria: Optional[str] = None
    descripcion_item: Optional[str] = None
    unidad: Optional[str] = None
    cantidad: Optional[float] = None
    precio_unitario: Optional[float] = None
    subtotal: Optional[float] = None

class CostFilters(BaseModel):
    project_id: Optional[str] = None
    proveedor: Optional[str] = None
    estado_costo: Optional[str] = None  # Cambiado a string para flexibilidad
    tipo_costo: Optional[str] = None  # Cambiado a string para flexibilidad
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    moneda: Optional[Moneda] = None

class CostResponse(BaseModel):
    headers: List[CostHeader]
    lines: List[CostLine]
    total_headers: int
    total_lines: int
    summary: Dict[str, Any]
    last_updated: Optional[datetime] = None

# === MODELOS PARA LOG ===
class LogEntry(BaseModel):
    fecha_hora: Optional[str] = None  # Cambiado a string para flexibilidad
    n_edp: Optional[int] = None
    proyecto: Optional[str] = None
    campo: Optional[str] = None
    antes: Optional[str] = None
    despues: Optional[str] = None
    usuario: Optional[str] = None

class LogFilters(BaseModel):
    n_edp: Optional[int] = None
    proyecto: Optional[str] = None
    usuario: Optional[str] = None
    campo: Optional[str] = None
    fecha_desde: Optional[str] = None  # Cambiado a string para flexibilidad
    fecha_hasta: Optional[str] = None  # Cambiado a string para flexibilidad

class LogResponse(BaseModel):
    data: List[LogEntry]
    total: int
    filtered: int
    last_updated: Optional[datetime] = None

# === MODELOS DE CAJA (Legacy - mantenemos compatibilidad) ===
class MovimientoCaja(BaseModel):
    """Movimiento individual de caja"""
    fecha: date
    descripcion: str
    categoria: str
    tipo: str  # "Ingreso" / "Egreso"
    monto: float
    proyecto: Optional[str] = None
    responsable: Optional[str] = None

class ResumenCaja(BaseModel):
    """Resumen financiero de caja"""
    total_ingresos: float
    total_egresos: float
    balance: float
    proyeccion_mensual: float

class CajaData(BaseModel):
    """Datos completos de caja"""
    movimientos: List[MovimientoCaja]
    resumen: ResumenCaja
    por_categoria: Dict[str, float]
    tendencia_mensual: Dict[str, float]

class CajaResponse(BaseModel):
    """Respuesta de consulta de caja"""
    data: CajaData
    total_movimientos: int
    filtered_movimientos: int
    cache_info: Dict[str, Any]
    last_updated: datetime

# === MODELOS DE DASHBOARD ===
class KPIDashboard(BaseModel):
    """KPIs principales del dashboard"""
    total_edps: int
    total_projects: int
    total_costs: int
    edps_aprobados: int
    edps_pendientes: int
    monto_total_aprobado: float
    monto_total_propuesto: float
    tasa_aprobacion: float
    proyectos_activos: int
    costos_pendientes: int
    costos_pagados: int

class DashboardData(BaseModel):
    """Datos completos del dashboard"""
    kpis: KPIDashboard
    edp_by_status: Dict[str, int]
    projects_by_status: Dict[str, int]
    costs_by_type: Dict[str, float]
    recent_activity: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    charts: Dict[str, Any]
    last_updated: datetime

# === MODELOS DE CACHE ===
class CacheStats(BaseModel):
    """Estadísticas del sistema de cache"""
    total_entries: int
    cache_keys: List[str]
    oldest_entry: Optional[float] = None
    newest_entry: Optional[float] = None
    hit_rate: Optional[float] = None
    timestamp: datetime

class CacheInvalidationRequest(BaseModel):
    """Request para invalidar cache"""
    pattern: str = Field(..., description="Patrón de keys a invalidar")
    reason: Optional[str] = Field(None, description="Razón de la invalidación")

# === MODELOS DE WEBHOOKS ===
class SheetsWebhookData(BaseModel):
    """Datos del webhook de Google Sheets"""
    sheet_id: str
    worksheet_name: str
    action: str  # 'update', 'insert', 'delete'
    range: Optional[str] = None
    values: Optional[List[List[str]]] = None
    timestamp: datetime

# === MODELOS DE RESPUESTA GENÉRICA ===
class APIResponse(BaseModel):
    """Respuesta genérica de la API"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime
    cache_info: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None

# === MODELOS DE CONFIGURACIÓN ===
class APIConfig(BaseModel):
    """Configuración de la API"""
    version: str
    environment: str
    cache_enabled: bool
    sheets_enabled: bool
    debug: bool
    max_page_size: int
    default_cache_ttl: int

class HealthCheck(BaseModel):
    api: str
    timestamp: str
    cache: Dict[str, Any]
    sheets: Dict[str, Any]
    version: str 