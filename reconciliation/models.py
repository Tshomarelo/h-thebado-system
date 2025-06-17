from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings # For ForeignKey to User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import AbstractUser
from django.contrib import admin
from decimal import ROUND_HALF_UP, Decimal, ROUND_DOWN
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.contrib.auth.models import User
#Congestion model
from django.contrib.auth.models import User




class FuelTank(models.Model):
    id = models.AutoField(primary_key=True)

    fuel_type = models.CharField(
        max_length=50,
        help_text="Type of fuel stored in the tank (e.g. 'ULP', 'Diesel')"
    )

    capacity_liters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum storage capacity in liters"
    )

    current_liters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Manually updated current tank level in liters (based on STOWE dips)"
    )

    last_reconciliation_date = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp of the latest confirmed dip or tank level update"
    )

    is_stowe_verified = models.BooleanField(
        default=False,
        help_text="Indicates whether the current level has been cross-checked with STOWE"
    )

    class Meta:
        db_table = "FuelTank"
        verbose_name = "Fuel Tank"
        verbose_name_plural = "Fuel Tanks"
        ordering = ['fuel_type']

    def __str__(self):
        return f"{self.fuel_type} Tank (ID: {self.id})"


class Cashier(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.employee_id})"


class Shift(models.Model):
    SHIFT_TYPE_CHOICES = [
        (1, 'Shift 1 (5:00 AM – 10:00 AM)'),
        (2, 'Shift 2 (10:00 AM – 4:00 PM)'),
        (3, 'Shift 3 (4:00 PM – 9:00 PM)'),
    ]

    shift_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional manual or auto-generated number to identify the shift sequence"
    )

    confirmed = models.BooleanField(
        default=False,
        help_text="Marked true when the shift has been reviewed and signed off"
    )

    stowe_shift_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="STOWE-provided identifier for this shift"
    )

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'CASHIER'},
        help_text="Cashier assigned to this shift"
    )

    shift_type = models.IntegerField(
        choices=SHIFT_TYPE_CHOICES,
        help_text="The type or time block of the shift"
    )

    start_datetime = models.DateTimeField(help_text="Start timestamp for the shift")
    end_datetime = models.DateTimeField(help_text="End timestamp for the shift")

    attachment = models.FileField(
        upload_to='shift_attachments/',
        blank=True,
        null=True,
        help_text="Optional uploaded file: reconciliation sheet, fuel log, etc."
    )

    source_of_data = models.CharField(
        max_length=50,
        default="STOWE",
        help_text="System or source that provided the initial shift data"
    )

    sales_data_confirmed_by_cashier = models.BooleanField(
        default=False,
        help_text="Has the cashier reviewed and approved the sales totals?"
    )

    final_variance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final reconciled variance (expected - actual), synced from congestion entry"
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when this record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp of last update")

    class Meta:
        ordering = ['-start_datetime']
        verbose_name = "Shift Record"
        verbose_name_plural = "Shift Records"

    def __str__(self):
        return f"Shift {self.shift_number or self.stowe_shift_id} ({self.cashier.username}) – {self.get_shift_type_display()}"

    @property
    def has_submission(self):
        """
        Returns True if this shift has associated ingestion or sales data.
        Includes:
        - congestionentry: reconciliation fuel/oil ingestion
        - oilsale: direct oil sale record
        """
        return hasattr(self, 'congestionentry') or hasattr(self, 'oilsale')

  

# Section 2.7: Petty Cash Management
class PettyCashAllocation(models.Model):
    allocated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='petty_cash_allocations_made', help_text="CEO who allocated the float")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Initial float amount")
    allocation_date = models.DateField(default=timezone.now, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Is this the current active float?")

    class Meta:
        verbose_name = "Petty Cash Allocation"
        verbose_name_plural = "Petty Cash Allocations"
        ordering = ['-allocation_date']

    def __str__(self):
        return f"R{self.amount} allocated by {self.allocated_by.username} on {self.allocation_date}"

    def save(self, *args, **kwargs):
        if self.is_active:
            PettyCashAllocation.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class PettyCashExpense(models.Model):
    allocation = models.ForeignKey(PettyCashAllocation, on_delete=models.PROTECT, related_name='expenses', help_text="The petty cash float this expense is against")
    expense_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_slip = models.FileField(upload_to='petty_cash_receipts/', blank=True, null=True, help_text="Scanned receipt/slip")
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='logged_petty_cash_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Petty Cash Expense"
        verbose_name_plural = "Petty Cash Expenses"
        ordering = ['-expense_date']

    def __str__(self):
        return f"R{self.amount} for {self.description} on {self.expense_date}"

#Price record model

class PriceRecord(models.Model):
    FUEL_CHOICES = [
        ('ULP', 'Unleaded Petrol'),
        ('Diesel', 'Diesel'),
        ('Oil', 'Oil'),
    ]

    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)
    effective_date = models.DateField()
    set_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price_per_liter = models.DecimalField(max_digits=6, decimal_places=3)
    truncated_price_per_liter = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=Decimal('0.000000')
    )

    class Meta:
        verbose_name = "Fuel Price Record"
        verbose_name_plural = "Fuel Price Records"
        ordering = ['-effective_date', 'fuel_type']
        unique_together = ('fuel_type', 'effective_date') 

    def __str__(self):
        return f"{self.get_fuel_type_display()} at R{self.price_per_liter}/L effective {self.effective_date}"

    def clean(self):
        if self.effective_date and self.effective_date.weekday() != 1: 
            # You had pass here; consider adding validation or comment
            pass
        super().clean()

    def calculate_stowe_effective_price(self, price: Decimal) -> Decimal:
        """
        Calculates the effective truncated price Stowe uses by subtracting
        a small offset and truncating without rounding.
        Offset values can be adjusted based on fuel type or business logic.
        """
        if self.fuel_type == 'Diesel':
            offset = Decimal('0.0021')
        elif self.fuel_type == 'ULP':
            offset = Decimal('0.0030')  # example offset for ULP, change as needed
        else:
            offset = Decimal('0.0000')

        effective_price = price - offset
        effective_price = effective_price.quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
        return effective_price

    def save(self, *args, **kwargs):
        price = Decimal(self.price_per_liter)
        self.truncated_price_per_liter = self.calculate_stowe_effective_price(price)
        super().save(*args, **kwargs)

    @classmethod
    def get_price_record(cls, fuel_type, date):
        """
        Returns the latest PriceRecord for the given fuel_type
        effective on or before the specified date.
        """
        return cls.objects.filter(
            fuel_type__iexact=fuel_type,
            effective_date__lte=date
        ).order_by('-effective_date').first()
    
# Section 2.8: Bank Deposits
class BankDeposit(models.Model):
    deposit_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount deposited")
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Bank deposit slip reference")
    deposited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bank_deposits_made', help_text="Manager who made the deposit")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bank Deposit"
        verbose_name_plural = "Bank Deposits"
        ordering = ['-deposit_date']

    def __str__(self):
        return f"R{self.amount} deposited by {self.deposited_by.username} on {self.deposit_date}"


# Section 2.6: COD Customers
class CODCustomer(models.Model):
    name = models.CharField(max_length=255, help_text="Customer or Company Name")
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    initial_deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Initial POP amount")
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Calculated current balance")
    pop_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Proof of Payment reference")
    registration_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "COD Customer"
        verbose_name_plural = "COD Customers"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Balance: R{self.current_balance})"

    def update_balance(self):
        total_spent = self.cod_transactions.aggregate(total=Sum('transaction_value_at_time'))['total'] or 0.00
        self.current_balance = self.initial_deposit_amount - total_spent
        self.save(update_fields=['current_balance']) 

class CODVehicle(models.Model):
    customer = models.ForeignKey(CODCustomer, on_delete=models.CASCADE, related_name='vehicles')
    registration_number = models.CharField(max_length=20, unique=True)
    company_name_on_vehicle = models.CharField(max_length=255, blank=True, null=True, help_text="Company name displayed on the vehicle, if different from customer")
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "COD Vehicle"
        verbose_name_plural = "COD Vehicles"
        ordering = ['registration_number']

    def __str__(self):
        return f"{self.registration_number} ({self.customer.name})"

class CODTransaction(models.Model):
    PRODUCT_CHOICES = PriceRecord.FUEL_CHOICES + [('OIL', 'Oil (Specify Type in Notes)')] 

    customer_vehicle = models.ForeignKey(CODVehicle, on_delete=models.PROTECT, related_name='cod_transactions')
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name='cod_transactions')
    cashier_verifying = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='verified_cod_transactions', limit_choices_to={'role': 'CASHIER'}, help_text="Cashier who verified the COD transaction")
    product_type = models.CharField(max_length=10, choices=PRODUCT_CHOICES)
    liters_dispensed = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_liter_at_time = models.DecimalField(max_digits=6, decimal_places=3, help_text="Price at the time of transaction")
    transaction_value_at_time = models.DecimalField(max_digits=10, decimal_places=2, help_text="Calculated value: liters * price")
    transaction_datetime = models.DateTimeField(default=timezone.now)
    manager_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_cod_transactions', help_text="Manager who approved this transaction")
    approval_datetime = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True, help_text="e.g., Specific oil type if 'OIL' is chosen")

    class Meta:
        verbose_name = "COD Transaction"
        verbose_name_plural = "COD Transactions"
        ordering = ['-transaction_datetime']

    def __str__(self):
        return f"{self.liters_dispensed}L of {self.get_product_type_display()} for {self.customer_vehicle} on {self.transaction_datetime.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        self.transaction_value_at_time = self.liters_dispensed * self.price_per_liter_at_time
        super().save(*args, **kwargs)
        self.customer_vehicle.customer.update_balance()

    def clean(self):
        super().clean()
        if not self.pk and self.customer_vehicle: # Only check for new transactions and if vehicle is set
            required_value = self.liters_dispensed * self.price_per_liter_at_time
            if self.customer_vehicle.customer.current_balance < required_value:
                 raise ValidationError(f"Insufficient balance for {self.customer_vehicle.customer.name}. Available: R{self.customer_vehicle.customer.current_balance:.2f}, Required: R{required_value:.2f}")

# Section 2.2 & 2.3: Fuel Stock Tracking & Dip Measurements
from django.db import models
from django.conf import settings
from django.utils import timezone

class FuelOrder(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved (Sent to Supplier)'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('RECEIVED', 'Fully Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    fuel_type = models.CharField(
        max_length=10,
        choices=PriceRecord.FUEL_CHOICES,
        help_text="Type of fuel being ordered (e.g. ULP, Diesel)"
    )

    quantity_ordered_liters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity of fuel ordered in liters"
    )

    buying_price_per_liter = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Purchase price per liter from the supplier"
    )

    cost_paid_rands = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total value paid for the order (buying_price × quantity)"
    )

    supplier_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional supplier name for reference"
    )

    order_date = models.DateField(
        default=timezone.now,
        help_text="Date the order was placed"
    )

    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
        help_text="Expected delivery date from supplier"
    )

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='PENDING',
        help_text="Lifecycle status of the order"
    )

    ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='fuel_orders_placed',
        help_text="User who placed the order"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_orders_approved',
        help_text="Senior Manager or CEO who approved this order"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional remarks or context"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this order record was created"
    )

    class Meta:
        verbose_name = "Fuel Stock Order"
        verbose_name_plural = "Fuel Stock Orders"
        ordering = ['-order_date']

    def __str__(self):
        return f"Order for {self.quantity_ordered_liters}L of {self.get_fuel_type_display()} on {self.order_date}"

class ReceivedStock(models.Model):
    fuel_order = models.ForeignKey(FuelOrder, on_delete=models.PROTECT, related_name='deliveries', null=True, blank=True, help_text="Link to original order if applicable")
    fuel_tank = models.ForeignKey(FuelTank, on_delete=models.PROTECT, related_name='deliveries_received') # Tank it was delivered into
    quantity_received_liters = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_date = models.DateTimeField(default=timezone.now)
    supplier_invoice_number = models.CharField(max_length=100, blank=True, null=True)
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_deliveries_logged', help_text="Manager who logged the delivery")
    notes = models.TextField(blank=True, null=True) # For discrepancies, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Received Fuel Stock"
        verbose_name_plural = "Received Fuel Stocks"
        ordering = ['-delivery_date']

    def __str__(self):
        return f"{self.quantity_received_liters}L of {self.fuel_tank.fuel_type} received on {self.delivery_date.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
         super().save(*args, **kwargs)
    # Removed: auto-update to fuel_tank.current_liters
    # Tank levels will be updated manually via DipRecords or admin interface only
    @property
    def cost_per_liter(self):
         return self.fuel_order.buying_price_per_liter if self.fuel_order else None

    @property
    def total_cost_rands(self):
        if self.cost_per_liter:
            return self.quantity_received_liters * self.cost_per_liter
        return None



class DipRecord(models.Model):
    DIP_TYPE_CHOICES = [
        ('OPENING', 'Opening Dip'),
        ('CLOSING', 'Closing Dip'),
        ('INTERIM', 'Interim Check'),  # For ad-hoc checks
    ]

    fuel_tank = models.ForeignKey(
        'FuelTank',
        on_delete=models.PROTECT,
        related_name='dip_records',
        help_text="Tank this dip reading corresponds to"
    )

    dip_type = models.CharField(
        max_length=10,
        choices=DIP_TYPE_CHOICES,
        help_text="Type of dip: Opening, Closing, or Interim"
    )

    dip_reading_liters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Physical measurement of fuel level in liters"
    )

    record_datetime = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when the dip was recorded"
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='dip_records_made',
        help_text="User who recorded the dip"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes or context for this reading"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this dip record was logged"
    )

    class Meta:
        verbose_name = "Tank Dip Record"
        verbose_name_plural = "Tank Dip Records"
        ordering = ['-record_datetime']

    def __str__(self):
        return f"{self.get_dip_type_display()} for {self.fuel_tank.fuel_type} – {self.dip_reading_liters:.2f}L at {self.record_datetime.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.dip_type == 'CLOSING':
            tank = self.fuel_tank
            tank.current_liters = self.dip_reading_liters
            tank.last_reconciliation_date = self.record_datetime
            tank.is_stowe_verified = True
            tank.save(update_fields=[
                'current_liters',
                'last_reconciliation_date',
                'is_stowe_verified'
            ])

# Section 3.13: Buying Prices (New Model)
class BuyingPrice(models.Model):
    PRODUCT_TYPE_CHOICES = PriceRecord.FUEL_CHOICES + [
        ('OIL', 'Oil (Specify particular product if necessary in notes/link)'),
    ]
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, help_text="Type of product (ULP, Diesel, or general Oil)")
    oil_product_specific = models.ForeignKey('OilProduct', on_delete=models.SET_NULL, null=True, blank=True, related_name='buying_prices', help_text="Link to a specific oil product if this price is for a particular oil")
    buying_price_per_unit = models.DecimalField(max_digits=10, decimal_places=3, help_text="Buying price per liter (for fuel) or per unit (for oil)")
    effective_date = models.DateField(help_text="Date this buying price becomes effective")
    supplier = models.CharField(max_length=255, blank=True, null=True, help_text="Supplier name, if applicable")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    set_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='buying_prices_set')

    class Meta:
        verbose_name = "Buying Price Record"
        verbose_name_plural = "Buying Price Records"
        ordering = ['-effective_date', 'product_type']
        unique_together = ('product_type', 'oil_product_specific', 'effective_date') # Ensure unique price per product/date

    def __str__(self):
        if self.oil_product_specific:
            return f"{self.oil_product_specific.name} Buying Price: R{self.buying_price_per_unit} effective {self.effective_date}"
        return f"{self.get_product_type_display()} Buying Price: R{self.buying_price_per_unit} effective {self.effective_date}"

# Section 2.4: Oil Stock Management
class OilProduct(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the oil product, e.g., Shell Helix HX5 5L")
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50, default="Unit", help_text="e.g., Liters, Unit, 500ml Bottle")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Current selling price per unit")
    current_stock_units = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Current stock level in units")
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="Threshold for low stock alert (in units)")
    buying_price = models.DecimalField(max_digits=10,decimal_places=2,default=0.00,help_text="Price the business pays per unit"
)

    class Meta:
        verbose_name = "Oil Product"
        verbose_name_plural = "Oil Products"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Stock: {self.current_stock_units})"
    
    @property
    def is_low_stock(self):
        return self.current_stock_units <= self.low_stock_threshold

class CashierOilWarehouse(models.Model):
    cashier = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='oil_warehouse',
        limit_choices_to={'role': 'CASHIER'}
    )
    oil_product = models.ForeignKey(OilProduct, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Cashier Oil Warehouse"
        verbose_name_plural = "Cashier Oil Warehouses"
        unique_together = ('cashier', 'oil_product')

    def __str__(self):
        return f"{self.cashier.username}'s Warehouse for {self.oil_product.name}"
class OilSale(models.Model):
    oil_product = models.ForeignKey(OilProduct, on_delete=models.PROTECT, related_name='sales_logged')
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name='oil_sales')
    cashier_responsible = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='oil_sales_managed', limit_choices_to={'role': 'CASHIER'}, help_text="Cashier responsible for the oil counter during this sale")
    quantity_sold = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_unit_at_sale = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price of one unit of this oil at the time of sale")
    total_sale_value = models.DecimalField(max_digits=10, decimal_places=2, editable=False, help_text="Calculated: quantity_sold * price_per_unit_at_sale")
    sale_datetime = models.DateTimeField(default=timezone.now)
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='oil_sales_logged_by')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Oil Sale Entry"
        verbose_name_plural = "Oil Sale Entries"
        ordering = ['-sale_datetime']

    def __str__(self):
        return f"{self.quantity_sold} x {self.oil_product.name} sold in Shift {self.shift.stowe_shift_id}"

def save(self, *args, **kwargs):
    # Fetch cashier's warehouse record
    warehouse = CashierOilWarehouse.objects.get(
        cashier=self.cashier_responsible,
        oil_product=self.oil_product
    )

    # Validate stock
    if warehouse.quantity < self.quantity_sold:
        raise ValidationError("Not enough oil stock in cashier’s warehouse.")

    # Set the selling price if not already specified
    if not self.price_per_unit_at_sale:
        self.price_per_unit_at_sale = self.oil_product.selling_price

    # Calculate total sale
    self.total_sale_value = self.quantity_sold * self.price_per_unit_at_sale

    # Save the sale entry
    super().save(*args, **kwargs)

    # Deduct stock from cashier’s warehouse
    warehouse.quantity -= self.quantity_sold
    warehouse.save(update_fields=['quantity'])

    # Update related shift’s oil revenue if needed
    current_shift = self.shift
    total_oil_sales_for_shift = current_shift.oil_sales.aggregate(total=Sum('total_sale_value'))['total'] or 0.00
    if current_shift.stowe_sales_oil != total_oil_sales_for_shift:
        current_shift.stowe_sales_oil = total_oil_sales_for_shift
        current_shift.save(update_fields=['stowe_sales_oil'])

class FuelSale(models.Model):
    product_type = models.CharField(max_length=100)
    litres_sold = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    shift = models.ForeignKey('Shift', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_type} - {self.litres_sold}L"
# Model for Fuel Adjustments (Testing, Returns, etc.)
class FuelAdjustment(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='fuel_adjustments')
    amount = models.DecimalField("Adjustment Amount (R)", max_digits=12, decimal_places=2)
    
    DIRECTION_CHOICES = [
        ('ADD', 'Add to Cash Submission'),
        ('SUB', 'Subtract from Cash Submission'),
    ]
    direction = models.CharField("Adjustment Type", max_length=3, choices=DIRECTION_CHOICES)
    reason_note = models.TextField("Reason for Adjustment")
    
    adjustment_datetime = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def signed_amount(self):
        return self.amount if self.direction == 'ADD' else -self.amount

    def __str__(self):
        return f"{self.get_direction_display()} R{self.amount} for Shift {self.shift.id}"




    
    #STOCKTAKE
class StockTake(models.Model):
    date = models.DateField(default=timezone.now)
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'CASHIER'}
    )
    notes = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='stocktakes/', blank=True, null=True)

    class Meta:
        verbose_name = "Stock Take"
        verbose_name_plural = "Stock Takes"
        ordering = ['-date']

    def __str__(self):
        return f"Stock take for {self.cashier.username} on {self.date}"

class StockTakeItem(models.Model):
    stock_take = models.ForeignKey(StockTake, on_delete=models.CASCADE, related_name='items')
    oil_product = models.ForeignKey(OilProduct, on_delete=models.CASCADE)
    system_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    physical_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def variance(self):
        return self.physical_quantity - self.system_quantity

    def __str__(self):
        return f"{self.oil_product.name} - Variance: {self.variance}"
    
    #EXPENSES
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class BusinessExpense(models.Model):
    expense_date = models.DateField(default=timezone.now)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.FileField(upload_to='business_expense_receipts/', blank=True, null=True, help_text="Scanned receipt/slip")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_business_expenses')

    class Meta:
        verbose_name = "Business Expense"
        verbose_name_plural = "Business Expenses"
        ordering = ['-expense_date']

    def __str__(self):
        return f"R{self.amount} for {self.description} on {self.expense_date}"
    
class CongestionEntry(models.Model):
    shift = models.OneToOneField(
        Shift,
        on_delete=models.CASCADE,
        related_name='congestion_entry'
    )
    stowe_shift_number = models.CharField(max_length=50, help_text="External STOWE reference")

    # Fuel volumes (in liters)
    diesel_volume_stowe = models.DecimalField(max_digits=10, decimal_places=2, help_text="Diesel liters sold")
    ulp_volume_stowe = models.DecimalField(max_digits=10, decimal_places=2, help_text="ULP liters sold")

    # Declared revenue values
    diesel_value_rands = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ulp_value_rands = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Calculated unit prices
    diesel_unit_price = models.DecimalField(max_digits=14, decimal_places=10, null=True, blank=True)
    ulp_unit_price = models.DecimalField(max_digits=14, decimal_places=10, null=True, blank=True)

    total_sales_calculated = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Sum of declared diesel + ULP totals"
    )

    # Oil sales
    oil_product = models.ForeignKey(OilProduct, on_delete=models.SET_NULL, null=True, blank=True)
    oil_quantity_sold = models.PositiveIntegerField(null=True, blank=True)

    # COD impact
    total_cod_sales_value_shift = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="COD value to subtract from actual received cash"
    )

    # Cash received
    cash_submitted = models.DecimalField(max_digits=12, decimal_places=2)
    speedpoint_submitted = models.DecimalField(max_digits=12, decimal_places=2)

    # Timestamp
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "Fuel Sale Ingestion Entry"
        verbose_name_plural = "Fuel Sale Ingestion Entries"

    def __str__(self):
        return f"Shift {self.shift} | STOWE #{self.stowe_shift_number}"

    @property
    def expected_revenue(self):
        """Total expected revenue from fuel only"""
        return (self.diesel_value_rands or Decimal('0.00')) + (self.ulp_value_rands or Decimal('0.00'))

    @property
    def oil_total_sale(self):
        """Value of oil sold"""
        if self.oil_product and self.oil_quantity_sold:
            return self.oil_product.selling_price * self.oil_quantity_sold
        return Decimal('0.00')

   
    @property
    def actual_cash_received(self):
        adjustment = Decimal('0.00')

        if hasattr(self, 'adjustment_amount') and self.adjustment_amount is not None:
            direction = getattr(self, 'adjustment_direction', None)
            if direction == 'ADD':
                adjustment = self.adjustment_amount
            elif direction == 'SUB':
                adjustment = -self.adjustment_amount

        return (
            (self.cash_submitted or Decimal('0.00')) +
            (self.speedpoint_submitted or Decimal('0.00')) -
            (self.total_cod_sales_value_shift or Decimal('0.00')) +
            adjustment
        )




    @property
    def variance(self):
        return self.expected_revenue - self.actual_cash_received

    @property
    def variance_label(self):
        v = self.variance
        if abs(v) <= Decimal('1.00'):
            return "Balanced (≤ R1.00)"
        return f"{'Deficit' if v > 0 else 'Surplus'} of R{abs(v):.2f}"

    @property
    def summary(self):
        return {
            "Expected Revenue (Fuel Only)": self.expected_revenue,
            "Oil Sale Value": self.oil_total_sale,
            "COD Deducted": self.total_cod_sales_value_shift or Decimal('0.00'),
            "Actual Received (Net)": self.actual_cash_received,
            "Variance": self.variance,
            "Status": self.variance_label
        }


class DailyFuelSale(models.Model):
    sale_date = models.DateField()
    shift = models.ForeignKey(
        'Shift',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    ulp_sold_liters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    diesel_sold_liters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    cod_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    cash = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    card = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        unique_together = ('sale_date', 'shift', 'cashier')
        ordering = ['sale_date']

    def __str__(self):
        return f"{self.sale_date} | Shift: {self.shift} | Cashier: {self.cashier}"