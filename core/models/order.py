# ==================================================
# FILE: core/models/order.py (VERSI LENGKAP DENGAN MODIFIER & OUTLET)
# FUNGSI: Model untuk Order/Transaksi Penjualan
# ==================================================

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from .menu import Menu
from decimal import Decimal


class Order(models.Model):
    """Transaksi penjualan"""
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Tunai'),
        ('qris', 'QRIS'),
        ('card', 'Kartu'),
        ('transfer', 'Transfer'),
    ]
    
    ORDER_TYPES = [
        ('normal', 'Normal'),
        ('gofood', 'GoFood'),
    ]
    
    outlet = models.ForeignKey(
        'Outlet',
        on_delete=models.PROTECT,
        null=True,
        verbose_name="Cabang"
    )
    
    order_no = models.CharField(max_length=50, unique=True)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer_name = models.CharField(max_length=200, blank=True, default='Umum')
    order_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='normal')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        if not self.outlet and self.cashier:
            try:
                self.outlet = self.cashier.profile.outlet
            except:
                pass
        super().save(*args, **kwargs)
    
    def __str__(self):
        outlet_info = f"[{self.outlet.code}] " if self.outlet else ""
        return f"{outlet_info}{self.order_no}"
    
    def calculate_totals(self):
        items = self.order_items.all()
        
        subtotal = Decimal('0')
        for item in items:
            subtotal += item.subtotal
        
        self.subtotal = subtotal
        self.change = self.amount_paid - self.total
        
        self.save(update_fields=['subtotal', 'change'])
    
    class Meta:
        verbose_name = "Pesanan"
        verbose_name_plural = "Pesanan"
        ordering = ['-order_date']


class OrderItem(models.Model):
    """Item dalam pesanan"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu = models.ForeignKey(Menu, on_delete=models.SET_NULL, null=True)
    menu_name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)
    is_gofood = models.BooleanField(default=False)
    
    def cek_stok_cukup(self, menu, quantity):
        for ingredient in menu.menu_ingredients.all():
            stok_tersedia = ingredient.stock_item.stock
            stok_dibutuhkan = ingredient.quantity_used * quantity
            
            if stok_dibutuhkan > stok_tersedia:
                raise Exception(
                    f"Stok {ingredient.stock_item.name} tidak cukup!\n"
                    f"Tersedia: {stok_tersedia:.2f} {ingredient.stock_item.unit}\n"
                    f"Dibutuhkan: {stok_dibutuhkan:.2f} {ingredient.stock_item.unit}\n"
                    f"Untuk {quantity} porsi {menu.name}"
                )
        return True
    
    def save(self, *args, **kwargs):
        if not self.menu_name and self.menu:
            self.menu_name = self.menu.name
        
        if not self.price and self.menu:
            if self.is_gofood:
                self.price = self.menu.gofood_price
            else:
                self.price = self.menu.selling_price
        
        self.subtotal = self.price * Decimal(str(self.quantity))
        
        if self.menu:
            print(f"\n🛒 Memproses Order: {self.menu_name} x{self.quantity}")
            if self.is_gofood:
                print("   Tipe: GoFood")
            else:
                print("   Tipe: Normal")
            print(f"   Harga: Rp {self.price}")
            self.cek_stok_cukup(self.menu, self.quantity)
        
        super().save(*args, **kwargs)
        
        self.order.calculate_totals()
        
        if self.menu:
            for ingredient in self.menu.menu_ingredients.all():
                stock_item = ingredient.stock_item
                if stock_item:
                    jumlah_dipakai = ingredient.quantity_used * self.quantity
                    stock_item.stock -= jumlah_dipakai
                    stock_item.save()
                    print(f"   Stok {stock_item.name} berkurang: {jumlah_dipakai} (sisa: {stock_item.stock})")
    
    class Meta:
        verbose_name = "Item Pesanan"
        verbose_name_plural = "Item Pesanan"


class OrderItemModifier(models.Model):
    """Modifier yang dipilih untuk item pesanan"""
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='selected_modifiers'
    )
    modifier_name = models.CharField(
        max_length=100,
        verbose_name="Nama Modifier"
    )
    option_name = models.CharField(
        max_length=100,
        verbose_name="Opsi Dipilih"
    )
    price_addition = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Tambahan Harga"
    )
    
    class Meta:
        verbose_name = "Modifier Pesanan"
        verbose_name_plural = "Modifier Pesanan"
    
    def __str__(self):
        return f"{self.modifier_name}: {self.option_name}"