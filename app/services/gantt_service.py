from app import db
from app.models.task import Task
from app.models.project import Project
from datetime import datetime, timedelta
import json

class GanttService:
    
    @staticmethod
    def generate_gantt_data(project_id):
        """Generate Gantt chart data for project"""
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        gantt_data = []
        for task in tasks:
            # Calculate duration
            if task.start_date and task.end_date:
                duration = (task.end_date - task.start_date).days
            else:
                duration = 1
            
            # Set color based on status
            colors = {
                'completed': '#28a745',
                'in_progress': '#007bff',
                'delayed': '#dc3545',
                'not_started': '#6c757d'
            }
            
            # Get dependencies
            dependencies = []
            for dep in task.dependencies:
                dependencies.append(f"task_{dep.depends_on_id}")
            
            task_data = {
                'id': f"task_{task.id}",
                'name': task.name,
                'start': task.start_date.isoformat() if task.start_date else None,
                'end': task.end_date.isoformat() if task.end_date else None,
                'progress': task.progress,
                'dependencies': dependencies,
                'custom_class': f"gantt-task-{task.status}",
                'status': task.status,
                'assignee': task.assignee.full_name if task.assignee else 'Unassigned'
            }
            gantt_data.append(task_data)
        
        return gantt_data
    
    @staticmethod
    def calculate_critical_path(project_id):
        """Calculate critical path using topological sort"""
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        # Build dependency graph
        graph = {}
        task_durations = {}
        
        for task in tasks:
            task_durations[task.id] = (task.end_date - task.start_date).days if task.start_date and task.end_date else 1
            graph[task.id] = {
                'dependencies': [d.depends_on_id for d in task.dependencies],
                'duration': task_durations[task.id]
            }
        
        # Find earliest start times
        earliest_start = {task.id: 0 for task in tasks}
        earliest_finish = {task.id: 0 for task in tasks}
        
        # Topological sort
        visited = set()
        stack = []
        
        def topological_sort(task_id):
            visited.add(task_id)
            for dep_id in graph[task_id]['dependencies']:
                if dep_id not in visited:
                    topological_sort(dep_id)
            stack.append(task_id)
        
        for task in tasks:
            if task.id not in visited:
                topological_sort(task.id)
        
        # Forward pass
        for task_id in stack:
            max_es = 0
            for dep_id in graph[task_id]['dependencies']:
                max_es = max(max_es, earliest_finish[dep_id])
            earliest_start[task_id] = max_es
            earliest_finish[task_id] = max_es + graph[task_id]['duration']
        
        project_duration = max(earliest_finish.values())
        
        # Backward pass
        latest_start = {task.id: project_duration for task in tasks}
        latest_finish = {task.id: project_duration for task in tasks}
        
        for task_id in reversed(stack):
            min_ls = project_duration
            for next_id, next_task in graph.items():
                if task_id in next_task['dependencies']:
                    min_ls = min(min_ls, latest_start[next_id] - graph[task_id]['duration'])
            latest_finish[task_id] = min_ls
            latest_start[task_id] = min_ls - graph[task_id]['duration']
        
        # Find critical path (tasks with zero float)
        critical_path = []
        for task_id in stack:
            float_time = latest_start[task_id] - earliest_start[task_id]
            if float_time == 0:
                critical_path.append(task_id)
        
        return {
            'critical_path': critical_path,
            'project_duration': project_duration,
            'tasks': [
                {
                    'id': task_id,
                    'earliest_start': earliest_start[task_id],
                    'earliest_finish': earliest_finish[task_id],
                    'latest_start': latest_start[task_id],
                    'latest_finish': latest_finish[task_id],
                    'float': latest_start[task_id] - earliest_start[task_id]
                }
                for task_id in stack
            ]
        }
    
    @staticmethod
    def update_task_dates(task_id, new_start_date, new_end_date):
        """Update task dates and adjust dependent tasks"""
        task = Task.query.get(task_id)
        if not task:
            return False
        
        old_start = task.start_date
        old_end = task.end_date
        delta = (new_start_date - old_start).days
        
        task.start_date = new_start_date
        task.end_date = new_end_date
        db.session.commit()
        
        # Update dependent tasks
        for dep in task.dependent_tasks:
            dependent_task = dep.task
            if dep.dependency_type == 'finish_to_start':
                if dependent_task.start_date < new_end_date + timedelta(days=dep.lag_days):
                    new_dep_start = new_end_date + timedelta(days=dep.lag_days)
                    new_dep_end = dependent_task.end_date + (new_dep_start - dependent_task.start_date)
                    GanttService.update_task_dates(dependent_task.id, new_dep_start, new_dep_end)
        
        return True