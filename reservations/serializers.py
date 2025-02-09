from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from typing import Dict, Any

from .models import Customer, Pet, MemorialRoom, Reservation, ReservationHistory
from funeral.models import FuneralPackage
from funeral.serializers import FuneralPackageSerializer
from accounts.serializers import UserSerializer
from accounts.models import User


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
            'gender', 'gender_display', 'is_neutered', 'special_notes', 'created_at'
        ]


class MemorialRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemorialRoom
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
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_staff_id = serializers.IntegerField(source='assigned_staff.id', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.name', read_only=True)
    visit_route_display = serializers.CharField(source='get_visit_route_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'customer', 'pet', 
            'memorial_room_id', 'memorial_room_name',
            'package_id', 'package_name', 'package_price',
            'scheduled_at', 'status', 'status_display',
            'is_emergency', 'assigned_staff_id', 'assigned_staff_name',
            'visit_route', 'visit_route_display',
            'referral_hospital', 'need_death_certificate', 'created_at'
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


class ReservationDetailSerializer(serializers.ModelSerializer):
    """예약 상세 정보 시리얼라이저"""
    customer = CustomerSerializer(read_only=True)
    pet = PetSerializer(read_only=True)
    package = FuneralPackageSerializer(read_only=True)
    package_id = serializers.PrimaryKeyRelatedField(source='package', read_only=True)
    memorial_room_id = serializers.PrimaryKeyRelatedField(source='memorial_room', read_only=True)
    assigned_staff = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_route_display = serializers.CharField(source='get_visit_route_display', read_only=True)
    histories = ReservationHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'customer', 'pet', 'package', 'package_id', 'memorial_room_id',
            'scheduled_at', 'status', 'status_display',
            'assigned_staff', 'is_emergency', 'visit_route',
            'visit_route_display', 'referral_hospital',
            'need_death_certificate', 'custom_requests',
            'created_by', 'created_at', 'updated_at',
            'histories'
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
        queryset=FuneralPackage.objects.all()
    )
    memorial_room_id = serializers.PrimaryKeyRelatedField(
        source='memorial_room',
        queryset=MemorialRoom.objects.all()
    )
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
            'scheduled_at', 'assigned_staff_id', 'is_emergency',
            'visit_route', 'referral_hospital',
            'need_death_certificate', 'custom_requests'
        ]

    def create(self, validated_data: Dict[str, Any]) -> Reservation:
        customer_data = validated_data.pop('customer')
        pet_data = validated_data.pop('pet')
        memorial_room = validated_data.get('memorial_room')  # source='memorial_room'으로 인해 이렇게 접근

        print(f"Validated data: {validated_data}")  # 디버그용
        print(f"Memorial room: {memorial_room}")    # 디버그용

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
                'memorial_room': memorial_room  # 명시적으로 추가
            })
            
            reservation = Reservation.objects.create(**validated_data)

            # 예약 이력 생성
            ReservationHistory.objects.create(
                reservation=reservation,
                from_status=Reservation.STATUS_PENDING,
                to_status=Reservation.STATUS_PENDING,
                changed_by=self.context['request'].user,
                notes='예약 생성'
            )

            return reservation


class ReservationUpdateSerializer(serializers.ModelSerializer):
    """예약 수정용 시리얼라이저"""
    package_id = serializers.PrimaryKeyRelatedField(
        source='package',
        queryset=FuneralPackage.objects.all(),
        required=False
    )
    memorial_room_id = serializers.PrimaryKeyRelatedField(
        source='memorial_room',
        queryset=MemorialRoom.objects.all(),
        required=False
    )
    assigned_staff_id = serializers.PrimaryKeyRelatedField(
        source='assigned_staff',
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Reservation
        fields = [
            'memorial_room_id', 'package_id',
            'scheduled_at', 'assigned_staff_id', 'is_emergency',
            'visit_route', 'referral_hospital',
            'need_death_certificate', 'custom_requests'
        ]

    def update(self, instance: Reservation, validated_data: Dict[str, Any]) -> Reservation:
        print(f"Update validated data: {validated_data}")  # 디버그용

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

            return instance 