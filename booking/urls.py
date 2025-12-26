from django.urls import path
from .views import (
    book_event_view,
    select_seats_view,
    add_shipping_address_view,
    process_payment_view,
    payment_success_view,
    payment_failed_view,
    booking_detail_view,
    cashfree_webhook_view,
)

app_name = "booking"

urlpatterns = [
    # =====================
    # BOOKING FLOW
    # =====================
    path("book/<int:event_id>/", book_event_view, name="book_event"),
    path("select-seats/<int:booking_id>/", select_seats_view, name="select_seats"),
    path(
        "shipping/<int:booking_id>/",
        add_shipping_address_view,
        name="add_shipping_address",
    ),

    # =====================
    # PAYMENT (CASHFREE)
    # =====================
    path(
        "payment/<int:booking_id>/",
        process_payment_view,
        name="process_payment",
    ),

    # =====================
    # PAYMENT RESULT PAGES
    # =====================
    path(
        "payment/success/<int:booking_id>/",
        payment_success_view,
        name="payment_success",
    ),
    path(
        "payment/failed/<int:booking_id>/",
        payment_failed_view,
        name="payment_failed",
    ),

    # =====================
    # BOOKING DETAILS
    # =====================
    path(
        "booking/<int:booking_id>/",
        booking_detail_view,
        name="booking_detail",
    ),

    # =====================
    # CASHFREE WEBHOOK
    # =====================
    path(
        "payment/webhook/cashfree/",
        cashfree_webhook_view,
        name="cashfree_webhook",
    ),
]
