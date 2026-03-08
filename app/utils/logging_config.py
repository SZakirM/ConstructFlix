import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import request, session

def setup_logging(app):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set log level
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # Format for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation (10 MB per file, keep 10 backups)
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Time-based rotation for security logs
    security_handler = TimedRotatingFileHandler(
        'logs/security.log',
        when='midnight',
        interval=1,
        backupCount=30
    )
    security_handler.setFormatter(formatter)
    security_handler.setLevel(logging.WARNING)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(security_handler)
    app.logger.setLevel(log_level)
    
    # Log application startup
    app.logger.info('ConstructFlix application started')
    
    # Add request logging middleware
    @app.before_request
    def log_request_info():
        app.logger.info(f'Request: {request.method} {request.path} - IP: {request.remote_addr}')
    
    @app.after_request
    def log_response_info(response):
        app.logger.info(f'Response: {response.status_code} - {request.method} {request.path}')
        return response

# Custom logger for security events
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('logs/security.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

def log_security_event(event_type, user=None, details=None):
    """Log security-related events"""
    user_info = f"User: {user}" if user else "Anonymous"
    details_info = f" - Details: {details}" if details else ""
    security_logger.warning(f"{event_type} - {user_info}{details_info}")