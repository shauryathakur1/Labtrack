from rest_framework import serializers
from .models import Chemical
from django.contrib.auth import get_user_model

User = get_user_model()

class ChemicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chemical
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role']
