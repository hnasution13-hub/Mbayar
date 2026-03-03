# ==================================================
# FILE: Mbayar/core/models/kodebarang.py
# PATH: D:/Project Pyton/Mbayar/core/models/kodebarang.py
# FUNGSI: Model untuk master kode barang (referensi seperti supplier)
# FITUR:
#   - Manajemen kode barang unik
#   - Auto timestamp creation & update
#   - Ordering by kode
#   - String representation dengan format kode - nama
# VERSION: 1.0.0
# UPDATE TERAKHIR: Initial creation
# ==================================================

"""
Model untuk menyimpan master kode barang.
Berfungsi sebagai referensi utama untuk pengkodean barang di seluruh sistem.
Mirip dengan master supplier, digunakan untuk standardisasi kode barang.
"""

from django.db import models
from django.core.exceptions import ValidationError
import re


# ==================================================
# MODEL: KodeBarang
# ==================================================

class KodeBarang(models.Model):
    """
    Master kode barang untuk standardisasi pengkodean di seluruh sistem.
    
    Model ini menyimpan daftar kode barang yang digunakan sebagai referensi
    untuk berbagai modul seperti stok, menu, dan pembelian. Berfungsi seperti
    master supplier namun untuk barang.
    
    Attributes:
        kode (CharField): Kode unik barang (max 50 karakter)
        nama (CharField): Nama barang (max 200 karakter)
        keterangan (TextField): Deskripsi tambahan (opsional)
        created_at (DateTimeField): Auto timestamp saat dibuat
        updated_at (DateTimeField): Auto timestamp saat diupdate
    """
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    kode = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Kode Barang",
        db_index=True,
        help_text="Kode unik untuk barang (maksimal 50 karakter)"
    )
    
    nama = models.CharField(
        max_length=200, 
        verbose_name="Nama Barang",
        help_text="Nama lengkap barang"
    )
    
    keterangan = models.TextField(
        blank=True, 
        verbose_name="Keterangan",
        help_text="Informasi tambahan tentang barang (opsional)"
    )
    
    # ==============================================
    # TIMESTAMPS
    # ==============================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Dibuat Pada",
        help_text="Tanggal dan waktu record dibuat"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Diupdate Pada",
        help_text="Tanggal dan waktu record terakhir diupdate"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Kode Barang"
        verbose_name_plural = "Kode Barang"
        ordering = ['kode']  # Default order by kode ascending
        indexes = [
            models.Index(fields=['kode']),
            models.Index(fields=['nama']),
        ]
        
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        """
        String representation dengan format: "KODE - Nama Barang"
        
        Returns:
            str: Format kode - nama
        """
        return f"{self.kode} - {self.nama}"
    
    # ==============================================
    # VALIDATION METHODS
    # ==============================================
    
    def clean(self):
        """
        Validasi data sebelum disimpan.
        Dipanggil oleh forms dan ModelForm.
        
        Raises:
            ValidationError: Jika validasi gagal
        """
        super().clean()
        
        # Validasi kode tidak boleh hanya spasi
        if self.kode and not self.kode.strip():
            raise ValidationError({'kode': 'Kode barang tidak boleh kosong'})
        
        # Validasi nama tidak boleh hanya spasi
        if self.nama and not self.nama.strip():
            raise ValidationError({'nama': 'Nama barang tidak boleh kosong'})
        
        # Validasi format kode (opsional - sesuai kebutuhan)
        if self.kode and not re.match(r'^[A-Z0-9\-_]+$', self.kode):
            raise ValidationError({
                'kode': 'Kode barang hanya boleh huruf kapital, angka, tanda hubung (-) dan underscore (_)'
            })
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        Override save method untuk melakukan validasi dan formatting.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        # Auto uppercase untuk kode (konsistensi)
        if self.kode:
            self.kode = self.kode.upper().strip()
        
        # Trim whitespace untuk nama
        if self.nama:
            self.nama = self.nama.strip()
        
        # Panggil clean untuk validasi
        self.full_clean()
        
        # Panggil save parent
        super().save(*args, **kwargs)
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def is_valid(self):
        """
        Cek apakah record valid (memiliki kode dan nama).
        
        Returns:
            bool: True jika valid, False jika tidak
        """
        return bool(self.kode and self.nama)
    
    @property
    def display_name(self):
        """
        Nama display lengkap.
        
        Returns:
            str: Format "[KODE] Nama Barang"
        """
        return f"[{self.kode}] {self.nama}"
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def get_by_kode(cls, kode):
        """
        Mendapatkan objek KodeBarang berdasarkan kode.
        
        Args:
            kode (str): Kode barang yang dicari
            
        Returns:
            KodeBarang: Instance jika ditemukan, None jika tidak
        """
        try:
            return cls.objects.get(kode__iexact=kode.strip().upper())
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def search(cls, query):
        """
        Mencari kode barang berdasarkan kode atau nama.
        
        Args:
            query (str): Kata kunci pencarian
            
        Returns:
            QuerySet: Hasil pencarian
        """
        return cls.objects.filter(
            models.Q(kode__icontains=query) | 
            models.Q(nama__icontains=query)
        )
    
    @classmethod
    def get_or_create_kode(cls, kode, nama, keterangan=''):
        """
        Mendapatkan atau membuat kode barang baru.
        
        Args:
            kode (str): Kode barang
            nama (str): Nama barang
            keterangan (str): Keterangan (opsional)
            
        Returns:
            tuple: (KodeBarang, created)
        """
        kode = kode.upper().strip()
        obj, created = cls.objects.get_or_create(
            kode=kode,
            defaults={
                'nama': nama.strip(),
                'keterangan': keterangan
            }
        )
        return obj, created
    
    @classmethod
    def get_all_kodes(cls):
        """
        Mendapatkan list semua kode.
        
        Returns:
            list: List of kode strings
        """
        return cls.objects.values_list('kode', flat=True)
    
    @classmethod
    def get_choices(cls):
        """
        Mendapatkan pilihan untuk dropdown/select.
        
        Returns:
            list: List of tuples (kode, display_name)
        """
        return [(item.kode, item.display_name) for item in cls.objects.all()]


# ==================================================
# SIGNALS (Opsional)
# ==================================================

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

@receiver(pre_save, sender=KodeBarang)
def kodebarang_pre_save(sender, instance, **kwargs):
    """
    Signal sebelum menyimpan KodeBarang.
    """
    # Tambahkan logic pre-save di sini jika diperlukan
    pass

@receiver(post_save, sender=KodeBarang)
def kodebarang_post_save(sender, instance, created, **kwargs):
    """
    Signal setelah menyimpan KodeBarang.
    """
    if created:
        # Logika untuk record baru
        pass
    else:
        # Logika untuk update record
        pass


# ==================================================
# END OF FILE: kodebarang.py
# ==================================================