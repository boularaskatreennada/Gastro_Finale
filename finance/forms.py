from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'description', 'category', 'expense_date']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date' ,'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}), 
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

