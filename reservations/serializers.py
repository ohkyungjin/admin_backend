from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from typing import Dict, Any

from .models import (
    Customer, Pet, MemorialRoom, Reservation,
    ReservationHistory, ReservationInventoryItem
)
from funeral.models import FuneralPackage, PremiumLine, AdditionalOption
from funeral.serializers import FuneralPackageSerializer
from accounts.serializers import UserSerializer
from accounts.models import User
from memorial_rooms.models import MemorialRoom as MemorialRoomModel
from inventory.models import InventoryItem
from inventory.serializers import InventoryItemSerializer


class CustomerSerializer(serializers.ModelSerializer):
    """고객 정보 시리얼라이저"""
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'address', 'created_at']


class PetListSerializer(serializers.ModelSerializer):
    """반려동물 목록 조회용 시리얼라이저"""
    death_reason_display = serializers.CharField(source='get_death_reason_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'species', 'breed', 'age', 
            'weight', 'death_date', 'death_reason', 'death_reason_display',
            'gender', 'gender_display', 'is_neutered'
        ]


class PetSerializer(serializers.ModelSerializer):
    """반려동물 상세 정보 시리얼라이저"""
    death_reason_display = serializers.CharField(source='get_death_reason_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        write_only=True,
        required=False,
        source='customer'
    )

    class Meta:
        model = Pet
        fields = [
            'id', 'customer', 'customer_id', 'name', 'species', 'breed', 'age', 
            'weight', 'death_date', 'death_reason', 'death_reason_display',
            'gender', 'gender_display', 'is_neutered', 'created_at'
        ]


class MemorialRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemorialRoomModel
        fields = ['id', 'name', 'capacity', 'description', 'is_active']


class ReservationHistorySerializer(serializers.ModelSerializer):
    """예약 이력 시리얼라이저"""
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    changed_by = UserSerializer(read_only=True)

    class Meta:
        model = ReservationHistory
        fields = [
            'id', 'from_status', 'from_status_display',
            'to_status', 'to_status_display',
            'changed_by', 'notes', 'created_at'
        ]


class PremiumLineSerializer(serializers.ModelSerializer):
    """프리미엄 라인 시리얼라이저"""
    class Meta:
        model = PremiumLine
        fields = ['id', 'name', 'price', 'is_active']


class AdditionalOptionSerializer(serializers.ModelSerializer):
    """추가 옵션 시리얼라이저"""
    class Meta:
        model = AdditionalOption
        fields = ['id', 'name', 'price', 'category', 'is_active']


class ReservationListSerializer(serializers.ModelSerializer):
    """예약 목록 조회용 시리얼라이저"""
    customer = CustomerSerializer(read_only=True)
    pet = PetListSerializer(read_only=True)
    memorial_room_id = serializers.IntegerField(source='memorial_room.id', read_only=True)
    memorial_room_name = serializers.CharField(source='memorial_room.name', read_only=True)
    package_id = serializers.IntegerField(source='package.id', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    package_price = serializers.DecimalField(
        source='package.base_price', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    premium_line = PremiumLineSerializer(read_only=True)
    additional_options = AdditionalOptionSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_route_display = serializers.CharField(source='get_visit_route_display', read_only=True)
    assigned_staff = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'customer', 'pet', 
            'memorial_room_id', 'memorial_room_name',
            'package_id', 'package_name', 'package_price',
            'premium_line', 'additional_options',
            'scheduled_at', 'status', 'status_display',
            'is_emergency', 'assigned_staff',
            'visit_route', 'visit_route_display',
            'referral_hospital', 'need_death_certificate', 'memo', 
            'created_by', 'created_at'
        ]

    def get_assigned_staff(self, obj):
        if obj.assigned_staff:
            return {
                'id': obj.assigned_staff.id,
                'name': obj.assigned_staff.name,
                'email': obj.assigned_staff.email,
                'phone': obj.assigned_staff.phone
            }
        return None

    def get_created_by(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'name': obj.created_by.name,
                'email': obj.created_by.email,
                'phone': obj.created_by.phone
            }
        return None

    def get_status_choices(self, obj) -> list:
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.STATUS_CHOICES
        ]

    def get_visit_route_choices(self, obj) -> list:
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.VISIT_ROUTE_CHOICES
        ]


class SimpleFuneralPackageSerializer(FuneralPackageSerializer):
    """간단한 장례 패키지 시리얼라이저"""
    class Meta(FuneralPackageSerializer.Meta):
        fields = ['id', 'name', 'base_price', 'is_active']


class ReservationInventoryItemSerializer(serializers.ModelSerializer):
    """예약에 사용된 재고 아이템 시리얼라이저"""
    inventory_item_detail = InventoryItemSerializer(source='inventory_item', read_only=True)
    
    class Meta:
        model = ReservationInventoryItem
        fields = ['id', 'inventory_item', 'inventory_item_detail', 'quantity']


class ReservationDetailSerializer(serializers.ModelSerializer):
    """예약 상세 정보 시리얼라이저"""
    customer = CustomerSerializer(read_only=True)
    pet = PetSerializer(read_only=True)
    package = SimpleFuneralPackageSerializer(read_only=True)
    package_id = serializers.PrimaryKeyRelatedField(source='package', read_only=True)
    premium_line = PremiumLineSerializer(read_only=True)
    additional_options = AdditionalOptionSerializer(many=True, read_only=True)
    memorial_room_id = serializers.PrimaryKeyRelatedField(source='memorial_room', read_only=True)
    assigned_staff = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_route_display = serializers.CharField(source='get_visit_route_display', read_only=True)
    histories = ReservationHistorySerializer(many=True, read_only=True)
    inventory_items_used = ReservationInventoryItemSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'customer', 'pet', 'package', 'package_id',
            'premium_line', 'additional_options',
            'memorial_room_id', 'scheduled_at', 'status', 'status_display',
            'assigned_staff', 'is_emergency', 'visit_route',
            'visit_route_display', 'referral_hospital',
            'need_death_certificate', 'memo',
            'created_by', 'created_at', 'updated_at',
            'histories', 'inventory_items_used'
        ]

    def get_status_choices(self, obj) -> list:
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.STATUS_CHOICES
        ]

    def get_visit_route_choices(self, obj) -> list:
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.VISIT_ROUTE_CHOICES
        ]


class ReservationCreateSerializer(serializers.ModelSerializer):
    """예약 생성용 시리얼라이저"""
    customer = CustomerSerializer()
    pet = PetSerializer()
    package_id = serializers.PrimaryKeyRelatedField(
        source='package',
        queryset=FuneralPackage.objects.all(),
        required=False,
        allow_null=True
    )
    premium_line_id = serializers.PrimaryKeyRelatedField(
        source='premium_line',
        queryset=PremiumLine.objects.all(),
        required=False,
        allow_null=True
    )
    additional_option_ids = serializers.PrimaryKeyRelatedField(
        source='additional_options',
        queryset=AdditionalOption.objects.all(),
        many=True,
        required=False
    )
    memorial_room_id = serializers.IntegerField(required=True)
    assigned_staff_id = serializers.PrimaryKeyRelatedField(
        source='assigned_staff',
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    inventory_items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Reservation
        fields = [
            'customer', 'pet', 'memorial_room_id', 'package_id',
            'premium_line_id', 'additional_option_ids',
            'scheduled_at', 'assigned_staff_id', 'is_emergency',
            'visit_route', 'referral_hospital',
            'need_death_certificate', 'memo', 'created_by',
            'inventory_items'
        ]

    def validate_memorial_room_id(self, value):
        """추모실 ID 유효성 검사"""
        try:
            memorial_room = MemorialRoomModel.objects.get(id=value)
            return value
        except MemorialRoomModel.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 추모실입니다.")

    def create(self, validated_data: Dict[str, Any]) -> Reservation:
        customer_data = validated_data.pop('customer')
        pet_data = validated_data.pop('pet')
        memorial_room_id = validated_data.pop('memorial_room_id')
        additional_options = validated_data.pop('additional_options', [])
        memo = validated_data.pop('memo', '')
        inventory_items_data = validated_data.pop('inventory_items', [])

        try:
            memorial_room = MemorialRoomModel.objects.get(id=memorial_room_id)
        except MemorialRoomModel.DoesNotExist:
            raise serializers.ValidationError({"memorial_room_id": "존재하지 않는 추모실입니다."})

        with transaction.atomic():
            # 고객 생성 또는 조회
            customer, _ = Customer.objects.get_or_create(
                phone=customer_data['phone'],
                defaults=customer_data
            )

            # 반려동물 생성
            pet = Pet.objects.create(customer=customer, **pet_data)

            # 예약 생성
            validated_data.update({
                'customer': customer,
                'pet': pet,
                'created_by': self.context['request'].user,
                'status': Reservation.STATUS_PENDING,
                'memorial_room': memorial_room,
                'memo': memo
            })
            
            reservation = Reservation.objects.create(**validated_data)

            # 추가 옵션 연결
            if additional_options:
                reservation.additional_options.set(additional_options)

            # 예약 이력 생성
            ReservationHistory.objects.create(
                reservation=reservation,
                from_status=Reservation.STATUS_PENDING,
                to_status=Reservation.STATUS_PENDING,
                changed_by=self.context['request'].user,
                notes=f'예약 생성 (접수자: {self.context["request"].user.name})'
            )

            # 재고 아이템 연결
            for item_data in inventory_items_data:
                try:
                    inventory_item = InventoryItem.objects.get(id=item_data['inventory_item_id'])
                    quantity = item_data['quantity']
                    
                    # 재고 수량 확인
                    if inventory_item.current_stock < quantity:
                        raise serializers.ValidationError(
                            f"재고 부족: {inventory_item.name}의 현재 재고({inventory_item.current_stock})가 "
                            f"요청 수량({quantity})보다 적습니다."
                        )
                    
                    ReservationInventoryItem.objects.create(
                        reservation=reservation,
                        inventory_item=inventory_item,
                        quantity=quantity
                    )
                except InventoryItem.DoesNotExist:
                    raise serializers.ValidationError(f"존재하지 않는 재고 아이템 ID: {item_data['inventory_item_id']}")

            return reservation


class ReservationUpdateSerializer(serializers.ModelSerializer):
    """예약 수정용 시리얼라이저"""
    customer = CustomerSerializer(required=False)
    pet = PetSerializer(required=False)
    package_id = serializers.PrimaryKeyRelatedField(
        source='package',
        queryset=FuneralPackage.objects.all(),
        required=False
    )
    premium_line_id = serializers.PrimaryKeyRelatedField(
        source='premium_line',
        queryset=PremiumLine.objects.all(),
        required=False,
        allow_null=True
    )
    additional_option_ids = serializers.PrimaryKeyRelatedField(
        source='additional_options',
        queryset=AdditionalOption.objects.all(),
        many=True,
        required=False
    )
    memorial_room_id = serializers.IntegerField(required=False)
    assigned_staff_id = serializers.PrimaryKeyRelatedField(
        source='assigned_staff',
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Reservation
        fields = [
            'customer', 'pet', 'memorial_room_id', 'package_id',
            'premium_line_id', 'additional_option_ids',
            'scheduled_at', 'assigned_staff_id', 'is_emergency',
            'visit_route', 'referral_hospital',
            'need_death_certificate', 'memo'
        ]

    def validate_memorial_room_id(self, value):
        """추모실 ID 유효성 검사"""
        try:
            memorial_room = MemorialRoomModel.objects.get(id=value)
            return value
        except MemorialRoomModel.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 추모실입니다.")

    def update(self, instance: Reservation, validated_data: Dict[str, Any]) -> Reservation:
        customer_data = validated_data.pop('customer', None)
        pet_data = validated_data.pop('pet', None)
        memorial_room_id = validated_data.pop('memorial_room_id', None)
        additional_options = validated_data.pop('additional_options', None)
        inventory_items_data = validated_data.pop('inventory_items', [])

        # 고객 정보 업데이트
        if customer_data:
            customer = instance.customer
            for attr, value in customer_data.items():
                setattr(customer, attr, value)
            customer.save()

        # 반려동물 정보 업데이트
        if pet_data:
            pet = instance.pet
            for attr, value in pet_data.items():
                setattr(pet, attr, value)
            pet.save()

        # 추모실 정보 업데이트
        if memorial_room_id:
            try:
                memorial_room = MemorialRoomModel.objects.get(id=memorial_room_id)
                validated_data['memorial_room'] = memorial_room
            except MemorialRoomModel.DoesNotExist:
                raise serializers.ValidationError({"memorial_room_id": "존재하지 않는 추모실입니다."})

        # 추가 옵션 업데이트
        if additional_options is not None:
            instance.additional_options.set(additional_options)

        with transaction.atomic():
            # 기본 필드 업데이트
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            instance.save()

            # 상태가 변경된 경우 이력 생성
            if 'status' in validated_data:
                ReservationHistory.objects.create(
                    reservation=instance,
                    from_status=instance.status,
                    to_status=validated_data['status'],
                    changed_by=self.context['request'].user,
                    notes='예약 상태 변경'
                )

            # 기존 재고 아이템 연결 삭제
            instance.inventory_items_used.all().delete()
            
            # 새로운 재고 아이템 연결
            for item_data in inventory_items_data:
                try:
                    inventory_item = InventoryItem.objects.get(id=item_data['inventory_item_id'])
                    quantity = item_data['quantity']
                    
                    # 재고 수량 확인
                    if inventory_item.current_stock < quantity:
                        raise serializers.ValidationError(
                            f"재고 부족: {inventory_item.name}의 현재 재고({inventory_item.current_stock})가 "
                            f"요청 수량({quantity})보다 적습니다."
                        )
                    
                    ReservationInventoryItem.objects.create(
                        reservation=instance,
                        inventory_item=inventory_item,
                        quantity=quantity
                    )
                except InventoryItem.DoesNotExist:
                    raise serializers.ValidationError(f"존재하지 않는 재고 아이템 ID: {item_data['inventory_item_id']}")

            return instance 