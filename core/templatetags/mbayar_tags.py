# ==================================================
# FILE: Mbayar/core/templatetags/mbayar_tags.py
# PATH: D:/Project Pyton/Mbayar/core/templatetags/mbayar_tags.py
# FUNGSI: Custom template tags untuk Mbayar POS
# ==================================================

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def rupiah(value):
    """
    Format angka ke Rupiah
    Usage: {{ value|rupiah }}
    """
    if value is None:
        return 'Rp 0'
    try:
        return f"Rp {float(value):,.0f}".replace(',', '.')
    except (ValueError, TypeError):
        return 'Rp 0'

@register.filter
def persen(value):
    """
    Format ke persen
    Usage: {{ value|persen }}
    """
    if value is None:
        return '0%'
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return '0%'

@register.filter
def divide(value, arg):
    """Bagi value dengan arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Kalikan value dengan arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Kurangi value dengan arg"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def status_badge(value):
    """
    Konversi status ke HTML badge
    Usage: {{ order.status|status_badge }}
    """
    badges = {
        'paid': ('success', 'Lunas'),
        'pending': ('warning', 'Pending'),
        'cancelled': ('danger', 'Batal'),
        'cash': ('info', 'Tunai'),
        'qris': ('info', 'QRIS'),
        'card': ('info', 'Kartu'),
        'transfer': ('info', 'Transfer'),
    }
    
    if value in badges:
        color, text = badges[value]
        return mark_safe(f'<span class="badge bg-{color}">{text}</span>')
    return value

@register.filter
def truncate(value, length):
    """Potong string"""
    if len(value) > length:
        return value[:length] + '...'
    return value

@register.simple_tag
def active_class(request, pattern):
    """Tentukan class active untuk menu"""
    import re
    if re.search(pattern, request.path):
        return 'active'
    return ''