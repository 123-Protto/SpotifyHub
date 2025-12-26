# rural_sports/store/forms.py

from django import forms
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country', 'phone_number']

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name',
            'phone_number',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postal_code',
            'country'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2 (Optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        }