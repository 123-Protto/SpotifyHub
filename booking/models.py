import uuid
from django.db import models
from django.conf import settings
from events.models import Event, Seat
from django.core.validators import RegexValidator


User = settings.AUTH_USER_MODEL

class BookingContact(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="booking_contacts"
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"



# ============================================================
# SHIPPING ADDRESS
# ============================================================
class ShippingAddress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shipping_addresses"
    )

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=10, blank=True, null=True
    )

    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name}, {self.city}"


# ============================================================
# BOOKING
# ============================================================
class Booking(models.Model):
    PAYMENT_PENDING = "pending"
    PAYMENT_SUCCESSFUL = "successful"
    PAYMENT_FAILED = "failed"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_SUCCESSFUL, "Successful"),
        (PAYMENT_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    num_tickets = models.PositiveIntegerField(default=1)

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    booking_date = models.DateTimeField(auto_now_add=True)

    shipping_address = models.ForeignKey(
        ShippingAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )

    seats = models.ManyToManyField(
        Seat,
        related_name="bookings",
        blank=True
    )
    contact = models.ForeignKey(
        BookingContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


    # ================= CASHFREE PAYMENT =================
    cashfree_order_id = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )
    cashfree_payment_id = models.CharField(
        max_length=100, blank=True, null=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING
    )

    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-booking_date"]
        indexes = [
            models.Index(fields=["cashfree_order_id"]),
            models.Index(fields=["payment_status"]),
        ]

    def __str__(self):
        return f"Booking #{self.id} - {self.event}"

    def mark_as_paid(self, payment_id: str):
        """Mark booking as paid after successful Cashfree payment"""
        self.cashfree_payment_id = payment_id
        self.payment_status = self.PAYMENT_SUCCESSFUL
        self.is_paid = True
        self.save(update_fields=[
            "cashfree_payment_id",
            "payment_status",
            "is_paid"
        ])
class Ticket(models.Model):
    ticket_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    seat = models.ForeignKey(
        Seat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    booking_ref = models.CharField(max_length=50)
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.ticket_id} - {self.event.name}"