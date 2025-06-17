import logging
from .forms_base import AuditableForm
from .forms_base import AuditableForm
from django import forms
from .models import CashierOilWarehouse, PriceRecord
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, InvalidOperation, DivisionByZero
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    Shift, PettyCashAllocation, PettyCashExpense, # Removed Cashier
    PriceRecord, BankDeposit, CODCustomer, CODVehicle, CODTransaction,
    FuelOrder, ReceivedStock, DipRecord, FuelTank, OilProduct, BuyingPrice, CongestionEntry, FuelAdjustment, StockTake, StockTakeItem)

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

#shift form
logger = logging.getLogger(__name__)

class ShiftForm(forms.ModelForm):
    cashier = forms.ModelChoiceField(
        queryset=User.objects.filter(role='CASHIER'),
        help_text="Select the cashier for this shift.",
        label="Cashier"
    )

    class Meta:
        model = Shift
        fields = ['cashier',
                'shift_type',
                'start_datetime',
                'end_datetime',
                'source_of_data',
                'sales_data_confirmed_by_cashier',
                'stowe_shift_id',
                'attachment',
                ]
        widgets = {
            'start_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'stowe_shift_id': forms.TextInput(
                attrs={'placeholder': 'Enter STOWE Shift ID', 'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        logger.debug("Initializing ShiftForm with args: %s, kwargs keys: %s", args, list(kwargs.keys()))
        super().__init__(*args, **kwargs)

        self.fields['start_datetime'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end_datetime'].input_formats = ('%Y-%m-%dT%H:%M',)

        # Optional logging of initial values
        if self.initial:
            logger.debug("Initial form values: %s", self.initial)
        if self.data:
            logger.debug("Posted form data: %s", dict(self.data))

class PettyCashAllocationForm(forms.ModelForm):
    class Meta:
        model = PettyCashAllocation
        exclude = ['allocated_by']
        widgets = {
            'allocation_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['allocation_date'].initial = timezone.now().date()

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Inject user as allocator
        if self.user:
            instance.allocated_by = self.user

        # Provide default allocation date if omitted
        if not instance.allocation_date:
            instance.allocation_date = timezone.now().date()

        if commit:
            instance.save()
        return instance

class PettyCashExpenseForm(forms.ModelForm):
    class Meta:
        model = PettyCashExpense
        fields = ['allocation', 'expense_date', 'description', 'amount', 'receipt_slip']
        widgets = {
            'allocation': forms.Select(attrs={'class': 'form-control'}),
            'expense_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of expense'
            }),
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'form-control'
            }),
            'receipt_slip': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf,image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Prefill today's date if none is set
        if not self.instance.pk and not self.data.get('expense_date'):
            self.fields['expense_date'].initial = timezone.now().date()

        # Disable allocation if no options
        if not self.fields['allocation'].queryset.exists():
            self.fields['allocation'].widget.attrs['disabled'] = True
            self.fields['allocation'].help_text = "⚠ No active allocations available."

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.logged_by = self.user
        if commit:
            instance.save()
        return instance

class PriceRecordForm(forms.ModelForm):
    class Meta:
        model = PriceRecord
        fields = ['fuel_type', 'price_per_liter', 'effective_date']
        widgets = {
            'price_per_liter': forms.NumberInput(attrs={'step': '0.001'}),
            'effective_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        help_texts = {
            'effective_date': 'Price becomes effective on this date. Typically the first Tuesday of the month.',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        self.fields['effective_date'].input_formats = ('%Y-%m-%d',)
        if not self.instance.pk: 
             self.fields['effective_date'].initial = timezone.now().date()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.set_by = self.user
        if commit:
            instance.save()
        return instance

    def clean_effective_date(self):
        date = self.cleaned_data.get('effective_date')
        return date

class BankDepositForm(forms.ModelForm):
    class Meta:
        model = BankDeposit
        fields = ['deposit_date', 'amount', 'reference_number', 'notes']
        widgets = {
            'deposit_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'reference_number': forms.TextInput(attrs={'placeholder': 'e.g., Slip_12345'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # To pass the user from the view
        super().__init__(*args, **kwargs)
        self.fields['deposit_date'].input_formats = ('%Y-%m-%d',)
        if not self.instance.pk: # For new records, default to today
             self.fields['deposit_date'].initial = timezone.now().date()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.deposited_by = self.user
        if commit:
            instance.save()
        return instance
    
class CODCustomerForm(forms.ModelForm):
    class Meta:
        model = CODCustomer
        fields = [
            'name', 'contact_person', 'contact_phone', 'contact_email', 
            'initial_deposit_amount', 'pop_reference', 'notes', 'is_active'
        ]
        # current_balance is calculated, so not in the form for direct input
        widgets = {
            'initial_deposit_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'contact_phone': forms.TextInput(attrs={'placeholder': 'e.g., +27821234567'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'e.g., customer@example.com'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set initial current_balance to initial_deposit_amount when creating new customer
        if not instance.pk: # Only for new customers
            instance.current_balance = instance.initial_deposit_amount
        if commit:
            instance.save()
        return instance

class CODVehicleForm(forms.ModelForm):
    # customer field might be pre-filled if adding vehicle from a customer's detail page
    class Meta:
        model = CODVehicle
        fields = ['customer', 'registration_number', 'company_name_on_vehicle', 'notes', 'is_active']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'registration_number': forms.TextInput(attrs={'placeholder': 'e.g., ABC 123 GP'}),
        }

class CODTransactionForm(forms.ModelForm):
    # customer_vehicle, shift, cashier_verifying, price_per_liter_at_time will be set in view or by context
    class Meta:
        model = CODTransaction
        fields = ['customer_vehicle', 'shift', 'cashier_verifying', 'product_type', 'liters_dispensed', 'price_per_liter_at_time', 'notes']
        widgets = {
            'liters_dispensed': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Specify oil type if "OIL" selected'}),
            # Consider making some fields HiddenInput if they are set by the view
            'customer_vehicle': forms.Select(), 
            'shift': forms.Select(), 
            'cashier_verifying': forms.Select(), 
            'price_per_liter_at_time': forms.HiddenInput(), # Auto-filled based on product and date
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None) # For manager_approved_by
        self.active_shift = kwargs.pop('active_shift', None)
        self.cod_customer = kwargs.pop('cod_customer', None)

        super().__init__(*args, **kwargs)
        
        if self.active_shift:
            self.fields['shift'].initial = self.active_shift
            self.fields['shift'].widget = forms.HiddenInput() # Or disabled select
            self.fields['cashier_verifying'].initial = self.active_shift.cashier
            self.fields['cashier_verifying'].widget = forms.HiddenInput()


        if self.cod_customer:
            self.fields['customer_vehicle'].queryset = CODVehicle.objects.filter(customer=self.cod_customer, is_active=True)
        else:
            self.fields['customer_vehicle'].queryset = CODVehicle.objects.filter(is_active=True) # Or empty if customer must be selected first

        # Auto-fill price_per_liter_at_time based on product_type and current date in the view/template via JS,
        # or on form submission in the clean method. For now, it's hidden and expected to be set by view.


    def clean(self):
        cleaned_data = super().clean()
        liters = cleaned_data.get('liters_dispensed')
        price = cleaned_data.get('price_per_liter_at_time') # This needs to be set before clean
        vehicle = cleaned_data.get('customer_vehicle')

        if not price and cleaned_data.get('product_type'):
            # Attempt to fetch price if not provided (e.g., if not set by JS)
            # This is a fallback; ideally, JS in template or view's get_initial/get_form_kwargs handles this.
            product = cleaned_data.get('product_type')
            if product != 'OIL': # Assuming OIL price is manually entered or handled differently
                latest_price_record = PriceRecord.objects.filter(
                    fuel_type=product, 
                    effective_date__lte=timezone.now().date()
                ).order_by('-effective_date').first()
                if latest_price_record:
                    cleaned_data['price_per_liter_at_time'] = latest_price_record.price_per_liter
                    price = latest_price_record.price_per_liter
                else:
                    self.add_error('product_type', f"No active price record found for {product}.")
            # For 'OIL', price might need to be entered manually or handled differently.

        if liters and price and vehicle:
            transaction_value = liters * price
            # Ensure customer has enough balance
            # This check is simplified. A race condition could occur.
            # Consider using select_for_update on CODCustomer in the view.
            if vehicle.customer.current_balance < transaction_value:
                self.add_error(None, f"Insufficient balance for {vehicle.customer.name}. "
                                     f"Available: R{vehicle.customer.current_balance:.2f}, "
                                     f"Required for this transaction: R{transaction_value:.2f}")
        elif liters and not price and cleaned_data.get('product_type') != 'OIL':
             self.add_error('price_per_liter_at_time', 'Price could not be determined for the selected product.')


        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.request_user and self.request_user.has_perm('reconciliation.approve_codtransaction'): # Example permission
            instance.manager_approved_by = self.request_user
            instance.approval_datetime = timezone.now()
        
        # Calculate transaction_value_at_time before final save
        if instance.liters_dispensed and instance.price_per_liter_at_time:
            instance.transaction_value_at_time = instance.liters_dispensed * instance.price_per_liter_at_time
        
        if commit:
            instance.save()
            # The model's save method handles updating customer balance.
        return instance

#Fuel Orders
from django import forms
from django.utils import timezone
from .models import FuelOrder

class FuelOrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set expected delivery date default for new instances
        if not self.instance.pk:
            self.fields['expected_delivery_date'].initial = timezone.now().date()
        
        # Enforce consistent input styling
        self.fields['expected_delivery_date'].input_formats = ('%Y-%m-%d',)
        self.fields['quantity_ordered_liters'].widget.attrs.update({'step': '0.01'})
        self.fields['notes'].widget.attrs.update({'rows': 3})

    class Meta:
        model = FuelOrder
        fields = [
            'fuel_type',
            'quantity_ordered_liters',
            'buying_price_per_liter',
            'cost_paid_rands',
            'supplier_name',
            'order_date',
            'expected_delivery_date',
            'status',
            'ordered_by',
            'approved_by',
            'notes',
        ]
        labels = {
            'fuel_type': 'Type of Fuel',
            'quantity_ordered_liters': 'Quantity Ordered (Liters)',
            'buying_price_per_liter': 'Buying Price (R/L)',
            'cost_paid_rands': 'Total Paid (R)',
            'supplier_name': 'Supplier',
            'order_date': 'Order Date',
            'expected_delivery_date': 'Expected Delivery',
            'status': 'Order Status',
            'ordered_by': 'Ordered By',
            'approved_by': 'Approved By',
            'notes': 'Additional Notes',
        }
        widgets = {
            'quantity_ordered_liters': forms.NumberInput(attrs={'class': 'form-control'}),
            'buying_price_per_liter': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_paid_rands': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'ordered_by': forms.Select(attrs={'class': 'form-select'}),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and not instance.pk:
            instance.ordered_by = self.user
        if commit:
            instance.save()
        return instance


# Dynamically derive choices from the model
FUEL_TYPE_CHOICES = FuelOrder._meta.get_field('fuel_type').choices
STATUS_CHOICES = FuelOrder._meta.get_field('status').choices

class FuelOrderFilterForm(forms.Form):
    fuel_type = forms.ChoiceField(
        required=False,
        label="Fuel Type",
        choices=[('', 'All Types')] + list(FUEL_TYPE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': 'Filter by fuel type'
        })
    )

    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[('', 'All Statuses')] + list(STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': 'Filter by status'
        })
    )

    supplier_name = forms.CharField(
        required=False,
        label="Supplier",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Engen, Total, Puma',
            'aria-label': 'Filter by supplier name'
        })
    )
    
class ReceivedStockForm(forms.ModelForm):
    fuel_order = forms.ModelChoiceField(
        queryset=FuelOrder.objects.filter(status__in=['APPROVED', 'PARTIALLY_RECEIVED']),
        required=False,
        help_text="Select if this delivery corresponds to a placed order."
    )

    fuel_tank = forms.ModelChoiceField(
        queryset=FuelTank.objects.all(),
        help_text="Select the tank this fuel was delivered into."
    )

    class Meta:
        model = ReceivedStock
        fields = [
            'fuel_order',
            'fuel_tank',
            'quantity_received_liters',
            'delivery_date',
            'supplier_invoice_number',
            'notes'
        ]
        widgets = {
            'quantity_received_liters': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'form-control'
            }),
            'delivery_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }, format='%Y-%m-%dT%H:%M'),
            'supplier_invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional invoice reference'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Note any discrepancies or delivery context...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['delivery_date'].input_formats = ('%Y-%m-%dT%H:%M',)

        if not self.instance.pk:
            self.fields['delivery_date'].initial = timezone.now()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.logged_by = self.user
        if commit:
            instance.save()
        return instance

class DipRecordForm(forms.ModelForm):
    fuel_tank = forms.ModelChoiceField(
        queryset=FuelTank.objects.all(),
        help_text="Select the tank for this dip reading."
    )
    class Meta:
        model = DipRecord
        fields = ['fuel_tank', 'dip_type', 'dip_reading_liters', 'record_datetime', 'notes']
        # recorded_by will be set in the view
        widgets = {
            'dip_reading_liters': forms.NumberInput(attrs={'step': '0.01'}),
            'record_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['record_datetime'].input_formats = ('%Y-%m-%dT%H:%M',)
        if not self.instance.pk:
             self.fields['record_datetime'].initial = timezone.now()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.recorded_by = self.user
        if commit:
            instance.save()
            # Optionally, trigger tank level update based on dip logic here or in model save
        return instance


    
class CashierWarehouseAllocationForm(forms.Form):
    cashier = forms.ModelChoiceField(
        queryset=User.objects.filter(role='CASHIER'),
        label="Cashier",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    oil_product = forms.ModelChoiceField(
        queryset=OilProduct.objects.none(),  # Populated in __init__
        label="Oil Product",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label="Quantity to Allocate",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        annotated = OilProduct.objects.all()
        choices = [
            (product.id, f"{product.name} — {product.current_stock_units} units available")
            for product in annotated
        ]
        self.fields['oil_product'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        oil_product_id = cleaned_data.get('oil_product')
        quantity = cleaned_data.get('quantity')

        if oil_product_id and quantity:
            try:
                product = OilProduct.objects.get(id=oil_product_id.id if hasattr(oil_product_id, 'id') else oil_product_id)
            except OilProduct.DoesNotExist:
                raise forms.ValidationError("Selected oil product does not exist.")

            if product.current_stock_units < quantity:
                raise forms.ValidationError(
                    f"Not enough stock for {product.name}. "
                    f"Available: {product.current_stock_units}, "
                    f"Requested: {quantity}"
                )

        return cleaned_data


class StockTakeForm(forms.ModelForm):
    class Meta:
        model = StockTake
        fields = ['cashier', 'notes', 'document']

class StockTakeItemForm(AuditableForm):
    class Meta:
        model = StockTakeItem
        fields = ['oil_product', 'physical_quantity']

class FuelCashAdjustmentForm(forms.ModelForm):
    class Meta:
        model = FuelAdjustment
        fields = ['amount', 'direction', 'reason_note']
        labels = {
            'amount': "Adjustment Amount (R)",
            'direction': "Adjustment Type",
            'reason_note': "Reason for Adjustment",
        }

#ADD OIL PRODUCT
class ManagerOilProductForm(forms.ModelForm):
    class Meta:
        model = OilProduct
        fields = [
            'name',
            'description',
            'unit_of_measure',
            'buying_price',
            'selling_price',
            'current_stock_units',
            'low_stock_threshold',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Shell Helix HX5 5L',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional details about the product',
                'rows': 3,
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Unit, Liter, 500ml Bottle',
            }),
            'buying_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'e.g. 145.00',
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
            }),
            'current_stock_units': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'help_text': 'Trigger stock alerts when below this amount',
            }),
        }
        
class CombinedFuelOilSaleIngestionForm(forms.ModelForm):
    adjustment_amount = forms.DecimalField(
        label="Fuel Adjustment (R)",
        required=False,
        min_value=Decimal('0.00'),
        decimal_places=2,
        max_digits=12
    )

    adjustment_direction = forms.ChoiceField(
        label="Adjustment Type",
        choices=[('ADD', 'Add to Cash Submission'), ('SUB', 'Subtract from Cash Submission')],
        required=False
    )

    adjustment_note = forms.CharField(
        label="Reason for Adjustment",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    class Meta:
        model = CongestionEntry
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self._active_shift = kwargs.pop('active_shift', None)
        super().__init__(*args, **kwargs)

        if self._active_shift:
            self.initial['shift'] = self._active_shift.id
        else:
            print("❌ active_shift was not passed into form kwargs.")

        oil_product_selected = self.data.get('oil_product')
        oil_quantity_entered = self.data.get('oil_quantity_sold')

        self.fields['oil_quantity_sold'].required = bool(oil_product_selected and not oil_quantity_entered)

        self.fields['diesel_value_rands'].widget.attrs.update({
            'id': 'display_total_sale_diesel',
            'class': 'form-control'
        })

        self.fields['ulp_value_rands'].widget.attrs.update({
            'id': 'display_total_sale_ulp',
            'class': 'form-control'
        })

    def clean(self):
        cleaned_data = super().clean()

        diesel = cleaned_data.get('diesel_value_rands')
        ulp = cleaned_data.get('ulp_value_rands')

        if diesel is None or ulp is None:
            raise forms.ValidationError("Please enter both Diesel and ULP sale values.")

        for field in ['cash_submitted', 'speedpoint_submitted', 'total_cod_sales_value_shift']:
            value = cleaned_data.get(field)
            if value is not None and value < 0:
                self.add_error(field, "This value cannot be negative.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self._active_shift:
            instance.shift = self._active_shift

            oil_product_id = self.data.get('oil_product')
            oil_qty = self.cleaned_data.get('oil_quantity_sold') or Decimal('0.00')

            if oil_product_id and oil_qty > 0:
                try:
                    oil_product = OilProduct.objects.get(pk=oil_product_id)
                    cashier = instance.shift.cashier
                    stock = CashierOilWarehouse.objects.select_for_update().get(
                        cashier=cashier,
                        oil_product=oil_product
                    )

                    if stock.quantity < oil_qty:
                        raise ValidationError(f"❌ Insufficient stock of {oil_product.name}. Available: {stock.quantity}")

                    stock.quantity -= oil_qty
                    stock.save()

                except CashierOilWarehouse.DoesNotExist:
                    raise ValidationError("⚠️ No warehouse entry found for this cashier and oil product.")
                except OilProduct.DoesNotExist:
                    raise ValidationError("❌ The selected oil product does not exist.")

        if commit:
            instance.save()

        return instance
    
class StockChangeReportForm(forms.Form):
    tank = forms.ModelChoiceField(
        queryset=FuelTank.objects.all(),
        label="Fuel Tank",
        help_text="Select the tank to analyze"
    )

    dip_open = forms.ModelChoiceField(
        queryset=DipRecord.objects.none(),
        label="Opening Dip",
        help_text="Opening dip reading for the reporting period"
    )

    dip_close = forms.ModelChoiceField(
        queryset=DipRecord.objects.none(),
        label="Closing Dip",
        help_text="Closing dip reading for the reporting period"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tank_id = None

        if self.is_bound and 'tank' in self.data:
            try:
                tank_id = int(self.data.get('tank'))
            except (ValueError, TypeError):
                pass

        elif 'tank' in self.initial:
            tank_initial = self.initial.get('tank')
            if hasattr(tank_initial, 'id'):
                tank_id = tank_initial.id
            else:
                try:
                    tank_id = int(tank_initial)
                except (ValueError, TypeError):
                    pass

        if tank_id:
            self.fields['dip_open'].queryset = DipRecord.objects.filter(
                fuel_tank_id=tank_id
            ).order_by('-record_datetime')
            self.fields['dip_close'].queryset = DipRecord.objects.filter(
                fuel_tank_id=tank_id
            ).order_by('-record_datetime')