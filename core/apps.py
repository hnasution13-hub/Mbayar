# ==================================================
# FILE: Mbayar/core/apps.py
# PATH: D:/Project Pyton/Mbayar/core/apps.py
# FUNGSI: Konfigurasi app core
# ==================================================

from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Aplikasi POS'
    
    def ready(self):
        # Import signals jika ada
        import core.models.profile
        import core.models.log
        pass