from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, Milestone
from datetime import datetime, date
from flask import Blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's projects
    projects = Project.query.filter_by(created_by=current_user.id).all()
    
    # Get tasks assigned to user
    tasks = Task.query.filter_by(assignee_id=current_user.id).all()
    
    # Get upcoming milestones
    upcoming_milestones = Milestone.query.join(Project).filter(
        Milestone.due_date >= date.today(),
        Milestone.status == 'pending'
    ).order_by(Milestone.due_date).limit(10).all()
    
    # Get portfolio stats
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='active').count()
    at_risk_projects = Project.query.filter(
        Project.status == 'active',
        Project.end_date < datetime.now().date()
    ).count()
    
    overdue_tasks = Task.query.filter(
        Task.status != 'completed',
        Task.end_date < date.today()
    ).count()
    
    stats = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'at_risk_projects': at_risk_projects,
        'overdue_tasks': overdue_tasks
    }
    
    return render_template('dashboard.html', 
                         projects=projects, 
                         tasks=tasks,
                         upcoming_milestones=upcoming_milestones,
                         stats=stats,
                         now=datetime.now())

@main_bp.route('/projects')
@login_required
def projects():
    projects = Project.query.filter_by(created_by=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('projects.html', projects=projects)

@main_bp.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        # Get form data with proper type handling
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        location = request.form.get('location', '')
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        budget_str = request.form.get('budget', '')
        
        # Parse dates with validation
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
        
        # Parse budget with validation
        budget = float(budget_str) if budget_str else None
        
        project = Project(
            name=name,
            description=description,
            location=location,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            status='planning',
            created_by=current_user.id
        )  # type: ignore[call-arg]
        
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('main.project_detail', project_id=project.id))
    
    return render_template('project_form.html', title='New Project')

@main_bp.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@main_bp.route('/project/<int:project_id>/schedule')
@login_required
def project_schedule(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.start_date).all()
    return render_template('schedule.html', project=project, tasks=tasks)

@main_bp.route('/project/<int:project_id>/reports')
@login_required
def project_reports(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id).all()
    milestones = Milestone.query.filter_by(project_id=project_id).all()
    
    # Calculate statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == 'completed'])
    in_progress_tasks = len([t for t in tasks if t.status == 'in_progress'])
    pending_tasks = len([t for t in tasks if t.status == 'pending'])
    
    total_milestones = len(milestones)
    achieved_milestones = len([m for m in milestones if m.status == 'achieved'])
    
    # Budget calculations
    total_budget = project.budget or 0
    spent_budget = sum(t.actual_cost or 0 for t in tasks)
    
    stats = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'pending_tasks': pending_tasks,
        'total_milestones': total_milestones,
        'achieved_milestones': achieved_milestones,
        'total_budget': total_budget,
        'spent_budget': spent_budget,
        'remaining_budget': total_budget - spent_budget
    }
    
    return render_template('reports.html', project=project, tasks=tasks, milestones=milestones, stats=stats)
