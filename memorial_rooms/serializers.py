from rest_framework import serializers
from .models import MemorialRoom


class OperatingHoursSerializer(serializers.Serializer):
    start_time = serializers.CharField(max_length=5)
    end_time = serializers.CharField(max_length=5)

    def validate(self, data):
        try:
            # HH:MM 형식 검증
            for time_str in [data['start_time'], data['end_time']]:
                hours, minutes = time_str.split(':')
                if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                    raise ValueError
        except (ValueError, IndexError):
            raise serializers.ValidationError("시간은 HH:MM 형식이어야 합니다.")
        return data


class MemorialRoomSerializer(serializers.ModelSerializer):
    current_status_display = serializers.CharField(source='get_current_status_display', read_only=True)

    class Meta:
        model = MemorialRoom
        fields = [
            'id', 'name', 'capacity', 'notes',
            'operating_hours', 'is_active', 'current_status',
            'current_status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'current_status']
        extra_kwargs = {
            'capacity': {'required': False},
            'notes': {'required': False},
            'is_active': {'required': False},
            'operating_hours': {
                'required': True,
                'help_text': '예: 09:00-18:00'
            }
        }

    def validate_operating_hours(self, value):
        try:
            start_time, end_time = value.split('-')
            # HH:MM 형식 검증
            for time_str in [start_time, end_time]:
                hours, minutes = time_str.split(':')
                if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                    raise ValueError
        except (ValueError, IndexError):
            raise serializers.ValidationError(
                "운영 시간은 'HH:MM-HH:MM' 형식이어야 합니다. (예: 09:00-18:00)"
            )
        return value

    def create(self, validated_data):
        operating_hours = validated_data.pop('operating_hours')
        memorial_room = MemorialRoom.objects.create(
            operating_hours=operating_hours,
            **validated_data
        )
        return memorial_room

    def update(self, instance, validated_data):
        if 'operating_hours' in validated_data:
            instance.operating_hours = validated_data.pop('operating_hours')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance 