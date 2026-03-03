# ==================================================
# FILE: core/utils/log_helpers.py
# PATH: D:/Project Pyton/Mbayar/core/utils/log_helpers.py
# FUNGSI: Helper functions untuk mencatat log aktivitas
# ==================================================

import json
from ..models.log import ActivityLog

def log_activity(request, user, action, model_name, object_id=None, object_repr='', details='', changes=None):
    """
    Helper untuk mencatat aktivitas
    
    Args:
        request: HttpRequest object
        user: User object atau None
        action: string (login, logout, create, update, delete, etc)
        model_name: string (user, stockitem, menu, order, etc)
        object_id: int (ID dari object)
        object_repr: string (representasi object)
        details: string (detail tambahan)
        changes: dict (perubahan sebelum/sesudah untuk update)
    """
    
    # Ambil IP address
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    # Ambil user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
    
    # Ambil method dan path
    request_method = request.method if request else ''
    request_path = request.path if request else ''
    
    # Convert changes ke JSON jika dict
    changes_json = None
    if changes:
        try:
            changes_json = json.dumps(changes, indent=2)
        except:
            changes_json = str(changes)
    
    # Buat log
    ActivityLog.objects.create(
        user=user,
        username=user.username if user else 'System',
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        details=details,
        changes=changes_json,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path
    )


def log_create(request, user, model_name, obj, details=''):
    """Mencatat pembuatan data baru"""
    log_activity(
        request=request,
        user=user,
        action='create',
        model_name=model_name,
        object_id=obj.id if hasattr(obj, 'id') else None,
        object_repr=str(obj),
        details=details or f"Membuat {model_name} baru: {str(obj)}"
    )


def log_update(request, user, model_name, obj, changes_dict, details=''):
    """Mencatat perubahan data"""
    log_activity(
        request=request,
        user=user,
        action='update',
        model_name=model_name,
        object_id=obj.id if hasattr(obj, 'id') else None,
        object_repr=str(obj),
        details=details or f"Mengubah {model_name}: {str(obj)}",
        changes=changes_dict
    )


def log_delete(request, user, model_name, obj_id, obj_repr, details=''):
    """Mencatat penghapusan data"""
    log_activity(
        request=request,
        user=user,
        action='delete',
        model_name=model_name,
        object_id=obj_id,
        object_repr=obj_repr,
        details=details or f"Menghapus {model_name}: {obj_repr}"
    )


def log_login(request, user):
    """Mencatat user login"""
    log_activity(
        request=request,
        user=user,
        action='login',
        model_name='user',
        object_id=user.id,
        object_repr=user.username,
        details=f"User {user.username} login"
    )


def log_logout(request, user):
    """Mencatat user logout"""
    log_activity(
        request=request,
        user=user,
        action='logout',
        model_name='user',
        object_id=user.id,
        object_repr=user.username,
        details=f"User {user.username} logout"
    )


def log_payment(request, user, order):
    """Mencatat transaksi pembayaran"""
    log_activity(
        request=request,
        user=user,
        action='payment',
        model_name='order',
        object_id=order.id,
        object_repr=order.order_no,
        details=f"Transaksi {order.order_no}: Rp {order.total} - {order.customer_name}"
    )