from django.contrib import admin
from .models import Attendant, Shift, WorkSchedule, ClockIn, ClockOut, ShiftAdjustment, HourlyRate

@admin.register(Attendant)
class AttendantAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user_full_name', 'user_username')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name')
    list_select_related = ('user',) # Optimize query by fetching user details

    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = 'Full Name'

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')
    search_fields = ('name',)

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('date', 'attendant_employee_id', 'shift_name', 'notes')
    list_filter = ('date', 'shift', 'attendant')
    search_fields = ('attendant__employee_id', 'attendant__user__username', 'shift__name', 'date')
    autocomplete_fields = ['attendant', 'shift'] # For easier selection in admin

    def attendant_employee_id(self, obj):
        return obj.attendant.employee_id
    attendant_employee_id.short_description = 'Attendant ID'

    def shift_name(self, obj):
        return obj.shift.name
    shift_name.short_description = 'Shift'

@admin.register(ClockIn)
class ClockInAdmin(admin.ModelAdmin):
    list_display = ('attendant_employee_id', 'timestamp', 'is_manual_adjustment')
    list_filter = ('timestamp', 'is_manual_adjustment', 'attendant')
    search_fields = ('attendant__employee_id', 'attendant__user__username')
    readonly_fields = ('timestamp',) # Typically auto_now_add fields are read-only after creation
    autocomplete_fields = ['attendant']

    def attendant_employee_id(self, obj):
        return obj.attendant.employee_id
    attendant_employee_id.short_description = 'Attendant ID'

@admin.register(ClockOut)
class ClockOutAdmin(admin.ModelAdmin):
    list_display = ('attendant_employee_id', 'timestamp', 'is_manual_adjustment')
    list_filter = ('timestamp', 'is_manual_adjustment', 'attendant')
    search_fields = ('attendant__employee_id', 'attendant__user__username')
    readonly_fields = ('timestamp',)
    autocomplete_fields = ['attendant']

    def attendant_employee_id(self, obj):
        return obj.attendant.employee_id
    attendant_employee_id.short_description = 'Attendant ID'

@admin.register(ShiftAdjustment)
class ShiftAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('attendant_employee_id', 'adjusted_by_username', 'adjustment_timestamp', 'reason')
    list_filter = ('adjustment_timestamp', 'adjusted_by', 'attendant')
    search_fields = ('attendant__employee_id', 'adjusted_by__username', 'reason')
    readonly_fields = ('adjustment_timestamp',)
    autocomplete_fields = ['attendant', 'adjusted_by', 'original_clock_in', 'original_clock_out']

    def attendant_employee_id(self, obj):
        return obj.attendant.employee_id
    attendant_employee_id.short_description = 'Attendant ID'

    def adjusted_by_username(self, obj):
        return obj.adjusted_by.username if obj.adjusted_by else 'N/A'
    adjusted_by_username.short_description = 'Adjusted By'

@admin.register(HourlyRate)
class HourlyRateAdmin(admin.ModelAdmin):
    list_display = ('attendant_employee_id', 'rate', 'effective_date')
    list_filter = ('effective_date', 'attendant')
    search_fields = ('attendant__employee_id', 'attendant__user__username', 'rate')
    autocomplete_fields = ['attendant']

    def attendant_employee_id(self, obj):
        return obj.attendant.employee_id
    attendant_employee_id.short_description = 'Attendant ID'
