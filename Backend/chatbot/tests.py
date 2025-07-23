from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class ChatbotAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('chatbot_api')
        self.teacher = User.objects.create_user(username='teacher1', password='pass123', role='teacher')
        self.assistant = User.objects.create_user(username='assistant1', password='pass123', role='assistant')
        self.student = User.objects.create_user(username='student1', password='pass123', role='student')

    def test_authentication_required(self):
        response = self.client.post(self.url, {'query': 'test'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_role_restriction(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.url, {'query': 'test'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_query(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('openai.Completion.create')
    def test_successful_response(self, mock_openai):
        mock_openai.return_value = type('obj', (object,), {
            'choices': [type('obj', (object,), {'text': 'This is a test response.'})()]
        })()
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(self.url, {'query': 'What is the safety procedure?'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertEqual(response.data['answer'], 'This is a test response.')

    @patch('openai.Completion.create', side_effect=Exception('API error'))
    def test_openai_api_error(self, mock_openai):
        self.client.force_authenticate(user=self.assistant)
        response = self.client.post(self.url, {'query': 'Test error handling'})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
