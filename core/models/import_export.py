# ==================================================
# FILE: core/models/import_export.py
# PATH: D:/Project Pyton/Mbayar/core/models/import_export.py
# FUNGSI: Model untuk log aktivitas import/export data
# FITUR:
#   - Mencatat semua aktivitas import dan export
#   - Tracking status, jumlah record, dan error
#   - Informasi file dan durasi proses
#   - IP address untuk audit trail
# VERSION: 1.0.0
# UPDATE TERAKHIR: Penambahan field duration_seconds dan completed_at
# ==================================================

"""
Model untuk mencatat semua aktivitas import dan export data dalam sistem.
Berguna untuk audit trail, monitoring, dan troubleshooting.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


# ==================================================
# MODEL: ImportExportLog
# ==================================================

class ImportExportLog(models.Model):
    """
    Model untuk mencatat log semua aktivitas import dan export data.
    
    Menyimpan informasi detail seperti:
    - Jenis aksi (import/export/backup/restore)
    - Tipe data yang diproses
    - Status dan jumlah record
    - Informasi file dan durasi
    - IP address untuk audit
    
    Relationships:
        user (ForeignKey): User yang melakukan aksi
    """
    
    # ==============================================
    # CHOICE FIELDS (Constants)
    # ==============================================
    
    ACTION_TYPES = [
        ('import', 'Import Data'),
        ('export', 'Export Data'),
        ('backup', 'Backup Database'),
        ('restore', 'Restore Database'),
        ('template_download', 'Download Template'),
    ]
    
    DATA_TYPES = [
        # Master Data
        ('kode_barang', 'Kode Barang'),
        ('supplier', 'Supplier'),
        ('outlet', 'Outlet'),
        ('pegawai', 'Pegawai'),
        
        # Menu & Produk
        ('menu', 'Menu & Bahan'),
        ('menu_category', 'Kategori Menu'),
        ('modifier', 'Modifier Menu'),
        
        # Stok & Inventori
        ('stock_item', 'Item Stok'),
        ('stock_purchase', 'Pembelian Stok'),
        ('stock_opname', 'Stok Opname'),
        
        # Transaksi
        ('order', 'Order/Transaksi'),
        ('order_item', 'Item Order'),
        
        # Laporan
        ('sales_report', 'Laporan Penjualan'),
        ('profit_report', 'Laporan Laba'),
        ('stock_report', 'Laporan Stok'),
        ('activity_report', 'Laporan Aktivitas'),
        
        # Database
        ('database', 'Database Full'),
        ('settings', 'Pengaturan Sistem'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '⏳ Diproses'),
        ('success', '✅ Sukses'),
        ('warning', '⚠️ Warning'),
        ('failed', '❌ Gagal'),
        ('cancelled', '🚫 Dibatalkan'),
    ]
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    # User Information
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Pengguna",
        help_text="User yang melakukan aksi"
    )
    
    # Action Information
    action = models.CharField(
        max_length=20, 
        choices=ACTION_TYPES,
        verbose_name="Tipe Aksi",
        help_text="Jenis aksi yang dilakukan"
    )
    
    data_type = models.CharField(
        max_length=50, 
        choices=DATA_TYPES,
        verbose_name="Tipe Data",
        help_text="Tipe data yang diproses"
    )
    
    # File Information
    filename = models.CharField(
        max_length=255,
        verbose_name="Nama File",
        help_text="Nama file yang diimport/export"
    )
    
    file_size = models.IntegerField(
        default=0,
        verbose_name="Ukuran File (bytes)",
        help_text="Ukuran file dalam bytes"
    )
    
    file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Path File",
        help_text="Lokasi penyimpanan file"
    )
    
    # Process Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Status",
        help_text="Status proses"
    )
    
    records_processed = models.IntegerField(
        default=0,
        verbose_name="Record Diproses",
        help_text="Jumlah total record yang diproses"
    )
    
    records_success = models.IntegerField(
        default=0,
        verbose_name="Record Sukses",
        help_text="Jumlah record yang berhasil"
    )
    
    records_failed = models.IntegerField(
        default=0,
        verbose_name="Record Gagal",
        help_text="Jumlah record yang gagal"
    )
    
    # Error & Warning
    error_message = models.TextField(
        blank=True,
        verbose_name="Pesan Error",
        help_text="Detail error jika terjadi kegagalan"
    )
    
    warning_message = models.TextField(
        blank=True,
        verbose_name="Pesan Warning",
        help_text="Peringatan selama proses"
    )
    
    # Audit Information
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True,
        verbose_name="IP Address",
        help_text="IP address pengguna"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Browser/device information"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Waktu Mulai",
        help_text="Waktu proses dimulai"
    )
    
    completed_at = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Waktu Selesai",
        help_text="Waktu proses selesai"
    )
    
    duration_seconds = models.FloatField(
        default=0,
        verbose_name="Durasi (detik)",
        help_text="Durasi proses dalam detik"
    )
    
    # Additional Notes
    notes = models.TextField(
        blank=True,
        verbose_name="Catatan",
        help_text="Catatan tambahan"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Log Import/Export"
        verbose_name_plural = "Log Import/Export"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['action', 'data_type']),
        ]
        
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        """String representation dari log"""
        return f"{self.get_action_display()} - {self.get_data_type_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def file_size_display(self):
        """
        Mengembalikan ukuran file dalam format human readable.
        
        Returns:
            str: Ukuran file (B, KB, MB, GB)
        """
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    @property
    def duration_display(self):
        """
        Mengembalikan durasi dalam format human readable.
        
        Returns:
            str: Durasi (detik, menit, jam)
        """
        if self.duration_seconds < 60:
            return f"{self.duration_seconds:.1f} detik"
        elif self.duration_seconds < 3600:
            minutes = self.duration_seconds / 60
            return f"{minutes:.1f} menit"
        else:
            hours = self.duration_seconds / 3600
            return f"{hours:.1f} jam"
    
    @property
    def success_rate(self):
        """
        Menghitung persentase keberhasilan.
        
        Returns:
            float: Persentase sukses (0-100)
        """
        if self.records_processed > 0:
            return (self.records_success / self.records_processed) * 100
        return 0
    
    @property
    def is_completed(self):
        """Cek apakah proses sudah selesai"""
        return self.status in ['success', 'failed', 'warning', 'cancelled']
    
    @property
    def filename_only(self):
        """Mengembalikan nama file tanpa path"""
        return os.path.basename(self.filename)
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def mark_as_completed(self, status='success'):
        """
        Menandai log sebagai selesai.
        
        Args:
            status (str): Status akhir (success/failed/warning)
        """
        self.status = status
        self.completed_at = timezone.now()
        if self.created_at:
            delta = self.completed_at - self.created_at
            self.duration_seconds = delta.total_seconds()
        self.save()
    
    def update_records(self, processed, success, failed):
        """
        Update jumlah record yang diproses.
        
        Args:
            processed (int): Total diproses
            success (int): Jumlah sukses
            failed (int): Jumlah gagal
        """
        self.records_processed = processed
        self.records_success = success
        self.records_failed = failed
        self.save()
    
    def add_error(self, error_message):
        """
        Menambahkan pesan error.
        
        Args:
            error_message (str): Pesan error
        """
        self.error_message = error_message
        self.status = 'failed'
        self.mark_as_completed('failed')
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def get_user_logs(cls, user, limit=50):
        """
        Mendapatkan log untuk user tertentu.
        
        Args:
            user: User object
            limit (int): Jumlah log maksimal
            
        Returns:
            QuerySet: Log user
        """
        return cls.objects.filter(user=user)[:limit]
    
    @classmethod
    def get_recent_logs(cls, limit=50):
        """
        Mendapatkan log terbaru.
        
        Args:
            limit (int): Jumlah log maksimal
            
        Returns:
            QuerySet: Log terbaru
        """
        return cls.objects.all()[:limit]
    
    @classmethod
    def get_success_rate_today(cls):
        """
        Menghitung success rate hari ini.
        
        Returns:
            dict: Statistik hari ini
        """
        today = timezone.now().date()
        logs = cls.objects.filter(created_at__date=today)
        
        total = logs.count()
        success = logs.filter(status='success').count()
        
        return {
            'total': total,
            'success': success,
            'failed': logs.filter(status='failed').count(),
            'rate': (success / total * 100) if total > 0 else 0
        }


# ==================================================
# SIGNALS (Optional - untuk auto cleanup)
# ==================================================

import os
from django.db.models.signals import pre_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=ImportExportLog)
def delete_associated_file(sender, instance, **kwargs):
    """
    Signal untuk menghapus file fisik ketika log dihapus.
    """
    if instance.file_path and os.path.exists(instance.file_path):
        try:
            os.remove(instance.file_path)
        except:
            pass  # Abaikan error jika file tidak bisa dihapus


# ==================================================
# END OF FILE: import_export.py
# ==================================================