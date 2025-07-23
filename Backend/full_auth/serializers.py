from rest_framework import serializers
from .models import Chemical, Equipment, CustomUser


class ChemicalSerializer(serializers.ModelSerializer):
    added_by_email = serializers.ReadOnlyField(source='added_by.email')
    is_expired = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    is_dangerous = serializers.SerializerMethodField()

    class Meta:
        model = Chemical
        fields = [
            'id', 'name', 'form', 'concentration', 'volume', 'quantity',
            'storage_location', 'expiry_date', 'is_expired',
            'msds_file', 'danger_classification',
            'added_by', 'added_by_email', 'created_at'
        ]
        read_only_fields = ['added_by', 'created_at']

    def get_is_expired(self, obj):
        from datetime import date
        return obj.expiry_date < date.today()

    def get_is_low_stock(self, obj):
        return obj.quantity <= 5  # threshold can be adjusted

    def get_is_dangerous(self, obj):
        return obj.danger_classification == 'red'


class EquipmentSerializer(serializers.ModelSerializer):
    added_by_email = serializers.ReadOnlyField(source='added_by.email')

    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'condition', 'quantity', 'last_maintenance_date',
            'notes', 'added_by', 'added_by_email', 'created_at'
        ]
        read_only_fields = ['added_by', 'created_at']


from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseCreateSerializer

class CustomUserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = ('id', 'username', 'email', 'role')  # include role in API output


class CustomUserCreateSerializer(BaseCreateSerializer):
    class Meta(BaseCreateSerializer.Meta):
        model = CustomUser
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        validated_data['role'] = 'student'  # Default role assigned on signup
        return super().create(validated_data)
