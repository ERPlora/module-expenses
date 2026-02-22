from django.utils.translation import gettext_lazy as _

MODULE_ID = 'expenses'
MODULE_NAME = _('Expenses')
MODULE_VERSION = '1.0.0'
MODULE_ICON = 'wallet-outline'
MODULE_DESCRIPTION = _('Expense tracking, suppliers, and purchase order management')
MODULE_AUTHOR = 'ERPlora'
MODULE_CATEGORY = 'purchasing'

MENU = {
    'label': _('Expenses'),
    'icon': 'wallet-outline',
    'order': 35,
}

NAVIGATION = [
    {'label': _('Dashboard'), 'icon': 'speedometer-outline', 'id': 'dashboard'},
    {'label': _('Expenses'), 'icon': 'receipt-outline', 'id': 'expense_list'},
    {'label': _('Suppliers'), 'icon': 'business-outline', 'id': 'suppliers'},
    {'label': _('Categories'), 'icon': 'pricetags-outline', 'id': 'categories'},
    {'label': _('Reports'), 'icon': 'bar-chart-outline', 'id': 'reports'},
    {'label': _('Settings'), 'icon': 'settings-outline', 'id': 'settings'},
]

DEPENDENCIES = []

PERMISSIONS = [
    'expenses.view_expense',
    'expenses.add_expense',
    'expenses.change_expense',
    'expenses.delete_expense',
    'expenses.approve_expense',
    'expenses.view_supplier',
    'expenses.add_supplier',
    'expenses.change_supplier',
    'expenses.delete_supplier',
    'expenses.view_reports',
    'expenses.manage_settings',
]
