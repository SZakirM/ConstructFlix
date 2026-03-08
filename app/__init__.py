# app/__init__.py
# This file re-exports from init.py for backwards compatibility
# The actual application factory is in app/init.py

from app.init import create_app, db, login_manager, migrate, csrf, mail, limiter, socketio

__all__ = ['create_app', 'db', 'login_manager', 'migrate', 'csrf', 'mail', 'limiter', 'socketio']

