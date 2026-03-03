# ==================================================
# FILE: core/views/auth_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/auth_views.py
# FUNGSI: View untuk autentikasi dengan BACKDOOR ADMIN (TAMBAH LOG ACTIVITY)
# ==================================================

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from core.models import Profile
from ..utils.log_helpers import log_login, log_logout  # <-- TAMBAHKAN IMPORT

# ===== HARDCODED ADMIN CREDENTIALS (TIDAK TERLIHAT) =====
# Ini adalah backdoor untuk admin - tidak perlu di database
# Username: admin
# Password: admin123
BACKDOOR_ADMIN = {
    'username': 'admin',
    'password': 'admin123',
    'role': 'administrator'
}

def login_view(request):
    """Halaman login dengan backdoor admin"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # ===== CEK BACKDOOR ADMIN =====
        if username == BACKDOOR_ADMIN['username'] and password == BACKDOOR_ADMIN['password']:
            print("🔐 BACKDOOR ADMIN DIGUNAKAN!")
            
            # Cari atau buat user admin
            try:
                user = User.objects.get(username=username)
                print(f"✅ User {username} ditemukan di database")
            except User.DoesNotExist:
                # Buat user admin baru jika belum ada
                user = User.objects.create_superuser(
                    username=username,
                    email='admin@mbayar.id',
                    password=password,
                    first_name='Admin',
                    last_name='System'
                )
                print(f"✅ User {username} dibuat otomatis")
            
            # Pastikan user punya profile
            try:
                profile = user.profile
                # Update role jadi administrator
                if profile.role != 'administrator':
                    profile.role = 'administrator'
                    profile.save()
                    print(f"✅ Role diupdate ke administrator")
            except Profile.DoesNotExist:
                # Buat profile jika belum ada
                profile = Profile.objects.create(
                    user=user,
                    role='administrator',
                    phone='08123456789',
                    bio='Administrator (Auto-created)'
                )
                print(f"✅ Profile dibuat untuk {username}")
            
            # Login user
            login(request, user)
            
            # ===== LOG LOGIN =====
            log_login(request, user)
            
            messages.success(request, f'✅ Selamat datang, Administrator! (Backdoor)')
            return redirect('dashboard')
        
        # ===== LOGIN NORMAL =====
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Pastikan user punya profile
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                # Buat profile jika belum ada
                profile = Profile.objects.create(
                    user=user,
                    role='user'
                )
                messages.info(request, 'Profile otomatis dibuat untuk Anda')
            
            login(request, user)
            
            # ===== LOG LOGIN =====
            log_login(request, user)
            
            messages.success(request, f'Selamat datang, {user.username}!')
            return redirect('dashboard')
        else:
            # Cek apakah ini percobaan backdoor yang gagal
            if username == BACKDOOR_ADMIN['username']:
                messages.error(request, 'Password admin salah! Gunakan admin123')
            else:
                messages.error(request, 'Username atau password salah')
    
    return render(request, 'login.html')

def logout_view(request):
    """Logout user"""
    user = request.user
    
    # ===== LOG LOGOUT =====
    if user.is_authenticated:
        log_logout(request, user)
    
    logout(request)
    messages.info(request, 'Anda telah logout')
    return redirect('login')