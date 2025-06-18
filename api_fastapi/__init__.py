"""
Pagora FastAPI Module

API centralizada para gestión de EDPs y datos financieros
que se integra con el sistema Flask existente.
"""

__version__ = "1.0.0"
__author__ = "Pagora Team"

from .main import app
from .models import *
from .services import APIService

__all__ = [
    "app",
    "APIService",
    "EDP",
    "EDPFilters", 
    "EDPResponse",
    "CajaData",
    "CajaResponse",
    "DashboardData"
] 