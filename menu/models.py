from django.db import models
from restaurant.models import Restaurant
from decimal import Decimal
from offers.models import Offer, OfferStatus 

class MainMenu(models.Model):
    category = models.CharField(max_length=100)

    def __str__(self):
        return self.category

class Dish(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='dishes/')
    menu = models.ForeignKey(MainMenu, on_delete=models.CASCADE)

class Ingredient(models.Model):

    CATEGORY_CHOICES = [
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('dairy', 'Dairy'),
        ('meat', 'Meat'),
        ('seafood', 'Seafood'),
        ('grains', 'Grains'),
        ('spices', 'Spices'),
        ('oils', 'Oils'),
        ('nuts', 'Nuts'),
        ('herbs', 'Herbs'),
        ('other', 'Other'),
    ]

    UNIT_CHOICES = [
        ('kg', 'Kilogram (kg)'),
        ('g', 'Gram (g)'),
        ('L', 'Liter (L)'),
        ('ml', 'Milliliter (ml)'),
        ('pc', 'Piece (pc)'),
        ('tsp', 'Teaspoon (tsp)'),
        ('tbsp', 'Tablespoon (tbsp)'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='g'
    )
    price_per_unit = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

# models.py
class DishIngredient(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.CharField(
        max_length=10,
        choices=Ingredient.UNIT_CHOICES, 
        default='g'
    )

    class Meta:
        unique_together = ('dish', 'ingredient')


class DailyMenu(models.Model):
    date = models.DateField()
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

class DailyMenuDish(models.Model):
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    initial_quantity = models.PositiveIntegerField(default=1)
    current_quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('menu', 'dish')

class ShoppingList(models.Model):
    menu = models.OneToOneField(DailyMenu, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

# models.py
class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    required_quantity = models.FloatField()
    unit = models.CharField(max_length=10, choices=Ingredient.UNIT_CHOICES)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):

      
      self.total_price = self.ingredient.price_per_unit * Decimal(str(self.required_quantity))
      super().save(*args, **kwargs)