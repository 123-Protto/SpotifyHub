from django.urls import path
from .views import (
    book_event_view,
    select_seats_view,
    add_booking_contact_view,
    process_payment_view,
    payment_success_view,
    payment_failed_view,
    booking_detail_view,
    download_ticket,
    cashfree_webhook,   # ✅ IMPORT THE WEBHOOK VIEW
)

app_name = "booking"

urlpatterns = [
    path("book/<int:event_id>/", book_event_view, name="book_event"),
    path("select-seats/<int:booking_id>/", select_seats_view, name="select_seats"),
    path("contact/<int:booking_id>/", add_booking_contact_view, name="add_booking_contact"),
    path("payment/<int:booking_id>/", process_payment_view, name="process_payment"),
    path("payment/success/<int:booking_id>/", payment_success_view, name="payment_success"),
    path("payment/failed/<int:booking_id>/", payment_failed_view, name="payment_failed"),
    path("booking/<int:booking_id>/", booking_detail_view, name="booking_detail"),

    # 🎟️ DOWNLOAD TICKET
    path(
        "ticket/download/<uuid:ticket_id>/",
        download_ticket,
        name="download_ticket"
    ),

    # 💳 CASHFREE WEBHOOK
    path(
        "cashfree/webhook/",
        cashfree_webhook,
        name="cashfree_webhook"
    ),
]
