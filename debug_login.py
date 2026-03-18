from app import create_app, db
from app.models.user import User

app = create_app('testing')
client = app.test_client()
with app.app_context():
    db.create_all()
    u = User(username='testuser', email='test@example.com', first_name='Test', last_name='User', is_active_account=True, email_verified=True)
    u.set_password('TestPass123')
    db.session.add(u)
    db.session.commit()
    r = client.post('/auth/login', data={'email':'test@example.com', 'password':'TestPass123'}, follow_redirects=True)
    print('status', r.status_code)
    print('location', r.headers.get('Location'))
    print(r.data.decode('utf-8')[:1200])
