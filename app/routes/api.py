# app/routes/api.py
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from app import db
from app.models.project import Project
from app.models.task import Task, Milestone
from app.models.resource import Resource
from app.models.financial import Budget, PurchaseOrder
from app.models.document import Document
from app.services.dashboard import DashboardService
from app.services.import_export import ImportExportService
from app.services.notification import NotificationService
from app.services.file_service import FileService
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ========== HEALTH CHECK ENDPOINT ==========

@api_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {}
    }
    
    # Check database
    try:
        db.session.execute(text('SELECT 1'))
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Check Redis (if available)
    try:
        from flask import current_app
        if hasattr(current_app, 'redis_client'):
            current_app.redis_client.ping()
            health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Check disk space
    try:
        import shutil
        disk_usage = shutil.disk_usage('/')
        if disk_usage.free / disk_usage.total < 0.1:  # Less than 10% free
            health_status['services']['disk'] = 'warning: low disk space'
            health_status['status'] = 'degraded'
        else:
            health_status['services']['disk'] = 'healthy'
    except Exception:
        pass
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

# ========== PROJECT ENDPOINTS ==========

@api_bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    """Get all projects for current user"""
    projects = Project.query.filter_by(created_by=current_user.id).all()
    return jsonify([p.to_dict() for p in projects])

@api_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create new project"""
    data = request.json
    
    project = Project(
        name=data.get('name'),
        description=data.get('description'),
        location=data.get('location'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
        budget=data.get('budget'),
        created_by=current_user.id
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify(project.to_dict()), 201

@api_bp.route('/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """Get single project"""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update project"""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.status = data.get('status', project.status)
    
    if 'start_date' in data:
        project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in data:
        project.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    if 'budget' in data:
        project.budget = data['budget']
    
    db.session.commit()
    
    return jsonify(project.to_dict())

# ========== TASK ENDPOINTS ==========

@api_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@login_required
def get_tasks(project_id):
    """Get all tasks for project"""
    tasks = Task.query.filter_by(project_id=project_id).all()
    return jsonify([t.to_dict() for t in tasks])

@api_bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@login_required
def create_task(project_id):
    """Create new task"""
    data = request.json
    
    task = Task(
        project_id=project_id,
        name=data.get('name'),
        description=data.get('description'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
        assignee_id=data.get('assignee_id'),
        priority=data.get('priority', 'medium'),
        cost_estimate=data.get('cost_estimate')
    )
    
    db.session.add(task)
    db.session.commit()
    
    # Add dependencies if provided
    if 'dependencies' in data:
        for dep_id in data['dependencies']:
            task.add_dependency(dep_id)
    
    # Notify assignee
    if task.assignee_id:
        NotificationService.task_assigned(task, task.assignee)
    
    return jsonify(task.to_dict()), 201

@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update task"""
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    task.name = data.get('name', task.name)
    task.description = data.get('description', task.description)
    
    if 'progress' in data:
        task.update_progress(data['progress'])
    
    if 'status' in data:
        task.status = data['status']
        if task.status == 'completed':
            task.actual_end_date = datetime.now().date()
            NotificationService.task_completed(task, current_user)
    
    db.session.commit()
    
    return jsonify(task.to_dict())

@api_bp.route('/tasks/<int:task_id>/dependencies', methods=['POST'])
@login_required
def add_dependency(task_id):
    """Add task dependency"""
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    try:
        task.add_dependency(
            depends_on_id=data['depends_on_id'],
            dependency_type=data.get('type', 'FS'),
            lag_days=data.get('lag_days', 0)
        )
        return jsonify({'message': 'Dependency added'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# ========== MILESTONE ENDPOINTS ==========

@api_bp.route('/projects/<int:project_id>/milestones', methods=['GET'])
@login_required
def get_milestones(project_id):
    """Get project milestones"""
    milestones = Milestone.query.filter_by(project_id=project_id).all()
    return jsonify([m.to_dict() for m in milestones])

@api_bp.route('/projects/<int:project_id>/milestones', methods=['POST'])
@login_required
def create_milestone(project_id):
    """Create milestone"""
    data = request.json
    
    milestone = Milestone(
        project_id=project_id,
        name=data.get('name'),
        description=data.get('description'),
        due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
        category=data.get('category')
    )
    
    db.session.add(milestone)
    db.session.commit()
    
    return jsonify(milestone.to_dict()), 201

@api_bp.route('/milestones/<int:milestone_id>/complete', methods=['POST'])
@login_required
def complete_milestone(milestone_id):
    """Mark milestone as complete"""
    milestone = Milestone.query.get_or_404(milestone_id)
    milestone.complete()
    
    return jsonify({'message': 'Milestone achieved'})

# ========== RESOURCE ENDPOINTS ==========

@api_bp.route('/projects/<int:project_id>/resources', methods=['GET'])
@login_required
def get_resources(project_id):
    """Get project resources"""
    resources = Resource.query.filter_by(project_id=project_id).all()
    return jsonify([r.to_dict() for r in resources])

@api_bp.route('/projects/<int:project_id>/resources', methods=['POST'])
@login_required
def create_resource(project_id):
    """Add resource"""
    data = request.json
    
    resource = Resource(
        project_id=project_id,
        name=data.get('name'),
        resource_type=data.get('type'),
        category=data.get('category'),
        total_quantity=data.get('total_quantity', 0),
        available_quantity=data.get('total_quantity', 0),
        unit=data.get('unit'),
        cost_per_unit=data.get('cost_per_unit'),
        supplier_id=data.get('supplier_id')
    )
    
    db.session.add(resource)
    db.session.commit()
    
    return jsonify(resource.to_dict()), 201

@api_bp.route('/resources/<int:resource_id>/allocate', methods=['POST'])
@login_required
def allocate_resource(resource_id):
    """Allocate resource to task"""
    resource = Resource.query.get_or_404(resource_id)
    data = request.json
    
    if resource.allocate(data.get('quantity')):
        return jsonify({'message': 'Resource allocated', 'resource': resource.to_dict()})
    return jsonify({'error': 'Insufficient quantity'}), 400

@api_bp.route('/resources/<int:resource_id>/release', methods=['POST'])
@login_required
def release_resource(resource_id):
    """Release resource from task"""
    resource = Resource.query.get_or_404(resource_id)
    data = request.json
    
    if resource.release(data.get('quantity')):
        return jsonify({'message': 'Resource released', 'resource': resource.to_dict()})
    return jsonify({'error': 'Invalid quantity'}), 400

# ========== DOCUMENT ENDPOINTS ==========

@api_bp.route('/projects/<int:project_id>/upload', methods=['POST'])
@login_required
def upload_project_file(project_id):
    """Upload file for project"""
    project = Project.query.get_or_404(project_id)
    
    # Check permission
    if project.created_by != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file
    file_info = FileService.save_upload(file, subfolder=str(project_id))
    
    if not file_info:
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Create document record
    document = Document(
        project_id=project_id,
        uploaded_by=current_user.id,
        filename=file_info['filename'],
        original_filename=file_info['original_filename'],
        file_path=file_info['path'],
        file_size=file_info['size'],
        file_hash=file_info['hash'],
        file_type=file_info['extension'],
        category=request.form.get('category', 'other'),
        description=request.form.get('description', ''),
        version=1
    )
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'document': document.to_dict()
    })

@api_bp.route('/projects/<int:project_id>/documents')
@login_required
def get_project_documents(project_id):
    """Get all documents for project"""
    project = Project.query.get_or_404(project_id)
    
    documents = Document.query.filter_by(
        project_id=project_id,
        is_archived=False
    ).order_by(Document.created_at.desc()).all()
    
    return jsonify({
        'documents': [doc.to_dict() for doc in documents]
    })

@api_bp.route('/documents/<int:document_id>/delete', methods=['POST'])
@login_required
def delete_document(document_id):
    """Delete document (archive it)"""
    document = Document.query.get_or_404(document_id)
    
    # Check permission
    if document.project.created_by != current_user.id and \
       document.uploaded_by != current_user.id and \
       current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
    
    # Archive instead of delete
    document.is_archived = True
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/documents/<int:document_id>/download')
@login_required
def download_document(document_id):
    """Download document"""
    document = Document.query.get_or_404(document_id)
    
    # Check permission
    if document.project.created_by != current_user.id and \
       not document.is_public and \
       current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
    
    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.original_filename
    )

