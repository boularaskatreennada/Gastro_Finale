# forms.py
from django import forms
from .models import Reservation, Restaurant

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['restaurant', 'datetime', 'number_of_people', 'phone']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'placeholder': 'Date and Time'}),
            'number_of_people': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Number of People'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'restaurant': forms.Select(attrs={'class': 'form-select', 'placeholder': 'restaurant'}),
        }
