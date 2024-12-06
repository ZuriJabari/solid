# Generated by Django 5.0 on 2024-12-06 08:10

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_payments', '0002_alter_mobilepayment_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobilepayment',
            name='currency',
            field=models.CharField(default='UGX', max_length=3),
        ),
        migrations.AlterField(
            model_name='mobilepayment',
            name='amount',
            field=models.DecimalField(decimal_places=0, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('100')), django.core.validators.MaxValueValidator(Decimal('100000000'))]),
        ),
        migrations.AlterField(
            model_name='mobilepayment',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed'), ('CANCELLED', 'Cancelled')], default='pending', max_length=20),
        ),
    ]
