import unittest
from app import create_app, db
from app.models.user import User
from app.models.project import Project
from datetime import datetime, timedelta
import json

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            is_active_account=True,
            email_verified=True
        )
        self.user.set_password('TestPass123')
        db.session.add(self.user)
        db.session.commit()
        
        # Login to get session
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestPass123'
        })
        
        # Create test project
        self.project = Project(
            name='Test Project',
            description='Test Description',
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=30),
            created_by=self.user.id,
            status='planning'
        )
        db.session.add(self.project)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_get_projects(self):
        """Test getting projects list"""
        response = self.client.get('/api/projects')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
    
    def test_create_project(self):
        """Test creating a new project"""
        response = self.client.post('/api/projects', json={
            'name': 'New API Project',
            'description': 'Created via API',
            'start_date': datetime.now().date().isoformat(),
            'end_date': (datetime.now().date() + timedelta(days=60)).isoformat(),
            'budget': 100000
        })
        
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['name'], 'New API Project')
    
    def test_get_project_documents(self):
        """Test getting project documents"""
        response = self.client.get(f'/api/projects/{self.project.id}/documents')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('documents', data)

if __name__ == '__main__':
    unittest.main()