# Expenses

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `expenses` |
| **Version** | `1.0.0` |
| **Icon** | `wallet-outline` |
| **Dependencies** | None |

## Models

### `ExpenseSettings`

Per-hub expense configuration.

| Field | Type | Details |
|-------|------|---------|
| `require_approval` | BooleanField |  |
| `approval_threshold` | DecimalField |  |
| `default_tax_rate` | DecimalField |  |
| `default_currency` | CharField | max_length=3 |
| `auto_numbering` | BooleanField |  |
| `number_prefix` | CharField | max_length=10 |

**Methods:**

- `get_settings()`

### `ExpenseCategory`

Expense category for organizing expenses.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=200 |
| `icon` | CharField | max_length=50 |
| `color` | CharField | max_length=7 |
| `description` | TextField | optional |
| `is_active` | BooleanField |  |
| `sort_order` | PositiveIntegerField |  |
| `parent` | ForeignKey | → `expenses.ExpenseCategory`, on_delete=SET_NULL, optional |

### `Supplier`

Supplier/vendor for expenses.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=255 |
| `contact_name` | CharField | max_length=255, optional |
| `email` | EmailField | max_length=254, optional |
| `phone` | CharField | max_length=20, optional |
| `tax_id` | CharField | max_length=20, optional |
| `address` | TextField | optional |
| `city` | CharField | max_length=100, optional |
| `postal_code` | CharField | max_length=10, optional |
| `country` | CharField | max_length=100 |
| `website` | URLField | max_length=200, optional |
| `notes` | TextField | optional |
| `is_active` | BooleanField |  |
| `total_spent` | DecimalField |  |
| `last_purchase_date` | DateField | optional |

**Methods:**

- `update_totals()` — Recalculate total_spent and last_purchase_date from paid expenses.

### `Expense`

Main expense record.

| Field | Type | Details |
|-------|------|---------|
| `expense_number` | CharField | max_length=50 |
| `title` | CharField | max_length=255 |
| `description` | TextField | optional |
| `category` | ForeignKey | → `expenses.ExpenseCategory`, on_delete=SET_NULL, optional |
| `supplier` | ForeignKey | → `expenses.Supplier`, on_delete=SET_NULL, optional |
| `amount` | DecimalField |  |
| `tax_rate` | DecimalField |  |
| `tax_amount` | DecimalField |  |
| `total_amount` | DecimalField |  |
| `expense_date` | DateField |  |
| `due_date` | DateField | optional |
| `status` | CharField | max_length=20, choices: draft, pending, approved, paid, rejected |
| `payment_method` | CharField | max_length=50, optional |
| `reference_number` | CharField | max_length=100, optional |
| `receipt_image` | ImageField | max_length=100, optional |
| `notes` | TextField | optional |
| `approved_by` | ForeignKey | → `accounts.LocalUser`, on_delete=SET_NULL, optional |
| `approved_at` | DateTimeField | optional |
| `paid_at` | DateTimeField | optional |

**Methods:**

- `generate_expense_number()` — Generate a unique expense number for the hub.

### `RecurringExpense`

Template for recurring costs (rent, utilities, subscriptions).

| Field | Type | Details |
|-------|------|---------|
| `title` | CharField | max_length=255 |
| `category` | ForeignKey | → `expenses.ExpenseCategory`, on_delete=SET_NULL, optional |
| `supplier` | ForeignKey | → `expenses.Supplier`, on_delete=SET_NULL, optional |
| `amount` | DecimalField |  |
| `tax_rate` | DecimalField |  |
| `frequency` | CharField | max_length=20, choices: weekly, monthly, quarterly, yearly |
| `next_due_date` | DateField |  |
| `is_active` | BooleanField |  |
| `auto_create` | BooleanField |  |
| `last_generated_date` | DateField | optional |

**Methods:**

- `get_next_date_after()` — Calculate the next due date based on frequency.

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `ExpenseCategory` | `parent` | `expenses.ExpenseCategory` | SET_NULL | Yes |
| `Expense` | `category` | `expenses.ExpenseCategory` | SET_NULL | Yes |
| `Expense` | `supplier` | `expenses.Supplier` | SET_NULL | Yes |
| `Expense` | `approved_by` | `accounts.LocalUser` | SET_NULL | Yes |
| `RecurringExpense` | `category` | `expenses.ExpenseCategory` | SET_NULL | Yes |
| `RecurringExpense` | `supplier` | `expenses.Supplier` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/expenses/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `dashboard` | GET |
| `expense_list/` | `expense_list` | GET |
| `list/` | `expense_list` | GET |
| `create/` | `expense_create` | GET/POST |
| `<uuid:pk>/` | `expense_detail` | GET |
| `<uuid:pk>/edit/` | `expense_edit` | GET |
| `<uuid:pk>/delete/` | `expense_delete` | GET/POST |
| `<uuid:pk>/approve/` | `expense_approve` | GET |
| `<uuid:pk>/mark-paid/` | `expense_mark_paid` | GET |
| `suppliers/` | `suppliers` | GET |
| `suppliers/create/` | `supplier_create` | GET/POST |
| `suppliers/<uuid:pk>/` | `supplier_detail` | GET |
| `suppliers/<uuid:pk>/edit/` | `supplier_edit` | GET |
| `suppliers/<uuid:pk>/delete/` | `supplier_delete` | GET/POST |
| `categories/` | `categories` | GET |
| `categories/create/` | `category_create` | GET/POST |
| `categories/<uuid:pk>/edit/` | `category_edit` | GET |
| `categories/<uuid:pk>/delete/` | `category_delete` | GET/POST |
| `reports/` | `reports` | GET |
| `settings/` | `settings` | GET |
| `settings/save/` | `settings_save` | GET/POST |

## Permissions

| Permission | Description |
|------------|-------------|
| `expenses.view_expense` | View Expense |
| `expenses.add_expense` | Add Expense |
| `expenses.change_expense` | Change Expense |
| `expenses.delete_expense` | Delete Expense |
| `expenses.approve_expense` | Approve Expense |
| `expenses.view_supplier` | View Supplier |
| `expenses.add_supplier` | Add Supplier |
| `expenses.change_supplier` | Change Supplier |
| `expenses.delete_supplier` | Delete Supplier |
| `expenses.view_reports` | View Reports |
| `expenses.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_expense`, `add_supplier`, `approve_expense`, `change_expense`, `change_supplier`, `view_expense`, `view_reports`, `view_supplier`
- **employee**: `add_expense`, `view_expense`, `view_supplier`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Dashboard | `speedometer-outline` | `dashboard` | No |
| Expenses | `receipt-outline` | `expense_list` | No |
| Suppliers | `business-outline` | `suppliers` | No |
| Categories | `pricetags-outline` | `categories` | No |
| Reports | `bar-chart-outline` | `reports` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_expenses`

List expenses with optional filters by status, category, or date range.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: draft, pending, approved, paid, rejected |
| `category_id` | string | No | Filter by category ID |
| `date_from` | string | No | Start date (YYYY-MM-DD) |
| `date_to` | string | No | End date (YYYY-MM-DD) |
| `limit` | integer | No | Max results (default 20) |

### `create_expense`

Record a new expense.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Expense title/description |
| `amount` | string | Yes | Amount before tax |
| `category_id` | string | No | Expense category ID |
| `supplier_id` | string | No | Supplier ID |
| `expense_date` | string | No | Date (YYYY-MM-DD). Defaults to today. |
| `notes` | string | No | Additional notes |

### `get_expense_summary`

Get expense totals by category for a date range.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_from` | string | No | Start date (YYYY-MM-DD) |
| `date_to` | string | No | End date (YYYY-MM-DD) |

## File Structure

```
README.md
__init__.py
ai_tools.py
apps.py
forms.py
locale/
  es/
    LC_MESSAGES/
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
templates/
  expenses/
    pages/
      categories.html
      category_form.html
      dashboard.html
      expense_detail.html
      expense_form.html
      expense_list.html
      reports.html
      settings.html
      supplier_detail.html
      supplier_form.html
      suppliers.html
    partials/
      categories_content.html
      category_form_content.html
      dashboard_content.html
      expense_detail_content.html
      expense_form_content.html
      expense_list_content.html
      expense_table_body.html
      reports_content.html
      settings_content.html
      supplier_detail_content.html
      supplier_form_content.html
      suppliers_content.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_views.py
urls.py
views.py
```
