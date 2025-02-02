from rest_framework import serializers
from .models import Category, Supplier, InventoryItem, StockMovement, PurchaseOrder, PurchaseOrderItem, PurchaseOrderHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class InventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = InventoryItem
        fields = '__all__'


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ('created_at',)


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'item_name', 'item_code', 'quantity',
            'unit_price', 'total_price', 'received_quantity',
            'notes', 'order', 'item'
        ]


class PurchaseOrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ('item', 'quantity', 'unit_price')


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name')
    status_display = serializers.CharField(source='get_status_display')
    created_by_name = serializers.CharField(source='created_by.name')
    items_info = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier_name',
            'order_date', 'expected_date', 'status', 'status_display',
            'total_amount', 'created_at', 'created_by_name',
            'items_info', 'notes'
        ]

    def get_items_info(self, obj):
        return [
            {
                'name': item.item.name,
                'code': item.item.code,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total_price': item.total_price
            } for item in obj.items.all()
        ]


class PurchaseOrderHistorySerializer(serializers.ModelSerializer):
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.name', read_only=True)

    class Meta:
        model = PurchaseOrderHistory
        fields = [
            'id', 'purchase_order',
            'from_status', 'from_status_display',
            'to_status', 'to_status_display',
            'changed_by', 'changed_by_name',
            'notes', 'created_at'
        ]


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier = SupplierSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True)
    ordered_by_name = serializers.CharField(source='ordered_by.name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.name', read_only=True)
    histories = PurchaseOrderHistorySerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'order_date', 'expected_date',
            'status', 'status_display', 'total_amount', 'notes',
            'created_by', 'created_by_name', 'created_at',
            'approved_by', 'approved_by_name', 'approved_at',
            'ordered_by', 'ordered_by_name', 'ordered_at',
            'received_by', 'received_by_name', 'received_at',
            'items', 'histories'
        ]


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemCreateSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ('supplier', 'expected_date', 'notes', 'items')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        validated_data['created_by'] = self.context['request'].user
        validated_data['order_number'] = self._generate_order_number()
        
        order = PurchaseOrder.objects.create(**validated_data)
        
        total_amount = 0
        for item_data in items_data:
            item_data['total_price'] = item_data['quantity'] * item_data['unit_price']
            total_amount += item_data['total_price']
            PurchaseOrderItem.objects.create(order=order, **item_data)
        
        order.total_amount = total_amount
        order.save()
        
        return order

    def _generate_order_number(self):
        import datetime
        prefix = 'PO'
        date = datetime.datetime.now().strftime('%Y%m%d')
        last_order = PurchaseOrder.objects.filter(
            order_number__startswith=f'{prefix}{date}'
        ).order_by('order_number').last()
        
        if last_order:
            last_number = int(last_order.order_number[-4:])
            new_number = str(last_number + 1).zfill(4)
        else:
            new_number = '0001'
        
        return f'{prefix}{date}{new_number}'


class PurchaseOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ('expected_date', 'notes', 'status')

    def validate_status(self, value):
        instance = getattr(self, 'instance', None)
        if instance and instance.status == 'cancelled':
            raise serializers.ValidationError("취소된 발주서는 수정할 수 없습니다.")
        if instance and instance.status == 'received':
            raise serializers.ValidationError("입고 완료된 발주서는 수정할 수 없습니다.")
        return value 