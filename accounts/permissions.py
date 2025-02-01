from rest_framework import permissions
from .models import User

class IsSuperAdmin(permissions.BasePermission):
    """
    슈퍼관리자 권한을 확인하는 퍼미션 클래스
    """
    def has_permission(self, request, view):
        return request.user.auth_level == User.LEVEL_SUPERADMIN

class IsAdmin(permissions.BasePermission):
    """
    관리자 이상의 권한을 확인하는 퍼미션 클래스
    """
    def has_permission(self, request, view):
        return request.user.auth_level >= User.LEVEL_ADMIN

class IsInstructor(permissions.BasePermission):
    """
    지도사 이상의 권한을 확인하는 퍼미션 클래스
    """
    def has_permission(self, request, view):
        return request.user.auth_level >= User.LEVEL_INSTRUCTOR

class IsOwnerOrHigherLevel(permissions.BasePermission):
    """
    본인이거나 더 높은 권한을 가진 사용자만 접근 가능
    """
    def has_object_permission(self, request, view, obj):
        # 본인인 경우
        if obj.id == request.user.id:
            return True
        # 대상보다 높은 권한을 가진 경우
        return request.user.auth_level > obj.auth_level
