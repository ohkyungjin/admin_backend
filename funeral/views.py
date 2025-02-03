from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import logging
from .models import (
    FuneralPackage, PackageItem, PackageItemOption,
    PremiumLine, PremiumLineItem, AdditionalOption
)
from .serializers import (
    FuneralPackageSerializer, PackageItemSerializer, PackageItemOptionSerializer,
    PremiumLineSerializer, PremiumLineItemSerializer, AdditionalOptionSerializer
)

logger = logging.getLogger('funeral')


class FuneralPackageViewSet(viewsets.ModelViewSet):
    queryset = FuneralPackage.objects.prefetch_related(
        'items__options', 
        'items__category', 
        'items__default_item'
    ).all()
    serializer_class = FuneralPackageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        logger.debug('Executing get_queryset in FuneralPackageViewSet')
        for package in qs:
            logger.debug(f'Package {package.name} items count: {package.items.count()}')
            for item in package.items.all():
                logger.debug(f'  - Item: Category={item.category.name}, Default Item={item.default_item.name}')
        return qs

    def list(self, request, *args, **kwargs):
        logger.info('Listing funeral packages')
        logger.debug(f'Request Method: {request.method}')
        logger.debug(f'Request Headers: {request.headers}')
        logger.debug(f'Request Query Params: {request.query_params}')
        logger.debug(f'Request User: {request.user}')
        response = super().list(request, *args, **kwargs)
        logger.debug(f'Response Data: {response.data}')
        return response

    def create(self, request, *args, **kwargs):
        logger.info(f'Creating funeral package with data: {request.data}')
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        logger.info(f'Updating funeral package {kwargs.get("pk")} with data: {request.data}')
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        logger.info(f'Deleting funeral package {kwargs.get("pk")}')
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        logger.info(f'Adding item to funeral package {pk} with data: {request.data}')
        package = self.get_object()
        serializer = PackageItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(package=package)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f'Invalid data for adding item to package {pk}: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PackageItemViewSet(viewsets.ModelViewSet):
    queryset = PackageItem.objects.select_related(
        'category', 
        'default_item'
    ).prefetch_related('options').all()
    serializer_class = PackageItemSerializer

    def list(self, request, *args, **kwargs):
        logger.info('Listing package items')
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.info(f'Creating package item with data: {request.data}')
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_option(self, request, pk=None):
        logger.info(f'Adding option to package item {pk} with data: {request.data}')
        package_item = self.get_object()
        serializer = PackageItemOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(package_item=package_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f'Invalid data for adding option to package item {pk}: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PremiumLineViewSet(viewsets.ModelViewSet):
    queryset = PremiumLine.objects.prefetch_related(
        'items__category', 
        'items__item'
    ).all()
    serializer_class = PremiumLineSerializer

    def list(self, request, *args, **kwargs):
        logger.info('Listing premium lines')
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.info(f'Creating premium line with data: {request.data}')
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        logger.info(f'Adding item to premium line {pk} with data: {request.data}')
        premium_line = self.get_object()
        serializer = PremiumLineItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(premium_line=premium_line)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f'Invalid data for adding item to premium line {pk}: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdditionalOptionViewSet(viewsets.ModelViewSet):
    queryset = AdditionalOption.objects.select_related('category').all()
    serializer_class = AdditionalOptionSerializer

    def list(self, request, *args, **kwargs):
        logger.info('Listing additional options')
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.info(f'Creating additional option with data: {request.data}')
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        logger.info(f'Updating additional option {kwargs.get("pk")} with data: {request.data}')
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        logger.info(f'Deleting additional option {kwargs.get("pk")}')
        return super().destroy(request, *args, **kwargs)
