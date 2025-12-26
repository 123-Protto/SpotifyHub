from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.events_list_view, name="events_list"),
    path(
        "buy/<int:event_id>/",
        views.buy_ticket_now,
        name="buy_ticket_now"
    ),
]
