import datetime
from math import trunc
from django.forms import DecimalField
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404

from finance.models import Expense
from menu.models import DailyMenu
from orders.models import *
from .models import *
from .forms import *
from .decorators import *
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import get_user_model, logout
from django.utils import timezone
from django.contrib import messages
from .forms import ClientRegistrationForm
from feedback.models import *
from reservations.models import *
from django.db.models.functions import TruncYear, TruncMonth, TruncDay, TruncDate
from django.db.models import Sum, F, FloatField
import json
from datetime import date, datetime


def client_register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('landing_page')  # Make sure this URL name matches your urls.py
        else:
            # Return the form with errors
            return render(request, 'login.html', {'form': form})
    else:
        form = ClientRegistrationForm()
    return render(request, 'login.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            user.user_type = user.user_type.upper()  # Convert to uppercase
            request.session['display_username'] = user.get_full_name() or user.username
            if user.user_type == 'PDG':
                return redirect('pdg_dashboard')
            elif user.user_type == 'MANAGER':
                return redirect('manager_dashboard')
            elif user.user_type == 'CHEF':
                return redirect('ordersListChef')
            elif user.user_type == 'SERVER':
                return redirect('takeOrder')
            elif user.user_type == 'DELIVERY':
                return redirect('DeliveryOrders')
            elif user.user_type == 'CLIENT':
                return redirect('landing_page')
            elif user.user_type == 'SUPPLIER':
                return redirect('supplier_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')

def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')  



def generate_dashboard_data(orders, expenses, filter_type):
    if filter_type == 'Year':
        trunc_orders = TruncYear('order_date')
        trunc_expenses = TruncYear('expense_date')
        date_format = '%Y'
    elif filter_type == 'Month':
        trunc_orders = TruncMonth('order_date')
        trunc_expenses = TruncMonth('expense_date')
        date_format = '%Y-%m'
    elif filter_type == 'Day':
        trunc_orders = TruncDate('order_date')
        trunc_expenses = TruncDay('expense_date')
        date_format = '%Y-%m-%d'

    # Annotate period
    orders = orders.annotate(period=trunc_orders)
    expenses = expenses.annotate(period=trunc_expenses)

    # Aggregate revenue per period
    revenue_data = orders.values('period').annotate(
        revenue=Sum(
            F('orderdish__quantity') * F('orderdish__dish__price'),
            output_field=FloatField()
        )
    ).order_by('period')

    # Aggregate expenses per period
    expense_data = expenses.values('period').annotate(
        total_expense=Sum('amount')
    ).order_by('period')

    # Build dictionaries for quick lookup
    revenue_dict = {}
    for entry in revenue_data:
        period = entry['period']
        if isinstance(period, datetime):
            period = period.date()
        key = period.strftime(date_format)
        revenue_dict[key] = entry['revenue'] or 0

    expense_dict = {}
    for entry in expense_data:
        period = entry['period']
        if isinstance(period, datetime):
            period = period.date()
        key = period.strftime(date_format)
        expense_dict[key] = float(entry['total_expense'] or 0)

    # Merge periods
    all_periods = set(revenue_dict.keys()).union(expense_dict.keys())
    sorted_periods = sorted(all_periods)

    # Prepare chart data
    labels, revenues, expenses_list, profits = [], [], [], []
    for period in sorted_periods:
        rev = revenue_dict.get(period, 0)
        exp = expense_dict.get(period, 0)
        profit = rev - exp

        labels.append(period)
        revenues.append(rev)
        expenses_list.append(exp)
        profits.append(profit)

    return labels, revenues, expenses_list, profits

@pdg_required
def pdg_dashboard(request):
    client_count = Client.objects.count()
    review_count = Review.objects.count()


    today = timezone.now().date()

    # Get all orders with status = paid and order_date = today (all restaurants)
    paid_orders_today = Order.objects.filter(
        status=OrderStatus.PAID,
        order_date__date=today
    )

    # Count them
    paid_orders_today_count = paid_orders_today.count()

    filter_type = request.GET.get('filter', 'Year')
    orders = Order.objects.filter(status='paid')
    expenses = Expense.objects.all()

    labels, revenues, expenses_list, profits = generate_dashboard_data(orders, expenses, filter_type)


    top_dishes = OrderDish.objects.values('dish__name') \
        .annotate(total_quantity=Sum('quantity')) \
        .order_by('-total_quantity')[:5]

    context = {
        'paid_orders_today_count': paid_orders_today_count,
        'client_count': client_count,
        'review_count': review_count,
        'labels_json': json.dumps(labels),
        'revenues_json': json.dumps(revenues),
        'expenses_json': json.dumps(expenses_list),
        'profits_json': json.dumps(profits),
        'current_filter': filter_type,
        'top_dish_labels_json': json.dumps([dish['dish__name'] for dish in top_dishes]),
        'top_dish_quantities_json': json.dumps([dish['total_quantity'] for dish in top_dishes]),
    }

    return render(request, 'pdg/dashboard.html', context)

# For Manager (restaurant-specific)
@manager_required
def manager_dashboard(request):
    manager = get_object_or_404(Manager, user=request.user)
    

    restaurant = manager.restaurant

    active_chefs = Chef.objects.filter(restaurant=restaurant, status=EmployeeStatus.ACTIVE).count()
    active_servers = Server.objects.filter(restaurant=restaurant, status=EmployeeStatus.ACTIVE).count()
    active_delivery_persons = DeliveryPerson.objects.filter(restaurant=restaurant, status=EmployeeStatus.ACTIVE).count()
    total_employees = active_chefs + active_servers + active_delivery_persons
    
    responded_complaint_count = Complaint.objects.filter(
        restaurant=restaurant,
        status=ComplaintStatus.RESPONDED
    ).count()


    today = timezone.now().date()

    
    paid_orders_today_count = Order.objects.filter(
        restaurant=restaurant,
        status=OrderStatus.PAID,
        order_date__date=today
    ).count()


    filter_type = request.GET.get('filter', 'Year')
    restaurant = request.user.manager.restaurant

    orders = Order.objects.filter(status='paid', restaurant=restaurant)
    expenses = Expense.objects.filter(restaurant=restaurant)

    labels, revenues, expenses_list, profits = generate_dashboard_data(orders, expenses, filter_type)

    top_dishes = OrderDish.objects.filter(order__restaurant=restaurant) \
        .values('dish__name') \
        .annotate(total_quantity=Sum('quantity')) \
        .order_by('-total_quantity')[:5]

    context = {
        'paid_orders_today_count': paid_orders_today_count,
        'total_employees': total_employees,
        'responded_complaint_count': responded_complaint_count,
        'labels_json': json.dumps(labels),
        'revenues_json': json.dumps(revenues),
        'expenses_json': json.dumps(expenses_list),
        'profits_json': json.dumps(profits),
        'current_filter': filter_type,
        'top_dish_labels_json': json.dumps([dish['dish__name'] for dish in top_dishes]),
        'top_dish_quantities_json': json.dumps([dish['total_quantity'] for dish in top_dishes]),
        
    }

    return render(request, 'manager/dashboard.html', context)

             

@chef_required
def chef_dashboard(request):
    restaurant = request.user.manager.restaurant
    return render(request, 'chef/ordersListChef.html', {'restaurant': restaurant})

@waiter_required
def waiter_dashboard(request):
    restaurant = request.user.manager.restaurant
    return render(request, 'serveur/ordersList.html', {'restaurant': restaurant})

@delivery_required
def delivery_dashboard(request):
    restaurant = request.user.manager.restaurant
    return render(request, 'livreur/DeliveryOrders.html', {'restaurant': restaurant})


def landing_page(request):
    return render(request, 'client/landingPage.html')







@pdg_required
def restaurant_list(request): 
    selected_city = request.GET.get('city')
    restaurants = Restaurant.objects.select_related('manager__user').all()
    if selected_city:
        restaurants = Restaurant.objects.filter(city=selected_city)
    else:
        restaurants = Restaurant.objects.all()

    cities = Restaurant.objects.values_list('city', flat=True).distinct()
    return render(request, 'pdg/restaurants.html', {
        'restaurants': restaurants,
        'cities': cities,
        'selected_city': selected_city
    })

@pdg_required
def add_restaurant(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('restaurants')
    else:
        form = RestaurantForm()
    return render(request, 'pdg/addRest.html', {'form': form})

@pdg_required
def edit_restaurant(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurants')
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'pdg/addRest.html', {'form': form})

@pdg_required
def delete_restaurant(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        return redirect('restaurants')
    return render(request, 'pdg/restaurants.html', {'restaurant': restaurant})



















@pdg_required
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    
    return render(request, 'pdg/addEmployee.html', {'form': form})

@pdg_required
def employee_list(request):
    highlight_manager = request.GET.get('highlight')
    
    managers = Manager.objects.select_related('user', 'restaurant').all()
    suppliers = Supplier.objects.select_related('user').all()
    
    return render(request, 'pdg/employees.html', {
        'managers': managers,
        'suppliers': suppliers,
        'highlight_manager': highlight_manager
    })

User = get_user_model()

@pdg_required
def edit_employee(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    try:
        if user.user_type == 'MANAGER':
            employee = Manager.objects.get(user=user)
        elif user.user_type == 'SUPPLIER':
            employee = Supplier.objects.get(user=user)
        else:
            return redirect('employee_list')
    except (Manager.DoesNotExist, Supplier.DoesNotExist):
        return redirect('employee_list')

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            
            if user.user_type == 'MANAGER':
                # Get the new restaurant from the form
                new_restaurant = form.cleaned_data['restaurant']
                
                # Check if the restaurant already has a different manager
                if Manager.objects.filter(restaurant=new_restaurant).exclude(user=user).exists():
                    form.add_error('restaurant', 'This restaurant already has a manager.')
                    context = {
                        'form': form,
                        'is_edit': True,
                        'user_type': user.user_type,
                    }
                    return render(request, 'pdg/add_employee.html', context)
                
                employee.restaurant = new_restaurant
                employee.status = form.cleaned_data['status']
                employee.save()
                
            elif user.user_type == 'SUPPLIER':
                employee.address = form.cleaned_data['address']
                employee.save()
            
            return redirect('employee_list')
    else:
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
            'user_type': user.user_type,
        }
        
        if user.user_type == 'MANAGER':
            initial_data.update({
                'restaurant': employee.restaurant,
                'status': employee.status,
            })
        elif user.user_type == 'SUPPLIER':
            initial_data.update({
                'address': employee.address,
            })
        
        form = EmployeeForm(instance=user, initial=initial_data)

    context = {
        'form': form,
        'is_edit': True,
        'user_type': user.user_type,
    }
    return render(request, 'pdg/addEmployee.html', context)

@pdg_required
def delete_manager(request, pk):
    manager = get_object_or_404(Manager, pk=pk)
    if request.method == 'POST':
        manager.user.delete()
        return redirect('employee_list')
    return redirect('employee_list')

@pdg_required
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.user.delete()
        return redirect('employee_list')
    return redirect('employee_list')















@manager_required
def employee_manager_list(request):
    manager = Manager.objects.get(user=request.user)
    restaurant = manager.restaurant

    waiters = Server.objects.filter(restaurant=restaurant)
    chefs = Chef.objects.filter(restaurant=restaurant)
    delivery_persons = DeliveryPerson.objects.filter(restaurant=restaurant)

    return render(request, 'manager/employee.html', {
        'waiters': waiters,
        'chefs': chefs,
        'DeliveryPersons': delivery_persons
    })


@manager_required
def add_staff_employee(request):
    form = StaffEmployeeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data

        user = User.objects.create_user(
         username=data['name'],
         email=data['email'],
         first_name=data['name'].split(' ')[0],
         last_name=' '.join(data['name'].split(' ')[1:]) if len(data['name'].split(' ')) > 1 else '',
         phone=data['phone'],
         user_type=data['role'],  
         password=data['password'],
        )

        # Get the current manager's restaurant
        manager = get_object_or_404(Manager, user=request.user)
        restaurant = manager.restaurant

        # Create the appropriate staff object
        if data['role'] == 'chef':
            Chef.objects.create(user=user, restaurant=restaurant, status=data['status'])
        elif data['role'] == 'server':
            Server.objects.create(user=user, restaurant=restaurant, status=data['status'])
        elif data['role'] == 'delivery':
            DeliveryPerson.objects.create(user=user, restaurant=restaurant, status=data['status'])

        return redirect('employee_manager_list')

    return render(request, 'manager/addEmployee.html', {'form': form})

@manager_required
def edit_staff_employee(request, role, pk):
    model = {'chef': Chef, 'server': Server, 'delivery': DeliveryPerson}.get(role)
    instance = get_object_or_404(model, pk=pk)

    # Get the current manager's restaurant
    manager = get_object_or_404(Manager, user=request.user)
    if instance.restaurant != manager.restaurant:
        return HttpResponseForbidden("You do not have permission to edit this employee.")

    initial_data = {
        'name': instance.user.get_full_name(),
        'email': instance.user.email,
        'phone': instance.user.phone,
        'role': role,
        'status': instance.status,
    }

    form = StaffEmployeeForm(request.POST or None, initial=initial_data)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        user = instance.user
        user.username= data['name']
        user.first_name = data['name'].split(' ')[0]
        user.last_name = ' '.join(data['name'].split(' ')[1:]) if len(data['name'].split(' ')) > 1 else ''
        user.email = data['email']
        user.phone = data['phone']
        if data['password']:
            user.set_password(data['password'])
        user.save()

        instance.status = data['status']
        instance.save()

        return redirect('employee_manager_list')

    return render(request, 'manager/addEmployee.html', {'form': form, 'employee': instance})

from django.http import HttpResponseForbidden

@manager_required
def delete_staff_employee(request, role, pk):
    model = {'chef': Chef, 'server': Server, 'delivery': DeliveryPerson}.get(role)
    employee = get_object_or_404(model, pk=pk)

    # Get the current manager's restaurant
    manager = get_object_or_404(Manager, user=request.user)
    if employee.restaurant != manager.restaurant:
        return HttpResponseForbidden("You do not have permission to delete this employee.")

    if request.method == 'POST':
        employee.user.delete()  # Delete the associated User too
        employee.delete()
        return redirect('employee_manager_list')

    return render(request, 'manager/confirm_delete.html', {'employee': employee})








def landing_page(request):

    restaurants = Restaurant.objects.all()[:4]

    reviews = Review.objects.select_related('client__user').order_by('-date')[:5]
    
    context = {
        'restaurants': restaurants,
        'reviews': reviews,
    }
    return render(request, 'client/landingPage.html', context)




@client_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        
        if 'update_info' in request.POST and u_form.is_valid():
            u_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
            
        elif 'change_password' in request.POST and p_form.is_valid():
            p_form.save()
            messages.success(request, 'Your password has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = CustomPasswordChangeForm(user=request.user)
    
    # Récupérer l'historique des commandes et réservations
    orders = Order.objects.filter(client=request.user.client).order_by('-order_date')[:5]
    reservations = Reservation.objects.filter(client=request.user.client).order_by('-datetime')[:5]
    
    orders_qs = Order.objects.filter(client=request.user.client).order_by('-order_date')[:5]
    order_details = []
    for order in orders_qs:
        items = []
        total = 0
        for od in order.orderdish_set.select_related('dish'):
            item_total = od.quantity * od.dish.price
            items.append({
                'name': od.dish.name,
                'quantity': od.quantity,
                'price': od.dish.price,
                'total': item_total,
            })
            total += item_total
        order_details.append({
            'id': order.id,
            'date': order.order_date,
            'restaurant': order.restaurant.name,
            'status': order.get_status_display(),
            'items': items,
            'total': total,
        })

    # Historique des réservations
    reservations = Reservation.objects.filter(client=request.user.client).order_by('-datetime')[:5]

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'order_details': order_details,
        'reservations': reservations,
    }
    
    return render(request, 'client/profil.html', context)









@pdg_required
def restaurant_information(request, restaurant_id):
    
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    view_type = request.GET.get('view', 'daily_menu')  # default to 'daily_menu'
    today = timezone.now().date()

    context = {
        'restaurant': restaurant,
        'view_type': view_type,
    }

    if view_type == 'daily_menu':
        date_str = request.GET.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = today
        
        menus = DailyMenu.objects.filter(restaurant=restaurant, date=selected_date)
        context['menus'] = menus
        context['selected_date'] = selected_date

    elif view_type == 'expenses':
        month = request.GET.get('month')
        year = request.GET.get('year')

        if month and year:
            expenses = Expense.objects.filter(
                restaurant=restaurant,
                expense_date__month=month,
                expense_date__year=year
            )
        else:
            now = timezone.now()
            expenses = Expense.objects.filter(
                restaurant=restaurant,
                expense_date__month=now.month,
                expense_date__year=now.year
            )
        context['expenses'] = expenses

    elif view_type == 'orders':
        date_str = request.GET.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = today
        
        orders = Order.objects.filter(
            restaurant=restaurant,
            status=OrderStatus.PAID,
            order_date__date=selected_date
        )
        context['orders'] = orders
        context['selected_date'] = selected_date

    elif view_type == 'complaints': 

        date_str = request.GET.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = today
        
        complaints = Complaint.objects.filter( restaurant=restaurant,).order_by('-date')
        context['complaints'] = complaints

    elif view_type == 'reservations':
        date_str = request.GET.get('date')
        if date_str:
           selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
           selected_date = today

        reservations = Reservation.objects.filter(
           restaurant=restaurant,
           datetime__date=selected_date
        ).order_by('-datetime') 
        context['reservations'] = reservations
        context['selected_date'] = selected_date


    return render(request, 'pdg/restaurantInfo.html', context)
