# views.py
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import EditReservationForm, ReservationForm
from .models import Client
from django.core.exceptions import ObjectDoesNotExist
from restaurant.decorators import client_required
from restaurant.decorators import waiter_required
from restaurant.models import Server
from .models import Reservation 
from django.db.models import Q
from datetime import datetime, time


@client_required
def create_reservation(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            try:
               
                client = Client.objects.get(user=request.user)
                
                reservation = form.save(commit=False)
                reservation.client = client
                reservation.status = 'Pending'  
                reservation.save()
                return redirect('landing_page')
            except ObjectDoesNotExist:
               
                return redirect('login')
    else:
        form = ReservationForm()

    return render(request, 'client/reserver.html', {'form': form})



@waiter_required
def reserved_tables(request):
    server = get_object_or_404(Server, user=request.user)
    restaurant = server.restaurant

    

    
    filter_date = request.GET.get('filterDate')
    filter_time = request.GET.get('filterTime')
    filter_status = request.GET.get('filterStatus')
    clear = request.GET.get('clear') == '1'
    search = request.GET.get('search')
    
    reservations = Reservation.objects.filter(restaurant=restaurant)
    
    if clear and not any((request.GET.get('search'), request.GET.get('filterDate'),
                        request.GET.get('filterTime'), request.GET.get('filterStatus'))):
        return redirect('reserved_tables')
     

    if filter_date:
        try:
            date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            reservations = reservations.filter(datetime__date=date_obj)
        except ValueError:
            pass  

    if filter_time:
        
        if filter_time == 'Lunch':
            reservations = reservations.filter(datetime__time__gte=time(11, 0), datetime__time__lt=time(15, 0))
        elif filter_time == 'Dinner':
            reservations = reservations.filter(datetime__time__gte=time(17, 0), datetime__time__lt=time(22, 0))

    if filter_status:
        reservations = reservations.filter(status__iexact=filter_status)


    if search:
        reservations = reservations.filter(
            Q(client__user__username__icontains=search) |
            Q(table__icontains=search)
        ).distinct()

    return render(request, 'serveur/reservedTables.html', {
        'reservations': reservations,
        'restaurant': restaurant,
         'search':search,
    })

@waiter_required
def update_reservation(request, pk):
    
    serveur = get_object_or_404(Server, user=request.user)
    restaurant = serveur.restaurant
    reservation = get_object_or_404(Reservation, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        
        form = EditReservationForm(request.POST, instance=reservation)
        
        if form.is_valid():
            form.save()
            return redirect('reserved_tables')
        else:
         print(form.errors)
    else:
       
        form = EditReservationForm(instance=reservation)
       
    return render(request, 'serveur/editReservation.html', {
        'form': form,
        'reservation': reservation,
        'restaurant': restaurant,
    })
    
@waiter_required
def update_reservation_status(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        table_number = request.POST.get('table_number')
        if new_status in dict(Reservation.STATUS_CHOICES):
            reservation.status = new_status
            if new_status == 'accepted' and table_number:
                reservation.table = table_number
            
            reservation.save()
    return redirect('reserved_tables')

@waiter_required
def update_reservation_table(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.status == 'accepted':
        table_number = request.POST.get('table_number')
        if table_number:
            reservation.table = table_number
            reservation.save()
    return redirect(request.META.get('HTTP_REFERER', 'some_default_url'))

@waiter_required
def cancel_reservation(request,pk):
    server = get_object_or_404(Server, user=request.user)
    reservation = get_object_or_404(
        Reservation,
        id=pk,
        restaurant=server.restaurant
    )
    
    if request.method == 'POST':
        reservation.status = 'canceled'
        reservation.save()
    
    return redirect('reserved_tables')
