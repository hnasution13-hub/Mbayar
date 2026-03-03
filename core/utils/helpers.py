# ==================================================
# FILE: Mbayar/core/utils/helpers.py
# PATH: D:/Project Pyton/Mbayar/core/utils/helpers.py
# FUNGSI: Fungsi-fungsi bantu yang sering dipakai
# ==================================================

import re
from datetime import datetime
from django.utils import timezone

def format_rupiah(angka):
    """
    Format angka ke format Rupiah
    Contoh: 10000 → "Rp 10.000"
    """
    if angka is None:
        return "Rp 0"
    try:
        return f"Rp {float(angka):,.0f}".replace(',', '.')
    except (ValueError, TypeError):
        return "Rp 0"

def parse_rupiah(rupiah_string):
    """
    Parse string Rupiah ke angka
    Contoh: "Rp 10.000" → 10000
    """
    if not rupiah_string:
        return 0
    # Hanya ambil angka
    numbers = re.sub(r'[^\d]', '', str(rupiah_string))
    try:
        return int(numbers) if numbers else 0
    except ValueError:
        return 0

def generate_invoice_no(prefix="INV"):
    """
    Generate nomor invoice unik
    Format: PREFIX-YYYYMMDDHHMMSS
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}-{timestamp}"

def parse_date(date_string, default=None):
    """
    Parse string ke date object dengan berbagai format
    """
    if not date_string:
        return default or timezone.now().date()
    
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(str(date_string), fmt).date()
        except (ValueError, TypeError):
            continue
    
    return default or timezone.now().date()

def round_up_to_multiple(value, multiple=500):
    """
    Pembulatan ke atas ke kelipatan tertentu
    Contoh: 1250 → 1500 (kelipatan 500)
    """
    if value <= 0:
        return 0
    return int(((value + multiple - 1) // multiple) * multiple)

def get_client_ip(request):
    """Mendapatkan IP address client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_activity(user, action, details=""):
    """
    Catat aktivitas user ke file log
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    username = user.username if user else "Anonymous"
    log_line = f"[{timestamp}] {username}: {action} - {details}\n"
    
    try:
        with open('logs/activities.log', 'a') as f:
            f.write(log_line)
    except:
        pass  # Gagal log, tapi jangan sampai crash