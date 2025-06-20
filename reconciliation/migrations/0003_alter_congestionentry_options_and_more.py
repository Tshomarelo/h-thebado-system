# Generated by Django 5.1.7 on 2025-06-14 13:01

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reconciliation', '0002_alter_pettycashallocation_allocation_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='congestionentry',
            options={'ordering': ['-submitted_at'], 'verbose_name': 'Fuel Sale Ingestion Entry', 'verbose_name_plural': 'Fuel Sale Ingestion Entries'},
        ),
        migrations.RemoveField(
            model_name='shift',
            name='stowe_sales_diesel',
        ),
        migrations.RemoveField(
            model_name='shift',
            name='stowe_sales_oil',
        ),
        migrations.RemoveField(
            model_name='shift',
            name='stowe_sales_ulp',
        ),
        migrations.AlterField(
            model_name='cashsubmission',
            name='cod_sales_value_reported',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total COD (Cash on Delivery) sales value reported by cashier for this shift', max_digits=10),
        ),
        migrations.AlterField(
            model_name='congestionentry',
            name='diesel_volume_stowe',
            field=models.DecimalField(decimal_places=2, help_text='Total diesel volume sold', max_digits=10),
        ),
        migrations.AlterField(
            model_name='congestionentry',
            name='stowe_shift_number',
            field=models.CharField(help_text='External STOWE reference', max_length=50),
        ),
        migrations.AlterField(
            model_name='congestionentry',
            name='total_cod_sales_value_shift',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='COD value paid in advance for the shift', max_digits=12),
        ),
        migrations.AlterField(
            model_name='congestionentry',
            name='ulp_volume_stowe',
            field=models.DecimalField(decimal_places=2, help_text='Total ULP volume sold', max_digits=10),
        ),
    ]
