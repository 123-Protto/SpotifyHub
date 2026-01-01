# booking/forms.py

from django import forms
from .models import ShippingAddress
from .models import BookingContact
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be exactly 10 digits."
)

class ShippingAddressForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=10,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            "type": "tel",
            "maxlength": "10",
            "inputmode": "numeric",
            "placeholder": "Enter 10-digit phone number"
        })
    )

    class Meta:
        model = ShippingAddress
        fields = [
            'full_name',
            'phone_number',
            'street_address',
            'city',
            'state',
            'zip_code',
            'country'
        ]

class BookingContactForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=10,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            "type": "tel",
            "maxlength": "10",
            "inputmode": "numeric",
            "placeholder": "Enter 10-digit phone number"
        })
    )

    class Meta:
        model = BookingContact
        fields = ["full_name", "email", "phone_number"]
