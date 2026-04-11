from app import db, socketio
from app.models.notification import Notification
from flask import current_app
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from datetime import datetime

class NotificationService:
    
    @staticmethod
    def create_notification(user_id, type, title, message, data=None):
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data
        )
        db.session.add(notification)
        db.session.commit()
        
        # Emit to user's room
        socketio.emit('new_notification', notification.to_dict(), room=f"user_{user_id}")
        
        return notification
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        Notification.query.filter_by(user_id=user_id, is_read=False).update(
            {'is_read': True}
        )
        db.session.commit()
    
    @staticmethod
    def get_unread_count(user_id):
        """Get unread notification count"""
        return Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).count()
    
    @staticmethod
    def get_user_notifications(user_id, limit=50):
        """Get user notifications"""
        return Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc())\
            .limit(limit).all()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")
        # Send unread count
        unread_count = NotificationService.get_unread_count(current_user.id)
        emit('unread_count', {'count': unread_count})

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")

@socketio.on('mark_read')
def handle_mark_read(data):
    if current_user.is_authenticated:
        notification_id = data.get('notification_id')
        if notification_id:
            NotificationService.mark_as_read(notification_id, current_user.id)
            # Update unread count
            unread_count = NotificationService.get_unread_count(current_user.id)
            emit('unread_count', {'count': unread_count}, room=f"user_{current_user.id}")

@socketio.on('mark_all_read')
def handle_mark_all_read():
    if current_user.is_authenticated:
        NotificationService.mark_all_as_read(current_user.id)
        emit('unread_count', {'count': 0}, room=f"user_{current_user.id}")