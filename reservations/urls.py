from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, PetViewSet, MemorialRoomViewSet,
    ReservationViewSet
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'pets', PetViewSet)
router.register(r'memorial-rooms', MemorialRoomViewSet)
router.register(r'reservations', ReservationViewSet, basename='reservations')

urlpatterns = [
    path('available-times/', ReservationViewSet.as_view({'get': 'available_times'}), name='available-times'),
    path('', include(router.urls)),
] 