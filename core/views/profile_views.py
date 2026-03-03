from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from core.models import Profile

@login_required
def profile_view(request):
    """Halaman profil user"""
    user = request.user
    profile = user.profile
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile.html', context)

@login_required
def profile_edit(request):
    """Edit profil user"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        # Update user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Update profile
        profile.phone = request.POST.get('phone', '')
        profile.bio = request.POST.get('bio', '')
        
        # Handle foto profil
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        
        # Simpan
        user.save()
        profile.save()
        
        messages.success(request, 'Profil berhasil diperbarui')
        return redirect('profile')
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile_edit.html', context)