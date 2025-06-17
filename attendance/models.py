from django.db import models
from django.conf import settings # To get the AUTH_USER_MODEL

# It's good practice to use settings.AUTH_USER_MODEL to refer to the User model
# This makes your app more reusable if the project uses a custom User model.
User = settings.AUTH_USER_MODEL

class Attendant(models.Model):
    """
    Represents a petrol attendant.
    Links to the main User model for authentication and basic user info.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='attendant_profile')
    employee_id = models.CharField(max_length=50, unique=True, help_text="Unique employee identifier")
    # Add other attendant-specific fields if needed, e.g., contact_number

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_id})"

class Shift(models.Model):
    """
    Represents a work shift with a defined start and end time.
    """
    name = models.CharField(max_length=100, help_text="e.g., Morning Shift, Night Shift")
    start_time = models.TimeField(help_text="Shift start time")
    end_time = models.TimeField(help_text="Shift end time")
    # Consider adding a duration field or calculating it dynamically

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class WorkSchedule(models.Model):
    """
    Assigns attendants to specific shifts on particular dates.
    """
    attendant = models.ForeignKey(Attendant, on_delete=models.CASCADE, related_name='work_schedules')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='scheduled_attendants')
    date = models.DateField(help_text="Date of the shift")
    # Notes or specific instructions for this scheduled shift
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('attendant', 'date', 'shift') # Ensures an attendant isn't scheduled for the same shift twice on the same day
        ordering = ['date', 'shift__start_time']

    def __str__(self):
        return f"{self.attendant} on {self.date.strftime('%Y-%m-%d')} for {self.shift}"

class ClockEvent(models.Model):
    """
    Abstract base model for clock-in and clock-out events.
    """
    # Removed related_name from here to avoid clashes in inherited models.
    # It will be defined in ClockIn and ClockOut specifically.
    attendant = models.ForeignKey(Attendant, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Exact time of the event")
    # scheduled_shift can be linked here if clock-ins are tied to a specific WorkSchedule instance
    # scheduled_shift = models.ForeignKey(WorkSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    is_manual_adjustment = models.BooleanField(default=False, help_text="True if this record was manually adjusted/created")
    notes = models.TextField(blank=True, null=True, help_text="Reason for manual adjustment or any other notes")

    class Meta:
        abstract = True
        ordering = ['-timestamp']

class ClockIn(ClockEvent):
    """
    Records an attendant's clock-in event.
    """
    attendant = models.ForeignKey(Attendant, on_delete=models.CASCADE, related_name='clock_ins', related_query_name='clock_in')
    # Potentially link to WorkSchedule if clock-in is for a specific scheduled shift
    # work_schedule_entry = models.ForeignKey(WorkSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_schedule_clock_ins')


    def __str__(self):
        return f"Clock-In: {self.attendant} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class ClockOut(ClockEvent):
    """
    Records an attendant's clock-out event.
    """
    attendant = models.ForeignKey(Attendant, on_delete=models.CASCADE, related_name='clock_outs', related_query_name='clock_out')
    # Potentially link to WorkSchedule or ClockIn event
    # clock_in_event = models.OneToOneField(ClockIn, on_delete=models.SET_NULL, null=True, blank=True, related_name='clock_out_pair')
    # work_schedule_entry = models.ForeignKey(WorkSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_schedule_clock_outs')

    def __str__(self):
        return f"Clock-Out: {self.attendant} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class ShiftAdjustment(models.Model):
    """
    Allows managers to manually adjust clock-in/out times or record missed punches.
    This might be superseded or work in conjunction with setting `is_manual_adjustment` on ClockIn/ClockOut.
    For simplicity, this model can log adjustments made by managers.
    """
    attendant = models.ForeignKey(Attendant, on_delete=models.CASCADE, related_name='shift_adjustments')
    adjusted_clock_in = models.DateTimeField(null=True, blank=True, help_text="Manually set clock-in time")
    adjusted_clock_out = models.DateTimeField(null=True, blank=True, help_text="Manually set clock-out time")
    original_clock_in = models.ForeignKey(ClockIn, on_delete=models.SET_NULL, null=True, blank=True, related_name='adjustments_made')
    original_clock_out = models.ForeignKey(ClockOut, on_delete=models.SET_NULL, null=True, blank=True, related_name='adjustments_made')
    reason = models.TextField(help_text="Reason for the adjustment")
    adjusted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='made_adjustments', help_text="Manager who made the adjustment")
    adjustment_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjustment for {self.attendant} by {self.adjusted_by.username} on {self.adjustment_timestamp.strftime('%Y-%m-%d')}"

class HourlyRate(models.Model):
    """
    Stores the hourly wage rate for each attendant.
    Rates can change over time, so effective dates are important.
    """
    attendant = models.ForeignKey(Attendant, on_delete=models.CASCADE, related_name='hourly_rates')
    rate = models.DecimalField(max_digits=8, decimal_places=2, help_text="Hourly wage rate")
    effective_date = models.DateField(help_text="Date from which this rate is effective")
    # end_date = models.DateField(null=True, blank=True, help_text="Date until which this rate is effective (optional)")

    class Meta:
        ordering = ['attendant', '-effective_date']
        # unique_together = ('attendant', 'effective_date') # Ensure one rate per attendant per effective date

    def __str__(self):
        return f"{self.attendant}: ${self.rate}/hour (from {self.effective_date.strftime('%Y-%m-%d')})"

# Future models to consider based on requirements:
# - ShiftChangeRequest
# - OvertimeRecord
# - Deduction
# - PayrollReport
