from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import (
    Category, Supplier, InventoryItem,
    StockMovement, PurchaseOrder, PurchaseOrderItem
)

User = get_user_model()

class CategoryTests(APITestCase):
    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            phone='010-1234-5678',
            department='테스트부서',
            position='테스트직책',
            auth_level=1
        )
        self.client.force_authenticate(user=self.user)
        
        # 테스트 카테고리 생성
        self.category = Category.objects.create(
            name='테스트 카테고리',
            description='테스트 설명'
        )

    def test_create_category(self):
        """카테고리 생성 테스트"""
        url = reverse('category-list')
        data = {
            'name': '새 카테고리',
            'description': '새로운 카테고리 설명'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Category.objects.latest('id').name, '새 카테고리')

    def test_retrieve_category(self):
        """카테고리 조회 테스트"""
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '테스트 카테고리')


class InventoryItemTests(APITestCase):
    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            phone='010-1234-5678',
            department='테스트부서',
            position='테스트직책',
            auth_level=1
        )
        self.client.force_authenticate(user=self.user)
        
        # 테스트 데이터 생성
        self.category = Category.objects.create(
            name='테스트 카테고리'
        )
        self.supplier = Supplier.objects.create(
            name='테스트 공급업체',
            contact_name='담당자',
            phone='010-1234-5678'
        )
        self.item = InventoryItem.objects.create(
            category=self.category,
            supplier=self.supplier,
            name='테스트 품목',
            code='TEST001',
            unit='개',
            unit_price=Decimal('10000.00'),
            current_stock=100,
            minimum_stock=10
        )

    def test_create_inventory_item(self):
        """재고 품목 생성 테스트"""
        url = reverse('inventoryitem-list')
        data = {
            'category': self.category.id,
            'supplier': self.supplier.id,
            'name': '새 품목',
            'code': 'TEST002',
            'unit': '개',
            'unit_price': '15000.00',
            'current_stock': 50,
            'minimum_stock': 5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryItem.objects.count(), 2)

    def test_low_stock_items(self):
        """재고 부족 품목 조회 테스트"""
        self.item.current_stock = 5  # 최소 재고량보다 낮게 설정
        self.item.save()
        
        url = reverse('inventoryitem-low-stock')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.item.id)

    def test_adjust_stock(self):
        """재고 수량 조정 테스트"""
        url = reverse('inventoryitem-adjust-stock', args=[self.item.id])
        data = {
            'quantity': 50,
            'notes': '재고 조정'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, 150)  # 100 + 50


class PurchaseOrderTests(APITestCase):
    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            phone='010-1234-5678',
            department='테스트부서',
            position='테스트직책',
            auth_level=1
        )
        self.client.force_authenticate(user=self.user)
        
        # 테스트 데이터 생성
        self.supplier = Supplier.objects.create(
            name='테스트 공급업체',
            contact_name='담당자',
            phone='010-1234-5678'
        )
        self.category = Category.objects.create(
            name='테스트 카테고리'
        )
        self.item = InventoryItem.objects.create(
            category=self.category,
            supplier=self.supplier,
            name='테스트 품목',
            code='TEST001',
            unit='개',
            unit_price=Decimal('10000.00'),
            current_stock=100
        )
        self.order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            order_number='PO20240301001',
            status='pending',
            created_by=self.user
        )
        self.order_item = PurchaseOrderItem.objects.create(
            order=self.order,
            item=self.item,
            quantity=10,
            unit_price=Decimal('10000.00'),
            total_price=Decimal('100000.00')
        )

    def test_create_purchase_order(self):
        """발주서 생성 테스트"""
        url = reverse('purchaseorder-list')
        data = {
            'supplier': self.supplier.id,
            'items': [{
                'item': self.item.id,
                'quantity': 5,
                'unit_price': '10000.00'
            }]
        }
        response = self.client.post(url, data, format='json')
        print("Response:", response.status_code)
        print("Response Data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PurchaseOrder.objects.count(), 2)

    def test_approve_purchase_order(self):
        """발주서 승인 테스트"""
        url = reverse('purchaseorder-approve', args=[self.order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'approved')
        self.assertEqual(self.order.approved_by, self.user)

    def test_receive_purchase_order(self):
        """발주 물품 입고 테스트"""
        self.order.status = 'approved'
        self.order.save()
        
        url = reverse('purchaseorder-receive', args=[self.order.id])
        data = {
            'items': [{
                'id': self.order_item.id,
                'received_quantity': 10
            }]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.order.refresh_from_db()
        self.order_item.refresh_from_db()
        self.item.refresh_from_db()
        
        self.assertEqual(self.order.status, 'received')
        self.assertEqual(self.order_item.received_quantity, 10)
        self.assertEqual(self.item.current_stock, 110)  # 100 + 10
