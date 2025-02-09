from rest_framework import serializers
from .models import MemorialRoom


class MemorialRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemorialRoom
        fields = [
            'id', 'name', 'capacity', 'operating_hours',
            'notes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'capacity': {'required': False},
            'notes': {'required': False},
            'is_active': {'required': False}
        } 