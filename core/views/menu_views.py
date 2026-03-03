# ==================================================
# FILE: core/views/menu_views.py
# ==================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from ..models import MenuCategory, Menu, MenuIngredient, StockItem
from ..forms import MenuForm

# ===== KATEGORI MENU =====

@login_required
def menu_category_list(request):
    """Daftar kategori menu"""
    categories = MenuCategory.objects.all()
    return render(request, 'menu/category_list.html', {'categories': categories})

@login_required
def menu_category_add(request):
    """Tambah kategori menu"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        MenuCategory.objects.create(name=name, description=description)
        messages.success(request, 'Kategori berhasil ditambahkan')
        return redirect('menu_category_list')
    return render(request, 'menu/category_add.html')

@login_required
def menu_category_edit(request, pk):
    """Edit kategori menu"""
    category = get_object_or_404(MenuCategory, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.save()
        messages.success(request, 'Kategori berhasil diupdate')
        return redirect('menu_category_list')
    return render(request, 'menu/category_edit.html', {'category': category})

# ===== MENU =====

@login_required
def menu_list(request):
    """Daftar menu"""
    menus = Menu.objects.all().prefetch_related('menu_ingredients__stock_item')
    categories = MenuCategory.objects.all()
    
    # Hitung statistik
    total_menu = menus.count()
    total_tersedia = menus.filter(is_available=True).count()
    total_tidak_tersedia = menus.filter(is_available=False).count()
    total_kategori = categories.count()
    
    context = {
        'menus': menus,
        'categories': categories,
        'total_menu': total_menu,
        'total_tersedia': total_tersedia,
        'total_tidak_tersedia': total_tidak_tersedia,
        'total_kategori': total_kategori,
    }
    return render(request, 'menu/list.html', context)

@login_required
def menu_add(request):
    """Tambah menu baru"""
    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES)
        if form.is_valid():
            menu = form.save()
            
            # Proses bahan-bahan
            ingredient_ids = request.POST.getlist('ingredient_id[]')
            quantities = request.POST.getlist('quantity[]')
            notes_list = request.POST.getlist('notes[]')
            
            for i in range(len(ingredient_ids)):
                if ingredient_ids[i] and quantities[i]:
                    MenuIngredient.objects.create(
                        menu=menu,
                        stock_item_id=ingredient_ids[i],
                        quantity_used=float(quantities[i]),
                        notes=notes_list[i] if i < len(notes_list) else ''
                    )
            
            messages.success(request, 'Menu berhasil ditambahkan')
            return redirect('menu_list')
    else:
        form = MenuForm()
    
    categories = MenuCategory.objects.all()
    # Ambil semua stock item dengan harga_gofood
    ingredients = StockItem.objects.all().select_related('kode_barang')
    
    return render(request, 'menu/add.html', {
        'form': form,
        'categories': categories,
        'ingredients': ingredients
    })

@login_required
def menu_edit(request, pk):
    """Edit menu"""
    menu = get_object_or_404(Menu, pk=pk)
    
    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES, instance=menu)
        if form.is_valid():
            menu = form.save()
            
            # Hapus bahan lama
            menu.menu_ingredients.all().delete()
            
            # Tambah bahan baru
            ingredient_ids = request.POST.getlist('ingredient_id[]')
            quantities = request.POST.getlist('quantity[]')
            notes_list = request.POST.getlist('notes[]')
            
            for i in range(len(ingredient_ids)):
                if ingredient_ids[i] and quantities[i]:
                    MenuIngredient.objects.create(
                        menu=menu,
                        stock_item_id=ingredient_ids[i],
                        quantity_used=float(quantities[i]),
                        notes=notes_list[i] if i < len(notes_list) else ''
                    )
            
            messages.success(request, 'Menu berhasil diupdate')
            return redirect('menu_list')
    else:
        form = MenuForm(instance=menu)
    
    categories = MenuCategory.objects.all()
    # Ambil semua stock item dengan harga_gofood
    ingredients = StockItem.objects.all().select_related('kode_barang')
    menu_ingredients = menu.menu_ingredients.all().select_related('stock_item')
    
    # Debug: cek apakah harga_gofood ada
    for ing in ingredients:
        print(f"DEBUG - {ing.name}: harga_gofood = {ing.harga_gofood}")
    
    return render(request, 'menu/edit.html', {
        'form': form,
        'categories': categories,
        'ingredients': ingredients,
        'menu': menu,
        'menu_ingredients': menu_ingredients
    })

@login_required
def menu_delete(request, pk):
    """Hapus menu"""
    menu = get_object_or_404(Menu, pk=pk)
    menu.delete()
    messages.success(request, 'Menu berhasil dihapus')
    return redirect('menu_list')

@login_required
def menu_toggle_availability(request, pk):
    """Toggle ketersediaan menu"""
    menu = get_object_or_404(Menu, pk=pk)
    menu.is_available = not menu.is_available
    menu.save()
    messages.success(request, f'Menu {menu.name} {"tersedia" if menu.is_available else "tidak tersedia"}')
    return redirect('menu_list')