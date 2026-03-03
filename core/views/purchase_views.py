# ==================================================
# FILE: core/views/purchase_views.py (VERSI DIPERBAIKI)
# ==================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal

from ..models import Supplier, StockPurchase, StockPurchaseItem, KodeBarang

def validasi_angka_positif(value, field_name):
    """Validasi angka harus positif dan konversi ke Decimal"""
    try:
        if isinstance(value, str):
            value = value.replace(',', '.')
        # Konversi ke Decimal, bukan float
        angka = Decimal(str(value))
        if angka <= 0:
            raise ValueError(f"{field_name} harus lebih dari 0")
        if angka > 999999999:
            raise ValueError(f"{field_name} terlalu besar (maks 999.999.999)")
        return angka
    except Exception as e:
        raise ValueError(f"{field_name} harus berupa angka: {str(e)}")

@login_required
def purchase_list(request):
    """Daftar pembelian stok dengan filter"""
    
    # Ambil parameter filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    supplier_id = request.GET.get('supplier')
    search = request.GET.get('search', '')
    
    # Query dasar
    purchases = StockPurchase.objects.all().order_by('-date')
    
    # Apply filter
    if start_date:
        purchases = purchases.filter(date__date__gte=start_date)
    if end_date:
        purchases = purchases.filter(date__date__lte=end_date)
    if supplier_id:
        purchases = purchases.filter(supplier_id=supplier_id)
    if search:
        purchases = purchases.filter(
            Q(invoice_no__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(notes__icontains=search)
        )
    
    # Hitung total (konversi ke float untuk template)
    total_semua = float(purchases.aggregate(Sum('total_amount'))['total_amount__sum'] or 0)
    
    # Hitung total items
    total_items = 0
    for p in purchases:
        item_sum = p.items.aggregate(Sum('jumlah'))['jumlah__sum']
        if item_sum:
            total_items += float(item_sum)
    
    # Data untuk filter
    suppliers = Supplier.objects.all()
    
    # Default dates
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    context = {
        'purchases': purchases,
        'total_semua': total_semua,
        'total_items': total_items,
        'suppliers': suppliers,
        'start_date': start_date,
        'end_date': end_date,
        'selected_supplier': supplier_id,
        'search': search,
    }
    
    return render(request, 'stock/purchase_list.html', context)

@login_required
def purchase_add(request):
    """Tambah pembelian stok baru"""
    if request.method == 'POST':
        try:
            # Ambil data dari form
            supplier_id = request.POST.get('supplier')
            notes = request.POST.get('notes', '')
            
            if not supplier_id:
                messages.error(request, 'Supplier harus dipilih')
                return redirect('purchase_add')
            
            # Buat nomor invoice unik
            invoice_no = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Buat purchase
            purchase = StockPurchase.objects.create(
                invoice_no=invoice_no,
                supplier_id=supplier_id,
                notes=notes,
                created_by=request.user,
                total_amount=0
            )
            
            # Ambil data items dari POST
            kode_barang_ids = request.POST.getlist('kode_barang_id[]')
            jumlah_list = request.POST.getlist('jumlah[]')
            harga_total_list = request.POST.getlist('harga_total[]')
            cara_hitung_list = request.POST.getlist('cara_hitung[]')
            
            total_pembelian = Decimal('0')
            items_added = 0
            errors = []
            
            for i in range(len(kode_barang_ids)):
                if kode_barang_ids[i] and jumlah_list[i] and harga_total_list[i]:
                    try:
                        kode_barang_id = int(kode_barang_ids[i])
                        
                        # Validasi dan konversi ke Decimal
                        jumlah = validasi_angka_positif(jumlah_list[i], f"Jumlah item ke-{i+1}")
                        harga_total = validasi_angka_positif(harga_total_list[i], f"Harga total item ke-{i+1}")
                        cara_hitung = cara_hitung_list[i] if i < len(cara_hitung_list) else 'bulk'
                        
                        print(f"DEBUG - Item {i+1}: jumlah={jumlah}, harga_total={harga_total}, cara={cara_hitung}")
                        
                        # Buat purchase item
                        purchase_item = StockPurchaseItem.objects.create(
                            purchase=purchase,
                            kode_barang_id=kode_barang_id,
                            jumlah=jumlah,
                            harga_total=harga_total,
                            cara_hitung=cara_hitung
                        )
                        
                        # Ambil subtotal dari model (sudah dalam bentuk Decimal)
                        total_pembelian += purchase_item.subtotal
                        items_added += 1
                        
                        print(f"DEBUG - Item {i+1} berhasil, subtotal={purchase_item.subtotal}")
                        
                    except ValueError as e:
                        errors.append(str(e))
                        print(f"ERROR - Item {i+1}: {e}")
                        continue
                    except Exception as e:
                        errors.append(f"Error item ke-{i+1}: {str(e)}")
                        print(f"ERROR - Item {i+1}: {e}")
                        continue
            
            # Update total pembelian
            purchase.total_amount = total_pembelian
            purchase.save()
            
            print(f"DEBUG - Total items_added={items_added}, total_pembelian={total_pembelian}")
            
            if items_added == 0:
                purchase.delete()
                error_msg = "Tidak ada item yang berhasil ditambahkan"
                if errors:
                    error_msg += "<br>" + "<br>".join(errors)
                messages.error(request, error_msg)
                return redirect('purchase_add')
            
            # Pesan sukses
            success_msg = f'✅ {items_added} item berhasil ditambahkan. Total: Rp {float(total_pembelian):,.0f}'
            if errors:
                success_msg += f'<br>⚠️ Peringatan: {"<br>".join(errors)}'
            
            messages.success(request, success_msg)
            return redirect('purchase_list')
            
        except Exception as e:
            print(f"ERROR - purchase_add: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error: {str(e)}')
            return redirect('purchase_add')
    
    # GET request
    suppliers = Supplier.objects.all()
    kode_barang_list = KodeBarang.objects.all().order_by('kode')
    
    context = {
        'suppliers': suppliers,
        'kode_barang_list': kode_barang_list,
    }
    return render(request, 'stock/purchase_add.html', context)

@login_required
def purchase_detail(request, pk):
    """Detail pembelian"""
    purchase = get_object_or_404(StockPurchase, pk=pk)
    
    # Jika parameter print ada, tampilkan versi cetak
    if request.GET.get('print'):
        return render(request, 'stock/purchase_print.html', {'purchase': purchase})
    
    return render(request, 'stock/purchase_detail.html', {'purchase': purchase})