from collections import defaultdict

from django.utils import timezone
import json
from django import forms
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from finance.models import Expense
from orders.models import Order, OrderDish
from .models import *
from restaurant.models import *
from .forms import *
from django.forms import modelformset_factory
from restaurant.decorators import *  
from django.contrib import messages
from datetime import date, datetime
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@chef_required
def recipes_list(request):
    # Récupère tous les plats
    dishes = Dish.objects.prefetch_related('dishingredient_set__ingredient').all()

    return render(request, 'chef/recipie.html', {
        'dishes': dishes,
    })

@pdg_required
def menu_view(request):
    categories = MainMenu.objects.all()
    selected_category_id = request.GET.get('category')
    
    if selected_category_id == 'all':
        dishes = Dish.objects.all()
    elif selected_category_id:
        dishes = Dish.objects.filter(menu_id=selected_category_id)
    else:
        dishes = Dish.objects.all()
  
    if request.method == "POST":
        new_category = request.POST.get("category")
        if new_category:
            MainMenu.objects.create(category=new_category)
            return redirect(f"{request.path}?category=all")

    context = {
        'categories': categories,
        'selected_category_id': selected_category_id,
        'dishes': dishes,
    }
    return render(request, 'pdg/menu.html', context)
DishIngredientFormSet = forms.modelformset_factory(
    DishIngredient,
    form=DishIngredientForm,
    extra=2,
    can_delete=True
)



@pdg_required
def add_plate(request):
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            dish = form.save(commit=False)
            dish.menu = form.cleaned_data['category']
            dish.save()

            # Clear existing ingredients if any (for edit case)
            DishIngredient.objects.filter(dish=dish).delete()

            # Process ingredients data sent as JSON string
            import json
            ingredients_data = request.POST.get('ingredients_data')
            if ingredients_data:
                try:
                    ingredients_list = json.loads(ingredients_data)
                    for item in ingredients_list:
                        ing_id = item.get('id')
                        qty = item.get('quantity')
                        unit = item.get('unit')
                        if ing_id and qty:
                            ingredient = Ingredient.objects.get(id=ing_id)
                            DishIngredient.objects.create(
                                dish=dish,
                                ingredient=ingredient,
                                quantity=qty,
                                unit=unit or ingredient.unit
                            )
                except Exception as e:
                    messages.error(request, f"Error processing ingredients: {e}")

            messages.success(request, "Dish added successfully.")
            return redirect('menu')
        else:
            messages.error(request, "Please correct the errors.")
    else:
        form = DishForm()

    # Group ingredients by category
    ingredients_by_category = defaultdict(list)
    for ingredient in Ingredient.objects.all().order_by('name'):
        ingredients_by_category[ingredient.category].append(ingredient)

    context = {
        'form': form,
        'ingredients_by_category': dict(ingredients_by_category),
        'ingredient_categories': Ingredient.CATEGORY_CHOICES,
        'edit_mode': False,
    }
    return render(request, 'pdg/addPlate.html', context)


@pdg_required
def edit_plate(request, pk):
    dish = get_object_or_404(Dish, id=pk)

    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            dish = form.save(commit=False)
            dish.menu = form.cleaned_data['category']
            dish.save()

            # Clear existing DishIngredients
            DishIngredient.objects.filter(dish=dish).delete()

            # Process ingredients
            ingredients_data = request.POST.get('ingredients_data')
            if ingredients_data:
                try:
                    ingredients_list = json.loads(ingredients_data)
                    for item in ingredients_list:
                        ing_id = item.get('id')
                        qty = item.get('quantity')
                        unit = item.get('unit')
                        if ing_id and qty:
                            ingredient = Ingredient.objects.get(id=ing_id)
                            DishIngredient.objects.create(
                                dish=dish,
                                ingredient=ingredient,
                                quantity=qty,
                                unit=unit or ingredient.unit
                            )
                except Exception as e:
                    messages.error(request, f"Error processing ingredients: {e}")

            messages.success(request, "Dish updated successfully.")
            return redirect('menu')
        else:
            messages.error(request, "Please correct the errors.")
    else:
        form = DishForm(instance=dish)

    # Ingredients grouped by category
    ingredients_by_category = defaultdict(list)
    all_ingredients = Ingredient.objects.all().order_by('name')
    for ingredient in all_ingredients:
        ingredients_by_category[ingredient.category].append(ingredient)

    # Get existing dish ingredients and create a dictionary for easy lookup
    dish_ingredients = DishIngredient.objects.filter(dish=dish)
    selected_ingredients = {
        di.ingredient.id: {
            'quantity': di.quantity,
            'unit': di.unit
        } for di in dish_ingredients
    }

    context = {
        'form': form,
        'ingredients_by_category': dict(ingredients_by_category),
        'ingredient_categories': Ingredient.CATEGORY_CHOICES,
        'edit_mode': True,
        'dish': dish,
        'selected_ingredients': selected_ingredients,
    }
    return render(request, 'pdg/addPlate.html', context)

@pdg_required
def delete_plate(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    dish.delete()
    messages.success(request, "Dish deleted successfully.")
    return redirect('menu')




def ingredients_view(request, pk=None):
    category_filter = request.GET.get('category', 'all')
    if category_filter != 'all':
        ingredients = Ingredient.objects.filter(category=category_filter).order_by('name')
    else:
        ingredients = Ingredient.objects.all().order_by('name')
    
    ingredient = None
    is_editing = False
    
    if pk:
        ingredient = get_object_or_404(Ingredient, pk=pk)
        is_editing = True

    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ingredient {'updated' if is_editing else 'added'} successfully!")
            return redirect('ingredients')
    else:
        form = IngredientForm(instance=ingredient)
    
    context = {
        'ingredients': ingredients,
        'form': form,
        'is_editing': is_editing,
        'current_ingredient': ingredient,
        'category_choices': Ingredient.CATEGORY_CHOICES
    }
    return render(request, 'pdg/ingredients.html', context)


@pdg_required
def delete_ingredient(request, pk):
    get_object_or_404(Ingredient, pk=pk).delete()
    return redirect('ingredients')

@pdg_required
def add_category(request):
    form = MainMenuForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('categories')
    return render(request, 'pdg/addCategory.html', {'form': form})

@pdg_required
def edit_category(request, pk):
    instance = get_object_or_404(MainMenu, pk=pk)
    form = MainMenuForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect('categories')
    return render(request, 'pdg/addCategory.html', {'form': form})

@pdg_required
def delete_category(request, pk):
    get_object_or_404(MainMenu, pk=pk).delete()
    return redirect('menu')























































@manager_required
def manager_daily_menu(request):
    """Page principale du manager pour gérer son menu"""
    main_menus = MainMenu.objects.all()
    return render(request, 'manager/menu.html', {'main_menus': main_menus})

@manager_required
def get_dishes_by_category(request):
    print("the function is working")
    category_id = request.GET.get('category_id')
    print("Category ID received:", category_id)
    
    if category_id:
        dishes = Dish.objects.filter(menu_id=category_id)
        print("Dishes found:", dishes.count())

        dishes_data = []
        for dish in dishes:
            dishes_data.append({
                'id': dish.id,
                'name': dish.name,
                'price': str(dish.price),  # convert Decimal to str for JSON
                'image_url': dish.image.url if dish.image else '',  # avoid errors if no image
            })

        return JsonResponse({'dishes': dishes_data})
    else:
        return JsonResponse({'dishes': []})
    
@manager_required
def get_daily_menu(request):
    """Récupérer tous les plats du menu du jour (AJAX)"""
    manager = Manager.objects.get(user=request.user)
    restaurant = manager.restaurant
    today = date.today()

    daily_menu, created = DailyMenu.objects.get_or_create(date=today, restaurant=restaurant)
    dishes = DailyMenuDish.objects.filter(menu=daily_menu)
    
    dishes_data = []
    for dish in dishes:
        dishes_data.append({
            'id': dish.id,
            'name': dish.dish.name,
            'initial_quantity': dish.initial_quantity,
            'current_quantity': dish.current_quantity,
        })
    
    return JsonResponse({'menu_dishes': dishes_data})

@csrf_exempt
@manager_required
def add_dish_to_daily_menu(request):
    """Ajouter un plat au menu du jour"""
    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        quantity = int(request.POST.get('quantity'))

        manager = Manager.objects.get(user=request.user)
        restaurant = manager.restaurant
        today = date.today()

        daily_menu, created = DailyMenu.objects.get_or_create(date=today, restaurant=restaurant)
        dish = get_object_or_404(Dish, id=dish_id)

        daily_menu_dish, created = DailyMenuDish.objects.get_or_create(
            menu=daily_menu,
            dish=dish,
            defaults={'initial_quantity': quantity, 'current_quantity': quantity}
        )
        
        if not created:
            # Si déjà existant, on augmente juste la quantité
            daily_menu_dish.initial_quantity += quantity
            daily_menu_dish.current_quantity += quantity
            daily_menu_dish.save()

        return JsonResponse({'success': True})

@csrf_exempt
@manager_required
def remove_dish_from_daily_menu(request, daily_menu_dish_id):
    """Supprimer un plat du menu du jour"""
    if request.method == 'POST':
        dish_entry = get_object_or_404(DailyMenuDish, id=daily_menu_dish_id)
        dish_entry.delete()
        return JsonResponse({'success': True})


















@manager_required
def generate_shopping_list(request):
    """Générer dynamiquement la liste d'achats basée sur le menu du jour"""
    manager = Manager.objects.get(user=request.user)
    restaurant = manager.restaurant

    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    daily_menu, _ = DailyMenu.objects.get_or_create(date=selected_date, restaurant=restaurant)

    shopping_list, _ = ShoppingList.objects.get_or_create(menu=daily_menu)

    ShoppingListItem.objects.filter(shopping_list=shopping_list).delete()

    dish_entries = DailyMenuDish.objects.filter(menu=daily_menu)

    ingredient_quantities = {}

    for entry in dish_entries:
        dish_ingredients = DishIngredient.objects.filter(dish=entry.dish)
        for di in dish_ingredients:
            key = (di.ingredient.id, di.unit)
            quantity = di.quantity * entry.initial_quantity

            if key in ingredient_quantities:
                ingredient_quantities[key] += quantity
            else:
                ingredient_quantities[key] = quantity

    for (ingredient_id, unit), total_quantity in ingredient_quantities.items():
        ingredient = Ingredient.objects.get(id=ingredient_id)
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            ingredient=ingredient,
            required_quantity=total_quantity,
            unit=unit
        )

    items = ShoppingListItem.objects.filter(shopping_list=shopping_list)

    total_cost = sum(item.total_price for item in items)
     
    expense_exists = Expense.objects.filter(
        restaurant=restaurant,
        category='FOOD',
        expense_date= date.today()
    ).exists()

    if not expense_exists:
        Expense.objects.create(
            restaurant=restaurant,
            amount=total_cost,
            description=f"shoppingList n°{date.today()}",
            category='FOOD',
            expense_date=date.today(),
            created_by=request.user
        )
    return render(request, 'manager/orders.html', {
        'items': items,
        'total_cost': total_cost,
        'selected_date': selected_date
    })














