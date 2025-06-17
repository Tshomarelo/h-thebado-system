from django.urls import path
from . import views
from .views import OilProductCreateView, OilProductListView, export_excel, stock_change_report_view
from reconciliation.views import CombinedFuelOilIngestionFormView
from .views import expense_report_view

app_name = 'reconciliation'

urlpatterns = [
    # Main Dashboard Overview
    path('', views.main_dashboard_overview, name='main_dashboard_overview'),

    # Shift URLs
    path('shifts/', views.ShiftListView.as_view(), name='shift_list'),
    path('shifts/new/', views.ShiftCreateView.as_view(), name='shift_create'),
    path('shifts/<int:pk>/', views.ShiftDetailView.as_view(), name='shift_detail'),
    path('shifts/<int:shift_id>/add-adjustment/', views.add_adjustment, name='add_adjustment'),
    
    # Combined Fuel and Oil Ingestion Form
    path('ingestion/combined-fuel-oil/', CombinedFuelOilIngestionFormView.as_view(), name='combined_fuel_oil_ingestion'),

    # Oil Allocation
    path('allocate_oil/', views.allocate_oil_to_cashier, name='allocate_oil_to_cashier'),
    path('allocation/success/', views.allocation_success_view, name='oil_allocation_success'),
    path('allocate/oil/list/', views.allocation_list_view, name='allocate_oil_list'),


    
    #ADD OIL PRODUCT
    path('oil-products/add/', OilProductCreateView.as_view(), name='add_oil_product'),
    path('oil-products/', OilProductListView.as_view(), name='oilproduct_list'),


    # Stocktake URLs
    path('stocktakes/', views.stocktake_list, name='stocktake_list'),
    path('stocktake/new/', views.stocktake_create, name='stocktake_create'),
    path('stocktake/<int:pk>/', views.stocktake_detail, name='stocktake_detail'),

    # Petty Cash URLs
    path('pettycash/allocations/', views.PettyCashAllocationListView.as_view(), name='pettycashallocation_list'),
    path('pettycash/allocations/new/', views.PettyCashAllocationCreateView.as_view(), name='pettycashallocation_create'),
    path('pettycash/expenses/', views.PettyCashExpenseListView.as_view(), name='pettycashexpense_list'),
    path('pettycash/expenses/new/', views.PettyCashExpenseCreateView.as_view(), name='pettycashexpense_create'),

    # Fuel Price Record URLs
    path('prices/', views.PriceRecordListView.as_view(), name='pricerecord_list'),
    path('prices/new/', views.PriceRecordCreateView.as_view(), name='pricerecord_create'),

    # Bank Deposit URLs
    path('congestion-entry/<int:pk>/update/', views.CongestionEntryUpdateView.as_view(), name='congestion_entry_update'),
    path('bankdeposits/', views.BankDepositListView.as_view(), name='bankdeposit_list'),
    path('bankdeposits/new/', views.BankDepositCreateView.as_view(), name='bankdeposit_create'),

    # COD Customer URLs
    path('cod/customers/', views.CODCustomerListView.as_view(), name='codcustomer_list'),
    path('cod/customers/new/', views.CODCustomerCreateView.as_view(), name='codcustomer_create'),
    path('cod/customers/<int:pk>/', views.CODCustomerDetailView.as_view(), name='codcustomer_detail'),

    # COD Vehicle URLs
    path('cod/customers/<int:customer_pk>/vehicles/new/', views.CODVehicleCreateView.as_view(), name='codvehicle_create'),

    # COD Transaction URLs
    path('cod/transactions/new/', views.CODTransactionCreateView.as_view(), name='codtransaction_create'),

    # Fuel Order URLs
    path('fuelorders/', views.FuelOrderListView.as_view(), name='fuelorder_list'),
    path('fuelorders/new/', views.FuelOrderCreateView.as_view(), name='fuelorder_create'),

    # Received Stock URLs
    path('stockdeliveries/', views.ReceivedStockListView.as_view(), name='receivedstock_list'),
    path('stockdeliveries/new/', views.ReceivedStockCreateView.as_view(), name='receivedstock_create'),

    # Dip Record URLs
    path('diprecords/', views.DipRecordListView.as_view(), name='diprecord_list'),
    path('diprecords/new/', views.DipRecordCreateView.as_view(), name='diprecord_create'),

    # Export URLs
    path('export-excel/', export_excel, name='export_excel'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('shifts/export-csv/', views.export_shifts_csv, name='export_shifts_csv'),
    path('reports/expenses/export/csv/', views.export_expenses_csv, name='export_expenses_csv'),
    path('shift/<int:pk>/export-pdf/', views.generate_shift_pdf, name='generate_shift_pdf'),
    path('export-daily-sales-csv/', views.export_daily_sales_csv, name='export_daily_sales_csv'),
    path('export-daily-sales/pdf/', views.export_daily_sales_pdf, name='export_daily_sales_pdf'),
    path('export-monthly-revenue/csv/', views.export_monthly_revenue_csv, name='export_monthly_revenue_csv'),
    path('export-monthly-revenue/pdf/', views.export_monthly_revenue_pdf, name='export_monthly_revenue_pdf'),
    path('export-variance-report/csv/', views.export_variance_report_csv, name='export_variance_report_csv'),
    path('export-variance-report/pdf/', views.export_variance_report_pdf, name='export_variance_report_pdf'),
    path('export-warehouse-report/csv/', views.export_warehouse_report_csv, name='export_warehouse_report_csv'),
    path('export-warehouse-report/pdf/', views.export_warehouse_report_pdf, name='export_warehouse_report_pdf'),
    path('export-oil-sales-report/csv/', views.export_oil_sales_report_csv, name='export_oil_sales_report_csv'),
    path('export-oil-sales-report/pdf/', views.export_oil_sales_report_pdf, name='export_oil_sales_report_pdf'),
    path('export-expenses-report/csv/', views.export_expenses_report_csv, name='export_expenses_report_csv'),
    path('export-expenses-report/pdf/', views.export_expenses_report_pdf, name='export_expenses_report_pdf'),

    # Daily Fuel Sales Summary
    path('daily-fuel-sales-summary/', views.daily_fuel_sales_summary, name='daily_fuel_sales_summary'),
    

    # Business Expense URLs
    path('expenses/categories/', views.ExpenseCategoryListView.as_view(), name='expensecategory_list'),
    path('expenses/categories/new/', views.ExpenseCategoryCreateView.as_view(), name='expensecategory_create'),
    path('expenses/', views.BusinessExpenseListView.as_view(), name='businessexpense_list'),
    path('expenses/new/', views.BusinessExpenseCreateView.as_view(), name='businessexpense_create'),

    # Reports
    path('reports/monthly-fuel-revenue/', views.monthly_fuel_revenue_report, name='monthly_fuel_revenue_report'),
    path('reports/variance/', views.variance_report, name='variance_report'),
    path('reports/cashier-warehouse/', views.cashier_warehouse_report, name='cashier_warehouse_report'),
    path('reports/oil-stock/', views.oil_stock_report, name='oil_stock_report'),
    path('reports/oil-sales/', views.oil_sales_report, name='oil_sales_report'),
    path('reports/expenses/', views.all_expenses_report, name='all_expenses_report'),
    path('stock-change-report/', stock_change_report_view, name='stock_change_report'),
    
    #charts
    path("", views.dashboard_view, name="dashboard"),  # Root of /reconciliation/
    path('expenses/', expense_report_view, name='expense_report'),
]
    
