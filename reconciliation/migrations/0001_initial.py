# Generated by Django 5.1.7 on 2025-06-14 01:30

import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cashier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('employee_id', models.CharField(max_length=20, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CODCustomer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Customer or Company Name', max_length=255)),
                ('contact_person', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('initial_deposit_amount', models.DecimalField(decimal_places=2, help_text='Initial POP amount', max_digits=12)),
                ('current_balance', models.DecimalField(decimal_places=2, help_text='Calculated current balance', max_digits=12)),
                ('pop_reference', models.CharField(blank=True, help_text='Proof of Payment reference', max_length=100, null=True)),
                ('registration_date', models.DateField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'COD Customer',
                'verbose_name_plural': 'COD Customers',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Expense Category',
                'verbose_name_plural': 'Expense Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='FuelTank',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('fuel_type', models.CharField(max_length=50)),
                ('capacity_liters', models.DecimalField(decimal_places=2, max_digits=10)),
                ('current_liters', models.DecimalField(decimal_places=2, max_digits=10)),
                ('last_reconciliation_date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'FuelTank',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='OilProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the oil product, e.g., Shell Helix HX5 5L', max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('unit_of_measure', models.CharField(default='Unit', help_text='e.g., Liters, Unit, 500ml Bottle', max_length=50)),
                ('selling_price', models.DecimalField(decimal_places=2, default=0.0, help_text='Current selling price per unit', max_digits=10)),
                ('current_stock_units', models.DecimalField(decimal_places=2, default=0.0, help_text='Current stock level in units', max_digits=10)),
                ('low_stock_threshold', models.DecimalField(decimal_places=2, default=5.0, help_text='Threshold for low stock alert (in units)', max_digits=10)),
                ('buying_price', models.DecimalField(decimal_places=2, default=0.0, help_text='Price the business pays per unit', max_digits=10)),
            ],
            options={
                'verbose_name': 'Oil Product',
                'verbose_name_plural': 'Oil Products',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BankDeposit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deposit_date', models.DateField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Amount deposited', max_digits=12)),
                ('reference_number', models.CharField(blank=True, help_text='Bank deposit slip reference', max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deposited_by', models.ForeignKey(help_text='Manager who made the deposit', on_delete=django.db.models.deletion.PROTECT, related_name='bank_deposits_made', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Bank Deposit',
                'verbose_name_plural': 'Bank Deposits',
                'ordering': ['-deposit_date'],
            },
        ),
        migrations.CreateModel(
            name='CODVehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_number', models.CharField(max_length=20, unique=True)),
                ('company_name_on_vehicle', models.CharField(blank=True, help_text='Company name displayed on the vehicle, if different from customer', max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vehicles', to='reconciliation.codcustomer')),
            ],
            options={
                'verbose_name': 'COD Vehicle',
                'verbose_name_plural': 'COD Vehicles',
                'ordering': ['registration_number'],
            },
        ),
        migrations.CreateModel(
            name='BusinessExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expense_date', models.DateField(default=django.utils.timezone.now)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('receipt', models.FileField(blank=True, help_text='Scanned receipt/slip', null=True, upload_to='business_expense_receipts/')),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_business_expenses', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expenses', to='reconciliation.expensecategory')),
            ],
            options={
                'verbose_name': 'Business Expense',
                'verbose_name_plural': 'Business Expenses',
                'ordering': ['-expense_date'],
            },
        ),
        migrations.CreateModel(
            name='FuelOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fuel_type', models.CharField(choices=[('ULP', 'Unleaded Petrol'), ('Diesel', 'Diesel'), ('Oil', 'Oil')], max_length=10)),
                ('quantity_ordered_liters', models.DecimalField(decimal_places=2, max_digits=10)),
                ('supplier_name', models.CharField(blank=True, max_length=255, null=True)),
                ('order_date', models.DateField(default=django.utils.timezone.now)),
                ('expected_delivery_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending Approval'), ('APPROVED', 'Approved (Sent to Supplier)'), ('PARTIALLY_RECEIVED', 'Partially Received'), ('RECEIVED', 'Fully Received'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('approved_by', models.ForeignKey(blank=True, help_text='Senior Manager or CEO who approved', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fuel_orders_approved', to=settings.AUTH_USER_MODEL)),
                ('ordered_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fuel_orders_placed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Fuel Stock Order',
                'verbose_name_plural': 'Fuel Stock Orders',
                'ordering': ['-order_date'],
            },
        ),
        migrations.CreateModel(
            name='DipRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dip_type', models.CharField(choices=[('OPENING', 'Opening Dip'), ('CLOSING', 'Closing Dip'), ('INTERIM', 'Interim Check')], max_length=10)),
                ('dip_reading_liters', models.DecimalField(decimal_places=2, help_text='Physical measurement in liters', max_digits=10)),
                ('record_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True, null=True)),
                ('recorded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='dip_records_made', to=settings.AUTH_USER_MODEL)),
                ('fuel_tank', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='dip_records', to='reconciliation.fueltank')),
            ],
            options={
                'verbose_name': 'Tank Dip Record',
                'verbose_name_plural': 'Tank Dip Records',
                'ordering': ['-record_datetime'],
            },
        ),
        migrations.CreateModel(
            name='PettyCashAllocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, help_text='Initial float amount', max_digits=10)),
                ('allocation_date', models.DateField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Is this the current active float?')),
                ('allocated_by', models.ForeignKey(help_text='CEO who allocated the float', on_delete=django.db.models.deletion.PROTECT, related_name='petty_cash_allocations_made', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Petty Cash Allocation',
                'verbose_name_plural': 'Petty Cash Allocations',
                'ordering': ['-allocation_date'],
            },
        ),
        migrations.CreateModel(
            name='PettyCashExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expense_date', models.DateField()),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('receipt_slip', models.FileField(blank=True, help_text='Scanned receipt/slip', null=True, upload_to='petty_cash_receipts/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('allocation', models.ForeignKey(help_text='The petty cash float this expense is against', on_delete=django.db.models.deletion.PROTECT, related_name='expenses', to='reconciliation.pettycashallocation')),
                ('logged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logged_petty_cash_expenses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Petty Cash Expense',
                'verbose_name_plural': 'Petty Cash Expenses',
                'ordering': ['-expense_date'],
            },
        ),
        migrations.CreateModel(
            name='ReceivedStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_received_liters', models.DecimalField(decimal_places=2, max_digits=10)),
                ('delivery_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('supplier_invoice_number', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('fuel_order', models.ForeignKey(blank=True, help_text='Link to original order if applicable', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='deliveries', to='reconciliation.fuelorder')),
                ('fuel_tank', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='deliveries_received', to='reconciliation.fueltank')),
                ('logged_by', models.ForeignKey(help_text='Manager who logged the delivery', on_delete=django.db.models.deletion.PROTECT, related_name='stock_deliveries_logged', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Received Fuel Stock',
                'verbose_name_plural': 'Received Fuel Stocks',
                'ordering': ['-delivery_date'],
            },
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stowe_shift_id', models.CharField(help_text='Unique shift identifier from STOWE', max_length=100, unique=True)),
                ('shift_type', models.IntegerField(choices=[(1, 'Shift 1 (5:00 AM – 10:00 AM)'), (2, 'Shift 2 (10:00 AM – 4:00 PM)'), (3, 'Shift 3 (4:00 PM – 9:00 PM)')])),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('stowe_sales_ulp', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='ULP Sales (R)')),
                ('stowe_sales_diesel', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Diesel Sales (R)')),
                ('stowe_sales_oil', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Oil Sales (R)')),
                ('attachment', models.FileField(blank=True, null=True, upload_to='shift_attachments/')),
                ('source_of_data', models.CharField(default='STOWE', max_length=50)),
                ('sales_data_confirmed_by_cashier', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cashier', models.ForeignKey(limit_choices_to={'role': 'CASHIER'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Shift Record',
                'verbose_name_plural': 'Shift Records',
                'ordering': ['-start_datetime'],
            },
        ),
        migrations.CreateModel(
            name='OilSale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_sold', models.DecimalField(decimal_places=2, max_digits=8)),
                ('price_per_unit_at_sale', models.DecimalField(decimal_places=2, help_text='Price of one unit of this oil at the time of sale', max_digits=10)),
                ('total_sale_value', models.DecimalField(decimal_places=2, editable=False, help_text='Calculated: quantity_sold * price_per_unit_at_sale', max_digits=10)),
                ('sale_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True, null=True)),
                ('cashier_responsible', models.ForeignKey(help_text='Cashier responsible for the oil counter during this sale', limit_choices_to={'role': 'CASHIER'}, on_delete=django.db.models.deletion.PROTECT, related_name='oil_sales_managed', to=settings.AUTH_USER_MODEL)),
                ('logged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='oil_sales_logged_by', to=settings.AUTH_USER_MODEL)),
                ('oil_product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_logged', to='reconciliation.oilproduct')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='oil_sales', to='reconciliation.shift')),
            ],
            options={
                'verbose_name': 'Oil Sale Entry',
                'verbose_name_plural': 'Oil Sale Entries',
                'ordering': ['-sale_datetime'],
            },
        ),
        migrations.CreateModel(
            name='FuelSale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(max_length=100)),
                ('litres_sold', models.DecimalField(decimal_places=2, max_digits=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reconciliation.shift')),
            ],
        ),
        migrations.CreateModel(
            name='FuelAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Adjustment Amount (R)')),
                ('direction', models.CharField(choices=[('ADD', 'Add to Cash Submission'), ('SUB', 'Subtract from Cash Submission')], max_length=3, verbose_name='Adjustment Type')),
                ('reason_note', models.TextField(verbose_name='Reason for Adjustment')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fuel_adjustments', to='reconciliation.shift')),
            ],
        ),
        migrations.CreateModel(
            name='CongestionEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stowe_shift_number', models.CharField(max_length=50)),
                ('diesel_volume_stowe', models.DecimalField(decimal_places=2, max_digits=10)),
                ('ulp_volume_stowe', models.DecimalField(decimal_places=2, max_digits=10)),
                ('diesel_value_rands', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('ulp_value_rands', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('total_cod_sales_value_shift', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('cash_submitted', models.DecimalField(decimal_places=2, max_digits=12)),
                ('speedpoint_submitted', models.DecimalField(decimal_places=2, max_digits=12)),
                ('oil_quantity_sold', models.PositiveIntegerField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('oil_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reconciliation.oilproduct')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='congestion_entries', to='reconciliation.shift')),
            ],
        ),
        migrations.CreateModel(
            name='CODTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(choices=[('ULP', 'Unleaded Petrol'), ('Diesel', 'Diesel'), ('Oil', 'Oil'), ('OIL', 'Oil (Specify Type in Notes)')], max_length=10)),
                ('liters_dispensed', models.DecimalField(decimal_places=2, max_digits=10)),
                ('price_per_liter_at_time', models.DecimalField(decimal_places=3, help_text='Price at the time of transaction', max_digits=6)),
                ('transaction_value_at_time', models.DecimalField(decimal_places=2, help_text='Calculated value: liters * price', max_digits=10)),
                ('transaction_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('approval_datetime', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, help_text="e.g., Specific oil type if 'OIL' is chosen", null=True)),
                ('cashier_verifying', models.ForeignKey(help_text='Cashier who verified the COD transaction', limit_choices_to={'role': 'CASHIER'}, on_delete=django.db.models.deletion.PROTECT, related_name='verified_cod_transactions', to=settings.AUTH_USER_MODEL)),
                ('manager_approved_by', models.ForeignKey(blank=True, help_text='Manager who approved this transaction', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_cod_transactions', to=settings.AUTH_USER_MODEL)),
                ('customer_vehicle', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cod_transactions', to='reconciliation.codvehicle')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cod_transactions', to='reconciliation.shift')),
            ],
            options={
                'verbose_name': 'COD Transaction',
                'verbose_name_plural': 'COD Transactions',
                'ordering': ['-transaction_datetime'],
            },
        ),
        migrations.CreateModel(
            name='CashSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cash_submitted', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Amount of cash submitted for this shift', max_digits=10)),
                ('speedpoint_submitted', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Amount submitted via speedpoint for this shift', max_digits=10)),
                ('cod_sales_value_reported', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Total COD (Cash on Delivery) sales value reported by cashier for this shift. This amount is expected NOT to reflect in till.', max_digits=10)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(blank=True, help_text='User who recorded this submission', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_cash_submissions', to=settings.AUTH_USER_MODEL)),
                ('shift', models.OneToOneField(help_text='The shift this cash submission belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='cash_submission', to='reconciliation.shift')),
            ],
            options={
                'verbose_name': 'Cash Submission',
                'verbose_name_plural': 'Cash Submissions',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='StockTake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True, null=True)),
                ('document', models.FileField(blank=True, null=True, upload_to='stocktakes/')),
                ('cashier', models.ForeignKey(limit_choices_to={'role': 'CASHIER'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Stock Take',
                'verbose_name_plural': 'Stock Takes',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='StockTakeItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('system_quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('physical_quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('oil_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reconciliation.oilproduct')),
                ('stock_take', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='reconciliation.stocktake')),
            ],
        ),
        migrations.CreateModel(
            name='CashierOilWarehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('cashier', models.OneToOneField(limit_choices_to={'role': 'CASHIER'}, on_delete=django.db.models.deletion.CASCADE, related_name='oil_warehouse', to=settings.AUTH_USER_MODEL)),
                ('oil_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reconciliation.oilproduct')),
            ],
            options={
                'verbose_name': 'Cashier Oil Warehouse',
                'verbose_name_plural': 'Cashier Oil Warehouses',
                'unique_together': {('cashier', 'oil_product')},
            },
        ),
        migrations.CreateModel(
            name='BuyingPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(choices=[('ULP', 'Unleaded Petrol'), ('Diesel', 'Diesel'), ('Oil', 'Oil'), ('OIL', 'Oil (Specify particular product if necessary in notes/link)')], help_text='Type of product (ULP, Diesel, or general Oil)', max_length=10)),
                ('buying_price_per_unit', models.DecimalField(decimal_places=3, help_text='Buying price per liter (for fuel) or per unit (for oil)', max_digits=10)),
                ('effective_date', models.DateField(help_text='Date this buying price becomes effective')),
                ('supplier', models.CharField(blank=True, help_text='Supplier name, if applicable', max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('set_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='buying_prices_set', to=settings.AUTH_USER_MODEL)),
                ('oil_product_specific', models.ForeignKey(blank=True, help_text='Link to a specific oil product if this price is for a particular oil', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='buying_prices', to='reconciliation.oilproduct')),
            ],
            options={
                'verbose_name': 'Buying Price Record',
                'verbose_name_plural': 'Buying Price Records',
                'ordering': ['-effective_date', 'product_type'],
                'unique_together': {('product_type', 'oil_product_specific', 'effective_date')},
            },
        ),
        migrations.CreateModel(
            name='PriceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fuel_type', models.CharField(choices=[('ULP', 'Unleaded Petrol'), ('Diesel', 'Diesel'), ('Oil', 'Oil')], max_length=20)),
                ('effective_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('price_per_liter', models.DecimalField(decimal_places=3, max_digits=6)),
                ('truncated_price_per_liter', models.DecimalField(decimal_places=6, default=Decimal('0.000000'), max_digits=10)),
                ('set_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Fuel Price Record',
                'verbose_name_plural': 'Fuel Price Records',
                'ordering': ['-effective_date', 'fuel_type'],
                'unique_together': {('fuel_type', 'effective_date')},
            },
        ),
    ]
