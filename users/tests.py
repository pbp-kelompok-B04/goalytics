from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

class UserTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_user_creation(self):
        """Test that a user can be created"""
        self.assertEqual(self.test_user.username, 'testuser')
        self.assertTrue(self.test_user.check_password('testpass123'))

    def test_user_login(self):
        """Test user login functionality"""
        login = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login)

    def test_user_logout(self):
        """Test user logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 301)