from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import MemorialRoom
from .serializers import MemorialRoomSerializer

# Create your views here.

class MemorialRoomViewSet(viewsets.ModelViewSet):
    queryset = MemorialRoom.objects.all()
    serializer_class = MemorialRoomSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'notes']
