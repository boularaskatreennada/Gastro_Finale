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
from django.db.models import F, Q ,Count ,Sum
from django.http import Http404

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





@waiter_required
def orders_list(request):
    #  Find the restaurant 
    server     = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant
    status = request.GET.get('filterStatus')
    order_type = request.GET.get('filterType')
    table_number = request.GET.get('filterTable')
    payment_status = request.GET.get('filterPayment')
    search = request.GET.get('search')
    date_str = request.GET.get('date')

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = None
            
    else:
        selected_date = timezone.localdate()

    # orders by that date
    orders = (
        Order.objects
             .filter(
                 restaurant=restaurant,
                 order_date__date=selected_date  
             ).annotate(
                items_count=Count('orderdish', distinct=True),
                total_price=Sum(F('orderdish__quantity') * F('orderdish__dish__price')
                )).order_by('-order_date')
             .prefetch_related('orderdish_set__dish')
             
    )

    if status:
        orders = orders.filter(status=status)
    if order_type:
        orders = orders.filter(mode=order_type)
    if table_number:
        orders = orders.filter(table__id=table_number)
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    if search:
        orders = orders.filter(
            Q(table__name__icontains=search) |
            Q(server__user__username__icontains=search) |
            Q(orderdish__dish__name__icontains=search)
        ).distinct()
    
    return render(request, 'serveur/ordersList.html', {
        'orders': orders,
        'selected_date': selected_date,
    })



@chef_required
def order_list_chef(request):
       # get chefs restaurant
    chef = get_object_or_404(Chef, user=request.user)
    restaurant = chef.restaurant
    filter_type = request.GET.get('filter_type')
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = None
            
    else:
        selected_date = timezone.localdate()

    orders = (
        Order.objects
             .filter(
                 restaurant=restaurant,
                 order_date__date=selected_date  
             ).exclude(status='cancelled')
             .order_by('-order_date')
             .prefetch_related('orderdish_set__dish')
    )
    if filter_type:
        orders = orders.filter(mode=filter_type)

    return render(request, 'chef/ordersListChef.html', {
        'orders': orders,
        'restaurant': restaurant
    })

@waiter_required
def edit_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
   
    # Get all dishes in today's menu 
    today_menu = DailyMenu.objects.filter(
        restaurant=order.restaurant,
        date=timezone.localdate()
    ).first()

    if not today_menu:
        raise Http404("No menu for today")

    menu_entries = DailyMenuDish.objects.filter(menu=today_menu).select_related('dish')

    # Prepare existing order items for JS cart initialization
    order_items = []
    for od in order.orderdish_set.select_related('dish').all():
        order_items.append({
            'id': od.dish.id,
            'name': od.dish.name,
            'price': float(od.dish.price),
            'quantity': od.quantity,
        })

    context = {
        'menu_entries': menu_entries,
        'order_items_json': json.dumps(order_items),  # pass as JSON string
        'order': order,
        
    }

    return render(request, 'serveur/takeOrder.html', context)

@chef_required
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(OrderStatus.choices):
            order.status = new_status
            order.save()
    return redirect('ordersListChef')

@waiter_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    if request.method == 'POST':
        order.status = OrderStatus.CANCELLED
        order.save()
    return redirect('ordersList')

@delivery_required
def delivery_orders(request):
    order= Delivery.objects.all()
    Delivery.objects.filter(delivery_person=request.user)
    return render(request, 'livreur/DeliveryOrders.html', {
        'orders': order, })

@delivery_required
def update_delivery_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(DeliveryStatus.choices):
            order.status = new_status
            order.save()
    return redirect('DeliveryOrders')

@waiter_required
def take_order(request):
    # 1️⃣ Find the restaurant from the logged-in waiter
    server     = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant
    

    # 2️⃣ Grab (or bail if missing) today’s DailyMenu
    today = date.today()
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    try:
        today_menu = DailyMenu.objects.get(restaurant=restaurant, date=today)
        # 3️⃣ Fetch all the dishes on that menu
        menu_entries = DailyMenuDish.objects.filter(menu=today_menu).select_related('dish')
        if category and category.lower() != "all":
            menu_entries = menu_entries.filter(dish__category__iexact=category)
        if search:
            menu_entries = menu_entries.filter(
                Q(dish__name__icontains=search) |
                Q(dish__description__icontains=search)
            )
    except DailyMenu.DoesNotExist:
        menu_entries = []

    # 4️⃣ Render, passing the list of entries
    return render(request, 'serveur/takeOrder.html', {
        'menu_entries': menu_entries,
        
        })

@waiter_required
def placeOrder(request):
    server = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant
    table_number = request.POST.get('table_number')

    
    today = date.today() # Use timezone-aware date
    order_id = request.POST.get('order_id')  # <-- NEW
    # Use transaction to lock rows and avoid race conditions
    with transaction.atomic():
        today_menu = DailyMenu.objects.filter(
            restaurant=restaurant,
            date=today
        ).first()
        if not today_menu:
          #  messages.error(request, "No menu for today.")
            return redirect('takeOrder')

        if request.method == 'POST':
            item_ids = request.POST.getlist('item_id')
            quantities = request.POST.getlist('quantity')
            note = request.POST.get('note', '')

            # Lock the menu entries for update
            menu_entries = DailyMenuDish.objects.select_for_update().filter(menu=today_menu)
            menu_map = {entry.dish_id: entry for entry in menu_entries}
            # --- NEW LOGIC ---
            if order_id:
                order = get_object_or_404(Order, pk=order_id)
                order.table_number = table_number
                
                # Restore original stock quantities
                if order.orderdish_set.exists():  # Prevent None error
                    original_menu = order.orderdish_set.first().dish.dailymenudish_set.first().menu
                    for old_item in order.orderdish_set.all():
                        DailyMenuDish.objects.filter(
                            menu=original_menu,
                            dish=old_item.dish
                        ).update(
                            current_quantity=F('current_quantity') + old_item.quantity
                        )
                
                order.orderdish_set.all().delete()
                order.save()
            else:
                order = Order.objects.create(
                    server     = server,
                    restaurant = restaurant,
                    table_number = table_number,
                    status     = OrderStatus.PENDING,
                    mode       = OrderMode.SERVED,
                )

            for dish_id_str, qty_str in zip(item_ids, quantities):
                try:
                    dish_id = int(dish_id_str)
                    qty = int(qty_str)
                except ValueError:
                    continue  # skip invalid data

                if qty <= 0:
                    continue

                entry = menu_map.get(dish_id)
                if not entry:
                  #  messages.error(request, f"Dish ID {dish_id} not on today's menu.")
                    continue

                # Check quantity and decrement safely
                if qty > entry.current_quantity:
                    qty = entry.current_quantity

                if qty <= 0:
                    continue

                # Create order item
                OrderDish.objects.create(
                    order=order,
                    dish=entry.dish,
                    quantity=qty
                )

                # Decrement available quantity using F expression (safe for concurrency)
                DailyMenuDish.objects.filter(pk=entry.pk).update(
                    current_quantity=F('current_quantity') - qty
                )

            #messages.success(request, f"Order #{order.pk} created!")
            return redirect('takeOrder')




