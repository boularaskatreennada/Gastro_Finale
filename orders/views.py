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
from django.db.models import Sum, F, Count, Q
from django.db.models.functions import Coalesce
from decimal import Decimal



@manager_required
def orderslistManager(request):
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
def placeOrderClient(request):
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
    
    # Initialisation des variables
    subtotal = order.total_amount
    final_amount = subtotal
    discount_amount = 0
    discount_percentage = 0
    discount_applied = False
    promo_error = None
    promo_success = None
    promo_code = None

    if request.method == 'POST':
        # Traitement du code promo
        if 'apply_promo' in request.POST:
            promo_code = request.POST.get('promo_code', '').strip()
            if promo_code:
                try:
                    offer = Offer.objects.get(code=promo_code)
                    today = timezone.now().date()
                    
                    # Vérification de la validité de l'offre
                    if offer.start_date <= today <= offer.end_date:
                        discount_percentage = Decimal(str(offer.discount))
                        discount_amount = (subtotal * discount_percentage) / Decimal('100')
                        final_amount = subtotal - discount_amount
                        discount_applied = True
                        promo_success = f"Promo code applied! {discount_percentage}% discount."
                        
                        # Sauvegarde des infos de réduction
                        order.discount_amount = discount_amount
                        order.discount_percentage = discount_percentage
                        order.promo_code = promo_code
                        order.save()
                    else:
                        promo_error = "This promo code is not currently active."
                except Offer.DoesNotExist:
                    promo_error = "Invalid promo code."

            # Retourner la réponse
            return render(request, 'client/confirmOrder.html', {
                'order': order,
                'subtotal': subtotal,
                'final_amount': final_amount,
                'discount_amount': discount_amount,
                'discount_percentage': discount_percentage,
                'discount_applied': discount_applied,
                'promo_error': promo_error,
                'promo_success': promo_success,
                'promo_code': promo_code,
                'address': request.POST.get('address', ''),
                'table_number': request.POST.get('table_number', ''),
            })

        # Traitement de la confirmation de commande
        mode = request.POST.get('mode')
        address = request.POST.get('address', '').strip()
        table_number = request.POST.get('table_number')
        promo_code = request.POST.get('promo_code', '').strip()

        # Validation du mode de commande
        if mode not in ['served', 'delivered', 'take-away']:
            messages.error(request, "Invalid mode selected.")
            return redirect('confirm_order', order_id=order.id)

        order.mode = mode

        # Gestion spécifique au mode 'served'
        if mode == 'served':
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
            order.table_number = None

        order.save()

        # Création d'une livraison si nécessaire
        if mode == 'delivered':
            Delivery.objects.create(
                order=order,
                delivery_person=None,
                delivery_date=timezone.now(),
                status=DeliveryStatus.PENDING,
                address=address
            )

        # Mise à jour des points de fidélité
        try:
            client = request.user.client
            client.loyality_points += 1
            client.save()
        except Exception as e:
            print(f"Error updating loyalty points: {e}")

        return redirect('profile')

    # GET request - Affichage initial
    return render(request, 'client/confirmOrder.html', {
        'order': order,
        'subtotal': subtotal,
        'final_amount': final_amount,
        'discount_amount': discount_amount,
        'discount_percentage': discount_percentage,
        'discount_applied': discount_applied,
        'promo_error': promo_error,
        'promo_success': promo_success,
        'promo_code': promo_code,
    })

@waiter_required
def orders_list(request):
    #  Find the restaurant 
    server     = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant
    status = request.GET.get('filterStatus')
    order_type = request.GET.get('filterType')

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


@waiter_required
def orders_list(request):
    #  Find the restaurant 
    server     = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant
    status = request.GET.get('filterStatus')
    order_type = request.GET.get('filterType')
    search = request.GET.get('search')
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
        .filter(restaurant=restaurant, order_date__date=selected_date)
        .exclude(status='cancelled')
        .annotate(
            items_count=Count('orderdish'),
            raw_subtotal=Sum(F('orderdish__quantity') * F('orderdish__dish__price'))
        )
        .order_by('-order_date')
        .prefetch_related('orderdish_set__dish')
    )
    
    if status:
        orders = orders.filter(status=status)
    if order_type:
        orders = orders.filter(mode=order_type)
    
    if search:
        orders = orders.filter(
            Q(client__user__username__icontains=search)).distinct()
    
    # Calculate final price for each order
    for order in orders:
        # Ensure we have proper decimal values
        order.subtotal = order.raw_subtotal if order.raw_subtotal else Decimal('0.00')
        
        # Calculate discounts
        if order.discount_percentage > 0:
            discount = (order.subtotal * order.discount_percentage) / Decimal('100')
            order.final_price = order.subtotal - discount
        elif order.discount_amount > 0:
            order.final_price = order.subtotal - order.discount_amount
        else:
            order.final_price = order.subtotal
        
        # Format for display
        order.display_subtotal = f"{order.subtotal:.2f}"
        order.display_final = f"{order.final_price:.2f}"
        
    return render(request, 'serveur/ordersList.html', {
        'orders': orders,
        'selected_date': selected_date,
        'search': search,
    })





@chef_required
def order_list_chef(request):
    # Get chef's restaurant
    chef = get_object_or_404(Chef, user=request.user)
    restaurant = chef.restaurant
    filter_type = request.GET.get('filter_type', '')
    date_str = request.GET.get('date')
    search = request.GET.get('search')
    
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = None
    else:
        selected_date = timezone.localdate()

    # Get base queryset
    orders = (
        Order.objects
        .filter(restaurant=restaurant, order_date__date=selected_date)
        .exclude(status='cancelled')
        .annotate(
            items_count=Count('orderdish'),
            raw_subtotal=Sum(F('orderdish__quantity') * F('orderdish__dish__price'))
        )
        .order_by('-order_date')
        .prefetch_related('orderdish_set__dish')
    )


    if filter_type:
        orders = orders.filter(mode=filter_type)

    if search:
        orders = orders.filter(
            Q(client__user__username__icontains=search)
        ).distinct()
    
    # Calculate final price for each order
    for order in orders:
        # Ensure we have proper decimal values
        order.subtotal = order.raw_subtotal if order.raw_subtotal else Decimal('0.00')
        
        # Calculate discounts
        if order.discount_percentage > 0:
            discount = (order.subtotal * order.discount_percentage) / Decimal('100')
            order.final_price = order.subtotal - discount
        elif order.discount_amount > 0:
            order.final_price = order.subtotal - order.discount_amount
        else:
            order.final_price = order.subtotal
        
        # Format for display
        order.display_subtotal = f"{order.subtotal:.2f}"
        order.display_final = f"{order.final_price:.2f}"
    
    return render(request, 'chef/ordersListChef.html', {
        'orders': orders,
        'restaurant': restaurant,
        'filter_type': filter_type,
        'search': search,
    })


@waiter_required
def edit_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
   
    # Get all dishes in today menu 
    today_menu = DailyMenu.objects.filter(
        restaurant=order.restaurant,
        date=timezone.localdate()
    ).first()

    if not today_menu:
        raise Http404("No menu for today")

    menu_entries = DailyMenuDish.objects.filter(menu=today_menu).select_related('dish')
     
    # existing order 
    order_items = []
    for od in order.orderdish_set.select_related('dish').all():
        order_items.append({
            'id': od.dish.id,
            'name': od.dish.name,
            'price': float(od.dish.price),
            'quantity': od.quantity,
        })
    category = request.GET.get('category')
    

    categories = MainMenu.objects.filter(
        id__in=menu_entries.values_list('dish__menu_id', flat=True).distinct()
    )
    if category and category.lower() != "all":
        menu_entries = menu_entries.filter(dish__menu__category__iexact=category)

    context = {
        'menu_entries': menu_entries,
        'order_items_json': json.dumps(order_items),  
        'order': order,
        'categories': categories,
        'selected_category': category or 'all',
        
    }

    return render(request, 'serveur/takeOrder.html', context)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
@chef_required
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
   
    if request.method == 'POST':
        new_status = request.POST.get('status')
        

        if new_status in dict(OrderStatus.choices):
            order.status = new_status
            order.save()
            
            
            if order.mode == 'delivered'and new_status == 'done'  :
             
             
                channel_layer = get_channel_layer()
             
                # Send to all connected 
                async_to_sync(channel_layer.group_send)(
                    "delivery_group",  
                    {
                        "type": "send_notification",
                        "data": {
                            "order_id": str(order.id),
                            "client": order.client.user.username,
                            "address": order.client.user.phone,
                            "phone": order.client.user.phone,
                        
                            "items": [
                                f"{item.quantity}x {item.dish.name}"
                                for item in order.orderdish_set.all()
                            ]or ["No items listed"]
                        }
                    }
                )
                order_delivery = get_object_or_404(Delivery,order=order)
                order_delivery.notified = True
                order_delivery.save()

            if order.mode == 'served' and new_status == 'done':
                if order.server:
                    target_server = order.server

                
                else:
                    servers = Server.objects.filter(
                        restaurant=order.restaurant,
                        status='active'
                    ).annotate(
                        served_count=Count(
                            'order',
                            filter=Q(order__mode='served', order__status='done')
                        )
                    )
                    target_server = servers.order_by('served_count').first()
                
                channel_layer = get_channel_layer()
                payload = {
                    "order_id": str(order.id),
                    "table":    order.table_number or "N/A",
                    "items":    [f"{i.quantity}× {i.dish.name}" for i in order.orderdish_set.all()],
                }

                async_to_sync(channel_layer.group_send)(
                    f"server_{target_server.user.id}",
                    {
                        "type": "send_notification",
                        "data": payload
                    }
                )
                order.server = target_server
                order.notified = True
                order.save()
    return redirect('ordersListChef')

@waiter_required
def update_order_status_waiter(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(OrderStatus.choices):
            order.status = new_status
            order.save()
    return redirect('ordersList')

@waiter_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, id=pk)
    if request.method == 'POST':
        order.status = OrderStatus.CANCELED
        order.save()
    return redirect('ordersList')

@delivery_required
def delivery_orders(request):
   
    livreur = get_object_or_404(DeliveryPerson, user=request.user)
    orders = Delivery.objects.filter(delivery_person=livreur)
    filter_type = request.GET.get('filter_type', '') 
    
    if filter_type:
        orders = orders.filter(status=filter_type)
    orders = orders.select_related('order').order_by('-order__order_date')
    return render(request, 'livreur/DeliveryOrders.html', {
        'delivery_orders': orders,
        'filter_type': filter_type,
         'delivery_status_choices': DeliveryStatus.choices, })

@delivery_required
def update_delivery_order(request, pk):
    delivery = get_object_or_404(Delivery, pk=pk)
    order = delivery.order  
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(DeliveryStatus.choices):
            delivery.status = new_status
            delivery.save()
            if new_status=="delivered":
                order.status='paid'
                order.save()
    return redirect('DeliveryOrders')

@waiter_required
def take_order(request):
    # Find the restaurant 
    server     = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant
    

    
    today = date.today()
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    try:
        today_menu = DailyMenu.objects.get(restaurant=restaurant, date=today)
        
        # all the dishes on that menu
        menu_entries = DailyMenuDish.objects.filter(menu=today_menu).select_related('dish')
        categories = MainMenu.objects.filter(
            id__in=menu_entries.values_list('dish__menu_id', flat=True).distinct())
        if category and category.lower() != "all":
            menu_entries = menu_entries.filter(dish__menu__category__iexact=category)
        if search:
            menu_entries = menu_entries.filter(
                Q(dish__name__icontains=search) |
                Q(dish__description__icontains=search)
            )
    except DailyMenu.DoesNotExist:
        menu_entries = []
        categories = []

    
    return render(request, 'serveur/takeOrder.html', {
        'menu_entries': menu_entries,
        'categories': categories,
        'selected_category': category or 'all',
        })

@waiter_required
def placeOrder(request):
    server = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant
    
    table_number = request.POST.get('table_number')

     
        
    today = date.today() 
    order_id = request.POST.get('order_id')  
    # transaction to lock rows and avoid race conditions
    with transaction.atomic():
        today_menu = DailyMenu.objects.filter(
            restaurant=restaurant,
            date=today
        ).first()
        if not today_menu:
          
            return redirect('takeOrder')

        if request.method == 'POST':
            item_ids = request.POST.getlist('item_id')
            quantities = request.POST.getlist('quantity')
            
            menu_entries = DailyMenuDish.objects.select_for_update().filter(menu=today_menu)
            menu_map = {entry.dish_id: entry for entry in menu_entries}
            
            if order_id:
                order = get_object_or_404(Order, pk=order_id)
                if order.mode == OrderMode.SERVED:
                    order.table_number = table_number
                else:
                    order.table_number = None
                
                
                if order.orderdish_set.exists(): 
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
                    continue  

                if qty <= 0:
                    continue

                entry = menu_map.get(dish_id)
                if not entry:
                  
                    continue

                
                if qty > entry.current_quantity:
                    qty = entry.current_quantity

                if qty <= 0:
                    continue

                
                OrderDish.objects.create(
                    order=order,
                    dish=entry.dish,
                    quantity=qty
                )

                # Decrement
                DailyMenuDish.objects.filter(pk=entry.pk).update(
                    current_quantity=F('current_quantity') - qty
                )

            
            return redirect('takeOrder')


@delivery_required
def notifications_del(request):
    deliveries = Delivery.objects.filter(
        notified=True).select_related('order__client__user').order_by('-delivery_date') 
    
    return render(request, 'livreur/notificationsDel.html', {
        'deliveries': deliveries,
    })


@waiter_required
def notifications_serveur(request):
    my_server = request.user.server
    orders = Order.objects.filter(
        notified=True,server=my_server).select_related('client__user', 'server', 'restaurant').order_by('-order_date')

    return render(request, 'serveur/Notifications.html', {
        'orders':orders,
    })

