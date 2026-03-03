# ==================================================
# FILE: core/views/__init__.py
# PATH: D:/Project Pyton/Mbayar/core/views/__init__.py
# DESKRIPSI: Central export semua views untuk Mbayar POS
# VERSION: 1.0.0
# UPDATE TERAKHIR: 03/03/2026
# ==================================================

# ==================================================
# AUTHENTICATION VIEWS
# ==================================================
from .auth_views import login_view, logout_view
from .register_views import register

# ==================================================
# LANDING & DASHBOARD VIEWS
# ==================================================
from .landing_views import landing
from .dashboard_views import dashboard, owner_dashboard

# ==================================================
# PROFILE VIEWS
# ==================================================
from .profile_views import profile_view, profile_edit

# ==================================================
# USER MANAGEMENT VIEWS
# ==================================================
from .user_management_views import user_list, user_edit_role

# ==================================================
# OUTLET MANAGEMENT VIEWS (MULTI-OUTLET)
# ==================================================
from .outlet_views import pilih_outlet, ganti_outlet

# ==================================================
# STOCK / INVENTORY VIEWS
# ==================================================
from .stock_views import (
    stock_item_list,
    stock_item_add,
    stock_item_edit,
    stock_item_delete,
    low_stock_list,
)

# ==================================================
# PURCHASE VIEWS
# ==================================================
from .purchase_views import (
    purchase_list,
    purchase_add,
    purchase_detail,
)

# ==================================================
# MENU & CATEGORY VIEWS
# ==================================================
from .menu_views import (
    menu_category_list,
    menu_category_add,
    menu_category_edit,
    menu_list,
    menu_add,
    menu_edit,
    menu_delete,
    menu_toggle_availability,
)

# ==================================================
# MENU MODIFIER VIEWS
# ==================================================
from .api_views import get_menu_modifiers

# ==================================================
# CASHIER / ORDER TRANSACTION VIEWS
# ==================================================
from .cashier_views import (
    cashier_view,
    search_menu,
    create_order,
    order_detail,
    print_receipt,
)

# ==================================================
# ORDER LISTING VIEWS
# ==================================================
from .order_views import (
    order_list,
    today_orders,
)

# ==================================================
# REPORTING VIEWS
# ==================================================
from .report_views import (
    sales_report,
    profit_report,
    stock_report,
)

# ==================================================
# EXPORT DATA VIEWS
# ==================================================
from .export_views import (
    export_sales_excel,
    export_sales_pdf,
    export_profit_excel,
    export_profit_pdf,
    export_stock_excel,
)

# ==================================================
# ADMIN DATA MANAGEMENT VIEWS
# ==================================================
from .admin_views import (
    admin_data_management,
    download_template,
    import_data,
    import_export_logs_api,
    export_multiple,
    backup_database,
    backup_list,
    restore_database,
)

# ==================================================
# ADMIN EXPORT/IMPORT VIEWS
# ==================================================
from ..admin_export_import import (
    export_all_data,
    import_data_page,
    import_from_zip,
    download_import_template,
    clear_database
)

# ==================================================
# LOG VIEWS
# ==================================================
from .log_views import activity_log_list

# ==================================================
# PUBLIC EXPORT - SEMUA VIEWS
# ==================================================
__all__ = [
    # Authentication
    "login_view",
    "logout_view",
    "register",

    # Landing & Dashboard
    "landing",
    "dashboard",
    "owner_dashboard",

    # Profile
    "profile_view",
    "profile_edit",

    # User Management
    "user_list",
    "user_edit_role",

    # Outlet Management
    "pilih_outlet",
    "ganti_outlet",

    # Stock
    "stock_item_list",
    "stock_item_add",
    "stock_item_edit",
    "stock_item_delete",
    "low_stock_list",

    # Purchase
    "purchase_list",
    "purchase_add",
    "purchase_detail",

    # Menu
    "menu_category_list",
    "menu_category_add",
    "menu_category_edit",
    "menu_list",
    "menu_add",
    "menu_edit",
    "menu_delete",
    "menu_toggle_availability",

    # Menu Modifier
    "get_menu_modifiers",

    # Cashier
    "cashier_view",
    "search_menu",
    "create_order",
    "order_detail",
    "print_receipt",

    # Orders
    "order_list",
    "today_orders",

    # Reports
    "sales_report",
    "profit_report",
    "stock_report",

    # Export
    "export_sales_excel",
    "export_sales_pdf",
    "export_profit_excel",
    "export_profit_pdf",
    "export_stock_excel",

    # Admin Data Management
    "admin_data_management",
    "download_template",
    "import_data",
    "import_export_logs_api",
    "export_multiple",
    "backup_database",
    "backup_list",
    "restore_database",

    # Admin Export/Import
    "export_all_data",
    "import_data_page",
    "import_from_zip",
    "download_import_template",
    "clear_database",

    # Log Views
    "activity_log_list",
]

# ==================================================
# AKHIR FILE
# ==================================================