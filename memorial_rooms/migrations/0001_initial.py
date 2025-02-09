# Generated by Django 5.1.5 on 2025-02-07 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MemorialRoom",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="추모실명")),
                (
                    "capacity",
                    models.IntegerField(blank=True, null=True, verbose_name="수용인원"),
                ),
                (
                    "operating_hours",
                    models.CharField(
                        blank=True,
                        help_text="예: 09:00-18:00",
                        max_length=100,
                        verbose_name="이용시간",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="특이사항")),
                ("is_active", models.BooleanField(default=True, verbose_name="사용가능여부")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="생성일"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="수정일")),
            ],
            options={
                "verbose_name": "추모실",
                "verbose_name_plural": "추모실 목록",
                "ordering": ["name"],
            },
        ),
    ]
