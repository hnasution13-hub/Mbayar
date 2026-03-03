# ==================================================
# FILE: core/views/outlet_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/outlet_views.py
# FUNGSI: View untuk manajemen pemilihan outlet/cabang
# FITUR:
#   - Menampilkan daftar outlet yang tersedia (aktif)
#   - Memilih outlet aktif dan menyimpannya ke session
#   - Membatasi outlet sesuai role user (admin bisa semua, user biasa hanya outlet miliknya)
# VERSION: 1.0.0
# UPDATE TERAKHIR: 03/03/2026
# ==================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models.outlet import Outlet
from ..models.profile import Profile

@login_required
def pilih_outlet(request):
    """
    Halaman untuk memilih outlet aktif.
    
    - Jika user adalah administrator, tampilkan semua outlet dengan status 'aktif'.
    - Jika user bukan administrator, tampilkan hanya outlet yang terdaftar di profilnya.
    - Setelah memilih, simpan outlet_id ke session dan redirect ke dashboard.
    """
    # Tentukan queryset outlet berdasarkan role
    if request.user.profile.role == 'administrator':
        # Administrator: tampilkan semua outlet dengan status aktif
        outlets = Outlet.objects.filter(status='aktif')
    else:
        # Non-administrator: hanya outlet yang terdaftar di profilnya (jika ada)
        if request.user.profile.outlet:
            outlets = [request.user.profile.outlet]
        else:
            outlets = []
            messages.warning(request, 'Anda belum memiliki outlet. Hubungi administrator.')
    
    # Proses pemilihan outlet (POST)
    if request.method == 'POST':
        outlet_id = request.POST.get('outlet_id')
        try:
            outlet = Outlet.objects.get(id=outlet_id, status='aktif')
            request.session['outlet_id'] = outlet.id
            messages.success(request, f'Sekarang bekerja di {outlet.name}')
            return redirect('dashboard')
        except Outlet.DoesNotExist:
            messages.error(request, 'Outlet tidak valid atau tidak aktif.')
    
    context = {
        'outlets': outlets,
        'current_outlet': getattr(request, 'outlet', None)
    }
    return render(request, 'outlet/pilih.html', context)


@login_required
def ganti_outlet(request):
    """
    Hapus session outlet dan redirect ke halaman pilih outlet.
    """
    if 'outlet_id' in request.session:
        del request.session['outlet_id']
    messages.info(request, 'Silakan pilih outlet')
    return redirect('pilih_outlet')