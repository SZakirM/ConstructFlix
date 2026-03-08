from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    unverified_users = User.query.filter_by(email_verified=False).count()
    
    # User growth (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    
    # Projects stats
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='active').count()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'unverified_users': unverified_users,
        'new_users': new_users,
        'total_projects': total_projects,
        'active_projects': active_projects
    }
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/user_detail.html', user=user)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate yourself'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.email} has been {action}.', 'success')
    
    return redirect(url_for('admin.user_detail', user_id=user.id))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    email = user.email
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {email} has been deleted.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/projects')
@login_required
@admin_required
def projects():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    projects = Project.query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/system-logs')
@login_required
@admin_required
def system_logs():
    log_file = 'logs/app.log'
    logs = []
    
    try:
        with open(log_file, 'r') as f:
            # Read last 100 lines
            logs = f.readlines()[-100:]
    except FileNotFoundError:
        logs = ['Log file not found']
    
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/system-stats')
@login_required
@admin_required
def system_stats():
    import psutil
    import os
    
    # System stats
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database stats
    db_size = db.session.execute("SELECT pg_database_size('construction_db')").scalar()
    
    stats = {
        'cpu': cpu_percent,
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.used / disk.total * 100
        },
        'database': {
            'size': db_size
        }
    }
    
    return render_template('admin/system_stats.html', stats=stats)