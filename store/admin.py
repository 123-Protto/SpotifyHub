from django.contrib import admin
from .models import Product, Order, OrderItem, Address, Cart, CartItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'postal_code')
    search_fields = ('user__username', 'full_name', 'city')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product', 'event']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'order_status', 'payment_status', 'created_at')
    list_filter = ('order_status', 'payment_status', 'created_at')
    search_fields = ('user__username', 'id', 'payment_gateway_order_id')
    inlines = [OrderItemInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'event', 'quantity')
    search_fields = ('cart__user__username', 'product__name', 'event__title')
    list_filter = ('cart',)