from .forms_base import AuditableForm
from django import forms
from .models import ExpenseCategory, BusinessExpense

class ExpenseCategoryForm(AuditableForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BusinessExpenseForm(AuditableForm):
    class Meta:
        model = BusinessExpense
        fields = ['expense_date', 'category', 'description', 'amount', 'receipt']
        widgets = {
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }