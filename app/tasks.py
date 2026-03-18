from celery import Celery
from flask import render_template
from celery.schedules import crontab
from app import create_app
from app.services.email_service import send_email
from app.services.notification_service import NotificationService
from app.models.project import Project
from app.models.task import Task
from datetime import datetime, timedelta
import os

celery = Celery(
    'constructflix',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)

@celery.task
def send_async_email(recipient, subject, template, **kwargs):
    """Send email asynchronously"""
    with create_app().app_context():
        send_email(
            subject=subject,
            recipients=recipient,
            text_body=render_template(f'email/{template}.txt', **kwargs),
            html_body=render_template(f'email/{template}.html', **kwargs)
        )

@celery.task
def check_upcoming_milestones():
    """Check for upcoming milestones and send notifications"""
    with create_app().app_context():
        from app.models.milestone import Milestone
        
        upcoming = Milestone.query.filter(
            Milestone.due_date <= datetime.now().date() + timedelta(days=7),
            Milestone.due_date >= datetime.now().date(),
            Milestone.status == 'pending'
        ).all()
        
        for milestone in upcoming:
            days_left = (milestone.due_date - datetime.now().date()).days
            NotificationService.create_notification(
                user_id=milestone.project.created_by,
                type='milestone_upcoming',
                title='Milestone Approaching',
                message=f"'{milestone.name}' is due in {days_left} days",
                data={'milestone_id': milestone.id, 'project_id': milestone.project_id}
            )

@celery.task
def check_overdue_tasks():
    """Check for overdue tasks and send notifications"""
    with create_app().app_context():
        overdue = Task.query.filter(
            Task.end_date < datetime.now().date(),
            Task.status != 'completed'
        ).all()
        
        for task in overdue:
            if task.assignee_id:
                NotificationService.create_notification(
                    user_id=task.assignee_id,
                    type='task_overdue',
                    title='Task Overdue',
                    message=f"Task '{task.name}' is overdue",
                    data={'task_id': task.id, 'project_id': task.project_id}
                )

@celery.task
def generate_daily_reports():
    """Generate daily reports for active projects"""
    with create_app().app_context():
        projects = Project.query.filter_by(status='active').all()
        
        for project in projects:
            # Generate progress report
            from app.services.report_service import ReportService
            report = ReportService.generate_daily_progress_report(project.id)
            
            # Send to project manager
            if project.creator:
                send_async_email.delay(
                    recipient=project.creator.email,
                    subject=f"Daily Report: {project.name}",
                    template='daily_report',
                    project=project,
                    report=report
                )

@celery.task
def cleanup_old_files():
    """Clean up temporary files older than 30 days"""
    with create_app().app_context():
        import os
        import shutil
        from datetime import datetime, timedelta
        
        upload_dir = 'app/static/uploads/temp'
        cutoff = datetime.now() - timedelta(days=30)
        
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            if os.path.getctime(filepath) < cutoff.timestamp():
                os.remove(filepath)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    # Check milestones every day at 8 AM
    sender.add_periodic_task(
        crontab(hour=8, minute=0),
        check_upcoming_milestones.s(),
        name='check-upcoming-milestones'
    )
    
    # Check overdue tasks every hour
    sender.add_periodic_task(
        3600.0,
        check_overdue_tasks.s(),
        name='check-overdue-tasks'
    )
    
    # Generate reports every day at 6 PM
    sender.add_periodic_task(
        crontab(hour=18, minute=0),
        generate_daily_reports.s(),
        name='generate-daily-reports'
    )
    
    # Clean up files every Sunday at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week='sun'),
        cleanup_old_files.s(),
        name='cleanup-old-files'
    )
