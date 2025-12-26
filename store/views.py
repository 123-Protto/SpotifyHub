from decimal import Decimal
import json
import uuid
import requests

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Cart, CartItem, Product, Address, Order, OrderItem
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

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if not created:
        cart_item.quantity += 1
    cart_item.save()

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
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("store:shop")

    order_items = []
    total_amount = Decimal("0.00")

    for item in cart_items:
        line_total = item.sub_total()
        total_amount += line_total

        order_items.append({
            "name": item.product.name,
            "qty": item.quantity,
            "total": line_total
        })

    address = Address.objects.filter(user=request.user).first()

    return render(request, "store/checkout.html", {
        "order_items": order_items,
        "total_amount": total_amount,
        "address": address,
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
# 🔥 CASHFREE CREATE ORDER (FIXED)
# =====================================================
@require_POST
@login_required
def create_cashfree_order(request):
    try:
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        cart_items = cart.items.select_related("product")

        if not cart_items.exists():
            return JsonResponse({"error": "Cart empty"}, status=400)

        total_amount = sum(item.sub_total() for item in cart_items)

        if total_amount <= 0:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        order_id = f"store_{uuid.uuid4().hex[:12]}"

        payload = {
            "order_id": order_id,
            "order_amount": float(total_amount),
            "order_currency": "INR",
            "customer_details": {
                "customer_id": str(user.id),
                "customer_email": user.email or "test@example.com",

                # ✅ MUST be realistic
                "customer_phone": (
                    user.address.phone
                    if hasattr(user, "address") and user.address.phone
                    else "9876543210"
                ),
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

        data = response.json()

        # 🔥 IMPORTANT DEBUG (keep while testing)
        print("🟡 Cashfree status:", response.status_code)
        print("🟡 Cashfree response:", data)

        if response.status_code not in (200, 201):
            return JsonResponse(
                {"error": "Cashfree API error", "details": data},
                status=400
            )

        if "payment_session_id" not in data:
            return JsonResponse(
                {"error": "Missing payment_session_id", "details": data},
                status=400
            )

        return JsonResponse({
            "order_id": order_id,
            "payment_session_id": data["payment_session_id"]
        })

    except Exception as e:
        print("❌ Cashfree Exception:", str(e))
        return JsonResponse({"error": "Server error"}, status=500)



# =====================================================
# CASHFREE WEBHOOK
# =====================================================
@csrf_exempt
@transaction.atomic
def cashfree_webhook(request):
    payload = json.loads(request.body)

    if payload.get("order_status") != "PAID":
        return JsonResponse({"status": "ignored"})

    user_id = payload["customer_details"]["customer_id"]
    order_id = payload["order_id"]

    cart = Cart.objects.get(user_id=user_id)
    cart_items = CartItem.objects.filter(cart=cart)

    order = Order.objects.create(
        user_id=user_id,
        total_amount=Decimal(payload["order_amount"]),
        payment_status="COMPLETED",
        payment_id=payload.get("cf_payment_id"),
        payment_gateway_order_id=order_id,
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price_at_purchase=item.product.price,
        )

    cart_items.delete()
    return JsonResponse({"status": "success"})


# =====================================================
# ORDERS
# =====================================================
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "store/order_confirmation.html", {"order": order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/my_orders.html", {"orders": orders})


@login_required
def buy_now(request, product_id):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)

    CartItem.objects.filter(cart=cart).delete()
    CartItem.objects.create(cart=cart, product=product, quantity=1)

    return redirect("store:checkout")


@login_required
def ajax_add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product
    )

    if not created:
        item.quantity += 1
        item.save()

    cart_count = cart.items.count()

    return JsonResponse({
        "status": "success",
        "cart_count": cart_count
    })
