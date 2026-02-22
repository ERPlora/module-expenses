from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class ExpenseSettings(HubBaseModel):
    """Per-hub expense configuration."""

    require_approval = models.BooleanField(
        _('Require Approval'),
        default=False,
        help_text=_('Require approval for expenses before they can be marked as paid.'),
    )
    approval_threshold = models.DecimalField(
        _('Approval Threshold'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Expenses above this amount require approval. 0 means all expenses.'),
    )
    default_tax_rate = models.DecimalField(
        _('Default Tax Rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('21.00'),
        help_text=_('Default tax rate for new expenses.'),
    )
    default_currency = models.CharField(
        _('Default Currency'),
        max_length=3,
        default='EUR',
        help_text=_('Default currency for expenses.'),
    )
    auto_numbering = models.BooleanField(
        _('Auto Numbering'),
        default=True,
        help_text=_('Automatically generate expense numbers.'),
    )
    number_prefix = models.CharField(
        _('Number Prefix'),
        max_length=10,
        default='EXP',
        help_text=_('Prefix for auto-generated expense numbers.'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'expenses_settings'
        verbose_name = _('Expense Settings')
        verbose_name_plural = _('Expense Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return f"Expense Settings (hub {self.hub_id})"

    @classmethod
    def get_settings(cls, hub_id):
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


# ---------------------------------------------------------------------------
# Expense Category
# ---------------------------------------------------------------------------

class ExpenseCategory(HubBaseModel):
    """Expense category for organizing expenses."""

    name = models.CharField(_('Name'), max_length=200)
    icon = models.CharField(
        _('Icon'),
        max_length=50,
        default='folder-outline',
        help_text=_('Icon name for the category.'),
    )
    color = models.CharField(
        _('Color'),
        max_length=7,
        default='#6366f1',
        help_text=_('Hex color code for the category.'),
    )
    description = models.TextField(_('Description'), blank=True, default='')
    is_active = models.BooleanField(_('Active'), default=True)
    sort_order = models.PositiveIntegerField(_('Sort Order'), default=0)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Parent Category'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'expenses_category'
        verbose_name = _('Expense Category')
        verbose_name_plural = _('Expense Categories')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

class Supplier(HubBaseModel):
    """Supplier/vendor for expenses."""

    name = models.CharField(_('Name'), max_length=255)
    contact_name = models.CharField(
        _('Contact Name'), max_length=255, blank=True, default='',
    )
    email = models.EmailField(_('Email'), blank=True, default='')
    phone = models.CharField(_('Phone'), max_length=20, blank=True, default='')
    tax_id = models.CharField(
        _('Tax ID'), max_length=20, blank=True, default='',
        help_text=_('NIF/CIF of the supplier.'),
    )
    address = models.TextField(_('Address'), blank=True, default='')
    city = models.CharField(_('City'), max_length=100, blank=True, default='')
    postal_code = models.CharField(
        _('Postal Code'), max_length=10, blank=True, default='',
    )
    country = models.CharField(
        _('Country'), max_length=100, default='España',
    )
    website = models.URLField(_('Website'), blank=True, default='')
    notes = models.TextField(_('Notes'), blank=True, default='')
    is_active = models.BooleanField(_('Active'), default=True)
    total_spent = models.DecimalField(
        _('Total Spent'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Total amount spent with this supplier.'),
    )
    last_purchase_date = models.DateField(
        _('Last Purchase Date'), null=True, blank=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'expenses_supplier'
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['name']

    def __str__(self):
        return self.name

    def update_totals(self):
        """Recalculate total_spent and last_purchase_date from paid expenses."""
        from django.db.models import Sum, Max
        agg = self.expenses.filter(
            is_deleted=False, status='paid',
        ).aggregate(
            total=Sum('total_amount'),
            last_date=Max('expense_date'),
        )
        self.total_spent = agg['total'] or Decimal('0.00')
        self.last_purchase_date = agg['last_date']
        self.save(update_fields=['total_spent', 'last_purchase_date', 'updated_at'])


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

class Expense(HubBaseModel):
    """Main expense record."""

    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('paid', _('Paid')),
        ('rejected', _('Rejected')),
    ]

    expense_number = models.CharField(
        _('Expense Number'),
        max_length=50,
        db_index=True,
    )
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True, default='')
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name=_('Category'),
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name=_('Supplier'),
    )

    # Amounts
    amount = models.DecimalField(
        _('Amount (Net)'),
        max_digits=10,
        decimal_places=2,
    )
    tax_rate = models.DecimalField(
        _('Tax Rate %'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('21.00'),
    )
    tax_amount = models.DecimalField(
        _('Tax Amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_amount = models.DecimalField(
        _('Total Amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    # Dates
    expense_date = models.DateField(_('Expense Date'))
    due_date = models.DateField(_('Due Date'), null=True, blank=True)

    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
    )

    # Payment
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=50,
        blank=True,
        default='',
    )
    reference_number = models.CharField(
        _('Reference Number'),
        max_length=100,
        blank=True,
        default='',
        help_text=_('Invoice/receipt number from supplier.'),
    )

    # Receipt
    receipt_image = models.ImageField(
        _('Receipt Image'),
        upload_to='expenses/receipts/',
        null=True,
        blank=True,
    )

    # Notes
    notes = models.TextField(_('Notes'), blank=True, default='')

    # Approval
    approved_by = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses',
        verbose_name=_('Approved By'),
    )
    approved_at = models.DateTimeField(_('Approved At'), null=True, blank=True)
    paid_at = models.DateTimeField(_('Paid At'), null=True, blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'expenses_expense'
        verbose_name = _('Expense')
        verbose_name_plural = _('Expenses')
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['hub_id', 'status', '-expense_date']),
            models.Index(fields=['hub_id', 'category', '-expense_date']),
            models.Index(fields=['hub_id', 'supplier']),
        ]

    def __str__(self):
        return f"{self.expense_number} - {self.title}"

    @classmethod
    def generate_expense_number(cls, hub_id, prefix='EXP'):
        """Generate a unique expense number for the hub."""
        today = timezone.now()
        date_part = today.strftime('%Y%m%d')
        full_prefix = f"{prefix}-{date_part}"

        last_expense = cls.all_objects.filter(
            hub_id=hub_id,
            expense_number__startswith=full_prefix,
        ).order_by('-expense_number').first()

        if last_expense:
            try:
                last_num = int(last_expense.expense_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{full_prefix}-{new_num:04d}"

    def save(self, *args, **kwargs):
        # Auto-calculate tax and total
        if self.amount:
            self.tax_amount = (self.amount * self.tax_rate / Decimal('100')).quantize(
                Decimal('0.01')
            )
            self.total_amount = (self.amount + self.tax_amount).quantize(
                Decimal('0.01')
            )

        # Auto-generate expense number
        if not self.expense_number:
            prefix = 'EXP'
            try:
                settings = ExpenseSettings.get_settings(self.hub_id)
                if settings.auto_numbering:
                    prefix = settings.number_prefix or 'EXP'
            except Exception:
                pass
            self.expense_number = self.generate_expense_number(
                self.hub_id, prefix=prefix,
            )

        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Recurring Expense
# ---------------------------------------------------------------------------

class RecurringExpense(HubBaseModel):
    """Template for recurring costs (rent, utilities, subscriptions)."""

    FREQUENCY_CHOICES = [
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
    ]

    title = models.CharField(_('Title'), max_length=255)
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_expenses',
        verbose_name=_('Category'),
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_expenses',
        verbose_name=_('Supplier'),
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=10,
        decimal_places=2,
    )
    tax_rate = models.DecimalField(
        _('Tax Rate %'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('21.00'),
    )
    frequency = models.CharField(
        _('Frequency'),
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='monthly',
    )
    next_due_date = models.DateField(_('Next Due Date'))
    is_active = models.BooleanField(_('Active'), default=True)
    auto_create = models.BooleanField(
        _('Auto Create'),
        default=False,
        help_text=_('Automatically create expense when due date arrives.'),
    )
    last_generated_date = models.DateField(
        _('Last Generated Date'), null=True, blank=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'expenses_recurring'
        verbose_name = _('Recurring Expense')
        verbose_name_plural = _('Recurring Expenses')
        ordering = ['next_due_date']

    def __str__(self):
        return f"{self.title} ({self.get_frequency_display()})"

    def get_next_date_after(self, current_date):
        """Calculate the next due date based on frequency."""
        from dateutil.relativedelta import relativedelta

        freq_map = {
            'weekly': relativedelta(weeks=1),
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'yearly': relativedelta(years=1),
        }
        delta = freq_map.get(self.frequency, relativedelta(months=1))
        return current_date + delta
