# run.py
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db, socketio
import ssl

app = create_app()

# Ensure instance folder exists for SQLite database
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

# Create missing tables automatically in development
with app.app_context():
    db.create_all()

@app.shell_context_processor
def make_shell_context():
    from app.models.user import User
    from app.models.project import Project
    from app.models.task import Task, TaskDependency, Milestone
    return {'db': db, 'User': User, 'Project': Project, 'Task': Task, 'Milestone': Milestone}

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    if os.environ.get('FLASK_ENV') == 'production':
        # Production with HTTPS
        cert_file = 'ssl/cert.pem'
        key_file = 'ssl/key.pem'
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            raise FileNotFoundError(f"Missing SSL files for production: {cert_file} and {key_file} must exist.")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        socketio.run(app, host=host, port=port, ssl_context=context)
    else:
        socketio.run(app, host=host, port=port, debug=debug)

