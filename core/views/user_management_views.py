from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from core.decorators import admin_required
from core.models import Profile

@login_required
@admin_required
def user_list(request):
    """Daftar semua user"""
    users = User.objects.all().select_related('profile')
    return render(request, 'admin/user_list.html', {'users': users})

@login_required
@admin_required
def user_edit_role(request, user_id):
    """Edit role user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        user.profile.role = new_role
        user.profile.save()
        messages.success(request, f'Role {user.username} diubah menjadi {new_role}')
        return redirect('user_list')
    
    return render(request, 'admin/user_edit_role.html', {'user': user})