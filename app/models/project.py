# app/models/project.py
from datetime import datetime
from app import db

project_members = db.Table(
    'project_members',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role', db.String(50), default='member'),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)


class Project(db.Model):
    """Project management model"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='planning')
    budget = db.Column(db.Numeric(15, 2))
    actual_cost = db.Column(db.Numeric(15, 2), default=0)
    progress = db.Column(db.Float, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - use string references to avoid circular imports
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='project', lazy=True, cascade='all, delete-orphan')
    members = db.relationship(
        'User',
        secondary=project_members,
        backref=db.backref('member_projects', lazy='dynamic'),
        lazy='dynamic'
    )
    # Note: resources backref is created automatically by Resource model
    
    def to_dict(self):
        """Convert project to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'budget': float(self.budget) if self.budget else None,
            'actual_cost': float(self.actual_cost) if self.actual_cost else None,
            'progress': self.progress,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'members': [u.full_name for u in self.members] if self.members is not None else []
        }
