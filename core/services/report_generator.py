# ==================================================
# FILE: core/services/report_generator.py
# PATH: D:/Project Pyton/Mbayar/core/services/report_generator.py
# FUNGSI: Service untuk pembuatan laporan (Penjualan, Laba Rugi, & Stok)
# FITUR:
#   - SalesReportGenerator: Ringkasan penjualan, tren harian, & produk terlaris
#   - ProfitReportGenerator: Kalkulasi laba kotor, margin, & analisis HPP harian
#   - StockReportGenerator: Monitoring pergerakan stok & valuasi inventori
#   - Integrasi dengan PriceCalculator untuk akurasi data finansial
# VERSION: 1.0.0
# UPDATE TERAKHIR: Implementasi generator laporan komprehensif
# ==================================================

"""
Service layer yang bertanggung jawab untuk mengolah data mentah dari database 
menjadi informasi laporan yang siap disajikan di dashboard atau diekspor.
"""

import logging
from datetime import timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
from ..models import Order, OrderItem, StockItem, StockPurchaseItem
from .price_calculator import PriceCalculator

# Inisialisasi Logger
logger = logging.getLogger(__name__)


# ==================================================
# CLASS: SalesReportGenerator
# ==================================================

class SalesReportGenerator:
    """
    Menghasilkan data laporan terkait performa penjualan.
    """
    
    def __init__(self, start_date=None, end_date=None):
        """
        Inisialisasi periode laporan (default: 30 hari terakhir).
        """
        self.start_date = start_date or timezone.now().date() - timedelta(days=30)
        self.end_date = end_date or timezone.now().date()
        self.orders = self._get_orders()
    
    def _get_orders(self):
        """Helper internal untuk mengambil data order yang sudah lunas (Paid)"""
        return Order.objects.filter(
            order_date__date__gte=self.start_date,
            order_date__date__lte=self.end_date,
            status='paid'
        ).order_by('-order_date')
    
    def get_summary(self):
        """Mengambil ringkasan total penjualan, transaksi, dan rata-rata"""
        orders = self._get_orders()
        total_penjualan = orders.aggregate(Sum('total'))['total__sum'] or 0
        total_transaksi = orders.count()
        rata_rata = total_penjualan / total_transaksi if total_transaksi > 0 else 0
        
        return {
            'total_penjualan': float(total_penjualan),
            'total_transaksi': total_transaksi,
            'rata_rata': float(rata_rata),
            'start_date': self.start_date,
            'end_date': self.end_date
        }
    
    def get_daily_data(self):
        """Menghasilkan data deret waktu (time-series) untuk grafik harian"""
        daily_data = []
        current = self.start_date
        
        while current <= self.end_date:
            daily_total = self.orders.filter(order_date__date=current).aggregate(
                Sum('total')
            )['total__sum'] or 0
            
            daily_data.append({
                'date': current,
                'date_str': current.strftime('%d/%m'),
                'total': float(daily_total)
            })
            current += timedelta(days=1)
        
        return daily_data
    
    def get_top_products(self, limit=10):
        """Mengidentifikasi produk terlaris berdasarkan kuantitas dan nilai jual"""
        top_items = OrderItem.objects.filter(
            order__in=self.orders
        ).values('menu_name').annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum('subtotal')
        ).order_by('-total_qty')[:limit]
        
        return list(top_items)
    
    def get_payment_methods(self):
        """Menganalisis distribusi penggunaan metode pembayaran"""
        methods = self.orders.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total')
        )
        
        result = []
        for method in methods:
            result.append({
                'method': method['payment_method'],
                'method_display': dict(Order.PAYMENT_METHODS).get(method['payment_method'], '-'),
                'count': method['count'],
                'total': float(method['total'])
            })
        
        return result


# ==================================================
# CLASS: ProfitReportGenerator
# ==================================================

class ProfitReportGenerator:
    """
    Menghasilkan data laporan laba rugi dengan membandingkan Penjualan vs HPP.
    """
    
    def __init__(self, start_date=None, end_date=None):
        self.start_date = start_date or timezone.now().date() - timedelta(days=30)
        self.end_date = end_date or timezone.now().date()
        self.orders = self._get_orders()
    
    def _get_orders(self):
        """Mengambil data order dengan prefetching untuk optimasi query"""
        return Order.objects.filter(
            order_date__date__gte=self.start_date,
            order_date__date__lte=self.end_date,
            status='paid'
        ).prefetch_related('order_items__menu__menu_ingredients')
    
    def get_summary(self):
        """Menghitung total laba kotor dan persentase margin"""
        total_penjualan = 0
        total_hpp = 0
        detail_count = 0
        
        for order in self.orders:
            for item in order.order_items.all():
                subtotal = float(item.subtotal) if item.subtotal else 0
                hpp = PriceCalculator.calculate_hpp_for_order_item(item)
                
                total_penjualan += subtotal
                total_hpp += hpp
                detail_count += 1
        
        laba_kotor = total_penjualan - total_hpp
        margin = (laba_kotor / total_penjualan * 100) if total_penjualan > 0 else 0
        
        return {
            'total_penjualan': total_penjualan,
            'total_hpp': total_hpp,
            'laba_kotor': laba_kotor,
            'margin': margin,
            'total_transaksi': self.orders.count(),
            'total_items': detail_count,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
    
    def get_detail_items(self, limit=100):
        """Menyajikan detail laba per item produk"""
        items = []
        for order in self.orders:
            for item in order.order_items.all():
                if len(items) >= limit: break
                    
                subtotal = float(item.subtotal) if item.subtotal else 0
                hpp = PriceCalculator.calculate_hpp_for_order_item(item)
                laba = subtotal - hpp
                margin = (laba / subtotal * 100) if subtotal > 0 else 0
                
                items.append({
                    'order_date': order.order_date,
                    'order_no': order.order_no,
                    'menu_name': item.menu_name,
                    'quantity': item.quantity,
                    'price': float(item.price) if item.price else 0,
                    'subtotal': subtotal,
                    'hpp': hpp,
                    'laba': laba,
                    'margin': margin
                })
            if len(items) >= limit: break
        
        return items

    def get_daily_profit(self):
        """Menganalisis tren laba harian"""
        daily_data = {}
        for order in self.orders:
            date_str = order.order_date.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {'date': order.order_date, 'penjualan': 0, 'hpp': 0, 'laba': 0}
            
            for item in order.order_items.all():
                subtotal = float(item.subtotal) if item.subtotal else 0
                hpp = PriceCalculator.calculate_hpp_for_order_item(item)
                daily_data[date_str]['penjualan'] += subtotal
                daily_data[date_str]['hpp'] += hpp
                daily_data[date_str]['laba'] += (subtotal - hpp)
        
        result = []
        for date_str, data in sorted(daily_data.items()):
            result.append({
                'date': data['date'],
                'date_str': data['date'].strftime('%d/%m'),
                'penjualan': data['penjualan'],
                'hpp': data['hpp'],
                'laba': data['laba']
            })
        return result


# ==================================================
# CLASS: StockReportGenerator
# ==================================================

class StockReportGenerator:
    """
    Menghasilkan laporan terkait inventori dan pergerakan stok.
    """
    
    def __init__(self, start_date=None, end_date=None):
        self.start_date = start_date or timezone.now().date() - timedelta(days=30)
        self.end_date = end_date or timezone.now().date()
    
    def get_movements(self, item_id=None, limit=100):
        """Melacak riwayat barang masuk dari pembelian stok"""
        purchases = StockPurchaseItem.objects.filter(
            purchase__date__date__gte=self.start_date,
            purchase__date__date__lte=self.end_date
        ).select_related('stock_item', 'purchase').order_by('-purchase__date')
        
        if item_id:
            purchases = purchases.filter(stock_item_id=item_id)
        
        movements = []
        for p in purchases[:limit]:
            movements.append({
                'tanggal': p.purchase.date,
                'item_name': p.stock_item.name,
                'tipe': 'MASUK',
                'referensi': p.purchase.invoice_no,
                'jumlah': float(p.quantity),
                'unit': p.stock_item.get_unit_display(),
                'stok_akhir': float(p.stock_item.stock),
                'keterangan': f"Rp {float(p.price_per_unit):,.0f}/unit"
            })
        return movements
    
    def get_summary(self):
        """Menghitung total nilai aset inventori dan jumlah stok kritis"""
        items = StockItem.objects.all()
        total_nilai = 0
        low_stock_count = 0
        
        for item in items:
            last_purchase = StockPurchaseItem.objects.filter(
                stock_item=item
            ).order_by('-purchase__date').first()
            
            if last_purchase and last_purchase.quantity > 0:
                price_per_unit = float(last_purchase.total_price) / float(last_purchase.quantity)
                total_nilai += float(item.stock) * price_per_unit
            
            if item.is_low_stock:
                low_stock_count += 1
        
        return {
            'total_items': items.count(),
            'total_nilai': total_nilai,
            'low_stock_count': low_stock_count,
            'start_date': self.start_date,
            'end_date': self.end_date
        }

# ==================================================
# END OF FILE: report_generator.py
# ==================================================
