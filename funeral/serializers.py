from rest_framework import serializers
from .models import (
    FuneralPackage, PackageItem, PackageItemOption,
    PremiumLine, PremiumLineItem, AdditionalOption
)
from inventory.models import Category, InventoryItem
from inventory.serializers import CategorySerializer, InventoryItemSerializer


class PackageItemOptionSerializer(serializers.ModelSerializer):
    item = InventoryItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=InventoryItem.objects.all(),
        source='item'
    )

    class Meta:
        model = PackageItemOption
        fields = ['id', 'item', 'item_id', 'additional_price', 'is_active']


class PackageItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=Category.objects.all(),
        source='category'
    )
    default_item = InventoryItemSerializer(read_only=True)
    default_item_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=InventoryItem.objects.all(),
        source='default_item'
    )
    options = PackageItemOptionSerializer(many=True, read_only=True)

    class Meta:
        model = PackageItem
        fields = [
            'id', 'category', 'category_id', 'default_item', 
            'default_item_id', 'is_required', 'options'
        ]


class FuneralPackageSerializer(serializers.ModelSerializer):
    items = PackageItemSerializer(many=True, read_only=True)
    items_data = PackageItemSerializer(many=True, write_only=True, required=False)
    price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        source='base_price', 
        required=True,
        coerce_to_string=False
    )

    class Meta:
        model = FuneralPackage
        fields = ['id', 'name', 'description', 'price', 'is_active', 'items', 'items_data']
        extra_kwargs = {
            'base_price': {'write_only': True}
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # items_data의 초기값을 현재 items로 설정
        items_data = []
        for item in instance.items.all():
            items_data.append({
                'category_id': item.category.id,
                'default_item_id': item.default_item.id,
                'is_required': item.is_required
            })
        ret['items_data'] = items_data
        return ret

    def create(self, validated_data):
        items_data = validated_data.pop('items_data', [])
        package = FuneralPackage.objects.create(**validated_data)
        
        for item_data in items_data:
            PackageItem.objects.create(package=package, **item_data)
        
        return package

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items_data', [])
        instance = super().update(instance, validated_data)
        
        if items_data:
            instance.items.all().delete()  # 기존 아이템 삭제
            for item_data in items_data:
                PackageItem.objects.create(package=instance, **item_data)
        
        return instance


class PremiumLineItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=Category.objects.all(),
        source='category'
    )
    item = InventoryItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=InventoryItem.objects.all(),
        source='item'
    )

    class Meta:
        model = PremiumLineItem
        fields = ['id', 'category', 'category_id', 'item', 'item_id']


class PremiumLineSerializer(serializers.ModelSerializer):
    items = PremiumLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = PremiumLine
        fields = ['id', 'name', 'description', 'price', 'is_active', 'items']


class AdditionalOptionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=Category.objects.all(),
        source='category',
        required=False,
        allow_null=True
    )

    class Meta:
        model = AdditionalOption
        fields = [
            'id', 'name', 'description', 'price', 
            'category', 'category_id', 'is_active'
        ]
