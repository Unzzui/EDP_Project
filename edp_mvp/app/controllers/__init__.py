"""
Controllers package - Refactored controllers using layered architecture.

This package contains the new controllers that replace the monolithic
dashboard/controller.py and dashboard/manager.py files.

Controllers:
- controller_controller.py: Replaces dashboard/controller.py (kanban, analytics, etc.)
- manager_controller.py: Replaces dashboard/manager.py (executive dashboard)
- edp_controller.py: EDP-specific operations

All controllers use the service layer for business logic and follow
the layered architecture pattern.
"""

# Version information
__version__ = '1.0.0'
__author__ = 'EDP Restructuring Team'

# Import controllers for easier access
from .controller_controller import controller_controller_bp
from .manager_controller import manager_controller_bp
from .edp_controller import edp_controller_bp
from .kanban_controller import kanban_bp
from .kanban_controller_optimized import kanban_opt_bp

__all__ = [
    'controller_controller_bp',
    'manager_controller_bp', 
    'edp_controller_bp',
    'kanban_bp',
    'kanban_opt_bp'
]
