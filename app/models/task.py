# app/models/task.py
from datetime import datetime, date
from app import db

class Task(db.Model):
    """Complete task management with all scheduling features"""
    __tablename__ = 'tasks'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    wbs_code = db.Column(db.String(50))  # Work Breakdown Structure code
    
    # Core task information
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Dates and scheduling
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    actual_start_date = db.Column(db.Date)
    actual_end_date = db.Column(db.Date)
    constraint_date = db.Column(db.Date)  # Must start/finish by this date
    constraint_type = db.Column(db.String(20))  # must_start_on, must_finish_on, etc.
    
    # Progress tracking
    progress = db.Column(db.Float, default=0)  # 0-100
    status = db.Column(db.String(50), default='not_started')  # not_started, in_progress, completed, delayed, blocked
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Duration calculations
    planned_duration = db.Column(db.Integer)  # in days
    actual_duration = db.Column(db.Integer)
    remaining_duration = db.Column(db.Integer)
    
    # Percent complete types
    physical_percent_complete = db.Column(db.Float, default=0)
    duration_percent_complete = db.Column(db.Float, default=0)
    units_percent_complete = db.Column(db.Float, default=0)
    
    # Cost tracking
    cost_estimate = db.Column(db.Numeric(15, 2))
    actual_cost = db.Column(db.Numeric(15, 2), default=0)
    remaining_cost = db.Column(db.Numeric(15, 2))
    
    # Resource tracking
    labor_hours_planned = db.Column(db.Float)
    labor_hours_actual = db.Column(db.Float)
    equipment_hours_planned = db.Column(db.Float)
    equipment_hours_actual = db.Column(db.Float)
    
    # Notes and attachments
    notes = db.Column(db.Text)
    attachments = db.Column(db.JSON)  # List of file paths
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    dependencies_from = db.relationship('TaskDependency', foreign_keys='TaskDependency.task_id', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    dependencies_to = db.relationship('TaskDependency', foreign_keys='TaskDependency.depends_on_id', backref='depended_on', lazy='dynamic')
    assignments = db.relationship('TaskAssignment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    # User relationship for assignee
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='assigned_tasks')
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.status != 'completed' and self.end_date:
            return self.end_date < date.today()
        return False
    
    @property
    def days_late(self):
        """Calculate days late"""
        if self.is_overdue:
            return (date.today() - self.end_date).days
        return 0
    
    @property
    def days_remaining(self):
        """Calculate days remaining"""
        if self.status != 'completed' and self.end_date:
            return (self.end_date - date.today()).days
        return 0
    
    def update_progress(self, new_progress):
        """Update task progress and recalculate derived fields"""
        self.progress = new_progress
        
        # Update status based on progress
        if new_progress == 100:
            self.status = 'completed'
            self.actual_end_date = date.today()
        elif new_progress > 0:
            self.status = 'in_progress'
            if not self.actual_start_date:
                self.actual_start_date = date.today()
        
        # Calculate remaining duration
        if self.planned_duration:
            self.remaining_duration = self.planned_duration * (100 - new_progress) / 100
        
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'progress': self.progress,
            'status': self.status,
            'priority': self.priority,
            'is_overdue': self.is_overdue,
            'days_late': self.days_late,
            'assignee': self.assignee.full_name if self.assignee else None,
            'dependencies': [dep.depends_on_id for dep in self.dependencies_from],
            'subtasks': [subtask.id for subtask in self.subtasks]
        }


class TaskDependency(db.Model):
    """Task dependency management with all relationship types"""
    __tablename__ = 'task_dependencies'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    depends_on_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    # Dependency types:
    # FS - Finish to Start (most common)
    # SS - Start to Start
    # FF - Finish to Finish
    # SF - Start to Finish
    dependency_type = db.Column(db.String(2), default='FS')
    
    # Lag time in days (positive) or lead time (negative)
    lag_days = db.Column(db.Integer, default=0)
    
    # Is this dependency critical?
    is_critical = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def validate_dependency(self):
        """Validate no circular dependencies"""
        # Implementation of cycle detection
        pass


class TaskAssignment(db.Model):
    """Resource assignment to tasks"""
    __tablename__ = 'task_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=True)
    
    # Assignment details
    role = db.Column(db.String(100))
    units = db.Column(db.Float, default=1.0)  # Full time = 1.0, half time = 0.5
    
    # Hours tracking
    hours_planned = db.Column(db.Float)
    hours_actual = db.Column(db.Float, default=0)
    
    # Cost tracking
    cost_rate = db.Column(db.Numeric(10, 2))  # $/hour
    total_cost = db.Column(db.Numeric(15, 2))
    
    # Dates
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='task_assignments')
    resource = db.relationship('Resource', backref='task_assignments')


class Milestone(db.Model):
    """Project milestones for key dates"""
    __tablename__ = 'milestones'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Date
    due_date = db.Column(db.Date, nullable=False)
    completed_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, achieved, missed
    
    # Color/category for visual representation
    category = db.Column(db.String(50))  # contract, funding, permit, completion
    color = db.Column(db.String(20), default='#ffc107')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_completed(self):
        return self.completed_date is not None
    
    @property
    def days_remaining(self):
        if not self.is_completed and self.due_date:
            return (self.due_date - date.today()).days
        return 0
    
    def complete(self):
        """Mark milestone as achieved"""
        self.status = 'achieved'
        self.completed_date = date.today()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'due_date': self.due_date.isoformat(),
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'status': self.status,
            'days_remaining': self.days_remaining,
            'category': self.category
        }
