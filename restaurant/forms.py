from django import forms
from .models import *
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator


class ClientRegistrationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control inputField',
        'placeholder': 'Email'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control inputField',
            'placeholder': 'Username'
        })
        self.fields['phone'].widget.attrs.update({
            'class': 'form-control inputField',
            'placeholder': 'Phone'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control inputField',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control inputField',
            'placeholder': 'Confirm Password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'CLIENT'
        if commit:
            user.save()
            Client.objects.create(user=user)  # Ensure Client is created
        return user


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Restaurant name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'address': forms.Textarea(attrs={'class': 'text-area form-control', 'placeholder': 'Complete address'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control d-none', 'id': 'id_photo'}),
        }


User = get_user_model()

class EmployeeForm(forms.ModelForm):
    USER_TYPE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('SUPPLIER', 'Supplier'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

  
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Password',
            'autocomplete': 'new-password'
        })
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

   
    restaurant = forms.ModelChoiceField(
        queryset=Restaurant.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

   
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address', 'rows': 3})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'user_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        if self.instance.pk is None and 'first_name' in self.data and 'last_name' in self.data:
            first = self.data['first_name'].lower()
            last = self.data['last_name'].lower()
            self.instance.username = f"{first}.{last}"

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        
        if not self.instance.username:
            first = cleaned_data.get('first_name', '').lower()
            last = cleaned_data.get('last_name', '').lower()
            if first and last:
                cleaned_data['username'] = f"{first}.{last}"
                self.instance.username = cleaned_data['username']

       
        if user_type == 'MANAGER':
            if not cleaned_data.get('restaurant'):
                self.add_error('restaurant', 'This field is required for managers.')
            
            if not cleaned_data.get('status'):
                self.add_error('status', 'This field is required for managers.')
            
            restaurant = cleaned_data.get('restaurant')
            if restaurant:
                existing_manager = Manager.objects.filter(restaurant=restaurant).exclude(user=self.instance).first()
                if existing_manager:
                    self.add_error('restaurant', f'This restaurant is already managed by {existing_manager.user.get_full_name()}')
        
        
        elif user_type == 'SUPPLIER':
            if not cleaned_data.get('address'):
                self.add_error('address', 'This field is required for suppliers.')
        
       
        if not self.instance.pk and not cleaned_data.get('password'):
            self.add_error('password', 'Password is required for new users.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
      
        if not user.username:
            user.username = f"{user.first_name.lower()}.{user.last_name.lower()}"
        
        
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            
            
            if user.user_type == 'MANAGER':
                Manager.objects.update_or_create(
                    user=user,
                    defaults={
                        'restaurant': self.cleaned_data['restaurant'],
                        'status': self.cleaned_data['status']
                    }
                )
                Supplier.objects.filter(user=user).delete()
            
            
            elif user.user_type == 'SUPPLIER':
                Supplier.objects.update_or_create(
                    user=user,
                    defaults={
                        'address': self.cleaned_data['address']
                    }
                )
                Manager.objects.filter(user=user).delete()
        
        return user
    
ROLE_CHOICES_Employee = [
    ('chef', 'Chef'),
    ('server', 'Server'),
    ('delivery', 'Delivery Person'),
]

STATUS_CHOICES = EmployeeStatus.choices


class StaffEmployeeForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES_Employee,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        role = self.data.get('role') or self.initial.get('role')

        if role in ['chef', 'server', 'delivery']:
            self.fields['password'].required = True
            self.fields['status'].required = True






from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from restaurant.models import User

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
         
            
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def init(self, *args, **kwargs):
        super().init(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})