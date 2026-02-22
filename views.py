import json
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .forms import (
    ExpenseCategoryForm, ExpenseForm, ExpenseSettingsForm,
    RecurringExpenseForm, SupplierForm,
)
from .models import (
    Expense, ExpenseCategory, ExpenseSettings,
    RecurringExpense, Supplier,
)


def _hub_id(request):
    return request.session.get('hub_id')


def _employee(request):
    """Return the current LocalUser from session."""
    from apps.accounts.models import LocalUser
    uid = request.session.get('local_user_id')
    if uid:
        try:
            return LocalUser.objects.get(pk=uid)
        except LocalUser.DoesNotExist:
            pass
    return None


# ============================================================================
# Dashboard
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'dashboard')
@htmx_view('expenses/pages/dashboard.html', 'expenses/partials/dashboard_content.html')
def dashboard(request):
    hub = _hub_id(request)
    today = timezone.now().date()
    month_start = today.replace(day=1)

    base_qs = Expense.objects.filter(hub_id=hub, is_deleted=False)

    # This month totals
    month_expenses = base_qs.filter(expense_date__gte=month_start)
    total_this_month = month_expenses.aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')
    count_this_month = month_expenses.count()

    # Pending approval
    pending_approval = base_qs.filter(status='pending').count()

    # By category (this month)
    by_category = (
        month_expenses
        .filter(category__isnull=False)
        .values('category__name', 'category__color')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('-total')
    )

    # Upcoming recurring
    upcoming_recurring = RecurringExpense.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
        next_due_date__lte=today + timedelta(days=30),
    ).order_by('next_due_date')[:5]

    # Recent expenses
    recent_expenses = base_qs.select_related(
        'category', 'supplier',
    ).order_by('-expense_date', '-created_at')[:5]

    return {
        'total_this_month': total_this_month,
        'count_this_month': count_this_month,
        'pending_approval': pending_approval,
        'by_category': by_category,
        'upcoming_recurring': upcoming_recurring,
        'recent_expenses': recent_expenses,
    }


# ============================================================================
# Expense List
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'expense_list')
@htmx_view('expenses/pages/expense_list.html', 'expenses/partials/expense_list_content.html')
def expense_list(request):
    hub = _hub_id(request)

    queryset = Expense.objects.filter(
        hub_id=hub, is_deleted=False,
    ).select_related('category', 'supplier')

    # Filters
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(expense_number__icontains=search)
            | Q(title__icontains=search)
            | Q(supplier__name__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    category_filter = request.GET.get('category', '')
    if category_filter:
        queryset = queryset.filter(category_id=category_filter)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        queryset = queryset.filter(expense_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(expense_date__lte=date_to)

    queryset = queryset.order_by('-expense_date', '-created_at')

    # Pagination
    from django.core.paginator import Paginator
    per_page = int(request.GET.get('per_page', 25))
    paginator = Paginator(queryset, per_page)
    page_num = int(request.GET.get('page', 1))
    page_obj = paginator.get_page(page_num)

    categories = ExpenseCategory.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')

    # HTMX table-only update
    if request.headers.get('HX-Target') == 'expenses-table-container':
        return render(request, 'expenses/partials/expense_table_body.html', {
            'expenses': page_obj.object_list,
            'page_obj': page_obj,
            'search': search,
            'status_filter': status_filter,
            'category_filter': category_filter,
            'date_from': date_from,
            'date_to': date_to,
        })

    return {
        'expenses': page_obj.object_list,
        'page_obj': page_obj,
        'categories': categories,
        'search': search,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'date_from': date_from,
        'date_to': date_to,
    }


# ============================================================================
# Expense Detail
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'expense_list')
@htmx_view('expenses/pages/expense_detail.html', 'expenses/partials/expense_detail_content.html')
def expense_detail(request, pk):
    hub = _hub_id(request)
    expense = get_object_or_404(
        Expense.objects.select_related('category', 'supplier', 'approved_by'),
        id=pk, hub_id=hub, is_deleted=False,
    )
    return {'expense': expense}


# ============================================================================
# Expense Create / Edit
# ============================================================================

@require_http_methods(["GET", "POST"])
@login_required
@with_module_nav('expenses', 'expense_list')
@htmx_view('expenses/pages/expense_form.html', 'expenses/partials/expense_form_content.html')
def expense_create(request):
    hub = _hub_id(request)
    settings = ExpenseSettings.get_settings(hub)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.hub_id = hub
            if not expense.tax_rate:
                expense.tax_rate = settings.default_tax_rate
            expense.save()
            # Redirect via HTMX
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = f'/m/expenses/{expense.pk}/'
            return response
    else:
        form = ExpenseForm(initial={
            'expense_date': timezone.now().date(),
            'tax_rate': settings.default_tax_rate,
            'status': 'draft',
        })
        form.fields['category'].queryset = ExpenseCategory.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        )
        form.fields['supplier'].queryset = Supplier.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        )

    return {
        'form': form,
        'is_edit': False,
    }


@require_http_methods(["GET", "POST"])
@login_required
@with_module_nav('expenses', 'expense_list')
@htmx_view('expenses/pages/expense_form.html', 'expenses/partials/expense_form_content.html')
def expense_edit(request, pk):
    hub = _hub_id(request)
    expense = get_object_or_404(
        Expense, id=pk, hub_id=hub, is_deleted=False,
    )

    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = f'/m/expenses/{expense.pk}/'
            return response
    else:
        form = ExpenseForm(instance=expense)
        form.fields['category'].queryset = ExpenseCategory.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        )
        form.fields['supplier'].queryset = Supplier.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        )

    return {
        'form': form,
        'expense': expense,
        'is_edit': True,
    }


# ============================================================================
# Expense Actions
# ============================================================================

@require_http_methods(["POST"])
@login_required
def expense_delete(request, pk):
    hub = _hub_id(request)
    expense = get_object_or_404(Expense, id=pk, hub_id=hub, is_deleted=False)
    try:
        expense.delete()  # Soft delete
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def expense_approve(request, pk):
    hub = _hub_id(request)
    employee = _employee(request)

    try:
        expense = get_object_or_404(Expense, id=pk, hub_id=hub, is_deleted=False)

        if expense.status not in ('draft', 'pending'):
            return JsonResponse({
                'success': False,
                'error': str(_('Only draft or pending expenses can be approved.')),
            })

        expense.status = 'approved'
        expense.approved_by = employee
        expense.approved_at = timezone.now()
        expense.save(update_fields=[
            'status', 'approved_by', 'approved_at', 'updated_at',
        ])

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def expense_mark_paid(request, pk):
    hub = _hub_id(request)

    try:
        expense = get_object_or_404(Expense, id=pk, hub_id=hub, is_deleted=False)

        settings = ExpenseSettings.get_settings(hub)
        if settings.require_approval and expense.status not in ('approved',):
            # If approval required, must be approved first
            if expense.total_amount > settings.approval_threshold or settings.approval_threshold == Decimal('0.00'):
                return JsonResponse({
                    'success': False,
                    'error': str(_('This expense requires approval before it can be marked as paid.')),
                })

        expense.status = 'paid'
        expense.paid_at = timezone.now()
        expense.save(update_fields=['status', 'paid_at', 'updated_at'])

        # Update supplier totals
        if expense.supplier:
            expense.supplier.update_totals()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# Suppliers
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'suppliers')
@htmx_view('expenses/pages/suppliers.html', 'expenses/partials/suppliers_content.html')
def suppliers(request):
    hub = _hub_id(request)

    queryset = Supplier.objects.filter(hub_id=hub, is_deleted=False)

    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(contact_name__icontains=search)
            | Q(email__icontains=search)
            | Q(tax_id__icontains=search)
        )

    show_inactive = request.GET.get('show_inactive', '') == 'true'
    if not show_inactive:
        queryset = queryset.filter(is_active=True)

    queryset = queryset.order_by('name')

    return {
        'suppliers': queryset,
        'search': search,
        'show_inactive': show_inactive,
    }


@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'suppliers')
@htmx_view('expenses/pages/supplier_detail.html', 'expenses/partials/supplier_detail_content.html')
def supplier_detail(request, pk):
    hub = _hub_id(request)
    supplier = get_object_or_404(
        Supplier, id=pk, hub_id=hub, is_deleted=False,
    )
    recent_expenses = Expense.objects.filter(
        hub_id=hub, is_deleted=False, supplier=supplier,
    ).order_by('-expense_date')[:10]

    return {
        'supplier': supplier,
        'recent_expenses': recent_expenses,
    }


@require_http_methods(["GET", "POST"])
@login_required
@with_module_nav('expenses', 'suppliers')
@htmx_view('expenses/pages/supplier_form.html', 'expenses/partials/supplier_form_content.html')
def supplier_create(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.hub_id = hub
            supplier.save()
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = f'/m/expenses/suppliers/{supplier.pk}/'
            return response
    else:
        form = SupplierForm()

    return {
        'form': form,
        'is_edit': False,
    }


@require_http_methods(["GET", "POST"])
@login_required
@with_module_nav('expenses', 'suppliers')
@htmx_view('expenses/pages/supplier_form.html', 'expenses/partials/supplier_form_content.html')
def supplier_edit(request, pk):
    hub = _hub_id(request)
    supplier = get_object_or_404(
        Supplier, id=pk, hub_id=hub, is_deleted=False,
    )

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = f'/m/expenses/suppliers/{supplier.pk}/'
            return response
    else:
        form = SupplierForm(instance=supplier)

    return {
        'form': form,
        'supplier': supplier,
        'is_edit': True,
    }


@require_http_methods(["POST"])
@login_required
def supplier_delete(request, pk):
    hub = _hub_id(request)
    try:
        supplier = get_object_or_404(Supplier, id=pk, hub_id=hub, is_deleted=False)
        supplier.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# Categories
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'categories')
@htmx_view('expenses/pages/categories.html', 'expenses/partials/categories_content.html')
def categories(request):
    hub = _hub_id(request)

    cats = ExpenseCategory.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('sort_order', 'name')

    # Annotate with expense count
    cats = cats.annotate(expense_count=Count(
        'expenses', filter=Q(expenses__is_deleted=False),
    ))

    return {'categories': cats}


@require_http_methods(["GET", "POST"])
@login_required
@with_module_nav('expenses', 'categories')
@htmx_view('expenses/pages/category_form.html', 'expenses/partials/category_form_content.html')
def category_create(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.hub_id = hub
            cat.save()
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = '/m/expenses/categories/'
            return response
    else:
        form = ExpenseCategoryForm()
        form.fields['parent'].queryset = ExpenseCategory.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        )

    return {
        'form': form,
        'is_edit': False,
    }


@require_http_methods(["GET", "POST"])
@login_required
@with_module_nav('expenses', 'categories')
@htmx_view('expenses/pages/category_form.html', 'expenses/partials/category_form_content.html')
def category_edit(request, pk):
    hub = _hub_id(request)
    cat = get_object_or_404(
        ExpenseCategory, id=pk, hub_id=hub, is_deleted=False,
    )

    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = '/m/expenses/categories/'
            return response
    else:
        form = ExpenseCategoryForm(instance=cat)
        form.fields['parent'].queryset = ExpenseCategory.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        ).exclude(pk=pk)

    return {
        'form': form,
        'category': cat,
        'is_edit': True,
    }


@require_http_methods(["POST"])
@login_required
def category_delete(request, pk):
    hub = _hub_id(request)
    try:
        cat = get_object_or_404(ExpenseCategory, id=pk, hub_id=hub, is_deleted=False)
        cat.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# Reports
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'reports')
@htmx_view('expenses/pages/reports.html', 'expenses/partials/reports_content.html')
def reports(request):
    hub = _hub_id(request)
    today = timezone.now().date()

    period = request.GET.get('period', 'month')
    period_map = {
        'week': today - timedelta(days=7),
        'month': today - timedelta(days=30),
        'quarter': today - timedelta(days=90),
        'year': today - timedelta(days=365),
    }
    start_date = period_map.get(period, period_map['month'])

    base_qs = Expense.objects.filter(
        hub_id=hub, is_deleted=False,
        expense_date__gte=start_date,
    )

    total_expenses = base_qs.aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')
    total_count = base_qs.count()
    total_tax = base_qs.aggregate(s=Sum('tax_amount'))['s'] or Decimal('0.00')

    # By status
    by_status = (
        base_qs
        .values('status')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('status')
    )

    # By category
    by_category = (
        base_qs
        .filter(category__isnull=False)
        .values('category__name', 'category__color')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('-total')
    )

    # By supplier (top 10)
    by_supplier = (
        base_qs
        .filter(supplier__isnull=False)
        .values('supplier__name')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('-total')[:10]
    )

    # Monthly trend
    monthly_trend = (
        base_qs
        .annotate(month=TruncMonth('expense_date'))
        .values('month')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('month')
    )

    return {
        'period': period,
        'start_date': start_date,
        'total_expenses': total_expenses,
        'total_count': total_count,
        'total_tax': total_tax,
        'by_status': by_status,
        'by_category': by_category,
        'by_supplier': by_supplier,
        'monthly_trend': monthly_trend,
    }


# ============================================================================
# Settings
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('expenses', 'settings')
@htmx_view('expenses/pages/settings.html', 'expenses/partials/settings_content.html')
def settings_view(request):
    hub = _hub_id(request)
    settings = ExpenseSettings.get_settings(hub)
    form = ExpenseSettingsForm(instance=settings)

    return {
        'config': settings,
        'settings_form': form,
    }


@require_http_methods(["POST"])
@login_required
def settings_save(request):
    hub = _hub_id(request)

    try:
        data = json.loads(request.body)
        settings = ExpenseSettings.get_settings(hub)

        settings.require_approval = data.get('require_approval', False)
        settings.approval_threshold = Decimal(str(data.get('approval_threshold', 0)))
        settings.default_tax_rate = Decimal(str(data.get('default_tax_rate', 21)))
        settings.default_currency = data.get('default_currency', 'EUR')
        settings.auto_numbering = data.get('auto_numbering', True)
        settings.number_prefix = data.get('number_prefix', 'EXP')

        settings.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
