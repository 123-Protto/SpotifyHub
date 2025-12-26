from django.db import models


class Event(models.Model):
    CATEGORY_CHOICES = [
        ("cricket", "Cricket"),
        ("football", "Football"),
        ("basketball", "Basketball"),
        ("volleyball", "Volleyball"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_tickets = models.IntegerField(default=0)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="other"
    )

    image = models.ImageField(
        upload_to="events/",
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Seat(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="seats"
    )
    section = models.CharField(max_length=50, default="Standard")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    row_number = models.CharField(max_length=5)
    seat_number = models.IntegerField()
    is_sold = models.BooleanField(default=False)

    class Meta:
        unique_together = ("event", "section", "row_number", "seat_number")
        ordering = ["section", "row_number", "seat_number"]
    
    def __str__(self):
        return f"{self.event.name} - {self.section} Row {self.row_number} Seat {self.seat_number}"
