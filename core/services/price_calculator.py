# ==================================================
# FILE: core/services/price_calculator.py
# PATH: D:/Project Pyton/Mbayar/core/services/price_calculator.py
# FUNGSI: Service untuk kalkulasi finansial (HPP, Modal, & Harga Jual)
# FITUR:
#   - Perhitungan HPP per item order berdasarkan bahan baku
#   - Estimasi HPP menu per porsi
#   - Tracking harga pembelian terakhir dari database
#   - Kalkulasi modal total menu berdasarkan komposisi bahan
#   - Fitur batch update untuk sinkronisasi harga seluruh menu
# VERSION: 1.0.0
# UPDATE TERAKHIR: Implementasi PriceCalculator dengan integrasi Django Apps
# ==================================================

"""
Service layer yang menangani seluruh logika perhitungan biaya produksi (HPP) 
dan penentuan harga jual dalam ekosistem Mbayar.
"""

import logging
from decimal import Decimal
from django.apps import apps

# Inisialisasi Logger
logger = logging.getLogger(__name__)


# ==================================================
# CLASS: PriceCalculator
# ==================================================

class PriceCalculator:
    """
    Kelas utilitas statis untuk menangani kalkulasi harga dan biaya.
    
    Tanggung Jawab:
    - Menghitung HPP (Harga Pokok Penjualan) secara real-time.
    - Mengambil data historis pembelian untuk estimasi modal.
    - Menyediakan fungsi pembantu untuk update harga massal.
    """
    
    # ----------------------------------------------
    # Method: calculate_hpp_for_order_item
    # ----------------------------------------------
    @staticmethod
    def calculate_hpp_for_order_item(order_item):
        """
        Menghitung total HPP untuk satu baris item dalam transaksi.
        
        Args:
            order_item (OrderItem): Objek item order yang diproses
            
        Returns:
            float: Total nilai HPP (bahan baku * harga beli * quantity)
        """
        try:
            total_hpp = 0
            menu = order_item.menu
            
            if not menu:
                return 0
            
            # Iterasi setiap bahan baku yang terdaftar di menu
            for ingredient in menu.menu_ingredients.all():
                stock_item = ingredient.stock_item
                if stock_item:
                    # Prioritas: Harga Rata-rata > Harga Beli Terakhir
                    harga_beli = float(stock_item.harga_rata_rata)
                    if harga_beli <= 0:
                        harga_beli = float(stock_item.harga_beli_terakhir)
                    
                    # Rumus: (Pemakaian per porsi * Harga Beli) * Jumlah Order
                    hpp_bahan = float(ingredient.quantity_used) * harga_beli * order_item.quantity
                    total_hpp += hpp_bahan
            
            return total_hpp
            
        except Exception as e:
            logger.error(f"Error in calculate_hpp_for_order_item: {e}")
            return 0
    
    # ----------------------------------------------
    # Method: calculate_menu_hpp
    # ----------------------------------------------
    @staticmethod
    def calculate_menu_hpp(menu, quantity=1):
        """
        Menghitung estimasi HPP untuk menu tertentu tanpa harus ada transaksi.
        
        Args:
            menu (Menu): Objek menu yang akan dihitung
            quantity (int): Jumlah porsi (default: 1)
        """
        try:
            total_hpp = 0
            for ingredient in menu.menu_ingredients.all():
                stock_item = ingredient.stock_item
                if stock_item:
                    harga_beli = float(stock_item.harga_rata_rata)
                    if harga_beli <= 0:
                        harga_beli = float(stock_item.harga_beli_terakhir)
                    
                    hpp_bahan = float(ingredient.quantity_used) * harga_beli * quantity
                    total_hpp += hpp_bahan
            
            return total_hpp
            
        except Exception as e:
            logger.error(f"Error in calculate_menu_hpp: {e}")
            return 0
    
    # ----------------------------------------------
    # Method: get_last_purchase_price
    # ----------------------------------------------
    @staticmethod
    def get_last_purchase_price(stock_item_id):
        """
        Mengambil data harga dari transaksi pembelian stok terakhir.
        """
        # Menggunakan apps.get_model untuk menghindari circular import
        StockPurchaseItem = apps.get_model('core', 'StockPurchaseItem')
        
        try:
            last_purchase = StockPurchaseItem.objects.filter(
                stock_item_id=stock_item_id
            ).select_related('purchase').order_by('-purchase__date').first()
            
            if last_purchase and last_purchase.quantity > 0:
                price_per_unit = float(last_purchase.total_price) / float(last_purchase.quantity)
                return {
                    'price_per_unit': price_per_unit,
                    'total_price': float(last_purchase.total_price),
                    'quantity': float(last_purchase.quantity),
                    'date': last_purchase.purchase.date
                }
        except Exception as e:
            logger.error(f"Error in get_last_purchase_price: {e}")
        
        return None
    
    # ----------------------------------------------
    # Method: calculate_menu_modal
    # ----------------------------------------------
    @staticmethod
    def calculate_menu_modal(menu):
        """
        Menghitung total modal (biaya bahan) untuk satu menu berdasarkan pembelian terakhir.
        """
        total_modal = 0
        ingredients = menu.menu_ingredients.all()
        
        for ingredient in ingredients:
            if not ingredient.stock_item:
                continue
                
            last_purchase = PriceCalculator.get_last_purchase_price(ingredient.stock_item.id)
            price_per_unit = last_purchase['price_per_unit'] if last_purchase else 0
            
            ingredient_cost = float(ingredient.quantity_used) * price_per_unit
            total_modal += ingredient_cost
        
        return total_modal
    
    # ----------------------------------------------
    # Method: calculate_menu_selling_price
    # ----------------------------------------------
    @staticmethod
    def calculate_menu_selling_price(menu):
        """
        Menghitung harga jual yang disarankan (saat ini disamakan dengan modal).
        """
        total_modal = PriceCalculator.calculate_menu_modal(menu)
        
        return {
            'total_modal': total_modal,
            'selling_price': total_modal  # Logika margin bisa ditambahkan di sini
        }
    
    # ----------------------------------------------
    # Method: recalculate_all_menu_prices
    # ----------------------------------------------
    @staticmethod
    def recalculate_all_menu_prices():
        """
        Melakukan kalkulasi ulang massal untuk seluruh menu yang ada di sistem.
        
        Returns:
            int: Jumlah menu yang berhasil diperbarui
        """
        Menu = apps.get_model('core', 'Menu')
        menus = Menu.objects.all()
        updated_count = 0
        
        for menu in menus:
            try:
                prices = PriceCalculator.calculate_menu_selling_price(menu)
                menu.total_modal = prices['total_modal']
                menu.selling_price = prices['selling_price']
                menu.save(update_fields=['total_modal', 'selling_price'])
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating menu {menu.id}: {e}")
                continue
        
        return updated_count

# ==================================================
# END OF FILE: price_calculator.py
# ==================================================
