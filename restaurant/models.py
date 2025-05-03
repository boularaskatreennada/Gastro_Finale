from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
# restaurant/models.py
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError

class User(AbstractUser):
    USER_TYPES = (
        ('PDG', 'PDG'),
        ('MANAGER', 'Manager'),
        ('CHEF', 'Chef'),
        ('SERVER', 'Server'),
        ('DELIVERY', 'Delivery Person'),
        ('CLIENT', 'Client'),
        ('SUPPLIER', 'Supplier'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    phone = models.CharField(max_length=20)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="restaurant_user_groups",  
        related_query_name="restaurant_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="restaurant_user_permissions", 
        related_query_name="restaurant_user",
    )

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    image = models.ImageField(upload_to='restaurant_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class EmployeeStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    loyality_points = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

class Manager(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        null=False,
        blank=False,
    )
    created_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=EmployeeStatus.choices)
    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='manager')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant'],
                name='unique_restaurant_manager',
                condition=models.Q(status='active'),
                violation_error_message="This restaurant already has an active manager."
            )
        ]

    def clean(self):
        if self.status == 'active' and Manager.objects.filter(restaurant=self.restaurant, status='active').exclude(user=self.user).exists():
            raise ValidationError("This restaurant already has an active manager.")

class Chef(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    created_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=EmployeeStatus.choices)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

class Server(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    created_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=EmployeeStatus.choices)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

class DeliveryPerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=EmployeeStatus.choices)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

class Supplier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"