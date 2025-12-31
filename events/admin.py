from django.contrib import admin
from django.utils.html import format_html
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "date",
        "location",
        "price",
        "thumbnail_preview",
        "available_tickets",
        "is_active",
    )

    def thumbnail_preview(self, obj):
        try:
            if obj.image and hasattr(obj.image, "url"):
                return format_html(
                    '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:6px;" />',
                    obj.image.url
                )
        except Exception:
            pass
        return "—"

    thumbnail_preview.short_description = "Thumbnail"
