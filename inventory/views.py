from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from django.utils import timezone
from .models import (
    Category, Supplier, InventoryItem, StockMovement,
    PurchaseOrder, PurchaseOrderItem
)
from .serializers import (
    CategorySerializer, SupplierSerializer, InventoryItemSerializer,
    StockMovementSerializer, PurchaseOrderListSerializer,
    PurchaseOrderDetailSerializer, PurchaseOrderCreateSerializer,
    PurchaseOrderUpdateSerializer, PurchaseOrderItemSerializer
)
import logging
from django.db import transaction

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"Category creation attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.info(f"Successfully created category: {serializer.data.get('name')}")
            return Response(
                {
                    "status": "success",
                    "message": "카테고리가 성공적으로 생성되었습니다.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to create category. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "카테고리 생성 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Category update attempt for {instance.name} with data: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"Successfully updated category: {serializer.data.get('name')}")
            return Response(
                {
                    "status": "success",
                    "message": "카테고리가 성공적으로 수정되었습니다.",
                    "data": serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Failed to update category. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "카테고리 수정 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Category deletion attempt for: {instance.name}")
        
        try:
            self.perform_destroy(instance)
            logger.info(f"Successfully deleted category: {instance.name}")
            return Response(
                {
                    "status": "success",
                    "message": "카테고리가 성공적으로 삭제되었습니다."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Failed to delete category. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "카테고리 삭제 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'contact_name', 'phone', 'email']

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"Supplier creation attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.info(f"Successfully created supplier: {serializer.data.get('name')}")
            return Response(
                {
                    "status": "success",
                    "message": "공급업체가 성공적으로 생성되었습니다.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to create supplier. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "공급업체 생성 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Supplier update attempt for {instance.name} with data: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"Successfully updated supplier: {serializer.data.get('name')}")
            return Response(
                {
                    "status": "success",
                    "message": "공급업체가 성공적으로 수정되었습니다.",
                    "data": serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Failed to update supplier. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "공급업체 수정 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Supplier deletion attempt for: {instance.name}")
        
        try:
            self.perform_destroy(instance)
            logger.info(f"Successfully deleted supplier: {instance.name}")
            return Response(
                {
                    "status": "success",
                    "message": "공급업체가 성공적으로 삭제되었습니다."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Failed to delete supplier. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "공급업체 삭제 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'supplier']
    search_fields = ['name', 'code']

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"Inventory item creation attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.info(f"Successfully created inventory item: {serializer.data.get('name')}")
            return Response(
                {
                    "status": "success",
                    "message": "재고 항목이 성공적으로 생성되었습니다.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to create inventory item. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "재고 항목 생성 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Inventory item update attempt for {instance.name} with data: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"Successfully updated inventory item: {serializer.data.get('name')}")
            return Response(
                {
                    "status": "success",
                    "message": "재고 항목이 성공적으로 수정되었습니다.",
                    "data": serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Failed to update inventory item. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "재고 항목 수정 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Inventory item deletion attempt for: {instance.name}")
        
        try:
            self.perform_destroy(instance)
            logger.info(f"Successfully deleted inventory item: {instance.name}")
            return Response(
                {
                    "status": "success",
                    "message": "재고 항목이 성공적으로 삭제되었습니다."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Failed to delete inventory item. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "재고 항목 삭제 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        logger = logging.getLogger(__name__)
        logger.info("Low stock items check requested")
        
        try:
            items = self.get_queryset().filter(
                current_stock__lte=F('minimum_stock')
            )
            serializer = self.get_serializer(items, many=True)
            logger.info(f"Found {len(items)} items with low stock")
            return Response(
                {
                    "status": "success",
                    "message": "저장량 부족 항목 조회 성공",
                    "data": serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Failed to check low stock items. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "저장량 부족 항목 조회 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='adjust-stock')
    def adjust_stock(self, request, pk=None):
        logger = logging.getLogger(__name__)
        item = self.get_object()
        logger.info(f"Stock adjustment attempt for {item.name} with data: {request.data}")
        
        quantity = request.data.get('quantity', 0)
        notes = request.data.get('notes', '')
        
        if quantity == 0:
            logger.error("Quantity is required for stock adjustment")
            return Response(
                {'error': '수량을 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 재고 이동 기록 생성
            movement_type = 'adjust'
            StockMovement.objects.create(
                item=item,
                movement_type=movement_type,
                quantity=quantity,
                unit_price=item.unit_price,
                notes=notes,
                employee=request.user
            )
            
            # 재고 수량 업데이트
            item.current_stock += quantity
            item.save()
            
            logger.info(f"Successfully adjusted stock for {item.name}")
            return Response({
                'status': 'success',
                'current_stock': item.current_stock
            })
        except Exception as e:
            logger.error(f"Failed to adjust stock for {item.name}. Error: {str(e)}")
            return Response({
                'status': 'error',
                'message': '재고 조정 중 오류가 발생했습니다.',
                'error_details': str(e)
            },
                status=status.HTTP_400_BAD_REQUEST
            )


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['item', 'movement_type']
    search_fields = ['reference_number', 'notes']

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"Stock movement creation attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.info(f"Successfully created stock movement: {serializer.data.get('reference_number')}")
            return Response(
                {
                    "status": "success",
                    "message": "재고 이동 기록이 성공적으로 생성되었습니다.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to create stock movement. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "재고 이동 기록 생성 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Stock movement update attempt for {instance.reference_number} with data: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"Successfully updated stock movement: {serializer.data.get('reference_number')}")
            return Response(
                {
                    "status": "success",
                    "message": "재고 이동 기록이 성공적으로 수정되었습니다.",
                    "data": serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Failed to update stock movement. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "재고 이동 기록 수정 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Stock movement deletion attempt for: {instance.reference_number}")
        
        try:
            self.perform_destroy(instance)
            logger.info(f"Successfully deleted stock movement: {instance.reference_number}")
            return Response(
                {
                    "status": "success",
                    "message": "재고 이동 기록이 성공적으로 삭제되었습니다."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Failed to delete stock movement. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "재고 이동 기록 삭제 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        logger = logging.getLogger(__name__)
        movement = serializer.save(employee=self.request.user)
        
        # 재고 수량 업데이트
        item = movement.item
        if movement.movement_type in ['in', 'adjust']:
            item.current_stock += movement.quantity
        elif movement.movement_type in ['out', 'return']:
            item.current_stock -= movement.quantity
        item.save()
        logger.info(f"Successfully updated stock for {item.name}")


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'supplier']
    search_fields = ['order_number', 'notes']

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        elif self.action == 'create':
            return PurchaseOrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PurchaseOrderUpdateSerializer
        return PurchaseOrderDetailSerializer

    def list(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data)
            logger.info(f"Purchase orders list response: {response_data.data}")
            return response_data
            
        serializer = self.get_serializer(queryset, many=True)
        response_data = Response(serializer.data)
        logger.info(f"Purchase orders list response: {response_data.data}")
        return response_data

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"Purchase order creation attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.info(f"Successfully created purchase order: {serializer.data.get('order_number')}")
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 생성되었습니다.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to create purchase order. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "발주서 생성 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Purchase order update attempt for {instance.order_number} with data: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"Successfully updated purchase order: {instance.order_number}")
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 수정되었습니다.",
                    "data": serializer.data
                }
            )
        except serializers.ValidationError as e:
            logger.error(f"Validation error while updating purchase order {instance.order_number}. Error: {str(e)}")
            logger.error(f"Current status: {instance.status}, Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "발주서 수정 중 유효성 검증 오류가 발생했습니다.",
                    "error_details": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error while updating purchase order {instance.order_number}. Error: {str(e)}")
            logger.error(f"Request data: {request.data}")
            return Response(
                {
                    "status": "error",
                    "message": "발주서 수정 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        logger.info(f"Purchase order deletion attempt for: {instance.order_number}")
        
        try:
            self.perform_destroy(instance)
            logger.info(f"Successfully deleted purchase order: {instance.order_number}")
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 삭제되었습니다."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Failed to delete purchase order. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "발주서 삭제 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        
        logger.info(f"Attempting to approve purchase order: {instance.order_number}")
        
        if instance.status != 'pending':
            return Response(
                {
                    "status": "error",
                    "message": "승인 대기 상태의 발주서만 승인할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            instance.status = 'approved'
            instance.approved_by = request.user
            instance.approved_at = timezone.now()
            instance.save()
            
            logger.info(f"Successfully approved purchase order: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 승인되었습니다.",
                    "data": PurchaseOrderDetailSerializer(instance).data
                }
            )
        except Exception as e:
            logger.error(f"Failed to approve purchase order {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "발주서 승인 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        
        logger.info(f"Attempting to mark purchase order as received: {instance.order_number}")
        
        if instance.status != 'ordered':
            return Response(
                {
                    "status": "error",
                    "message": "발주 처리된 발주서만 입고 완료 처리할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # 트랜잭션으로 처리하여 데이터 일관성 보장
            with transaction.atomic():
                # 재고 수량 업데이트
                for item in instance.items.all():
                    inventory_item = item.item
                    inventory_item.current_stock += item.quantity
                    inventory_item.save()
                    
                    # 입고 이력 생성
                    StockMovement.objects.create(
                        item=inventory_item,
                        quantity=item.quantity,
                        movement_type='in',
                        reference_number=instance.order_number,
                        employee=request.user,
                        notes=f'발주서 {instance.order_number} 입고',
                        unit_price=item.unit_price
                    )
                
                # 발주서 상태 업데이트
                instance.status = 'received'
                instance.received_at = timezone.now()
                instance.received_by = request.user
                instance.save()
            
            logger.info(f"Successfully marked purchase order as received: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 입고 완료 처리되었습니다.",
                    "data": PurchaseOrderDetailSerializer(instance).data
                }
            )
        except Exception as e:
            logger.error(f"Failed to mark purchase order as received {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "입고 완료 처리 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        
        logger.info(f"Attempting to cancel purchase order: {instance.order_number}")
        
        if instance.status == 'cancelled':
            return Response(
                {
                    "status": "error",
                    "message": "이미 취소된 발주서입니다."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if instance.status == 'received':
            return Response(
                {
                    "status": "error",
                    "message": "입고 완료된 발주서는 취소할 수 없습니다."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            instance.status = 'cancelled'
            instance.save()
            logger.info(f"Successfully cancelled purchase order: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 취소되었습니다.",
                    "data": PurchaseOrderDetailSerializer(instance).data
                }
            )
        except Exception as e:
            logger.error(f"Failed to cancel purchase order {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "발주서 취소 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def order(self, request, pk=None):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        
        logger.info(f"Attempting to process order for purchase order: {instance.order_number}")
        
        if instance.status != 'approved':
            return Response(
                {
                    "status": "error",
                    "message": "승인된 발주서만 발주 처리할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            instance.status = 'ordered'
            instance.order_date = timezone.now().date()
            instance.save()
            
            logger.info(f"Successfully processed order for purchase order: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 발주 처리되었습니다.",
                    "data": PurchaseOrderDetailSerializer(instance).data
                }
            )
        except Exception as e:
            logger.error(f"Failed to process order for purchase order {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "발주 처리 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def pending(self, request, pk=None):
        logger = logging.getLogger(__name__)
        instance = self.get_object()
        
        logger.info(f"Attempting to change purchase order to pending status: {instance.order_number}")
        
        if instance.status != 'draft':
            return Response(
                {
                    "status": "error",
                    "message": "임시저장 상태의 발주서만 승인 요청할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            instance.status = 'pending'
            instance.save()
            
            logger.info(f"Successfully changed purchase order to pending status: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 승인 요청되었습니다.",
                    "data": PurchaseOrderDetailSerializer(instance).data
                }
            )
        except Exception as e:
            logger.error(f"Failed to change purchase order to pending status {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "승인 요청 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
