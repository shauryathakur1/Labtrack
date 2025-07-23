from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import requests

class SendVerificationCodeView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        code = f"{random.randint(100000, 999999)}"
        cache.set(f'verification_code_{email}', code, timeout=10*60)  # 10 minutes expiry

        # Send email (simplified, configure your email backend properly)
        send_mail(
            'Your LabTrack Verification Code',
            f'Your verification code is: {code}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({'message': 'Verification code sent'}, status=status.HTTP_200_OK)

class VerifyCodeView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        if not email or not code:
            return Response({'error': 'Email and code are required'}, status=status.HTTP_400_BAD_REQUEST)

        cached_code = cache.get(f'verification_code_{email}')
        if cached_code == code:
            cache.delete(f'verification_code_{email}')
            return Response({'message': 'Verification successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

class VerifyRecaptchaView(APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        secret_key = settings.RECAPTCHA_SECRET_KEY
        url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {
            'secret': secret_key,
            'response': token,
        }
        response = requests.post(url, data=data)
        result = response.json()

        if result.get('success') and result.get('score', 0) >= 0.5:
            return Response({'message': 'reCAPTCHA verified'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'reCAPTCHA verification failed'}, status=status.HTTP_400_BAD_REQUEST)
