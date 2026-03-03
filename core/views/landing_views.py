from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def landing(request):
    """Halaman utama publik (sebelum login)"""
    return render(request, 'landing.html')