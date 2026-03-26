# app/routes/tasks.py - Complete task management
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from datetime import datetime
from app.models.task import Task, TaskDependency
from app.init import socketio

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

# Removed duplicate create_task endpoint - use /api/projects/<id>/tasks instead
# Keeping blueprint for potential future task-specific routes

