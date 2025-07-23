import os
import django
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from users.models import CustomUser, Chemical, AuditLog
from rest_framework import status

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.full_auth.settings')
# os.environ.setdefault('DJANGO_CONFIGURATION', 'Settings')  # Commented out as django-configurations is not used
django.setup()

class TestPermission(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create users with different roles
        self.lab_expert = CustomUser.objects.create_user(username='labexpert', email='labexpert@example.com', password='password123', role='lab_expert')
        self.teacher = CustomUser.objects.create_user(username='teacher', email='teacher@example.com', password='password123', role='teacher')
        self.student = CustomUser.objects.create_user(username='student', email='student@example.com', password='password123', role='student')

        # Login URLs
        self.login_url = reverse('login')  # Adjust if login URL is different

        # Chemical list URL
        self.chemical_url = reverse('chemical-list')  # Adjust if router name is different

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_lab_expert_can_create_update_delete(self):
        self.authenticate(self.lab_expert)
        # Create chemical
        data = {
            'name': 'Test Chemical',
            'form': 'powder',
            'quantity': 10,
            'storage_location': 'Shelf A',
            'expiry_date': '2030-01-01',
            'danger_classification': 'green'
        }
        response = self.client.post(self.chemical_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chemical_id = response.data['id']

        # Update chemical
        update_data = {'quantity': 20}
        response = self.client.patch(f"{self.chemical_url}{chemical_id}/", update_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

        # Delete chemical
        response = self.client.delete(f"{self.chemical_url}{chemical_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_teacher_can_create_update_delete(self):
        self.authenticate(self.teacher)
        data = {
            'name': 'Teacher Chemical',
            'form': 'aqueous',
            'quantity': 5,
            'storage_location': 'Shelf B',
            'expiry_date': '2030-01-01',
            'danger_classification': 'yellow'
        }
        response = self.client.post(self.chemical_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chemical_id = response.data['id']

        update_data = {'quantity': 15}
        response = self.client.patch(f"{self.chemical_url}{chemical_id}/", update_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

        response = self.client.delete(f"{self.chemical_url}{chemical_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_student_read_only_access(self):
        self.authenticate(self.student)
        # Student can list chemicals
        response = self.client.get(self.chemical_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Student cannot create chemical
        data = {
            'name': 'Student Chemical',
            'form': 'crystalline',
            'quantity': 3,
            'storage_location': 'Shelf C',
            'expiry_date': '2030-01-01',
            'danger_classification': 'red'
        }
        response = self.client.post(self.chemical_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_audit_log_created(self):
        self.authenticate(self.lab_expert)
        data = {
            'name': 'Audit Chemical',
            'form': 'powder',
            'quantity': 7,
            'storage_location': 'Shelf D',
            'expiry_date': '2030-01-01',
            'danger_classification': 'green'
        }
        response = self.client.post(self.chemical_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chemical_id = response.data['id']

        # Check audit log for create
        log = AuditLog.objects.filter(object_id=chemical_id, action='create', user=self.lab_expert)
        self.assertTrue(log.exists())
