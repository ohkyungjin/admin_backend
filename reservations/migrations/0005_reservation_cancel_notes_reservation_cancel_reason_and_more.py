# Generated by Django 5.1.5 on 2025-02-08 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0004_alter_reservation_memorial_room_alter_pet_age_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="cancel_notes",
            field=models.TextField(blank=True, verbose_name="취소비고"),
        ),
        migrations.AddField(
            model_name="reservation",
            name="cancel_reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("customer_request", "고객 요청"),
                    ("admin_cancel", "관리자 취소"),
                    ("no_show", "노쇼"),
                ],
                max_length=20,
                null=True,
                verbose_name="취소사유",
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="취소일시"),
        ),
        migrations.AddField(
            model_name="reservation",
            name="penalty_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="위약금",
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="refund_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="환불금액",
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="refund_status",
            field=models.CharField(
                choices=[("pending", "대기"), ("completed", "완료"), ("failed", "실패")],
                default="pending",
                max_length=20,
                verbose_name="환불상태",
            ),
        ),
        migrations.AlterField(
            model_name="pet",
            name="death_reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("natural", "자연사"),
                    ("disease", "병사"),
                    ("accident", "사고사"),
                    ("euthanasia", "안락사"),
                    ("other", "기타"),
                ],
                max_length=20,
                null=True,
                verbose_name="사망사유",
            ),
        ),
    ]
