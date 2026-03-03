# ==================================================
# FILE: Mbayar/core/urls.py
# PATH: D:/Project Pyton/Mbayar/core/urls.py
# FUNGSI: Routing URLs (TAMBAH OWNER DASHBOARD)
# ==================================================

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from core.forms import CustomPasswordResetForm, CustomSetPasswordForm

urlpatterns = [
    # ===== PUBLIC PAGES (TANPA LOGIN) =====
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ===== RESET PASSWORD =====
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             form_class=CustomPasswordResetForm
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             form_class=CustomSetPasswordForm
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # ===== PROTECTED PAGES (BUTUH LOGIN) =====
    path('dashboard/', views.dashboard, name='dashboard'),
    path('owner-dashboard/', views.owner_dashboard, name='owner_dashboard'),  # <-- TAMBAHKAN INI
    path('outlet/pilih/', views.pilih_outlet, name='pilih_outlet'),

    # ===== MANAJEMEN STOK =====
    path('stock/items/', views.stock_item_list, name='stock_item_list'),
    path('stock/items/add/', views.stock_item_add, name='stock_item_add'),
    path('stock/items/<int:pk>/edit/', views.stock_item_edit, name='stock_item_edit'),
    path('stock/items/<int:pk>/delete/', views.stock_item_delete, name='stock_item_delete'),
    path('stock/low/', views.low_stock_list, name='low_stock_list'),

    # ===== PEMBELIAN STOK =====
    path('stock/purchases/', views.purchase_list, name='purchase_list'),
    path('stock/purchases/add/', views.purchase_add, name='purchase_add'),
    path('stock/purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),

    # ===== KATEGORI MENU =====
    path('menu/categories/', views.menu_category_list, name='menu_category_list'),
    path('menu/categories/add/', views.menu_category_add, name='menu_category_add'),
    path('menu/categories/<int:pk>/edit/', views.menu_category_edit, name='menu_category_edit'),

    # ===== MENU =====
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/add/', views.menu_add, name='menu_add'),
    path('menu/<int:pk>/edit/', views.menu_edit, name='menu_edit'),
    path('menu/<int:pk>/delete/', views.menu_delete, name='menu_delete'),
    path('menu/<int:pk>/toggle/', views.menu_toggle_availability, name='menu_toggle'),

    # ===== KASIR =====
    path('cashier/', views.cashier_view, name='cashier'),
    path('cashier/search/', views.search_menu, name='search_menu'),
    path('cashier/create-order/', views.create_order, name='create_order'),
    path('cashier/order/<str:order_no>/', views.order_detail, name='order_detail'),
    path('cashier/print/<str:order_no>/', views.print_receipt, name='print_receipt'),

    # ===== ORDERS =====
    path('orders/', views.order_list, name='order_list'),
    path('orders/today/', views.today_orders, name='today_orders'),

    # ===== LAPORAN =====
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/profit/', views.profit_report, name='profit_report'),
    path('reports/stock/', views.stock_report, name='stock_report'),

    # ===== EXPORT =====
    path('reports/export/sales/excel/', views.export_sales_excel, name='export_sales_excel'),
    path('reports/export/sales/pdf/', views.export_sales_pdf, name='export_sales_pdf'),
    path('reports/export/profit/excel/', views.export_profit_excel, name='export_profit_excel'),
    path('reports/export/profit/pdf/', views.export_profit_pdf, name='export_profit_pdf'),
    path('reports/export/stock/excel/', views.export_stock_excel, name='export_stock_excel'),

    # ===== PROFILE =====
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # ===== DATA MANAGEMENT =====
    path('data-management/', views.admin_data_management, name='admin_data_management'),
    path('download-template/<str:data_type>/', views.download_template, name='download_template'),
    path('import-data/', views.import_data, name='import_data'),
    path('import-export-logs/', views.import_export_logs_api, name='import_export_logs'),
    path('export-multiple/', views.export_multiple, name='export_multiple'),
    path('backup-database/', views.backup_database, name='backup_database'),
    path('backup-list/', views.backup_list, name='backup_list'),
    path('restore-database/<str:backup_file>/', views.restore_database, name='restore_database'),

    # ===== MANAGEMENT USER =====
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/<int:user_id>/edit-role/', views.user_edit_role, name='user_edit_role'),

    # ===== EXPORT & IMPORT ADMIN =====
    path('admin/export-all/', views.export_all_data, name='export_all_data'),
    path('admin/import/', views.import_data_page, name='import_data_page'),
    path('admin/import-from-zip/', views.import_from_zip, name='import_from_zip'),
    path('admin/download-template/<str:template_type>/', views.download_import_template, name='download_import_template'),
    path('admin/clear-database/', views.clear_database, name='clear_database'),

    # ===== LOG AKTIVITAS =====
    path('admin/logs/', views.activity_log_list, name='activity_log_list'),

    # ===== API ENDPOINTS UNTUK MODIFIER =====
    path('api/menu/<int:menu_id>/modifiers/', views.get_menu_modifiers, name='api_menu_modifiers'),
]