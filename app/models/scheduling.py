# app/models/scheduling.py
# Scheduling-related functions and utilities
# Models are defined in separate files: project.py, task.py
from datetime import datetime, date, timedelta
from app import db


def calculate_critical_path(project_id):
    """Calculate the critical path for a project"""
    from app.models.task import Task, TaskDependency
    
    # Get all tasks for the project
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    if not tasks:
        return {'critical_path': [], 'project_duration': 0}
    
    # Build dependency graph
    task_dict = {task.id: task for task in tasks}
    
    # Calculate early start/finish times
    def calculate_early_times(task_id, visited=None):
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return 0, 0
        
        visited.add(task_id)
        task = task_dict.get(task_id)
        
        if not task:
            return 0, 0
        
        # Get all dependencies (tasks that must complete before this one)
        deps = TaskDependency.query.filter_by(depends_on_id=task_id).all()
        
        if not deps:
            early_start = 0
        else:
            max_finish = 0
            for dep in deps:
                prev_early_start, prev_early_finish = calculate_early_times(dep.task_id, visited.copy())
                max_finish = max(max_finish, prev_early_finish)
            early_start = max_finish
        
        duration = (task.end_date - task.start_date).days if task.start_date and task.end_date else 0
        early_finish = early_start + duration
        
        return early_start, early_finish
    
    # Calculate late start/finish times
    def calculate_late_times(task_id, project_end, visited=None):
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return project_end, project_end
        
        visited.add(task_id)
        task = task_dict.get(task_id)
        
        if not task:
            return project_end, project_end
        
        # Get all dependent tasks (tasks that depend on this one)
        deps = TaskDependency.query.filter_by(task_id=task_id).all()
        
        if not deps:
            late_finish = project_end
        else:
            min_start = project_end
            for dep in deps:
                prev_late_start, prev_late_finish = calculate_late_times(dep.depends_on_id, project_end, visited.copy())
                min_start = min(min_start, prev_late_start)
            late_finish = min_start
        
        duration = (task.end_date - task.start_date).days if task.start_date and task.end_date else 0
        late_start = late_finish - duration
        
        return late_start, late_finish
    
    # Find project end date
    project_end = max([task.end_date for task in tasks if task.end_date]) if tasks else date.today()
    project_duration = (project_end - min([task.start_date for task in tasks if task.start_date])).days if tasks else 0
    
    # Find critical path (tasks with zero float)
    critical_path = []
    for task in tasks:
        early_start, early_finish = calculate_early_times(task.id)
        late_start, late_finish = calculate_late_times(task.id, project_duration)
        
        float_time = late_start - early_start
        if float_time == 0:
            critical_path.append(task.id)
    
    return {
        'critical_path': critical_path,
        'project_duration': project_duration,
        'project_end': project_end.isoformat()
    }


def schedule_tasks_auto(project_id):
    """Automatically schedule tasks based on dependencies"""
    from app.models.task import Task, TaskDependency
    
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.start_date).all()
    
    for task in tasks:
        # Check dependencies
        deps = TaskDependency.query.filter_by(depends_on_id=task.id).all()
        
        if deps:
            max_end_date = date.today()
            for dep in deps:
                prev_task = Task.query.get(dep.task_id)
                if prev_task and prev_task.end_date:
                    if prev_task.end_date > max_end_date:
                        max_end_date = prev_task.end_date
            
            # Set new start date after all dependencies are complete
            task.start_date = max_end_date + timedelta(days=1)
            task.end_date = task.start_date + timedelta(days=dep.lag_days) if hasattr(dep, 'lag_days') else task.start_date + timedelta(days=7)
    
    db.session.commit()
    return tasks


def get_schedule_analysis(project_id):
    """Get comprehensive schedule analysis for a project"""
    from app.models.task import Task
    
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    if not tasks:
        return {
            'total_tasks': 0,
            'completed': 0,
            'in_progress': 0,
            'not_started': 0,
            'overdue': 0,
            'on_track': 0
        }
    
    completed = sum(1 for t in tasks if t.status == 'completed')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    not_started = sum(1 for t in tasks if t.status == 'not_started')
    overdue = sum(1 for t in tasks if t.is_overdue)
    on_track = completed + in_progress - overdue
    
    # Calculate float for each task
    task_floats = []
    for task in tasks:
        if task.start_date and task.end_date:
            duration = (task.end_date - task.start_date).days
            # Simplified float calculation
            task_floats.append({
                'task_id': task.id,
                'task_name': task.name,
                'duration': duration,
                'days_remaining': task.days_remaining if hasattr(task, 'days_remaining') else 0
            })
    
    return {
        'total_tasks': len(tasks),
        'completed': completed,
        'in_progress': in_progress,
        'not_started': not_started,
        'overdue': overdue,
        'on_track': on_track,
        'progress_percentage': (completed / len(tasks) * 100) if tasks else 0,
        'task_floats': task_floats
    }

