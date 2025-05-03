import json
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from restaurant.decorators import *
from django.utils import timezone
from django.http import JsonResponse
from restaurant.models import *
from menu.models import *
from .models import *
from .forms import OrderConfirmationForm
from datetime import date, datetime
from django.db import transaction
from feedback.models import *
from django.views.decorators.http import require_POST


@manager_required
def orders_list(request):
    restaurant = request.user.manager.restaurant

    date_str = request.GET.get('date')
    orders = []
    complaints = [] 

    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = timezone.now().date()

    try:
        orders = Order.objects.filter(
            restaurant=restaurant,
            order_date__date=selected_date
        ).order_by('-order_date')

        complaints = Complaint.objects.filter(
            restaurant=restaurant,
            date=selected_date 
        ).order_by('-date')

    except ValueError:
        selected_date = None
        orders = []
        complaints = []

    return render(request, 'manager/client_orders.html', {
        'orders': orders,
        'complaints': complaints,
        'selected_date': selected_date,
        'Complaint': Complaint ,
        'ComplaintStatus': ComplaintStatus
    })



@manager_required
@require_POST
def update_complaint_status(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id, restaurant=request.user.manager.restaurant)
    new_status = request.POST.get('status')
    
    if new_status in dict(ComplaintStatus.choices).keys():
        complaint.status = new_status
        complaint.save()
    else:
        messages.error(request, "Invalid status selected.")
        
    return redirect('clients_orders_list')

@client_required
def clientOrder(request):
    selected_city = request.GET.get('city')
    selected_restaurant_id = request.GET.get('restaurant')
    selected_category = request.GET.get('category')

    # Filter restaurants by city
    restaurants = Restaurant.objects.all()
    if selected_city:
        restaurants = restaurants.filter(city=selected_city)

    # Get distinct cities
    cities = Restaurant.objects.values_list('city', flat=True).distinct()

    categories = None
    dishes = None
    selected_restaurant = None

    if selected_restaurant_id:
        selected_restaurant = get_object_or_404(Restaurant, id=selected_restaurant_id)

        # Get today's daily menu of selected restaurant
        today = date.today()
        try:
            daily_menu = DailyMenu.objects.get(restaurant=selected_restaurant, date=today)

            # Get dishes in today's daily menu
            daily_menu_dishes = DailyMenuDish.objects.filter(menu=daily_menu, current_quantity__gt=0).select_related('dish', 'dish__menu')
            # Extract unique categories from dishes
            categories = MainMenu.objects.filter(
                id__in=daily_menu_dishes.values_list('dish__menu', flat=True).distinct()
            )

            if selected_category:
               # Filter dishes of selected category
                dishes = []
                for dmd in daily_menu_dishes:
                    if str(dmd.dish.menu.category) == selected_category:
                       # Attach current_quantity dynamically to dish (so template can show it)
                       dmd.dish.dailymenudish = dmd  # this is fine for template usage
                       dishes.append(dmd.dish)
            else:
                # No category selected → show all available dishes
                dishes = []
                for dmd in daily_menu_dishes:
                    dmd.dish.dailymenudish = dmd
                    dishes.append(dmd.dish)

        except DailyMenu.DoesNotExist:
            daily_menu_dishes = []
            categories = []
            dishes = []

    return render(request, 'client/order.html', {
        'restaurants': restaurants,
        'cities': cities,
        'selected_city': selected_city,
        'selected_restaurant': selected_restaurant,
        'categories': categories,
        'selected_category': selected_category,
        'dishes': dishes,
    })







@client_required
def place_order(request):
    if request.method == 'POST':
        data = json.loads(request.POST.get('cart'))
        restaurant_id = request.POST.get('restaurant_id')
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        client = request.user.client

        today = date.today()

        try:
            daily_menu = DailyMenu.objects.get(restaurant=restaurant, date=today)
        except DailyMenu.DoesNotExist:
            return JsonResponse({'error': 'Today\'s menu is not available.'}, status=400)

        with transaction.atomic():  # Ensure atomicity
            order = Order.objects.create(
                status='pending',
                mode='served',
                client=client,
                server=None,
                restaurant=restaurant
            )

            for dish_id, item in data.items():
                dish = get_object_or_404(Dish, id=dish_id)
                quantity = item['quantity']

                # Find DailyMenuDish entry for this dish
                daily_menu_dish = get_object_or_404(
                    DailyMenuDish,
                    menu=daily_menu,
                    dish=dish
                )

                if daily_menu_dish.current_quantity < quantity:
                    transaction.set_rollback(True)
                    return JsonResponse({
                        'error': f'Not enough stock for {dish.name}. Available: {daily_menu_dish.current_quantity}'
                    }, status=400)

                # Decrease quantity
                daily_menu_dish.current_quantity -= quantity
                daily_menu_dish.save()

                OrderDish.objects.create(
                    order=order,
                    dish=dish,
                    quantity=quantity
                )

        return JsonResponse({'redirect_url': f'/orders/confirm_order/{order.id}/'})

    return JsonResponse({'error': 'Invalid request'}, status=400)



@client_required
def confirm_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user.client)

    if request.method == 'POST':
        mode = request.POST.get('mode')
        address = request.POST.get('address', '').strip()
        table_number = request.POST.get('table_number')

        if mode not in ['served', 'delivered', 'take-away']:
            messages.error(request, "Invalid mode selected.")
            return redirect('confirm_order', order_id=order.id)


        order.mode = mode

        if mode == 'served':
            # Validate and save table_number
            if table_number:
                try:
                    table_number_int = int(table_number)
                    if table_number_int <= 0:
                        raise ValueError
                    order.table_number = table_number_int
                except ValueError:
                    messages.error(request, "Invalid table number.")
                    return redirect('confirm_order', order_id=order.id)
            else:
                messages.error(request, "Table number is required for served orders.")
                return redirect('confirm_order', order_id=order.id)
        else:
            order.table_number = None  # Clear table number for other modes

        order.save()

        return redirect('landing_page')

    return render(request, 'client/confirmOrder.html', {'order': order})
