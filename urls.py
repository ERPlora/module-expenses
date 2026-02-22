from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Expenses CRUD
    path('list/', views.expense_list, name='expense_list'),
    path('create/', views.expense_create, name='expense_create'),
    path('<uuid:pk>/', views.expense_detail, name='expense_detail'),
    path('<uuid:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('<uuid:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('<uuid:pk>/approve/', views.expense_approve, name='expense_approve'),
    path('<uuid:pk>/mark-paid/', views.expense_mark_paid, name='expense_mark_paid'),

    # Suppliers
    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<uuid:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<uuid:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<uuid:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Categories
    path('categories/', views.categories, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<uuid:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<uuid:pk>/delete/', views.category_delete, name='category_delete'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
]
