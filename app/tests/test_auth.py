import unittest
from app import create_app, db
from app.models.user import User
from flask import url_for
import json

class AuthTestCase(unittest.TestCase):
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
            is_active=True,
            email_verified=True
        )
        self.user.set_password('TestPass123')
        db.session.add(self.user)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_valid_login(self):
        """Test login with valid credentials"""
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestPass123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_registration(self):
        """Test user registration"""
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'NewPass123',
            'password2': 'NewPass123',
            'agree_terms': True
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        
        # Check user was created
        user = User.query.filter_by(email='new@example.com').first()
        self.assertIsNotNone(user)
    
    def test_duplicate_registration(self):
        """Test registration with existing email"""
        response = self.client.post('/auth/register', data={
            'username': 'testuser2',
            'email': 'test@example.com',  # Existing email
            'first_name': 'Another',
            'last_name': 'User',
            'password': 'TestPass123',
            'password2': 'TestPass123',
            'agree_terms': True
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email already registered', response.data)

if __name__ == '__main__':
    unittest.main()