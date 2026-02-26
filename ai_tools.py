"""AI tools for the Expenses module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListExpenses(AssistantTool):
    name = "list_expenses"
    description = "List expenses with optional filters by status, category, or date range."
    module_id = "expenses"
    required_permission = "expenses.view_expense"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: draft, pending, approved, paid, rejected"},
            "category_id": {"type": "string", "description": "Filter by category ID"},
            "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "End date (YYYY-MM-DD)"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from expenses.models import Expense
        qs = Expense.objects.select_related('category', 'supplier').order_by('-expense_date')
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        if args.get('category_id'):
            qs = qs.filter(category_id=args['category_id'])
        if args.get('date_from'):
            qs = qs.filter(expense_date__gte=args['date_from'])
        if args.get('date_to'):
            qs = qs.filter(expense_date__lte=args['date_to'])
        limit = args.get('limit', 20)
        return {
            "expenses": [
                {
                    "id": str(e.id),
                    "expense_number": e.expense_number,
                    "title": e.title,
                    "category": e.category.name if e.category else None,
                    "supplier": e.supplier.name if e.supplier else None,
                    "total_amount": str(e.total_amount),
                    "status": e.status,
                    "expense_date": str(e.expense_date) if e.expense_date else None,
                }
                for e in qs[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class CreateExpense(AssistantTool):
    name = "create_expense"
    description = "Record a new expense."
    module_id = "expenses"
    required_permission = "expenses.change_expense"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Expense title/description"},
            "amount": {"type": "string", "description": "Amount before tax"},
            "category_id": {"type": "string", "description": "Expense category ID"},
            "supplier_id": {"type": "string", "description": "Supplier ID"},
            "expense_date": {"type": "string", "description": "Date (YYYY-MM-DD). Defaults to today."},
            "notes": {"type": "string", "description": "Additional notes"},
        },
        "required": ["title", "amount"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from datetime import date
        from decimal import Decimal
        from expenses.models import Expense
        e = Expense.objects.create(
            title=args['title'],
            amount=Decimal(args['amount']),
            category_id=args.get('category_id'),
            supplier_id=args.get('supplier_id'),
            expense_date=args.get('expense_date', date.today()),
            notes=args.get('notes', ''),
            status='draft',
        )
        return {"id": str(e.id), "expense_number": e.expense_number, "created": True}


@register_tool
class GetExpenseSummary(AssistantTool):
    name = "get_expense_summary"
    description = "Get expense totals by category for a date range."
    module_id = "expenses"
    required_permission = "expenses.view_expense"
    parameters = {
        "type": "object",
        "properties": {
            "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "End date (YYYY-MM-DD)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from datetime import date, timedelta
        from django.db.models import Sum
        from expenses.models import Expense
        date_from = args.get('date_from', str(date.today().replace(day=1)))
        date_to = args.get('date_to', str(date.today()))
        qs = Expense.objects.filter(
            expense_date__gte=date_from,
            expense_date__lte=date_to,
            status__in=['approved', 'paid'],
        )
        total = qs.aggregate(total=Sum('total_amount'))['total'] or 0
        by_category = qs.values('category__name').annotate(
            total=Sum('total_amount'),
        ).order_by('-total')
        return {
            "date_from": date_from,
            "date_to": date_to,
            "total": str(total),
            "by_category": [
                {"category": item['category__name'] or 'Uncategorized', "total": str(item['total'])}
                for item in by_category
            ],
        }
