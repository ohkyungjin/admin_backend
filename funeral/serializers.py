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
    price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        source='base_price', 
        required=True
    )

    class Meta:
        model = FuneralPackage
        fields = ['id', 'name', 'description', 'price', 'is_active', 'items']
        extra_kwargs = {
            'base_price': {'write_only': True}
        }


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
