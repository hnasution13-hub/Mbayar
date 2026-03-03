# ==================================================
# FILE: core/views/stock_views.py
# ==================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F

from ..models import StockItem, KodeBarang

@login_required
def stock_item_list(request):
    """Daftar semua item stok"""
    items = StockItem.objects.all().select_related('kode_barang')
    return render(request, 'stock/item_list.html', {'items': items})

@login_required
def stock_item_add(request):
    """Tambah item stok baru"""
    if request.method == 'POST':
        # Manual handling untuk menghindari error
        kode_barang_id = request.POST.get('kode_barang')
        name = request.POST.get('name')
        unit = request.POST.get('unit')
        stock = request.POST.get('stock', 0)
        min_stock = request.POST.get('min_stock', 0)
        markup_persen = request.POST.get('markup_persen', 30)
        markup_nominal = request.POST.get('markup_nominal', 0)
        
        # Konversi nilai kosong menjadi 0
        try:
            stock = float(stock) if stock else 0
        except ValueError:
            stock = 0
            
        try:
            min_stock = float(min_stock) if min_stock else 0
        except ValueError:
            min_stock = 0
            
        try:
            markup_persen = float(markup_persen) if markup_persen else 30
        except ValueError:
            markup_persen = 30
            
        try:
            markup_nominal = float(markup_nominal) if markup_nominal else 0
        except ValueError:
            markup_nominal = 0
        
        # Buat item baru
        kode_barang = get_object_or_404(KodeBarang, id=kode_barang_id)
        
        StockItem.objects.create(
            kode_barang=kode_barang,
            name=name,
            unit=unit,
            stock=stock,
            min_stock=min_stock,
            markup_persen=markup_persen,
            markup_nominal=markup_nominal,
            harga_beli_terakhir=0,
            harga_rata_rata=0,
            total_nilai_stok=0
        )
        
        messages.success(request, 'Item stok berhasil ditambahkan')
        return redirect('stock_item_list')
    
    # GET request
    kode_barang_list = KodeBarang.objects.all().order_by('kode')
    
    return render(request, 'stock/item_add.html', {
        'kode_barang_list': kode_barang_list,
    })

@login_required
def stock_item_edit(request, pk):
    """Edit item stok (hanya markup dan nama, stok otomatis dari pembelian)"""
    item = get_object_or_404(StockItem.objects.select_related('kode_barang'), pk=pk)
    
    if request.method == 'POST':
        # Ambil data dari form dengan penanganan nilai kosong
        name = request.POST.get('name')
        unit = request.POST.get('unit')
        min_stock = request.POST.get('min_stock', 0)
        markup_persen = request.POST.get('markup_persen', 30)
        markup_nominal = request.POST.get('markup_nominal', 0)
        
        # Konversi nilai kosong menjadi 0
        try:
            min_stock = float(min_stock) if min_stock else 0
        except ValueError:
            min_stock = 0
            
        try:
            markup_persen = float(markup_persen) if markup_persen else 30
        except ValueError:
            markup_persen = 30
            
        try:
            markup_nominal = float(markup_nominal) if markup_nominal else 0
        except ValueError:
            markup_nominal = 0
        
        # Update field yang boleh diedit
        item.name = name
        item.unit = unit
        item.min_stock = min_stock
        item.markup_persen = markup_persen
        item.markup_nominal = markup_nominal
        
        # Kode barang tidak boleh diubah karena terhubung dengan pembelian
        # Stok tidak boleh diubah manual karena otomatis dari pembelian
        
        item.save()
        messages.success(request, 'Item stok berhasil diupdate')
        return redirect('stock_item_list')
    
    # GET request - tampilkan form
    kode_barang_list = KodeBarang.objects.all().order_by('kode')
    
    return render(request, 'stock/item_edit.html', {
        'item': item,
        'kode_barang_list': kode_barang_list,
    })

@login_required
def stock_item_delete(request, pk):
    """Hapus item stok"""
    item = get_object_or_404(StockItem, pk=pk)
    item.delete()
    messages.success(request, 'Item stok berhasil dihapus')
    return redirect('stock_item_list')

@login_required
def low_stock_list(request):
    """Daftar stok menipis"""
    items = StockItem.objects.filter(stock__lte=F('min_stock'), min_stock__gt=0).select_related('kode_barang')
    return render(request, 'stock/low_stock.html', {'items': items})