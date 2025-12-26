from django.contrib import admin
from django.utils.html import format_html
from .models import Event, Seat


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "date",
        "location",
        "price",
        "image_preview",
        "available_tickets",
        "is_active",
    )

    list_filter = ("category", "is_active", "date")
    search_fields = ("name", "location")
    ordering = ("date",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" '
                'style="object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return "No Image"

    image_preview.short_description = "Thumbnail"


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "section",
        "row_number",
        "seat_number",
        "is_sold",
    )
    list_filter = ("section", "is_sold")
