# ==================================================
# FILE: core/context_processors.py
# PATH: D:/Project Pyton/Mbayar/core/context_processors.py
# DESKRIPSI: Context processors untuk menyediakan data ke semua template
# VERSION: 1.0.0
# ==================================================

from django.conf import settings

# ==================================================
# SITE INFORMATION
# ==================================================

def site_info(request):
    """
    Menyediakan informasi site ke semua template
    """
    return {
        'site_name': 'Mbayar.id',
        'site_version': '1.0.0',
        'app_name': 'Mbayarku',
    }


# ==================================================
# OUTLET INFORMATION (MULTI-OUTLET)
# ==================================================

def outlet_info(request):
    """
    Menyediakan informasi outlet aktif ke semua template
    Data diambil dari request.outlet yang diset oleh middleware
    """
    outlet = getattr(request, 'outlet', None)
    
    return {
        'outlet': outlet,
        'outlet_name': outlet.name if outlet else 'Semua Cabang',
        'outlet_code': outlet.code if outlet else 'ALL',
    }