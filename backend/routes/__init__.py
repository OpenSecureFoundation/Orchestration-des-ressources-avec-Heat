"""
Routes de l'application
"""

from .auth_routes import auth_bp
from .template_routes import template_bp
from .stack_routes import stack_bp
from .vm_routes import vm_bp
from .metrics_routes import metrics_bp
from .dashboard_routes import dashboard_bp

__all__ = [
    'auth_bp',
    'template_bp',
    'stack_bp',
    'vm_bp',
    'metrics_bp',
    'dashboard_bp'
]
