# ==================================================
# FILE: core/services/stock_manager.py
# PATH: D:/Project Pyton/Mbayar/core/services/stock_manager.py
# FUNGSI: Service untuk manajemen operasional stok barang
# FITUR:
#   - Penambahan & pengurangan stok secara atomik
#   - Monitoring stok kritis (low stock) dengan threshold kustom
#   - Valuasi total nilai aset stok berdasarkan pembelian terakhir
#   - Sinkronisasi stok otomatis dari transaksi pembelian & penjualan
#   - Pelacakan riwayat pergerakan stok (inbound/outbound)
# VERSION: 1.0.0
# UPDATE TERAKHIR: Implementasi StockManager dengan integrasi Order & Purchase
# ==================================================

"""
Service layer yang menangani seluruh logika manipulasi stok fisik, 
pemeriksaan ketersediaan bahan, dan sinkronisasi inventori dalam sistem Mbayar.
"""

import logging
from django.db.models import F, Q
from ..models import StockItem, StockPurchaseItem

# Inisialisasi Logger
logger = logging.getLogger(__name__)


# ==================================================
# CLASS: StockManager
# ==================================================

class StockManager:
    """
    Kelas utilitas statis untuk manajemen inventori dan stok.
    
    Tanggung Jawab:
    - Melakukan update jumlah stok (tambah/kurang).
    - Memvalidasi kecukupan stok sebelum transaksi.
    - Menghasilkan data pergerakan stok untuk audit.
    """
    
    # ----------------------------------------------
    # Method: add_stock
    # ----------------------------------------------
    @staticmethod
    def add_stock(stock_item_id, quantity):
        """
        Menambah jumlah stok barang tertentu.
        
        Args:
            stock_item_id (int): ID dari StockItem
            quantity (float): Jumlah yang akan ditambahkan
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            item = StockItem.objects.get(id=stock_item_id)
            item.stock = float(item.stock) + float(quantity)
            item.save(update_fields=['stock'])
            
            logger.info(f"Stock added: {item.code} (+{quantity})")
            return True
            
        except StockItem.DoesNotExist:
            logger.error(f"Stock item ID {stock_item_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error in add_stock: {e}")
            return False
    
    # ----------------------------------------------
    # Method: reduce_stock
    # ----------------------------------------------
    @staticmethod
    def reduce_stock(stock_item_id, quantity):
        """
        Mengurangi jumlah stok barang dengan validasi kecukupan.
        
        Returns:
            bool: True jika stok cukup dan berhasil dikurangi
        """
        try:
            item = StockItem.objects.get(id=stock_item_id)
            
            # Validasi kecukupan stok
            if float(item.stock) < float(quantity):
                logger.warning(
                    f"Insufficient stock: {item.code} "
                    f"(Available: {item.stock}, Requested: {quantity})"
                )
                return False
            
            item.stock = float(item.stock) - float(quantity)
            item.save(update_fields=['stock'])
            
            logger.info(f"Stock reduced: {item.code} (-{quantity})")
            return True
            
        except StockItem.DoesNotExist:
            logger.error(f"Stock item ID {stock_item_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error in reduce_stock: {e}")
            return False
    
    # ----------------------------------------------
    # Method: check_low_stock
    # ----------------------------------------------
    @staticmethod
    def check_low_stock(threshold=None):
        """
        Mencari barang-barang yang stoknya sudah mencapai batas minimum.
        
        Args:
            threshold (float): Batas manual jika ingin override min_stock
            
        Returns:
            QuerySet: Daftar barang dengan stok kritis
        """
        query = Q(stock__lte=F('min_stock'))
        if threshold:
            query |= Q(stock__lte=threshold)
        
        return StockItem.objects.filter(query).order_by('stock')
    
    # ----------------------------------------------
    # Method: get_stock_value
    # ----------------------------------------------
    @staticmethod
    def get_stock_value():
        """
        Menghitung total nilai aset seluruh stok berdasarkan harga beli terakhir.
        """
        total_value = 0
        items = StockItem.objects.all()
        
        for item in items:
            last_purchase = StockPurchaseItem.objects.filter(
                stock_item=item
            ).order_by('-purchase__date').first()
            
            if last_purchase and last_purchase.quantity > 0:
                price_per_unit = float(last_purchase.total_price) / float(last_purchase.quantity)
                total_value += float(item.stock) * price_per_unit
        
        return total_value
    
    # ----------------------------------------------
    # Method: update_stock_from_purchase
    # ----------------------------------------------
    @staticmethod
    def update_stock_from_purchase(purchase_item):
        """
        Sinkronisasi stok otomatis saat terjadi pembelian barang masuk.
        """
        return StockManager.add_stock(
            purchase_item.stock_item.id, 
            purchase_item.quantity
        )
    
    # ----------------------------------------------
    # Method: update_stock_from_order
    # ----------------------------------------------
    @staticmethod
    def update_stock_from_order(order_item):
        """
        Sinkronisasi stok otomatis saat terjadi penjualan (mengurangi bahan baku).
        """
        success = True
        if order_item.menu:
            # Iterasi setiap bahan baku yang menyusun menu tersebut
            for ingredient in order_item.menu.menu_ingredients.all():
                quantity_needed = float(ingredient.quantity_used) * order_item.quantity
                result = StockManager.reduce_stock(
                    ingredient.stock_item.id, 
                    quantity_needed
                )
                if not result:
                    success = False
        return success
    
    # ----------------------------------------------
    # Method: get_movement_history
    # ----------------------------------------------
    @staticmethod
    def get_movement_history(stock_item_id=None, start_date=None, end_date=None, limit=100):
        """
        Mengambil riwayat pergerakan stok (saat ini fokus pada stok masuk/pembelian).
        """
        # Import lokal untuk menghindari circular dependency
        from ..models import StockPurchaseItem
        
        movements = []
        purchases = StockPurchaseItem.objects.all()
        
        # Filter berdasarkan parameter
        if stock_item_id:
            purchases = purchases.filter(stock_item_id=stock_item_id)
        if start_date:
            purchases = purchases.filter(purchase__date__date__gte=start_date)
        if end_date:
            purchases = purchases.filter(purchase__date__date__lte=end_date)
        
        # Eksekusi query dengan optimasi select_related
        for p in purchases.select_related('stock_item', 'purchase').order_by('-purchase__date')[:limit]:
            movements.append({
                'tanggal': p.purchase.date,
                'item_name': p.stock_item.name,
                'tipe': 'MASUK',
                'referensi': p.purchase.invoice_no,
                'jumlah': float(p.quantity),
                'unit': p.stock_item.get_unit_display(),
                'stok_akhir': p.stock_item.stock,
                'keterangan': f"Harga: Rp {float(p.price_per_unit):,.0f}"
            })
        
        return movements

# ==================================================
# END OF FILE: stock_manager.py
# ==================================================
