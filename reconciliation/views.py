import json
from multiprocessing import context
import openpyxl
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from decimal import Decimal
from datetime import timedelta, date # date might not be used directly
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField # F, ExpressionWrapper might not be used now
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, DetailView # UpdateView removed for now
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib import messages
from .decorators import role_required
from reconciliation.models import Shift, CODCustomer, CongestionEntry
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncDate
from django.urls import reverse_lazy
import csv
from django.db.models import Q
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import StockTake, StockTakeItem
from .utils import calculate_stock_change_report
# from django.contrib.auth import get_user_model # User = get_user_model() not seen in snippets
from django.views.generic.edit import UpdateView
from django.db.models.functions import Cast
from datetime import datetime, timedelta
from collections import defaultdict

from .models import (
    Shift, PettyCashAllocation, PettyCashExpense,
    PriceRecord, BankDeposit, CODCustomer, CODVehicle, CODTransaction,
    FuelOrder, ReceivedStock, DipRecord, FuelTank, OilSale, OilProduct, BuyingPrice, FuelSale,
    FuelAdjustment, CongestionEntry, ExpenseCategory, BusinessExpense, StockTake, StockTakeItem, CashierOilWarehouse, DailyFuelSale,
    BusinessExpense
    
)
from .forms import (
    ShiftForm, PettyCashAllocationForm, PettyCashExpenseForm, 
    PriceRecordForm, BankDepositForm, CODCustomerForm, CODVehicleForm, CODTransactionForm,
    FuelOrderForm, ReceivedStockForm, DipRecordForm, CombinedFuelOilSaleIngestionForm,
    ManagerOilProductForm, StockTakeForm, StockTakeItemForm, CashierWarehouseAllocationForm, StockChangeReportForm,
    FuelOrderFilterForm
)
from .expense_forms import ExpenseCategoryForm, BusinessExpenseForm

User = get_user_model() 


# Shift Views
class ShiftListView(ListView):
    model = Shift
    template_name = 'reconciliation/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Shift.objects.select_related('cashier').order_by('-start_datetime')
        stowe_id = self.request.GET.get('stowe_id')
        cashier = self.request.GET.get('cashier')
        shift_type = self.request.GET.get('shift_type')
        date = self.request.GET.get('date')

        if stowe_id:
            queryset = queryset.filter(stowe_shift_id__icontains=stowe_id)

        if cashier:
            queryset = queryset.filter(
                Q(cashier__username__icontains=cashier) |
                Q(cashier__first_name__icontains=cashier) |
                Q(cashier__last_name__icontains=cashier)
            )

        if shift_type and shift_type.isdigit():
            queryset = queryset.filter(shift_type=int(shift_type))

        if date:
            queryset = queryset.filter(start_datetime__date=date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shift_type_choices'] = Shift.SHIFT_TYPE_CHOICES
        return context


class ShiftCreateView(LoginRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'reconciliation/shift_form.html'
    success_url = '/reconciliation/shifts/'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ShiftDetailView(LoginRequiredMixin, DetailView):
    model = Shift
    template_name = 'reconciliation/shift_detail.html'
    context_object_name = 'shift'
    login_url = 'users:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift = self.object

        # Cash submission
        cash_submission = getattr(shift, 'cash_submission', None)
        context['cash_submission_obj'] = cash_submission
        context['total_submitted'] = getattr(cash_submission, 'total_submitted', Decimal('0.00'))
        context['cod_reported'] = getattr(cash_submission, 'cod_sales_value_reported', Decimal('0.00'))
        context['original_variance'] = getattr(cash_submission, 'variance', Decimal('0.00'))

        # Congestion entry (fuel reconciliation)
        congestion_entry = getattr(shift, 'congestion_entry', None)
        expected_revenue = getattr(congestion_entry, 'expected_revenue', Decimal('0.00'))
        actual_received = getattr(congestion_entry, 'actual_cash_received', Decimal('0.00'))

        context['congestion_entry'] = congestion_entry
        context['expected_revenue'] = expected_revenue
        context['base_actual_received'] = actual_received

        # Adjustments
        fuel_adjustments = FuelAdjustment.objects.filter(shift=shift)
        total_adjustment_sum = sum(adj.signed_amount() for adj in fuel_adjustments) if fuel_adjustments.exists() else Decimal('0.00')

        final_actual_received = actual_received + total_adjustment_sum
        final_variance = expected_revenue - final_actual_received

        # Extra metadata
        context.update({
            'fuel_adjustments': fuel_adjustments,
            'total_adjustment_sum': total_adjustment_sum,
            'final_actual_received': final_actual_received,
            'final_variance': final_variance,
            'now': now()
        })

        return context

@method_decorator(
    role_required(allowed_roles=['CASHIER', 'MANAGER', 'SENIOR_MANAGER', 'CEO']),
    name='dispatch'
)

   
# Petty Cash Views (Reconstructing from memory/snippets)
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class PettyCashAllocationListView(LoginRequiredMixin, ListView):
    model = PettyCashAllocation
    template_name = 'reconciliation/pettycashallocation_list.html'
    context_object_name = 'allocations'
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class PettyCashAllocationCreateView(LoginRequiredMixin, CreateView):
    model = PettyCashAllocation
    form_class = PettyCashAllocationForm
    template_name = 'reconciliation/pettycashallocation_form.html'
    success_url = reverse_lazy('reconciliation:pettycashallocation_list')
    login_url = 'users:login'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # ✅ This line injects the user into the form
        return kwargs
    
    def form_invalid(self, form):
        print("❌ Form validation errors:", form.errors.as_data())
        return super().form_invalid(form)

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class PettyCashExpenseListView(LoginRequiredMixin, ListView):
    model = PettyCashExpense
    template_name = 'reconciliation/pettycashexpense_list.html'
    context_object_name = 'expenses'
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class PettyCashExpenseCreateView(LoginRequiredMixin, CreateView):
    model = PettyCashExpense
    form_class = PettyCashExpenseForm
    template_name = 'reconciliation/pettycashexpense_form.html'
    success_url = reverse_lazy('reconciliation:pettycashexpense_list')
    login_url = 'users:login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        print("✅ form_valid() called in PettyCashExpenseCreateView")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("❌ Form validation errors:", form.errors.as_data())
        return super().form_invalid(form)

# Fuel Price Record Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class PriceRecordListView(LoginRequiredMixin, ListView):
    model = PriceRecord
    template_name = 'reconciliation/pricerecord_list.html'
    context_object_name = 'prices'
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class PriceRecordCreateView(LoginRequiredMixin, CreateView):
    model = PriceRecord
    form_class = PriceRecordForm
    template_name = 'reconciliation/pricerecord_form.html'
    success_url = reverse_lazy('reconciliation:pricerecord_list')
    login_url = 'users:login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save()
        messages.success(self.request, "Price record saved successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error saving the price record.")
        return super().form_invalid(form)

# Bank Deposit Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class BankDepositListView(LoginRequiredMixin, ListView):
    model = BankDeposit
    template_name = 'reconciliation/bankdeposit_list.html'
    context_object_name = 'deposits'
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class BankDepositCreateView(LoginRequiredMixin, CreateView):
    model = BankDeposit
    form_class = BankDepositForm
    template_name = 'reconciliation/bankdeposit_form.html'
    success_url = reverse_lazy('reconciliation:bankdeposit_list')
    login_url = 'users:login'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user 
        return kwargs

# COD Customer Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class CODCustomerListView(LoginRequiredMixin, ListView):
    model = CODCustomer
    template_name = 'reconciliation/codcustomer_list.html'
    context_object_name = 'customers'
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class CODCustomerCreateView(LoginRequiredMixin, CreateView):
    model = CODCustomer
    form_class = CODCustomerForm
    template_name = 'reconciliation/codcustomer_form.html'
    success_url = reverse_lazy('reconciliation:codcustomer_list')
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class CODCustomerDetailView(LoginRequiredMixin, DetailView):
    model = CODCustomer
    template_name = 'reconciliation/codcustomer_detail.html'
    context_object_name = 'customer'
    login_url = 'users:login'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicles'] = CODVehicle.objects.filter(customer=self.object, is_active=True)
        context['transactions'] = CODTransaction.objects.filter(customer_vehicle__customer=self.object).order_by('-transaction_datetime')[:20]
        return context

# COD Vehicle Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class CODVehicleCreateView(LoginRequiredMixin, CreateView):
    model = CODVehicle
    form_class = CODVehicleForm
    template_name = 'reconciliation/codvehicle_form.html'
    login_url = 'users:login'
    def get_initial(self):
        initial = super().get_initial()
        customer_pk = self.kwargs.get('customer_pk')
        if customer_pk:
            initial['customer'] = get_object_or_404(CODCustomer, pk=customer_pk)
        return initial
    def form_valid(self, form):
        customer_pk = self.kwargs.get('customer_pk')
        if customer_pk:
            form.instance.customer = get_object_or_404(CODCustomer, pk=customer_pk)
        return super().form_valid(form)
    def get_success_url(self):
        if self.object and self.object.customer:
            return reverse_lazy('reconciliation:codcustomer_detail', kwargs={'pk': self.object.customer.pk})
        return reverse_lazy('reconciliation:codcustomer_list')

# COD Transaction Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class CODTransactionCreateView(LoginRequiredMixin, CreateView):
    model = CODTransaction
    form_class = CODTransactionForm
    template_name = 'reconciliation/codtransaction_form.html'
    login_url = 'users:login'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        # Example: Pass active shift or COD customer if creating from specific context
        # customer_pk = self.kwargs.get('customer_pk')
        # if customer_pk:
        #    kwargs['cod_customer'] = get_object_or_404(CODCustomer, pk=customer_pk)
        return kwargs
    def form_valid(self, form):
        product = form.cleaned_data.get('product_type')
        transaction_date = form.instance.transaction_datetime.date() if form.instance.transaction_datetime else timezone.now().date()
        if product and product != 'OIL':
            latest_price = PriceRecord.objects.filter(fuel_type=product, effective_date__lte=transaction_date).order_by('-effective_date').first()
            if latest_price:
                form.instance.price_per_liter_at_time = latest_price.price_per_liter
            else:
                form.add_error('product_type', f"No active price record found for {product} on {transaction_date}.")
                return self.form_invalid(form)
        elif product == 'OIL' and not form.cleaned_data.get('price_per_liter_at_time'): # Assuming price_per_liter_at_time is a field in the form for OIL
             form.add_error('price_per_liter_at_time', "Price for OIL must be entered or configured.")
             return self.form_invalid(form)
        if self.request.user.has_perm('reconciliation.approve_codtransaction'):
            form.instance.manager_approved_by = self.request.user
            form.instance.approval_datetime = timezone.now()
        return super().form_valid(form)
    def get_success_url(self):
        if self.object and self.object.customer_vehicle:
            return reverse_lazy('reconciliation:codcustomer_detail', kwargs={'pk': self.object.customer_vehicle.customer.pk})
        return reverse_lazy('reconciliation:codcustomer_list')

# Fuel Order Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class FuelOrderListView(LoginRequiredMixin, ListView):
    model = FuelOrder
    template_name = 'reconciliation/fuelorder_list.html'
    context_object_name = 'fuel_orders'
    login_url = 'users:login'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-order_date')
        self.filter_form = FuelOrderFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            fuel_type = self.filter_form.cleaned_data.get('fuel_type')
            status = self.filter_form.cleaned_data.get('status')
            supplier_name = self.filter_form.cleaned_data.get('supplier_name')

            if fuel_type:
                queryset = queryset.filter(fuel_type=fuel_type)
            if status:
                queryset = queryset.filter(status=status)
            if supplier_name:
                queryset = queryset.filter(supplier_name__icontains=supplier_name)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class FuelOrderCreateView(LoginRequiredMixin, CreateView):
    model = FuelOrder
    form_class = FuelOrderForm
    template_name = 'reconciliation/fuelorder_form.html'
    success_url = reverse_lazy('reconciliation:fuelorder_list')
    login_url = 'users:login'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

# Received Stock Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class ReceivedStockListView(LoginRequiredMixin, ListView):
    model = ReceivedStock
    template_name = 'reconciliation/receivedstock_list.html'
    context_object_name = 'received_stocks'
    login_url = 'users:login'
    paginate_by = 10

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class ReceivedStockCreateView(LoginRequiredMixin, CreateView):
    model = ReceivedStock
    form_class = ReceivedStockForm
    template_name = 'reconciliation/receivedstock_form.html'
    success_url = reverse_lazy('reconciliation:receivedstock_list')
    login_url = 'users:login'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

# Dip Record Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class DipRecordListView(LoginRequiredMixin, ListView):
    model = DipRecord
    template_name = 'reconciliation/diprecord_list.html'
    context_object_name = 'dip_records'
    login_url = 'users:login'
    paginate_by = 10

    def get_queryset(self):
        """
        Optionally add filtering here in the future:
        e.g. return DipRecord.objects.filter(recorded_by=self.request.user)
        """
        return super

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class DipRecordCreateView(LoginRequiredMixin, CreateView):
    model = DipRecord
    form_class = DipRecordForm
    template_name = 'reconciliation/diprecord_form.html'
    success_url = reverse_lazy('reconciliation:diprecord_list')
    login_url = 'users:login'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

# Function-based views (main_dashboard_overview, sales_volume_report)
# These were partially visible in snippets. I'll reconstruct their basic structure.
# Actual complex logic within them might need further review if issues arise.

@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def main_dashboard_overview(request):
    print("👉 Entered main_dashboard_overview")

    today = now().date()
    print(f"Today date: {today}")

    selected_month = request.GET.get('month')
    selected_cashier_id = request.GET.get('cashier_id')
    start_input = request.GET.get("start_date")
    end_input = request.GET.get("end_date")
    print(f"Filters - month: {selected_month}, cashier_id: {selected_cashier_id}, start_date: {start_input}, end_date: {end_input}")

    base_qs = CongestionEntry.objects.none()
    start_date = today
    end_date = today
    recon_data = []
    summary = {}
    totals = {
        'cash_submitted': 0,
        'speedpoint_submitted': 0,
        'oil_quantity_sold': 0,
    }

    chart_labels = []
    ulp_series = []
    diesel_series = []
    total_fuel_series = []

    try:
        if start_input and end_input:
            start_date = datetime.strptime(start_input, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_input, "%Y-%m-%d").date()
            base_qs = CongestionEntry.objects.filter(submitted_at__date__range=(start_date, end_date))
            print(f"Filtered by custom date range {start_date} to {end_date}, entries count: {base_qs.count()}")

        elif selected_month:
            year, month = map(int, selected_month.split('-'))
            base_qs = CongestionEntry.objects.filter(
                shift__start_datetime__year=year,
                shift__start_datetime__month=month
            )
            print(f"Filtered by selected month {year}-{month}, entries count: {base_qs.count()}")

            if selected_cashier_id:
                base_qs = base_qs.filter(shift__cashier__id=selected_cashier_id)
                print(f"Filtered by cashier {selected_cashier_id}, entries count: {base_qs.count()}")

        else:
            base_qs = CongestionEntry.objects.filter(shift__start_datetime__date=today)
            print(f"Default filtered by today {today}, entries count: {base_qs.count()}")

        summary = base_qs.aggregate(
            total_cash=Sum('cash_submitted'),
            total_card=Sum('speedpoint_submitted'),
            total_diesel=Sum('diesel_volume_stowe'),
            total_ulp=Sum('ulp_volume_stowe'),
            total_cod=Sum('total_cod_sales_value_shift'),
            total_oil=Sum('oil_quantity_sold'),
        ) or {}
        print(f"Aggregated summary: {summary}")

        trend_data = (
            base_qs
            .annotate(entry_date=TruncDate("submitted_at"))
            .values("entry_date")
            .annotate(
                ulp_total=Sum("ulp_volume_stowe"),
                diesel_total=Sum("diesel_volume_stowe")
            )
            .order_by("entry_date")
        )
        print(f"Trend data points count: {len(trend_data)}")

        for entry in trend_data:
            date_str = entry["entry_date"].strftime("%Y-%m-%d")
            ulp = float(entry["ulp_total"] or 0)
            diesel = float(entry["diesel_total"] or 0)
            chart_labels.append(date_str)
            ulp_series.append(ulp)
            diesel_series.append(diesel)
            total_fuel_series.append(round(ulp + diesel, 2))

        print(f"Chart labels: {chart_labels}")
        print(f"ULP series: {ulp_series}")
        print(f"Diesel series: {diesel_series}")
        print(f"Total fuel series: {total_fuel_series}")

        if selected_month:
            entries = base_qs.values('shift__cashier__username').annotate(
                cash_submitted=Sum('cash_submitted'),
                speedpoint_submitted=Sum('speedpoint_submitted'),
                oil_quantity_sold=Sum('oil_quantity_sold'),
            )
            print(f"Monthly recon entries count: {len(entries)}")

            for entry in entries:
                recon_data.append({
                    'cashier': entry['shift__cashier__username'],
                    'cash_submitted': entry['cash_submitted'] or 0,
                    'speedpoint_submitted': entry['speedpoint_submitted'] or 0,
                    'oil_quantity_sold': entry['oil_quantity_sold'] or 0,
                })
                totals['cash_submitted'] += entry['cash_submitted'] or 0
                totals['speedpoint_submitted'] += entry['speedpoint_submitted'] or 0
                totals['oil_quantity_sold'] += entry['oil_quantity_sold'] or 0

            print(f"Recon data: {recon_data}")
            print(f"Recon totals: {totals}")

    except Exception as e:
        print("🔥 View error:", str(e))

    context = {
        'page_title': 'Main Dashboard Overview',
        'sales_trend_data': json.dumps({
            "labels": chart_labels,
            "ulp": ulp_series,
            "diesel": diesel_series,
            "total": total_fuel_series,
        }),
        'fuel_stock_data': json.dumps({"labels": [], "data": []}),
        'oil_stock_summary': [],
        'recent_shifts_summary': Shift.objects.order_by('-start_datetime')[:5],
        'cod_customer_summary': CODCustomer.objects.filter(is_active=True).order_by('-current_balance')[:5],
        'start_date': start_input or start_date.strftime('%Y-%m-%d'),
        'end_date': end_input or end_date.strftime('%Y-%m-%d'),
        'fuel_type_filter': 'ALL',
        'period_filter': 'weekly',
        'fuel_type_choices': [('ALL', 'All Fuel Types'), ('ULP', 'ULP'), ('DIESEL', 'Diesel')],
        'period_choices': [
            ('custom', 'Custom Range'),
            ('daily', 'Today'),
            ('weekly', 'This Week'),
            ('monthly', 'This Month'),
        ],
        'eod_summary': summary,
        'selected_month': selected_month or today.strftime('%Y-%m'),
        'selected_cashier_id': selected_cashier_id,
        'cashiers': User.objects.filter(role='CASHIER').order_by('username'),
        'recon_data': recon_data,
        'recon_totals': totals,
    }

    print("👉 Rendering main_dashboard_overview.html with context")
    return render(request, 'reconciliation/main_dashboard_overview.html', context)


#View for excel export
def export_excel(request):
    month = request.GET.get('month')
    cashier_id = request.GET.get('cashier')
    
    # Filter queryset based on selected month and cashier
    queryset = CongestionEntry.objects.filter(submitted_at__month=month[-2:], submitted_at__year=month[:4])
    
    if cashier_id:
        queryset = queryset.filter(shift__cashier_id=cashier_id)
    
    # Calculate totals for the columns we need
    totals = queryset.aggregate(
        total_cash_submitted=Sum('cash_submitted'),
        total_speedpoint_submitted=Sum('speedpoint_submitted'),
        total_oil_quantity_sold=Sum('oil_quantity_sold')
    )
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Monthly Recons"

    # Header
    ws.append(['Cashier', 'Hard Cash', 'Speedpoint', 'Oil Sales'])

    # Add data rows
    for item in queryset:
        ws.append([
            str(item.shift.cashier.username),
            float(item.cash_submitted),
            float(item.speedpoint_submitted),
            float(item.oil_quantity_sold or 0)
        ])
    
    # Add totals row
    ws.append(['TOTAL', 
               float(totals['total_cash_submitted'] or 0), 
               float(totals['total_speedpoint_submitted'] or 0), 
               float(totals['total_oil_quantity_sold'] or 0)
    ])

    # Set response for Excel download
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Cashier_Recons_{month}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'

    wb.save(response)
    return response

#PDF Views
def export_pdf(request):
    month = request.GET.get('month')
    cashier_id = request.GET.get('cashier')
    
    # Filter queryset based on selected month and cashier
    queryset = CongestionEntry.objects.filter(submitted_at__month=month[-2:], submitted_at__year=month[:4])
    
    if cashier_id:
        queryset = queryset.filter(shift__cashier_id=cashier_id)
    
    # Calculate totals for the columns we need
    totals = queryset.aggregate(
        total_cash_submitted=Sum('cash_submitted'),
        total_speedpoint_submitted=Sum('speedpoint_submitted'),
        total_oil_quantity_sold=Sum('oil_quantity_sold')
    )
    
    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f"Cashier_Recons_{month}.pdf"
    response['Content-Disposition'] = f'attachment; filename={filename}'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Define starting Y position for drawing the table
    y = height - 40
    p.setFont("Helvetica", 10)
    
    # Header row
    p.drawString(50, y, "Cashier")
    p.drawString(150, y, "Hard Cash")
    p.drawString(250, y, "Speedpoint")
    p.drawString(350, y, "Oil Sales")
    
    y -= 20
    
    # Add data rows
    for item in queryset:
        p.drawString(50, y, str(item.shift.cashier.username))
        p.drawString(150, y, f"{float(item.cash_submitted):,.2f}")
        p.drawString(250, y, f"{float(item.speedpoint_submitted):,.2f}")
        p.drawString(350, y, f"{float(item.oil_quantity_sold or 0):,.2f}")
        y -= 20
    
    # Add total row
    p.drawString(50, y, "TOTAL")
    p.drawString(150, y, f"{float(totals['total_cash_submitted'] or 0):,.2f}")
    p.drawString(250, y, f"{float(totals['total_speedpoint_submitted'] or 0):,.2f}")
    p.drawString(350, y, f"{float(totals['total_oil_quantity_sold'] or 0):,.2f}")
    
    # Save the PDF to the response
    p.showPage()
    p.save()
    
    return response


def export_shifts_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shift_records.csv"'

    writer = csv.writer(response)
    writer.writerow(['STOWE ID', 'Cashier', 'Shift Type', 'Start Time', 'End Time'])

    for shift in Shift.objects.select_related('cashier').all():
        writer.writerow([
            shift.stowe_shift_id,
            shift.cashier.get_full_name() if hasattr(shift.cashier, 'get_full_name') else shift.cashier.username,
            shift.get_shift_type_display(),
            shift.start_datetime.strftime('%Y-%m-%d %H:%M'),
            shift.end_datetime.strftime('%Y-%m-%d %H:%M')
        ])

    return response



def generate_shift_pdf(request, pk):
    shift = Shift.objects.select_related('cashier').get(pk=pk)

    # Resolve congestion_entry and adjustments safely
    congestion_entry = getattr(shift, 'congestion_entry', None)
    expected_revenue = getattr(congestion_entry, 'expected_revenue', 0)
    actual_received = getattr(congestion_entry, 'actual_cash_received', 0)

    fuel_adjustments = FuelAdjustment.objects.filter(shift=shift)
    total_adjustment_sum = sum(adj.signed_amount() for adj in fuel_adjustments) if fuel_adjustments.exists() else 0

    final_actual_received = actual_received + total_adjustment_sum
    final_variance = expected_revenue - final_actual_received

    template = get_template('reconciliation/shift_pdf.html')
    context = {
        'shift': shift,
        'congestion_entry': congestion_entry,
        'expected_revenue': expected_revenue,
        'base_actual_received': actual_received,
        'fuel_adjustments': fuel_adjustments,
        'total_adjustment_sum': total_adjustment_sum,
        'final_actual_received': final_actual_received,
        'final_variance': final_variance,
        'now': now(),
        'user': request.user
    }

    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Shift_{shift.pk}_Summary.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse(f'Error generating PDF: {pisa_status.err}', status=500)

    return response

def daily_fuel_sales_summary(request):
    # Get filter parameters from GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    shift_id = request.GET.get('shift_id')
    cashier_id = request.GET.get('cashier_id')

    # Base queryset
    entries = CongestionEntry.objects.all()

    # Filter by date range
    if start_date and end_date:
        entries = entries.filter(submitted_at__date__range=[start_date, end_date])

    # Filter by shift if given
    if shift_id:
        entries = entries.filter(shift_id=shift_id)

    # Filter by cashier if given (assuming Shift model has cashier field)
    if cashier_id:
        entries = entries.filter(shift__cashier_id=cashier_id)

    # Annotate sale_date (date part of submitted_at)
    entries = entries.annotate(sale_date=TruncDate('submitted_at'))

    # Calculate fuel sold volumes (stowe - returned/testing)
    diesel_sold = ExpressionWrapper(
        F('diesel_volume_stowe') - Coalesce(F('diesel_volume_returned_testing'), 0),
        output_field=DecimalField(max_digits=10, decimal_places=2)
    )
    ulp_sold = ExpressionWrapper(
        F('ulp_volume_stowe') - Coalesce(F('ulp_volume_returned_testing'), 0),
        output_field=DecimalField(max_digits=10, decimal_places=2)
    )



# Daily fuel sales summary grouped by sale_date
    daily_summary = (
    entries.values('sale_date')
    .annotate(
        diesel_sold_liters=Sum('diesel_volume_stowe'),
        ulp_sold_liters=Sum('ulp_volume_stowe'),
        cod_value=Sum('total_cod_sales_value_shift'),
        cash=Sum('cash_submitted'),
        card=Sum('speedpoint_submitted'),
    )
    .order_by('-sale_date')
)

    # Calculate grand totals
    grand_total = daily_summary.aggregate(
        total_diesel=Sum('diesel_sold_liters'),
        total_ulp=Sum('ulp_sold_liters'),
        total_cod=Sum('cod_value'),
        total_cash=Sum('cash'),
        total_card=Sum('card'),
    )

    context = {
        'daily_summary': daily_summary,
        'grand_total': grand_total,
        'start_date': start_date,
        'end_date': end_date,
        'shift_id': shift_id,
        'cashier_id': cashier_id,
        'shifts': Shift.objects.all(),
        'cashiers': User.objects.filter(role='CASHIER'),
    }
    return render(request, 'reconciliation/daily_fuel_sales_summary.html', context)



@login_required
@role_required(allowed_roles=['SENIOR_MANAGER'])
def allocate_oil_to_cashier(request):
    form = CashierWarehouseAllocationForm(request.POST or None)

    # Fetch oil products with available stock for UI display
    available_products = OilProduct.objects.filter(current_stock_units__gt=0).order_by('name')

    if request.method == 'POST' and form.is_valid():
        cashier = form.cleaned_data['cashier']
        oil_product = form.cleaned_data['oil_product']
        quantity = form.cleaned_data['quantity']

        if quantity <= 0:
            form.add_error('quantity', 'Quantity must be greater than zero.')
        elif oil_product.current_stock_units < quantity:
            form.add_error('quantity', f"Only {oil_product.current_stock_units} units available.")
        else:
            try:
                with transaction.atomic():
                    # Decrease from main warehouse
                    oil_product.current_stock_units -= quantity
                    oil_product.save(update_fields=['current_stock_units'])

                    # Allocate to cashier warehouse
                    warehouse, _ = CashierOilWarehouse.objects.get_or_create(
                        cashier=cashier,
                        oil_product=oil_product,
                        defaults={'quantity': 0}
                    )
                    warehouse.quantity += quantity
                    warehouse.save(update_fields=['quantity'])

                messages.success(
                    request,
                    f"✅ {quantity} units of {oil_product.name} allocated to {cashier.get_full_name() or cashier.username}."
                )
                return redirect(reverse('reconciliation:oil_allocation_success'))

            except Exception as e:
                form.add_error(None, f"Unexpected error occurred: {str(e)}")

    return render(request, 'reconciliation/allocate_oil_form.html', {
        'form': form,
        'available_products': available_products,
        'page_title': 'Allocate Oil to Cashier Warehouse'
    })

def allocation_success_view(request):
    return render(request, 'reconciliation/allocation_success.html', {
        'page_title': 'Allocation Complete'
    })
    
def allocation_list_view(request):
    allocations = CashierOilWarehouse.objects.select_related('cashier', 'oil_product').order_by('-last_updated')
    return render(request, 'reconciliation/allocate_oil_list.html', {
        'allocations': allocations
    })

@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def stocktake_list(request):
    stocktakes = StockTake.objects.all()
    context = {
        'stocktakes': stocktakes,
        'page_title': 'Stock Takes'
    }
    return render(request, 'reconciliation/stocktake_list.html', context)

@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def stocktake_create(request):
    if request.method == 'POST':
        form = StockTakeForm(request.POST, request.FILES)
        if form.is_valid():
            stocktake = form.save()
            # Logic to create stocktake items will be handled in a separate view or via JS
            return redirect('reconciliation:stocktake_detail', pk=stocktake.pk)
    else:
        form = StockTakeForm()

    context = {
        'form': form,
        'page_title': 'Create Stock Take'
    }
    return render(request, 'reconciliation/stocktake_form.html', context)

@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def stocktake_detail(request, pk):
    stocktake = get_object_or_404(StockTake, pk=pk)
    
    if request.method == 'POST':
        # This is a simplified approach. A more robust solution would use a formset.
        for product in CashierOilWarehouse.objects.filter(cashier=stocktake.cashier):
            physical_quantity = request.POST.get(f'product_{product.oil_product.pk}')
            if physical_quantity:
                StockTakeItem.objects.create(
                    stock_take=stocktake,
                    oil_product=product.oil_product,
                    system_quantity=product.quantity,
                    physical_quantity=physical_quantity
                )
        return redirect('reconciliation:stocktake_detail', pk=pk)

    items = stocktake.items.all()
    cashier_warehouse_items = CashierOilWarehouse.objects.filter(cashier=stocktake.cashier)

    context = {
        'stocktake': stocktake,
        'items': items,
        'cashier_warehouse_items': cashier_warehouse_items,
        'page_title': f'Stock Take for {stocktake.cashier.username} on {stocktake.date}'
    }
    return render(request, 'reconciliation/stocktake_detail.html', context)

# Expense Category Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class ExpenseCategoryListView(LoginRequiredMixin, ListView):
    model = ExpenseCategory
    template_name = 'reconciliation/expensecategory_list.html'
    context_object_name = 'categories'
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class ExpenseCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'reconciliation/expensecategory_form.html'
    success_url = reverse_lazy('reconciliation:expensecategory_list')
    login_url = 'users:login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # ✅ Pass the request into the form
        return kwargs

# Business Expense Views
@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class BusinessExpenseListView(LoginRequiredMixin, ListView):
    model = BusinessExpense
    template_name = 'reconciliation/businessexpense_list.html'
    context_object_name = 'expenses'
    login_url = 'users:login'

@method_decorator(role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO']), name='dispatch')
class BusinessExpenseCreateView(LoginRequiredMixin, CreateView):
    model = BusinessExpense
    form_class = BusinessExpenseForm
    template_name = 'reconciliation/businessexpense_form.html'
    success_url = reverse_lazy('reconciliation:businessexpense_list')
    login_url = 'users:login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

def monthly_fuel_revenue_report(request):
    selected_month = request.GET.get('month') or timezone.now().strftime('%Y-%m')
    year, month = map(int, selected_month.split('-'))

    shifts = Shift.objects.filter(start_datetime__year=year, start_datetime__month=month)
    print("Loaded", shifts.count(), "shifts for", selected_month, flush=True)

    report_data = []
    total_expected_revenue = 0
    total_actual_revenue = 0

    for shift in shifts:
        if hasattr(shift, 'congestion_entry'):
            congestion = shift.congestion_entry
            expected = congestion.expected_revenue or 0
            actual = congestion.actual_cash_received or 0
        else:
            expected = 0
            actual = 0

        variance = expected - actual

        report_data.append({
            'shift': shift,
            'expected_revenue': expected,
            'actual_revenue': actual,
            'variance': variance,
        })

        total_expected_revenue += expected
        total_actual_revenue += actual

    total_variance = total_expected_revenue - total_actual_revenue

    context = {
        'report_data': report_data,
        'total_expected_revenue': total_expected_revenue,
        'total_actual_revenue': total_actual_revenue,
        'total_variance': total_variance,
        'selected_month': selected_month,
    }

    return render(request, 'reconciliation/monthly_fuel_revenue_report.html', context)

def variance_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    cashier_id = request.GET.get('cashier_id')

    # Filter base queryset
    entries = CongestionEntry.objects.select_related('shift', 'shift__cashier')

    if start_date and end_date:
        entries = entries.filter(shift__start_datetime__date__range=[start_date, end_date])
    if cashier_id:
        entries = entries.filter(shift__cashier_id=cashier_id)

    report_data = []
    for entry in entries:
        report_data.append({
            'shift': entry.shift,
            'expected_revenue': entry.expected_revenue,
            'actual_received': entry.actual_cash_received,
            'variance': entry.variance,
            'variance_label': entry.variance_label,
        })

    context = {
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'cashier_id': cashier_id,
        'cashiers': User.objects.filter(role='CASHIER'),
    }
    return render(request, 'reconciliation/variance_report.html', context)

@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def cashier_warehouse_report(request):
    warehouses = CashierOilWarehouse.objects.all()
    context = {
        'warehouses': warehouses,
        'page_title': 'Cashier Warehouse Report'
    }
    return render(request, 'reconciliation/cashier_warehouse_report.html', context)

@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def oil_stock_report(request):
    cashier_id = request.GET.get('cashier_id')
    warehouses = CashierOilWarehouse.objects.all()
    if cashier_id:
        warehouses = warehouses.filter(cashier_id=cashier_id)
    
    context = {
        'warehouses': warehouses,
        'cashiers': User.objects.filter(role='CASHIER'),
        'selected_cashier_id': cashier_id,
        'page_title': 'Oil Stock Report'
    }
    return render(request, 'reconciliation/oil_stock_report.html', context)


@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def oil_sales_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    cashier_id = request.GET.get('cashier_id')

    sales = OilSale.objects.select_related('cashier_responsible', 'oil_product')

    if start_date and end_date:
        sales = sales.filter(sale_datetime__date__range=[start_date, end_date])

    if cashier_id:
        sales = sales.filter(cashier_responsible_id=cashier_id)

    sales = sales.order_by('-sale_datetime')

    # Calculate total per sale and annotate in Python
    for sale in sales:
        sale.line_total = sale.quantity_sold * sale.price_per_unit_at_sale

    # Totals per cashier (Python aggregation for full flexibility)
    per_cashier_totals = {}
    grand_total = Decimal('0.00')

    for sale in sales:
        cashier = sale.cashier_responsible.username
        subtotal = per_cashier_totals.get(cashier, Decimal('0.00'))
        subtotal += sale.line_total
        per_cashier_totals[cashier] = subtotal
        grand_total += sale.line_total

    context = {
        'sales': sales,
        'cashiers': User.objects.filter(role='CASHIER'),
        'start_date': start_date,
        'end_date': end_date,
        'selected_cashier_id': cashier_id,
        'per_cashier_totals': per_cashier_totals,
        'grand_total': grand_total,
        'page_title': 'Oil Sales Report',
        'now': now(),
        'user': request.user,
    }

    return render(request, 'reconciliation/oil_sales_report.html', context)



@method_decorator(role_required(allowed_roles=['SENIOR_MANAGER', 'CEO']), name='dispatch')
class CongestionEntryUpdateView(LoginRequiredMixin, UpdateView):
    model = CongestionEntry
    form_class = CombinedFuelOilSaleIngestionForm
    template_name = 'reconciliation/combined_fuel_oil_ingestion_form.html'
    login_url = 'users:login'

    def get_success_url(self):
        return reverse_lazy('reconciliation:shift_detail', kwargs={'pk': self.object.shift.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Review / Adjust Congestion Entry for Shift {self.object.shift.stowe_shift_id}"
        return context
        return render(request, 'reconciliation/oil_sales_report.html', context)

@method_decorator(user_passes_test(lambda u: u.is_staff or u.groups.filter(name='Managers').exists()), name='dispatch')
class OilProductCreateView(CreateView):
    model = OilProduct
    form_class = ManagerOilProductForm
    template_name = 'reconciliation/oilproduct_form.html'
    success_url = reverse_lazy('reconciliation:oilproduct_list')
  # you can customize this
    
class OilProductListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = OilProduct
    template_name = 'reconciliation/oilproduct_list.html'
    context_object_name = 'products'
    ordering = ['name']

    def get_queryset(self):
        return OilProduct.objects.annotate(
            margin=F('selling_price') - F('buying_price')
        ).order_by(*self.ordering)

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role in ['MANAGER', 'SENIOR_MANAGER', 'CEO']
   
class CombinedFuelOilIngestionFormView(LoginRequiredMixin, FormView):
    template_name = 'reconciliation/combined_fuel_oil_ingestion_form.html'
    form_class = CombinedFuelOilSaleIngestionForm
    login_url = 'users:login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        shift_id = self.request.GET.get('shift')
        kwargs['active_shift'] = Shift.objects.filter(pk=shift_id).first()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift_id = self.request.GET.get('shift')
        shift = Shift.objects.filter(pk=shift_id).first()
        context['shift'] = shift
        context['cashier_name'] = shift.cashier.username if shift else ''
        context['page_title'] = "Combined Shift Data Ingestion"

        if shift and shift.cashier:
            warehouse_qs = CashierOilWarehouse.objects.filter(
                cashier=shift.cashier
            ).select_related('oil_product')

            oil_products_data = {
                str(w.oil_product.id): {
                    "name": w.oil_product.name,
                    "selling_price": str(w.oil_product.selling_price),
                    "current_stock_units": str(w.quantity),
                    "is_low_stock": w.quantity < float(w.oil_product.low_stock_threshold),
                } for w in warehouse_qs
            }

            context['oil_product_choices'] = [
                (str(w.oil_product.id), w.oil_product.name) for w in warehouse_qs
            ]

            context['oil_prices_json'] = json.dumps({
                str(w.oil_product.id): str(w.oil_product.selling_price)
                for w in warehouse_qs
            })

            context['oil_products_data_json'] = json.dumps(oil_products_data)

        return context

    def form_valid(self, form):
        print("🔧 [form_valid] Entered form_valid()")

        shift = form.cleaned_data.get('shift')
        print(f"🧾 [form_valid] Retrieved shift: {shift}")

        if not shift:
            print("❌ [form_valid] Shift is missing from cleaned_data")
            messages.error(self.request, "Shift information is missing.")
            return self.form_invalid(form)

        now = timezone.now()
        user = self.request.user

        diesel_value = form.cleaned_data.get('diesel_value_rands') or Decimal('0.00')
        ulp_value = form.cleaned_data.get('ulp_value_rands') or Decimal('0.00')
        diesel_volume = form.cleaned_data.get('diesel_volume_stowe') or Decimal('0.00')
        ulp_volume = form.cleaned_data.get('ulp_volume_stowe') or Decimal('0.00')

        print(f"⛽ diesel_value: {diesel_value}, volume: {diesel_volume}")
        print(f"⛽ ulp_value: {ulp_value}, volume: {ulp_volume}")

        diesel_unit_price = (diesel_value / diesel_volume).quantize(Decimal('0.0000000001')) if diesel_volume else Decimal('0.0000000000')
        ulp_unit_price = (ulp_value / ulp_volume).quantize(Decimal('0.0000000001')) if ulp_volume else Decimal('0.0000000000')
        total_sales = diesel_value + ulp_value

        print(f"💰 Calculated diesel_unit_price={diesel_unit_price}, ulp_unit_price={ulp_unit_price}")
        print(f"📊 Total sales calculated: {total_sales}")

        try:
            with transaction.atomic():
                entry = form.save(commit=False)
                print("✅ Entry pulled from form")

                entry.submitted_at = now
                entry.diesel_unit_price = diesel_unit_price
                entry.ulp_unit_price = ulp_unit_price
                entry.total_sales_calculated = total_sales
                entry.diesel_value_rands = diesel_value
                entry.ulp_value_rands = ulp_value
                entry.save()
                print(f"📥 CongestionEntry saved: ID {entry.id}")

                if self.request.FILES.get('attachment'):
                    shift.attachment = self.request.FILES['attachment']
                    print("📎 Attachment added to shift")

                shift.sales_data_confirmed_by_cashier = True
                shift.final_variance = entry.variance.quantize(Decimal("0.01"))
                shift.save()
                print(f"📌 Shift updated with final_variance: {shift.final_variance}")

                oil_product = form.cleaned_data.get('oil_product')
                oil_qty = form.cleaned_data.get('oil_quantity_sold') or Decimal('0.00')
                print(f"🛢️ Oil product: {oil_product}, Quantity: {oil_qty}")

                if oil_product and oil_qty > 0:
                    warehouse = CashierOilWarehouse.objects.filter(
                        cashier=shift.cashier,
                        oil_product=oil_product
                    ).first()

                    if not warehouse:
                        print("❌ No matching cashier warehouse entry")
                        messages.error(self.request, f"No warehouse record found for {oil_product.name}.")
                        return self.form_invalid(form)

                    if warehouse.quantity < oil_qty:
                        print(f"🚫 Insufficient stock for {oil_product.name}: available={warehouse.quantity}, needed={oil_qty}")
                        messages.error(self.request, f"Insufficient stock of {oil_product.name}. Available: {warehouse.quantity}")
                        return self.form_invalid(form)

                    warehouse.quantity -= oil_qty
                    warehouse.save()
                    print(f"🪙 Warehouse updated. Remaining for {oil_product.name}: {warehouse.quantity}")

                    OilSale.objects.create(
                        oil_product=oil_product,
                        shift=shift,
                        cashier_responsible=shift.cashier,
                        quantity_sold=oil_qty,
                        price_per_unit_at_sale=oil_product.selling_price,
                        total_sale_value=oil_qty * oil_product.selling_price,
                        sale_datetime=now,
                        logged_by=user
                    )
                    print("🧾 Oil sale record created")

                messages.success(self.request, f"Shift '{shift}' successfully recorded.")
                print("🎉 Shift submission complete. Redirecting...")
                return redirect('reconciliation:shift_detail', pk=shift.pk)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"🔥 Exception during form_valid: {e}")
            messages.error(self.request, f"An error occurred while saving shift data: {e}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There were errors in your submission. Please review the form and try again.")
        return super().form_invalid(form)

    
@login_required
def add_adjustment(request, shift_id):
    if request.method == "POST":
        shift = get_object_or_404(Shift, pk=shift_id)
        FuelAdjustment.objects.create(
            shift=shift,
            amount=request.POST.get("amount"),
            direction=request.POST.get("direction"),
            reason_note=request.POST.get("reason_note"),
            recorded_by=request.user
        )
    return redirect('reconciliation:shift_detail', pk=shift_id)


def all_expenses_report(request):
    expenses = BusinessExpense.objects.select_related('category').order_by('-expense_date')

    category_totals = (
        expenses
        .values('category__name')
        .annotate(total_amount=Sum('amount'))
        .order_by('category__name')
    )

    grand_total = expenses.aggregate(total=Sum('amount'))['total']

    context = {
        'expenses': expenses,
        'category_totals': category_totals,
        'grand_total': grand_total,
    }
    return render(request, 'reconciliation/all_expenses_report.html', context)


def export_expenses_csv(request):
    expenses = BusinessExpense.objects.select_related('category', 'recorded_by')

    # Optional filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    cashier_id = request.GET.get('cashier_id')

    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    if cashier_id:
        expenses = expenses.filter(recorded_by_id=cashier_id)

    # Prepare response with UTF-8 BOM for Excel
    response = HttpResponse(content_type='text/csv')
    filename = f"business_expenses_{now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(u'\ufeff'.encode('utf8'))  # Excel-safe BOM

    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Description', 'Amount', 'Recorded By', 'Receipt'])

    for exp in expenses:
        writer.writerow([
            exp.expense_date.strftime('%Y-%m-%d'),
            exp.category.name,
            exp.description,
            f"{exp.amount:.2f}",
            exp.recorded_by.username if exp.recorded_by else '—',
            request.build_absolute_uri(exp.receipt.url) if exp.receipt else '—'
        ])

    return response

def dashboard_view(request):
    fuel_tanks = FuelTank.objects.all().order_by('fuel_type')
    recent_deliveries = ReceivedStock.objects.select_related('fuel_order', 'fuel_tank').order_by('-delivery_date')[:10]

    # Optionally include other dashboard data as you already are
    context = {
        'fuel_tanks': fuel_tanks,
        'recent_deliveries': recent_deliveries,
        # Include your eod_summary, recon_data, recon_totals, cashiers, etc.
    }

    return render(request, 'dashboard/dashboard.html', context)

def stock_change_report_view(request):
    form = StockChangeReportForm(request.GET or None)
    report_data = None

    if form.is_valid():
        tank = form.cleaned_data['tank']
        dip_open = form.cleaned_data['dip_open']
        dip_close = form.cleaned_data['dip_close']

        report_data = calculate_stock_change_report(tank, dip_open, dip_close)
        report_data.update({
            'dip_open': dip_open,
            'dip_close': dip_close,
            'user': request.user,
            'now': timezone.now()
        })
    else:
        # Manually hydrate queryset even if form is not valid
        tank_id = request.GET.get('tank')
        if tank_id:
            form.fields['dip_open'].queryset = DipRecord.objects.filter(fuel_tank_id=tank_id).order_by('-record_datetime')
            form.fields['dip_close'].queryset = DipRecord.objects.filter(fuel_tank_id=tank_id).order_by('-record_datetime')

    context = {
        'form': form,
        'report': report_data
    }
    return render(request, 'reconciliation/stock_change_report.html', context)

@login_required
@role_required(allowed_roles=['MANAGER', 'SENIOR_MANAGER', 'CEO'])
def expense_report_view(request):
    print("📌 Entered expense_report_view")

    # Retrieve filter parameters from GET query string
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_cashier_id = request.GET.get('cashier_id')

    print(f"📋 Filters received - Start: {start_date}, End: {end_date}, Cashier ID: {selected_cashier_id}")

    # Start with all expenses
    expenses = BusinessExpense.objects.all()

    # Apply date range filter if both dates are provided and valid
    if start_date and end_date:
        try:
            expenses = expenses.filter(expense_date__range=[start_date, end_date])
            print(f"📅 Filtered by date range: {start_date} - {end_date}, Count: {expenses.count()}")
        except Exception as e:
            print(f"⚠️ Error applying date filter: {e}")

    # Filter by cashier if provided
    if selected_cashier_id:
        try:
            expenses = expenses.filter(recorded_by__id=selected_cashier_id)
            print(f"👤 Filtered by cashier ID: {selected_cashier_id}, Count: {expenses.count()}")
        except Exception as e:
            print(f"⚠️ Error applying cashier filter: {e}")

    # Aggregate totals grouped by category
    category_totals = expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    print(f"📊 Category Totals: {list(category_totals)}")

    # Group expenses by category for detailed listing
    grouped_expenses = defaultdict(list)
    # Use select_related for efficient foreign key loading
    for exp in expenses.select_related('category', 'recorded_by'):
        grouped_expenses[exp.category.name].append(exp)
    print(f"📂 Grouped expenses into {len(grouped_expenses)} categories")

    # Prepare chart data
    chart_labels = [entry['category__name'] for entry in category_totals]
    chart_data = [float(entry['total']) for entry in category_totals]

    # Compute grand total of filtered expenses safely
    grand_total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    # Get list of cashiers for filter dropdown or display
    cashiers = User.objects.filter(role='CASHIER')

    # Context data to pass to the template
    context = {
        'page_title': 'Expenses Overview',
        'category_totals': category_totals,
        'grouped_expenses': grouped_expenses,
        'grand_total': grand_total,
        'start_date': start_date,
        'end_date': end_date,
        'selected_cashier_id': selected_cashier_id,
        'cashiers': cashiers,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }

    print("✅ Rendering expense_report.html with context")
    return render(request, 'reconciliation/expense_report.html', context)


def export_daily_sales_csv(request):
    # Placeholder logic for now
    return HttpResponse("CSV export coming soon.", content_type="text/plain")

def export_daily_sales_pdf(request):
    # Placeholder logic – customize this later
    return HttpResponse("PDF export not implemented yet.", content_type="text/plain")

def export_monthly_revenue_csv(request):
    # Placeholder: implement export logic later
    return HttpResponse("Monthly CSV export coming soon.", content_type="text/plain")

def export_monthly_revenue_pdf(request):
    # Placeholder: implement export logic later
    return HttpResponse("Monthly pdf export coming soon.", content_type="text/plain")



def export_variance_report_csv(request):
    return HttpResponse("CSV export not yet implemented for Variance Report.", content_type="text/plain")



def export_variance_report_pdf(request):
    return HttpResponse("pdf export not yet implemented for Variance Report.", content_type="text/plain")



def export_warehouse_report_csv(request):
    return HttpResponse("Warehouse Report CSV export coming soon.", content_type="text/plain")

def export_warehouse_report_pdf(request):
    return HttpResponse("Warehouse Report PDF export coming soon.", content_type="text/plain")



def export_oil_sales_report_csv(request):
    return HttpResponse("Oil Sales Report CSV export coming soon.", content_type="text/plain")

def export_oil_sales_report_pdf(request):
    return HttpResponse("Oil Sales Report PDF export coming soon.", content_type="text/plain")



def export_expenses_report_csv(request):
    return HttpResponse("Expenses Report CSV export coming soon.", content_type="text/plain")

def export_expenses_report_pdf(request):
    return HttpResponse("Expenses Report PDF export coming soon.", content_type="text/plain")



