# ==================================================
# FILE: core/views/api_views.py
# FUNGSI: API endpoints untuk fitur-fitur tambahan
# ==================================================

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ..models import Menu, MenuModifier, ModifierOption

@login_required
def get_menu_modifiers(request, menu_id):
    """
    API untuk mendapatkan modifier menu
    Dipanggil dari cashier saat user klik menu
    """
    try:
        menu = Menu.objects.get(id=menu_id, is_available=True)
        modifiers = []
        
        # Ambil semua modifier aktif untuk menu ini
        for modifier in menu.modifiers.filter(is_active=True).order_by('sort_order'):
            modifier_data = {
                'id': modifier.id,
                'name': modifier.name,
                'type': modifier.type,
                'required': modifier.required,
                'min_select': modifier.min_select,
                'max_select': modifier.max_select,
                'options': []
            }
            
            # Ambil semua opsi untuk modifier ini
            for option in modifier.options.all().order_by('sort_order'):
                modifier_data['options'].append({
                    'id': option.id,
                    'name': option.name,
                    'price_addition': float(option.price_addition),
                    'is_default': option.is_default,
                    'has_stock': option.stock_item is not None and option.quantity_used > 0
                })
            
            modifiers.append(modifier_data)
        
        return JsonResponse({
            'success': True,
            'menu_name': menu.name,
            'base_price': float(menu.selling_price),
            'gofood_price': float(menu.gofood_price),
            'modifiers': modifiers
        })
        
    except Menu.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Menu tidak ditemukan'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)