from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from .models import Customer, Pet, MemorialRoom, Reservation, ReservationHistory
from funeral.models import FuneralPackage
from funeral.serializers import FuneralPackageSerializer
from accounts.serializers import UserSerializer
from accounts.models import User


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'address', 'created_at']


class PetListSerializer(serializers.ModelSerializer):
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

    def create(self, validated_data):
        if 'customer' not in validated_data and 'customer_id' not in validated_data:
            raise serializers.ValidationError({"customer": "고객 정보는 필수입니다."})
        return super().create(validated_data)


class MemorialRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemorialRoom
        fields = ['id', 'name', 'capacity', 'description', 'is_active']


class ReservationHistorySerializer(serializers.ModelSerializer):
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
    customer = CustomerSerializer(read_only=True)
    pet = PetListSerializer(read_only=True)
    memorial_room_name = serializers.CharField(source='memorial_room.name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    package_price = serializers.DecimalField(source='package.base_price', max_digits=10, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.name', read_only=True)
    visit_route_display = serializers.CharField(source='get_visit_route_display', read_only=True)
    visit_route_choices = serializers.SerializerMethodField()
    status_choices = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'customer', 'pet', 
            'memorial_room_name', 'package_name', 'package_price',
            'scheduled_at', 'status', 'status_display', 'status_choices',
            'is_emergency', 'assigned_staff_name', 
            'visit_route', 'visit_route_display', 'visit_route_choices',
            'referral_hospital', 'need_death_certificate', 'created_at'
        ]

    def get_visit_route_choices(self, obj):
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.VISIT_ROUTE_CHOICES
        ]

    def get_status_choices(self, obj):
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.STATUS_CHOICES
        ]


class ReservationDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    pet = PetSerializer(read_only=True)
    package = FuneralPackageSerializer(read_only=True)
    memorial_room = MemorialRoomSerializer(read_only=True)
    assigned_staff = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_route_display = serializers.CharField(source='get_visit_route_display', read_only=True)
    histories = ReservationHistorySerializer(many=True, read_only=True)
    visit_route_choices = serializers.SerializerMethodField()
    status_choices = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'customer', 'pet', 'package', 'memorial_room',
            'scheduled_at', 'status', 'status_display', 'status_choices',
            'assigned_staff', 'is_emergency', 'visit_route',
            'visit_route_display', 'visit_route_choices', 'referral_hospital',
            'need_death_certificate', 'custom_requests',
            'created_by', 'created_at', 'updated_at',
            'histories'
        ]

    def get_visit_route_choices(self, obj):
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.VISIT_ROUTE_CHOICES
        ]

    def get_status_choices(self, obj):
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in Reservation.STATUS_CHOICES
        ]


class ReservationCreateSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    pet = PetSerializer()
    package_id = serializers.PrimaryKeyRelatedField(
        source='package',
        queryset=FuneralPackage.objects.all(),
        required=False,
        allow_null=True
    )
    memorial_room_id = serializers.PrimaryKeyRelatedField(
        source='memorial_room',
        queryset=MemorialRoom.objects.all(),
        required=False,
        allow_null=True
    )
    assigned_staff = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Reservation
        fields = [
            'customer', 'pet', 'package_id', 'memorial_room_id',
            'scheduled_at', 'assigned_staff', 'is_emergency',
            'visit_route', 'referral_hospital',
            'need_death_certificate', 'custom_requests'
        ]
        extra_kwargs = {
            'scheduled_at': {'required': False},
            'visit_route': {'required': False},
            'is_emergency': {'required': False},
            'need_death_certificate': {'required': False}
        }

    def create(self, validated_data):
        customer_data = validated_data.pop('customer')
        pet_data = validated_data.pop('pet')

        # 고객 생성 또는 조회
        customer, _ = Customer.objects.get_or_create(
            phone=customer_data['phone'],
            defaults=customer_data
        )

        # 반려동물 생성
        pet_data['customer'] = customer
        pet = Pet.objects.create(**pet_data)

        # 예약 생성
        validated_data['customer'] = customer
        validated_data['pet'] = pet
        validated_data['created_by'] = self.context['request'].user
        
        reservation = Reservation.objects.create(**validated_data)

        # 예약 이력 생성
        ReservationHistory.objects.create(
            reservation=reservation,
            from_status='pending',
            to_status='pending',
            changed_by=self.context['request'].user,
            notes='예약 생성'
        )

        return reservation 


class ReservationUpdateSerializer(serializers.ModelSerializer):
    """
    예약 수정을 위한 시리얼라이저

    [필수 필드]
    - scheduled_at: 예약 일시 (ISO 8601 형식, 예: "2024-03-20T14:30:00Z")
    - status: 예약 상태 (pending/confirmed/in_progress/completed/cancelled)
    - visit_route: 방문 경로 (internet/blog/hospital/referral)

    [선택 필드]
    - customer:
        - name: 고객명
        - phone: 전화번호
        - email: 이메일
        - address: 주소
    - pet:
        - name: 반려동물명
        - species: 종류 (dog/cat)
        - breed: 품종
        - age: 나이
        - weight: 체중
        - gender: 성별 (male/female)
        - death_date: 사망일시
        - death_reason: 사망사유 (natural/disease/accident/euthanasia)
    - memorial_room: 추모실 이름
    - package: 패키지 이름
    - is_emergency: 긴급여부 (true/false)
    - assigned_staff: 담당 직원 ID
    - referral_hospital: 의뢰 병원명
    - need_death_certificate: 사망확인서 필요여부 (true/false)
    - custom_requests: 요청사항
    """
    memorial_room = serializers.CharField(required=False)
    package = serializers.CharField(required=False)
    customer = CustomerSerializer(required=False)
    pet = PetSerializer(required=False)
    assigned_staff = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Reservation
        fields = [
            'customer', 'pet', 'memorial_room', 'package',
            'scheduled_at', 'status', 'assigned_staff',
            'is_emergency', 'visit_route', 'referral_hospital',
            'need_death_certificate', 'custom_requests'
        ]

    def validate(self, data):
        if 'memorial_room' in data:
            try:
                memorial_room_name = data['memorial_room']
                memorial_room = MemorialRoom.objects.get(name=memorial_room_name)
                data['memorial_room'] = memorial_room
            except MemorialRoom.DoesNotExist:
                raise serializers.ValidationError({"memorial_room": "존재하지 않는 추모실입니다."})

        if 'package' in data:
            try:
                package_name = data['package']
                package = FuneralPackage.objects.get(name=package_name)
                data['package'] = package
            except FuneralPackage.DoesNotExist:
                raise serializers.ValidationError({"package": "존재하지 않는 패키지입니다."})

        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        # 고객 정보 업데이트
        if 'customer' in validated_data:
            customer_data = validated_data.pop('customer')
            customer = instance.customer
            for attr, value in customer_data.items():
                setattr(customer, attr, value)
            customer.save()

        # 반려동물 정보 업데이트
        if 'pet' in validated_data:
            pet_data = validated_data.pop('pet')
            pet = instance.pet
            for attr, value in pet_data.items():
                setattr(pet, attr, value)
            pet.save()

        # 예약 상태가 변경된 경우 이력 생성
        if 'status' in validated_data and validated_data['status'] != instance.status:
            ReservationHistory.objects.create(
                reservation=instance,
                from_status=instance.status,
                to_status=validated_data['status'],
                changed_by=self.context['request'].user,
                notes='예약 상태 변경'
            )

        return super().update(instance, validated_data) 