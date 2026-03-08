# app/services/dashboard.py
from app.models.project import Project
from app.models.task import Task, Milestone
from app.models.financial import Budget
from datetime import date, timedelta
from sqlalchemy import func

class DashboardService:
    """Real-time dashboard and reporting service"""
    
    @staticmethod
    def get_portfolio_dashboard(user_id):
        """Get portfolio-level dashboard data"""
        # Get all projects for user
        projects = Project.query.filter_by(created_by=user_id).all()
        
        # Summary statistics
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if p.status == 'active')
        completed_projects = sum(1 for p in projects if p.status == 'completed')
        
        # Financial summary
        total_budget = sum(float(p.budget or 0) for p in projects)
        total_actual = sum(float(p.actual_cost or 0) for p in projects)
        
        # Task statistics
        total_tasks = 0
        completed_tasks = 0
        overdue_tasks = 0
        
        for project in projects:
            tasks = project.tasks.all()
            total_tasks += len(tasks)
            completed_tasks += sum(1 for t in tasks if t.status == 'completed')
            overdue_tasks += sum(1 for t in tasks if t.is_overdue)
        
        # At-risk projects (behind schedule)
        at_risk = []
        for project in projects:
            if project.status == 'active':
                expected_progress = DashboardService._calculate_expected_progress(project)
                if project.progress < expected_progress - 10:  # 10% behind
                    at_risk.append({
                        'id': project.id,
                        'name': project.name,
                        'progress': project.progress,
                        'expected': expected_progress,
                        'delay': expected_progress - project.progress
                    })
        
        # Upcoming milestones (next 30 days)
        upcoming_milestones = Milestone.query.join(Project).filter(
            Milestone.due_date.between(date.today(), date.today() + timedelta(days=30)),
            Milestone.status == 'pending',
            Project.created_by == user_id
        ).order_by(Milestone.due_date).all()
        
        # Recent activity
        recent_tasks = Task.query.join(Project).filter(
            Project.created_by == user_id
        ).order_by(Task.updated_at.desc()).limit(10).all()
        
        return {
            'summary': {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'total_budget': total_budget,
                'total_actual': total_actual,
                'variance': total_budget - total_actual,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'overdue_tasks': overdue_tasks
            },
            'at_risk_projects': at_risk,
            'upcoming_milestones': [m.to_dict() for m in upcoming_milestones],
            'recent_activity': [{
                'id': t.id,
                'name': t.name,
                'project': t.project.name,
                'status': t.status,
                'updated_at': t.updated_at.isoformat()
            } for t in recent_tasks]
        }
    
    @staticmethod
    def get_project_dashboard(project_id):
        """Get detailed project dashboard"""
        project = Project.query.get_or_404(project_id)
        
        # Update project progress
        project.calculate_progress()
        
        # Task statistics
        tasks = project.tasks.all()
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == 'completed')
        in_progress_tasks = sum(1 for t in tasks if t.status == 'in_progress')
        not_started_tasks = sum(1 for t in tasks if t.status == 'not_started')
        delayed_tasks = sum(1 for t in tasks if t.is_overdue)
        
        # Task priority breakdown
        critical_tasks = sum(1 for t in tasks if t.priority == 'critical')
        high_tasks = sum(1 for t in tasks if t.priority == 'high')
        
        # Milestones
        milestones = project.milestones.all()
        completed_milestones = sum(1 for m in milestones if m.status == 'achieved')
        
        # Resource utilization
        resources = project.resources_list.all()
        resource_utilization = []
        for resource in resources:
            resource_utilization.append({
                'name': resource.name,
                'type': resource.resource_type,
                'utilization': resource.utilization_rate,
                'available': resource.available_quantity,
                'total': resource.total_quantity
            })
        
        # Financial data
        budgets = project.budgets.all()
        total_budget = sum(float(b.revised_budget or b.original_budget) for b in budgets)
        total_actual = sum(float(b.actual_cost) for b in budgets)
        
        # Earned value metrics
        evm_metrics = {}
        for budget in budgets:
            metrics = budget.calculate_earned_value()
            if metrics:
                evm_metrics = metrics
        
        # Timeline data for charts
        timeline_data = DashboardService._get_timeline_data(project_id)
        
        return {
            'project': project.to_dict(),
            'task_stats': {
                'total': total_tasks,
                'completed': completed_tasks,
                'in_progress': in_progress_tasks,
                'not_started': not_started_tasks,
                'delayed': delayed_tasks,
                'completion_percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'critical_tasks': critical_tasks,
                'high_priority': high_tasks
            },
            'milestone_stats': {
                'total': len(milestones),
                'completed': completed_milestones,
                'pending': len(milestones) - completed_milestones,
                'completion_rate': (completed_milestones / len(milestones) * 100) if milestones else 0
            },
            'financial': {
                'total_budget': total_budget,
                'total_actual': total_actual,
                'variance': total_budget - total_actual,
                'variance_percentage': ((total_budget - total_actual) / total_budget * 100) if total_budget > 0 else 0,
                'evm': evm_metrics
            },
            'resources': resource_utilization,
            'timeline': timeline_data,
            'health': DashboardService._assess_project_health(project, tasks, budgets)
        }
    
    @staticmethod
    def _calculate_expected_progress(project):
        """Calculate expected progress based on time elapsed"""
        total_duration = (project.end_date - project.start_date).days
        elapsed = (date.today() - project.start_date).days
        
        if total_duration > 0 and elapsed > 0:
            return (elapsed / total_duration) * 100
        return 0
    
    @staticmethod
    def _get_timeline_data(project_id):
        """Get timeline data for charts"""
        tasks = Task.query.filter_by(project_id=project_id).order_by(Task.start_date).all()
        
        # Group by week
        weekly_data = {}
        
        for task in tasks:
            week_num = task.start_date.isocalendar()[1]
            year = task.start_date.year
            week_key = f"{year}-W{week_num}"
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    'week': week_key,
                    'planned': 0,
                    'actual': 0,
                    'tasks': 0
                }
            
            weekly_data[week_key]['planned'] += 1
            weekly_data[week_key]['actual'] += 1 if task.status == 'completed' else 0
            weekly_data[week_key]['tasks'] += 1
        
        return list(weekly_data.values())
    
    @staticmethod
    def _assess_project_health(project, tasks, budgets):
        """Assess overall project health"""
        score = 100
        
        # Schedule health
        expected_progress = DashboardService._calculate_expected_progress(project)
        if project.progress < expected_progress:
            delay_factor = (expected_progress - project.progress) / expected_progress
            score -= delay_factor * 30
        
        # Task health
        overdue_tasks = sum(1 for t in tasks if t.is_overdue)
        if tasks:
            overdue_ratio = overdue_tasks / len(tasks)
            score -= overdue_ratio * 20
        
        # Budget health
        total_budget = sum(float(b.revised_budget or b.original_budget) for b in budgets)
        total_actual = sum(float(b.actual_cost) for b in budgets)
        
        if total_budget > 0:
            budget_ratio = total_actual / total_budget
            if budget_ratio > 1:
                score -= (budget_ratio - 1) * 30
        
        # Determine status
        if score >= 80:
            status = 'healthy'
        elif score >= 50:
            status = 'at_risk'
        else:
            status = 'critical'
        
        return {
            'score': max(0, min(100, score)),
            'status': status,
            'issues': {
                'schedule_delay': project.progress < expected_progress,
                'overdue_tasks': overdue_tasks > 0,
                'budget_overrun': total_actual > total_budget if total_budget > 0 else False
            }
        }