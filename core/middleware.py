# ==================================================
# FILE: core/middleware.py
# PATH: D:/Project Pyton/Mbayar/core/middleware.py
# FUNGSI: Middleware untuk mencatat aktivitas dan manajemen outlet
# ==================================================

from .utils.log_helpers import log_activity
from .models.outlet import Outlet
from .models import Profile


# ==================================================
# MIDDLEWARE: ActivityLogMiddleware
# ==================================================
class ActivityLogMiddleware:
    """
    Middleware untuk mencatat request (saat ini masih placeholder).
    Bisa dikembangkan untuk mencatat setiap request ke database.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request sebelum view
        response = self.get_response(request)

        # Catat setelah response (bisa ditambahkan nanti)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Bisa digunakan untuk log specific views
        pass


# ==================================================
# MIDDLEWARE: OutletMiddleware
# ==================================================
class OutletMiddleware:
    """
    Middleware untuk menambahkan informasi outlet ke dalam request.
    Outlet ditentukan dari session atau dari profil user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        outlet = self.get_outlet(request)
        request.outlet = outlet
        response = self.get_response(request)
        return response

    def get_outlet(self, request):
        """Mengambil outlet berdasarkan session atau profil user."""
        outlet_id = request.session.get('outlet_id')
        if outlet_id:
            try:
                # Gunakan status='aktif' karena field is_active tidak ada
                return Outlet.objects.get(id=outlet_id, status='aktif')
            except Outlet.DoesNotExist:
                pass

        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                outlet = profile.outlet
                if outlet and outlet.status == 'aktif':
                    request.session['outlet_id'] = outlet.id
                    return outlet
            except (Profile.DoesNotExist, AttributeError):
                pass

        return None


# ==================================================
# MIDDLEWARE: EnsureProfileMiddleware
# ==================================================
class EnsureProfileMiddleware:
    """
    Middleware untuk memastikan setiap user yang sudah login memiliki objek Profile.
    Jika belum ada, akan dibuat secara otomatis dengan role default 'user'.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            Profile.objects.get_or_create(
                user=request.user,
                defaults={'role': 'user'}
            )
        response = self.get_response(request)
        return response