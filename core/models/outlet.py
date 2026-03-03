# ==================================================
# FILE: core/models/outlet.py
# PATH: D:/Project Pyton/Mbayar/core/models/outlet.py
# FUNGSI: Model untuk Multi-Outlet/Cabang dengan konfigurasi lengkap
# FITUR:
#   - Manajemen cabang/toko dengan kode unik
#   - Mode stok (terpusat vs terpisah)
#   - Konfigurasi harga khusus per cabang
#   - Manajemen pegawai per cabang
#   - Tracking transaksi per cabang
# VERSION: 2.0.0
# UPDATE TERAKHIR: Penambahan konfigurasi pajak dan price multiplier
# ==================================================

"""
Model untuk mendukung multi-outlet/cabang dalam satu aplikasi.
Setiap cabang dapat memiliki konfigurasi stok, harga, dan pajak sendiri.
Pegawai dapat ditugaskan ke cabang tertentu dengan role masing-masing.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count
import logging

logger = logging.getLogger(__name__)


# ==================================================
# MODEL: Outlet
# ==================================================

class Outlet(models.Model):
    """
    Model untuk menyimpan data cabang/toko.
    
    Setiap outlet memiliki konfigurasi sendiri untuk:
    - Mode stok (terpusat atau terpisah)
    - Pengali harga (untuk harga khusus cabang)
    - Tarif pajak
    
    Relationships:
        created_by (ForeignKey): User yang membuat outlet
        pegawai_set (RelatedManager): Pegawai yang bekerja di outlet ini
    """
    
    # ==============================================
    # CHOICE FIELDS (Constants)
    # ==============================================
    
    STOK_CHOICES = [
        ('pusat', '🏢 Stok Terpusat (bersama semua cabang)'),
        ('cabang', '🏬 Stok Terpisah (masing-masing cabang)'),
    ]
    
    STATUS_CHOICES = [
        ('aktif', '✅ Aktif'),
        ('nonaktif', '❌ Nonaktif'),
        ('tutup', '🔒 Tutup Sementara'),
    ]
    
    TYPE_CHOICES = [
        ('utama', '🏢 Cabang Utama'),
        ('cabang', '🏬 Cabang Biasa'),
        ('gerai', '🏪 Gerai/Kios'),
    ]
    
    # ==============================================
    # FIELDS - Informasi Dasar
    # ==============================================
    
    code = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Kode Cabang",
        db_index=True,
        help_text="Contoh: JKT01, BDG01, SBY01 (unik)"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nama Cabang",
        help_text="Nama lengkap cabang/toko"
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='cabang',
        verbose_name="Tipe Cabang",
        help_text="Jenis cabang"
    )
    
    # ==============================================
    # FIELDS - Alamat & Kontak
    # ==============================================
    
    address = models.TextField(
        verbose_name="Alamat Lengkap",
        help_text="Alamat lengkap cabang"
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
    
    phone = models.CharField(
        max_length=20,
        verbose_name="No. Telepon",
        help_text="Nomor telepon yang bisa dihubungi"
    )
    
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="No. Telepon Cadangan",
        help_text="Nomor telepon alternatif"
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name="Email",
        help_text="Alamat email cabang"
    )
    
    # ==============================================
    # FIELDS - Status & Operasional
    # ==============================================
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aktif',
        verbose_name="Status",
        db_index=True
    )
    
    opened_date = models.DateField(
        default=timezone.now,
        verbose_name="Tanggal Buka",
        help_text="Tanggal operasional dimulai"
    )
    
    closed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Tanggal Tutup",
        help_text="Tanggal jika cabang ditutup"
    )
    
    business_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Jam Operasional",
        help_text="Format: {'senin': '08:00-22:00', ...}"
    )
    
    # ==============================================
    # FIELDS - Konfigurasi Stok
    # ==============================================
    
    stok_mode = models.CharField(
        max_length=10,
        choices=STOK_CHOICES,
        default='cabang',
        verbose_name="Mode Stok",
        help_text="Pusat = stok digabung, Cabang = stok masing-masing"
    )
    
    # ==============================================
    # FIELDS - Konfigurasi Harga
    # ==============================================
    
    use_special_pricing = models.BooleanField(
        default=False,
        verbose_name="Gunakan Harga Khusus",
        help_text="Jika ya, cabang ini bisa punya harga berbeda dari pusat"
    )
    
    price_multiplier = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=1.00,
        verbose_name="Pengali Harga",
        help_text="Contoh: 1.20 = harga 20% lebih mahal dari pusat"
    )
    
    price_rounding = models.IntegerField(
        default=0,
        verbose_name="Pembulatan Harga",
        help_text="0 = tidak dibulatkan, 50 = ke 50 terdekat, 100 = ke 100 terdekat"
    )
    
    # ==============================================
    # FIELDS - Konfigurasi Pajak
    # ==============================================
    
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=11.00,
        verbose_name="Tarif Pajak (%)",
        help_text="Contoh: 11 untuk PPN 11%"
    )
    
    tax_inclusive = models.BooleanField(
        default=True,
        verbose_name="Harga Termasuk Pajak",
        help_text="Centang jika harga sudah termasuk pajak"
    )
    
    service_charge = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Service Charge (%)",
        help_text="Biaya layanan dalam persen"
    )
    
    # ==============================================
    # FIELDS - Konfigurasi Lainnya
    #==============================================
    
    prefix_transaksi = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Prefix No. Transaksi",
        help_text="Contoh: INV, REC"
    )
    
    printer_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Printer",
        help_text="IP Address printer thermal"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Catatan",
        help_text="Catatan internal tentang cabang"
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
        related_name='outlets_created',
        verbose_name="Dibuat Oleh"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Cabang/Outlet"
        verbose_name_plural = "Cabang/Outlet"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['city']),
            models.Index(fields=['stok_mode']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        return f"[{self.code}] {self.name}"
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        Override save untuk validasi dan uppercase kode.
        """
        # Uppercase kode
        if self.code:
            self.code = self.code.upper().strip()
        
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
        if self.closed_date and self.closed_date < self.opened_date:
            raise ValidationError({
                'closed_date': 'Tanggal tutup tidak boleh sebelum tanggal buka'
            })
        
        if self.price_multiplier <= 0:
            raise ValidationError({
                'price_multiplier': 'Pengali harga harus lebih dari 0'
            })
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def total_pegawai(self):
        """Hitung jumlah pegawai aktif di cabang ini"""
        return self.pegawai.filter(is_active=True).count()
    
    @property
    def total_transaksi_hari_ini(self):
        """Hitung jumlah transaksi hari ini"""
        from .order import Order
        today = timezone.now().date()
        return Order.objects.filter(
            outlet=self,
            created_at__date=today
        ).count()
    
    @property
    def total_pendapatan_hari_ini(self):
        """Hitung total pendapatan hari ini"""
        from .order import Order
        today = timezone.now().date()
        result = Order.objects.filter(
            outlet=self,
            created_at__date=today,
            status='selesai'
        ).aggregate(total=Sum('total_amount'))
        return result['total'] or 0
    
    @property
    def is_operational(self):
        """Cek apakah cabang sedang beroperasi"""
        return self.status == 'aktif'
    
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
    def business_hours_display(self):
        """Jam operasional untuk display"""
        if not self.business_hours:
            return "Senin-Minggu: 08:00-22:00"
        
        # Default display
        return ", ".join([f"{day}: {hours}" for day, hours in self.business_hours.items()])
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def apply_price_multiplier(self, base_price):
        """
        Apply pengali harga ke harga dasar.
        
        Args:
            base_price (Decimal): Harga dasar
            
        Returns:
            Decimal: Harga setelah multiplier
        """
        if not self.use_special_pricing:
            return base_price
        
        price = base_price * self.price_multiplier
        
        # Pembulatan
        if self.price_rounding > 0:
            price = round(price / self.price_rounding) * self.price_rounding
        
        return price
    
    def get_pegawai_by_role(self, role):
        """
        Mendapatkan pegawai berdasarkan role.
        
        Args:
            role (str): Role pegawai
            
        Returns:
            QuerySet: Pegawai dengan role tertentu
        """
        return self.pegawai.filter(role=role, is_active=True)
    
    def get_statistics(self):
        """
        Mendapatkan statistik cabang.
        
        Returns:
            dict: Dictionary berisi statistik
        """
        from .order import Order
        from django.db.models import Count, Sum
        
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        
        # Orders hari ini
        orders_today = Order.objects.filter(
            outlet=self,
            created_at__date=today
        )
        
        # Orders bulan ini
        orders_month = Order.objects.filter(
            outlet=self,
            created_at__date__gte=first_of_month
        )
        
        return {
            'pegawai_aktif': self.total_pegawai,
            'transaksi_hari_ini': orders_today.count(),
            'pendapatan_hari_ini': orders_today.aggregate(total=Sum('total_amount'))['total'] or 0,
            'transaksi_bulan_ini': orders_month.count(),
            'pendapatan_bulan_ini': orders_month.aggregate(total=Sum('total_amount'))['total'] or 0,
            'rata_rata_transaksi': orders_month.aggregate(avg=Sum('total_amount')/Count('id'))['avg'] or 0,
        }
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def get_active_outlets(cls):
        """Mendapatkan semua outlet aktif"""
        return cls.objects.filter(status='aktif')
    
    @classmethod
    def get_by_city(cls, city):
        """Mendapatkan outlet berdasarkan kota"""
        return cls.objects.filter(city__iexact=city)
    
    @classmethod
    def get_statistics_all(cls):
        """
        Mendapatkan statistik semua cabang.
        
        Returns:
            dict: Statistik global
        """
        outlets = cls.objects.all()
        return {
            'total_outlet': outlets.count(),
            'aktif': outlets.filter(status='aktif').count(),
            'nonaktif': outlets.filter(status='nonaktif').count(),
            'total_pegawai': sum(o.total_pegawai for o in outlets),
            'total_transaksi_hari_ini': sum(o.total_transaksi_hari_ini for o in outlets),
        }


# ==================================================
# MODEL: Pegawai
# ==================================================

class Pegawai(models.Model):
    """
    Model untuk pegawai yang bekerja di cabang tertentu.
    
    Setiap pegawai terikat dengan satu user dan satu outlet.
    Memiliki role dan NIP unik.
    
    Relationships:
        user (OneToOneField): User account untuk login
        outlet (ForeignKey): Outlet tempat bekerja
    """
    
    # ==============================================
    # CHOICE FIELDS
    # ==============================================
    
    ROLE_CHOICES = [
        ('kasir', '💳 Kasir'),
        ('supervisor', '👔 Supervisor'),
        ('manajer', '👨‍💼 Manajer Cabang'),
        ('gudang', '📦 Staff Gudang'),
        ('dapur', '👨‍🍳 Staff Dapur'),
        ('admin', '⚙️ Admin'),
    ]
    
    STATUS_CHOICES = [
        ('aktif', '✅ Aktif'),
        ('cuti', '🏖️ Cuti'),
        ('keluar', '🚫 Keluar'),
        ('nonaktif', '❌ Nonaktif'),
    ]
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='pegawai',
        verbose_name="User",
        help_text="User account untuk login"
    )
    
    outlet = models.ForeignKey(
        Outlet,
        on_delete=models.CASCADE,
        related_name='pegawai',
        verbose_name="Cabang",
        help_text="Cabang tempat pegawai bekerja"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='kasir',
        verbose_name="Jabatan",
        db_index=True
    )
    
    nip = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="NIP",
        help_text="Nomor Induk Pegawai (unik)"
    )
    
    # Informasi Personal
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="No. Telepon",
        help_text="Nomor telepon pribadi"
    )
    
    address = models.TextField(
        blank=True,
        verbose_name="Alamat",
        help_text="Alamat tempat tinggal"
    )
    
    # Employment Info
    join_date = models.DateField(
        default=timezone.now,
        verbose_name="Tanggal Bergabung"
    )
    
    resign_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Tanggal Keluar"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aktif',
        verbose_name="Status"
    )
    
    # Additional Info
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Kontak Darurat",
        help_text="Nama dan nomor kontak darurat"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Catatan",
        help_text="Catatan internal tentang pegawai"
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
        verbose_name = "Pegawai"
        verbose_name_plural = "Pegawai"
        ordering = ['outlet', 'role', 'user__username']
        unique_together = ['outlet', 'nip']  # NIP unik per outlet
        indexes = [
            models.Index(fields=['outlet']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['nip']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.outlet.name} ({self.get_role_display()})"
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """Override save untuk validasi"""
        # Uppercase NIP
        if self.nip:
            self.nip = self.nip.upper().strip()
        
        # Validasi
        self.clean()
        
        # Update user profile role jika perlu
        if hasattr(self.user, 'profile'):
            self.user.profile.role = self.role
            self.user.profile.save()
        
        super().save(*args, **kwargs)
    
    # ==============================================
    # VALIDATION
    # ==============================================
    
    def clean(self):
        """Validasi data pegawai"""
        if self.resign_date and self.resign_date < self.join_date:
            raise ValidationError({
                'resign_date': 'Tanggal keluar tidak boleh sebelum tanggal bergabung'
            })
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def name(self):
        """Nama lengkap pegawai"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def is_active_employee(self):
        """Cek apakah pegawai aktif"""
        return self.status == 'aktif'
    
    @property
    def display_role(self):
        """Role untuk display"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    @property
    def masa_kerja(self):
        """Hitung masa kerja dalam hari"""
        if self.resign_date:
            end = self.resign_date
        else:
            end = timezone.now().date()
        return (end - self.join_date).days
    
    @property
    def masa_kerja_display(self):
        """Masa kerja dalam format tahun/bulan"""
        days = self.masa_kerja
        years = days // 365
        months = (days % 365) // 30
        
        if years > 0:
            return f"{years} tahun {months} bulan"
        elif months > 0:
            return f"{months} bulan"
        else:
            return f"{days} hari"
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def has_permission(self, permission):
        """
        Cek apakah pegawai memiliki permission tertentu.
        
        Args:
            permission (str): Nama permission
            
        Returns:
            bool: True jika memiliki permission
        """
        # Admin punya semua akses
        if self.role == 'admin':
            return True
        
        # Mapping role ke permissions
        role_permissions = {
            'kasir': ['order.create', 'order.view', 'payment.process'],
            'supervisor': ['order.*', 'report.view', 'employee.view'],
            'manajer': ['*'],
            'gudang': ['stock.*'],
            'dapur': ['order.view', 'kitchen.view'],
        }
        
        perms = role_permissions.get(self.role, [])
        return permission in perms or '*' in perms
    
    def get_transaction_stats(self, days=30):
        """
        Mendapatkan statistik transaksi pegawai.
        
        Args:
            days (int): Jumlah hari ke belakang
            
        Returns:
            dict: Statistik transaksi
        """
        from .order import Order
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        orders = Order.objects.filter(
            cashier=self.user,
            created_at__gte=start_date
        )
        
        return {
            'total_transaksi': orders.count(),
            'total_nominal': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'rata_rata': orders.aggregate(avg=Sum('total_amount')/Count('id'))['avg'] or 0,
        }
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def get_by_outlet(cls, outlet):
        """Mendapatkan semua pegawai di outlet tertentu"""
        return cls.objects.filter(outlet=outlet)
    
    @classmethod
    def get_by_role(cls, role):
        """Mendapatkan pegawai dengan role tertentu"""
        return cls.objects.filter(role=role, status='aktif')
    
    @classmethod
    def get_kasir_aktif(cls):
        """Mendapatkan kasir yang aktif"""
        return cls.objects.filter(role='kasir', status='aktif')


# ==================================================
# SIGNALS (Auto create profile)
# ==================================================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Pegawai)
def sync_user_profile(sender, instance, created, **kwargs):
    """
    Sync role ke user profile saat pegawai disimpan.
    """
    if hasattr(instance.user, 'profile'):
        profile = instance.user.profile
        profile.role = instance.role
        profile.outlet = instance.outlet
        profile.save()
        logger.info(f"Synced profile for user {instance.user.username}")


# ==================================================
# END OF FILE: outlet.py
# ==================================================