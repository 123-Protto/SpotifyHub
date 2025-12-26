# booking/views.py

import json
import uuid
import logging
import requests
from itertools import groupby
from operator import attrgetter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from twilio.rest import Client

from events.models import Event, Seat
from .models import Booking, ShippingAddress
from .forms import ShippingAddressForm

logger = logging.getLogger(__name__)

# -------------------------
# 1) BOOK EVENT
# -------------------------
@login_required
def book_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        try:
            num_tickets = int(request.POST.get("num_tickets", 1))
        except (ValueError, TypeError):
            messages.error(request, "Invalid number of tickets.")
            return redirect("booking:book_event", event_id=event.id)

        if num_tickets < 1:
            messages.error(request, "Number of tickets must be greater than zero.")
            return redirect("booking:book_event", event_id=event.id)

        booking = Booking.objects.create(
            user=request.user,
            event=event,
            num_tickets=num_tickets,
            total_price=event.price * num_tickets,
            payment_status="pending",
            is_paid=False,
        )

        messages.success(request, "Please select seats.")
        return redirect("booking:select_seats", booking_id=booking.id)

    return render(request, "booking/book_event.html", {"event": event})


# -------------------------
# 2) SELECT SEATS
# -------------------------
@login_required
def select_seats_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    event = booking.event

    if request.method == "POST":
        selected_seats = request.POST.getlist("selected_seats")
        if not selected_seats:
            messages.error(request, "Please select at least one seat.")
            return redirect("booking:select_seats", booking_id=booking.id)

        booking.seats.clear()
        for seat_id in selected_seats:
            seat = get_object_or_404(Seat, id=seat_id, event=event)
            booking.seats.add(seat)

        return redirect("booking:booking_detail", booking_id=booking.id)

    seats = Seat.objects.filter(event=event).order_by("section", "row_number")
    grouped = []
    for section, sec_group in groupby(seats, key=attrgetter("section")):
        rows = []
        for row, row_group in groupby(sec_group, key=attrgetter("row_number")):
            rows.append((row, list(row_group)))
        grouped.append((section, rows))

    return render(
        request,
        "booking/select_seats.html",
        {"booking": booking, "event": event, "seats_by_section_and_row": grouped},
    )


# -------------------------
# 3) ADD SHIPPING ADDRESS
# -------------------------
@login_required
def add_shipping_address_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if not booking.seats.exists():
        messages.warning(request, "Select seats first.")
        return redirect("booking:select_seats", booking_id=booking.id)

    address, _ = ShippingAddress.objects.get_or_create(
        user=request.user, defaults={"is_default": True}
    )

    if request.method == "POST":
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            booking.shipping_address = form.save()
            booking.save(update_fields=["shipping_address"])
            return redirect("booking:process_payment", booking_id=booking.id)
    else:
        form = ShippingAddressForm(instance=address)

    return render(
        request,
        "booking/add_shipping_address.html",
        {"booking": booking, "form": form},
    )


# -------------------------
# 4) PAYMENT PAGE (CASHFREE)
# -------------------------

@login_required
def process_payment_view(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user,
        payment_status="pending"
    )

    if booking.is_paid:
        return redirect("booking:payment_success", booking_id=booking.id)

    # Create Cashfree Order ID (TEMP, NOT SAVED)
    order_id = f"cf_booking_{uuid.uuid4().hex[:10]}"

    payload = {
        "order_id": order_id,
        "order_amount": float(booking.total_price),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(booking.user.id),
            "customer_email": booking.user.email,
            "customer_phone": (
                booking.shipping_address.phone_number
                if booking.shipping_address
                else "9999999999"
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
        timeout=10,
    )

    data = response.json()

    if response.status_code != 200 or "payment_session_id" not in data:
        messages.error(request, "Unable to initiate payment.")
        return redirect("booking:booking_detail", booking_id=booking.id)

    return render(
        request,
        "booking/payment_page.html",
        {
            "booking": booking,
            "payment_session_id": data["payment_session_id"],
            "mode": "sandbox",  # change to production later
        },
    )

# -------------------------
# 5) PAYMENT SUCCESS / FAILURE
# -------------------------
@login_required
def payment_success_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "booking/payment_success.html", {"booking": booking})


@login_required
def payment_failed_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "booking/payment_failed.html", {"booking": booking})


# -------------------------
# 6) CASHFREE WEBHOOK
# -------------------------
@csrf_exempt
@transaction.atomic
def cashfree_webhook_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        order_id = payload.get("order_id")
        status = payload.get("order_status")

        booking = Booking.objects.filter(cashfree_order_id=order_id).first()
        if not booking:
            return JsonResponse({"status": "ignored"})

        if status == "PAID":
            booking.payment_status = "successful"
            booking.is_paid = True
            booking.cashfree_payment_id = payload.get("cf_payment_id")
            booking.save()
            _send_confirmation_messages(booking)

        elif status in ("FAILED", "CANCELLED"):
            booking.payment_status = "failed"
            booking.is_paid = False
            booking.save()

        return JsonResponse({"status": "ok"})

    except Exception as e:
        logger.exception("Cashfree webhook error")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# -------------------------
# 7) BOOKING DETAIL
# -------------------------
@login_required
def booking_detail_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "booking/booking_detail.html", {"booking": booking})


# -------------------------
# 8) EMAIL + SMS
# -------------------------
def _send_confirmation_messages(booking):
    try:
        subject = f"Booking Confirmation - {booking.event.name}"
        html = render_to_string("booking/email_confirmation.html", {"booking": booking})
        text = strip_tags(html)
        send_mail(
            subject,
            text,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            html_message=html,
        )
    except Exception as e:
        logger.error("Email error: %s", e)

    if booking.shipping_address and booking.shipping_address.phone_number:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=booking.shipping_address.phone_number,
                from_=settings.TWILIO_PHONE_NUMBER,
                body=f"Your booking for {booking.event.name} is confirmed. ID: {booking.id}",
            )
        except Exception as e:
            logger.error("SMS error: %s", e)
