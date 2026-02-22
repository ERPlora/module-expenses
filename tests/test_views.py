"""
Integration tests for Expenses views.
"""

import json
import uuid
import pytest
from datetime import date
from decimal import Decimal
from django.test import Client


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_requires_login(self):
        client = Client()
        response = client.get('/m/expenses/')
        assert response.status_code == 302

    def test_dashboard_loads(self, auth_client):
        response = auth_client.get('/m/expenses/')
        assert response.status_code == 200

    def test_htmx_returns_partial(self, auth_client):
        response = auth_client.get('/m/expenses/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_dashboard_with_expenses(self, auth_client, expense):
        response = auth_client.get('/m/expenses/')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Expense List
# ---------------------------------------------------------------------------

class TestExpenseList:

    def test_list_loads(self, auth_client):
        response = auth_client.get('/m/expenses/list/')
        assert response.status_code == 200

    def test_list_with_expenses(self, auth_client, expense):
        response = auth_client.get('/m/expenses/list/')
        assert response.status_code == 200

    def test_search(self, auth_client, expense):
        response = auth_client.get('/m/expenses/list/?search=Office')
        assert response.status_code == 200

    def test_filter_by_status(self, auth_client, expense):
        response = auth_client.get('/m/expenses/list/?status=draft')
        assert response.status_code == 200

    def test_filter_by_category(self, auth_client, expense, category):
        response = auth_client.get(f'/m/expenses/list/?category={category.pk}')
        assert response.status_code == 200

    def test_htmx_returns_partial(self, auth_client):
        response = auth_client.get('/m/expenses/list/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Expense Detail
# ---------------------------------------------------------------------------

class TestExpenseDetail:

    def test_detail_loads(self, auth_client, expense):
        response = auth_client.get(f'/m/expenses/{expense.pk}/')
        assert response.status_code == 200

    def test_detail_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.get(f'/m/expenses/{fake_uuid}/')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Expense Create
# ---------------------------------------------------------------------------

class TestExpenseCreate:

    def test_create_form_loads(self, auth_client):
        response = auth_client.get('/m/expenses/create/')
        assert response.status_code == 200

    def test_create_expense(self, auth_client, category, supplier):
        from expenses.models import Expense
        response = auth_client.post(
            '/m/expenses/create/',
            data={
                'title': 'New Expense',
                'amount': '150.00',
                'tax_rate': '21.00',
                'expense_date': date.today().isoformat(),
                'status': 'draft',
                'category': str(category.pk),
                'supplier': str(supplier.pk),
            },
            HTTP_HX_REQUEST='true',
        )
        # Should redirect via HX-Redirect
        assert response.status_code == 200
        assert Expense.objects.filter(title='New Expense').exists()

        expense = Expense.objects.get(title='New Expense')
        assert expense.tax_amount == Decimal('31.50')
        assert expense.total_amount == Decimal('181.50')


# ---------------------------------------------------------------------------
# Expense Edit
# ---------------------------------------------------------------------------

class TestExpenseEdit:

    def test_edit_form_loads(self, auth_client, expense):
        response = auth_client.get(f'/m/expenses/{expense.pk}/edit/')
        assert response.status_code == 200

    def test_edit_expense(self, auth_client, expense):
        response = auth_client.post(
            f'/m/expenses/{expense.pk}/edit/',
            data={
                'title': 'Updated Expense',
                'amount': '200.00',
                'tax_rate': '21.00',
                'expense_date': date.today().isoformat(),
                'status': 'draft',
            },
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        expense.refresh_from_db()
        assert expense.title == 'Updated Expense'
        assert expense.amount == Decimal('200.00')


# ---------------------------------------------------------------------------
# Expense Delete
# ---------------------------------------------------------------------------

class TestExpenseDelete:

    def test_delete(self, auth_client, expense):
        response = auth_client.post(f'/m/expenses/{expense.pk}/delete/')
        data = response.json()
        assert data['success'] is True
        expense.refresh_from_db()
        assert expense.is_deleted is True

    def test_delete_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.post(f'/m/expenses/{fake_uuid}/delete/')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Expense Approve
# ---------------------------------------------------------------------------

class TestExpenseApprove:

    def test_approve_draft(self, auth_client, expense):
        response = auth_client.post(f'/m/expenses/{expense.pk}/approve/')
        data = response.json()
        assert data['success'] is True
        expense.refresh_from_db()
        assert expense.status == 'approved'
        assert expense.approved_at is not None
        assert expense.approved_by is not None

    def test_approve_pending(self, auth_client, expense):
        expense.status = 'pending'
        expense.save()

        response = auth_client.post(f'/m/expenses/{expense.pk}/approve/')
        data = response.json()
        assert data['success'] is True
        expense.refresh_from_db()
        assert expense.status == 'approved'

    def test_cannot_approve_paid(self, auth_client, paid_expense):
        response = auth_client.post(f'/m/expenses/{paid_expense.pk}/approve/')
        data = response.json()
        assert data['success'] is False


# ---------------------------------------------------------------------------
# Expense Mark Paid
# ---------------------------------------------------------------------------

class TestExpenseMarkPaid:

    def test_mark_paid(self, auth_client, expense):
        response = auth_client.post(f'/m/expenses/{expense.pk}/mark-paid/')
        data = response.json()
        assert data['success'] is True
        expense.refresh_from_db()
        assert expense.status == 'paid'
        assert expense.paid_at is not None

    def test_mark_paid_requires_approval(self, auth_client, expense, expense_settings):
        """When approval is required, draft expenses cannot be marked paid."""
        expense_settings.require_approval = True
        expense_settings.approval_threshold = Decimal('0.00')
        expense_settings.save()

        response = auth_client.post(f'/m/expenses/{expense.pk}/mark-paid/')
        data = response.json()
        assert data['success'] is False

    def test_mark_paid_approved_with_approval_required(self, auth_client, expense, expense_settings):
        """Approved expenses can be marked paid when approval is required."""
        expense_settings.require_approval = True
        expense_settings.approval_threshold = Decimal('0.00')
        expense_settings.save()

        expense.status = 'approved'
        expense.save()

        response = auth_client.post(f'/m/expenses/{expense.pk}/mark-paid/')
        data = response.json()
        assert data['success'] is True

    def test_mark_paid_updates_supplier_totals(self, auth_client, expense, supplier):
        response = auth_client.post(f'/m/expenses/{expense.pk}/mark-paid/')
        data = response.json()
        assert data['success'] is True

        supplier.refresh_from_db()
        assert supplier.total_spent == expense.total_amount


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

class TestSupplierViews:

    def test_suppliers_list(self, auth_client):
        response = auth_client.get('/m/expenses/suppliers/')
        assert response.status_code == 200

    def test_suppliers_list_with_data(self, auth_client, supplier):
        response = auth_client.get('/m/expenses/suppliers/')
        assert response.status_code == 200

    def test_suppliers_search(self, auth_client, supplier):
        response = auth_client.get('/m/expenses/suppliers/?search=ACME')
        assert response.status_code == 200

    def test_supplier_detail(self, auth_client, supplier):
        response = auth_client.get(f'/m/expenses/suppliers/{supplier.pk}/')
        assert response.status_code == 200

    def test_supplier_detail_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.get(f'/m/expenses/suppliers/{fake_uuid}/')
        assert response.status_code == 404

    def test_supplier_create_form(self, auth_client):
        response = auth_client.get('/m/expenses/suppliers/create/')
        assert response.status_code == 200

    def test_supplier_create(self, auth_client):
        from expenses.models import Supplier
        response = auth_client.post(
            '/m/expenses/suppliers/create/',
            data={
                'name': 'New Supplier',
                'contact_name': 'Jane',
                'email': 'jane@supplier.com',
                'country': 'España',
                'is_active': True,
            },
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        assert Supplier.objects.filter(name='New Supplier').exists()

    def test_supplier_edit_form(self, auth_client, supplier):
        response = auth_client.get(f'/m/expenses/suppliers/{supplier.pk}/edit/')
        assert response.status_code == 200

    def test_supplier_edit(self, auth_client, supplier):
        response = auth_client.post(
            f'/m/expenses/suppliers/{supplier.pk}/edit/',
            data={
                'name': 'Updated ACME',
                'country': 'España',
                'is_active': True,
            },
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        supplier.refresh_from_db()
        assert supplier.name == 'Updated ACME'

    def test_supplier_delete(self, auth_client, supplier):
        from expenses.models import Supplier
        response = auth_client.post(f'/m/expenses/suppliers/{supplier.pk}/delete/')
        data = response.json()
        assert data['success'] is True
        assert Supplier.objects.filter(pk=supplier.pk).count() == 0


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class TestCategoryViews:

    def test_categories_list(self, auth_client):
        response = auth_client.get('/m/expenses/categories/')
        assert response.status_code == 200

    def test_categories_list_with_data(self, auth_client, category):
        response = auth_client.get('/m/expenses/categories/')
        assert response.status_code == 200

    def test_category_create_form(self, auth_client):
        response = auth_client.get('/m/expenses/categories/create/')
        assert response.status_code == 200

    def test_category_create(self, auth_client):
        from expenses.models import ExpenseCategory
        response = auth_client.post(
            '/m/expenses/categories/create/',
            data={
                'name': 'Travel',
                'icon': 'airplane-outline',
                'color': '#10b981',
                'sort_order': 5,
                'is_active': True,
            },
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        assert ExpenseCategory.objects.filter(name='Travel').exists()

    def test_category_edit_form(self, auth_client, category):
        response = auth_client.get(f'/m/expenses/categories/{category.pk}/edit/')
        assert response.status_code == 200

    def test_category_edit(self, auth_client, category):
        response = auth_client.post(
            f'/m/expenses/categories/{category.pk}/edit/',
            data={
                'name': 'Updated Category',
                'icon': 'folder-outline',
                'color': '#6366f1',
                'sort_order': 1,
                'is_active': True,
            },
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        category.refresh_from_db()
        assert category.name == 'Updated Category'

    def test_category_delete(self, auth_client, category):
        from expenses.models import ExpenseCategory
        response = auth_client.post(f'/m/expenses/categories/{category.pk}/delete/')
        data = response.json()
        assert data['success'] is True
        assert ExpenseCategory.objects.filter(pk=category.pk).count() == 0


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class TestReports:

    def test_reports_loads(self, auth_client):
        response = auth_client.get('/m/expenses/reports/')
        assert response.status_code == 200

    def test_reports_with_data(self, auth_client, expense, paid_expense):
        response = auth_client.get('/m/expenses/reports/')
        assert response.status_code == 200

    def test_reports_period_filter(self, auth_client):
        for period in ('week', 'month', 'quarter', 'year'):
            response = auth_client.get(f'/m/expenses/reports/?period={period}')
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettingsView:

    def test_settings_loads(self, auth_client):
        response = auth_client.get('/m/expenses/settings/')
        assert response.status_code == 200

    def test_save_settings(self, auth_client, hub_id, expense_settings):
        from expenses.models import ExpenseSettings
        response = auth_client.post(
            '/m/expenses/settings/save/',
            data=json.dumps({
                'require_approval': True,
                'approval_threshold': 500,
                'default_tax_rate': 10,
                'default_currency': 'USD',
                'auto_numbering': True,
                'number_prefix': 'GASTO',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        refreshed = ExpenseSettings.get_settings(hub_id)
        assert refreshed.require_approval is True
        assert refreshed.approval_threshold == Decimal('500')
        assert refreshed.default_tax_rate == Decimal('10')
        assert refreshed.default_currency == 'USD'
        assert refreshed.number_prefix == 'GASTO'

    def test_save_requires_login(self):
        client = Client()
        response = client.post(
            '/m/expenses/settings/save/',
            data=json.dumps({'require_approval': True}),
            content_type='application/json',
        )
        assert response.status_code == 302
