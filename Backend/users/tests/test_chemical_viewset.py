from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from users.models import Chemical, AuditLog
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, timedelta

User = get_user_model()

class TestChemicalViewSet(APITestCase):
    def setUp(self):
        # Create users with different roles
        self.teacher = User.objects.create_user(email='teacher@example.com', password='pass', role='teacher')
        self.lab_expert = User.objects.create_user(email='labexpert@example.com', password='pass', role='lab_expert')
        self.student = User.objects.create_user(email='student@example.com', password='pass', role='student')

        # Create a chemical added by teacher
        self.chemical = Chemical.objects.create(
            name='Test Chemical',
            form='powder',
            concentration='10%',
            volume=100.0,
            quantity=10,
            storage_location='Shelf A',
            expiry_date=date.today() + timedelta(days=30),
            danger_classification='green',
            added_by=self.teacher
        )

        # URLs
        self.list_url = reverse('chemical-list')
        self.detail_url = reverse('chemical-detail', args=[self.chemical.id])

        # Clients with authentication
        self.teacher_client = self.get_client_for_user(self.teacher)
        self.lab_expert_client = self.get_client_for_user(self.lab_expert)
        self.student_client = self.get_client_for_user(self.student)
        self.anon_client = APIClient()

    def get_client_for_user(self, user):
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return client

    def test_list_chemicals_authenticated(self):
        response = self.teacher_client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_list_chemicals_unauthenticated(self):
        response = self.anon_client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_chemical(self):
        response = self.teacher_client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.chemical.name)

    def test_create_chemical_permission(self):
        data = {
            'name': 'New Chemical',
            'form': 'aqueous',
            'concentration': '5%',
            'volume': 50.0,
            'quantity': 5,
            'storage_location': 'Shelf B',
            'expiry_date': str(date.today() + timedelta(days=60)),
            'danger_classification': 'yellow',
        }
        # Student should not be able to create
        response = self.student_client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Lab expert should be able to create
        response = self.lab_expert_client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Chemical')

    def test_update_chemical_permission(self):
        data = {
            'name': 'Updated Chemical',
            'form': 'crystalline',
            'concentration': '15%',
            'volume': 75.0,
            'quantity': 8,
            'storage_location': 'Shelf C',
            'expiry_date': str(date.today() + timedelta(days=90)),
            'danger_classification': 'red',
        }
        # Student should not be able to update
        response = self.student_client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Lab expert should be able to update
        response = self.lab_expert_client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Chemical')

    def test_delete_chemical_permission(self):
        # Student should not be able to delete
        response = self.student_client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Lab expert should be able to delete
        response = self.lab_expert_client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_audit_log_created_on_create(self):
        data = {
            'name': 'Audit Chemical',
            'form': 'powder',
            'concentration': '20%',
            'volume': 30.0,
            'quantity': 3,
            'storage_location': 'Shelf D',
            'expiry_date': str(date.today() + timedelta(days=120)),
            'danger_classification': 'green',
        }
        response = self.lab_expert_client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chemical_id = response.data['id']
        audit_logs = AuditLog.objects.filter(object_id=chemical_id, action='create', model_name='Chemical')
        self.assertTrue(audit_logs.exists())

    def test_audit_log_created_on_update(self):
        data = {
            'name': 'Audit Updated Chemical',
            'form': 'aqueous',
            'concentration': '25%',
            'volume': 40.0,
            'quantity': 6,
            'storage_location': 'Shelf E',
            'expiry_date': str(date.today() + timedelta(days=150)),
            'danger_classification': 'yellow',
        }
        response = self.lab_expert_client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        audit_logs = AuditLog.objects.filter(object_id=self.chemical.id, action='update', model_name='Chemical')
        self.assertTrue(audit_logs.exists())

    def test_audit_log_created_on_delete(self):
        response = self.lab_expert_client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        audit_logs = AuditLog.objects.filter(object_id=self.chemical.id, action='delete', model_name='Chemical')
        self.assertTrue(audit_logs.exists())

    def test_filter_expired(self):
        expired_chemical = Chemical.objects.create(
            name='Expired Chemical',
            form='powder',
            concentration='10%',
            volume=10.0,
            quantity=2,
            storage_location='Shelf F',
            expiry_date=date.today() - timedelta(days=1),
            danger_classification='green',
            added_by=self.teacher
        )
        response = self.teacher_client.get(self.list_url + '?expired=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(c['id'] == expired_chemical.id for c in response.data))

    def test_filter_low_stock(self):
        low_stock_chemical = Chemical.objects.create(
            name='Low Stock Chemical',
            form='powder',
            concentration='10%',
            volume=10.0,
            quantity=3,
            storage_location='Shelf G',
            expiry_date=date.today() + timedelta(days=10),
            danger_classification='green',
            added_by=self.teacher
        )
        response = self.teacher_client.get(self.list_url + '?low_stock=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(c['id'] == low_stock_chemical.id for c in response.data))

    def test_filter_danger(self):
        danger_chemical = Chemical.objects.create(
            name='Danger Chemical',
            form='powder',
            concentration='10%',
            volume=10.0,
            quantity=10,
            storage_location='Shelf H',
            expiry_date=date.today() + timedelta(days=10),
            danger_classification='red',
            added_by=self.teacher
        )
        response = self.teacher_client.get(self.list_url + '?danger=red')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(c['id'] == danger_chemical.id for c in response.data))
