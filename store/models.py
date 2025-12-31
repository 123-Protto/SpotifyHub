from django.db import models
from django.conf import settings
from decimal import Decimal
from events.models import Event

User = settings.AUTH_USER_MODEL


# ============================================================
# BOOKING (STORE LEVEL SUMMARY)
# ============================================================
class Booking(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="store_bookings"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} by {self.user}"


# ============================================================
# PRODUCT
# ============================================================
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to="products/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ============================================================
# ADDRESS
# ============================================================
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(
        max_length=255, blank=True, null=True
    )
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.full_name}, {self.city}"


# ============================================================
# CART
# ============================================================
class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user}"


# ============================================================
# CART ITEM
# ============================================================
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        if self.product:
            item_name = self.product.name
        elif self.event:
            item_name = self.event.name
        else:
            item_name = "Unknown item"
        return f"{self.quantity} x {item_name}"

    def sub_total(self):
        if self.product:
            return self.product.price * self.quantity
        if self.event:
            return self.event.price * self.quantity
        return Decimal("0.00")

    def clean(self):
        """
        Ensure only one of product or event is set
        """
        if self.product and self.event:
            raise ValueError("CartItem cannot have both product and event.")
        if not self.product and not self.event:
            raise ValueError("CartItem must have either product or event.")


# ============================================================
# ORDER
# ============================================================
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ Order lifecycle
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="PENDING"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="PENDING"
    )

    # ✅ Money
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # ✅ Payment gateway refs
    payment_gateway_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )

    payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # ✅ Delivery confirmation (customer-side)
    delivered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Order #{self.id}"

    # ✅ Safe total calculation
    def calculate_total_amount(self):
        total = sum(
            item.sub_total() for item in self.items.all()
        )
        self.total_amount = total
        self.save(update_fields=["total_amount"])


# ============================================================
# ORDER ITEM
# ============================================================
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        if self.product:
            item_name = self.product.name
        elif self.event:
            item_name = self.event.name
        else:
            item_name = "Unknown item"
        return f"{self.quantity} x {item_name} (Order #{self.order.id})"

    def sub_total(self):
        return self.price_at_purchase * self.quantity

class OrderShipping(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="shipping"
    )

    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    # Live tracking (optional – future use)
    courier_name = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipping for Order #{self.order.id}"
