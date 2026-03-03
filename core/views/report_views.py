# ==================================================
# FILE: Mbayar/core/views/report_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/report_views.py
# FUNGSI: View untuk laporan (tanpa export)
# ==================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from ..services.report_generator import (
    SalesReportGenerator, ProfitReportGenerator, StockReportGenerator
)
from ..utils.helpers import parse_date

@login_required
def sales_report(request):
    """Laporan penjualan"""
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    
    generator = SalesReportGenerator(start_date, end_date)
    
    context = {
        'orders': generator.orders,
        'total_penjualan': generator.get_summary()['total_penjualan'],
        'total_transaksi': generator.get_summary()['total_transaksi'],
        'rata_rata': generator.get_summary()['rata_rata'],
        'start_date': start_date,
        'end_date': end_date,
        'dates': [d['date_str'] for d in generator.get_daily_data()],
        'daily_totals': [d['total'] for d in generator.get_daily_data()],
    }
    return render(request, 'reports/sales.html', context)

@login_required
def profit_report(request):
    """Laporan laba rugi"""
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    
    generator = ProfitReportGenerator(start_date, end_date)
    summary = generator.get_summary()
    daily_data = generator.get_daily_profit()
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_penjualan': summary['total_penjualan'],
        'total_hpp': summary['total_hpp'],
        'laba_kotor': summary['laba_kotor'],
        'margin': summary['margin'],
        'detail_items': generator.get_detail_items(50),
        'chart_labels': [d['date_str'] for d in daily_data],
        'chart_penjualan': [d['penjualan'] for d in daily_data],
        'chart_hpp': [d['hpp'] for d in daily_data],
        'chart_laba': [d['laba'] for d in daily_data],
    }
    return render(request, 'reports/profit.html', context)

@login_required
def stock_report(request):
    """Laporan pergerakan stok"""
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    item_id = request.GET.get('item_id')
    
    generator = StockReportGenerator(start_date, end_date)
    summary = generator.get_summary()
    movements = generator.get_movements(item_id)
    
    from ..models import StockItem
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'selected_item': int(item_id) if item_id and item_id != '' else None,
        'stock_items': StockItem.objects.all(),
        'movements': movements,
        'total_item': summary['total_items'],
        'total_masuk': sum(m['jumlah'] for m in movements if m['tipe'] == 'MASUK'),
        'total_keluar': 0,  # Bisa ditambah dari order nanti
        'nilai_stok': summary['total_nilai'],
        'chart_dates': [m['tanggal'].strftime('%d/%m') for m in movements[:10]],
        'chart_masuk': [m['jumlah'] for m in movements[:10] if m['tipe'] == 'MASUK'],
        'chart_keluar': [0 for _ in movements[:10]],
    }
    return render(request, 'reports/stock_movement.html', context)