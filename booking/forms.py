# booking/forms.py

from django import forms
from .models import ShippingAddress
from .models import BookingContact

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'phone_number', 'street_address', 'city', 'state', 'zip_code', 'country','phone_number']

class BookingContactForm(forms.ModelForm):
    class Meta:
        model = BookingContact
        fields = ["full_name", "email", "phone_number"]