from app import db
from datetime import datetime

class Notification(db.Model):
    """Real-time notification system"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification details
    type = db.Column(db.String(50))  # task_assigned, project_update, deadline_approaching, etc.
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    
    # Priority levels: low, medium, high, urgent
    priority = db.Column(db.String(20), default='medium')
    
    # Data payload (JSON for additional context)
    data = db.Column(db.JSON)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Delivery methods
    delivered_email = db.Column(db.Boolean, default=False)
    delivered_sms = db.Column(db.Boolean, default=False)
    delivered_push = db.Column(db.Boolean, default=False)
    delivered_in_app = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    @classmethod
    def send_to_user(cls, user_id, notification_type, title, message, 
                     priority='medium', data=None, delivery_methods=None):
        """Send notification to a specific user"""
        if delivery_methods is None:
            delivery_methods = {'email': False, 'sms': False, 'push': False, 'in_app': True}
        
        notification = cls(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data=data,
            delivered_email=delivery_methods.get('email', False),
            delivered_sms=delivery_methods.get('sms', False),
            delivered_push=delivery_methods.get('push', False),
            delivered_in_app=delivery_methods.get('in_app', True)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Trigger real-time WebSocket notification
        from app.init import socketio
        socketio.emit('notification', {
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'priority': notification.priority,
            'data': notification.data,
            'created_at': notification.created_at.isoformat()
        }, room=f"user_{user_id}")
        
        return notification
    
    @classmethod
    def send_to_project(cls, project_id, notification_type, title, message, 
                        exclude_user_id=None, **kwargs):
        """Send notification to all project members"""
        from app.models.project import Project
        
        project = Project.query.get(project_id)
        if not project:
            return
        
        # Get all users associated with project
        user_ids = set()
        
        # Project creator
        if project.created_by:
            user_ids.add(project.created_by)
        
        # Task assignees
        for task in project.tasks:
            if task.assignee_id:
                user_ids.add(task.assignee_id)
        
        # Remove excluded user
        if exclude_user_id and exclude_user_id in user_ids:
            user_ids.remove(exclude_user_id)
        
        # Send to each user
        notifications = []
        for user_id in user_ids:
            notification = cls.send_to_user(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                **kwargs
            )
            notifications.append(notification)
        
        return notifications
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'time_ago': self.get_time_ago()
        }
    
    def get_time_ago(self):
        diff = datetime.utcnow() - self.created_at
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"


class Comment(db.Model):
    """Comments and discussions on tasks/projects"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Polymorphic association (can be on project, task, milestone, etc.)
    target_type = db.Column(db.String(50))  # project, task, milestone, document
    target_id = db.Column(db.Integer, nullable=False)
    
    # Comment content
    content = db.Column(db.Text, nullable=False)
    
    # Rich text formatting
    formatted_content = db.Column(db.Text)  # HTML version
    
    # Mentions (users mentioned in comment)
    mentions = db.Column(db.JSON)  # List of user IDs
    
    # Attachments
    attachments = db.Column(db.JSON)
    
    # Threading (for replies)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    thread_level = db.Column(db.Integer, default=0)
    
    # Metadata
    is_edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def save_with_mentions(self):
        """Save comment and notify mentioned users"""
        db.session.add(self)
        db.session.flush()
        
        # Notify mentioned users
        if self.mentions:
            for user_id in self.mentions:
                Notification.send_to_user(
                    user_id=user_id,
                    notification_type='mention',
                    title=f"{self.user.full_name} mentioned you",
                    message=self.content[:100] + "...",
                    data={
                        'comment_id': self.id,
                        'target_type': self.target_type,
                        'target_id': self.target_id
                    }
                )
        
        db.session.commit()


class Message(db.Model):
    """Direct messaging between users"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Message content
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_archived_sender = db.Column(db.Boolean, default=False)
    is_archived_recipient = db.Column(db.Boolean, default=False)
    
    # Threading
    conversation_id = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

