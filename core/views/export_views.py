# ==================================================
# FILE: Mbayar/core/views/export_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/export_views.py
# FUNGSI: View untuk export Excel dan PDF
# ==================================================

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from ..models import Order, StockPurchaseItem, StockItem
from ..services.report_generator import SalesReportGenerator, ProfitReportGenerator
from ..services.price_calculator import PriceCalculator
from ..utils.helpers import parse_date
from ..utils.excel_exporters import SalesExcelExporter, ProfitExcelExporter
from ..utils.pdf_exporters import SalesPDFExporter

# ===== EXPORT EXCEL =====

@login_required
def export_sales_excel(request):
    """Export laporan penjualan ke Excel"""
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    
    orders = Order.objects.filter(
        order_date__date__gte=start_date,
        order_date__date__lte=end_date,
        status='paid'
    ).order_by('-order_date')
    
    exporter = SalesExcelExporter()
    exporter.export(orders, start_date, end_date)
    
    filename = f"laporan_penjualan_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
    return exporter.get_response(filename)

@login_required
def export_profit_excel(request):
    """Export laporan laba rugi ke Excel"""
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    
    generator = ProfitReportGenerator(start_date, end_date)
    summary = generator.get_summary()
    detail_items = generator.get_detail_items(1000)  # Ambil semua untuk export
    
    exporter = ProfitExcelExporter()
    exporter.export(detail_items, start_date, end_date, summary)
    
    filename = f"laporan_laba_rugi_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
    return exporter.get_response(filename)

@login_required
def export_stock_excel(request):
    """Export laporan stok ke Excel"""
    from ..utils.excel_exporters import ExcelExporter
    
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    item_id = request.GET.get('item_id')
    
    # Query movements
    purchases = StockPurchaseItem.objects.filter(
        purchase__date__date__gte=start_date,
        purchase__date__date__lte=end_date
    ).select_related('stock_item', 'purchase').order_by('-purchase__date')
    
    if item_id and item_id != '':
        try:
            purchases = purchases.filter(stock_item_id=int(item_id))
        except:
            pass
    
    exporter = ExcelExporter("Pergerakan Stok")
    exporter.add_title("LAPORAN PERGERAKAN STOK")
    exporter.add_period_info(start_date, end_date)
    exporter.current_row += 1
    
    headers = ['No', 'Tanggal', 'Item', 'Tipe', 'Jumlah', 'Satuan', 'Harga/Unit', 'Total', 'Referensi']
    exporter.add_header(headers)
    
    total_nilai = 0
    for i, purchase in enumerate(purchases, 1):
        jumlah = float(purchase.quantity) if purchase.quantity else 0
        harga = float(purchase.price_per_unit) if purchase.price_per_unit else 0
        total = float(purchase.total_price) if purchase.total_price else 0
        total_nilai += total
        
        data = [
            i,
            purchase.purchase.date.strftime('%d/%m/%Y %H:%M'),
            purchase.stock_item.name,
            'MASUK',
            jumlah,
            purchase.stock_item.get_unit_display(),
            harga,
            total,
            purchase.purchase.invoice_no
        ]
        formats = {5: 'number', 7: 'number', 8: 'number'}
        exporter.add_row(data, formats)
    
    if purchases.count() > 0:
        exporter.current_row += 1
        exporter.add_total_row("TOTAL NILAI:", total_nilai, 7)
    
    exporter.add_footer()
    
    filename = f"laporan_stok_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
    return exporter.get_response(filename)

# ===== EXPORT PDF =====

@login_required
def export_sales_pdf(request):
    """Export laporan penjualan ke PDF"""
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    
    orders = Order.objects.filter(
        order_date__date__gte=start_date,
        order_date__date__lte=end_date,
        status='paid'
    ).order_by('-order_date')
    
    exporter = SalesPDFExporter()
    exporter.export(orders, start_date, end_date)
    
    filename = f"laporan_penjualan_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.pdf"
    return exporter.get_response(filename)

@login_required
def export_profit_pdf(request):
    """Export laporan laba rugi ke PDF"""
    from ..utils.pdf_exporters import PDFExporter
    
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    
    generator = ProfitReportGenerator(start_date, end_date)
    summary = generator.get_summary()
    detail_items = generator.get_detail_items(50)
    
    exporter = PDFExporter("Laporan Laba Rugi")
    exporter.add_title("LAPORAN LABA RUGI")
    exporter.add_period_info(start_date, end_date)
    
    # Summary
    summary_data = [
        ['Total Penjualan', f"Rp {summary['total_penjualan']:,.0f}"],
        ['Total HPP', f"Rp {summary['total_hpp']:,.0f}"],
        ['Laba Kotor', f"Rp {summary['laba_kotor']:,.0f}"],
        ['Margin', f"{summary['margin']:.1f}%"]
    ]
    exporter.add_summary_table(summary_data)
    
    # Table data
    table_data = [['No', 'Tanggal', 'Menu', 'Qty', 'Penjualan', 'HPP', 'Laba']]
    for i, item in enumerate(detail_items, 1):
        table_data.append([
            str(i),
            item['order_date'].strftime('%d/%m'),
            item['menu_name'][:15] + ('...' if len(item['menu_name']) > 15 else ''),
            str(item['quantity']),
            f"Rp {item['subtotal']:,.0f}",
            f"Rp {item['hpp']:,.0f}",
            f"Rp {item['laba']:,.0f}"
        ])
    
    exporter.add_table(table_data, [25, 40, 80, 25, 60, 60, 60])
    exporter.add_footer()
    
    filename = f"laporan_laba_rugi_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.pdf"
    return exporter.get_response(filename)