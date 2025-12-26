# booking/forms.py

from django import forms
from .models import ShippingAddress

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'phone_number', 'street_address', 'city', 'state', 'zip_code', 'country','phone_number']