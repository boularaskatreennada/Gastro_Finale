from django.db import models
from restaurant.models import Restaurant
from django.contrib.auth import get_user_model

User = get_user_model()

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('FOOD', 'Food Supplies'),
        ('DRINKS', 'Beverages'),
        ('EQUIPMENT', 'Equipment'),
        ('UTILITIES', 'Utilities'),
        ('SALARY', 'Salaries'),
        ('OTHER', 'Other'),
    ]
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    expense_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

