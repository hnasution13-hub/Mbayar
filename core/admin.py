# ==================================================
# FILE: Mbayar/core/admin.py
# PATH: D:/Project Pyton/Mbayar/core/admin.py
# FUNGSI: Registrasi model di admin (DENGAN EXPORT, USER PROFILE, DAN OUTLET)
# ==================================================

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse
import csv

from core.models import (
    Supplier, StockItem, StockPurchase, StockPurchaseItem,
    MenuCategory, Menu, MenuIngredient, Order, OrderItem,
    KodeBarang, Profile, MenuModifier, ModifierOption, OrderItemModifier,
    Outlet  # <-- TAMBAHKAN OUTLET
)


# ==================================================
# OUTLET ADMIN
# ==================================================
@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'city', 'status', 'stok_mode', 'created_at']
    list_filter = ['status', 'stok_mode', 'city']
    search_fields = ['code', 'name', 'address', 'phone']
    list_per_page = 20
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('code', 'name', 'type', 'status')
        }),
        ('Alamat & Kontak', {
            'fields': ('address', 'city', 'province', 'postal_code', 'phone', 'email')
        }),
        ('Konfigurasi Stok & Harga', {
            'fields': ('stok_mode', 'use_special_pricing', 'price_multiplier', 'price_rounding')
        }),
        ('Pengaturan Pajak', {
            'fields': ('tax_rate', 'tax_inclusive', 'service_charge')
        }),
        ('Informasi Tambahan', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['created_by']


# ==================================================
# KODE BARANG (DENGAN EXPORT)
# ==================================================
@admin.register(KodeBarang)
class KodeBarangAdmin(admin.ModelAdmin):
    list_display = ['kode', 'nama', 'keterangan', 'created_at']
    search_fields = ['kode', 'nama']
    list_per_page = 20
    fieldsets = (
        ('Informasi Kode Barang', {
            'fields': ('kode', 'nama', 'keterangan')
        }),
    )
    
    actions = ['export_to_csv']
    
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="kode_barang.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Kode', 'Nama', 'Keterangan', 'Tanggal Dibuat'])
        
        for obj in queryset:
            writer.writerow([
                obj.kode,
                obj.nama,
                obj.keterangan,
                obj.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    
    export_to_csv.short_description = "Export ke CSV"


# ==================================================
# SUPPLIER
# ==================================================
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'created_at']
    search_fields = ['name', 'contact_person', 'phone']
    list_per_page = 20


# ==================================================
# CUSTOM AUTOCOMPLETE UNTUK STOCK ITEM
# ==================================================
class StockItemAutocomplete(admin.ModelAdmin):
    """Custom autocomplete untuk search di kode DAN nama"""
    
    def get_search_results(self, request, queryset, search_term):
        """Override untuk search berdasarkan kode ATAU nama sekaligus"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        if search_term:
            queryset = queryset.filter(
                Q(kode_barang__kode__icontains=search_term) | 
                Q(kode_barang__nama__icontains=search_term) |
                Q(name__icontains=search_term)
            )
        return queryset, use_distinct


# ==================================================
# STOCK ITEM
# ==================================================
@admin.register(StockItem)
class StockItemAdmin(StockItemAutocomplete):
    list_display = ['kode_display', 'name', 'unit', 'stock', 'min_stock', 'colored_stock_status', 'supplier_link']
    list_filter = ['unit', 'supplier', 'kode_barang']
    search_fields = ['kode_barang__kode', 'kode_barang__nama', 'name']
    list_per_page = 20
    autocomplete_fields = ['kode_barang', 'supplier']
    
    def kode_display(self, obj):
        if obj.kode_barang:
            return f"{obj.kode_barang.kode}"
        return "-"
    kode_display.short_description = "Kode Barang"
    kode_display.admin_order_field = 'kode_barang__kode'
    
    def colored_stock_status(self, obj):
        if obj.stock <= 0:
            color = 'red'
            status = 'Habis'
        elif obj.stock <= obj.min_stock:
            color = 'orange'
            status = 'Menipis'
        else:
            color = 'green'
            status = 'Aman'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    colored_stock_status.short_description = 'Status Stok'
    
    def supplier_link(self, obj):
        if obj.supplier:
            url = reverse('admin:core_supplier_change', args=[obj.supplier.id])
            return format_html('<a href="{}">{}</a>', url, obj.supplier.name)
        return "-"
    supplier_link.short_description = 'Supplier'


# ==================================================
# STOCK PURCHASE INLINE
# ==================================================
class StockPurchaseItemInline(admin.TabularInline):
    model = StockPurchaseItem
    extra = 1
    fields = ['kode_barang', 'cara_hitung', 'jumlah', 'harga_total', 'harga_unit', 'subtotal', 'markup_percent', 'markup_nominal', 'total_price']
    readonly_fields = ['harga_unit', 'subtotal', 'total_price']
    autocomplete_fields = ['kode_barang']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "kode_barang":
            kwargs["queryset"] = KodeBarang.objects.all().order_by('kode')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==================================================
# STOCK PURCHASE
# ==================================================
@admin.register(StockPurchase)
class StockPurchaseAdmin(admin.ModelAdmin):
    list_display = ['invoice_no', 'supplier_link', 'date', 'total_amount', 'created_by']
    list_filter = ['date', 'supplier']
    search_fields = ['invoice_no']
    inlines = [StockPurchaseItemInline]
    readonly_fields = ['total_amount']
    list_per_page = 20
    autocomplete_fields = ['supplier', 'created_by']
    
    def supplier_link(self, obj):
        if obj.supplier:
            url = reverse('admin:core_supplier_change', args=[obj.supplier.id])
            return format_html('<a href="{}">{}</a>', url, obj.supplier.name)
        return "-"
    supplier_link.short_description = 'Supplier'


# ==================================================
# MENU CATEGORY
# ==================================================
@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'menu_count']
    search_fields = ['name']
    
    def menu_count(self, obj):
        return obj.menu_set.count()
    menu_count.short_description = 'Jumlah Menu'


# ==================================================
# MENU INGREDIENT INLINE
# ==================================================
class MenuIngredientInline(admin.TabularInline):
    model = MenuIngredient
    extra = 1
    fields = ['stock_item', 'quantity_used', 'notes']
    autocomplete_fields = ['stock_item']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "stock_item":
            kwargs["queryset"] = StockItem.objects.all().order_by('kode_barang__kode')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==================================================
# MODIFIER INLINES
# ==================================================
class ModifierOptionInline(admin.TabularInline):
    model = ModifierOption
    extra = 2
    fields = ['name', 'price_addition', 'is_default', 'sort_order', 'stock_item', 'quantity_used']
    autocomplete_fields = ['stock_item']


class MenuModifierInline(admin.TabularInline):
    model = MenuModifier
    extra = 1
    fields = ['name', 'type', 'required', 'min_select', 'max_select', 'sort_order', 'is_active']


# ==================================================
# MENU
# ==================================================
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'total_modal', 'selling_price', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['code', 'name']
    inlines = [MenuIngredientInline, MenuModifierInline]
    readonly_fields = ['total_modal', 'selling_price']
    list_per_page = 20
    actions = ['make_available', 'make_unavailable']
    autocomplete_fields = ['category']
    
    def make_available(self, request, queryset):
        queryset.update(is_available=True)
    make_available.short_description = "Tandai tersedia"
    
    def make_unavailable(self, request, queryset):
        queryset.update(is_available=False)
    make_unavailable.short_description = "Tandai tidak tersedia"


# ==================================================
# ORDER ITEM INLINE
# ==================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['menu_name', 'quantity', 'price', 'subtotal']
    can_delete = False
    autocomplete_fields = ['menu']


# ==================================================
# ORDER
# ==================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'cashier', 'customer_name', 'order_date', 'total', 'payment_method', 'status']
    list_filter = ['status', 'payment_method', 'order_date']
    search_fields = ['order_no', 'customer_name']
    inlines = [OrderItemInline]
    readonly_fields = ['order_no', 'subtotal', 'tax', 'discount', 'total', 'change']
    list_per_page = 20
    autocomplete_fields = ['cashier']


# ==================================================
# USER PROFILE ADMIN
# ==================================================
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profil'
    fields = ['role', 'phone', 'photo', 'bio']
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__role']
    
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except Profile.DoesNotExist:
            return '-'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'


# Unregister User default, register ulang dengan custom
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ==================================================
# REGISTER MODIFIER ADMIN
# ==================================================
@admin.register(MenuModifier)
class MenuModifierAdmin(admin.ModelAdmin):
    list_display = ['name', 'menu', 'type', 'required', 'is_active']
    list_filter = ['type', 'required', 'is_active']
    search_fields = ['name', 'menu__name']
    inlines = [ModifierOptionInline]


@admin.register(ModifierOption)
class ModifierOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'modifier', 'price_addition', 'is_default']
    list_filter = ['is_default']
    search_fields = ['name', 'modifier__name']
    autocomplete_fields = ['modifier', 'stock_item']


@admin.register(OrderItemModifier)
class OrderItemModifierAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'modifier_name', 'option_name', 'price_addition']
    search_fields = ['order_item__menu_name', 'modifier_name', 'option_name']


# ==================================================
# SITE HEADER
# ==================================================
admin.site.site_header = "Mbayar POS Administration"
admin.site.site_title = "Mbayar POS Admin"
admin.site.index_title = "Dashboard Admin Mbayar POS"