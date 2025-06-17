from django.contrib import admin
from .models import (
    FuelTank, Shift,
    PettyCashAllocation, PettyCashExpense, PriceRecord, BankDeposit,
    CODCustomer, CODVehicle, CODTransaction, FuelOrder, ReceivedStock, DipRecord,
    OilProduct, OilSale, BuyingPrice, Cashier, CongestionEntry, FuelAdjustment # Added BuyingPrice, removed Cashier
)


@admin.register(Cashier)
class CashierAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_id', 'email', 'phone_number', 'active')
    search_fields = ('name', 'employee_id', 'email')
    
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('stowe_shift_id', 'cashier_username', 'shift_type', 'start_datetime', 'end_datetime', 'source_of_data', 'sales_data_confirmed_by_cashier')
    list_filter = ('shift_type', 'start_datetime', 'cashier__username', 'source_of_data')
    search_fields = ('stowe_shift_id', 'cashier__username')
    raw_id_fields = ('cashier',) # For easier selection of users

    def cashier_username(self, obj):
        return obj.cashier.username
    cashier_username.short_description = 'Cashier'

class CODTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_vehicle_info', 'shift_info', 'cashier_verifying_username', 'product_type', 'liters_dispensed', 'transaction_value_at_time', 'transaction_datetime')
    list_filter = ('product_type', 'transaction_datetime', 'cashier_verifying__username', 'shift__stowe_shift_id')
    search_fields = ('customer_vehicle__registration_number', 'cashier_verifying__username', 'shift__stowe_shift_id')
    raw_id_fields = ('customer_vehicle', 'shift', 'cashier_verifying', 'manager_approved_by')

    def customer_vehicle_info(self, obj):
        return str(obj.customer_vehicle)
    customer_vehicle_info.short_description = 'COD Vehicle'

    def shift_info(self, obj):
        return obj.shift.stowe_shift_id
    shift_info.short_description = 'Shift ID'
    
    def cashier_verifying_username(self, obj):
        return obj.cashier_verifying.username
    cashier_verifying_username.short_description = 'Verifying Cashier'

class OilSaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'oil_product_name', 'shift_info', 'cashier_responsible_username', 'quantity_sold', 'total_sale_value', 'sale_datetime')
    list_filter = ('sale_datetime', 'cashier_responsible__username', 'oil_product__name', 'shift__stowe_shift_id')
    search_fields = ('oil_product__name', 'cashier_responsible__username', 'shift__stowe_shift_id')
    raw_id_fields = ('oil_product', 'shift', 'cashier_responsible', 'logged_by')

    def oil_product_name(self, obj):
        return obj.oil_product.name
    oil_product_name.short_description = 'Oil Product'

    def shift_info(self, obj):
        return obj.shift.stowe_shift_id
    shift_info.short_description = 'Shift ID'

    def cashier_responsible_username(self, obj):
        return obj.cashier_responsible.username
    cashier_responsible_username.short_description = 'Cashier Responsible'

class OilProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'selling_price', 'current_stock_units', 'buying_price','low_stock_threshold', 'unit_of_measure', 'display_is_low_stock')
    search_fields = ('name',)
    # list_filter = ('is_low_stock',) # Cannot filter directly on a property

    def display_is_low_stock(self, obj):
        return obj.is_low_stock # The property on the model
    display_is_low_stock.boolean = True # Display as an icon
    display_is_low_stock.short_description = 'Low Stock?'


class BuyingPriceAdmin(admin.ModelAdmin):
    list_display = ('product_type', 'oil_product_specific_name', 'buying_price_per_unit', 'effective_date', 'supplier', 'set_by_username')
    list_filter = ('product_type', 'effective_date', 'supplier', 'oil_product_specific__name')
    search_fields = ('product_type', 'oil_product_specific__name', 'supplier', 'set_by__username')
    raw_id_fields = ('oil_product_specific', 'set_by')

    def oil_product_specific_name(self, obj):
        return obj.oil_product_specific.name if obj.oil_product_specific else '-'
    oil_product_specific_name.short_description = 'Specific Oil Product'

    def set_by_username(self, obj):
        return obj.set_by.username
    set_by_username.short_description = 'Set By'

@admin.register(PettyCashAllocation)
class PettyCashAllocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'allocated_by', 'allocation_date', 'amount', 'is_active']
    list_filter = ['is_active', 'allocation_date']
    search_fields = ['allocated_by__username', 'notes']
    date_hierarchy = 'allocation_date'

@admin.register(PettyCashExpense)
class PettyCashExpenseAdmin(admin.ModelAdmin):
    list_display = ['id', 'allocation', 'expense_date', 'description', 'amount', 'logged_by']
    list_filter = ['expense_date']
    search_fields = ['description', 'allocation__allocated_to__username']
    date_hierarchy = 'expense_date'

@admin.register(ReceivedStock)
class ReceivedStockAdmin(admin.ModelAdmin):
    list_display = (
        'fuel_tank',
        'fuel_order',
        'quantity_received_liters',
        'cost_per_liter_display',
        'total_cost_rands_display',
        'delivery_date',
        'logged_by',
    )

    readonly_fields = ('cost_per_liter_display', 'total_cost_rands_display')

    def cost_per_liter_display(self, obj):
        return f"R {obj.cost_per_liter:.4f}" if obj.cost_per_liter else "—"
    cost_per_liter_display.short_description = "Price/Liter"

    def total_cost_rands_display(self, obj):
        return f"R {obj.total_cost_rands:.2f}" if obj.total_cost_rands else "—"
    total_cost_rands_display.short_description = "Total Cost"

# Register models with their custom admin classes
admin.site.register(Shift, ShiftAdmin)
admin.site.register(CODTransaction, CODTransactionAdmin)
admin.site.register(OilSale, OilSaleAdmin)
admin.site.register(OilProduct, OilProductAdmin)
admin.site.register(BuyingPrice, BuyingPriceAdmin)

# Register other models with default admin
admin.site.register([
    FuelTank,  BankDeposit, CODCustomer, CODVehicle, FuelOrder
])

@admin.register(DipRecord)
class DipRecordAdmin(admin.ModelAdmin):
    list_display = (
        'fuel_tank',
        'dip_type',
        'dip_reading_liters',
        'record_datetime',
        'recorded_by',
        'notes_snippet',
    )
    list_filter = ('dip_type', 'fuel_tank__fuel_type')
    search_fields = ('fuel_tank__fuel_type', 'recorded_by__username', 'notes')
    ordering = ('-record_datetime',)
    readonly_fields = ('created_at',)

    def notes_snippet(self, obj):
        return (obj.notes[:40] + '...') if obj.notes and len(obj.notes) > 40 else obj.notes or '—'
    notes_snippet.short_description = 'Notes'

#fuel adjustments

from django.contrib import admin
from .models import FuelAdjustment

@admin.register(FuelAdjustment)
class FuelAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        'shift',
        'amount',
        'direction',
        'reason_note',
        'recorded_by',
        'adjustment_datetime',  # replace if your model uses a different timestamp field
    )
    list_filter = (
        'direction',
        'adjustment_datetime',  # match your actual timestamp field
        'recorded_by',
    )
    search_fields = (
        'shift__id',
        'reason_note',
        'recorded_by__username',
    )
    date_hierarchy = 'adjustment_datetime'
    ordering = ['-adjustment_datetime']
    readonly_fields = ('recorded_by', 'adjustment_datetime')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
    

from django.contrib import admin
from .models import CongestionEntry

@admin.register(CongestionEntry)
class CongestionEntryAdmin(admin.ModelAdmin):
    list_display = (
        'stowe_shift_number',
        'shift',
        'diesel_volume_stowe',
        'diesel_unit_price',
        'ulp_volume_stowe',
        'ulp_unit_price',
        'total_cod_sales_value_shift',
        'cash_submitted',
        'speedpoint_submitted',
        'oil_product',
        'oil_quantity_sold',
        'submitted_at',
        'expected_revenue',
        'oil_total_sale',
        'actual_cash_received',
        'variance',
        'variance_label',
    )

    list_filter = ('shift', 'submitted_at')

    search_fields = ('stowe_shift_number', 'shift__id', 'shift__stowe_shift_id')

    readonly_fields = (
        'submitted_at',
        'diesel_unit_price',
        'ulp_unit_price',
        'expected_revenue',
        'oil_total_sale',
        'actual_cash_received',
        'variance',
        'variance_label',
    )

    ordering = ('-submitted_at',)

    fieldsets = (
        ('Entry Information', {
            'fields': ('stowe_shift_number', 'shift', 'submitted_at'),
        }),
        ('Fuel Volumes', {
            'fields': (
                'diesel_volume_stowe',
                'ulp_volume_stowe',
                'diesel_unit_price',
                'ulp_unit_price',
                'diesel_volume_returned_testing',
                'diesel_value_returned_testing',
                'ulp_volume_returned_testing',
                'ulp_value_returned_testing',
            ),
        }),
        ('Sales Details', {
            'fields': (
                'oil_product',
                'oil_quantity_sold',
                'total_cod_sales_value_shift',
                'cash_submitted',
                'speedpoint_submitted',
                'expected_revenue',
                'oil_total_sale',
                'actual_cash_received',
                'variance',
                'variance_label',
            ),
        }),
    )

class FuelOrderAdmin(admin.ModelAdmin):
    list_display = ['fuel_type', 'quantity_ordered_liters', 'buying_price_per_liter', 'cost_paid_rands', 'status', 'order_date']
    fields = [
        'fuel_type', 'quantity_ordered_liters', 'buying_price_per_liter', 'cost_paid_rands',
        'supplier_name', 'order_date', 'expected_delivery_date',
        'status', 'ordered_by', 'approved_by', 'notes'
    ]


class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ['fuel_type', 'effective_date', 'price_per_liter', 'truncated_price_per_liter']

    def truncated_price_per_liter(self, obj):
        return f"{obj.price_per_liter:.2f}"

    truncated_price_per_liter.short_description = 'Price/Liter (Truncated)'

admin.site.register(PriceRecord, PriceRecordAdmin)
