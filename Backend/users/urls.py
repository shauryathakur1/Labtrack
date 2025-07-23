from django.urls import path, re_path
from .views import (
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView
)

from .api import auth_views

urlpatterns = [
    re_path(
        r'^o/(?P<provider>\S+)/$',
        CustomProviderAuthView.as_view(),
        name='provider-auth'
    ),
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('logout/', LogoutView.as_view()),

    path('api/send-verification-code/', auth_views.SendVerificationCodeView.as_view(), name='send_verification_code'),
    path('api/verify-code/', auth_views.VerifyCodeView.as_view(), name='verify_code'),
    path('api/verify-recaptcha/', auth_views.VerifyRecaptchaView.as_view(), name='verify_recaptcha'),
]
