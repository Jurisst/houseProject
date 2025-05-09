# Generated by Django 4.2.3 on 2025-04-09 09:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bills', '0035_apartment_electricity_meters_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartment',
            name='mean_house_part',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0, 'Must be at least 0')]),
            preserve_default=False,
        ),
    ]
