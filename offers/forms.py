from django import forms
from .models import Offer

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = '__all__'
        exclude = ['uses', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Offer Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control text-area', 'placeholder': 'Description'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Discount %'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Promo Code'}),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'id': 'id_photo',
                'style': 'display:none;',
            }),
        }
