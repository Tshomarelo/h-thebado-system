from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # For restricting access
from django.contrib import messages
from .models import WorkSchedule, ClockIn, ClockOut, ShiftAdjustment, HourlyRate, Attendant, Shift
from .forms import (
    ShiftAssignmentForm, ClockInForm, ClockOutForm, ManagerShiftAdjustmentForm,
    HourlyRateEntryForm
)
# Import User model correctly
from django.conf import settings
User = settings.AUTH_USER_MODEL


@login_required
def attendance_dashboard(request):
    """
    Dashboard for the attendance module.
    Displays summary information or links to other features.
    """
    # Placeholder: Add context data as needed
    # For example, recent clock-ins, upcoming shifts, etc.
    work_schedules = WorkSchedule.objects.select_related('attendant__user', 'shift').order_by('-date')[:10]
    recent_clock_ins = ClockIn.objects.select_related('attendant__user').order_by('-timestamp')[:5]
    recent_clock_outs = ClockOut.objects.select_related('attendant__user').order_by('-timestamp')[:5]

    context = {
        'work_schedules': work_schedules,
        'recent_clock_ins': recent_clock_ins,
        'recent_clock_outs': recent_clock_outs,
        'page_title': 'Attendance Dashboard'
    }
    return render(request, 'attendance/dashboard.html', context)

@login_required
def assign_shift(request):
    """
    Allows managers to assign shifts to attendants.
    """
    if not request.user.is_staff: # Or a more specific permission check
        messages.error(request, "You do not have permission to assign shifts.")
        return redirect('attendance:dashboard')

    if request.method == 'POST':
        form = ShiftAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift assigned successfully.')
            return redirect('attendance:work_schedule_overview') # Or dashboard
    else:
        form = ShiftAssignmentForm()
    context = {
        'form': form,
        'page_title': 'Assign Shift'
    }
    return render(request, 'attendance/shift_assignment_form.html', context)

@login_required
def work_schedule_overview(request):
    """
    Displays weekly/monthly shift allocations.
    """
    # Add filtering by date range, attendant, etc. later
    schedules = WorkSchedule.objects.select_related('attendant__user', 'shift').order_by('date', 'shift__start_time')
    context = {
        'schedules': schedules,
        'page_title': 'Work Schedule Overview'
    }
    return render(request, 'attendance/work_schedule_overview.html', context)


@login_required # Or allow non-logged-in users if it's a kiosk
def clock_in(request):
    """
    Handles attendant clock-in.
    """
    if request.method == 'POST':
        form = ClockInForm(request.POST)
        if form.is_valid():
            # In a real system, you might want to check if the attendant is already clocked in
            # or if they are clocking in for a scheduled shift.
            clock_in_instance = form.save(commit=False)
            # If attendant is selected via form, it's already set.
            # If identifying by logged-in user:
            # try:
            #     attendant = request.user.attendant_profile
            #     clock_in_instance.attendant = attendant
            # except Attendant.DoesNotExist:
            #     messages.error(request, "Your user profile is not linked to an attendant.")
            #     return render(request, 'attendance/clock_in_form.html', {'form': form, 'page_title': 'Clock In'})
            clock_in_instance.save()
            messages.success(request, f"{clock_in_instance.attendant.user.username} clocked in successfully at {clock_in_instance.timestamp.strftime('%H:%M:%S')}.")
            return redirect('attendance:dashboard') # Or a confirmation page
    else:
        form = ClockInForm()
        # Potentially pre-fill attendant if user is logged in and linked
        # try:
        #     if hasattr(request.user, 'attendant_profile'):
        #         form.fields['attendant'].initial = request.user.attendant_profile
        # except Attendant.DoesNotExist:
        #     pass

    context = {
        'form': form,
        'page_title': 'Clock In'
    }
    return render(request, 'attendance/clock_in_form.html', context)

@login_required # Or allow non-logged-in users
def clock_out(request):
    """
    Handles attendant clock-out.
    """
    if request.method == 'POST':
        form = ClockOutForm(request.POST)
        if form.is_valid():
            # Similar checks as clock_in: ensure attendant is clocked in, etc.
            clock_out_instance = form.save(commit=False)
            # Logic to link to an open ClockIn record could be added here.
            clock_out_instance.save()
            messages.success(request, f"{clock_out_instance.attendant.user.username} clocked out successfully at {clock_out_instance.timestamp.strftime('%H:%M:%S')}.")
            return redirect('attendance:dashboard')
    else:
        form = ClockOutForm()
        # Pre-fill attendant if possible
        # try:
        #     if hasattr(request.user, 'attendant_profile'):
        #         form.fields['attendant'].initial = request.user.attendant_profile
        # except Attendant.DoesNotExist:
        #     pass
    context = {
        'form': form,
        'page_title': 'Clock Out'
    }
    return render(request, 'attendance/clock_out_form.html', context)

@login_required
def adjust_shift_new(request):
    """
    Allows managers to make a new manual shift adjustment.
    """
    if not request.user.is_staff: # Basic permission check
        messages.error(request, "You do not have permission to make shift adjustments.")
        return redirect('attendance:dashboard')

    if request.method == 'POST':
        form = ManagerShiftAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.adjusted_by = request.user
            adjustment.save()
            messages.success(request, 'Shift adjustment recorded successfully.')
            return redirect('attendance:dashboard') # Or a list of adjustments
    else:
        form = ManagerShiftAdjustmentForm()
    context = {
        'form': form,
        'page_title': 'New Shift Adjustment'
    }
    return render(request, 'attendance/shift_adjustment_form.html', context)

@login_required
def adjust_shift_detail(request, pk):
    """
    Allows managers to edit an existing manual shift adjustment.
    """
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to edit shift adjustments.")
        return redirect('attendance:dashboard')

    adjustment = get_object_or_404(ShiftAdjustment, pk=pk)
    if request.method == 'POST':
        form = ManagerShiftAdjustmentForm(request.POST, instance=adjustment)
        if form.is_valid():
            updated_adjustment = form.save(commit=False)
            updated_adjustment.adjusted_by = request.user # Ensure adjusted_by is current manager
            updated_adjustment.save()
            messages.success(request, 'Shift adjustment updated successfully.')
            return redirect('attendance:dashboard') # Or list of adjustments
    else:
        form = ManagerShiftAdjustmentForm(instance=adjustment)
    context = {
        'form': form,
        'adjustment': adjustment,
        'page_title': 'Edit Shift Adjustment'
    }
    return render(request, 'attendance/shift_adjustment_form.html', context)


@login_required
def hourly_rate_entry(request):
    """
    Allows managers to set or update hourly rates for attendants.
    """
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to set hourly rates.")
        return redirect('attendance:dashboard')

    if request.method == 'POST':
        form = HourlyRateEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hourly rate saved successfully.')
            return redirect('attendance:dashboard') # Or a list of rates
    else:
        form = HourlyRateEntryForm()

    hourly_rates = HourlyRate.objects.select_related('attendant__user').order_by('attendant__user__username', '-effective_date')
    context = {
        'form': form,
        'hourly_rates': hourly_rates,
        'page_title': 'Hourly Rate Entry'
    }
    return render(request, 'attendance/hourly_rate_entry_form.html', context)

# Placeholder views for other URLs defined in urls.py
# These will need to be implemented based on further requirements.

# def request_shift_change(request):
#     # ...
#     return render(request, 'attendance/shift_change_request_form.html', {})

# def shift_summary(request):
#     # ...
#     return render(request, 'attendance/shift_summary.html', {})

# def overtime_summary(request):
#     # ...
#     return render(request, 'attendance/overtime_summary.html', {})

# def wage_summary(request):
#     # ...
#     return render(request, 'attendance/wage_summary.html', {})

# def payroll_report(request):
#     # ...
#     return render(request, 'attendance/payroll_report.html', {})

# def attendance_report(request):
#     # ...
#     return render(request, 'attendance/attendance_report.html', {})

# def handle_exception(request):
#     # ...
#     return render(request, 'attendance/exception_handling_form.html', {})
