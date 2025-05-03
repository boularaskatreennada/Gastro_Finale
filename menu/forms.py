from django import forms
from .models import DailyMenu, DailyMenuDish, Dish, DishIngredient, Ingredient, MainMenu


class MainMenuForm(forms.ModelForm):
    class Meta:
        model = MainMenu
        fields = ['category']
        widgets = {
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'})
        }

class DishForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=MainMenu.objects.all(),
        label="Category",
        empty_label="Select a category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Dish
        fields = ['name', 'description', 'price', 'image']  # exclude 'menu' here
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dish name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Recipe description', 'id': 'desc'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control d-none', 'id': 'id_photo'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing Dish, initialize category field with the related menu
        if self.instance and self.instance.pk:
            self.fields['category'].initial = self.instance.menu



class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'category', 'unit', 'price_per_unit']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingredient name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            })
        }


class DishIngredientForm(forms.ModelForm):
    class Meta:
        model = DishIngredient
        fields = ['ingredient', 'quantity', 'unit']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ingredient'].queryset = Ingredient.objects.all()
        self.fields['ingredient'].widget.attrs.update({'class': 'form-control ingredient-select'})
        self.fields['quantity'].widget.attrs.update({'class': 'form-control'})
        self.fields['unit'].widget.attrs.update({'class': 'form-control'})




