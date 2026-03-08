# app/routes/tasks.py - Complete task management
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from datetime import datetime
from app.models.task import Task, TaskDependency
from app.init import socketio

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

@tasks_bp.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
@login_required
def create_task(project_id):
    """Create task with full scheduling capabilities"""
    data = request.json
    
    # Create task with all scheduling attributes
    task = Task(
        project_id=project_id,
        name=data['name'],
        description=data.get('description', ''),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
        assignee_id=data.get('assignee_id'),
        priority=data.get('priority', 'medium'),
        status='not_started'
    )
    
    db.session.add(task)
    db.session.flush()  # Get task ID
    
    # Add dependencies (finish-to-start, start-to-start, etc.)
    if 'dependencies' in data:
        for dep in data['dependencies']:
            dependency = TaskDependency(
                task_id=task.id,
                depends_on_id=dep['task_id'],
                dependency_type=dep.get('type', 'finish_to_start'),
                lag_days=dep.get('lag_days', 0)
            )
            db.session.add(dependency)
    
    db.session.commit()
    
    # Trigger real-time update
    socketio.emit('task_created', task.to_dict(), room=f"project_{project_id}")
    
    return jsonify(task.to_dict()), 201

