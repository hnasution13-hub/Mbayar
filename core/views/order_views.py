# ==================================================
# FILE: Mbayar/core/views/order_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/order_views.py
# FUNGSI: View untuk riwayat transaksi
# ==================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from ..models import Order

@login_required
def order_list(request):
    """Daftar semua transaksi"""
    orders = Order.objects.all().order_by('-order_date')
    return render(request, 'orders/list.html', {'orders': orders})

@login_required
def today_orders(request):
    """Daftar transaksi hari ini"""
    today = timezone.now().date()
    orders = Order.objects.filter(order_date__date=today).order_by('-order_date')
    return render(request, 'orders/list.html', {'orders': orders, 'today': True})