# Generated by Django 4.2.3 on 2025-03-31 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bills', '0028_remove_apartment_person_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='outgoingbill',
            name='extra_fields',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
