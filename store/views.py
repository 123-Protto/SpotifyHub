from decimal import Decimal
import json
import requests

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone

from .models import (
    Cart, CartItem, Product, Address,
    Order, OrderItem, OrderShipping
)
from .forms import AddressForm


# =====================================================
# SHOP & CART
# =====================================================
def shop_view(request):
    products = Product.objects.filter(is_active=True)
    return render(request, "store/shop.html", {"products": products})


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total_price = sum(item.sub_total() for item in cart_items)

    return render(request, "store/cart.html", {
        "cart_items": cart_items,
        "total_price": total_price
    })


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )
    if not created:
        item.quantity += 1
        item.save()

    messages.success(request, "Item added to cart")
    return redirect("store:cart")


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )
    cart_item.delete()
    messages.success(request, "Item removed from cart")
    return redirect("store:cart")


# =====================================================
# CHECKOUT
# =====================================================
@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    buy_now_product_id = request.GET.get("buy_now")

    # Store buy-now in session
    if buy_now_product_id:
        request.session["buy_now"] = buy_now_product_id
    else:
        request.session.pop("buy_now", None)

    if buy_now_product_id:
        product = get_object_or_404(Product, id=buy_now_product_id)
        cart_items = [{
            "product": product,
            "quantity": 1,
            "sub_total": product.price
        }]
        total_amount = product.price
    else:
        cart_items_qs = cart.items.all()
        if not cart_items_qs.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect("store:shop")

        cart_items = cart_items_qs
        total_amount = sum(item.sub_total() for item in cart_items_qs)

    address = Address.objects.filter(user=request.user).first()

    return render(request, "store/checkout.html", {
        "cart_items": cart_items,
        "total_amount": total_amount,
        "address": address,
        "buy_now": buy_now_product_id,
    })


@login_required
def add_address(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect("store:checkout")
    else:
        form = AddressForm()

    return render(request, "store/add_address_form.html", {"form": form})


# =====================================================
# CASHFREE CREATE ORDER
# =====================================================
@require_POST
@login_required
def create_cashfree_order(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = {}

    buy_now_product_id = data.get("buy_now") or request.session.get("buy_now")

    # Calculate total
    if buy_now_product_id:
        product = get_object_or_404(Product, id=buy_now_product_id)
        order_total = product.price
        order_items = [(product, 1)]
    else:
        cart_items = cart.items.all()
        if not cart_items.exists():
            return JsonResponse({"error": "No items to pay for"}, status=400)

        order_total = sum(item.sub_total() for item in cart_items)
        order_items = [(item.product, item.quantity) for item in cart_items]

    # Create order
    address = Address.objects.filter(user=request.user).first()

    order = Order.objects.create(
        user=request.user,
        address=address,
        total_amount=order_total,
        payment_status="PENDING",
        order_status="PENDING",
    )

    for product, qty in order_items:
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            price_at_purchase=product.price,
        )

    cashfree_order_id = f"store_{order.id}"

    payload = {
        "order_id": cashfree_order_id,
        "order_amount": float(order.total_amount),
        "order_currency": "INR",
        "order_meta": {
            "notify_url": f"{settings.CASHFREE_WEBHOOK_URL}"
        },
        "customer_details": {
            "customer_id": str(request.user.id),
            "customer_email": request.user.email,
            "customer_phone": "9876543210",
        },
    }

    headers = {
        "x-client-id": settings.CASHFREE_CLIENT_ID,
        "x-client-secret": settings.CASHFREE_CLIENT_SECRET,
        "x-api-version": "2022-09-01",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{settings.CASHFREE_BASE_URL}/orders",
        json=payload,
        headers=headers,
        timeout=15,
    )

    if response.status_code != 200:
        order.delete()
        return JsonResponse({"error": "Cashfree failed"}, status=400)

    order.payment_gateway_order_id = cashfree_order_id
    order.save(update_fields=["payment_gateway_order_id"])

    return JsonResponse({
        "payment_session_id": response.json()["payment_session_id"],
        "order_id": order.id,
    })


# =====================================================
# CASHFREE WEBHOOK (SAFE + IDEMPOTENT)
# =====================================================
@csrf_exempt
@require_POST
def cashfree_webhook(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if payload.get("type") != "PAYMENT_SUCCESS_WEBHOOK":
        return JsonResponse({"status": "ignored"})

    data = payload.get("data", {})
    order_id = data.get("order", {}).get("order_id")
    payment = data.get("payment", {})

    if payment.get("payment_status") != "SUCCESS":
        return JsonResponse({"status": "payment not successful"})

    try:
        order = Order.objects.get(payment_gateway_order_id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    # Prevent duplicate execution
    if order.payment_status == "COMPLETED":
        return JsonResponse({"status": "already processed"})

    with transaction.atomic():
        order.payment_status = "COMPLETED"
        order.order_status = "PROCESSING"
        order.payment_id = str(payment.get("cf_payment_id"))
        order.save(update_fields=[
            "payment_status",
            "order_status",
            "payment_id"
        ])

        # Create shipping snapshot once
        if order.address and not hasattr(order, "shipping"):
            addr = order.address
            OrderShipping.objects.create(
                order=order,
                full_name=addr.full_name,
                phone=addr.phone_number,
                address_line_1=addr.address_line_1,
                address_line_2=addr.address_line_2 or "",
                city=addr.city,
                state=addr.state,
                pincode=addr.postal_code,
            )

        CartItem.objects.filter(cart__user=order.user).delete()

    request.session.pop("buy_now", None)
    return JsonResponse({"status": "success"})


# =====================================================
# ORDERS
# =====================================================
@login_required
def my_orders(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )
    return render(request, "store/my_orders.html", {"orders": orders})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "store/order_confirmation.html", {"order": order})


@login_required
def buy_now(request, product_id):
    return redirect(f"/store/checkout/?buy_now={product_id}")


@login_required
def ajax_add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )
    if not created:
        item.quantity += 1
        item.save()

    return JsonResponse({
        "status": "success",
        "cart_count": cart.items.count()
    })


@login_required
@require_POST
def confirm_delivery(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
        order_status="SHIPPED"
    )

    order.order_status = "DELIVERED"
    order.save(update_fields=["order_status"])

    messages.success(request, "🎉 Delivery confirmed. Thank you!")
    return redirect("store:order_confirmation", order_id=order.id)

@login_required
def invoice_view(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
        payment_status="COMPLETED"
    )
    return render(request, "store/invoice.html", {"order": order})
