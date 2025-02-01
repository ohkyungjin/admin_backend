from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import ActivityLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'phone', 'auth_level', 'department', 
                 'position', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at', 'last_password_change')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': '비밀번호는 필수 입력 항목입니다.',
            'blank': '비밀번호를 입력해주세요.'
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': '비밀번호 확인은 필수 입력 항목입니다.',
            'blank': '비밀번호 확인을 입력해주세요.'
        }
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'name', 'phone', 'department', 'position', 'auth_level')
        extra_kwargs = {
            'email': {
                'required': True,
                'error_messages': {
                    'required': '이메일은 필수 입력 항목입니다.',
                    'invalid': '유효한 이메일 주소를 입력해주세요.',
                    'unique': '이미 사용 중인 이메일 주소입니다.'
                }
            },
            'name': {
                'required': True,
                'error_messages': {
                    'required': '이름은 필수 입력 항목입니다.',
                    'blank': '이름을 입력해주세요.'
                }
            },
            'phone': {
                'required': True,
                'error_messages': {
                    'required': '전화번호는 필수 입력 항목입니다.',
                    'blank': '전화번호를 입력해주세요.'
                }
            },
            'auth_level': {
                'required': True,
                'error_messages': {
                    'required': '권한 레벨은 필수 입력 항목입니다.',
                    'invalid_choice': '유효하지 않은 권한 레벨입니다.',
                }
            }
        }

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('비밀번호는 최소 8자 이상이어야 합니다.')
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError('비밀번호는 최소 1개 이상의 숫자를 포함해야 합니다.')
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError('비밀번호는 최소 1개 이상의 대문자를 포함해야 합니다.')
        if not any(char.islower() for char in value):
            raise serializers.ValidationError('비밀번호는 최소 1개 이상의 소문자를 포함해야 합니다.')
        if not any(char in '!@#$%^&*()' for char in value):
            raise serializers.ValidationError('비밀번호는 최소 1개 이상의 특수문자(!@#$%^&*())를 포함해야 합니다.')
        return value

    def validate_phone(self, value):
        import re
        if not re.match(r'^\d{2,3}-\d{3,4}-\d{4}$', value):
            raise serializers.ValidationError('올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)')
        return value

    def validate(self, data):
        if 'password' not in data:
            raise serializers.ValidationError({
                'password': '비밀번호는 필수 입력 항목입니다.'
            })
        if 'password_confirm' not in data:
            raise serializers.ValidationError({
                'password_confirm': '비밀번호 확인은 필수 입력 항목입니다.'
            })
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': '비밀번호가 일치하지 않습니다.'
            })
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'phone', 'auth_level', 'department', 'position', 'is_active')


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "새 비밀번호가 일치하지 않습니다."})
        return attrs


class ActivityLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ('created_at',)