# ==================================================
# FILE: Mbayar/core/models/supplier.py
# PATH: D:/Project Pyton/Mbayar/core/models/supplier.py
# FUNGSI: Model untuk manajemen data pemasok/supplier barang
# FITUR:
#   - Data lengkap supplier (nama, kontak, telepon, alamat)
#   - Tracking histori pembelian dari supplier
#   - Status aktif/nonaktif untuk supplier
#   - Kategorisasi supplier berdasarkan jenis barang
#   - Metadata pembuatan dan pembaruan data
# VERSION: 2.0.0
# UPDATE TERAKHIR: 03/03/2026
# AUTHOR: m4n9.0de
# ==================================================

"""
Model untuk menyimpan data pemasok (supplier) barang.

Supplier adalah pihak yang memasok barang ke toko/restoran.
Model ini menyimpan informasi kontak dan detail supplier,
serta terintegrasi dengan pembelian stok untuk tracking histori.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
import logging

logger = logging.getLogger(__name__)


# ==================================================
# MODEL: Supplier
# ==================================================

class Supplier(models.Model):
    """
    Model untuk menyimpan data pemasok barang.
    
    Menyimpan informasi lengkap tentang supplier termasuk:
    - Identitas dan kontak (nama, telepon, email)
    - Alamat dan informasi perusahaan
    - Kategori dan jenis barang yang disuplai
    - Status kerjasama (aktif/nonaktif)
    
    Relationships:
        stockitem_set (RelatedManager): Item stok dari supplier ini
        stockpurchase_set (RelatedManager): Pembelian dari supplier ini
    """
    
    # ==============================================
    # CHOICE FIELDS (Constants)
    # ==============================================
    
    SUPPLIER_TYPE_CHOICES = [
        ('distributor', '🏭 Distributor'),
        ('manufacturer', '🏭 Pabrik/Langsung'),
        ('wholesaler', '📦 Grosir'),
        ('agent', '🤝 Agen'),
        ('importir', '🌍 Importir'),
        ('others', '📌 Lainnya'),
    ]
    
    PAYMENT_TERM_CHOICES = [
        ('cash', '💰 Tunai'),
        ('credit_7', '📅 7 Hari'),
        ('credit_14', '📅 14 Hari'),
        ('credit_30', '📅 30 Hari'),
        ('credit_60', '📅 60 Hari'),
    ]
    
    STATUS_CHOICES = [
        ('active', '✅ Aktif'),
        ('inactive', '❌ Nonaktif'),
        ('blacklist', '⛔ Blacklist'),
    ]
    
    # ==============================================
    # FIELDS - Informasi Dasar
    # ==============================================
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Kode Supplier",
        help_text="Kode unik untuk supplier (contoh: SPL001)",
        db_index=True
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nama Supplier",
        help_text="Nama perusahaan / pemasok",
        db_index=True
    )
    
    supplier_type = models.CharField(
        max_length=20,
        choices=SUPPLIER_TYPE_CHOICES,
        default='distributor',
        verbose_name="Tipe Supplier",
        help_text="Kategori/jenis supplier"
    )
    
    # ==============================================
    # FIELDS - Informasi Kontak
    # ==============================================
    
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nama Kontak",
        help_text="Nama orang yang bisa dihubungi"
    )
    
    phone = models.CharField(
        max_length=20,
        verbose_name="No. Telepon",
        help_text="Nomor telepon utama"
    )
    
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="No. Telepon Alternatif",
        help_text="Nomor telepon cadangan"
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name="Email",
        help_text="Alamat email supplier"
    )
    
    website = models.URLField(
        blank=True,
        verbose_name="Website",
        help_text="Alamat website (jika ada)"
    )
    
    # ==============================================
    # FIELDS - Alamat
    # ==============================================
    
    address = models.TextField(
        blank=True,
        verbose_name="Alamat",
        help_text="Alamat lengkap supplier"
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Kota",
        help_text="Kota/Kabupaten"
    )
    
    province = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Provinsi",
        help_text="Provinsi"
    )
    
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Kode Pos",
        help_text="Kode pos"
    )
    
    country = models.CharField(
        max_length=100,
        default='Indonesia',
        verbose_name="Negara",
        help_text="Negara"
    )
    
    # ==============================================
    # FIELDS - Informasi Bisnis
    # ==============================================
    
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="NPWP/Nomor Pajak",
        help_text="Nomor pokok wajib pajak"
    )
    
    payment_term = models.CharField(
        max_length=20,
        choices=PAYMENT_TERM_CHOICES,
        default='cash',
        verbose_name="Termin Pembayaran",
        help_text="Jatuh tempo pembayaran"
    )
    
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nama Bank",
        help_text="Bank untuk transfer"
    )
    
    bank_account = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="No. Rekening",
        help_text="Nomor rekening bank"
    )
    
    bank_account_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Atas Nama Rekening",
        help_text="Nama pemilik rekening"
    )
    
    # ==============================================
    # FIELDS - Status & Metadata
    # ==============================================
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Status",
        db_index=True,
        help_text="Status kerjasama dengan supplier"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Catatan",
        help_text="Catatan internal tentang supplier"
    )
    
    # ==============================================
    # FIELDS - Timestamps
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
        verbose_name = "Supplier"
        verbose_name_plural = "Supplier"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['supplier_type']),
            models.Index(fields=['-created_at']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        """
        String representation dengan format:
        [KODE] NAMA - TELEPON
        """
        return f"{self.code} - {self.name} ({self.phone})"
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        Override save untuk validasi dan formatting.
        """
        # Auto-generate kode jika belum ada
        if not self.code:
            self.code = self.generate_code()
        else:
            self.code = self.code.upper().strip()
        
        # Clean nama
        if self.name:
            self.name = self.name.strip()
        
        # Validasi
        self.clean()
        
        super().save(*args, **kwargs)
    
    # ==============================================
    # VALIDATION
    # ==============================================
    
    def clean(self):
        """
        Validasi data sebelum disimpan.
        """
        # Validasi nomor telepon (hanya angka dan beberapa karakter)
        if self.phone:
            # Hapus karakter non-digit untuk validasi
            phone_digits = re.sub(r'\D', '', self.phone)
            if len(phone_digits) < 8:
                raise ValidationError({
                    'phone': 'Nomor telepon minimal 8 digit'
                })
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def is_active(self):
        """Cek apakah supplier aktif"""
        return self.status == 'active'
    
    @property
    def total_purchases(self):
        """Total pembelian dari supplier ini"""
        return self.stockpurchase_set.count()
    
    @property
    def total_spent(self):
        """Total uang yang sudah dikeluarkan ke supplier ini"""
        from django.db.models import Sum
        total = self.stockpurchase_set.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        return float(total)
    
    @property
    def last_purchase_date(self):
        """Tanggal pembelian terakhir"""
        last_purchase = self.stockpurchase_set.order_by('-date').first()
        return last_purchase.date if last_purchase else None
    
    @property
    def display_address(self):
        """Alamat lengkap untuk display"""
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)
        return ', '.join(filter(None, parts))
    
    @property
    def display_payment_term(self):
        """Termin pembayaran untuk display"""
        return dict(self.PAYMENT_TERM_CHOICES).get(self.payment_term, self.payment_term)
    
    @property
    def display_status(self):
        """Status dengan icon"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def generate_code(self):
        """
        Generate kode supplier otomatis.
        
        Format: SPL + 3 digit angka (SPL001, SPL002, dst)
        
        Returns:
            str: Kode supplier baru
        """
        last_supplier = Supplier.objects.all().order_by('code').last()
        if not last_supplier:
            return 'SPL001'
        
        last_code = last_supplier.code
        if last_code.startswith('SPL'):
            try:
                last_number = int(last_code[3:])
                new_number = last_number + 1
                return f'SPL{new_number:03d}'
            except:
                pass
        
        return 'SPL001'
    
    def get_purchase_history(self, limit=10):
        """
        Mendapatkan history pembelian.
        
        Args:
            limit (int): Jumlah data
            
        Returns:
            QuerySet: History pembelian
        """
        return self.stockpurchase_set.all()[:limit]
    
    def get_items_supplied(self):
        """
        Mendapatkan item stok yang disuplai.
        
        Returns:
            QuerySet: Item stok dari supplier ini
        """
        return self.stockitem_set.all()
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def get_active_suppliers(cls):
        """Mendapatkan semua supplier aktif"""
        return cls.objects.filter(status='active')
    
    @classmethod
    def search(cls, query):
        """
        Mencari supplier berdasarkan kode, nama, atau telepon.
        
        Args:
            query (str): Kata kunci pencarian
            
        Returns:
            QuerySet: Hasil pencarian
        """
        return cls.objects.filter(
            models.Q(code__icontains=query) |
            models.Q(name__icontains=query) |
            models.Q(phone__icontains=query) |
            models.Q(contact_person__icontains=query) |
            models.Q(email__icontains=query)
        )
    
    @classmethod
    def get_by_type(cls, supplier_type):
        """Mendapatkan supplier berdasarkan tipe"""
        return cls.objects.filter(supplier_type=supplier_type, status='active')
    
    @classmethod
    def get_top_suppliers(cls, limit=5):
        """
        Mendapatkan supplier dengan pembelian terbanyak.
        
        Args:
            limit (int): Jumlah supplier
            
        Returns:
            list: Supplier dengan total pembelian
        """
        from django.db.models import Sum
        
        return cls.objects.filter(
            status='active'
        ).annotate(
            total_pembelian=Sum('stockpurchase__total_amount')
        ).order_by('-total_pembelian')[:limit]


# ==================================================
# SIGNALS (Auto update related data)
# ==================================================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Supplier)
def log_supplier_changes(sender, instance, created, **kwargs):
    """
    Log perubahan supplier.
    """
    if created:
        logger.info(f"✅ Supplier baru: {instance.code} - {instance.name}")
    else:
        logger.info(f"📝 Supplier diupdate: {instance.code} - {instance.name}")


# ==================================================
# END OF FILE: supplier.py
# ==================================================