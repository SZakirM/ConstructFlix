from app import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    file_hash = db.Column(db.String(64))  # SHA-256
    file_type = db.Column(db.String(50))  # pdf, image, doc, etc.
    
    category = db.Column(db.String(50))  # drawing, contract, permit, photo, report
    description = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)
    
    is_public = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='documents')
    uploader = db.relationship('User', backref='uploaded_documents')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'category': self.category,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'uploaded_by': self.uploader.full_name if self.uploader else None
        }
    
    @property
    def file_url(self):
        return f"/static/uploads/{self.project_id}/{self.filename}"
    
    @property
    def size_formatted(self):
        """Return human-readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"