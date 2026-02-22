"""
Shared fixtures for Expenses module tests.
"""

import os
import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.test import Client


os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


# ---------------------------------------------------------------------------
# Hub & Auth Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_hub_config(db, settings):
    """Ensure HubConfig + StoreConfig exist."""
    from apps.configuration.models import HubConfig, StoreConfig
    config = HubConfig.get_solo()
    config.save()
    store = StoreConfig.get_solo()
    store.business_name = 'Test Business'
    store.is_configured = True
    store.save()


@pytest.fixture
def hub_id(db):
    from apps.configuration.models import HubConfig
    return HubConfig.get_solo().hub_id


@pytest.fixture
def employee(db):
    """Create a local user (employee)."""
    from apps.accounts.models import LocalUser
    return LocalUser.objects.create(
        name='Test Employee',
        email='employee@test.com',
        role='admin',
        is_active=True,
    )


@pytest.fixture
def auth_client(employee):
    """Authenticated Django test client."""
    client = Client()
    session = client.session
    session['local_user_id'] = str(employee.id)
    session['user_name'] = employee.name
    session['user_email'] = employee.email
    session['user_role'] = employee.role
    session['store_config_checked'] = True
    session.save()
    return client


# ---------------------------------------------------------------------------
# Model Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def expense_settings(hub_id):
    """Get expense settings for the test hub."""
    from expenses.models import ExpenseSettings
    return ExpenseSettings.get_settings(hub_id)


@pytest.fixture
def category(hub_id):
    """Create an expense category."""
    from expenses.models import ExpenseCategory
    return ExpenseCategory.objects.create(
        hub_id=hub_id,
        name='Office Supplies',
        icon='folder-outline',
        color='#6366f1',
        is_active=True,
        sort_order=1,
    )


@pytest.fixture
def category_2(hub_id):
    """Create a second expense category."""
    from expenses.models import ExpenseCategory
    return ExpenseCategory.objects.create(
        hub_id=hub_id,
        name='Utilities',
        icon='flash-outline',
        color='#f59e0b',
        is_active=True,
        sort_order=2,
    )


@pytest.fixture
def supplier(hub_id):
    """Create a supplier."""
    from expenses.models import Supplier
    return Supplier.objects.create(
        hub_id=hub_id,
        name='ACME Corp',
        contact_name='John Doe',
        email='john@acme.com',
        phone='+34 600 123 456',
        tax_id='B12345678',
        address='Calle Principal 1',
        city='Madrid',
        postal_code='28001',
        country='España',
        is_active=True,
    )


@pytest.fixture
def supplier_2(hub_id):
    """Create a second supplier."""
    from expenses.models import Supplier
    return Supplier.objects.create(
        hub_id=hub_id,
        name='Telefonica',
        email='billing@telefonica.com',
        tax_id='A87654321',
        is_active=True,
    )


@pytest.fixture
def expense(hub_id, category, supplier):
    """Create an expense."""
    from expenses.models import Expense
    return Expense.objects.create(
        hub_id=hub_id,
        title='Office Paper',
        description='Monthly paper supply',
        category=category,
        supplier=supplier,
        amount=Decimal('100.00'),
        tax_rate=Decimal('21.00'),
        expense_date=date.today(),
        status='draft',
    )


@pytest.fixture
def paid_expense(hub_id, category, supplier):
    """Create a paid expense."""
    from expenses.models import Expense
    from django.utils import timezone
    return Expense.objects.create(
        hub_id=hub_id,
        title='Printer Ink',
        category=category,
        supplier=supplier,
        amount=Decimal('50.00'),
        tax_rate=Decimal('21.00'),
        expense_date=date.today(),
        status='paid',
        paid_at=timezone.now(),
    )


@pytest.fixture
def recurring_expense(hub_id, category, supplier):
    """Create a recurring expense."""
    from expenses.models import RecurringExpense
    return RecurringExpense.objects.create(
        hub_id=hub_id,
        title='Office Rent',
        category=category,
        supplier=supplier,
        amount=Decimal('1500.00'),
        tax_rate=Decimal('21.00'),
        frequency='monthly',
        next_due_date=date.today() + timedelta(days=10),
        is_active=True,
        auto_create=False,
    )
