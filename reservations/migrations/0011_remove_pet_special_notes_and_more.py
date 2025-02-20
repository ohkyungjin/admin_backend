# Generated by Django 5.1.5 on 2025-02-15 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0010_reservation_additional_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(model_name="pet", name="special_notes",),
        migrations.RemoveField(model_name="reservation", name="custom_requests",),
        migrations.AddField(
            model_name="reservation",
            name="memo",
            field=models.TextField(blank=True, verbose_name="메모"),
        ),
    ]
