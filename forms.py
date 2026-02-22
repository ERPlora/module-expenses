from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Expense, ExpenseCategory, ExpenseSettings,
    RecurringExpense, Supplier,
)


class ExpenseForm(forms.ModelForm):
    """Form for creating and editing expenses."""

    class Meta:
        model = Expense
        fields = [
            'title', 'description', 'category', 'supplier',
            'amount', 'tax_rate', 'expense_date', 'due_date',
            'status', 'payment_method', 'reference_number',
            'receipt_image', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Expense title'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': '3',
                'placeholder': _('Description (optional)'),
            }),
            'category': forms.Select(attrs={
                'class': 'select',
            }),
            'supplier': forms.Select(attrs={
                'class': 'select',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'expense_date': forms.DateInput(attrs={
                'class': 'input',
                'type': 'date',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'input',
                'type': 'date',
            }),
            'status': forms.Select(attrs={
                'class': 'select',
            }),
            'payment_method': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('e.g. Bank transfer, Cash, Card'),
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Supplier invoice number'),
            }),
            'receipt_image': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': 'image/*',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': '2',
                'placeholder': _('Additional notes'),
            }),
        }


class SupplierForm(forms.ModelForm):
    """Form for creating and editing suppliers."""

    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_name', 'email', 'phone', 'tax_id',
            'address', 'city', 'postal_code', 'country',
            'website', 'notes', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Supplier name'),
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Contact person'),
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': _('email@example.com'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('+34 600 000 000'),
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('NIF/CIF'),
            }),
            'address': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': '2',
                'placeholder': _('Street address'),
            }),
            'city': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('City'),
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Postal code'),
            }),
            'country': forms.TextInput(attrs={
                'class': 'input',
            }),
            'website': forms.URLInput(attrs={
                'class': 'input',
                'placeholder': _('https://example.com'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': '3',
                'placeholder': _('Notes about this supplier'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }


class ExpenseCategoryForm(forms.ModelForm):
    """Form for creating and editing expense categories."""

    class Meta:
        model = ExpenseCategory
        fields = ['name', 'icon', 'color', 'description', 'is_active', 'sort_order', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Category name'),
            }),
            'icon': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('e.g. folder-outline'),
            }),
            'color': forms.TextInput(attrs={
                'class': 'input',
                'type': 'color',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': '2',
                'placeholder': _('Category description'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
            }),
            'parent': forms.Select(attrs={
                'class': 'select',
            }),
        }


class ExpenseSettingsForm(forms.ModelForm):
    """Form for expense module settings."""

    class Meta:
        model = ExpenseSettings
        fields = [
            'require_approval', 'approval_threshold', 'default_tax_rate',
            'default_currency', 'auto_numbering', 'number_prefix',
        ]
        widgets = {
            'require_approval': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'approval_threshold': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
            }),
            'default_tax_rate': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'default_currency': forms.TextInput(attrs={
                'class': 'input',
                'maxlength': '3',
                'placeholder': 'EUR',
            }),
            'auto_numbering': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'number_prefix': forms.TextInput(attrs={
                'class': 'input',
                'maxlength': '10',
                'placeholder': 'EXP',
            }),
        }


class RecurringExpenseForm(forms.ModelForm):
    """Form for creating and editing recurring expenses."""

    class Meta:
        model = RecurringExpense
        fields = [
            'title', 'category', 'supplier', 'amount', 'tax_rate',
            'frequency', 'next_due_date', 'is_active', 'auto_create',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Recurring expense title'),
            }),
            'category': forms.Select(attrs={
                'class': 'select',
            }),
            'supplier': forms.Select(attrs={
                'class': 'select',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'frequency': forms.Select(attrs={
                'class': 'select',
            }),
            'next_due_date': forms.DateInput(attrs={
                'class': 'input',
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'auto_create': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }
