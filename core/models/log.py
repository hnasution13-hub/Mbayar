# ==================================================
# FILE: core/models/log.py
# PATH: D:/Project Pyton/Mbayar/core/models/log.py
# FUNGSI: Model untuk mencatat semua aktivitas user (Audit Trail)
# FITUR:
#   - Tracking semua aksi user (CRUD, Login, Logout, dll)
#   - Menyimpan detail perubahan dalam format JSON
#   - Informasi request (IP, User Agent, Method, Path)
#   - Audit trail lengkap untuk compliance
# VERSION: 2.0.0
# UPDATE TERAKHIR: Penambahan fields untuk request info dan changes JSON
# ==================================================

"""
Model untuk mencatat semua aktivitas user dalam sistem.
Berfungsi sebagai audit trail untuk monitoring, security, dan troubleshooting.
Menyimpan detail lengkap termasuk perubahan data sebelum/sesudah.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)


# ==================================================
# MODEL: ActivityLog
# ==================================================

class ActivityLog(models.Model):
    """
    Model untuk mencatat semua aktivitas user di sistem.
    
    Menyimpan informasi detail setiap aksi user termasuk:
    - User yang melakukan aksi (dengan backup username)
    - Tipe aksi dan model yang terlibat
    - Object yang diubah (ID dan representasi string)
    - Detail perubahan dalam format JSON
    - Informasi request (IP, User Agent, Method, Path)
    
    Relationships:
        user (ForeignKey): User yang melakukan aksi (nullable jika user dihapus)
    """
    
    # ==============================================
    # CHOICE FIELDS (Constants)
    # ==============================================
    
    ACTION_TYPES = [
        # Authentication
        ('login', '🔐 Login'),
        ('logout', '🚪 Logout'),
        ('login_failed', '❌ Login Gagal'),
        ('password_change', '🔑 Ubah Password'),
        ('password_reset', '🔄 Reset Password'),
        
        # CRUD Operations
        ('create', '➕ Tambah Data'),
        ('update', '✏️ Ubah Data'),
        ('delete', '🗑️ Hapus Data'),
        ('view', '👁️ Lihat Data'),
        
        # Data Operations
        ('export', '📤 Export Data'),
        ('import', '📥 Import Data'),
        ('backup', '💾 Backup Database'),
        ('restore', '↩️ Restore Database'),
        
        # Business Operations
        ('payment', '💰 Pembayaran'),
        ('refund', '↩️ Refund'),
        ('cancel', '❌ Pembatalan'),
        ('print', '🖨️ Print/Cetak'),
        
        # Other
        ('other', '📌 Lainnya'),
    ]
    
    MODEL_TYPES = [
        # User & Auth
        ('auth.user', '👤 User'),
        ('auth.group', '👥 Group'),
        ('core.profile', '👤 Profile'),
        
        # Master Data
        ('core.outlet', '🏢 Outlet'),
        ('core.pegawai', '👨‍💼 Pegawai'),
        ('core.supplier', '🏭 Supplier'),
        ('core.kodebarang', '📦 Kode Barang'),
        
        # Menu
        ('core.menucategory', '📋 Kategori Menu'),
        ('core.menu', '🍽️ Menu'),
        ('core.menuingredient', '🥘 Bahan Menu'),
        ('core.menumodifier', '⚙️ Modifier Menu'),
        ('core.modifieroption', '🔘 Opsi Modifier'),
        
        # Stock
        ('core.stockitem', '📦 Stok Barang'),
        ('core.stockpurchase', '🛒 Pembelian Stok'),
        ('core.stockpurchaseitem', '📋 Item Pembelian'),
        
        # Order/Transaction
        ('core.order', '🧾 Transaksi'),
        ('core.orderitem', '📋 Item Transaksi'),
        ('core.orderitemmodifier', '🔧 Modifier Item'),
        
        # Logs
        ('core.importexportlog', '📊 Log Import/Export'),
        ('core.activitylog', '📋 Log Aktivitas'),
        
        # Other
        ('other', '📌 Lainnya'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'ℹ️ Info'),
        ('warning', '⚠️ Warning'),
        ('error', '❌ Error'),
        ('critical', '🔥 Critical'),
    ]
    
    # ==============================================
    # FIELDS
    # ==============================================
    
    # User Information (dengan backup)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="User",
        help_text="User yang melakukan aksi (null jika user sudah dihapus)",
        related_name='activity_logs'
    )
    
    username = models.CharField(
        max_length=150, 
        blank=True,
        verbose_name="Username",
        help_text="Username yang disimpan untuk berjaga-jaga jika user dihapus"
    )
    
    # Action Information
    action = models.CharField(
        max_length=20, 
        choices=ACTION_TYPES,
        verbose_name="Aksi",
        help_text="Jenis aksi yang dilakukan",
        db_index=True
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='info',
        verbose_name="Severity",
        help_text="Tingkat kepentingan log"
    )
    
    # Model Information
    model_name = models.CharField(
        max_length=50, 
        choices=MODEL_TYPES,
        default='other',
        verbose_name="Model",
        help_text="Model yang terlibat dalam aksi",
        db_index=True
    )
    
    object_id = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="ID Object",
        help_text="Primary key dari object yang diubah"
    )
    
    object_repr = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="Representasi Object",
        help_text="String representation dari object (contoh: 'Gula Pasir')"
    )
    
    # Detail Information
    details = models.TextField(
        blank=True,
        null=True,
        verbose_name="Detail",
        help_text="Deskripsi detail tentang aksi"
    )
    
    changes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Perubahan",
        help_text="JSON format untuk menyimpan perubahan sebelum/sesudah (before/after)"
    )
    
    # Request Information
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name="IP Address",
        help_text="IP address client"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Browser/device information"
    )
    
    request_method = models.CharField(
        max_length=10, 
        blank=True,
        verbose_name="HTTP Method",
        help_text="GET, POST, PUT, DELETE, dll"
    )
    
    request_path = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="URL Path",
        help_text="Path dari request"
    )
    
    request_query = models.TextField(
        blank=True,
        verbose_name="Query String",
        help_text="Query parameters dari request"
    )
    
    # Additional Information
    duration_ms = models.IntegerField(
        default=0,
        verbose_name="Durasi (ms)",
        help_text="Durasi eksekusi dalam milidetik"
    )
    
    session_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Session Key",
        help_text="Session identifier"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Waktu",
        help_text="Waktu aksi terjadi",
        db_index=True
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Log Aktivitas"
        verbose_name_plural = "Log Aktivitas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['username', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['model_name', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]
        
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        """
        String representation dengan format:
        [WAKTU] USERNAME - AKSI - OBJECT
        """
        waktu = self.created_at.strftime('%d/%m/%Y %H:%M')
        user_display = self.username or 'System'
        action_display = self.get_action_display().replace('🔐', '').replace('🚪', '').strip()
        return f"[{waktu}] {user_display} - {action_display} - {self.object_repr or '-'}"
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        Override save method untuk menyimpan username jika user ada.
        """
        # Simpan username dari user jika ada dan belum diisi
        if self.user and not self.username:
            self.username = self.user.username
        
        # Validasi JSON changes jika ada
        if self.changes:
            try:
                json.loads(self.changes)
            except json.JSONDecodeError:
                self.changes = json.dumps({'error': 'Invalid JSON', 'original': self.changes})
        
        super().save(*args, **kwargs)
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def changes_dict(self):
        """
        Mengembalikan changes sebagai dictionary.
        
        Returns:
            dict: Parsed JSON changes, {} jika error
        """
        if not self.changes:
            return {}
        
        try:
            return json.loads(self.changes)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing changes JSON: {e}")
            return {'error': 'Invalid JSON', 'raw': self.changes[:100]}
    
    @property
    def changes_pretty(self):
        """
        Mengembalikan changes dalam format JSON yang rapi.
        
        Returns:
            str: Formatted JSON string
        """
        changes = self.changes_dict
        if changes:
            return json.dumps(changes, indent=2, ensure_ascii=False)
        return "{}"
    
    @property
    def waktu_formatted(self):
        """
        Format waktu yang lebih detail.
        
        Returns:
            str: Format 'dd/mm/yyyy HH:MM:SS'
        """
        return self.created_at.strftime('%d/%m/%Y %H:%M:%S')
    
    @property
    def waktu_relative(self):
        """
        Waktu dalam format relatif (misal: '5 menit yang lalu').
        
        Returns:
            str: Relative time string
        """
        delta = timezone.now() - self.created_at
        
        if delta.days > 0:
            return f"{delta.days} hari yang lalu"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} jam yang lalu"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} menit yang lalu"
        else:
            return f"{delta.seconds} detik yang lalu"
    
    @property
    def has_changes(self):
        """Cek apakah ada perubahan data"""
        return bool(self.changes and self.changes != '{}')
    
    @property
    def is_error(self):
        """Cek apakah ini log error"""
        return self.severity in ['error', 'critical']
    
    @property
    def user_display(self):
        """Nama user untuk display"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.username or 'System'
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def set_changes(self, before, after):
        """
        Set perubahan dalam format JSON.
        
        Args:
            before (dict): Data sebelum perubahan
            after (dict): Data setelah perubahan
        """
        changes_data = {
            'before': before,
            'after': after,
            'timestamp': timezone.now().isoformat()
        }
        self.changes = json.dumps(changes_data, cls=DjangoJSONEncoder)
    
    def add_detail(self, key, value):
        """
        Menambahkan detail ke existing details.
        
        Args:
            key (str): Key detail
            value (any): Value detail
        """
        try:
            current_details = json.loads(self.details) if self.details else {}
        except:
            current_details = {}
        
        current_details[key] = value
        self.details = json.dumps(current_details, cls=DjangoJSONEncoder)
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def log_activity(cls, user, action, model_name='other', object_id=None, 
                     object_repr='', details='', changes='', request=None,
                     severity='info'):
        """
        Class method untuk mencatat aktivitas dengan mudah.
        
        Args:
            user: User object
            action (str): Action type
            model_name (str): Model name
            object_id (int): Object ID
            object_repr (str): Object representation
            details (str): Detail text
            changes (str/dict): JSON changes atau dict
            request: HttpRequest object (untuk extract IP, user agent, dll)
            severity (str): Severity level
            
        Returns:
            ActivityLog: Created log instance
        """
        # Convert changes to JSON string if dict
        if isinstance(changes, dict):
            changes = json.dumps(changes, cls=DjangoJSONEncoder)
        
        # Extract request info
        ip_address = None
        user_agent = ''
        request_method = ''
        request_path = ''
        request_query = ''
        session_key = ''
        
        if request:
            # Get IP with proxy support
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            request_method = request.method
            request_path = request.path
            request_query = request.META.get('QUERY_STRING', '')
            session_key = request.session.session_key or ''
        
        # Create log
        log = cls.objects.create(
            user=user,
            username=user.username if user else '',
            action=action,
            severity=severity,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr[:255],
            details=details,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent[:500],
            request_method=request_method,
            request_path=request_path[:255],
            request_query=request_query,
            session_key=session_key
        )
        
        return log
    
    @classmethod
    def get_user_activity(cls, user, limit=50):
        """
        Mendapatkan aktivitas untuk user tertentu.
        
        Args:
            user: User object atau username
            limit (int): Jumlah log maksimal
            
        Returns:
            QuerySet: User activity logs
        """
        if isinstance(user, User):
            return cls.objects.filter(user=user)[:limit]
        else:
            return cls.objects.filter(username=user)[:limit]
    
    @classmethod
    def get_recent_activity(cls, limit=100):
        """
        Mendapatkan aktivitas terbaru.
        
        Args:
            limit (int): Jumlah log maksimal
            
        Returns:
            QuerySet: Recent activity logs
        """
        return cls.objects.all()[:limit]
    
    @classmethod
    def get_activity_by_date(cls, date):
        """
        Mendapatkan aktivitas berdasarkan tanggal.
        
        Args:
            date: Date object
            
        Returns:
            QuerySet: Activity logs on that date
        """
        return cls.objects.filter(created_at__date=date)
    
    @classmethod
    def get_activity_summary(cls, days=7):
        """
        Mendapatkan summary aktivitas untuk periode tertentu.
        
        Args:
            days (int): Jumlah hari ke belakang
            
        Returns:
            dict: Summary statistics
        """
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        logs = cls.objects.filter(created_at__gte=start_date)
        
        return {
            'total': logs.count(),
            'by_action': logs.values('action').annotate(count=models.Count('id')),
            'by_user': logs.values('username').annotate(count=models.Count('id'))[:10],
            'by_model': logs.values('model_name').annotate(count=models.Count('id')),
            'errors': logs.filter(severity__in=['error', 'critical']).count(),
        }
    
    @classmethod
    def cleanup_old_logs(cls, days=90):
        """
        Menghapus log yang lebih tua dari hari tertentu.
        
        Args:
            days (int): Umur maksimal log dalam hari
            
        Returns:
            int: Jumlah log yang dihapus
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = cls.objects.filter(created_at__lt=cutoff_date).delete()
        
        logger.info(f"Cleaned up {deleted_count} old activity logs")
        return deleted_count


# ==================================================
# SIGNALS (Auto logging)
# ==================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    """
    Signal untuk mencatat perubahan user.
    """
    action = 'create' if created else 'update'
    ActivityLog.log_activity(
        user=instance,
        action=action,
        model_name='auth.user',
        object_id=instance.id,
        object_repr=str(instance),
        details=f"User {'created' if created else 'updated'}: {instance.username}"
    )

@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    """
    Signal untuk mencatat penghapusan user.
    """
    ActivityLog.log_activity(
        user=None,
        action='delete',
        model_name='auth.user',
        object_id=instance.id,
        object_repr=str(instance),
        details=f"User deleted: {instance.username}"
    )


# ==================================================
# MIDDLEWARE COMPONENT (untuk auto logging request)
# ==================================================

class ActivityLogMiddleware:
    """
    Middleware untuk auto logging request.
    Tambahkan ke MIDDLEWARE di settings.py
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request before view
        # Bisa log request di sini jika perlu
        
        response = self.get_response(request)
        
        # Process response after view
        return response


# ==================================================
# END OF FILE: log.py
# ==================================================