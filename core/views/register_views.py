from django.shortcuts import render, redirect
from django.contrib import messages
# HAPUS: from django.contrib.auth import login  <-- HAPUS BARIS INI
from core.forms import RegisterForm

def register(request):
    """Halaman pendaftaran user baru"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # HAPUS: login(request, user)  <-- JANGAN LOGIN OTOMATIS
            
            messages.success(request, 'Pendaftaran berhasil! Silakan login.')
            return redirect('login')  # <-- LANGSUNG KE LOGIN, BUKAN DASHBOARD
        else:
            # Tampilkan error
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})