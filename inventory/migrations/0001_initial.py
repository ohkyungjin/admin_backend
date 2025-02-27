# Generated by Django 5.1.5 on 2025-01-31 05:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='카테고리명')),
                ('description', models.TextField(blank=True, verbose_name='설명')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
            ],
            options={
                'verbose_name': '카테고리',
                'verbose_name_plural': '카테고리 목록',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='공급업체명')),
                ('contact_name', models.CharField(max_length=50, verbose_name='담당자명')),
                ('phone', models.CharField(max_length=20, verbose_name='전화번호')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='이메일')),
                ('address', models.TextField(blank=True, verbose_name='주소')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
            ],
            options={
                'verbose_name': '공급업체',
                'verbose_name_plural': '공급업체 목록',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='품목명')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='품목코드')),
                ('description', models.TextField(blank=True, verbose_name='설명')),
                ('unit', models.CharField(max_length=20, verbose_name='단위')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='단가')),
                ('current_stock', models.IntegerField(default=0, verbose_name='현재 재고')),
                ('minimum_stock', models.IntegerField(default=0, verbose_name='최소 재고')),
                ('maximum_stock', models.IntegerField(default=0, verbose_name='최대 재고')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='inventory.category')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='inventory.supplier')),
            ],
            options={
                'verbose_name': '재고 품목',
                'verbose_name_plural': '재고 품목 목록',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(max_length=50, unique=True, verbose_name='발주번호')),
                ('status', models.CharField(choices=[('draft', '임시저장'), ('pending', '승인대기'), ('approved', '승인완료'), ('ordered', '발주완료'), ('received', '입고완료'), ('cancelled', '취소')], default='draft', max_length=20, verbose_name='상태')),
                ('order_date', models.DateField(blank=True, null=True, verbose_name='발주일')),
                ('expected_date', models.DateField(blank=True, null=True, verbose_name='입고예정일')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='총 금액')),
                ('notes', models.TextField(blank=True, verbose_name='비고')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='approved_orders', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_orders', to=settings.AUTH_USER_MODEL)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchase_orders', to='inventory.supplier')),
            ],
            options={
                'verbose_name': '발주서',
                'verbose_name_plural': '발주서 목록',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PurchaseOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(verbose_name='수량')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='단가')),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='합계')),
                ('received_quantity', models.IntegerField(default=0, verbose_name='입고수량')),
                ('notes', models.TextField(blank=True, verbose_name='비고')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='inventory.inventoryitem')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventory.purchaseorder')),
            ],
            options={
                'verbose_name': '발주 품목',
                'verbose_name_plural': '발주 품목 목록',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('in', '입고'), ('out', '출고'), ('adjust', '조정'), ('return', '반품')], max_length=10, verbose_name='이동 유형')),
                ('quantity', models.IntegerField(verbose_name='수량')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='단가')),
                ('reference_number', models.CharField(blank=True, max_length=50, verbose_name='참조번호')),
                ('notes', models.TextField(blank=True, verbose_name='비고')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='stock_movements', to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movements', to='inventory.inventoryitem')),
            ],
            options={
                'verbose_name': '재고 이동',
                'verbose_name_plural': '재고 이동 목록',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['movement_type', 'created_at'], name='inventory_s_movemen_ed5291_idx'), models.Index(fields=['item', 'created_at'], name='inventory_s_item_id_a9fe64_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='purchaseorder',
            index=models.Index(fields=['order_number'], name='inventory_p_order_n_ff9797_idx'),
        ),
        migrations.AddIndex(
            model_name='purchaseorder',
            index=models.Index(fields=['status', 'order_date'], name='inventory_p_status_1b7ac0_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['code'], name='inventory_i_code_971ebd_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['category', 'name'], name='inventory_i_categor_25941c_idx'),
        ),
    ]
