from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Chemical, AuditLog
from .serializers import ChemicalSerializer
from .permissions import IsTeacherOrAssistant
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import filters

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None or not user.is_active:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({
            "access": access_token,
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)

        #  Set secure, HTTP-only JWT cookie
        response.set_cookie(
            key=settings.AUTH_COOKIE,
            value=access_token,
            max_age=settings.AUTH_COOKIE_MAX_AGE,
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            path=settings.AUTH_COOKIE_PATH,
        )

        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({"detail": "Logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.AUTH_COOKIE)
        return response


class ChemicalViewSet(viewsets.ModelViewSet):
    queryset = Chemical.objects.all()
    serializer_class = ChemicalSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'form', 'concentration']
    ordering_fields = ['expiry_date', 'quantity', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]  # All logged-in users can view
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAssistant()]  # Only teachers/assistants can modify
        return super().get_permissions()

    def perform_create(self, serializer):
        chemical = serializer.save(added_by=self.request.user)
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            model_name='Chemical',
            object_id=chemical.id,
            changes=f"Created: {chemical.name}"
        )

    def perform_update(self, serializer):
        chemical = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action='update',
            model_name='Chemical',
            object_id=chemical.id,
            changes=f"Updated: {chemical.name}"
        )

    def perform_destroy(self, instance):
        AuditLog.objects.create(
            user=self.request.user,
            action='delete',
            model_name='Chemical',
            object_id=instance.id,
            changes=f"Deleted: {instance.name}"
        )
        instance.delete()

    def get_queryset(self):
        qs = super().get_queryset()
        # Automated alerts: expired, low stock, dangerous
        expired = self.request.query_params.get('expired')
        low_stock = self.request.query_params.get('low_stock')
        danger = self.request.query_params.get('danger')
        if expired == 'true':
            from datetime import date
            qs = qs.filter(expiry_date__lt=date.today())
        if low_stock == 'true':
            qs = qs.filter(quantity__lte=5)  # threshold can be adjusted
        if danger:
            qs = qs.filter(danger_classification=danger)
        return qs
