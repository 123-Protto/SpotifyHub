from django.contrib import admin
from .models import (
    Product,
    Order,
    OrderItem,
    Address,
    Cart,
    CartItem,
    OrderShipping,
)

# =====================================================
# PRODUCT
# =====================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


# =====================================================
# ADDRESS
# =====================================================
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "postal_code")
    search_fields = ("user__username", "full_name", "city")


# =====================================================
# ORDER ITEM INLINE (READONLY)
# =====================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "event", "quantity", "price_at_purchase")
    can_delete = False


# =====================================================
# SHIPPING INLINE
# =====================================================
class OrderShippingInline(admin.StackedInline):
    model = OrderShipping
    extra = 0
    max_num = 1


# =====================================================
# ORDER
# =====================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_amount",
        "order_status",
        "payment_status",
        "created_at",
    )
    list_filter = ("order_status", "payment_status", "created_at")
    search_fields = (
        "id",
        "user__username",
        "user__email",
        "payment_gateway_order_id",
    )
    ordering = ("-created_at",)

    inlines = [OrderItemInline, OrderShippingInline]

    actions = [
        "mark_as_processing",
        "mark_as_shipped",
        "mark_as_delivered",
    ]

    # ---------- ADMIN ACTIONS ----------
    @admin.action(description="Mark selected orders as PROCESSING")
    def mark_as_processing(self, request, queryset):
        queryset.update(order_status="PROCESSING")

    @admin.action(description="Mark selected orders as SHIPPED")
    def mark_as_shipped(self, request, queryset):
        queryset.update(order_status="SHIPPED")

    @admin.action(description="Mark selected orders as DELIVERED")
    def mark_as_delivered(self, request, queryset):
        queryset.update(order_status="DELIVERED")


# =====================================================
# CART
# =====================================================
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    search_fields = ("user__username",)


# =====================================================
# CART ITEM
# =====================================================
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "event", "quantity")
    search_fields = (
        "cart__user__username",
        "product__name",
        "event__name",
    )
    list_filter = ("cart",)
