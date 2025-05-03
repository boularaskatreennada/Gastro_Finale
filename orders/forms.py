from django import forms
from .models import Order

class OrderConfirmationForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['mode']
        widgets = {
            'mode': forms.Select(attrs={'class': 'form-control'})
        }
