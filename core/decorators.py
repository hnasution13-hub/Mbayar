from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles=[]):
    """Decorator untuk membatasi akses berdasarkan role"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                user_role = request.user.profile.role
            except:
                # Kalau profile belum ada, redirect ke logout
                messages.error(request, 'Profil user tidak ditemukan. Silakan login ulang.')
                return redirect('logout')
            
            if user_role in allowed_roles or user_role == 'administrator':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Anda tidak memiliki akses ke halaman ini')
                return redirect('dashboard')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """Decorator khusus administrator"""
    return role_required(['administrator'])(view_func)

def supervisor_required(view_func):
    """Decorator untuk supervisor ke atas"""
    return role_required(['supervisor', 'administrator'])(view_func)

def kasir_required(view_func):
    """Decorator untuk semua user (kasir, supervisor, admin)"""
    return role_required(['user', 'supervisor', 'administrator'])(view_func)