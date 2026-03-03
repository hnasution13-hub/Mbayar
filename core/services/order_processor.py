# ==================================================
# FILE: core/services/order_processor.py
# PATH: D:/Project Pyton/Mbayar/core/services/order_processor.py
# FUNGSI: Service untuk memproses order dan manajemen keranjang
# FITUR:
#   - Pembuatan order baru dengan kalkulasi pajak & diskon
#   - Pembatalan order dengan pengembalian stok otomatis
#   - Pengambilan detail order lengkap (prefetching)
#   - Manajemen keranjang belanja berbasis session
# VERSION: 1.0.0
# UPDATE TERAKHIR: Implementasi OrderProcessor dan CartManager
# ==================================================

"""
Service layer untuk menangani logika bisnis terkait transaksi (Order) 
dan manajemen keranjang belanja (Cart) dalam sistem Mbayar.
"""

import logging
from django.utils import timezone
from ..models import Order, OrderItem, Menu
from ..utils.helpers import generate_invoice_no
from ..utils.constants import ORDER_INVOICE_PREFIX, DEFAULT_CUSTOMER_NAME, TAX_RATE
from .stock_manager import StockManager
from .price_calculator import PriceCalculator

# Inisialisasi Logger
logger = logging.getLogger(__name__)


# ==================================================
# CLASS: OrderProcessor
# ==================================================

class OrderProcessor:
    """
    Kelas utama untuk memproses seluruh siklus hidup order/transaksi.
    
    Tanggung Jawab:
    - Validasi dan pembuatan record Order & OrderItem
    - Kalkulasi finansial (subtotal, tax, total, change)
    - Penanganan pembatalan dan integrasi stok
    """
    
    def __init__(self, user):
        """
        Inisialisasi processor dengan user yang sedang bertugas.
        
        Args:
            user (User): Objek user/kasir yang melakukan transaksi
        """
        self.user = user
        self.order = None
    
    # ----------------------------------------------
    # Method: create_order
    # ----------------------------------------------
    def create_order(self, data):
        """
        Membuat order baru berdasarkan data dari frontend/keranjang.
        
        Args:
            data (dict): Dictionary berisi customer_name, items, payment_method, dll.
            
        Returns:
            dict: Status keberhasilan dan detail order yang dibuat
        """
        try:
            # 1. Generate nomor invoice unik
            order_no = generate_invoice_no(ORDER_INVOICE_PREFIX)
            
            # 2. Inisialisasi record Order (Status awal: Paid)
            self.order = Order.objects.create(
                order_no=order_no,
                cashier=self.user,
                customer_name=data.get('customer_name', DEFAULT_CUSTOMER_NAME),
                payment_method=data.get('payment_method', 'cash'),
                amount_paid=data.get('amount_paid', 0),
                discount=data.get('discount', 0),
                tax=data.get('tax', 0) or self._calculate_tax(data.get('subtotal', 0)),
                status='paid'
            )
            
            # 3. Proses setiap item dalam order
            total_subtotal = 0
            for item_data in data['items']:
                menu = Menu.objects.get(id=item_data['menu_id'])
                order_item = OrderItem.objects.create(
                    order=self.order,
                    menu=menu,
                    menu_name=menu.name,
                    quantity=item_data['quantity'],
                    price=menu.selling_price,
                    notes=item_data.get('notes', '')
                )
                total_subtotal += float(order_item.subtotal)
            
            # 4. Finalisasi kalkulasi finansial
            self.order.subtotal = total_subtotal
            self.order.total = total_subtotal - float(self.order.discount) + float(self.order.tax)
            self.order.change = float(self.order.amount_paid) - float(self.order.total)
            self.order.save()
            
            logger.info(f"Order created: {self.order.order_no} by {self.user.username}")
            
            return {
                'success': True,
                'order': self.order,
                'order_no': self.order.order_no,
                'total': float(self.order.total),
                'change': float(self.order.change)
            }
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            if self.order:
                self.order.delete()  # Rollback jika terjadi error saat proses item
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_tax(self, subtotal):
        """Helper internal untuk menghitung pajak berdasarkan konstanta TAX_RATE"""
        return float(subtotal) * TAX_RATE
    
    # ----------------------------------------------
    # Method: cancel_order (Static)
    # ----------------------------------------------
    @staticmethod
    def cancel_order(order_no):
        """
        Membatalkan transaksi dan mengembalikan stok bahan baku secara otomatis.
        """
        try:
            order = Order.objects.get(order_no=order_no)
            
            # Iterasi item untuk pengembalian stok bahan (ingredients)
            for item in order.order_items.all():
                if item.menu:
                    for ingredient in item.menu.menu_ingredients.all():
                        StockManager.add_stock(
                            ingredient.stock_item.id,
                            float(ingredient.quantity_used) * item.quantity
                        )
            
            order.status = 'cancelled'
            order.save()
            
            logger.info(f"Order cancelled: {order_no}")
            return True
            
        except Order.DoesNotExist:
            logger.error(f"Order {order_no} not found")
            return False
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    # ----------------------------------------------
    # Method: get_order_details (Static)
    # ----------------------------------------------
    @staticmethod
    def get_order_details(order_no):
        """
        Mengambil detail transaksi lengkap untuk keperluan struk atau laporan.
        """
        try:
            order = Order.objects.prefetch_related(
                'order_items', 
                'order_items__menu'
            ).get(order_no=order_no)
            
            items = []
            for item in order.order_items.all():
                items.append({
                    'id': item.id,
                    'menu_name': item.menu_name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'subtotal': float(item.subtotal),
                    'notes': item.notes
                })
            
            return {
                'order_no': order.order_no,
                'order_date': order.order_date,
                'customer_name': order.customer_name,
                'cashier': order.cashier.username if order.cashier else '-',
                'status': order.status,
                'payment_method': order.get_payment_method_display(),
                'subtotal': float(order.subtotal),
                'discount': float(order.discount),
                'tax': float(order.tax),
                'total': float(order.total),
                'amount_paid': float(order.amount_paid),
                'change': float(order.change),
                'items': items
            }
            
        except Order.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting order details: {e}")
            return None


# ==================================================
# CLASS: CartManager
# ==================================================

class CartManager:
    """
    Kelas untuk mengelola keranjang belanja sementara berbasis session Django.
    """
    
    def __init__(self, session):
        """Inisialisasi keranjang dari data session"""
        self.session = session
        self.cart = session.get('cart', [])
    
    def add_item(self, menu_id, quantity=1):
        """Menambah item ke keranjang atau update quantity jika sudah ada"""
        for item in self.cart:
            if item['id'] == menu_id:
                item['quantity'] += quantity
                self._save()
                return True
        
        try:
            menu = Menu.objects.get(id=menu_id)
            self.cart.append({
                'id': menu_id,
                'name': menu.name,
                'price': float(menu.selling_price),
                'quantity': quantity
            })
            self._save()
            return True
        except Menu.DoesNotExist:
            return False
    
    def remove_item(self, menu_id):
        """Menghapus item tertentu dari keranjang"""
        self.cart = [item for item in self.cart if item['id'] != menu_id]
        self._save()
    
    def update_quantity(self, menu_id, quantity):
        """Mengubah jumlah item secara spesifik"""
        for item in self.cart:
            if item['id'] == menu_id:
                if quantity <= 0:
                    self.remove_item(menu_id)
                else:
                    item['quantity'] = quantity
                self._save()
                return True
        return False
    
    def get_cart(self):
        """Mengambil seluruh isi keranjang saat ini"""
        return self.cart
    
    def clear(self):
        """Mengosongkan seluruh isi keranjang"""
        self.cart = []
        self._save()
    
    def get_totals(self):
        """Menghitung ringkasan finansial keranjang belanja"""
        subtotal = sum(item['price'] * item['quantity'] for item in self.cart)
        tax = subtotal * TAX_RATE
        total = subtotal + tax
        
        return {
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
            'item_count': len(self.cart),
            'total_items': sum(item['quantity'] for item in self.cart)
        }
    
    def _save(self):
        """Sinkronisasi data keranjang kembali ke session Django"""
        self.session['cart'] = self.cart
        self.session.modified = True

# ==================================================
# END OF FILE: order_processor.py
# ==================================================
