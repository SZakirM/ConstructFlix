# app/routes/__init__.py
from .main import main_bp
from .auth import auth_bp
from .admin import admin_bp
from .api import api_bp
from .tasks import tasks_bp
from .gantt import gantt_bp

__all__ = ['main_bp', 'auth_bp', 'admin_bp', 'api_bp', 'tasks_bp', 'gantt_bp']

