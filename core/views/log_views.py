# ==================================================
# FILE: core/views/log_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/log_views.py
# FUNGSI: View untuk menampilkan log aktivitas
# ==================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from ..models.log import ActivityLog
from ..decorators import admin_required

@login_required
@admin_required
def activity_log_list(request):
    """Halaman daftar log aktivitas"""
    
    # Ambil parameter filter
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    search = request.GET.get('search', '')
    
    # Query dasar
    logs = ActivityLog.objects.all()
    
    # Apply filter
    if user_filter:
        logs = logs.filter(username__icontains=user_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)
    if model_filter:
        logs = logs.filter(model_name=model_filter)
    if start_date:
        logs = logs.filter(created_at__date__gte=start_date)
    if end_date:
        logs = logs.filter(created_at__date__lte=end_date)
    if search:
        logs = logs.filter(
            Q(object_repr__icontains=search) |
            Q(details__icontains=search) |
            Q(username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(logs, 50)  # 50 per halaman
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Data untuk filter dropdown
    users = ActivityLog.objects.values_list('username', flat=True).distinct().order_by('username')
    actions = ActivityLog.ACTION_TYPES
    models = ActivityLog.MODEL_TYPES
    
    context = {
        'logs': page_obj,
        'users': users,
        'actions': actions,
        'models': models,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
    }
    
    return render(request, 'admin/activity_log.html', context)