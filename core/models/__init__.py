# ==================================================
# FILE: Mbayar/core/models/__init__.py
# PATH: D:/Project Pyton/Mbayar/core/models/__init__.py
# FUNGSI: Export semua model untuk akses mudah dari core.models
# FITUR: 
#   - Import model dalam urutan yang benar (menghindari circular import)
#   - Export semua model melalui __all__
#   - Update dengan field-field terbaru
# VERSION: 2.0.0
# UPDATE TERAKHIR: Penambahan model Outlet dan Pegawai
# ==================================================

"""
Module inisialisasi untuk models package.
Mengekspor semua model yang tersedia untuk memudahkan import:
    from core.models import Supplier, StockItem, Order, dll.
"""

# ==================================================
# IMPORT MODELS (Urutan berjenjang hindari circular)
# ==================================================

# 1. MASTER DATA / REFERENSI
# ==================================================
from .outlet import Outlet, Pegawai
from .supplier import Supplier
from .kodebarang import KodeBarang

# 2. MENU & KATEGORI (tergantung outlet)
# ==================================================
from .menu import MenuCategory, Menu, MenuIngredient, MenuModifier, ModifierOption

# 3. STOK & INVENTORI (tergantung menu & supplier)
# ==================================================
from .stock import StockItem, StockPurchase, StockPurchaseItem

# 4. TRANSAKSI / ORDER (tergantung menu & stok)
# ==================================================
from .order import Order, OrderItem, OrderItemModifier

# 5. USER PROFIL & AKTIVITAS
# ==================================================
from .profile import Profile
from .log import ActivityLog

# 6. UTILITY & LOGGING
# ==================================================
from .import_export import ImportExportLog


# ==================================================
# EXPORT ALL MODELS (__all__)
# ==================================================

__all__ = [
    # === MASTER DATA ===
    'Outlet',               # Cabang/toko
    'Pegawai',              # Karyawan per cabang
    'Supplier',             # Pemasok barang
    'KodeBarang',           # Kode unik untuk barang
    
    # === MENU ===
    'MenuCategory',         # Kategori menu (makanan/minuman)
    'Menu',                 # Item menu utama
    'MenuIngredient',       # Bahan baku untuk menu
    'MenuModifier',         # Modifier group (level pedas, topping)
    'ModifierOption',       # Opsi modifier (level 1, level 2)
    
    # === STOCK ===
    'StockItem',            # Item stok/gudang
    'StockPurchase',        # Pembelian stok
    'StockPurchaseItem',    # Detail pembelian stok
    
    # === ORDER ===
    'Order',                # Pesanan/transaksi
    'OrderItem',            # Item dalam pesanan
    'OrderItemModifier',    # Modifier untuk item pesanan
    
    # === USER ===
    'Profile',              # Profil tambahan user
    
    # === LOGS & UTILITY ===
    'ActivityLog',          # Log aktivitas user
    'ImportExportLog',      # Log import/export data
]


# ==================================================
# INFORMASI VERSIONING
# ==================================================

__version__ = '2.0.0'
__models_count__ = len(__all__)
__last_updated__ = '2024-01-15'


# ==================================================
# FUNGSI HELPER (Opsional)
# ==================================================

def get_model_list():
    """
    Mengembalikan daftar semua model yang tersedia.
    
    Returns:
        list: Daftar nama model
    """
    return __all__


def get_model_count():
    """
    Mengembalikan jumlah total model.
    
    Returns:
        int: Jumlah model
    """
    return __models_count__


def get_model_by_category():
    """
    Mengembalikan model yang dikelompokkan berdasarkan kategori.
    
    Returns:
        dict: Model per kategori
    """
    return {
        'master': ['Outlet', 'Pegawai', 'Supplier', 'KodeBarang'],
        'menu': ['MenuCategory', 'Menu', 'MenuIngredient', 'MenuModifier', 'ModifierOption'],
        'stock': ['StockItem', 'StockPurchase', 'StockPurchaseItem'],
        'order': ['Order', 'OrderItem', 'OrderItemModifier'],
        'user': ['Profile'],
        'logs': ['ActivityLog', 'ImportExportLog'],
    }


# ==================================================
# INISIALISASI PACKAGE
# ==================================================

# Optional: Print info saat development
import os
if os.environ.get('DJANGO_DEVELOPMENT') == 'True':
    print(f"✅ Models loaded: {__models_count__} models")
    print(f"📦 Models: {', '.join(__all__)}")


# ==================================================
# END OF FILE: __init__.py
# ==================================================