# Generated by Django 4.2.3 on 2025-02-17 12:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bills', '0013_remove_meter_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='meter',
            name='address',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.PROTECT, to='bills.house'),
        ),
    ]
