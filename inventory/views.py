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
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderHistory
)
from .serializers import (
    CategorySerializer, SupplierSerializer, InventoryItemSerializer,
    StockMovementSerializer, PurchaseOrderListSerializer,
    PurchaseOrderDetailSerializer, PurchaseOrderCreateSerializer,
    PurchaseOrderUpdateSerializer, PurchaseOrderItemSerializer
)
from utils.telegram import send_telegram_message, format_purchase_order_message
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
            instance = self.perform_create(serializer)
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
            instance = self.perform_create(serializer)
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
            instance = self.perform_create(serializer)
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
            instance = self.perform_create(serializer)
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
    serializer_class = PurchaseOrderDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'supplier']
    search_fields = ['order_number']

    def get_queryset(self):
        logger = logging.getLogger(__name__)
        logger.debug("Getting purchase orders queryset")
        
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'supplier', 'created_by', 'approved_by', 
            'ordered_by', 'received_by'
        ).prefetch_related('items', 'items__item', 'histories')
        
        logger.debug(f"Queryset SQL: {str(queryset.query)}")
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseOrderCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return PurchaseOrderUpdateSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        try:
            logger.debug("Processing purchase orders list request")
            logger.debug(f"Query params: {request.query_params}")
            
            queryset = self.filter_queryset(self.get_queryset())
            
            # id와 include_details가 있으면 상세 정보를 반환
            order_id = request.query_params.get('id')
            include_details = request.query_params.get('include_details') == 'true'
            
            if order_id and include_details:
                try:
                    instance = queryset.get(id=order_id)
                    serializer = PurchaseOrderDetailSerializer(instance)
                    return Response(serializer.data)
                except PurchaseOrder.DoesNotExist:
                    return Response(
                        {"message": "발주서를 찾을 수 없습니다."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # 일반 목록 조회
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = PurchaseOrderListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = PurchaseOrderListSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in list view: {str(e)}", exc_info=True)
            return Response(
                {
                    "status": "error",
                    "message": "발주서 목록을 조회하는 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        logger = logging.getLogger(__name__)
        instance = serializer.save(created_by=self.request.user)
        return instance

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"Purchase order creation attempt with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            instance = self.perform_create(serializer)
            
            # 텔레그램 알림 발송
            message = format_purchase_order_message(instance, 'created')
            send_telegram_message(message)
            
            logger.info(f"Successfully created purchase order: {instance.order_number}")
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 성공적으로 생성되었습니다.",
                    "data": PurchaseOrderDetailSerializer(instance).data
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
        instance = self.get_object()
        logger = logging.getLogger(__name__)
        
        logger.info(f"Attempting to delete purchase order: {instance.order_number}")
        
        if instance.status not in ['draft', 'cancelled']:
            return Response(
                {
                    "status": "error",
                    "message": "임시저장 또는 취소된 발주서만 삭제할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # 텔레그램 알림 발송
            message = format_purchase_order_message(instance, 'cancelled')
            send_telegram_message(message)
            
            instance.delete()
            
            logger.info(f"Successfully deleted purchase order: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 삭제되었습니다."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Failed to delete purchase order {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "삭제 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _record_status_change(self, instance, from_status, to_status, notes=''):
        change_mapping = {
            ('draft', 'pending'): 'draft_to_pending',
            ('pending', 'approved'): 'pending_to_approved',
            ('approved', 'ordered'): 'approved_to_ordered',
            ('ordered', 'received'): 'ordered_to_received',
        }
        
        # 취소 상태로 변경되는 경우
        if to_status == 'cancelled':
            change_type = 'to_cancelled'
        else:
            change_type = change_mapping.get((from_status, to_status))
            
        if not change_type:
            return
            
        PurchaseOrderHistory.objects.create(
            purchase_order=instance,
            from_status=from_status,
            to_status=to_status,
            change_type=change_type,
            changed_by=self.request.user,
            notes=notes
        )

    @action(detail=True, methods=['post'])
    def pending(self, request, pk=None):
        instance = self.get_object()
        logger = logging.getLogger(__name__)
        
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
            from_status = instance.status
            instance.status = 'pending'
            instance.save()
            
            self._record_status_change(instance, from_status, 'pending')
            
            # 텔레그램 알림 발송
            message = format_purchase_order_message(instance, 'pending')
            send_telegram_message(message)
            
            logger.info(f"Successfully changed purchase order to pending status: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 승인 요청되었습니다.",
                    "data": {
                        "id": instance.id,
                        "order_number": instance.order_number,
                        "status": instance.status,
                        "status_display": instance.get_status_display()
                    }
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

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        instance = self.get_object()
        logger = logging.getLogger(__name__)
        
        logger.info(f"Attempting to approve purchase order: {instance.order_number}")
        
        if instance.status != 'pending':
            return Response(
                {
                    "status": "error",
                    "message": "승인대기 상태의 발주서만 승인할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from_status = instance.status
            instance.status = 'approved'
            instance.approved_by = request.user
            instance.approved_at = timezone.now()
            instance.save()
            
            self._record_status_change(instance, from_status, 'approved')
            
            # 텔레그램 알림 발송
            message = format_purchase_order_message(instance, 'approved')
            send_telegram_message(message)
            
            logger.info(f"Successfully approved purchase order: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 승인되었습니다.",
                    "data": {
                        "id": instance.id,
                        "order_number": instance.order_number,
                        "status": instance.status,
                        "status_display": instance.get_status_display()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to approve purchase order {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "승인 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def order(self, request, pk=None):
        instance = self.get_object()
        logger = logging.getLogger(__name__)
        
        logger.info(f"Attempting to order purchase order: {instance.order_number}")
        
        if instance.status != 'approved':
            return Response(
                {
                    "status": "error",
                    "message": "승인완료 상태의 발주서만 발주할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from_status = instance.status
            instance.status = 'ordered'
            instance.ordered_by = request.user
            instance.ordered_at = timezone.now()
            instance.save()
            
            self._record_status_change(instance, from_status, 'ordered')
            
            # 텔레그램 알림 발송
            message = format_purchase_order_message(instance, 'ordered')
            send_telegram_message(message)
            
            logger.info(f"Successfully ordered purchase order: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 발주되었습니다.",
                    "data": {
                        "id": instance.id,
                        "order_number": instance.order_number,
                        "status": instance.status,
                        "status_display": instance.get_status_display()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to order purchase order {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "발주 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        instance = self.get_object()
        
        if instance.status != 'ordered':
            return Response(
                {
                    "status": "error",
                    "message": "발주완료 상태의 발주서만 입고할 수 있습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from_status = instance.status
            
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
                instance.received_by = request.user
                instance.received_at = timezone.now()
                instance.save()
                
                # 상태 변경 이력 기록
                self._record_status_change(instance, from_status, 'received')
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 입고되었습니다.",
                    "data": {
                        "id": instance.id,
                        "order_number": instance.order_number,
                        "status": instance.status,
                        "status_display": instance.get_status_display()
                    }
                }
            )
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": "입고 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        logger = logging.getLogger(__name__)
        
        logger.info(f"Attempting to cancel purchase order: {instance.order_number}")
        
        if instance.status in ['received', 'cancelled']:
            return Response(
                {
                    "status": "error",
                    "message": "입고완료 또는 취소된 발주서는 취소할 수 없습니다.",
                    "current_status": instance.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from_status = instance.status
            instance.status = 'cancelled'
            instance.save()
            
            self._record_status_change(instance, from_status, 'cancelled')
            
            # 텔레그램 알림 발송
            message = format_purchase_order_message(instance, 'cancelled')
            send_telegram_message(message)
            
            logger.info(f"Successfully cancelled purchase order: {instance.order_number}")
            
            return Response(
                {
                    "status": "success",
                    "message": "발주서가 취소되었습니다.",
                    "data": {
                        "id": instance.id,
                        "order_number": instance.order_number,
                        "status": instance.status,
                        "status_display": instance.get_status_display()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to cancel purchase order {instance.order_number}. Error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "취소 중 오류가 발생했습니다.",
                    "error_details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
