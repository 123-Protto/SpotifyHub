from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event
from store.models import Cart, CartItem

def events_list_view(request):
    category = request.GET.get("category")

    events = Event.objects.filter(is_active=True)

    if category:
        events = events.filter(category=category)

    return render(
        request,
        "events/events_list.html",
        {
            "events": events,
            "selected_category": category,
        }
    )



@login_required
def buy_ticket_now(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        event=event,
        defaults={"quantity": 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"Ticket for {event.name} added to cart.")
    return redirect("store:cart")
