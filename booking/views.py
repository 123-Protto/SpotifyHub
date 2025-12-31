# booking/views.py

import json
import uuid
import logging
import requests
from itertools import groupby
from operator import attrgetter
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader   # ✅ REQUIRED

from events.models import Event, Seat
from .models import Booking, ShippingAddress, BookingContact, Ticket
from .forms import ShippingAddressForm, BookingContactForm
from .utils import generate_ticket_qr



logger = logging.getLogger(__name__)

# =====================================================
# 1) BOOK EVENT
# =====================================================
@login_required
def book_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        num_tickets = int(request.POST.get("num_tickets", 1))

        booking = Booking.objects.create(
            user=request.user,
            event=event,
            num_tickets=num_tickets,
            total_price=event.price * num_tickets,
            payment_status=Booking.PAYMENT_PENDING,
            is_paid=False,
        )

        return redirect("booking:select_seats", booking_id=booking.id)

    return render(request, "booking/book_event.html", {"event": event})


# =====================================================
# 2) SELECT SEATS
# =====================================================
@login_required
def select_seats_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    event = booking.event

    if request.method == "POST":
        seat_ids = request.POST.getlist("selected_seats")

        if not seat_ids:
            messages.error(request, "Select at least one seat")
            return redirect("booking:select_seats", booking_id=booking.id)

        booking.seats.clear()
        for sid in seat_ids:
            seat = get_object_or_404(Seat, id=sid, event=event)
            booking.seats.add(seat)

        return redirect("booking:add_booking_contact", booking_id=booking.id)

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
        {
            "booking": booking,
            "event": event,
            "seats_by_section_and_row": grouped,
        },
    )


# =====================================================
# 3) ADD CONTACT
# =====================================================
@login_required
def add_booking_contact_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    contact = BookingContact.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = BookingContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()

            booking.contact = contact
            booking.save(update_fields=["contact"])

            return redirect("booking:process_payment", booking_id=booking.id)
    else:
        form = BookingContactForm(instance=contact)

    return render(
        request,
        "booking/add_contact.html",
        {"form": form, "booking": booking},
    )


# =====================================================
# 4) PAYMENT PAGE (CASHFREE)
# =====================================================
@login_required
def process_payment_view(request, booking_id):
    # ✅ Fetch booking (any status)
    booking = Booking.objects.filter(
        id=booking_id,
        user=request.user
    ).first()

    if not booking:
        raise Http404

    # 🔁 If already paid, go to tickets instead of 404
    if booking.payment_status != Booking.PAYMENT_PENDING:
        return redirect("booking:booking_detail", booking_id=booking.id)

    if not booking.contact:
        return redirect("booking:add_booking_contact", booking_id=booking.id)

    # ✅ Ensure stable Cashfree order ID
    if not booking.cashfree_order_id:
        booking.cashfree_order_id = f"cf_booking_{uuid.uuid4().hex[:12]}"
        booking.save(update_fields=["cashfree_order_id"])

    payload = {
        "order_id": booking.cashfree_order_id,
        "order_amount": float(booking.total_price),
        "order_currency": "INR",
        "order_meta": {
            # 🔔 Backend webhook
            "notify_url": settings.CASHFREE_BOOKING_WEBHOOK_URL,

            # 🔁 Frontend redirect
            "return_url": request.build_absolute_uri(
                reverse("booking:booking_detail", args=[booking.id])
            ),
        },
        "customer_details": {
            "customer_id": str(request.user.id),
            "customer_name": booking.contact.full_name,
            "customer_email": booking.contact.email,
            "customer_phone": booking.contact.phone_number,
        },
    }

    headers = {
        "x-client-id": settings.CASHFREE_CLIENT_ID,
        "x-client-secret": settings.CASHFREE_CLIENT_SECRET,
        "x-api-version": "2022-09-01",
        "Content-Type": "application/json",
    }

    res = requests.post(
        f"{settings.CASHFREE_BASE_URL}/orders",
        json=payload,
        headers=headers,
        timeout=10,
    )

    data = res.json()

    if res.status_code != 200 or "payment_session_id" not in data:
        messages.error(request, "Payment initiation failed")
        return redirect("booking:booking_detail", booking_id=booking.id)

    return render(
        request,
        "booking/payment_page.html",
        {
            "booking": booking,
            "payment_session_id": data["payment_session_id"],
            "mode": "sandbox",
        },
    )
# =====================================================
# 5) CASHFREE WEBHOOK
# =====================================================
@csrf_exempt
@transaction.atomic
def cashfree_webhook(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        logger.error("Invalid webhook JSON")
        return JsonResponse({"status": "invalid json"}, status=400)

    event_type = payload.get("type")
    logger.info(f"Cashfree webhook received: {event_type}")

    # ✅ Allow dashboard test webhook
    if event_type == "TEST_WEBHOOK":
        return JsonResponse({"status": "ok"})

    # ✅ Correct success event
    if event_type != "PAYMENT_SUCCESS":
        return JsonResponse({"status": "ignored"})

    data = payload.get("data", {})
    order = data.get("order", {})
    payment = data.get("payment", {})

    if payment.get("payment_status") != "SUCCESS":
        return JsonResponse({"status": "payment not successful"})

    order_id = order.get("order_id")
    if not order_id:
        return JsonResponse({"status": "missing order id"}, status=400)

    booking = get_object_or_404(Booking, cashfree_order_id=order_id)

    # 🔁 Idempotency guard
    if booking.is_paid:
        return JsonResponse({"status": "already processed"})

    # ✅ Mark booking paid
    booking.is_paid = True
    booking.payment_status = Booking.PAYMENT_SUCCESSFUL
    booking.cashfree_payment_id = str(payment.get("cf_payment_id"))
    booking.save(update_fields=[
        "is_paid",
        "payment_status",
        "cashfree_payment_id",
    ])

    # 🎟️ Generate tickets safely (avoid duplicates)
    for seat in booking.seats.all():
        Ticket.objects.get_or_create(
            user=booking.user,
            event=booking.event,
            seat=seat,
            booking_ref=str(booking.id),
        )

    logger.info(f"Payment confirmed for booking {booking.id}")

    return JsonResponse({"status": "success"})



# =====================================================
# 6) BOOKING DETAIL
# =====================================================
@login_required
def booking_detail_view(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    tickets = Ticket.objects.filter(
        booking_ref=str(booking.id),
        user=request.user
    )

    return render(
        request,
        "booking/booking_detail.html",
        {
            "booking": booking,
            "tickets": tickets,
        }
    )


# =====================================================
# 7) DOWNLOAD TICKET (PDF + QR)
# =====================================================
@login_required
def download_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id, user=request.user)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 🎨 COLORS
    PRIMARY = (0.05, 0.2, 0.6)     # Deep blue
    LIGHT_BG = (0.95, 0.96, 0.98)  # Light background
    DARK = (0.1, 0.1, 0.1)

    # 📐 CARD DIMENSIONS
    card_x = 40
    card_y = 80
    card_width = width - 80
    card_height = height - 160

    # 🧾 CARD BACKGROUND
    p.setFillColorRGB(*LIGHT_BG)
    p.roundRect(card_x, card_y, card_width, card_height, 16, fill=1, stroke=0)

    # 🔵 HEADER BAR
    p.setFillColorRGB(*PRIMARY)
    p.roundRect(card_x, height - 140, card_width, 70, 16, fill=1, stroke=0)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, height - 110, "EVENT ENTRY TICKET")

    # 📝 TICKET DETAILS
    p.setFillColorRGB(*DARK)
    p.setFont("Helvetica", 12)

    text_x = card_x + 30
    text_y = height - 190
    line_gap = 24

    p.drawString(text_x, text_y, f"Event: {ticket.event.name}")
    text_y -= line_gap
    p.drawString(text_x, text_y, f"Seat: {ticket.seat.section} - Seat {ticket.seat.seat_number}")
    text_y -= line_gap
    p.drawString(text_x, text_y, f"Booking Ref: {ticket.booking_ref}")
    text_y -= line_gap
    p.drawString(text_x, text_y, f"Ticket ID: {ticket.ticket_id}")

    # 🧾 FOOTER NOTE
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(text_x, card_y + 40, "• This ticket is valid for one entry only")
    p.drawString(text_x, card_y + 25, "• Please carry a digital or printed copy")

    # 🔳 QR CODE (CENTERED)
    qr_buffer = generate_ticket_qr(ticket)
    qr_image = ImageReader(qr_buffer)

    qr_size = 160
    qr_x = card_x + card_width - qr_size - 50
    qr_y = card_y + (card_height - qr_size) / 2

    # QR BORDER
    p.roundRect(
        qr_x - 12,
        qr_y - 12,
        qr_size + 24,
        qr_size + 24,
        14,
        stroke=1,
        fill=0
    )

    p.drawImage(qr_image, qr_x, qr_y, qr_size, qr_size, mask="auto")

    # QR LABEL
    p.setFont("Helvetica-Oblique", 9)
    p.drawCentredString(qr_x + qr_size / 2, qr_y - 18, "SCAN AT ENTRY")

    # 🖨️ FINALIZE PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="ticket-{ticket.ticket_id}.pdf"'
    )
    return response



# =====================================================
# 8) QR SCAN ENDPOINT
# =====================================================
@csrf_exempt
def scan_ticket(request):
    ticket_id = request.POST.get("ticket_id")

    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)

    if ticket.is_used:
        return JsonResponse({"status": "INVALID"})

    ticket.is_used = True
    ticket.save(update_fields=["is_used"])

    return JsonResponse({
        "status": "VALID",
        "event": ticket.event.name,
        "seat": ticket.seat.seat_number,
    })


# =====================================================
# 9) PAYMENT RESULT PAGES
# =====================================================
@login_required
def payment_success_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "booking/payment_success.html", {"booking": booking})


@login_required
def payment_failed_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, "booking/payment_failed.html", {"booking": booking})
