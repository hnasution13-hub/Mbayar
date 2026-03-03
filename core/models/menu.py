# ==================================================
# FILE: core/models/menu.py
# PATH: D:/Project Pyton/Mbayar/core/models/menu.py
# FUNGSI: Model untuk Menu dengan perhitungan HPP yang benar dan modifier
# FITUR:
#   - Kategori menu untuk pengelompokan
#   - Menu dengan perhitungan harga otomatis dari bahan
#   - Bahan menu (MenuIngredient) untuk komposisi
#   - Modifier dan opsi (extra topping, level pedas, dll)
#   - Perhitungan HPP (Harga Pokok Penjualan) real-time
#   - Support harga jual normal dan GoFood
# VERSION: 2.0.0
# UPDATE TERAKHIR: Penambahan MenuModifier dan ModifierOption
# ==================================================

"""
Model untuk manajemen menu, bahan, dan modifier.
Sistem menghitung harga secara otomatis berdasarkan bahan yang digunakan.
Modifier memungkinkan kustomisasi menu seperti level pedas atau extra topping.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
import logging

from .stock import StockItem

logger = logging.getLogger(__name__)


# ==================================================
# MODEL: MenuCategory
# ==================================================

class MenuCategory(models.Model):
    """
    Kategori untuk mengelompokkan menu (Makanan, Minuman, Snack, dll).
    
    Attributes:
        name (CharField): Nama kategori
        description (TextField): Deskripsi kategori (opsional)
        sort_order (IntegerField): Urutan tampilan
        is_active (BooleanField): Status aktif
        created_at (DateTimeField): Auto timestamp
    """
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nama Kategori",
        help_text="Contoh: Makanan, Minuman, Snack"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Deskripsi",
        help_text="Penjelasan tambahan tentang kategori"
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ikon",
        help_text="Nama icon FontAwesome (contoh: fa-utensils)"
    )
    
    sort_order = models.IntegerField(
        default=0,
        verbose_name="Urutan",
        help_text="Semakin kecil angka, semakin atas tampilannya"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
        help_text="Centang jika kategori ini aktif"
    )
    
    # ==============================================
    # TIMESTAMPS
    # ==============================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Dibuat Pada"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Diupdate Pada"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Kategori Menu"
        verbose_name_plural = "Kategori Menu"
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        return self.name
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def menu_count(self):
        """Jumlah menu dalam kategori ini"""
        return self.menu_set.filter(is_available=True).count()


# ==================================================
# MODEL: Menu
# ==================================================

class Menu(models.Model):
    """
    Menu yang dijual di aplikasi.
    
    PENJELASAN UNTUK PEMULA:
    ========================
    Setiap menu bisa punya beberapa bahan.
    Contoh: Nasi Goreng punya bahan:
    - Beras 0.25 kg
    - Telur 2 butir
    - Minyak 0.05 liter
    
    Sistem akan otomatis hitung:
    1. HPP (Harga Pokok Penjualan) = total modal dari semua bahan
    2. HARGA JUAL = total dari harga jual semua bahan
    3. HARGA GOFOOD = total dari harga gofood semua bahan
    
    Attributes:
        code (CharField): Kode unik menu
        name (CharField): Nama menu
        category (ForeignKey): Kategori menu
        image (ImageField): Gambar menu
        description (TextField): Deskripsi menu
        is_available (BooleanField): Status ketersediaan
        estimated_time (IntegerField): Estimasi waktu masak (menit)
        total_modal (DecimalField): Total modal dari semua bahan (auto)
        selling_price (DecimalField): Harga jual normal (auto)
        gofood_price (DecimalField): Harga GoFood (auto)
        preparation_time (IntegerField): Waktu persiapan (menit)
        is_popular (BooleanField): Menu populer
        is_recommended (BooleanField): Menu rekomendasi
        created_at (DateTimeField): Auto timestamp
        updated_at (DateTimeField): Auto timestamp
    """
    
    # ==============================================
    # FIELDS - Informasi Dasar
    # ==============================================
    
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Kode Menu",
        db_index=True,
        help_text="Kode unik untuk menu (contoh: MKN-001)"
    )
    
    name = models.CharField(
        max_length=200, 
        verbose_name="Nama Menu",
        db_index=True,
        help_text="Nama menu yang akan ditampilkan"
    )
    
    category = models.ForeignKey(
        MenuCategory, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Kategori",
        help_text="Kategori menu (Makanan, Minuman, dll)"
    )
    
    image = models.ImageField(
        upload_to='menu/', 
        blank=True, 
        null=True,
        verbose_name="Gambar Menu",
        help_text="Upload gambar menu (format: JPG, PNG)"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Deskripsi",
        help_text="Deskripsi detail tentang menu"
    )
    
    # ==============================================
    # FIELDS - Status & Ketersediaan
    # ==============================================
    
    is_available = models.BooleanField(
        default=True, 
        verbose_name="Tersedia",
        help_text="Centang jika menu tersedia untuk dijual"
    )
    
    estimated_time = models.IntegerField(
        default=15,
        verbose_name="Estimasi Waktu (menit)",
        help_text="Estimasi waktu penyajian dalam menit"
    )
    
    preparation_time = models.IntegerField(
        default=10,
        verbose_name="Waktu Persiapan (menit)",
        help_text="Waktu yang dibutuhkan untuk menyiapkan"
    )
    
    # ==============================================
    # FIELDS - Markup (Kompatibilitas)
    # ==============================================
    
    # Field ini tetap ada untuk kompatibilitas tapi tidak dipakai
    # Markup sekarang diatur di level stok barang
    markup_persen = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Markup Keuntungan (%)",
        help_text="⚠️ TIDAK DIGUNAKAN - Markup diatur di stok barang"
    )
    
    markup_nominal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Tambahan Nominal (Rp)",
        help_text="⚠️ TIDAK DIGUNAKAN - Markup diatur di stok barang"
    )
    
    # ==============================================
    # FIELDS - Hasil Perhitungan Otomatis
    # ==============================================
    
    total_modal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        editable=False,
        verbose_name="Total Modal (Harga Beli)",
        help_text="Total modal dari semua bahan (otomatis)"
    )
    
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        editable=False,
        verbose_name="Harga Jual Normal",
        help_text="Harga jual normal (otomatis dari bahan)"
    )
    
    gofood_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        editable=False,
        verbose_name="Harga GoFood",
        help_text="Harga untuk GoFood (otomatis dari bahan)"
    )
    
    # ==============================================
    # FIELDS - Metadata & Promo
    # ==============================================
    
    is_popular = models.BooleanField(
        default=False,
        verbose_name="Menu Populer",
        help_text="Centang jika menu ini populer"
    )
    
    is_recommended = models.BooleanField(
        default=False,
        verbose_name="Menu Rekomendasi",
        help_text="Centang untuk menu rekomendasi"
    )
    
    # ==============================================
    # TIMESTAMPS
    # ==============================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Dibuat Pada"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Diupdate Pada"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Menu"
        verbose_name_plural = "Menu"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_available']),
            models.Index(fields=['-created_at']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        """Untuk tampilan di dropdown"""
        return f"{self.code} - {self.name}"
    
    # ==============================================
    # CALCULATION METHODS
    # ==============================================
    
    def calculate_prices(self):
        """
        Hitung total modal, harga jual, dan harga gofood dari semua bahan.
        
        LANGKAH-LANGKAH:
        1. Ambil semua bahan menu ini
        2. Untuk setiap bahan, ambil:
           - Harga BELI dari stok (untuk modal)
           - Harga JUAL dari stok (untuk harga jual)
           - Harga GOFOOD dari stok (untuk harga gofood)
        3. Hitung total masing-masing
        
        Returns:
            dict: Dictionary berisi total_modal, selling_price, gofood_price
        """
        if not self.pk:
            # Menu belum disimpan, belum punya bahan
            return {
                'total_modal': 0,
                'selling_price': 0,
                'gofood_price': 0
            }
        
        # Ambil semua bahan
        ingredients = self.menu_ingredients.select_related('stock_item').all()
        
        total_modal = Decimal('0')
        total_jual = Decimal('0')
        total_gofood = Decimal('0')
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🍽️ MENGHITUNG HARGA MENU: {self.name}")
        logger.info(f"{'='*60}")
        
        # Hitung total dari setiap bahan
        for ing in ingredients:
            if ing.stock_item:
                # Konversi ke Decimal untuk perhitungan akurat
                jumlah = Decimal(str(ing.quantity_used))
                
                # ===== HARGA BELI (MODAL) =====
                harga_beli = ing.stock_item.harga_beli_terakhir
                if harga_beli <= 0:
                    # Fallback ke harga rata-rata jika perlu
                    harga_beli = ing.stock_item.harga_rata_rata
                
                modal_item = jumlah * harga_beli
                total_modal += modal_item
                
                # ===== HARGA JUAL (DARI STOK) =====
                harga_jual = ing.stock_item.harga_jual
                jual_item = jumlah * harga_jual
                total_jual += jual_item
                
                # ===== HARGA GOFOOD (DARI STOK) =====
                harga_gofood = ing.stock_item.harga_gofood
                gofood_item = jumlah * harga_gofood
                total_gofood += gofood_item
                
                logger.info(f"\n   📦 {ing.stock_item.name}:")
                logger.info(f"      Jumlah: {float(jumlah):.2f} {ing.stock_item.unit}")
                logger.info(f"      Harga Beli: Rp {float(harga_beli):,.0f} → Modal: Rp {float(modal_item):,.0f}")
                logger.info(f"      Harga Jual: Rp {float(harga_jual):,.0f} → Total Jual: Rp {float(jual_item):,.0f}")
                logger.info(f"      Harga GoFood: Rp {float(harga_gofood):,.0f} → Total GoFood: Rp {float(gofood_item):,.0f}")
        
        # Simpan hasil perhitungan
        self.total_modal = total_modal
        self.selling_price = total_jual
        self.gofood_price = total_gofood
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ RINGKASAN MENU: {self.name}")
        logger.info(f"   Total Modal (Harga Beli): Rp {float(total_modal):,.0f}")
        logger.info(f"   Harga Jual Normal: Rp {float(total_jual):,.0f}")
        logger.info(f"   Harga GoFood: Rp {float(total_gofood):,.0f}")
        logger.info(f"{'='*60}\n")
        
        return {
            'total_modal': float(total_modal),
            'selling_price': float(total_jual),
            'gofood_price': float(total_gofood)
        }
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        Saat menyimpan menu:
        1. Hitung dulu harga-harga
        2. Baru simpan
        """
        logger.info(f"\n💾 Menyimpan Menu: {self.name}")
        self.calculate_prices()
        super().save(*args, **kwargs)
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def ingredient_count(self):
        """Jumlah bahan yang digunakan"""
        return self.menu_ingredients.count()
    
    @property
    def modifier_count(self):
        """Jumlah modifier yang tersedia"""
        return self.modifiers.filter(is_active=True).count()
    
    @property
    def profit_margin(self):
        """Margin keuntungan (harga jual - modal)"""
        return float(self.selling_price) - float(self.total_modal)
    
    @property
    def profit_percentage(self):
        """Persentase keuntungan"""
        if self.total_modal > 0:
            return (self.profit_margin / float(self.total_modal)) * 100
        return 0
    
    @property
    def display_price(self):
        """Format harga untuk display"""
        return f"Rp {float(self.selling_price):,.0f}"
    
    @property
    def display_gofood(self):
        """Format harga gofood untuk display"""
        return f"Rp {float(self.gofood_price):,.0f}"
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def toggle_availability(self):
        """Toggle status ketersediaan"""
        self.is_available = not self.is_available
        self.save()
        return self.is_available
    
    def get_active_modifiers(self):
        """Mendapatkan modifier yang aktif"""
        return self.modifiers.filter(is_active=True)
    
    def has_stock(self):
        """
        Cek apakah semua bahan tersedia di stok.
        
        Returns:
            bool: True jika semua bahan cukup
        """
        for ing in self.menu_ingredients.all():
            if ing.stock_item.current_stock < ing.quantity_used:
                return False
        return True


# ==================================================
# MODEL: MenuIngredient
# ==================================================

class MenuIngredient(models.Model):
    """
    Bahan baku yang digunakan untuk satu menu.
    
    PENJELASAN:
    Satu menu bisa punya banyak bahan.
    Contoh: Nasi Goreng:
    - Bahan: Beras, quantity_used: 0.25
    - Bahan: Telur, quantity_used: 2
    
    Attributes:
        menu (ForeignKey): Menu yang menggunakan bahan
        stock_item (ForeignKey): Bahan baku dari stok
        quantity_used (FloatField): Jumlah yang digunakan
        unit (CharField): Satuan (override dari stok)
        waste_percentage (DecimalField): Persentase waste/penyusutan
        notes (CharField): Catatan tambahan
        is_primary (BooleanField): Bahan utama
        sort_order (IntegerField): Urutan
    """
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    menu = models.ForeignKey(
        Menu, 
        on_delete=models.CASCADE, 
        related_name='menu_ingredients',
        verbose_name="Menu"
    )
    
    stock_item = models.ForeignKey(
        StockItem, 
        on_delete=models.CASCADE, 
        verbose_name="Bahan Baku",
        help_text="Pilih bahan dari master stok"
    )
    
    quantity_used = models.FloatField(
        verbose_name="Jumlah yang Digunakan",
        help_text="Contoh: 0.25 untuk 250ml, 2 untuk 2 butir"
    )
    
    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Satuan",
        help_text="Kosongkan untuk menggunakan satuan dari stok"
    )
    
    waste_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Waste/Penyusutan (%)",
        help_text="Persentase bahan yang terbuang saat proses"
    )
    
    notes = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Catatan",
        help_text="Contoh: 2 butir telur, 100gr daging"
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Bahan Utama",
        help_text="Centang jika ini adalah bahan utama"
    )
    
    sort_order = models.IntegerField(
        default=0,
        verbose_name="Urutan"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        unique_together = ['menu', 'stock_item']  # Satu bahan tidak boleh dobel
        verbose_name = "Bahan Menu"
        verbose_name_plural = "Bahan Menu"
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['menu']),
            models.Index(fields=['stock_item']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        return f"{self.menu.name} - {self.stock_item.name} ({self.quantity_used} {self.unit_display})"
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """Override save untuk update unit dari stock_item"""
        if not self.unit and self.stock_item:
            self.unit = self.stock_item.unit
        super().save(*args, **kwargs)
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def unit_display(self):
        """Satuan untuk display"""
        return self.unit or (self.stock_item.unit if self.stock_item else '')
    
    @property
    def total_cost(self):
        """Total biaya untuk bahan ini"""
        if self.stock_item:
            return float(self.quantity_used) * float(self.stock_item.harga_beli_terakhir)
        return 0
    
    @property
    def total_selling(self):
        """Total harga jual untuk bahan ini"""
        if self.stock_item:
            return float(self.quantity_used) * float(self.stock_item.harga_jual)
        return 0
    
    @property
    def display_quantity(self):
        """Format quantity untuk display"""
        return f"{self.quantity_used:.2f} {self.unit_display}"


# ==================================================
# MODEL: MenuModifier
# ==================================================

class MenuModifier(models.Model):
    """
    Modifier untuk menu (extra topping, level pedas, dll).
    
    Memungkinkan kustomisasi pesanan seperti:
    - Level pedas (single choice)
    - Extra topping (multiple choice)
    - Catatan khusus (text input)
    
    Attributes:
        menu (ForeignKey): Menu yang memiliki modifier
        name (CharField): Nama modifier group
        type (CharField): Tipe input (single/multiple/text)
        required (BooleanField): Wajib dipilih
        min_select (IntegerField): Minimal pilihan (untuk multiple)
        max_select (IntegerField): Maksimal pilihan (untuk multiple)
        sort_order (IntegerField): Urutan tampilan
        is_active (BooleanField): Status aktif
    """
    
    MODIFIER_TYPES = [
        ('single', '🔘 Pilih Satu (Radio)'),
        ('multiple', '✅ Bisa Pilih Banyak (Checkbox)'),
        ('text', '📝 Input Teks (Catatan)'),
    ]
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    menu = models.ForeignKey(
        Menu, 
        on_delete=models.CASCADE, 
        related_name='modifiers',
        verbose_name="Menu"
    )
    
    name = models.CharField(
        max_length=100, 
        verbose_name="Nama Modifier",
        help_text="Contoh: Level Pedas, Extra Topping, Catatan"
    )
    
    type = models.CharField(
        max_length=20, 
        choices=MODIFIER_TYPES, 
        default='single',
        verbose_name="Tipe Input"
    )
    
    required = models.BooleanField(
        default=False, 
        verbose_name="Wajib Dipilih",
        help_text="Pelanggan wajib memilih opsi ini"
    )
    
    min_select = models.IntegerField(
        default=0, 
        verbose_name="Minimal Pilihan",
        help_text="Untuk tipe multiple, minimal opsi yang harus dipilih"
    )
    
    max_select = models.IntegerField(
        default=0, 
        verbose_name="Maksimal Pilihan",
        help_text="0 = tidak terbatas"
    )
    
    placeholder = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Placeholder Text",
        help_text="Untuk tipe text (contoh: 'Tulis catatan...')"
    )
    
    sort_order = models.IntegerField(
        default=0,
        verbose_name="Urutan"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif"
    )
    
    # ==============================================
    # TIMESTAMPS
    # ==============================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Dibuat Pada"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Diupdate Pada"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Modifier Menu"
        verbose_name_plural = "Modifier Menu"
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['menu']),
            models.Index(fields=['is_active']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        return f"{self.menu.name} - {self.name} ({self.get_type_display()})"
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def option_count(self):
        """Jumlah opsi yang tersedia"""
        return self.options.count()
    
    @property
    def has_options(self):
        """Cek apakah memiliki opsi"""
        return self.options.exists() or self.type == 'text'
    
    @property
    def min_max_display(self):
        """Display untuk min/max select"""
        if self.type == 'multiple':
            if self.min_select > 0 and self.max_select > 0:
                return f"Pilih {self.min_select}-{self.max_select}"
            elif self.min_select > 0:
                return f"Minimal {self.min_select}"
            elif self.max_select > 0:
                return f"Maksimal {self.max_select}"
        return ""
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def get_active_options(self):
        """Mendapatkan opsi yang aktif"""
        return self.options.all()
    
    def validate_selection(self, selected_options):
        """
        Validasi pilihan sesuai aturan.
        
        Args:
            selected_options (list): List opsi yang dipilih
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if self.type == 'text':
            return True, ""
        
        if not selected_options and self.required:
            return False, f"{self.name} wajib dipilih"
        
        if self.type == 'single' and len(selected_options) > 1:
            return False, f"Hanya boleh memilih satu untuk {self.name}"
        
        if self.type == 'multiple':
            if self.min_select > 0 and len(selected_options) < self.min_select:
                return False, f"Pilih minimal {self.min_select} untuk {self.name}"
            
            if self.max_select > 0 and len(selected_options) > self.max_select:
                return False, f"Pilih maksimal {self.max_select} untuk {self.name}"
        
        return True, ""


# ==================================================
# MODEL: ModifierOption
# ==================================================

class ModifierOption(models.Model):
    """
    Opsi untuk modifier (Pedas 1, Extra Keju, dll).
    
    Attributes:
        modifier (ForeignKey): Modifier parent
        name (CharField): Nama opsi
        price_addition (DecimalField): Tambahan harga
        is_default (BooleanField): Opsi default
        sort_order (IntegerField): Urutan
        stock_item (ForeignKey): Item stok yang terkait
        quantity_used (FloatField): Jumlah stok terpakai
        is_active (BooleanField): Status aktif
        description (TextField): Deskripsi opsi
    """
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    modifier = models.ForeignKey(
        MenuModifier, 
        on_delete=models.CASCADE, 
        related_name='options',
        verbose_name="Modifier"
    )
    
    name = models.CharField(
        max_length=100, 
        verbose_name="Nama Opsi",
        help_text="Contoh: Pedas 1, Keju, Daging"
    )
    
    price_addition = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Tambahan Harga (Rp)",
        help_text="Harga tambahan untuk opsi ini"
    )
    
    is_default = models.BooleanField(
        default=False, 
        verbose_name="Default",
        help_text="Centang jika ini opsi default"
    )
    
    sort_order = models.IntegerField(
        default=0,
        verbose_name="Urutan"
    )
    
    # Stock tracking
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kurangi Stok",
        help_text="Pilih jika opsi ini mengurangi stok (contoh: extra daging)"
    )
    
    quantity_used = models.FloatField(
        default=0,
        verbose_name="Jumlah Stok Terpakai",
        help_text="Contoh: 0.5 kg untuk extra daging"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Deskripsi",
        help_text="Penjelasan tambahan tentang opsi"
    )
    
    # ==============================================
    # TIMESTAMPS
    # ==============================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Dibuat Pada"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Diupdate Pada"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Opsi Modifier"
        verbose_name_plural = "Opsi Modifier"
        ordering = ['sort_order', 'id']
        unique_together = ['modifier', 'name']  # Nama unik dalam satu modifier
        indexes = [
            models.Index(fields=['modifier']),
            models.Index(fields=['is_active']),
            models.Index(fields=['stock_item']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        if self.price_addition > 0:
            return f"{self.name} (+Rp {self.price_addition:,.0f})"
        return self.name
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """Override save dengan validasi"""
        # Validasi hanya satu default per modifier
        if self.is_default:
            ModifierOption.objects.filter(
                modifier=self.modifier, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def display_price(self):
        """Format harga untuk display"""
        if self.price_addition > 0:
            return f"+ Rp {self.price_addition:,.0f}"
        return "Gratis"
    
    @property
    def has_stock_impact(self):
        """Cek apakah opsi mempengaruhi stok"""
        return self.stock_item is not None and self.quantity_used > 0
    
    @property
    def stock_impact_display(self):
        """Display untuk dampak stok"""
        if self.has_stock_impact:
            return f"Mengurangi {self.quantity_used} {self.stock_item.unit} {self.stock_item.name}"
        return ""


# ==================================================
# SIGNALS (Auto update harga saat bahan berubah)
# ==================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=MenuIngredient)
def update_menu_price_on_ingredient_save(sender, instance, **kwargs):
    """Update harga menu saat bahan disimpan"""
    instance.menu.save()  # Akan trigger calculate_prices

@receiver(post_delete, sender=MenuIngredient)
def update_menu_price_on_ingredient_delete(sender, instance, **kwargs):
    """Update harga menu saat bahan dihapus"""
    instance.menu.save()  # Akan trigger calculate_prices

@receiver(post_save, sender=StockItem)
def update_all_menu_prices_on_stock_change(sender, instance, **kwargs):
    """Update semua menu yang menggunakan stock item ini"""
    # Cari semua menu yang menggunakan stock item ini
    ingredients = MenuIngredient.objects.filter(stock_item=instance)
    for ing in ingredients:
        ing.menu.save()  # Akan trigger calculate_prices


# ==================================================
# END OF FILE: menu.py
# ==================================================