"""
AI context for the Expenses module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Expenses

### Models

**ExpenseSettings** (singleton per hub)
- `require_approval` (bool, default False): whether approval workflow is active
- `approval_threshold` (Decimal): expenses above this amount require approval; 0 = all
- `default_tax_rate` (Decimal, default 21.00)
- `default_currency` (CharField, default `EUR`)
- `auto_numbering` (bool, default True)
- `number_prefix` (CharField, default `EXP`)
- Access via `ExpenseSettings.get_settings(hub_id)`

**ExpenseCategory**
- `name`, `icon`, `color` (hex), `description`
- `is_active`, `sort_order`
- `parent` (FK self, nullable): hierarchical categories

**Supplier**
- `name`, `contact_name`, `email`, `phone`
- `tax_id` (NIF/CIF), `address`, `city`, `postal_code`, `country` (default `España`)
- `website`, `notes`, `is_active`
- `total_spent` (Decimal): auto-updated from paid expenses
- `last_purchase_date` (DateField): auto-updated
- `update_totals()`: recalculates from paid expenses

**Expense**
- `expense_number` (CharField): auto-generated as `PREFIX-YYYYMMDD-NNNN`
- `title`, `description`
- `category` (FK ExpenseCategory, nullable)
- `supplier` (FK Supplier, nullable)
- `amount` (Decimal, net), `tax_rate` (default 21.00), `tax_amount`, `total_amount`
  — tax and total are auto-calculated on save
- `expense_date` (DateField), `due_date` (nullable)
- `status`: `draft` → `pending` → `approved` → `paid` | `rejected`
- `payment_method`, `reference_number` (supplier invoice/receipt number)
- `receipt_image` (ImageField, optional)
- `approved_by` (FK accounts.LocalUser, nullable), `approved_at`, `paid_at`

**RecurringExpense** (template for repeating costs)
- `title`, `category` (FK), `supplier` (FK)
- `amount`, `tax_rate`
- `frequency`: `weekly`, `monthly`, `quarterly`, `yearly`
- `next_due_date` (DateField)
- `is_active`, `auto_create` (bool): auto-generate Expense when due
- `last_generated_date` (DateField, nullable)

### Key flows

**Create and pay an expense:**
1. Create `Expense` — number auto-generated, tax/total auto-calculated
2. If `require_approval=True` and amount > threshold: set `status='pending'`
3. Approver sets `status='approved'`, fills `approved_by` and `approved_at`
4. On payment: set `status='paid'`, fill `paid_at`, `payment_method`
5. Call `supplier.update_totals()` to refresh supplier stats

**Recurring expenses:**
- `RecurringExpense` acts as a template
- When `auto_create=True`, system creates `Expense` on `next_due_date`
- After generation, update `last_generated_date` and advance `next_due_date`

### Relationships
- Expense → ExpenseCategory (FK, nullable)
- Expense → Supplier (FK, nullable, related_name `expenses`)
- Expense → accounts.LocalUser as approved_by (FK, nullable)
- RecurringExpense → ExpenseCategory (FK, nullable)
- RecurringExpense → Supplier (FK, nullable)
"""

SOPS = [
    {
        "id": "new_expense",
        "triggers": {
            "es": ["nuevo gasto", "registrar gasto", "añadir gasto", "crear gasto"],
            "en": ["new expense", "add expense", "create expense", "record expense"],
        },
        "description": {"es": "Registrar un gasto", "en": "Record an expense"},
        "steps": [
            {"tool": "create_expense", "description": "Create expense with amount, category, and description"},
        ],
        "modules_required": ["expenses"],
    },
]
