"""
Unit tests for Expenses models.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# ExpenseSettings
# ---------------------------------------------------------------------------

class TestExpenseSettings:
    """Tests for ExpenseSettings model."""

    def test_get_settings_creates_singleton(self, hub_id):
        from expenses.models import ExpenseSettings
        s = ExpenseSettings.get_settings(hub_id)
        assert s is not None
        assert s.hub_id == hub_id

    def test_get_settings_returns_existing(self, hub_id):
        from expenses.models import ExpenseSettings
        s1 = ExpenseSettings.get_settings(hub_id)
        s2 = ExpenseSettings.get_settings(hub_id)
        assert s1.pk == s2.pk

    def test_default_values(self, expense_settings):
        assert expense_settings.require_approval is False
        assert expense_settings.approval_threshold == Decimal('0.00')
        assert expense_settings.default_tax_rate == Decimal('21.00')
        assert expense_settings.default_currency == 'EUR'
        assert expense_settings.auto_numbering is True
        assert expense_settings.number_prefix == 'EXP'

    def test_str(self, expense_settings):
        assert 'Expense Settings' in str(expense_settings)

    def test_update_settings(self, expense_settings):
        from expenses.models import ExpenseSettings
        expense_settings.require_approval = True
        expense_settings.approval_threshold = Decimal('500.00')
        expense_settings.number_prefix = 'GASTO'
        expense_settings.save()

        refreshed = ExpenseSettings.get_settings(expense_settings.hub_id)
        assert refreshed.require_approval is True
        assert refreshed.approval_threshold == Decimal('500.00')
        assert refreshed.number_prefix == 'GASTO'


# ---------------------------------------------------------------------------
# ExpenseCategory
# ---------------------------------------------------------------------------

class TestExpenseCategory:
    """Tests for ExpenseCategory model."""

    def test_create(self, category):
        assert category.name == 'Office Supplies'
        assert category.icon == 'folder-outline'
        assert category.color == '#6366f1'
        assert category.is_active is True

    def test_str(self, category):
        assert str(category) == 'Office Supplies'

    def test_ordering(self, hub_id):
        from expenses.models import ExpenseCategory
        c1 = ExpenseCategory.objects.create(
            hub_id=hub_id, name='Z Category', sort_order=2,
        )
        c2 = ExpenseCategory.objects.create(
            hub_id=hub_id, name='A Category', sort_order=1,
        )
        cats = list(ExpenseCategory.objects.filter(hub_id=hub_id))
        assert cats[0].pk == c2.pk
        assert cats[1].pk == c1.pk

    def test_hierarchy(self, hub_id, category):
        from expenses.models import ExpenseCategory
        child = ExpenseCategory.objects.create(
            hub_id=hub_id,
            name='Toner',
            parent=category,
        )
        assert child.parent == category
        assert category.children.count() == 1
        assert category.children.first().name == 'Toner'

    def test_soft_delete(self, category):
        from expenses.models import ExpenseCategory
        category.delete()
        assert category.is_deleted is True
        assert ExpenseCategory.objects.filter(pk=category.pk).count() == 0
        assert ExpenseCategory.all_objects.filter(pk=category.pk).count() == 1

    def test_default_icon_and_color(self, hub_id):
        from expenses.models import ExpenseCategory
        cat = ExpenseCategory.objects.create(
            hub_id=hub_id, name='Test',
        )
        assert cat.icon == 'folder-outline'
        assert cat.color == '#6366f1'


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

class TestSupplier:
    """Tests for Supplier model."""

    def test_create(self, supplier):
        assert supplier.name == 'ACME Corp'
        assert supplier.contact_name == 'John Doe'
        assert supplier.email == 'john@acme.com'
        assert supplier.tax_id == 'B12345678'
        assert supplier.city == 'Madrid'
        assert supplier.country == 'España'
        assert supplier.is_active is True

    def test_str(self, supplier):
        assert str(supplier) == 'ACME Corp'

    def test_ordering(self, hub_id):
        from expenses.models import Supplier
        s1 = Supplier.objects.create(hub_id=hub_id, name='Zebra Inc')
        s2 = Supplier.objects.create(hub_id=hub_id, name='Alpha Ltd')
        suppliers = list(Supplier.objects.filter(hub_id=hub_id))
        assert suppliers[0].pk == s2.pk
        assert suppliers[1].pk == s1.pk

    def test_default_total_spent(self, supplier):
        assert supplier.total_spent == Decimal('0.00')
        assert supplier.last_purchase_date is None

    def test_update_totals(self, hub_id, supplier):
        """Test that update_totals recalculates from paid expenses."""
        from expenses.models import Expense
        Expense.objects.create(
            hub_id=hub_id,
            title='Expense 1',
            supplier=supplier,
            amount=Decimal('100.00'),
            tax_rate=Decimal('21.00'),
            expense_date=date.today(),
            status='paid',
            paid_at=timezone.now(),
        )
        Expense.objects.create(
            hub_id=hub_id,
            title='Expense 2',
            supplier=supplier,
            amount=Decimal('200.00'),
            tax_rate=Decimal('21.00'),
            expense_date=date.today() - timedelta(days=5),
            status='paid',
            paid_at=timezone.now(),
        )
        # Draft expense should not count
        Expense.objects.create(
            hub_id=hub_id,
            title='Draft Expense',
            supplier=supplier,
            amount=Decimal('50.00'),
            tax_rate=Decimal('21.00'),
            expense_date=date.today(),
            status='draft',
        )

        supplier.update_totals()
        supplier.refresh_from_db()

        # total_amount for 100 net + 21 tax = 121, and 200 + 42 = 242
        assert supplier.total_spent == Decimal('363.00')
        assert supplier.last_purchase_date == date.today()

    def test_soft_delete(self, supplier):
        from expenses.models import Supplier
        supplier.delete()
        assert supplier.is_deleted is True
        assert Supplier.objects.filter(pk=supplier.pk).count() == 0
        assert Supplier.all_objects.filter(pk=supplier.pk).count() == 1


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

class TestExpense:
    """Tests for Expense model."""

    def test_auto_expense_number(self, expense):
        today = timezone.now().strftime('%Y%m%d')
        assert expense.expense_number.startswith(f'EXP-{today}')

    def test_sequential_expense_numbers(self, hub_id, category):
        from expenses.models import Expense
        e1 = Expense.objects.create(
            hub_id=hub_id, title='E1', amount=Decimal('10.00'),
            tax_rate=Decimal('21.00'), expense_date=date.today(),
        )
        e2 = Expense.objects.create(
            hub_id=hub_id, title='E2', amount=Decimal('20.00'),
            tax_rate=Decimal('21.00'), expense_date=date.today(),
        )
        num1 = int(e1.expense_number.split('-')[-1])
        num2 = int(e2.expense_number.split('-')[-1])
        assert num2 == num1 + 1

    def test_custom_prefix(self, hub_id, expense_settings):
        from expenses.models import Expense
        expense_settings.number_prefix = 'GASTO'
        expense_settings.save()

        e = Expense.objects.create(
            hub_id=hub_id, title='Test', amount=Decimal('10.00'),
            tax_rate=Decimal('0.00'), expense_date=date.today(),
        )
        assert e.expense_number.startswith('GASTO-')

    def test_tax_calculation(self, expense):
        """Tax amount and total are auto-calculated on save."""
        assert expense.tax_amount == Decimal('21.00')
        assert expense.total_amount == Decimal('121.00')

    def test_zero_tax(self, hub_id):
        from expenses.models import Expense
        e = Expense.objects.create(
            hub_id=hub_id, title='Tax Free',
            amount=Decimal('100.00'), tax_rate=Decimal('0.00'),
            expense_date=date.today(),
        )
        assert e.tax_amount == Decimal('0.00')
        assert e.total_amount == Decimal('100.00')

    def test_reduced_tax(self, hub_id):
        from expenses.models import Expense
        e = Expense.objects.create(
            hub_id=hub_id, title='Reduced',
            amount=Decimal('100.00'), tax_rate=Decimal('10.00'),
            expense_date=date.today(),
        )
        assert e.tax_amount == Decimal('10.00')
        assert e.total_amount == Decimal('110.00')

    def test_default_status(self, expense):
        assert expense.status == 'draft'

    def test_all_statuses(self, hub_id):
        from expenses.models import Expense
        for status, _ in Expense.STATUS_CHOICES:
            e = Expense.objects.create(
                hub_id=hub_id, title=f'Status {status}',
                amount=Decimal('10.00'), tax_rate=Decimal('0.00'),
                expense_date=date.today(), status=status,
            )
            assert e.status == status

    def test_str(self, expense):
        assert expense.expense_number in str(expense)
        assert expense.title in str(expense)

    def test_ordering(self, hub_id):
        from expenses.models import Expense
        e1 = Expense.objects.create(
            hub_id=hub_id, title='Old',
            amount=Decimal('10.00'), tax_rate=Decimal('0.00'),
            expense_date=date.today() - timedelta(days=5),
        )
        e2 = Expense.objects.create(
            hub_id=hub_id, title='New',
            amount=Decimal('20.00'), tax_rate=Decimal('0.00'),
            expense_date=date.today(),
        )
        expenses = list(Expense.objects.filter(hub_id=hub_id))
        assert expenses[0].pk == e2.pk  # Newest first

    def test_indexes(self):
        from expenses.models import Expense
        index_fields = [idx.fields for idx in Expense._meta.indexes]
        assert ['hub_id', 'status', '-expense_date'] in index_fields
        assert ['hub_id', 'category', '-expense_date'] in index_fields
        assert ['hub_id', 'supplier'] in index_fields

    def test_soft_delete(self, expense):
        from expenses.models import Expense
        expense.delete()
        assert expense.is_deleted is True
        assert Expense.objects.filter(pk=expense.pk).count() == 0
        assert Expense.all_objects.filter(pk=expense.pk).count() == 1

    def test_with_supplier_and_category(self, expense, supplier, category):
        assert expense.supplier == supplier
        assert expense.category == category

    def test_approval_fields(self, expense, employee):
        expense.status = 'approved'
        expense.approved_by = employee
        expense.approved_at = timezone.now()
        expense.save()

        expense.refresh_from_db()
        assert expense.status == 'approved'
        assert expense.approved_by == employee
        assert expense.approved_at is not None

    def test_paid_at(self, expense):
        expense.status = 'paid'
        expense.paid_at = timezone.now()
        expense.save()

        expense.refresh_from_db()
        assert expense.status == 'paid'
        assert expense.paid_at is not None


# ---------------------------------------------------------------------------
# RecurringExpense
# ---------------------------------------------------------------------------

class TestRecurringExpense:
    """Tests for RecurringExpense model."""

    def test_create(self, recurring_expense):
        assert recurring_expense.title == 'Office Rent'
        assert recurring_expense.amount == Decimal('1500.00')
        assert recurring_expense.frequency == 'monthly'
        assert recurring_expense.is_active is True
        assert recurring_expense.auto_create is False

    def test_str(self, recurring_expense):
        result = str(recurring_expense)
        assert 'Office Rent' in result

    def test_all_frequencies(self, hub_id):
        from expenses.models import RecurringExpense
        for freq, _ in RecurringExpense.FREQUENCY_CHOICES:
            r = RecurringExpense.objects.create(
                hub_id=hub_id,
                title=f'Recurring {freq}',
                amount=Decimal('100.00'),
                next_due_date=date.today(),
                frequency=freq,
            )
            assert r.frequency == freq

    def test_ordering(self, hub_id):
        from expenses.models import RecurringExpense
        r1 = RecurringExpense.objects.create(
            hub_id=hub_id, title='Later',
            amount=Decimal('100.00'),
            next_due_date=date.today() + timedelta(days=30),
        )
        r2 = RecurringExpense.objects.create(
            hub_id=hub_id, title='Sooner',
            amount=Decimal('100.00'),
            next_due_date=date.today() + timedelta(days=5),
        )
        items = list(RecurringExpense.objects.filter(hub_id=hub_id))
        assert items[0].pk == r2.pk  # Sooner first

    def test_get_next_date_monthly(self, recurring_expense):
        today = date.today()
        next_date = recurring_expense.get_next_date_after(today)
        assert next_date.month != today.month or next_date.year != today.year

    def test_get_next_date_weekly(self, hub_id):
        from expenses.models import RecurringExpense
        r = RecurringExpense.objects.create(
            hub_id=hub_id, title='Weekly',
            amount=Decimal('50.00'),
            next_due_date=date.today(),
            frequency='weekly',
        )
        today = date.today()
        next_date = r.get_next_date_after(today)
        assert (next_date - today).days == 7

    def test_get_next_date_quarterly(self, hub_id):
        from expenses.models import RecurringExpense
        r = RecurringExpense.objects.create(
            hub_id=hub_id, title='Quarterly',
            amount=Decimal('500.00'),
            next_due_date=date(2026, 1, 1),
            frequency='quarterly',
        )
        next_date = r.get_next_date_after(date(2026, 1, 1))
        assert next_date == date(2026, 4, 1)

    def test_get_next_date_yearly(self, hub_id):
        from expenses.models import RecurringExpense
        r = RecurringExpense.objects.create(
            hub_id=hub_id, title='Yearly',
            amount=Decimal('1200.00'),
            next_due_date=date(2026, 3, 15),
            frequency='yearly',
        )
        next_date = r.get_next_date_after(date(2026, 3, 15))
        assert next_date == date(2027, 3, 15)

    def test_soft_delete(self, recurring_expense):
        from expenses.models import RecurringExpense
        recurring_expense.delete()
        assert recurring_expense.is_deleted is True
        assert RecurringExpense.objects.filter(pk=recurring_expense.pk).count() == 0
        assert RecurringExpense.all_objects.filter(pk=recurring_expense.pk).count() == 1

    def test_last_generated_date(self, recurring_expense):
        assert recurring_expense.last_generated_date is None
        recurring_expense.last_generated_date = date.today()
        recurring_expense.save()
        recurring_expense.refresh_from_db()
        assert recurring_expense.last_generated_date == date.today()
