from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from config import Config, TestingConfig
import os
from app.utils.logging_config import setup_logging, log_security_event
import redis
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

# Initialize extensions (singleton instances)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
socketio = SocketIO()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    if isinstance(config_class, str):
        if config_class.lower() == 'testing':
            config_class = TestingConfig
        elif config_class.lower() in ['default', 'config', 'base']:
            config_class = Config
        else:
            # attempt import path as fallback
            try:
                from werkzeug.utils import import_string
                config_class = import_string(config_class)
            except Exception as e:
                raise ValueError(f"Unknown config class: {config_class}") from e
    app.config.from_object(config_class)
    if app.config.get('TESTING'):
        app.config['WTF_CSRF_ENABLED'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    
    # Set login manager settings after init_app
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access this page.'
    login_manager.login_message_category = 'info'

    # user loader required by flask-login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('auth.login', next=request.path))
    
    # Setup logging
    setup_logging(app)
    
    # Make security logger available
    app.log_security_event = log_security_event
    
    # Redis client for other features
    if 'REDIS_URL' in app.config:
        app.redis_client = redis.from_url(app.config['REDIS_URL'])
        # Initialize SocketIO with message queue
        socketio.init_app(app, cors_allowed_origins="*", message_queue=app.config.get('REDIS_URL'))
    else:
        socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    from app.routes import main_bp, auth_bp, admin_bp, api_bp, tasks_bp, gantt_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(gantt_bp, url_prefix='/gantt')
    
    # Skip db.create_all() - tables should already exist or be created manually
    # with app.app_context():
    #     db.create_all()
    
    return app

