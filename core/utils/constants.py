#==================================================
#FILE: Mbayar/core/utils/constants.py
#PATH: D:/Project Pyton/Mbayar/core/utils/constants.py
#FUNGSI: Menyimpan semua konstanta aplikasi
#==================================================


from django.conf import settings

# ===== UNIT CHOICES =====
UNIT_CHOICES = [
    ('kg', 'Kilogram'),
    ('gram', 'Gram'),
    ('liter', 'Liter'),
    ('ml', 'Mililiter'),
    ('pcs', 'Buah/Pcs'),
    ('pack', 'Pack'),
    ('box', 'Box'),
]

# ===== ORDER STATUS =====
ORDER_STATUS = [
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('cancelled', 'Cancelled'),
]

# ===== PAYMENT METHODS =====
PAYMENT_METHODS = [
    ('cash', 'Tunai'),
    ('qris', 'QRIS'),
    ('card', 'Kartu'),
    ('transfer', 'Transfer'),
]

# ===== TAX =====
TAX_RATE = getattr(settings, 'TAX_RATE', 0.11)  # Default 11%

# ===== ROUNDING =====
ROUNDING_MULTIPLE = 500  # Pembulatan ke kelipatan 500

# ===== INVOICE PREFIX =====
PURCHASE_INVOICE_PREFIX = "PO"
ORDER_INVOICE_PREFIX = "ORD"

# ===== DEFAULT VALUES =====
DEFAULT_CUSTOMER_NAME = "Umum"
DEFAULT_MARKUP_PERCENT = 0
DEFAULT_MARKUP_NOMINAL = 0