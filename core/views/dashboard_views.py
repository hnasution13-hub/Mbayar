# ==================================================
# FILE: core/views/dashboard_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/dashboard_views.py
# FUNGSI: View untuk dashboard (biasa dan owner)
# ==================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from ..decorators import role_required
from ..models import Order, OrderItem, Menu, StockItem, Outlet
from ..decorators import role_required


@login_required
def dashboard(request):
    """Halaman utama dashboard (untuk kasir/supervisor)"""
    today = timezone.now().date()

    # Statistik hari ini
    today_orders = Order.objects.filter(order_date__date=today)
    total_penjualan = today_orders.aggregate(Sum('total'))['total__sum'] or 0
    jumlah_transaksi = today_orders.count()

    # Menu terlaris
    menu_terlaris = OrderItem.objects.filter(
        order__order_date__date=today
    ).values('menu_name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]

    # Stok menipis
    low_stock = StockItem.objects.filter(stock__lte=F('min_stock'))[:10]

    # Grafik penjualan 7 hari terakhir
    last_7_days = []
    sales_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        total = Order.objects.filter(
            order_date__date=date
        ).aggregate(Sum('total'))['total__sum'] or 0
        last_7_days.append(date.strftime('%d/%m'))
        sales_data.append(float(total))

    context = {
        'total_penjualan': total_penjualan,
        'jumlah_transaksi': jumlah_transaksi,
        'total_menu': Menu.objects.count(),
        'total_stok': StockItem.objects.count(),
        'stok_menipis': low_stock,
        'menu_terlaris': menu_terlaris,
        'orders_today': today_orders[:10],
        'last_7_days': last_7_days,
        'sales_data': sales_data,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
@role_required(['owner', 'administrator'])
def owner_dashboard(request):
    """
    Dashboard khusus untuk owner/administrator yang menampilkan data seluruh cabang.
    """
    today = timezone.now().date()
    first_day_month = today.replace(day=1)

    # ===== STATISTIK GLOBAL =====
    total_sales_today = Order.objects.filter(
        order_date__date=today, status='paid'
    ).aggregate(Sum('total'))['total__sum'] or 0

    total_sales_month = Order.objects.filter(
        order_date__date__gte=first_day_month, status='paid'
    ).aggregate(Sum('total'))['total__sum'] or 0

    transactions_today = Order.objects.filter(
        order_date__date=today, status='paid'
    ).count()

    # ===== STOK KRITIS GLOBAL =====
    low_stock_items = StockItem.objects.filter(
        stock__lte=F('min_stock'), min_stock__gt=0
    ).select_related('kode_barang', 'outlet')[:10]

    # ===== STATISTIK PER CABANG =====
    outlets = Outlet.objects.filter(status='aktif').annotate(
        sales_today=Sum('order__total', filter=Q(order__order_date__date=today, order__status='paid')),
        transactions_today=Count('order', filter=Q(order__order_date__date=today, order__status='paid')),
    ).values('code', 'name', 'sales_today', 'transactions_today')

    # ===== GRAFIK 7 HARI TERAKHIR =====
    last_7_days = []
    sales_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        total = Order.objects.filter(
            order_date__date=date, status='paid'
        ).aggregate(Sum('total'))['total__sum'] or 0
        last_7_days.append(date.strftime('%d/%m'))
        sales_data.append(float(total))

    context = {
        'total_sales_today': total_sales_today,
        'total_sales_month': total_sales_month,
        'transactions_today': transactions_today,
        'low_stock_items': low_stock_items,
        'outlets': outlets,
        'last_7_days': last_7_days,
        'sales_data': sales_data,
    }
    return render(request, 'dashboard/owner.html', context)