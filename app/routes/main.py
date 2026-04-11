from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, Milestone
from app.models.notification import Notification
from app.services.email_service import send_email
from datetime import datetime, date
from flask import Blueprint
from urllib.parse import quote_plus

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

def _can_assign_project_members():
    return current_user.role in ('admin', 'engineer')

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
    
    report_project = projects[0] if projects else None
    
    return render_template('dashboard.html', 
                         projects=projects, 
                         tasks=tasks,
                         upcoming_milestones=upcoming_milestones,
                         stats=stats,
                         report_project=report_project,
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
    users = User.query.order_by(User.first_name.asc()).all()
    invite_text = f"Join our project {project.name} on ConstructFlix: {request.url}"
    whatsapp_url = f"https://wa.me/?text={quote_plus(invite_text)}"
    can_assign = _can_assign_project_members()
    return render_template('project_detail.html', project=project, users=users, whatsapp_url=whatsapp_url, can_assign=can_assign)

@main_bp.route('/project/<int:project_id>/start', methods=['POST'])
@login_required
def start_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.created_by != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to start this project.', 'danger')
        return redirect(url_for('main.project_detail', project_id=project_id))

    if project.status != 'active':
        project.status = 'active'
        db.session.commit()
        flash('Project started successfully!', 'success')
    else:
        flash('Project is already active.', 'info')

    return redirect(url_for('main.project_detail', project_id=project_id))

@main_bp.route('/project/<int:project_id>/invite', methods=['POST'])
@login_required
def invite_project_member(project_id):
    project = Project.query.get_or_404(project_id)
    if not _can_assign_project_members():
        flash('Only admin and engineer users can assign team members.', 'danger')
        return redirect(url_for('main.project_detail', project_id=project_id))

    user_id = request.form.get('user_id')
    email = request.form.get('email', '').strip().lower()
    user = None

    if user_id:
        try:
            user = User.query.get(int(user_id))
        except (ValueError, TypeError):
            user = None

    if not user and email:
        user = User.query.filter_by(email=email).first()

    if not user and not email:
        flash('Please select a user or enter an email to invite.', 'warning')
        return redirect(url_for('main.project_detail', project_id=project_id))

    if user:
        if project.members.filter_by(id=user.id).first():
            flash('This user is already assigned to the project.', 'info')
        else:
            project.members.append(user)
            db.session.commit()
            Notification.send_to_user(
                user_id=user.id,
                notification_type='project_assignment',
                title=f'Assigned to project {project.name}',
                message=f'You have been added to project "{project.name}".',
                priority='high',
                data={'project_id': project.id}
            )
            send_email(
                subject=f'You have been added to {project.name}',
                recipients=user.email,
                text_body=f'Hello {user.full_name},\n\nYou have been assigned to the project "{project.name}" on ConstructFlix. Visit {request.url} to view the project.',
                html_body=f'<p>Hello {user.full_name},</p><p>You have been assigned to the project "{project.name}" on ConstructFlix.</p><p><a href="{request.url}">View project</a></p>'
            )
            flash('User assigned to the project and notified.', 'success')
    else:
        invite_link = f"https://{current_app.config.get('DOMAIN', 'localhost:5000')}/auth/register"
        send_email(
            subject=f'Invitation to join project {project.name}',
            recipients=email,
            text_body=f'Hello,\n\nYou have been invited to join the project "{project.name}" on ConstructFlix. Register here: {invite_link}',
            html_body=f'<p>Hello,</p><p>You have been invited to join the project "{project.name}" on ConstructFlix.</p><p><a href="{invite_link}">Register now</a></p>'
        )
        flash('Invitation email sent to the provided address.', 'success')

    return redirect(url_for('main.project_detail', project_id=project_id))

@main_bp.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.created_by != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to delete this project.', 'danger')
        return redirect(url_for('main.project_detail', project_id=project_id))

    db.session.delete(project)
    db.session.commit()
    flash('Project removed successfully.', 'success')
    return redirect(url_for('main.projects'))

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
