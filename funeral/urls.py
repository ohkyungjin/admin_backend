from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'packages', views.FuneralPackageViewSet)
router.register(r'package-items', views.PackageItemViewSet)
router.register(r'premium-lines', views.PremiumLineViewSet)
router.register(r'additional-options', views.AdditionalOptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
