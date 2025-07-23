from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
import openai

class ChatbotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Role-based access example: restrict certain queries for some roles
        if hasattr(user, 'role'):
            if user.role not in ['teacher', 'assistant']:
                return Response({'error': 'You do not have permission to use the chatbot.'}, status=status.HTTP_403_FORBIDDEN)

        # Initialize OpenAI client
        openai.api_key = settings.OPENAI_API_KEY

        # Compose prompt with context awareness and user role
        prompt = f"You are a helpful assistant for a high school science lab chemical inventory system. The user role is {user.role}. Answer the query accordingly.\nUser query: {query}"

        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7,
                n=1,
                stop=None,
            )
            answer = response.choices[0].text.strip()
        except Exception as e:
            return Response({'error': f'AI service error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'answer': answer})
