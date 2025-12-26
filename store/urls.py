from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    # SHOP
    path("shop/", views.shop_view, name="shop"),
    path("cart/", views.cart_view, name="cart"),
    path("checkout/", views.checkout, name="checkout"),

    # CART ACTIONS
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove-from-cart/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("buy_now/<int:product_id>/", views.buy_now, name="buy_now"),

    # ADDRESS
    path("add-address/", views.add_address, name="add_address"),

    # 🔥 CASHFREE (THIS WAS MISSING)
    path(
        "cashfree/create-order/",
        views.create_cashfree_order,
        name="create_cashfree_order",
    ),

    # WEBHOOK
    path(
        "cashfree/webhook/",
        views.cashfree_webhook,
        name="cashfree_webhook",
    ),

    # ORDERS
    path("order-confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path("my-orders/", views.my_orders, name="my_orders"),

    path("cart/add/<int:product_id>/", views.ajax_add_to_cart, name="ajax_add_to_cart"),

]
