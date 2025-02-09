from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MemorialRoomViewSet

router = DefaultRouter()
router.register(r'rooms', MemorialRoomViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 