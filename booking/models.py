from django.db import models
from django.conf import settings
from events.models import Event, Seat


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shipping_addresses"
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}"


class Booking(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    num_tickets = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booking_date = models.DateTimeField(auto_now_add=True)

    shipping_address = models.ForeignKey(
        ShippingAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    seats = models.ManyToManyField(Seat, related_name="bookings", blank=True)

    # ================= CASHFREE ONLY =================
    cashfree_order_id = models.CharField(max_length=100, blank=True, null=True)
    cashfree_payment_id = models.CharField(max_length=100, blank=True, null=True)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Booking #{self.id} - {self.event.name}"
