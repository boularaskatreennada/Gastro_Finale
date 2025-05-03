# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ReservationForm
from .models import Client
from django.core.exceptions import ObjectDoesNotExist
from restaurant.decorators import client_required


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