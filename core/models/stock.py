# ==================================================
# FILE: core/models/stock.py
# PATH: D:/Project Pyton/Mbayar/core/models/stock.py
# FUNGSI: Model untuk manajemen stok dan pembelian barang
# FITUR:
#   - Manajemen item stok dengan multi-outlet
#   - Tracking stok, harga beli, dan nilai modal
#   - Perhitungan otomatis harga jual dengan markup
#   - Perhitungan harga GoFood dengan fee
#   - Pembelian stok dengan update rata-rata tertimbang
#   - History pembelian per item
#   - Low stock notification
# VERSION: 2.0.0
# UPDATE TERAKHIR: 03/03/2026
# AUTHOR: m4n9.0de
# ==================================================

"""
Model untuk manajemen inventaris dan pembelian stok.

Modul ini menangani:
1. StockItem: Barang inventaris dengan tracking stok dan harga
2. StockPurchase: Pembelian barang dari supplier
3. StockPurchaseItem: Detail item dalam pembelian

Setiap pembelian akan otomatis mengupdate:
- Stok barang
- Nilai total modal
- Harga rata-rata tertimbang
- Harga jual (dengan markup)
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# ==================================================
# MODEL: StockItem
# ==================================================

class StockItem(models.Model):
    """
    Model untuk barang inventaris/bahan baku.
    
    Menyimpan informasi lengkap tentang item stok termasuk:
    - Identitas (kode, nama, supplier)
    - Stok (jumlah, minimum, peringatan)
    - Keuangan (harga beli, modal total, rata-rata)
    - Harga jual (dengan markup dan pembulatan)
    
    Relationships:
        kode_barang (ForeignKey): Referensi ke master kode barang
        supplier (ForeignKey): Pemasok barang
        outlet (ForeignKey): Cabang tempat stok berada (untuk multi-cabang)
    """
    
    # ==============================================
    # CHOICE FIELDS
    # ==============================================
    
    UNIT_CHOICES = [
        ('kg', '📦 Kilogram (kg)'),
        ('gram', '⚖️ Gram (g)'),
        ('liter', '🧪 Liter (L)'),
        ('ml', '💧 Mililiter (ml)'),
        ('pcs', '📦 Buah/Pcs'),
        ('pack', '📦 Pack'),
        ('box', '📦 Box'),
        ('dus', '📦 Dus'),
        ('karton', '📦 Karton'),
        ('sak', '🛍️ Sak'),
    ]
    
    # ==============================================
    # FIELDS - Relasi
    # ==============================================
    
    kode_barang = models.ForeignKey(
        'KodeBarang', 
        on_delete=models.PROTECT,
        verbose_name="Kode Barang",
        help_text="Pilih kode barang dari master",
        related_name='stock_items'
    )
    
    supplier = models.ForeignKey(
        'Supplier', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Supplier",
        help_text="Pemasok utama barang ini",
        related_name='stock_items'
    )
    
    # ==============================================
    # FIELDS - Multi-Outlet
    # ==============================================
    
    outlet = models.ForeignKey(
        'Outlet',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Cabang",
        help_text="Kosongkan jika stok terpusat (semua cabang)",
        related_name='stock_items'
    )
    
    # ==============================================
    # FIELDS - Informasi Dasar
    # ==============================================
    
    name = models.CharField(
        max_length=200, 
        verbose_name="Nama Barang",
        help_text="Nama lengkap barang (akan otomatis dari kode barang jika baru)"
    )
    
    unit = models.CharField(
        max_length=10, 
        choices=UNIT_CHOICES, 
        default='pcs', 
        verbose_name="Satuan",
        help_text="Satuan unit barang (kg, pcs, liter, dll)"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Deskripsi",
        help_text="Informasi tambahan tentang barang"
    )
    
    # ==============================================
    # FIELDS - Stok
    # ==============================================
    
    stock = models.FloatField(
        default=0, 
        verbose_name="Stok Saat Ini",
        help_text="Jumlah stok tersedia dalam satuan unit"
    )
    
    min_stock = models.FloatField(
        default=0, 
        verbose_name="Stok Minimum",
        help_text="Batas minimum stok (untuk notifikasi)"
    )
    
    max_stock = models.FloatField(
        default=0, 
        verbose_name="Stok Maksimum",
        help_text="Batas maksimum stok (0 = tidak terbatas)"
    )
    
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Lokasi Penyimpanan",
        help_text="Rak/gudang tempat penyimpanan"
    )
    
    # ==============================================
    # FIELDS - Markup & Harga Jual
    # ==============================================
    
    markup_persen = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=30,
        verbose_name="Markup Keuntungan (%)", 
        help_text="Contoh: 30 untuk untung 30% dari modal"
    )
    
    markup_nominal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Tambahan Nominal (Rp)", 
        help_text="Contoh: 2000 untuk tambah Rp 2.000 per unit"
    )
    
    # ==============================================
    # FIELDS - Modal & Harga Beli
    # ==============================================
    
    harga_beli_terakhir = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Harga Beli per Unit Terakhir",
        help_text="Harga beli dari pembelian terakhir"
    )
    
    harga_rata_rata = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Harga Rata-rata per Unit",
        help_text="Rata-rata tertimbang dari semua pembelian"
    )
    
    total_nilai_stok = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Modal Stok",
        help_text="Total nilai uang yang diinvestasikan dalam stok ini"
    )
    
    # ==============================================
    # FIELDS - Hasil Perhitungan Otomatis
    # ==============================================
    
    harga_jual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Harga Jual Per Unit",
        help_text="Harga jual setelah markup dan pembulatan"
    )
    
    harga_gofood = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Harga GoFood",
        help_text="Harga untuk platform GoFood (termasuk fee)"
    )
    
    # ==============================================
    # FIELDS - Metadata
    # ==============================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Dibuat Pada"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Diupdate Pada"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Dibuat Oleh",
        related_name='stock_items_created'
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Item Stok"
        verbose_name_plural = "Item Stok"
        ordering = ['kode_barang__kode']
        unique_together = ['kode_barang', 'outlet']  # Satu barang bisa beda stok per outlet
        indexes = [
            models.Index(fields=['kode_barang']),
            models.Index(fields=['outlet']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['stock']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        outlet_info = f" @ {self.outlet.code}" if self.outlet else ""
        return f"{self.kode_barang.kode} - {self.name}{outlet_info}"
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def is_low_stock(self):
        """Cek apakah stok menipis (di bawah minimum)"""
        return self.stock <= self.min_stock
    
    @property
    def is_out_of_stock(self):
        """Cek apakah stok habis"""
        return self.stock <= 0
    
    @property
    def is_over_stock(self):
        """Cek apakah stok melebihi maksimum"""
        return self.max_stock > 0 and self.stock > self.max_stock
    
    @property
    def modal_total(self):
        """Total uang yang sudah dikeluarkan untuk stok ini (float)"""
        return float(self.total_nilai_stok)
    
    @property
    def modal_rata_per_unit(self):
        """Rata-rata modal per unit dalam float"""
        if self.stock > 0:
            return float(self.total_nilai_stok) / float(self.stock)
        return 0
    
    @property
    def nilai_stok_saat_ini(self):
        """Nilai stok berdasarkan harga jual"""
        return float(self.stock) * float(self.harga_jual)
    
    @property
    def profit_potensial(self):
        """Potensi keuntungan jika semua stok terjual"""
        return self.nilai_stok_saat_ini - float(self.total_nilai_stok)
    
    @property
    def margin_keuntungan(self):
        """Persentase margin keuntungan"""
        if self.modal_rata_per_unit > 0:
            return ((float(self.harga_jual) - self.modal_rata_per_unit) / self.modal_rata_per_unit) * 100
        return 0
    
    @property
    def status_stok(self):
        """Status stok dengan icon"""
        if self.is_out_of_stock:
            return "❌ Habis"
        elif self.is_low_stock:
            return "⚠️ Menipis"
        elif self.is_over_stock:
            return "📦 Berlebih"
        else:
            return "✅ Normal"
    
    @property
    def display_harga_jual(self):
        """Format harga jual untuk display"""
        return f"Rp {float(self.harga_jual):,.0f}/{self.unit}"
    
    @property
    def display_harga_gofood(self):
        """Format harga gofood untuk display"""
        return f"Rp {float(self.harga_gofood):,.0f}/{self.unit}"
    
    # ==============================================
    # METHODS - Perhitungan Harga
    # ==============================================
    
    def hitung_harga_jual(self):
        """
        Hitung harga jual dengan pembulatan ke atas.
        
        ALUR PERHITUNGAN:
        =================
        Modal (harga beli/pcs)
            ↓
        + Markup % (ditentukan user)
            ↓
        + Markup Rp (ditentukan user)
            ↓
        = Harga Jual Sebelum Pembulatan
            ↓
        + Pembulatan ke atas
            ↓
        = Harga Jual Final
            ↓
        + Markup GoFood 20%
            ↓
        + Pembulatan ke atas
            ↓
        = Harga GoFood Final
        
        ATURAN PEMBULATAN:
        ==================
        - < 500    → 500
        - 500-1000 → 1000
        - > 1000   → kelipatan 100 ke atas
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🏷️  MENGHITUNG HARGA JUAL: {self.name}")
            logger.info(f"{'='*60}")
            
            # ===== STEP 1: Ambil modal per unit =====
            modal = float(self.harga_rata_rata)
            if modal <= 0:
                modal = float(self.harga_beli_terakhir)
                logger.info(f"   📌 Menggunakan harga beli terakhir")
            
            logger.info(f"\n1️⃣ MODAL DASAR")
            logger.info(f"   ├─ Harga beli per unit: Rp {modal:,.0f}")
            
            # ===== STEP 2: Hitung markup persen =====
            markup_persen = float(self.markup_persen)
            markup_dari_persen = (markup_persen / 100) * modal
            
            logger.info(f"\n2️⃣ MARKUP PERSEN ({markup_persen}%)")
            logger.info(f"   ├─ {markup_persen}% × Rp {modal:,.0f} = Rp {markup_dari_persen:,.0f}")
            
            # ===== STEP 3: Markup nominal =====
            markup_nominal = float(self.markup_nominal)
            logger.info(f"\n3️⃣ MARKUP NOMINAL")
            logger.info(f"   ├─ Tambahan tetap: Rp {markup_nominal:,.0f}")
            
            # ===== STEP 4: Total markup =====
            total_markup = markup_dari_persen + markup_nominal
            logger.info(f"\n4️⃣ TOTAL MARKUP")
            logger.info(f"   ├─ {markup_persen}% + Rp {markup_nominal:,.0f} = Rp {total_markup:,.0f}")
            
            # ===== STEP 5: Harga sebelum pembulatan =====
            harga_sebelum = modal + total_markup
            logger.info(f"\n5️⃣ HARGA SEBELUM PEMBULATAN")
            logger.info(f"   ├─ Rp {modal:,.0f} + Rp {total_markup:,.0f} = Rp {harga_sebelum:,.0f}")
            
            # ===== STEP 6: Pembulatan ke atas =====
            harga_jual = self._bulatkan_ke_atas(harga_sebelum)
            logger.info(f"\n6️⃣ PEMBULATAN KE ATAS")
            logger.info(f"   ├─ Harga sebelum: Rp {harga_sebelum:,.0f}")
            logger.info(f"   ├─ Harga setelah: Rp {harga_jual:,.0f}")
            
            # ===== STEP 7: Harga Jual Final =====
            self.harga_jual = Decimal(str(harga_jual))
            
            # ===== STEP 8: Hitung Harga GoFood =====
            gofood_fee = getattr(settings, 'GOFOOD_FEE_PERCENT', 20)
            
            if self.harga_jual > 0:
                # Harga GoFood = Harga Jual / (1 - fee_percent/100)
                harga_gofood_sebelum = float(self.harga_jual) / (1 - (gofood_fee / 100))
                harga_gofood = self._bulatkan_ke_atas(harga_gofood_sebelum)
                self.harga_gofood = Decimal(str(harga_gofood))
                
                logger.info(f"\n7️⃣ HARGA GOFOOD (fee {gofood_fee}%)")
                logger.info(f"   ├─ Fee {gofood_fee}%: Rp {float(self.harga_jual) * (gofood_fee/100):,.0f}")
                logger.info(f"   ├─ Harga sebelum: Rp {harga_gofood_sebelum:,.0f}")
                logger.info(f"   ├─ Harga setelah: Rp {harga_gofood:,.0f}")
            else:
                self.harga_gofood = Decimal('0')
                logger.info(f"\n7️⃣ HARGA GOFOOD: Rp 0")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ HASIL AKHIR:")
            logger.info(f"   Harga Jual: Rp {self.harga_jual:,.0f}/{self.unit}")
            logger.info(f"   Harga GoFood: Rp {self.harga_gofood:,.0f}/{self.unit}")
            logger.info(f"{'='*60}")
            
        except Exception as e:
            logger.error(f"❌ ERROR hitung_harga_jual: {e}")
            self.harga_jual = Decimal('0')
            self.harga_gofood = Decimal('0')
        
        return self.harga_jual
    
    def _bulatkan_ke_atas(self, nilai):
        """
        Membulatkan nilai ke atas dengan aturan:
        - < 500    → 500
        - 500-1000 → 1000
        - > 1000   → kelipatan 100 terdekat ke atas
        
        Args:
            nilai (float): Nilai yang akan dibulatkan
            
        Returns:
            float: Nilai setelah pembulatan
        """
        if nilai <= 0:
            return 0
        
        if nilai < 500:
            return 500
        
        if nilai <= 1000:
            return 1000
        
        # Kelipatan 100 ke atas
        return int(((nilai + 99) // 100) * 100)
    
    # ==============================================
    # METHODS - Update Stok & Harga
    # ==============================================
    
    def update_average_cost(self, jumlah_baru, harga_unit_baru):
        """
        Update harga rata-rata tertimbang dengan pembelian baru.
        
        Metode weighted average:
        (Nilai stok lama + Nilai pembelian baru) / (Stok lama + Stok baru)
        
        Args:
            jumlah_baru (float): Jumlah unit yang dibeli
            harga_unit_baru (Decimal): Harga per unit pembelian baru
            
        Returns:
            float: Harga rata-rata baru
        """
        try:
            # Konversi ke float
            jumlah_baru = float(jumlah_baru)
            harga_unit_baru = float(harga_unit_baru)
            
            # Stok dan nilai sebelum pembelian ini
            stok_lama = float(self.stock) - jumlah_baru
            nilai_lama = float(self.total_nilai_stok) - (jumlah_baru * harga_unit_baru)
            
            # Stok dan nilai setelah pembelian
            total_stok = float(self.stock)
            total_nilai = float(self.total_nilai_stok)
            
            # Hitung rata-rata baru
            if total_stok > 0:
                harga_rata_rata_baru = total_nilai / total_stok
            else:
                harga_rata_rata_baru = 0
            
            # Update field
            self.harga_rata_rata = Decimal(str(harga_rata_rata_baru))
            self.harga_beli_terakhir = Decimal(str(harga_unit_baru))
            
            logger.info(f"   📊 Update rata-rata: Rp {harga_rata_rata_baru:,.0f}")
            
            return harga_rata_rata_baru
            
        except Exception as e:
            logger.error(f"Error update_average_cost: {e}")
            return float(self.harga_rata_rata)
    
    def get_harga_beli_terakhir(self):
        """
        Ambil harga beli terakhir dari pembelian.
        
        Returns:
            float: Harga beli terakhir atau 0
        """
        last_purchase = self.stockpurchaseitem_set.order_by('-purchase__date').first()
        if last_purchase:
            return float(last_purchase.harga_unit)
        return 0
    
    # ==============================================
    # METHODS - Stok Operasi
    # ==============================================
    
    def tambah_stok(self, jumlah, harga_per_unit, catatan=""):
        """
        Menambah stok secara manual (adjustment).
        
        Args:
            jumlah (float): Jumlah stok ditambah
            harga_per_unit (Decimal): Harga per unit
            catatan (str): Catatan adjustment
            
        Returns:
            bool: True jika berhasil
        """
        try:
            # Update nilai stok
            nilai_tambah = float(jumlah) * float(harga_per_unit)
            
            self.stock += float(jumlah)
            self.total_nilai_stok += Decimal(str(nilai_tambah))
            
            # Update rata-rata
            if self.stock > 0:
                self.harga_rata_rata = self.total_nilai_stok / Decimal(str(self.stock))
            
            self.harga_beli_terakhir = harga_per_unit
            self.hitung_harga_jual()
            self.save()
            
            # Log adjustment
            logger.info(f"✅ Stok ditambah: +{jumlah} {self.unit} (Rp {float(harga_per_unit):,.0f}/unit)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tambah_stok: {e}")
            return False
    
    def kurangi_stok(self, jumlah, catatan=""):
        """
        Mengurangi stok secara manual (adjustment).
        
        Args:
            jumlah (float): Jumlah stok dikurangi
            catatan (str): Catatan adjustment
            
        Returns:
            bool: True jika berhasil
        """
        try:
            if self.stock < jumlah:
                logger.warning(f"⚠️ Stok tidak cukup: {self.stock} < {jumlah}")
                return False
            
            # Hitung nilai yang dikurangi (menggunakan rata-rata)
            nilai_kurang = float(jumlah) * self.modal_rata_per_unit
            
            self.stock -= float(jumlah)
            self.total_nilai_stok -= Decimal(str(nilai_kurang))
            
            self.save()
            
            logger.info(f"✅ Stok dikurangi: -{jumlah} {self.unit}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error kurangi_stok: {e}")
            return False
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        Override save method untuk auto-calculate.
        
        Saat item baru:
        - Set nama dari kode barang jika kosong
        - Inisialisasi harga jika ada harga beli
        
        Saat update:
        - Hitung ulang harga jual
        """
        logger.info(f"\n💾 Menyimpan StockItem: {self.name or 'New Item'}")
        
        # Set nama dari kode barang jika baru
        if not self.name and self.kode_barang:
            self.name = self.kode_barang.nama
        
        # Inisialisasi untuk item baru
        if not self.pk and self.harga_beli_terakhir > 0:
            self.harga_rata_rata = self.harga_beli_terakhir
            self.total_nilai_stok = Decimal(str(self.stock)) * self.harga_beli_terakhir
        
        # Hitung harga jual
        self.hitung_harga_jual()
        
        logger.info(f"   - Stok: {self.stock} {self.unit}")
        logger.info(f"   - Modal total: Rp {float(self.total_nilai_stok):,.0f}")
        logger.info(f"   - Harga rata-rata: Rp {float(self.harga_rata_rata):,.0f}")
        logger.info(f"   - Harga jual: Rp {float(self.harga_jual):,.0f}")
        
        super().save(*args, **kwargs)
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def get_low_stock_items(cls, outlet=None):
        """
        Mendapatkan item dengan stok menipis.
        
        Args:
            outlet: Filter berdasarkan outlet
            
        Returns:
            QuerySet: Item dengan stok <= minimum
        """
        queryset = cls.objects.filter(stock__lte=models.F('min_stock'))
        if outlet:
            queryset = queryset.filter(outlet=outlet)
        return queryset
    
    @classmethod
    def get_out_of_stock_items(cls, outlet=None):
        """
        Mendapatkan item dengan stok habis.
        
        Args:
            outlet: Filter berdasarkan outlet
            
        Returns:
            QuerySet: Item dengan stok <= 0
        """
        queryset = cls.objects.filter(stock__lte=0)
        if outlet:
            queryset = queryset.filter(outlet=outlet)
        return queryset
    
    @classmethod
    def get_by_outlet(cls, outlet):
        """Mendapatkan semua item di outlet tertentu"""
        return cls.objects.filter(outlet=outlet)
    
    @classmethod
    def search(cls, query):
        """Mencari item berdasarkan kode atau nama"""
        return cls.objects.filter(
            models.Q(kode_barang__kode__icontains=query) |
            models.Q(kode_barang__nama__icontains=query) |
            models.Q(name__icontains=query)
        )


# ==================================================
# MODEL: StockPurchase
# ==================================================

class StockPurchase(models.Model):
    """
    Model untuk pembelian barang dari supplier.
    
    Menyimpan header transaksi pembelian termasuk:
    - Nomor invoice
    - Supplier
    - Tanggal pembelian
    - Total amount
    
    Relationships:
        items (RelatedManager): Detail item dalam pembelian ini
        created_by (ForeignKey): User yang membuat transaksi
    """
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    invoice_no = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="No. Invoice",
        help_text="Nomor invoice dari supplier"
    )
    
    supplier = models.ForeignKey(
        'Supplier', 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Supplier",
        help_text="Pemasok barang",
        related_name='purchases'
    )
    
    date = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Tanggal Pembelian",
        help_text="Tanggal transaksi pembelian"
    )
    
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0, 
        verbose_name="Total Pembelian",
        help_text="Total nilai pembelian (uang keluar)"
    )
    
    notes = models.TextField(
        blank=True, 
        verbose_name="Catatan",
        help_text="Catatan tambahan tentang pembelian"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Dibuat oleh",
        related_name='purchases_created'
    )
    
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
        verbose_name = "Pembelian Stok"
        verbose_name_plural = "Pembelian Stok"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['invoice_no']),
            models.Index(fields=['-date']),
            models.Index(fields=['supplier']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        return f"{self.invoice_no} - {self.date.strftime('%d/%m/%Y')}"
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def total_items(self):
        """Jumlah item dalam pembelian"""
        return self.items.count()
    
    @property
    def total_quantity(self):
        """Total unit barang yang dibeli"""
        return self.items.aggregate(total=models.Sum('jumlah'))['total'] or 0
    
    @property
    def display_total(self):
        """Format total untuk display"""
        return f"Rp {float(self.total_amount):,.0f}"
    
    @property
    def invoice_display(self):
        """Format invoice untuk display"""
        return f"{self.invoice_no} ({self.date.strftime('%d/%b')})"


# ==================================================
# MODEL: StockPurchaseItem
# ==================================================

class StockPurchaseItem(models.Model):
    """
    Detail item dalam pembelian stok.
    
    KONSEP UNTUK PEDAGANG:
    ======================
    Saya beli barang dari supplier:
    - Jumlah = 20 pcs (berapa unit yang saya terima)
    - Harga Total = Rp 20.000 (total uang yang saya bayar ke supplier)
    
    Sistem akan menghitung:
    - Harga per Unit = Rp 20.000 ÷ 20 = Rp 1.000/pcs (untuk stok)
    - Subtotal = Rp 20.000 (uang keluar dari kas - untuk laporan)
    - Modal = Rp 20.000 (total uang keluar)
    """
    
    # ==============================================
    # CHOICE FIELDS
    # ==============================================
    
    HITUNG_CHOICES = [
        ('bulk', '📦 BULK - Beli dalam jumlah banyak'),
        ('piece', '🔢 PIECE - Beli satuan'),
    ]
    
    # ==============================================
    # FIELDS - Relasi
    # ==============================================
    
    purchase = models.ForeignKey(
        StockPurchase, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Pembelian",
        help_text="Header pembelian"
    )
    
    kode_barang = models.ForeignKey(
        'KodeBarang', 
        on_delete=models.PROTECT,
        verbose_name="Kode Barang",
        help_text="Barang yang dibeli",
        related_name='purchase_items'
    )
    
    # ==============================================
    # FIELDS - Informasi Pembelian
    # ==============================================
    
    jumlah = models.FloatField(
        verbose_name="Jumlah (unit)",
        help_text="Jumlah unit yang dibeli"
    )
    
    harga_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Harga Total (uang keluar)",
        help_text="Total uang yang dibayarkan ke supplier"
    )
    
    cara_hitung = models.CharField(
        max_length=10, 
        choices=HITUNG_CHOICES, 
        default='bulk',
        verbose_name="Cara Hitung",
        help_text="BULK = harga total untuk banyak unit, PIECE = harga per unit"
    )
    
    # ==============================================
    # FIELDS - Hasil Perhitungan
    # ==============================================
    
    harga_unit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Harga per Unit",
        help_text="Harga Total ÷ Jumlah (untuk stok)"
    )
    
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Subtotal",
        help_text="Sama dengan Harga Total (uang keluar dari kas)"
    )
    
    # ==============================================
    # FIELDS - Kompatibilitas (Legacy)
    # ==============================================
    
    markup_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Markup % (legacy)"
    )
    
    markup_nominal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Markup Nominal (legacy)"
    )
    
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Total Price (legacy)"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Item Pembelian"
        verbose_name_plural = "Item Pembelian"
        ordering = ['purchase__date', 'id']
        indexes = [
            models.Index(fields=['purchase']),
            models.Index(fields=['kode_barang']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        return f"{self.kode_barang.kode} - {self.jumlah} x Rp {float(self.harga_unit):,.0f}"
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        ALUR LENGKAP UNTUK PEDAGANG:
        
        Contoh Transaksi:
        =================
        Saya beli "Patty Ikan" dari supplier "Kevin Frozen Food"
        - Jumlah: 20 pcs (saya terima 20 pcs)
        - Harga Total: Rp 20.000 (saya bayar ke supplier)
        
        Proses:
        1. Harga per unit = 20.000 ÷ 20 = Rp 1.000/pcs (untuk stok)
        2. Subtotal = Rp 20.000 (uang keluar dari kas)
        3. MODAL = Rp 20.000 (total uang keluar)
        4. Stok bertambah 20 pcs
        5. Total modal stok bertambah Rp 20.000
        """
        
        logger.info("\n" + "="*70)
        logger.info("🔵 TRANSAKSI PEMBELIAN DARI SUPPLIER")
        logger.info("="*70)
        
        # ===== STEP 1: Hitung harga per unit (untuk stok) =====
        if self.jumlah > 0:
            jumlah_dec = Decimal(str(self.jumlah))
            harga_total_dec = Decimal(str(self.harga_total))
            self.harga_unit = harga_total_dec / jumlah_dec
            
            logger.info(f"\n📦 DETAIL PEMBELIAN:")
            logger.info(f"   Barang: {self.kode_barang.nama}")
            logger.info(f"   Jumlah: {float(jumlah_dec):.0f} unit")
            logger.info(f"   Harga Total (bayar ke supplier): Rp {float(harga_total_dec):,.0f}")
            logger.info(f"   Harga per unit (hasil bagi): Rp {float(self.harga_unit):,.0f}/unit")
        else:
            self.harga_unit = Decimal('0')
            logger.info("\n⚠️ PERINGATAN: Jumlah = 0, tidak bisa hitung harga per unit")
        
        # ===== STEP 2: Subtotal = Harga Total (uang keluar) =====
        self.subtotal = self.harga_total
        logger.info(f"\n💰 LAPORAN KEUANGAN:")
        logger.info(f"   Subtotal (uang keluar dari kas): Rp {float(self.subtotal):,.0f}")
        
        # ===== STEP 3: Simpan data pembelian =====
        super().save(*args, **kwargs)
        logger.info(f"   ✅ Data pembelian tersimpan")
        
        # ===== STEP 4: Cari atau buat StockItem =====
        stock_item, created = StockItem.objects.get_or_create(
            kode_barang=self.kode_barang,
            defaults={
                'name': self.kode_barang.nama,
                'unit': 'pcs',
                'stock': 0,
                'min_stock': 0,
                'harga_beli_terakhir': self.harga_unit,
                'harga_rata_rata': self.harga_unit,
                'total_nilai_stok': Decimal('0'),
                'markup_persen': 30,
                'markup_nominal': 0
            }
        )
        
        if created:
            logger.info(f"\n📦 BARANG BARU: {stock_item.name}")
            logger.info(f"   Stok awal: 0 unit")
            logger.info(f"   Modal awal: Rp 0")
        else:
            logger.info(f"\n📦 UPDATE STOK: {stock_item.name}")
            logger.info(f"   Stok sebelum: {stock_item.stock} unit")
            logger.info(f"   Modal sebelum: Rp {float(stock_item.total_nilai_stok):,.0f}")
        
        # ===== STEP 5: TAMBAH STOK (jumlah unit) =====
        stock_item.stock += float(self.jumlah)
        logger.info(f"\n📊 UPDATE STOK:")
        logger.info(f"   Stok ditambah: +{float(self.jumlah)} unit")
        logger.info(f"   Stok sekarang: {stock_item.stock} unit")
        
        # ===== STEP 6: TAMBAH MODAL (total uang keluar) =====
        stock_item.total_nilai_stok += Decimal(str(self.harga_total))
        logger.info(f"\n💰 UPDATE MODAL:")
        logger.info(f"   Modal ditambah: Rp {float(self.harga_total):,.0f}")
        logger.info(f"   TOTAL MODAL SEKARANG: Rp {float(stock_item.total_nilai_stok):,.0f}")
        
        # ===== STEP 7: HITUNG ULANG HARGA RATA-RATA PER UNIT =====
        if stock_item.stock > 0:
            stock_item.harga_rata_rata = stock_item.total_nilai_stok / Decimal(str(stock_item.stock))
            logger.info(f"\n📊 RATA-RATA MODAL PER UNIT:")
            logger.info(f"   Total modal: Rp {float(stock_item.total_nilai_stok):,.0f}")
            logger.info(f"   Total stok: {stock_item.stock} unit")
            logger.info(f"   Rata-rata modal/unit: Rp {float(stock_item.harga_rata_rata):,.0f}")
        else:
            logger.info(f"\n⚠️ Stok 0, tidak bisa hitung rata-rata")
        
        # ===== STEP 8: UPDATE HARGA BELI TERAKHIR =====
        stock_item.harga_beli_terakhir = self.harga_unit
        logger.info(f"\n🏷️ HARGA BELI TERAKHIR: Rp {float(stock_item.harga_beli_terakhir):,.0f}/unit")
        
        # ===== STEP 9: HITUNG HARGA JUAL (dengan markup user) =====
        stock_item.hitung_harga_jual()
        
        # ===== STEP 10: SIMPAN STOCK ITEM =====
        stock_item.save()
        logger.info(f"\n✅ SEMUA DATA TERSIMPAN")
        logger.info(f"   Stok akhir: {stock_item.stock} unit")
        logger.info(f"   Total modal: Rp {float(stock_item.total_nilai_stok):,.0f}")
        logger.info("="*70 + "\n")
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def display_harga(self):
        """Format harga untuk display"""
        return f"Rp {float(self.harga_unit):,.0f} x {float(self.jumlah):.0f} = Rp {float(self.subtotal):,.0f}"
    
    @property
    def nama_barang(self):
        """Nama barang dari kode barang"""
        return self.kode_barang.nama


# ==================================================
# SIGNALS
# ==================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=StockPurchaseItem)
def update_purchase_total(sender, instance, **kwargs):
    """Update total amount di header purchase"""
    purchase = instance.purchase
    total = purchase.items.aggregate(total=models.Sum('subtotal'))['total'] or 0
    purchase.total_amount = total
    purchase.save()

@receiver(post_delete, sender=StockPurchaseItem)
def update_purchase_total_on_delete(sender, instance, **kwargs):
    """Update total amount saat item dihapus"""
    purchase = instance.purchase
    total = purchase.items.aggregate(total=models.Sum('subtotal'))['total'] or 0
    purchase.total_amount = total
    purchase.save()


# ==================================================
# END OF FILE: stock.py
# ==================================================