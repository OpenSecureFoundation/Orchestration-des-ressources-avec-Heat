from .main_routes import main_bp
from .stack_routes import stack_bp
from .vm_routes import vm_bp
from .metrics_routes import metrics_bp
from .template_routes import template_bp

__all__ = ["main_bp", "stack_bp", "vm_bp", "metrics_bp", "template_bp"]
