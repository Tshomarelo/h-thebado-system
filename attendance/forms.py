from django import forms
from .models import WorkSchedule, ClockIn, ClockOut, ShiftAdjustment, HourlyRate, Attendant, Shift, User

class ShiftAssignmentForm(forms.ModelForm):
    """
    Form for managers to assign shifts to attendants.
    """
    attendant = forms.ModelChoiceField(queryset=Attendant.objects.all(), label="Attendant")
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), label="Shift")
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Date")

    class Meta:
        model = WorkSchedule
        fields = ['attendant', 'shift', 'date', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class ClockInForm(forms.ModelForm):
    """
    Form for attendants to clock in.
    Attendant might be identified via employee_id or selected if it's a shared terminal.
    For simplicity, we'll allow selection here, but in a real scenario,
    this would often be tied to the logged-in user or an ID scan.
    """
    # We might want to auto-fill attendant based on logged-in user in the view
    # or have a field for employee_id to look up the attendant.
    attendant = forms.ModelChoiceField(
        queryset=Attendant.objects.all(),
        label="Select Your Name/ID",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    # Timestamp is auto_now_add, so not included in the form for direct user input.
    # Notes can be added if there's a reason for a slightly off-time clock-in.
    class Meta:
        model = ClockIn
        fields = ['attendant', 'notes'] # 'timestamp' is auto-generated
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional notes for clock-in'}),
        }

class ClockOutForm(forms.ModelForm):
    """
    Form for attendants to clock out.
    Similar to ClockInForm, attendant identification is key.
    """
    attendant = forms.ModelChoiceField(
        queryset=Attendant.objects.all(),
        label="Select Your Name/ID",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    # Timestamp is auto_now_add.
    class Meta:
        model = ClockOut
        fields = ['attendant', 'notes'] # 'timestamp' is auto-generated
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional notes for clock-out'}),
        }

class ManagerShiftAdjustmentForm(forms.ModelForm):
    """
    Form for managers to manually adjust clock-in/out times or record missed punches.
    """
    attendant = forms.ModelChoiceField(queryset=Attendant.objects.all(), label="Attendant")
    # adjusted_by will be set to the logged-in manager in the view.
    # original_clock_in and original_clock_out might be linked if editing an existing record.

    class Meta:
        model = ShiftAdjustment
        fields = [
            'attendant',
            'adjusted_clock_in',
            'adjusted_clock_out',
            'reason',
            # 'original_clock_in', # Optional: if linking to a specific flagged event
            # 'original_clock_out', # Optional
        ]
        widgets = {
            'adjusted_clock_in': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'adjusted_clock_out': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['adjusted_clock_in'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['adjusted_clock_out'].input_formats = ('%Y-%m-%dT%H:%M',)


class HourlyRateEntryForm(forms.ModelForm):
    """
    Form for managers to input or update hourly wage rates for attendants.
    """
    attendant = forms.ModelChoiceField(queryset=Attendant.objects.all(), label="Attendant")
    effective_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Effective Date")

    class Meta:
        model = HourlyRate
        fields = ['attendant', 'rate', 'effective_date']


# Placeholder forms for features requiring more models or complex logic:

class ShiftChangeRequestForm(forms.Form): # Placeholder - Needs ShiftChangeRequest model
    requesting_attendant = forms.ModelChoiceField(queryset=Attendant.objects.all(), label="Your Name/ID")
    original_schedule_entry = forms.ModelChoiceField(queryset=WorkSchedule.objects.all(), label="Shift to Change") # Needs filtering
    requested_shift_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    requested_shift_time = forms.ModelChoiceField(queryset=Shift.objects.all(), required=False)
    covering_attendant = forms.ModelChoiceField(queryset=Attendant.objects.all(), required=False, label="Covering Attendant (if applicable)")
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

class OvertimeCalculationForm(forms.Form): # Placeholder - Needs OvertimeRecord model
    work_schedule_entry = forms.ModelChoiceField(queryset=WorkSchedule.objects.all(), label="Original Scheduled Shift")
    actual_hours_worked = forms.DecimalField(max_digits=5, decimal_places=2)
    overtime_reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))

class ExceptionHandlingForm(forms.Form): # Placeholder
    attendant = forms.ModelChoiceField(queryset=Attendant.objects.all())
    date_of_exception = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    exception_type = forms.ChoiceField(choices=[('missed_clock_in', 'Missed Clock-In'), ('missed_clock_out', 'Missed Clock-Out'), ('incorrect_time', 'Incorrect Time')])
    explanation = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    # Could link to a ClockIn/ClockOut record if it exists but is flagged.