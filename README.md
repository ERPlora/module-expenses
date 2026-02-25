# Expenses Module

Expense tracking, suppliers, and purchase order management.

## Features

- Record and track business expenses with automatic numbering
- Manage suppliers/vendors with contact details and spending totals
- Organize expenses by customizable categories with icons and colors
- Hierarchical category support (parent/child categories)
- Approval workflow with configurable threshold amounts
- Tax calculation with configurable default tax rate and currency
- Receipt image attachment for expense documentation
- Recurring expense templates (weekly, monthly, quarterly, yearly) with optional auto-creation
- Expense reports and analytics
- Payment tracking with method and reference number fields

## Installation

This module is installed automatically via the ERPlora Marketplace.

## Configuration

Access settings via: **Menu > Expenses > Settings**

Configurable options include:
- Require approval for expenses (with threshold amount)
- Default tax rate and currency
- Auto-numbering with custom prefix

## Usage

Access via: **Menu > Expenses**

### Views

| View | URL | Description |
|------|-----|-------------|
| Dashboard | `/m/expenses/dashboard/` | Overview of expense activity, totals, and trends |
| Expenses | `/m/expenses/expense_list/` | List, create, and manage individual expenses |
| Suppliers | `/m/expenses/suppliers/` | Manage supplier/vendor records |
| Categories | `/m/expenses/categories/` | Create and organize expense categories |
| Reports | `/m/expenses/reports/` | Expense reports and analytics |
| Settings | `/m/expenses/settings/` | Configure module settings |

## Models

| Model | Description |
|-------|-------------|
| `ExpenseSettings` | Per-hub configuration for approval rules, tax rate, currency, and numbering |
| `ExpenseCategory` | Hierarchical expense categories with icon, color, and sort order |
| `Supplier` | Supplier/vendor records with contact info, tax ID, and spending totals |
| `Expense` | Individual expense records with amounts, tax, status, approval, and receipt |
| `RecurringExpense` | Templates for recurring costs with frequency and auto-creation settings |

## Permissions

| Permission | Description |
|------------|-------------|
| `expenses.view_expense` | View expenses |
| `expenses.add_expense` | Create new expenses |
| `expenses.change_expense` | Edit existing expenses |
| `expenses.delete_expense` | Delete expenses |
| `expenses.approve_expense` | Approve or reject expenses |
| `expenses.view_supplier` | View suppliers |
| `expenses.add_supplier` | Create new suppliers |
| `expenses.change_supplier` | Edit existing suppliers |
| `expenses.delete_supplier` | Delete suppliers |
| `expenses.view_reports` | Access expense reports |
| `expenses.manage_settings` | Manage module settings |

## License

MIT

## Author

ERPlora Team - support@erplora.com
