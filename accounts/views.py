from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging
from .models import ActivityLog, User
from .permissions import IsSuperAdmin, IsAdmin, IsOwnerOrHigherLevel
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, ActivityLogSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_permissions(self):
        """
        액션별 권한 설정:
        - 목록 조회: 관리자 이상
        - 상세 조회: 관리자 이상 또는 본인
        - 생성: 슈퍼관리자만
        - 수정: 본인 또는 더 높은 권한
        - 삭제: 슈퍼관리자만
        """
        if self.action == 'list':
            permission_classes = [IsAdmin]
        elif self.action == 'create':
            permission_classes = [IsSuperAdmin]
        elif self.action in ['destroy']:
            permission_classes = [IsSuperAdmin]
        elif self.action in ['retrieve', 'update', 'partial_update', 'change_password', 'toggle_active']:
            permission_classes = [IsOwnerOrHigherLevel]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        권한에 따른 쿼리셋 필터링:
        - 슈퍼관리자: 모든 사용자
        - 관리자: 자신과 지도사
        - 지도사: 자신만
        """
        user = self.request.user
        if user.auth_level == User.LEVEL_SUPERADMIN:
            return User.objects.all()
        elif user.auth_level == User.LEVEL_ADMIN:
            return User.objects.filter(auth_level__lte=user.auth_level)
        else:
            return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return PasswordChangeSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        logger.info(f"User creation attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(f"Validation failed for user creation: {serializer.errors}")
            logger.error(f"Request data: {request.data}")
            logger.error(f"Error details: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "사용자 생성 실패",
                    "errors": serializer.errors,
                    "request_data": request.data
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = serializer.save()
            logger.info(f"Successfully created user: {user.email}")
            
            # 활동 로그 생성
            ActivityLog.objects.create(
                user=request.user,
                action_type='user_create',
                description=f'새로운 직원 계정 생성: {user.email}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "status": "success",
                    "message": "사용자가 성공적으로 생성되었습니다.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to create user. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "사용자 생성 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_update(self, serializer):
        logger.info(f"Updating user with data: {serializer.validated_data}")
        try:
            user = serializer.save()
            logger.info(f"Successfully updated user: {user.email}")
        except Exception as e:
            logger.error(f"Failed to update user. Error: {str(e)}")
            raise

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        logger.info(f"Password change attempt for user: {user.email}")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                # Check old password
                if not user.check_password(serializer.data.get('old_password')):
                    logger.warning(f"Invalid current password for user: {user.email}")
                    return Response({'old_password': ['현재 비밀번호가 올바르지 않습니다.']},
                                status=status.HTTP_400_BAD_REQUEST)
                
                # Set new password
                user.set_password(serializer.data.get('new_password'))
                user.last_password_change = timezone.now()
                user.save()
                
                logger.info(f"Successfully changed password for user: {user.email}")
                return Response({'status': 'success', 'message': '비밀번호가 성공적으로 변경되었습니다.'})
            except Exception as e:
                logger.error(f"Failed to change password for user: {user.email}. Error: {str(e)}")
                return Response({'error': '비밀번호 변경 중 오류가 발생했습니다.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.error(f"Invalid password change data for user: {user.email}. Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        logger.info(f"Toggling active status for user: {user.email}")
        
        try:
            user.is_active = not user.is_active
            user.save()
            status_str = "활성화" if user.is_active else "비활성화"
            logger.info(f"Successfully {status_str} user: {user.email}")
            return Response({'is_active': user.is_active, 'message': f'사용자가 {status_str} 되었습니다.'})
        except Exception as e:
            logger.error(f"Failed to toggle active status for user: {user.email}. Error: {str(e)}")
            return Response({'error': '상태 변경 중 오류가 발생했습니다.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def me(self, request):
        """현재 로그인한 사용자의 정보를 반환합니다."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ActivityLog.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        action_type = self.request.query_params.get('action_type', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action_type:
            queryset = queryset.filter(action_type=action_type)
            
        return queryset

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # 사용자 정보 조회
            user = User.objects.get(email=request.data['email'])
            
            # 권한 레벨에 따른 토큰 유효기간 설정
            auth_level_map = {
                User.LEVEL_SUPERADMIN: 'SUPERADMIN',
                User.LEVEL_ADMIN: 'ADMIN',
                User.LEVEL_INSTRUCTOR: 'INSTRUCTOR',
            }
            
            auth_level = auth_level_map.get(user.auth_level)
            if auth_level and auth_level in settings.SIMPLE_JWT['AUTH_LEVEL_TOKEN_LIFETIMES']:
                # 새로운 토큰 생성
                refresh = RefreshToken.for_user(user)
                
                # 토큰 유효기간 설정
                token_settings = settings.SIMPLE_JWT['AUTH_LEVEL_TOKEN_LIFETIMES'][auth_level]
                refresh.set_exp(lifetime=token_settings['REFRESH_TOKEN_LIFETIME'])
                refresh.access_token.set_exp(lifetime=token_settings['ACCESS_TOKEN_LIFETIME'])
                
                # 추가 클레임 설정
                refresh['auth_level'] = user.auth_level
                refresh.access_token['auth_level'] = user.auth_level
                
                response.data = {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'name': user.name,
                        'auth_level': user.auth_level,
                        'auth_level_display': user.get_auth_level_display(),
                        'department': user.department,
                        'position': user.position,
                    }
                }
            
            # 로그인 이력 기록
            ActivityLog.objects.create(
                user=user,
                action_type='login',
                description=f'로그인 (권한: {user.get_auth_level_display()})',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        return response
