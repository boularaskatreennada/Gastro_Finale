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
class EditReservationForm(forms.ModelForm):
    datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control', 'placeholder': 'Date and Time'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    class Meta:
        model = Reservation
        fields = [ 'datetime', 'number_of_people', 'phone']
        widgets = {
            #'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'placeholder': 'Date and Time'},format='%Y-%m-%dT%H:%M'),
            'number_of_people': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Number of People'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'restaurant': forms.Select(attrs={'class': 'form-select', 'placeholder': 'restaurant'}),
        }
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.initial['datetime'] = self.instance.datetime.strftime('%Y-%m-%dT%H:%M')
            # seed number_of_people
            self.initial['number_of_people'] = self.instance.number_of_people
            # seed phone
            self.initial['phone'] = self.instance.phone
            