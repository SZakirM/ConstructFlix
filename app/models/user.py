from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(100))
    role = db.Column(db.String(50), default='team_member')
    
    # Account status - renamed to avoid conflict with UserMixin.is_active
    is_active_account = db.Column(db.Boolean, default=True, name='is_active')
    email_verified = db.Column(db.Boolean, default=False)
    
    # Security
    last_login = db.Column(db.DateTime)
    reset_token = db.Column(db.String(100), unique=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # Note: assigned_tasks backref is created by Task.assignee relationship
    created_projects = db.relationship('Project', foreign_keys='Project.created_by', backref='creator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_active(self):
        """Required by Flask-Login"""
        return self.is_active_account
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'email_verified': self.email_verified
        }
