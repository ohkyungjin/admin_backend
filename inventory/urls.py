from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, SupplierViewSet, InventoryItemViewSet,
    StockMovementViewSet, PurchaseOrderViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'movements', StockMovementViewSet)
router.register(r'orders', PurchaseOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 