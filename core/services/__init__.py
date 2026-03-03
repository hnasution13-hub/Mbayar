# ==================================================
# FILE: __init__.py
# PATH: core/services/__init__.py
# FUNGSI: Export semua services untuk akses mudah dari core.services
# FITUR:
#   - Import services berdasarkan kategori fungsional
#   - Export semua services melalui __all__
#   - Update dengan service-service terbaru
# VERSION: 1.0.0
# UPDATE TERAKHIR: Initial release dengan semua service
# ==================================================

"""
Module inisialisasi untuk services package.
Mengekspor semua service yang tersedia untuk memudahkan import:
    from core.services import PriceCalculator, StockManager, OrderProcessor, dll.
"""

# ==================================================
# IMPORT SERVICES (Berdasarkan kategori fungsional)
# ==================================================

# 1. PRICE CALCULATOR SERVICES
# ==================================================
from .price_calculator import PriceCalculator

# 2. STOCK MANAGEMENT SERVICES
# ==================================================
from .stock_manager import StockManager

# 3. ORDER PROCESSING SERVICES
# ==================================================
from .order_processor import OrderProcessor, CartManager

# 4. REPORT GENERATOR SERVICES
# ==================================================
from .report_generator import (
    SalesReportGenerator,
    ProfitReportGenerator,
    StockReportGenerator,
)


# ==================================================
# EXPORT ALL SERVICES (__all__)
# ==================================================

__all__ = [
    # === PRICE CALCULATOR ===
    'PriceCalculator',          # Kalkulator harga dan diskon
    
    # === STOCK MANAGER ===
    'StockManager',             # Manajemen stok dan inventori
    
    # === ORDER PROCESSOR ===
    'OrderProcessor',           # Proses pesanan/transaksi
    'CartManager',              # Manajemen keranjang belanja
    
    # === REPORT GENERATORS ===
    'SalesReportGenerator',     # Generator laporan penjualan
    'ProfitReportGenerator',    # Generator laporan keuntungan
    'StockReportGenerator',     # Generator laporan stok
]


# ==================================================
# INFORMASI VERSIONING
# ==================================================

__version__ = '1.0.0'
__services_count__ = len(__all__)
__last_updated__ = '2024-01-15'


# ==================================================
# FUNGSI HELPER (Opsional)
# ==================================================

def get_service_list():
    """
    Mengembalikan daftar semua service yang tersedia.
    
    Returns:
        list: Daftar nama service
    """
    return __all__


def get_service_count():
    """
    Mengembalikan jumlah total service.
    
    Returns:
        int: Jumlah service
    """
    return __services_count__


def get_service_by_category():
    """
    Mengembalikan service yang dikelompokkan berdasarkan kategori.
    
    Returns:
        dict: Service per kategori
    """
    return {
        'price': ['PriceCalculator'],
        'stock': ['StockManager'],
        'order': ['OrderProcessor', 'CartManager'],
        'report': ['SalesReportGenerator', 'ProfitReportGenerator', 'StockReportGenerator'],
    }


# ==================================================
# INISIALISASI PACKAGE
# ==================================================

# Optional: Print info saat development
import os
if os.environ.get('DJANGO_DEVELOPMENT') == 'True':
    print(f"✅ Services loaded: {__services_count__} services")
    print(f"📦 Services: {', '.join(__all__)}")


# ==================================================
# END OF FILE: __init__.py
# ==================================================