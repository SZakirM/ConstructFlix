# run.py
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db, socketio
import ssl

app = create_app()

@app.shell_context_processor
def make_shell_context():
    from app.models.user import User
    from app.models.project import Project
    from app.models.task import Task, TaskDependency, Milestone
    return {'db': db, 'User': User, 'Project': Project, 'Task': Task, 'Milestone': Milestone}

if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') == 'production':
        # Production with HTTPS
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('ssl/cert.pem', 'ssl/key.pem')
        socketio.run(app, host='0.0.0.0', port=443, ssl_context=context)
    else:
        # Development
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)

