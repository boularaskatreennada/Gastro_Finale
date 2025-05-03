from django.contrib import admin
from .models import MainMenu, Dish, Ingredient, DishIngredient, DailyMenu, DailyMenuDish

admin.site.register(MainMenu)
admin.site.register(Dish)
admin.site.register(Ingredient)
admin.site.register(DishIngredient)
admin.site.register(DailyMenu)
admin.site.register(DailyMenuDish)
