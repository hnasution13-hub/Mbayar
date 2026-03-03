# ==================================================
# FILE: core/views/admin_views.py
# PATH: D:/Project Pyton/Mbayar/core/views/admin_views.py
# FUNGSI: View untuk admin data management
# ==================================================

import os
import json
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.conf import settings
from django.utils import timezone
from django.db import connection
import pandas as pd

from ..models import ImportExportLog
from ..utils.import_handlers import get_import_handler
from ..utils.helpers import parse_date
from ..decorators import admin_required  # <-- IMPORT DECORATOR

@login_required
@admin_required  # <-- PAKAI DECORATOR ROLE
def admin_data_management(request):
    """Halaman utama admin untuk manajemen data"""
    recent_logs = ImportExportLog.objects.all()[:20]
    
    context = {
        'recent_logs': recent_logs,
        'start_date': timezone.now().date() - timedelta(days=30),
        'end_date': timezone.now().date(),
    }
    return render(request, 'admin/data_management.html', context)

@login_required
@admin_required
def download_template(request, data_type):
    """Download template Excel untuk import"""
    # Generate template on the fly
    return generate_template(data_type)

def generate_template(data_type):
    """Generate template Excel jika file belum ada"""
    output = BytesIO()
    
    if data_type == 'kode_barang':
        df = pd.DataFrame(columns=['KODE', 'NAMA', 'KETERANGAN'])
        df.loc[0] = ['B001', 'Gula Pasir', 'Gula putih 1kg']
        
    elif data_type == 'supplier':
        df = pd.DataFrame(columns=['NAMA', 'KONTAK', 'TELEPON', 'ALAMAT'])
        df.loc[0] = ['PT Sumber Makmur', 'Budi', '08123456789', 'Jl. Sudirman No. 123']
        
    elif data_type == 'menu':
        df = pd.DataFrame(columns=['KODE_MENU', 'NAMA_MENU', 'KATEGORI', 'KODE_BAHAN', 'JUMLAH', 'CATATAN'])
        df.loc[0] = ['M001', 'Nasi Goreng', 'Makanan', 'B001', '0.25', 'kg']
        df.loc[1] = ['M001', 'Nasi Goreng', 'Makanan', 'B002', '2', 'butir']
        
    else:
        return JsonResponse({'error': 'Tipe data tidak dikenal'}, status=400)
    
    # Simpan ke Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{data_type}_template.xlsx"'
    return response

@login_required
@admin_required
def import_data(request):
    """Proses import data dari file Excel/CSV"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method tidak diizinkan'}, status=405)
    
    start_time = datetime.now()
    
    try:
        data_type = request.POST.get('data_type')
        file = request.FILES.get('import_file')
        
        if not data_type or not file:
            return JsonResponse({'error': 'Tipe data dan file harus diisi'}, status=400)
        
        # Buat log entry
        log = ImportExportLog.objects.create(
            user=request.user,
            action='import',
            data_type=data_type,
            filename=file.name,
            file_size=file.size,
            status='pending',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Proses import
        handler = get_import_handler(data_type, file, request.user)
        results = handler.process()
        
        # Update log
        log.status = 'success' if results['failed'] == 0 else 'warning'
        log.records_processed = results['total']
        log.records_success = results['success']
        log.records_failed = results['failed']
        log.completed_at = datetime.now()
        log.duration_seconds = (log.completed_at - start_time).total_seconds()
        
        if results['errors']:
            log.error_message = json.dumps(results['errors'][:5])  # Simpan 5 error pertama
        
        log.save()
        
        message = f"Import selesai: {results['success']} sukses, {results['failed']} gagal"
        if results['warnings']:
            message += f", {len(results['warnings'])} warning"
        
        return JsonResponse({
            'success': True,
            'message': message,
            'results': results
        })
        
    except Exception as e:
        # Log error
        if 'log' in locals():
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = datetime.now()
            log.save()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@admin_required
def import_export_logs_api(request):
    """API untuk mendapatkan log terbaru (AJAX)"""
    logs = ImportExportLog.objects.all()[:20]
    data = []
    
    for log in logs:
        data.append({
            'id': log.id,
            'time': log.created_at.strftime('%d/%m/%Y %H:%M'),
            'user': log.user.username if log.user else 'System',
            'action': log.get_action_display(),
            'data_type': log.get_data_type_display(),
            'filename': log.filename,
            'file_size': log.file_size_display,
            'status': log.status,
            'records_success': log.records_success,
            'records_failed': log.records_failed,
            'duration': f"{log.duration_seconds:.1f}s"
        })
    
    return JsonResponse({'logs': data})

@login_required
@admin_required
def export_multiple(request):
    """Export multiple laporan sekaligus dalam ZIP"""
    reports = request.GET.getlist('reports')
    start_date = parse_date(request.GET.get('start_date'), timezone.now().date() - timedelta(days=30))
    end_date = parse_date(request.GET.get('end_date'), timezone.now().date())
    
    if not reports:
        messages.error(request, 'Pilih minimal satu laporan')
        return redirect('admin_data_management')
    
    # Buat parameter untuk request
    from django.http import QueryDict
    qd = QueryDict(mutable=True)
    qd['start_date'] = start_date.strftime('%Y-%m-%d')
    qd['end_date'] = end_date.strftime('%Y-%m-%d')
    
    # Buat request baru
    from django.test import RequestFactory
    factory = RequestFactory()
    new_request = factory.get('/', qd)
    new_request.user = request.user
    new_request.session = request.session
    
    # Buat ZIP in memory
    zip_buffer = BytesIO()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for report in reports:
            try:
                if report == 'sales_excel':
                    from ..views.export_views import export_sales_excel
                    response = export_sales_excel(new_request)
                    zip_file.writestr(f'laporan_penjualan_{timestamp}.xlsx', response.content)
                    
                elif report == 'profit_excel':
                    from ..views.export_views import export_profit_excel
                    response = export_profit_excel(new_request)
                    zip_file.writestr(f'laporan_laba_{timestamp}.xlsx', response.content)
                    
                elif report == 'stock_excel':
                    from ..views.export_views import export_stock_excel
                    response = export_stock_excel(new_request)
                    zip_file.writestr(f'laporan_stok_{timestamp}.xlsx', response.content)
                    
                elif report == 'sales_pdf':
                    from ..views.export_views import export_sales_pdf
                    response = export_sales_pdf(new_request)
                    zip_file.writestr(f'laporan_penjualan_{timestamp}.pdf', response.content)
                    
                elif report == 'profit_pdf':
                    from ..views.export_views import export_profit_pdf
                    response = export_profit_pdf(new_request)
                    zip_file.writestr(f'laporan_laba_{timestamp}.pdf', response.content)
                    
                elif report == 'backup':
                    backup_data = backup_database(request, return_content=True)
                    if backup_data:
                        zip_file.writestr(f'backup_database_{timestamp}.sql', backup_data)
                
                # Log export activity
                ImportExportLog.objects.create(
                    user=request.user,
                    action='export',
                    data_type=report.replace('_', ' '),
                    filename=f"{report}_{timestamp}.{'xlsx' if 'excel' in report else 'pdf' if 'pdf' in report else 'sql'}",
                    status='success'
                )
                
            except Exception as e:
                ImportExportLog.objects.create(
                    user=request.user,
                    action='export',
                    data_type=report,
                    filename='error',
                    status='failed',
                    error_message=str(e)
                )
    
    zip_buffer.seek(0)
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="laporan_lengkap_{timestamp}.zip"'
    return response

@login_required
@admin_required
def backup_database(request, return_content=False):
    """Backup database SQLite"""
    import sqlite3
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'mbayar_backup_{timestamp}.sql')
    
    # Backup SQLite
    db_path = settings.DATABASES['default']['NAME']
    if isinstance(db_path, str):
        with sqlite3.connect(db_path) as conn:
            with open(backup_file, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
    
    if return_content:
        with open(backup_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Log backup
    ImportExportLog.objects.create(
        user=request.user,
        action='backup',
        data_type='database',
        filename=os.path.basename(backup_file),
        file_size=os.path.getsize(backup_file),
        status='success'
    )
    
    messages.success(request, f'Backup database berhasil: {os.path.basename(backup_file)}')
    return redirect('admin_data_management')

@login_required
@admin_required
def backup_list(request):
    """Daftar file backup"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = []
    
    if os.path.exists(backup_dir):
        files = sorted(os.listdir(backup_dir), reverse=True)
        for f in files:
            if f.endswith('.sql'):
                path = os.path.join(backup_dir, f)
                backups.append({
                    'name': f,
                    'size': os.path.getsize(path),
                    'size_display': format_size(os.path.getsize(path)),
                    'modified': datetime.fromtimestamp(os.path.getmtime(path)),
                    'modified_str': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%d/%m/%Y %H:%M')
                })
    
    return render(request, 'admin/backup_list.html', {'backups': backups})

def format_size(size):
    """Format ukuran file"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

@login_required
@admin_required
def restore_database(request, backup_file):
    """Restore database dari file backup"""
    backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_file)
    
    if not os.path.exists(backup_path):
        messages.error(request, 'File backup tidak ditemukan')
        return redirect('backup_list')
    
    try:
        import sqlite3
        
        # Backup current database first
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup = os.path.join(settings.BASE_DIR, 'backups', f'before_restore_{timestamp}.sql')
        db_path = settings.DATABASES['default']['NAME']
        
        with sqlite3.connect(db_path) as conn:
            with open(current_backup, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
        
        # Restore
        with sqlite3.connect(db_path) as conn:
            with open(backup_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
                conn.executescript(sql_script)
        
        # Log restore
        ImportExportLog.objects.create(
            user=request.user,
            action='restore',
            data_type='database',
            filename=backup_file,
            status='success'
        )
        
        messages.success(request, f'Database berhasil direstore dari {backup_file}')
        
    except Exception as e:
        messages.error(request, f'Error saat restore: {str(e)}')
    
    return redirect('backup_list')