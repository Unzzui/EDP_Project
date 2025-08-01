"""
Base model classes for the EDP project.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class BaseModel:
    """Base model with common functionality."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary."""
        # Filter only fields that exist in the model
        valid_fields = {
            key: value for key, value in data.items()
            if key in cls.__annotations__
        }
        return cls(**valid_fields)


@dataclass
class EDP(BaseModel):
    """EDP (Estado de Pago) model."""
    
    id: Optional[int] = None
    n_edp: Optional[str] = None
    proyecto: Optional[str] = None
    cliente: Optional[str] = None
    gestor: Optional[str] = None
    jefe_proyecto: Optional[str] = None
    mes: Optional[str] = None
    fecha_emision: Optional[datetime] = None
    fecha_envio_cliente: Optional[datetime] = None
    monto_propuesto: Optional[float] = None
    monto_aprobado: Optional[float] = None
    fecha_estimada_pago: Optional[datetime] = None
    conformidad_enviada: Optional[bool] = None  # Booleano: True si está enviada, False si no
    n_conformidad: Optional[str] = None
    fecha_conformidad: Optional[datetime] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None
    estado_detallado: Optional[str] = None
    registrado_por: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    motivo_no_aprobado: Optional[str] = None
    tipo_falla: Optional[str] = None
    # Calculated fields
    validado: Optional[bool] = None
    critico: Optional[bool] = None
    dso_actual: Optional[float] = None
    dias_habiles: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create EDP instance from dictionary with date conversion."""
        # Fields that should be converted to datetime
        date_fields = [
            'fecha_emision', 'fecha_envio_cliente', 'fecha_estimada_pago',
            'fecha_conformidad', 'fecha_registro'
        ]
        
        # Fields that should be converted to boolean
        boolean_fields = ['conformidad_enviada', 'validado', 'critico']
        
        # Create a copy to avoid modifying original data
        processed_data = data.copy()
        
        # Convert date strings to datetime objects
        for field in date_fields:
            if field in processed_data and processed_data[field]:
                try:
                    # Handle different date formats
                    date_value = processed_data[field]
                    if isinstance(date_value, str):
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                            try:
                                processed_data[field] = datetime.strptime(date_value, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format works, try fromisoformat
                            try:
                                processed_data[field] = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                            except ValueError:
                                # If all fails, set to None
                                processed_data[field] = None
                    elif not isinstance(date_value, datetime):
                        processed_data[field] = None
                except Exception:
                    processed_data[field] = None
        
        # Convert boolean fields
        for field in boolean_fields:
            if field in processed_data and processed_data[field] is not None:
                try:
                    value = processed_data[field]
                    if isinstance(value, str):
                        # Handle string representations of booleans
                        if value.lower() in ['true', 'yes', 'si', 'sí', '1', 'on']:
                            processed_data[field] = True
                        elif value.lower() in ['false', 'no', '0', 'off', '']:
                            processed_data[field] = False
                        else:
                            processed_data[field] = None
                    elif isinstance(value, (int, float)):
                        # Handle numeric representations
                        processed_data[field] = bool(value)
                    elif not isinstance(value, bool):
                        processed_data[field] = None
                except Exception:
                    processed_data[field] = None
        
        # Filter only fields that exist in the model
        valid_fields = {
            key: value for key, value in processed_data.items()
            if key in cls.__annotations__
        }
        
        return cls(**valid_fields)
    
    @property
    def is_validated(self) -> bool:
        """Check if EDP is validated."""
        return self.estado and self.estado.lower() == 'validado'
    
    @property
    def is_critical(self) -> bool:
        """Check if EDP is critical (over 30 days waiting using DSO)."""
        return self.dso_actual is not None and self.dso_actual > 30
    
    @property
    def is_paid(self) -> bool:
        """Check if EDP is paid."""
        return self.estado and self.estado.lower() == 'pagado'


@dataclass
class Project(BaseModel):
    """Project model."""
    
    id: Optional[int] = None
    project_id: Optional[str] = None  # OT identifier
    proyecto: Optional[str] = None
    cliente: Optional[str] = None
    gestor: Optional[str] = None
    jefe_proyecto: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin_prevista: Optional[datetime] = None
    monto_contrato: Optional[float] = None
    moneda: Optional[str] = None
    estado_proyecto: Optional[str] = None
    
    @property
    def duration_days(self) -> Optional[int]:
        """Calculate project duration in days."""
        if self.fecha_inicio and self.fecha_fin_prevista:
            return (self.fecha_fin_prevista - self.fecha_inicio).days
        return None


@dataclass
class KPI(BaseModel):
    """KPI (Key Performance Indicator) model."""
    
    name: str
    value: Optional[float] = None
    target: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    period: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    @property
    def achievement_percentage(self) -> Optional[float]:
        """Calculate achievement percentage vs target."""
        if self.value is not None and self.target is not None and self.target != 0:
            return (self.value / self.target) * 100
        return None
    
    @property
    def status(self) -> str:
        """Get KPI status based on achievement."""
        achievement = self.achievement_percentage
        if achievement is None:
            return 'unknown'
        elif achievement >= 100:
            return 'excellent'
        elif achievement >= 80:
            return 'good'
        elif achievement >= 60:
            return 'warning'
        else:
            return 'critical'


@dataclass
class LogEntry(BaseModel):
    """Log entry model for tracking changes."""
    
    # id: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    n_edp: Optional[str] = None
    proyecto: Optional[str] = None
    campo: Optional[str] = None
    antes: Optional[str] = None
    despues: Optional[str] = None
    usuario: Optional[str] = None


@dataclass
class Cost(BaseModel):
    """Cost model for project expenses."""
    
    cost_id: Optional[int] = None
    project_id: Optional[str] = None  # OT identifier
    proveedor: Optional[str] = None
    factura: Optional[str] = None
    fecha_factura: Optional[datetime] = None
    fecha_recepcion: Optional[datetime] = None
    fecha_vencimiento: Optional[datetime] = None
    fecha_pago: Optional[datetime] = None
    importe_bruto: Optional[float] = None
    importe_neto: Optional[float] = None
    moneda: Optional[str] = None
    estado_costo: Optional[str] = None
    tipo_costo: Optional[str] = None  # opex, capex, etc.
    detalle_costo: Optional[str] = None
    responsable_registro: Optional[str] = None
    observaciones: Optional[str] = None
    url_respaldo: Optional[str] = None
    
    @property
    def is_paid(self) -> bool:
        """Check if cost is paid."""
        return self.estado_costo and self.estado_costo.lower() == 'pagado'
    
    @property
    def is_overdue(self) -> bool:
        """Check if cost is overdue."""
        if self.fecha_vencimiento and not self.is_paid:
            return datetime.now() > self.fecha_vencimiento
        return False
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date."""
        if self.fecha_vencimiento and not self.is_paid:
            return (self.fecha_vencimiento - datetime.now()).days
        return None
