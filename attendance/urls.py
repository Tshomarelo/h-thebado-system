from django.urls import path
from . import views # Views will be created in the next step

app_name = 'attendance'

urlpatterns = [
    # Work Schedule & Roster Management
    path('schedule/assign/', views.assign_shift, name='assign_shift'), # ShiftAssignmentForm
    path('schedule/overview/', views.work_schedule_overview, name='work_schedule_overview'), # WorkScheduleOverviewForm (Display)
    # path('schedule/change-request/new/', views.request_shift_change, name='request_shift_change'), # ShiftChangeRequestForm

    # Clock-In & Clock-Out Tracking
    path('clock-in/', views.clock_in, name='clock_in'), # ClockInForm
    path('clock-out/', views.clock_out, name='clock_out'), # ClockOutForm
    path('shift/adjust/<int:pk>/', views.adjust_shift_detail, name='adjust_shift_detail'), # ManagerShiftAdjustmentForm (for a specific entry)
    path('shift/adjust/new/', views.adjust_shift_new, name='adjust_shift_new'), # ManagerShiftAdjustmentForm (new entry)


    # Shift & Hour Calculation (Display views primarily)
    # path('summary/shift/', views.shift_summary, name='shift_summary'), # ShiftSummaryForm (Display)
    # path('summary/overtime/', views.overtime_summary, name='overtime_summary'), # OvertimeCalculationForm (Display/Entry)

    # Wage Calculation
    path('rates/entry/', views.hourly_rate_entry, name='hourly_rate_entry'), # HourlyRateEntryForm
    # path('wages/summary/', views.wage_summary, name='wage_summary'), # WageCalculationSummaryForm (Display)
    # path('payroll/report/', views.payroll_report, name='payroll_report'), # PayrollReportForm (Display/Generate)

    # Attendance & Shift Compliance
    # path('reports/attendance/', views.attendance_report, name='attendance_report'), # AttendanceReportForm (Display)
    # path('exceptions/handle/', views.handle_exception, name='handle_exception'), # ExceptionHandlingForm

    # Placeholder for a dashboard or main page for the attendance app
    path('', views.attendance_dashboard, name='dashboard'),
]