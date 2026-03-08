# app/services/notification.py
from app import db, socketio
from app.models.notification import Notification
from flask import render_template
from threading import Thread

class NotificationService:
    """Complete notification and collaboration service"""
    
    @staticmethod
    def send_to_user(user_id, notification_type, title, message, 
                     priority='medium', data=None, delivery_methods=None):
        """Send notification to specific user"""
        if delivery_methods is None:
            delivery_methods = {'email': False, 'sms': False, 'push': False, 'in_app': True}
        
        notification = Notification(
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
        
        # Real-time WebSocket notification
        socketio.emit('notification', {
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'priority': notification.priority,
            'data': notification.data,
            'created_at': notification.created_at.isoformat()
        }, room=f"user_{user_id}")
        
        # Async email delivery
        if delivery_methods.get('email'):
            NotificationService._send_email.delay(
                to_email=notification.user.email,
                subject=title,
                template='notification_email',
                context={'notification': notification}
            )
        
        return notification
    
    @staticmethod
    def send_to_project(project_id, notification_type, title, message, 
                       exclude_user_id=None, **kwargs):
        """Send notification to all project members"""
        from app.models.project import Project
        
        project = Project.query.get(project_id)
        if not project:
            return []
        
        # Collect all project users
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
            notification = NotificationService.send_to_user(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                **kwargs
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def task_assigned(task, assignee):
        """Notify when task is assigned"""
        return NotificationService.send_to_user(
            user_id=assignee.id,
            notification_type='task_assigned',
            title='New Task Assigned',
            message=f'You have been assigned to task: {task.name}',
            priority='high',
            data={
                'task_id': task.id,
                'project_id': task.project_id,
                'project_name': task.project.name
            },
            delivery_methods={'email': True, 'in_app': True, 'push': True}
        )
    
    @staticmethod
    def task_completed(task, completed_by):
        """Notify when task is completed"""
        return NotificationService.send_to_project(
            project_id=task.project_id,
            notification_type='task_completed',
            title='Task Completed',
            message=f'Task "{task.name}" completed by {completed_by.full_name}',
            priority='medium',
            data={
                'task_id': task.id,
                'project_id': task.project_id,
                'completed_by': completed_by.full_name
            }
        )
    
    @staticmethod
    def task_overdue(task):
        """Notify when task becomes overdue"""
        return NotificationService.send_to_user(
            user_id=task.assignee_id,
            notification_type='task_overdue',
            title='Task Overdue',
            message=f'Task "{task.name}" is {task.days_late} days overdue',
            priority='urgent',
            data={
                'task_id': task.id,
                'project_id': task.project_id,
                'days_late': task.days_late
            },
            delivery_methods={'email': True, 'sms': True, 'in_app': True, 'push': True}
        )
    
    @staticmethod
    def milestone_achieved(milestone):
        """Notify when milestone is achieved"""
        return NotificationService.send_to_project
# app/services/notification.py
from app import db, socketio
from app.models.notification import Notification
from flask import render_template
from threading import Thread

class NotificationService:
    """Complete notification and collaboration service"""
    
    @staticmethod
    def send_to_user(user_id, notification_type, title, message, 
                     priority='medium', data=None, delivery_methods=None):
        """Send notification to specific user"""
        if delivery_methods is None:
            delivery_methods = {'email': False, 'sms': False, 'push': False, 'in_app': True}
        
        notification = Notification(
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
        
        # Real-time WebSocket notification
        socketio.emit('notification', {
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'priority': notification.priority,
            'data': notification.data,
            'created_at': notification.created_at.isoformat()
        }, room=f"user_{user_id}")
        
        # Async email delivery
        if delivery_methods.get('email'):
            NotificationService._send_email.delay(
                to_email=notification.user.email,
                subject=title,
                template='notification_email',
                context={'notification': notification}
            )
        
        return notification
    
    @staticmethod
    def send_to_project(project_id, notification_type, title, message, 
                       exclude_user_id=None, **kwargs):
        """Send notification to all project members"""
        from app.models.project import Project
        
        project = Project.query.get(project_id)
        if not project:
            return []
        
        # Collect all project users
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
            notification = NotificationService.send_to_user(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                **kwargs
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def task_assigned(task, assignee):
        """Notify when task is assigned"""
        return NotificationService.send_to_user(
            user_id=assignee.id,
            notification_type='task_assigned',
            title='New Task Assigned',
            message=f'You have been assigned to task: {task.name}',
            priority='high',
            data={
                'task_id': task.id,
                'project_id': task.project_id,
                'project_name': task.project.name
            },
            delivery_methods={'email': True, 'in_app': True, 'push': True}
        )
    
    @staticmethod
    def task_completed(task, completed_by):
        """Notify when task is completed"""
        return NotificationService.send_to_project(
            project_id=task.project_id,
            notification_type='task_completed',
            title='Task Completed',
            message=f'Task "{task.name}" completed by {completed_by.full_name}',
            priority='medium',
            data={
                'task_id': task.id,
                'project_id': task.project_id,
                'completed_by': completed_by.full_name
            }
        )
    
    @staticmethod
    def task_overdue(task):
        """Notify when task becomes overdue"""
        return NotificationService.send_to_user(
            user_id=task.assignee_id,
            notification_type='task_overdue',
            title='Task Overdue',
            message=f'Task "{task.name}" is {task.days_late} days overdue',
            priority='urgent',
            data={
                'task_id': task.id,
                'project_id': task.project_id,
                'days_late': task.days_late
            },
            delivery_methods={'email': True, 'sms': True, 'in_app': True, 'push': True}
        )
    
    @staticmethod
    def milestone_achieved(milestone):
        """Notify when milestone is achieved"""
        return NotificationService.send_to_project(
            project_id=milestone.project_id,
            notification_type='milestone',
            title='🎉 Milestone Achieved',
            message=f'Milestone "{milestone.name}" has been achieved!',
            priority='high',
            data={
                'milestone_id': milestone.id,
                'project_id': milestone.project_id,
                'milestone_name': milestone.name
            }
        )
    
    @staticmethod
    def deadline_approaching(task, days_left):
        """Notify when deadline is approaching"""
        return NotificationService.send_to_user(
            user_id=task.assignee_id,
            notification_type='deadline',
            title='⚠️ Deadline Approaching',
            message=f'Task "{task.name}" is due in {days_left} days',
            priority='high',
            data={
                'task_id': task.id,
                'days_left': days_left,
                'due_date': task.end_date.isoformat()
            },
            delivery_methods={'email': True, 'in_app': True, 'push': True}
        )
    
    @staticmethod
    def project_update(project, update_message, updated_by):
        """Send project update to all members"""
        return NotificationService.send_to_project(
            project_id=project.id,
            notification_type='project_update',
            title=f'Project Update: {project.name}',
            message=update_message,
            exclude_user_id=updated_by.id,
            priority='medium',
            data={
                'project_id': project.id,
                'updated_by': updated_by.full_name
            }
        )
    
    @staticmethod
    def budget_alert(project, variance):
        """Notify when budget variance exceeds threshold"""
        admins = User.query.filter_by(role='admin').all()
        
        notifications = []
        for admin in admins:
            notification = NotificationService.send_to_user(
                user_id=admin.id,
                notification_type='budget_alert',
                title='💰 Budget Variance Alert',
                message=f'Project "{project.name}" has budget variance of {variance:.1f}%',
                priority='high',
                data={
                    'project_id': project.id,
                    'variance': variance,
                    'budget': float(project.budget) if project.budget else 0,
                    'actual': float(project.actual_cost) if project.actual_cost else 0
                },
                delivery_methods={'email': True, 'in_app': True}
            )
            notifications.append(notification)
        
        return notifications


class CommentService:
    """Discussion and commenting service"""
    
    @staticmethod
    def add_comment(user_id, target_type, target_id, content, parent_id=None):
        """Add comment to any target"""
        from app.models.comment import Comment
        
        comment = Comment(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            content=content,
            parent_id=parent_id
        )
        
        # Extract mentions (@username)
        mentions = CommentService._extract_mentions(content)
        if mentions:
            comment.mentions = mentions
        
        db.session.add(comment)
        db.session.commit()
        
        # Notify mentioned users
        if mentions:
            for user_id in mentions:
                NotificationService.send_to_user(
                    user_id=user_id,
                    notification_type='mention',
                    title=f"{comment.user.full_name} mentioned you",
                    message=content[:100] + "...",
                    data={
                        'comment_id': comment.id,
                        'target_type': target_type,
                        'target_id': target_id
                    }
                )
        
        # Notify project members (for task comments)
        if target_type == 'task':
            task = Task.query.get(target_id)
            if task:
                NotificationService.send_to_project(
                    project_id=task.project_id,
                    notification_type='new_comment',
                    title=f'New comment on {task.name}',
                    message=content[:100] + "...",
                    exclude_user_id=user_id,
                    data={
                        'comment_id': comment.id,
                        'task_id': task.id,
                        'project_id': task.project_id
                    }
                )
        
        # Trigger real-time update
        socketio.emit('new_comment', comment.to_dict(), room=f"{target_type}_{target_id}")
        
        return comment
    
    @staticmethod
    def _extract_mentions(text):
        """Extract mentioned usernames from text"""
        import re
        from app.models.user import User
        
        mentions = re.findall(r'@(\w+)', text)
        user_ids = []
        
        for username in mentions:
            user = User.query.filter_by(username=username).first()
            if user:
                user_ids.append(user.id)
        
        return user_ids


class MessageService:
    """Direct messaging between users"""
    
    @staticmethod
    def send_message(sender_id, recipient_id, subject, content):
        """Send direct message"""
        from app.models.message import Message
        
        # Generate conversation ID
        conversation_id = f"{min(sender_id, recipient_id)}_{max(sender_id, recipient_id)}"
        
        message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            subject=subject,
            content=content
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Send notification
        NotificationService.send_to_user(
            user_id=recipient_id,
            notification_type='new_message',
            title=f'New message from {message.sender.full_name}',
            message=subject,
            data={
                'message_id': message.id,
                'conversation_id': conversation_id,
                'sender': message.sender.full_name
            },
            delivery_methods={'email': True, 'in_app': True, 'push': True}
        )
        
        # Real-time notification
        socketio.emit('new_message', message.to_dict(), room=f"user_{recipient_id}")
        
        return message
    
    @staticmethod
    def get_conversation(user1_id, user2_id, limit=50):
        """Get conversation between two users"""
        from app.models.message import Message
        
        conversation_id = f"{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
        
        messages = Message.query.filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()
        
        return messages