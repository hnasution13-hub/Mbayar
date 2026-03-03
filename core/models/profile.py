# ==================================================
# FILE: core/models/profile.py
# PATH: D:/Project Pyton/Mbayar/core/models/profile.py
# FUNGSI: Model untuk profil tambahan user (extends User)
# FITUR:
#   - One-to-one relationship dengan User model bawaan Django
#   - Role-based access control (user, supervisor, administrator)
#   - Informasi kontak dan foto profil
#   - Relasi dengan Outlet (cabang tempat user bekerja)
#   - Auto-create profile via signal saat user baru dibuat
# VERSION: 2.0.0
# UPDATE TERAKHIR: Penambahan relasi ke Outlet untuk multi-cabang
# ==================================================

"""
Model Profile untuk menyimpan data tambahan user yang tidak ada di User bawaan Django.
Berfungsi sebagai extension dari User model dengan field tambahan seperti role,
nomor telepon, foto profil, dan cabang tempat user bekerja.

Signals:
    - create_user_profile: Auto-create profile saat User baru dibuat
    - save_user_profile: Auto-save profile saat User disimpan
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import os
import logging

logger = logging.getLogger(__name__)


# ==================================================
# MODEL: Profile
# ==================================================

class Profile(models.Model):
    """
    Model untuk menyimpan data tambahan user.
    
    Memperluas model User bawaan Django dengan field-field berikut:
    - role: Level akses user (user/supervisor/administrator)
    - phone: Nomor telepon kontak
    - photo: Foto profil user
    - bio: Biografi singkat
    - outlet: Cabang tempat user bekerja (untuk multi-cabang)
    
    Relationships:
        user (OneToOneField): User terkait (reverse: user.profile)
        outlet (ForeignKey): Outlet tempat user bekerja (nullable)
    """
    
    # ==============================================
    # CHOICE FIELDS (Constants)
    # ==============================================
    
    ROLE_CHOICES = [
        ('user', '👤 User Biasa'),
        ('kasir', '💰 Kasir'),
        ('supervisor', '👔 Supervisor'),
        ('administrator', '⚙️ Administrator'),
        ('owner', '👑 Owner'),
    ]
    
    LANGUAGE_CHOICES = [
        ('id', 'Bahasa Indonesia'),
        ('en', 'English'),
    ]
    
    THEME_CHOICES = [
        ('light', '☀️ Light'),
        ('dark', '🌙 Dark'),
        ('auto', '🔄 Auto'),
    ]
    
    # ==============================================
    # FIELDS - Informasi Dasar
    # ==============================================
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="User",
        help_text="User account terkait"
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='user',
        verbose_name="Role / Jabatan",
        db_index=True,
        help_text="Level akses user dalam sistem"
    )
    
    # ==============================================
    # FIELDS - Informasi Kontak
    # ==============================================
    
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="No. Telepon",
        help_text="Nomor telepon yang bisa dihubungi"
    )
    
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="No. Telepon Alternatif",
        help_text="Nomor telepon cadangan"
    )
    
    address = models.TextField(
        blank=True,
        verbose_name="Alamat",
        help_text="Alamat lengkap"
    )
    
    # ==============================================
    # FIELDS - Foto & Bio
    # ==============================================
    
    photo = models.ImageField(
        upload_to='profiles/', 
        blank=True, 
        null=True, 
        verbose_name="Foto Profil",
        help_text="Upload foto profil (format: JPG, PNG, maks: 2MB)"
    )
    
    bio = models.TextField(
        blank=True, 
        verbose_name="Bio",
        help_text="Biografi singkat atau deskripsi diri"
    )
    
    # ==============================================
    # FIELDS - Relasi ke Outlet (UNTUK MULTI-CABANG)
    # ==============================================
    
    outlet = models.ForeignKey(
        'Outlet',  # String reference untuk hindari circular import
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Cabang",
        help_text="Pilih cabang tempat user bekerja",
        related_name='user_profiles'
    )
    
    # ==============================================
    # FIELDS - Preferensi User
    # ==============================================
    
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='id',
        verbose_name="Bahasa",
        help_text="Preferensi bahasa"
    )
    
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        verbose_name="Tema",
        help_text="Preferensi tema tampilan"
    )
    
    notification_email = models.BooleanField(
        default=True,
        verbose_name="Notifikasi Email",
        help_text="Terima notifikasi via email"
    )
    
    notification_whatsapp = models.BooleanField(
        default=False,
        verbose_name="Notifikasi WhatsApp",
        help_text="Terima notifikasi via WhatsApp"
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
    
    last_active = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Terakhir Aktif",
        help_text="Timestamp terakhir user melakukan aktivitas"
    )
    
    # ==============================================
    # META CLASS
    # ==============================================
    
    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profil"
        ordering = ['user__username']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
            models.Index(fields=['outlet']),
        ]
    
    # ==============================================
    # STRING REPRESENTATION
    # ==============================================
    
    def __str__(self):
        """
        String representation dengan format:
        username - role (outlet)
        """
        outlet_info = f" - {self.outlet.name}" if self.outlet else ""
        role_display = self.get_role_display().replace('👤', '').replace('💰', '').replace('👔', '').replace('⚙️', '').replace('👑', '').strip()
        return f"{self.user.username} - {role_display}{outlet_info}"
    
    # ==============================================
    # SAVE METHOD
    # ==============================================
    
    def save(self, *args, **kwargs):
        """
        Override save method untuk validasi dan cleanup.
        """
        # Validasi data
        self.clean()
        
        # Hapus foto lama jika diganti
        if self.pk:
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.photo and old_profile.photo != self.photo:
                    if os.path.isfile(old_profile.photo.path):
                        os.remove(old_profile.photo.path)
            except Profile.DoesNotExist:
                pass
            except Exception as e:
                logger.warning(f"Error deleting old photo: {e}")
        
        super().save(*args, **kwargs)
    
    # ==============================================
    # VALIDATION
    # ==============================================
    
    def clean(self):
        """
        Validasi data sebelum disimpan.
        """
        # Validasi role dan outlet
        if self.role == 'administrator' and not self.outlet:
            # Admin boleh tanpa outlet (super admin)
            pass
        elif self.role in ['kasir', 'supervisor'] and not self.outlet:
            raise ValidationError({
                'outlet': f'User dengan role {self.get_role_display()} harus memiliki cabang'
            })
    
    # ==============================================
    # PROPERTIES
    # ==============================================
    
    @property
    def full_name(self):
        """Nama lengkap user"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def initials(self):
        """Inisial user untuk avatar"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        elif self.user.first_name:
            return self.user.first_name[0].upper()
        else:
            return self.user.username[0].upper()
    
    @property
    def avatar_color(self):
        """Warna avatar berdasarkan username (konsisten)"""
        import hashlib
        hash_object = hashlib.md5(self.user.username.encode())
        hex_color = hash_object.hexdigest()[:6]
        return f"#{hex_color}"
    
    @property
    def is_admin(self):
        """Cek apakah user adalah administrator"""
        return self.role == 'administrator'
    
    @property
    def is_supervisor(self):
        """Cek apakah user adalah supervisor"""
        return self.role == 'supervisor'
    
    @property
    def is_kasir(self):
        """Cek apakah user adalah kasir"""
        return self.role == 'kasir'
    
    @property
    def outlet_name(self):
        """Nama outlet tempat user bekerja"""
        return self.outlet.name if self.outlet else '-'
    
    @property
    def outlet_code(self):
        """Kode outlet tempat user bekerja"""
        return self.outlet.code if self.outlet else '-'
    
    # ==============================================
    # METHODS
    # ==============================================
    
    def has_permission(self, permission):
        """
        Cek apakah user memiliki permission tertentu berdasarkan role.
        
        Args:
            permission (str): Nama permission (contoh: 'menu.edit', 'order.view')
            
        Returns:
            bool: True jika memiliki akses
        """
        # Owner punya semua akses
        if self.role == 'owner':
            return True
        
        # Administrator punya hampir semua akses
        if self.role == 'administrator':
            restricted = ['owner.access', 'system.delete']
            return permission not in restricted
        
        # Mapping permission per role
        role_permissions = {
            'supervisor': [
                'order.view', 'order.edit', 'order.cancel',
                'menu.view', 'menu.edit',
                'stock.view', 'stock.adjust',
                'report.view', 'employee.view'
            ],
            'kasir': [
                'order.create', 'order.view', 'order.payment',
                'customer.view', 'discount.apply'
            ],
            'user': [
                'profile.view', 'profile.edit'
            ]
        }
        
        return permission in role_permissions.get(self.role, [])
    
    def update_last_active(self):
        """Update timestamp terakhir aktif"""
        from django.utils import timezone
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])
    
    def get_role_display_clean(self):
        """Role display tanpa emoji"""
        role_display = self.get_role_display()
        # Hapus emoji
        import re
        return re.sub(r'[^\w\s]', '', role_display).strip()
    
    def to_dict(self):
        """
        Mengembalikan data profile sebagai dictionary.
        
        Returns:
            dict: Data profile
        """
        return {
            'id': self.id,
            'user_id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'full_name': self.full_name,
            'role': self.role,
            'role_display': self.get_role_display_clean(),
            'phone': self.phone,
            'outlet_id': self.outlet.id if self.outlet else None,
            'outlet_name': self.outlet_name,
            'outlet_code': self.outlet_code,
            'photo_url': self.photo.url if self.photo else None,
            'language': self.language,
            'theme': self.theme,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
        }
    
    # ==============================================
    # CLASS METHODS
    # ==============================================
    
    @classmethod
    def get_by_role(cls, role):
        """Mendapatkan semua profile dengan role tertentu"""
        return cls.objects.filter(role=role)
    
    @classmethod
    def get_by_outlet(cls, outlet):
        """Mendapatkan semua profile di outlet tertentu"""
        return cls.objects.filter(outlet=outlet)
    
    @classmethod
    def get_kasir_aktif(cls, outlet=None):
        """Mendapatkan kasir aktif"""
        queryset = cls.objects.filter(role='kasir')
        if outlet:
            queryset = queryset.filter(outlet=outlet)
        return queryset
    
    @classmethod
    def search(cls, query):
        """Mencari profile berdasarkan username, email, atau nama"""
        return cls.objects.filter(
            models.Q(user__username__icontains=query) |
            models.Q(user__email__icontains=query) |
            models.Q(user__first_name__icontains=query) |
            models.Q(user__last_name__icontains=query) |
            models.Q(phone__icontains=query)
        )


# ==================================================
# SIGNALS: Auto-create & Auto-save Profile
# ==================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal untuk membuat Profile secara otomatis saat User baru dibuat.
    
    Args:
        sender: Model class (User)
        instance: Instance User yang disimpan
        created (bool): True jika record baru dibuat
        **kwargs: Keyword arguments tambahan
    """
    if created:
        Profile.objects.create(user=instance)
        logger.info(f"Profile created for user: {instance.username}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal untuk menyimpan Profile saat User disimpan.
    
    Args:
        sender: Model class (User)
        instance: Instance User yang disimpan
        **kwargs: Keyword arguments tambahan
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Jika profile tidak ada, buat baru
        Profile.objects.create(user=instance)
        logger.info(f"Profile created (missing) for user: {instance.username}")


# ==================================================
# SIGNALS: Update related data saat role berubah
# ==================================================

#@receiver(post_save, sender=Profile)
#def on_profile_change(sender, instance, created, **kwargs):
#    """
#    Signal untuk handle perubahan profile.
    
#    Args:
#        sender: Model class (Profile)
#        instance: Instance Profile yang disimpan
#        created (bool): True jika record baru dibuat
#        **kwargs: Keyword arguments tambahan
#    """
    # Update user groups berdasarkan role
#    if not created and instance.tracker.has_changed('role'):
#        old_role = instance.tracker.previous('role')
#        new_role = instance.role
        
#        logger.info(f"Role changed for user {instance.user.username}: {old_role} -> {new_role}")
#        
#        # TODO: Update user groups/permissions di sini jika diperlukan
#       pass


# ==================================================
# TRACKING (untuk mengetahui field yang berubah)
# ==================================================

from django.db.models import Model
from django.utils.functional import cached_property

class TrackableModel(Model):
    """
    Mixin untuk tracking perubahan field.
    """
    
    class Meta:
        abstract = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_state = self._get_current_state()
    
    def _get_current_state(self):
        """Mendapatkan state semua field"""
        state = {}
        for field in self._meta.fields:
            state[field.name] = getattr(self, field.name)
        return state
    
    @cached_property
    def tracker(self):
        """Tracker untuk melihat perubahan"""
        return type('Tracker', (), {
            'has_changed': lambda self, field: self._original_state.get(field) != getattr(self, field),
            'previous': lambda self, field: self._original_state.get(field),
            'changed_fields': [f for f in self._meta.fields if self._original_state.get(f.name) != getattr(self, f.name)]
        })()


# Apply tracking ke Profile
# Profile.__bases__ = (TrackableModel,) + Profile.__bases__


# ==================================================
# END OF FILE: profile.py
# ==================================================