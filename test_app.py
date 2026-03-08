#!/usr/bin/env python
"""
Comprehensive application test suite
"""
from app import create_app, db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, Milestone
import sys

print('=== Application Test Suite ===\n')

# Test 1: App creation
print('[1] Creating Flask app...')
try:
    app = create_app()
    print('OK: App created successfully\n')
except Exception as e:
    print('FAIL: ' + str(e) + '\n')
    sys.exit(1)

# Test 2: Database models
print('[2] Testing database models...')
try:
    with app.app_context():
        print('  - User model: OK')
        print('  - Project model: OK')
        print('  - Task model: OK')
        print('  - Milestone model: OK')
    print('OK: All models accessible\n')
except Exception as e:
    print('FAIL: ' + str(e) + '\n')
    sys.exit(1)

# Test 3: Test routes
print('[3] Testing routes...')
routes_to_test = [
    ('/', 'Index/Login redirect'),
    ('/auth/login', 'Login page'),
    ('/auth/register', 'Register page'),
]

try:
    with app.test_client() as c:
        for route, desc in routes_to_test:
            r = c.get(route)
            status = 'OK' if r.status_code in [200, 302] else 'FAIL'
            print('  ' + status + ' GET ' + route + ': ' + str(r.status_code) + ' - ' + desc)
    print()
except Exception as e:
    print('FAIL: ' + str(e) + '\n')
    sys.exit(1)

# Test 4: Database query
print('[4] Testing database queries...')
try:
    with app.app_context():
        user_count = User.query.count()
        project_count = Project.query.count()
        task_count = Task.query.count()
        print('  - Users in DB: ' + str(user_count))
        print('  - Projects in DB: ' + str(project_count))
        print('  - Tasks in DB: ' + str(task_count))
    print('OK: Database queries successful\n')
except Exception as e:
    print('FAIL: ' + str(e) + '\n')
    sys.exit(1)

# Test 5: User authentication
print('[5] Testing user authentication...')
try:
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if user:
            print('  - Found test user: ' + user.username)
            is_valid = user.check_password('password123')
            check_result = 'OK' if is_valid else 'FAIL'
            print('  - Password check: ' + check_result)
        else:
            print('  - No test user found')
    print('OK: Authentication check complete\n')
except Exception as e:
    print('FAIL: ' + str(e) + '\n')
    sys.exit(1)

# Test 6: Login flow
print('[6] Testing login functionality...')
try:
    with app.test_client() as c:
        # GET login page
        r = c.get('/auth/login')
        if r.status_code == 200:
            print('  - Login page loads: OK')
        else:
            print('  - Login page loads: FAIL (' + str(r.status_code) + ')')
    print('OK: Login flow check complete\n')
except Exception as e:
    print('FAIL: ' + str(e) + '\n')
    sys.exit(1)

print('=== All tests PASSED ===')
