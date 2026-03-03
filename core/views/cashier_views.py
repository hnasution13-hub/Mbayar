# ==================================================
# FILE: core/views/cashier_views.py
# FUNGSI: View untuk kasir dengan dukungan GoFood
# ==================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from decimal import Decimal

from ..models import Menu, MenuCategory, Order, OrderItem

@login_required
def cashier_view(request):
    """Halaman utama kasir"""
    menus = Menu.objects.filter(is_available=True).select_related('category')
    categories = MenuCategory.objects.all()
    
    # Debug: cek harga gofood (bisa dihapus setelah production)
    for menu in menus:
        print(f"Menu: {menu.name}")
        print(f"  - Harga Jual: Rp {menu.selling_price}")
        print(f"  - Harga GoFood: Rp {menu.gofood_price}")
    
    return render(request, 'cashier/index.html', {
        'menus': menus,
        'categories': categories
    })

@login_required
def search_menu(request):
    """Search menu via AJAX"""
    query = request.GET.get('q', '')
    menus = Menu.objects.filter(
        Q(code__icontains=query) | Q(name__icontains=query),
        is_available=True
    )[:10]
    
    data = [{
        'id': m.id,
        'code': m.code,
        'name': m.name,
        'price': float(m.selling_price),
        'gofood_price': float(m.gofood_price)
    } for m in menus]
    
    return JsonResponse({'menus': data})

@csrf_exempt
@login_required
def create_order(request):
    """Buat order baru dari keranjang"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Ambil data dengan validasi
            customer_name = data.get('customer_name', 'Umum')
            items = data.get('items', [])
            payment_method = data.get('payment_method', 'cash')
            amount_paid = Decimal(str(data.get('amount_paid', 0)))
            discount = Decimal(str(data.get('discount', 0)))
            order_type = data.get('order_type', 'normal')
            total_final = Decimal(str(data.get('total_final', 0)))
            
            if not items:
                return JsonResponse({'success': False, 'error': 'Keranjang kosong'})
            
            # Buat nomor order
            from ..utils.helpers import generate_invoice_no
            order_no = generate_invoice_no('ORD')
            
            # Hitung subtotal dari items
            subtotal = Decimal('0')
            order_items_data = []
            
            print("\n" + "="*60)
            print("📝 MEMPROSES ORDER BARU")
            print("="*60)
            print(f"Pelanggan: {customer_name}")
            print(f"Tipe Order: {order_type}")
            
            for i, item in enumerate(items):
                menu_id = item.get('menu_id')
                quantity = int(item.get('quantity', 1))
                is_gofood = item.get('is_gofood', False)
                
                try:
                    menu = Menu.objects.get(id=menu_id)
                    
                    # Tentukan harga berdasarkan tipe order
                    if is_gofood:
                        price = menu.gofood_price
                        print(f"\n{i+1}. {menu.name} (GoFood)")
                    else:
                        price = menu.selling_price
                        print(f"\n{i+1}. {menu.name} (Normal)")
                    
                    # Hitung subtotal item (price sudah Decimal)
                    item_subtotal = price * quantity
                    subtotal += item_subtotal
                    
                    print(f"   Harga: Rp {price} x {quantity} = Rp {item_subtotal}")
                    
                    order_items_data.append({
                        'menu': menu,
                        'menu_name': menu.name,
                        'quantity': quantity,
                        'price': price,
                        'subtotal': item_subtotal,
                        'notes': item.get('notes', ''),
                        'is_gofood': is_gofood
                    })
                    
                except Menu.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Menu dengan ID {menu_id} tidak ditemukan'})
            
            # Hitung pajak (10% dari subtotal)
            tax = subtotal * Decimal('0.1')
            
            print(f"\n💰 RINCIAN:")
            print(f"   Subtotal: Rp {subtotal}")
            print(f"   Diskon: Rp {discount}")
            print(f"   Pajak 10%: Rp {tax}")
            print(f"   Total final (dari client): Rp {total_final}")
            
            # Buat order
            order = Order.objects.create(
                order_no=order_no,
                cashier=request.user,
                customer_name=customer_name,
                payment_method=payment_method,
                amount_paid=amount_paid,
                discount=discount,
                tax=tax,
                subtotal=subtotal,
                total=total_final,
                status='paid',
                order_date=timezone.now(),
                order_type=order_type
            )
            
            # Hitung kembalian
            order.change = amount_paid - total_final
            order.save(update_fields=['change'])
            
            # Buat order items
            for item_data in order_items_data:
                order_item = OrderItem.objects.create(
                    order=order,
                    menu=item_data['menu'],
                    menu_name=item_data['menu_name'],
                    quantity=item_data['quantity'],
                    price=item_data['price'],
                    subtotal=item_data['subtotal'],
                    notes=item_data['notes'],
                    is_gofood=item_data['is_gofood']
                )
                
                # Kurangi stok bahan
                if item_data['menu']:
                    for ingredient in item_data['menu'].menu_ingredients.all():
                        stock_item = ingredient.stock_item
                        if stock_item:
                            jumlah_dipakai = ingredient.quantity_used * item_data['quantity']
                            stock_item.stock -= jumlah_dipakai
                            stock_item.save()
                            print(f"   Stok {stock_item.name} berkurang: {jumlah_dipakai}")
            
            print(f"\n✅ ORDER BERHASIL: {order_no}")
            print("="*60)
            
            return JsonResponse({
                'success': True,
                'order_no': order.order_no,
                'total': float(order.total),
                'change': float(order.change)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Format data tidak valid'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method tidak diizinkan'})

@login_required
def order_detail(request, order_no):
    """Detail order"""
    order = get_object_or_404(Order, order_no=order_no)
    return render(request, 'orders/detail.html', {'order': order})

@login_required
def print_receipt(request, order_no):
    """Cetak struk"""
    order = get_object_or_404(Order, order_no=order_no)
    return render(request, 'cashier/receipt.html', {'order': order})